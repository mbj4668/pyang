"""pyang LSP Server"""

from __future__ import absolute_import
import optparse
import os
import tempfile
from pathlib import Path
from typing import List

from pyang import error, repository, util
from pyang import yang_parser
from pyang import context
from pyang import plugin
from pyang import syntax
from pyang.statements import Statement
from pyang.translators import yang

from lsprotocol import types as lsp
from pygls.server import LanguageServer
from pygls.workspace import TextDocument
from pygls.uris import from_fs_path, to_fs_path

import importlib

ext_deps = ['pygls']
def try_import_deps():
    """Raises `ModuleNotFoundError` if external module dependencies are missing"""
    for dep in ext_deps:
        importlib.import_module(dep)

SERVER_NAME = "pyang"
SERVER_VERSION = "v0.1"

SERVER_MODE_IO = "io"
SERVER_MODE_TCP = "tcp"
SERVER_MODE_WS = "ws"
supported_modes = [
    SERVER_MODE_IO,
    SERVER_MODE_TCP,
    SERVER_MODE_WS,
]
default_mode = SERVER_MODE_IO
default_host = "127.0.0.1"
default_port = 2087

# Diagnostics/Formatting parameters
default_line_length = 80
default_canonical_order = False
default_remove_unused_imports = False
default_remove_comments = False

class PyangLanguageServer(LanguageServer):
    def __init__(self):
        self.ctx : context.Context
        self.yangfmt : yang.YANGPlugin
        super().__init__(
            name=SERVER_NAME,
            version=SERVER_VERSION,
            text_document_sync_kind=lsp.TextDocumentSyncKind.Full
        )

pyangls = PyangLanguageServer()


def add_opts(optparser: optparse.OptionParser):
    optlist = [
        # use capitalized versions of std options help and version
        optparse.make_option("--lsp-mode",
                             dest="pyangls_mode",
                             default=default_mode,
                             metavar="LSP_MODE",
                             help="Provide LSP Service in this mode" \
                             "Supported LSP server modes are: " +
                             ', '.join(supported_modes)),
        optparse.make_option("--lsp-host",
                             dest="pyangls_host",
                             default=default_host,
                             metavar="LSP_HOST",
                             help="Bind LSP Server to this address"),
        optparse.make_option("--lsp-port",
                             dest="pyangls_port",
                             type="int",
                             default=default_port,
                             metavar="LSP_PORT",
                             help="Bind LSP Server to this port"),
        ]
    g = optparser.add_option_group("LSP Server specific options")
    g.add_options(optlist)


def start_server(optargs, ctx: context.Context, fmts: dict):
    pyangls.ctx = ctx
    pyangls.yangfmt = fmts['yang']
    if optargs.pyangls_mode == SERVER_MODE_TCP:
        pyangls.start_tcp(optargs.pyangls_host, optargs.pyangls_port)
    elif optargs.pyangls_mode == SERVER_MODE_WS:
        pyangls.start_ws(optargs.pyangls_host, optargs.pyangls_port)
    else:
        pyangls.start_io()

def _delete_from_ctx(text_doc: TextDocument):
    assert text_doc.filename
    m = syntax.re_filename.search(text_doc.filename)
    if m is not None:
        name, rev, _ = m.groups()
        module = pyangls.ctx.get_module(name, rev)
        if module is not None:
            pyangls.ctx.del_module(module)
    else:
        p = yang_parser.YangParser()
        ctx = context.Context(repository.FileRepository())
        module = p.parse(ctx, text_doc.path, text_doc.source)
        if module is not None:
            rev = util.get_latest_revision(module)
            module = pyangls.ctx.get_module(module.arg, rev)
            if module is not None:
                pyangls.ctx.del_module(module)

def _add_to_ctx(text_doc: TextDocument):
    assert text_doc.filename
    m = syntax.re_filename.search(text_doc.filename)
    if m is not None:
        name, rev, in_format = m.groups()
        assert in_format == 'yang'
        module = pyangls.ctx.add_module(text_doc.path, text_doc.source,
                                        in_format, name, rev,
                                        expect_failure_error=False,
                                        primary_module=True)
    else:
        module = pyangls.ctx.add_module(text_doc.path, text_doc.source,
                                        primary_module=True)
    return module

def _update_ctx_module(text_doc: TextDocument):
    _delete_from_ctx(text_doc)
    return _add_to_ctx(text_doc)

def _update_ctx_modules():
    for text_doc in pyangls.workspace.documents.values():
        _update_ctx_module(text_doc)

def _get_ctx_modules():
    modules = []
    for k in pyangls.ctx.modules:
        m = pyangls.ctx.modules[k]
        if m is not None:
            modules.append(m)
    return modules

