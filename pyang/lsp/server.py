"""pyang LSP handling"""

from __future__ import absolute_import
import optparse
import tempfile
from pathlib import Path
from typing import Union

from pyang import error
from pyang import context
from pyang import plugin
from pyang import syntax
from pyang.translators import yang

from lsprotocol import types as lsp
from pygls.server import LanguageServer

import importlib
ext_deps = ['lsprotocol.types', 'pygls.server']
def try_import_deps():
    """Throws ModuleNotFoundError if external module dependencies are missing"""
    for dep in ext_deps:
        importlib.import_module(dep)

SERVER_NAME = "pyangls"
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

class PyangLanguageServer(LanguageServer):
    def __init__(self, *args):
        self.ctx : context.Context
        self.yangfmt : yang.YANGPlugin
        super().__init__(*args)

pyangls = PyangLanguageServer(SERVER_NAME, SERVER_VERSION)

def _validate(ls: LanguageServer,
              params: Union[lsp.DidChangeTextDocumentParams,
                            lsp.DidOpenTextDocumentParams,
                            lsp.DocumentDiagnosticParams]):
    ls.show_message_log("Validating YANG...")

    text_doc = ls.workspace.get_text_document(params.text_document.uri)

    pyangls.ctx.errors = []
    diagnostics = []
    if text_doc.source:
        _validate_yang(text_doc)

        diagnostics = _build_diagnostics()

    ls.publish_diagnostics(text_doc.uri, diagnostics)

def _validate_yang(text_doc):
    modules = []
    m = syntax.re_filename.search(Path(text_doc.filename).name)
    if m is not None:
        name, rev, in_format = m.groups()
        module = pyangls.ctx.get_module(name, rev)
        if module is not None:
            pyangls.ctx.del_module(module)
        module = pyangls.ctx.add_module(text_doc.path, text_doc.source,
                                        in_format, name, rev,
                                        expect_failure_error=False,
                                        primary_module=True)
    else:
        module = pyangls.ctx.add_module(text_doc.path, text_doc.source,
                                        primary_module=True)
    if module is not None:
        modules.append(module)
        p : plugin.PyangPlugin
        for p in plugin.plugins:
            p.pre_validate_ctx(pyangls.ctx, modules)
        pyangls.ctx.validate()
        module.prune()
        for p in plugin.plugins:
            p.post_validate_ctx(pyangls.ctx, modules)
        pyangls.ctx.errors.sort(key=lambda e: (e[0].ref, e[0].line),
                                reverse=True)

    return module


def _build_diagnostics():
    """Builds lsp diagnostics from pyang context"""
    diagnostics = []

    for epos, etag, eargs in pyangls.ctx.errors:
        msg = error.err_to_str(etag, eargs)
        # pyang just stores line context, not keyword/argument context
        start_line = epos.line - 1
        start_col = 0
        end_line = epos.line - 1
        end_col = 1
        def level_to_severity(level):
            if level == 1 or level == 2:
                return lsp.DiagnosticSeverity.Error
            elif level == 3:
                return lsp.DiagnosticSeverity.Warning
            elif level == 4:
                return lsp.DiagnosticSeverity.Information
            else:
                return None
        d = lsp.Diagnostic(
            range=lsp.Range(
                start=lsp.Position(line=start_line, character=start_col),
                end=lsp.Position(line=end_line, character=end_col),
            ),
            message=msg,
            severity=level_to_severity(error.err_level(etag)),
            code=etag,
            source=SERVER_NAME,
        )

        diagnostics.append(d)

    return diagnostics


@pyangls.feature(
    lsp.TEXT_DOCUMENT_DIAGNOSTIC,
    lsp.DiagnosticOptions(
        identifier="pyangls",
        inter_file_dependencies=True,
        workspace_diagnostics=True,
    ),
)
def text_document_diagnostic(
    params: lsp.DocumentDiagnosticParams,
) -> lsp.DocumentDiagnosticReport:
    """Returns diagnostic report."""
    return lsp.RelatedFullDocumentDiagnosticReport(
        items=_validate(pyangls, params),
        kind=lsp.DocumentDiagnosticReportKind.Full,
    )


@pyangls.feature(lsp.WORKSPACE_DIAGNOSTIC)
def workspace_diagnostic(
    params: lsp.WorkspaceDiagnosticParams,
) -> lsp.WorkspaceDiagnosticReport:
    """Returns diagnostic report."""
    documents = pyangls.workspace.text_documents.keys()

    if len(documents) == 0:
        items = []
    else:
        first = list(documents)[0]
        document = pyangls.workspace.get_text_document(first)
        items = [
            lsp.WorkspaceFullDocumentDiagnosticReport(
                uri=document.uri,
                version=document.version,
                items=_validate(pyangls, params),
                kind=lsp.DocumentDiagnosticReportKind.Full,
            )
        ]

    return lsp.WorkspaceDiagnosticReport(items=items)


@pyangls.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: LanguageServer, params: lsp.DidChangeTextDocumentParams):
    """Text document did change notification."""

    _validate(ls, params)


@pyangls.feature(lsp.TEXT_DOCUMENT_DID_CLOSE)
def did_close(ls: PyangLanguageServer, params: lsp.DidCloseTextDocumentParams):
    """Text document did close notification."""
    ls.show_message("Text Document Did Close")


@pyangls.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: LanguageServer, params: lsp.DidOpenTextDocumentParams):
    """Text document did open notification."""
    ls.show_message("Text Document Did Open")
    _validate(ls, params)


@pyangls.feature(lsp.TEXT_DOCUMENT_FORMATTING)
def formatting(ls: LanguageServer, params: lsp.DocumentFormattingParams):
    """Text document formatting."""
    ls.show_message("Text Document Formatting")
    text_doc = ls.workspace.get_text_document(params.text_document.uri)
    source = text_doc.source

    if source:
        module = _validate_yang(text_doc)
    else:
        ls.show_message("No text_doc.source found")
        return []

    opts = params.options
    if opts.insert_spaces == False:
        ls.log_trace("insert_spaces is currently restricted to True")
    if opts.tab_size:
        pyangls.ctx.opts.yang_indent_size = opts.tab_size
    if opts.trim_trailing_whitespace == False:
        ls.log_trace("trim_trailing_whitespace is currently restricted to True")
    if opts.trim_final_newlines == False:
        ls.log_trace("trim_final_newlines is currently restricted to True")
    pyangls.ctx.opts.yang_canonical = True
    pyangls.ctx.opts.yang_line_length = 80
    pyangls.ctx.opts.yang_remove_unused_imports = False
    pyangls.ctx.opts.yang_remove_comments = False

    pyangls.yangfmt.setup_fmt(pyangls.ctx)
    tmpfd = tempfile.TemporaryFile(mode="w+", encoding="utf-8")

    pyangls.yangfmt.emit(pyangls.ctx, [module], tmpfd)

    tmpfd.seek(0)
    fmt_text = tmpfd.read()
    tmpfd.close()

    # pyang only supports unix file endings and inserts a final one if missing
    if not opts.insert_final_newline and not source.endswith('\n'):
        fmt_text.rstrip('\n')

    start_pos = lsp.Position(line=0, character=0)
    end_pos = lsp.Position(line=len(text_doc.lines), character=0)
    text_range = lsp.Range(start=start_pos, end=end_pos)

    return [lsp.TextEdit(range=text_range, new_text=fmt_text)]


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