def _clear_stmt_validation(stmt: Statement):
    stmt.i_is_validated = False
    substmt : Statement
    for substmt in stmt.substmts:
        _clear_stmt_validation(substmt)

def _clear_ctx_validation():
    # pyangls.ctx.internal_reset()
    pyangls.ctx.errors = []
    module : Statement
    for module in pyangls.ctx.modules.values():
        module.internal_reset()
        # _clear_stmt_validation(module)

def _validate_ctx_modules():
    # ls.show_message_log("Validating YANG...")
    modules = _get_ctx_modules()

    p : plugin.PyangPlugin

    for p in plugin.plugins:
        p.pre_validate_ctx(pyangls.ctx, modules)

    pyangls.ctx.validate()

    for _m in modules:
        _m.prune()

    for p in plugin.plugins:
        p.post_validate_ctx(pyangls.ctx, modules)

def _build_doc_diagnostics(ref: str) -> List[lsp.Diagnostic]:
    """Builds lsp diagnostics from pyang context"""
    diagnostics = []
    pyangls.ctx.errors.sort(key=lambda e: (e[0].ref, e[0].line), reverse=True)
    for epos, etag, eargs in pyangls.ctx.errors:
        if epos.ref != ref:
            continue
        msg = error.err_to_str(etag, eargs)

        def line_to_lsp_range(line) -> lsp.Range:
            # pyang just stores line context, not keyword/argument context
            start_line = line - 1
            if etag == 'LONG_LINE' and pyangls.ctx.max_line_len is not None:
                start_col = pyangls.ctx.max_line_len
            else:
                start_col = 0
            end_line = line
            end_col = 0
            return lsp.Range(
                start=lsp.Position(line=start_line, character=start_col),
                end=lsp.Position(line=end_line, character=end_col),
            )

        def level_to_lsp_severity(level) -> lsp.DiagnosticSeverity:
            if level == 1 or level == 2:
                return lsp.DiagnosticSeverity.Error
            elif level == 3:
                return lsp.DiagnosticSeverity.Warning
            elif level == 4:
                return lsp.DiagnosticSeverity.Information
            else:
                return lsp.DiagnosticSeverity.Hint

        diag_tags=[]
        rel_info=[]
        unused_etags = [
            'UNUSED_IMPORT',
            'UNUSED_TYPEDEF',
            'UNUSED_GROUPING',
        ]
        duplicate_1_etags = [
            'DUPLICATE_ENUM_NAME',
            'DUPLICATE_ENUM_VALUE',
            'DUPLICATE_BIT_POSITION',
            'DUPLICATE_CHILD_NAME',
        ]
        if etag in unused_etags:
            diag_tags.append(lsp.DiagnosticTag.Unnecessary)
        elif etag in duplicate_1_etags:
            if etag == 'DUPLICATE_ENUM_NAME':
                dup_arg = 1
                dup_msg = 'Original Enumeration'
            elif etag == 'DUPLICATE_ENUM_VALUE':
                dup_arg = 1
                dup_msg = 'Original Enumeration with Value'
            elif etag == 'DUPLICATE_BIT_POSITION':
                dup_arg = 1
                dup_msg = 'Original Bit Position'
            elif etag == 'DUPLICATE_CHILD_NAME':
                dup_arg = 3
                dup_msg = 'Original Child'
            dup_uri = from_fs_path(eargs[dup_arg].ref)
            dup_range = line_to_lsp_range(eargs[dup_arg].line)
            if dup_uri:
                dup_loc = lsp.Location(uri=dup_uri, range=dup_range)
                rel_info.append(lsp.DiagnosticRelatedInformation(location=dup_loc,
                                                             message=dup_msg))
        elif etag == 'DUPLICATE_NAMESPACE':
            # TODO
            pass

        d = lsp.Diagnostic(
            range=line_to_lsp_range(epos.line),
            message=msg,
            severity=level_to_lsp_severity(error.err_level(etag)),
            tags=diag_tags,
            related_information=rel_info,
            code=etag,
            source=SERVER_NAME,
        )

        diagnostics.append(d)

    return diagnostics

def _publish_doc_diagnostics(text_doc: TextDocument):
    if not pyangls.client_capabilities.text_document:
        return
    if not pyangls.client_capabilities.text_document.publish_diagnostics:
        return
    diagnostics = _build_doc_diagnostics(text_doc.path)
    pyangls.publish_diagnostics(text_doc.uri, diagnostics)

def _publish_workspace_diagnostics():
    for text_doc in pyangls.workspace.text_documents.values():
        _publish_doc_diagnostics(text_doc)

def _get_folder_yang_uris(folder_uri) -> List[str]:
    """Recursively find all .yang files in the given folder."""
    folder = to_fs_path(folder_uri)
    assert folder
    yang_files = []
    for root, _, files in os.walk(folder):
        file : str
        for file in files:
            if file.endswith(".yang") and not file.startswith('.#'):
                yang_files.append(from_fs_path(os.path.join(root, file)))
    return yang_files

def _have_parser_errors() -> bool:
    for _, etag, _ in pyangls.ctx.errors:
        if etag in yang_parser.errors:
            return True
    return False

def _format_yang(source: str, opts, module) -> str:
    if opts.insert_spaces == False:
        pyangls.log_trace("insert_spaces is currently restricted to True")
    if opts.tab_size:
        pyangls.ctx.opts.yang_indent_size = opts.tab_size # type: ignore
    if opts.trim_trailing_whitespace == False:
        pyangls.log_trace("trim_trailing_whitespace is currently restricted to True")
    if opts.trim_final_newlines == False:
        pyangls.log_trace("trim_final_newlines is currently restricted to True")
    pyangls.ctx.opts.yang_canonical = default_canonical_order # type: ignore
    pyangls.ctx.opts.yang_line_length = default_line_length # type: ignore
    pyangls.ctx.opts.yang_remove_unused_imports = default_remove_unused_imports # type: ignore
    pyangls.ctx.opts.yang_remove_comments = default_remove_comments # type: ignore

    pyangls.yangfmt.setup_fmt(pyangls.ctx)
    tmpfd = tempfile.TemporaryFile(mode="w+", encoding="utf-8")

    pyangls.yangfmt.emit(pyangls.ctx, [module], tmpfd)

    tmpfd.seek(0)
    fmt_text = tmpfd.read()
    tmpfd.close()

    # pyang only supports unix file endings and inserts a final one if missing
    if not opts.insert_final_newline and not source.endswith('\n'):
        fmt_text.rstrip('\n')

    return fmt_text


@pyangls.feature(lsp.INITIALIZED)
def initialized(
    ls: LanguageServer,
    params: lsp.InitializedParams,
):
    # ls.show_message("Received Initialized")
    # TODO: Try sending first diagnostics notifications here
    #       Does not seem to work, hence sending on first workspace/didChangeConfiguration
    pass


@pyangls.feature(lsp.WORKSPACE_DID_CHANGE_CONFIGURATION)
def did_change_configuration(
    ls: LanguageServer,
    params: lsp.DidChangeConfigurationParams
):
    # ls.show_message("Received Workspace Did Change Configuration")
    # TODO: Handle configuration changes including ignoring additional files/subdirs

    _clear_ctx_validation()

    if ls.workspace.folders:
        # TODO: Handle more than one workspace folder
        folder = next(iter(ls.workspace.folders.values()))
        yang_uris = _get_folder_yang_uris(folder.uri)
        for yang_uri in yang_uris:
            if not yang_uri in ls.workspace.text_documents.keys():
                yang_file = to_fs_path(yang_uri)
                assert yang_file
                with open(yang_file, 'r') as file:
                    yang_source = file.read()
                    file.close()
                ls.workspace.put_text_document(
                    lsp.TextDocumentItem(
                        uri=yang_uri,
                        language_id='yang',
                        version=0,
                        text=yang_source,
                    )
                )

    _update_ctx_modules()

    _validate_ctx_modules()
    _publish_workspace_diagnostics()


@pyangls.feature(lsp.WORKSPACE_DID_CHANGE_WATCHED_FILES)
def did_change_watched_files(
    ls: LanguageServer,
    params: lsp.DidChangeWatchedFilesParams
):
    """Workspace did change watched files notification."""
    ls.show_message("Received Workspace Did Change Watched Files")
    _clear_ctx_validation()

    # Process all the Deleted events first to handle renames more gracefully
    for event in params.changes:
        if event.type != lsp.FileChangeType.Deleted:
            continue

        text_doc = ls.workspace.get_text_document(event.uri)
        ls.workspace.remove_text_document(text_doc.uri)
        _delete_from_ctx(text_doc)

    for event in params.changes:
        if event.type == lsp.FileChangeType.Created:
            yang_file = to_fs_path(event.uri)
            assert yang_file
            with open(yang_file, 'r') as file:
                yang_source = file.read()
                file.close()
            ls.workspace.put_text_document(
                lsp.TextDocumentItem(
                    uri=event.uri,
                    language_id='yang',
                    version=0,
                    text=yang_source,
                )
            )
        elif event.type == lsp.FileChangeType.Changed:
            text_doc = ls.workspace.get_text_document(event.uri)
            text_doc._source = None

    _update_ctx_modules()
    _validate_ctx_modules()
    _publish_workspace_diagnostics()


@pyangls.feature(
    lsp.TEXT_DOCUMENT_DIAGNOSTIC,
    lsp.DiagnosticOptions(
        identifier=SERVER_NAME,
        inter_file_dependencies=True,
        workspace_diagnostics=True,
    ),
)
def text_document_diagnostic(
    params: lsp.DocumentDiagnosticParams,
) -> lsp.DocumentDiagnosticReport:
    """Returns diagnostic report."""
    # pyangls.show_message("Received Text Document Diagnostic")
    if pyangls.client_capabilities.text_document is None or \
        pyangls.client_capabilities.text_document.diagnostic is None:
        pyangls.show_message("Unexpected textDocument/diagnostic from incapable client.")
    text_doc = pyangls.workspace.get_text_document(params.text_document.uri)
    doc_items = _build_doc_diagnostics(text_doc.path)
    if doc_items is None:
        items = []
    else:
        items = doc_items
    # TODO: check if there are any errors which provide related diagnostics
    return lsp.RelatedFullDocumentDiagnosticReport(
        items=items,
    )


@pyangls.feature(lsp.WORKSPACE_DIAGNOSTIC)
def workspace_diagnostic(
    params: lsp.WorkspaceDiagnosticParams,
) -> lsp.WorkspaceDiagnosticReport:
    """Returns diagnostic report."""
    # pyangls.show_message("Received Workspace Diagnostic")
    if pyangls.client_capabilities.text_document is None or \
        pyangls.client_capabilities.text_document.diagnostic is None:
        pyangls.show_message("Unexpected workspace/diagnostic from incapable client.")

    items : List[lsp.WorkspaceDocumentDiagnosticReport] = []
    for text_doc_uri in pyangls.workspace.text_documents.keys():
        text_doc = pyangls.workspace.get_text_document(text_doc_uri)
        doc_items = _build_doc_diagnostics(text_doc.path)
        if doc_items is not None:
            items.append(
                lsp.WorkspaceFullDocumentDiagnosticReport(
                    uri=text_doc.uri,
                    version=text_doc.version,
                    items=doc_items,
                    kind=lsp.DocumentDiagnosticReportKind.Full,
                )
            )

    return lsp.WorkspaceDiagnosticReport(items=items)


# pyang supports LSP TextDocumentSyncKind Full but not Incremental
# The mapping is provided via initialization parameters of pygls LanguageServer
@pyangls.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
def did_change(
    ls: LanguageServer,
    params: lsp.DidChangeTextDocumentParams
):
    """Text document did change notification."""
    # ls.show_message("Received Text Document Did Change")
    _clear_ctx_validation()
    for content_change in params.content_changes:
        ls.workspace.update_text_document(params.text_document, content_change)

    _update_ctx_modules()
    _validate_ctx_modules()
    _publish_workspace_diagnostics()


@pyangls.feature(lsp.TEXT_DOCUMENT_DID_CLOSE)
def did_close(
    ls: PyangLanguageServer,
    params: lsp.DidCloseTextDocumentParams
):
    """Text document did close notification."""
    # ls.show_message("Received Text Document Did Close")
    _clear_ctx_validation()
    text_doc = ls.workspace.get_text_document(params.text_document.uri)
    # Force file read on next source access
    text_doc._source = None

    _update_ctx_modules()
    _validate_ctx_modules()
    _publish_workspace_diagnostics()


@pyangls.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
def did_open(
    ls: LanguageServer,
    params: lsp.DidOpenTextDocumentParams
):
    """Text document did open notification."""
    # ls.show_message("Received Text Document Did Open")
    text_doc = ls.workspace.get_text_document(params.text_document.uri)
    # Prevent direct file read on next TextDocument.source access
    text_doc._source = params.text_document.text
    # Keep Eglot+Flymake happy... without this buffer diagnostics are not shown
    # in the mode-line even though diagnostics for the file is reported earlier
    # via _publish_workspace_diagnostics
    _publish_doc_diagnostics(text_doc)


@pyangls.feature(lsp.TEXT_DOCUMENT_FORMATTING)
def formatting(
    ls: LanguageServer,
    params: lsp.DocumentFormattingParams
):
    """Text document formatting."""
    # ls.show_message("Received Text Document Formatting")
    text_doc = ls.workspace.get_text_document(params.text_document.uri)
    source = text_doc.source

    if source is None:
        ls.show_message("No source found")
        return []

    module = _update_ctx_module(text_doc)
    if module is None:
        if _have_parser_errors():
            ls.show_message("Document was syntactically invalid. Did not format.")
        return []

    _validate_ctx_modules()

    fmt_text=_format_yang(source, params.options, module)

    start_pos = lsp.Position(line=0, character=0)
    end_pos = lsp.Position(line=len(text_doc.lines), character=0)
    text_range = lsp.Range(start=start_pos, end=end_pos)

    return [lsp.TextEdit(range=text_range, new_text=fmt_text)]
