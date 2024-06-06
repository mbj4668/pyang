#!/usr/bin/env python

"""pyang Test LSP Client"""

import asyncio
import json
import logging
import os
import shutil
import sys
import traceback
from typing import List
from pygls.lsp.client import BaseLanguageClient
from lsprotocol import types as lsp
from pygls.uris import from_fs_path, to_fs_path
from pygls.exceptions import PyglsError, JsonRpcException

CLIENT_NAME = 'pyangtlc'
CLIENT_VERSION = 'v0.1'

EDIT_FOLDER = 'edit'
WORKSPACE_FOLDER = 'workspace'
EXPECTATION_FOLDER = 'expect'

class PyangTestLanguageClient(BaseLanguageClient):
    def _build_workspace(self, folder) -> List[str]:
        yang_files = []
        for root, _, files in os.walk(folder):
            for file in files:
                if file.endswith(".yang"):
                    yang_files.append(os.path.join(os.path.realpath('.'),
                                                   os.path.join(root, file)))
        return yang_files

    def handle_server_error(
        self,
        error: Exception,
        source: PyglsError | JsonRpcException
    ) -> None:
        logger.info(error)
        logger.info(source)

    async def handle_server_exit(
        self,
        server: asyncio.subprocess.Process,
    ) -> None:
        logger.info(server)

    def __init__(self):
        self.workspace = self._build_workspace(WORKSPACE_FOLDER)
        self.test_step : int = 0
        self.report_server_error = self.handle_server_error
        self.server_exit = self.handle_server_exit
        super().__init__(
            name=CLIENT_NAME,
            version=CLIENT_VERSION
        )

pyangtlc = PyangTestLanguageClient()

logger = logging.getLogger()

def _ensure_server_capabilities(caps: lsp.ServerCapabilities):
    """Ensure reported capabilities have expected content"""

    # Ordered by pygls generated jsonrpc result sequence

    assert caps.position_encoding == lsp.PositionEncodingKind.Utf16

    assert caps.text_document_sync is not None
    assert type(caps.text_document_sync) is lsp.TextDocumentSyncOptions
    assert caps.text_document_sync.open_close
    assert caps.text_document_sync.change == lsp.TextDocumentSyncKind.Full
    assert not caps.text_document_sync.will_save
    assert not caps.text_document_sync.will_save_wait_until
    assert not caps.text_document_sync.save

    assert caps.document_formatting_provider

    assert caps.execute_command_provider is not None
    assert not caps.execute_command_provider.commands

    assert caps.diagnostic_provider is not None
    assert caps.diagnostic_provider.inter_file_dependencies
    assert caps.diagnostic_provider.workspace_diagnostics
    assert caps.diagnostic_provider.identifier == 'pyang'

    assert caps.workspace is not None
    assert caps.workspace.workspace_folders is not None
    assert caps.workspace.workspace_folders.supported
    assert caps.workspace.workspace_folders.change_notifications
    assert caps.workspace.file_operations
    assert caps.workspace.file_operations.did_create is None
    assert caps.workspace.file_operations.did_delete is None
    assert caps.workspace.file_operations.did_rename is None
    assert caps.workspace.file_operations.will_create is None
    assert caps.workspace.file_operations.will_delete is None
    assert caps.workspace.file_operations.will_rename is None

def _ensure_server_incapabilities(caps: lsp.ServerCapabilities):
    """Ensure incapabilies are not reported at all"""

    # Ordered alphabetically
    assert caps.call_hierarchy_provider is None
    assert caps.code_action_provider is None
    assert caps.code_lens_provider is None
    assert caps.color_provider is None
    assert caps.completion_provider is None
    assert caps.declaration_provider is None
    assert caps.definition_provider is None
    assert caps.document_highlight_provider is None
    assert caps.document_link_provider is None
    assert caps.document_link_provider is None
    assert caps.document_on_type_formatting_provider is None
    assert caps.document_range_formatting_provider is None
    assert caps.document_symbol_provider is None
    assert caps.experimental is None
    assert caps.folding_range_provider is None
    assert caps.hover_provider is None
    assert caps.implementation_provider is None
    assert caps.inlay_hint_provider is None
    assert caps.inline_completion_provider is None
    assert caps.inline_value_provider is None
    assert caps.linked_editing_range_provider is None
    assert caps.moniker_provider is None
    assert caps.notebook_document_sync is None
    assert caps.references_provider is None
    assert caps.rename_provider is None
    assert caps.selection_range_provider is None
    assert caps.semantic_tokens_provider is None
    assert caps.signature_help_provider is None
    assert caps.type_definition_provider is None
    assert caps.type_hierarchy_provider is None
    assert caps.workspace_symbol_provider is None

def _validate_initialize_result(result: lsp.InitializeResult):
    """Validate `initialize` result"""

    logger.info("Received initialize result. Validating...")

    caps = result.capabilities
    _ensure_server_capabilities(caps)
    _ensure_server_incapabilities(caps)

    assert result.server_info is not None
    assert result.server_info.name == 'pyang'
    assert result.server_info.version == 'v0.1'

    logger.info("Valid initialize result!")

def _validate_diagnostics(
    diagnostics: List[lsp.Diagnostic],
    exp_filepath: str
):
    with open(exp_filepath) as exp_file:
        exp_json = json.load(exp_file)
        exp_items = exp_json['items']
        try:
            assert len(diagnostics) == len(exp_items)
            i = 0
            for exp_item in exp_items:
                diagnostic = diagnostics[i]
                range = diagnostic.range
                exp_start = exp_item['range']['start']
                exp_end = exp_item['range']['end']
                assert range.start.line == exp_start['line']
                assert range.start.character == exp_start['character']
                assert range.end.line == exp_end['line']
                assert range.end.character == exp_end['character']
                assert diagnostic.message == exp_item['message']
                assert diagnostic.severity == exp_item['severity']
                assert diagnostic.code == exp_item['code']
                assert diagnostic.source == exp_item['source']
                exp_tags = exp_item['tags']
                if exp_tags:
                    assert diagnostic.tags
                    assert len(diagnostic.tags) == len(exp_tags)
                    j = 0
                    for exp_tag in exp_tags:
                        tag = diagnostic.tags[j]
                        assert tag == exp_tag
                        j += 1
                else:
                    assert not diagnostic.tags
                exp_rel_infos = exp_item['relatedInformation']
                if exp_rel_infos:
                    assert diagnostic.related_information
                    assert len(diagnostic.related_information) == len(exp_rel_infos)
                    j = 0
                    for exp_rel_info in exp_rel_infos:
                        rel_info = diagnostic.related_information[j]
                        uri = rel_info.location.uri
                        assert uri == exp_rel_info['location']['uri']
                        range = rel_info.location.range
                        exp_start = exp_rel_info['location']['range']['start']
                        exp_end = exp_rel_info['location']['range']['end']
                        assert range.start.line == exp_start['line']
                        assert range.start.character == exp_start['character']
                        assert range.end.line == exp_end['line']
                        assert range.end.character == exp_end['character']
                        assert rel_info.message == exp_rel_info['message']
                        j += 1
                else:
                    assert not diagnostic.related_information
                i += 1
        except Exception as exc:
            exp_file.close()
            raise exc
    exp_file.close()

@pyangtlc.feature('window/logMessage')
async def window_log_message(ls, params: lsp.LogMessageParams):
    logging.info("Received window/logMessage: %s", params.message)

@pyangtlc.feature('window/showMessage')
async def window_show_message(ls, params: lsp.ShowMessageParams):
    logging.info("Received window/showMessage: %s", params.message)

def _file_in_workspace(uri: str) -> bool:
    return to_fs_path(uri) in pyangtlc.workspace

def _expected_diagnostics_filepath(uri: str) -> str:
    fs_path = to_fs_path(uri)
    assert fs_path is not None
    exp_root, _ = os.path.splitext(fs_path)
    exp_filename = os.path.basename(exp_root) + '.json'
    return os.path.join(EXPECTATION_FOLDER, str(pyangtlc.test_step), exp_filename)

@pyangtlc.feature('textDocument/publishDiagnostics')
async def document_publish_diagnostics(ls, params: lsp.PublishDiagnosticsParams):
    logging.info("Received textDocument/publishDiagnostics %s. Validating...", params.uri)
    assert _file_in_workspace(params.uri)
    try:
        exp_diag_file = _expected_diagnostics_filepath(params.uri)
        _validate_diagnostics(params.diagnostics, exp_diag_file)
    except Exception:
        traceback.print_exc()
        logger.error("Invalid textDocument/publishDiagnostics! %s", params.uri)
        sys.exit(1)

    logger.info("Valid textDocument/publishDiagnostics %s!", params.uri)

async def test_generic():
    await asyncio.wait_for(
        pyangtlc.start_io('pyang','--lsp'),
        timeout=2.0
    )

    pyangtlc.test_step = 1

    test_doc = 'test-a.yang'
    test_doc_path = os.path.join(os.path.realpath(WORKSPACE_FOLDER), test_doc)
    doc_uri = from_fs_path(test_doc_path)
    assert doc_uri is not None
    with open(test_doc_path) as test_fd:
        doc_source = test_fd.read()
        test_fd.close()

    def prepare_client_capabilities() -> lsp.ClientCapabilities:
        """Prepare reference client capabilities based on a generic LSP 3.17 client"""

        execute_command_caps = lsp.ExecuteCommandClientCapabilities(
            dynamic_registration=False,
        )
        workspace_edit_caps = lsp.WorkspaceEditClientCapabilities(
            document_changes=True,
        )
        did_change_watched_files_caps = lsp.DidChangeWatchedFilesClientCapabilities(
            dynamic_registration=True,
        )
        symbol_caps = lsp.WorkspaceSymbolClientCapabilities(
            dynamic_registration=False,
        )
        workspace_caps = lsp.WorkspaceClientCapabilities(
            apply_edit=True,
            execute_command=execute_command_caps,
            workspace_edit=workspace_edit_caps,
            did_change_watched_files=did_change_watched_files_caps,
            symbol=symbol_caps,
            configuration=True,
            workspace_folders=True,
        )

        synchronization_caps = lsp.TextDocumentSyncClientCapabilities(
            dynamic_registration=False,
            will_save=True,
            will_save_wait_until=True,
            did_save=True,
        )
        completion_item_resolve_support_caps = lsp.CompletionClientCapabilitiesCompletionItemTypeResolveSupportType(
            [
                'documentation',
                'details',
                'additionalTextEdits'
            ]
        )
        completion_item_tag_support_caps = lsp.CompletionClientCapabilitiesCompletionItemTypeTagSupportType(
            [
                lsp.CompletionItemTag.Deprecated
            ]
        )
        completion_item_caps = lsp.CompletionClientCapabilitiesCompletionItemType(
            snippet_support=True,
            deprecated_support=True,
            resolve_support=completion_item_resolve_support_caps,
            tag_support=completion_item_tag_support_caps,
        )
        completion_caps = lsp.CompletionClientCapabilities(
            dynamic_registration=False,
            completion_item=completion_item_caps,
            context_support=True,
        )
        content_format_caps = [
            lsp.MarkupKind.Markdown,
            lsp.MarkupKind.PlainText,
        ]
        hover_caps = lsp.HoverClientCapabilities(
            dynamic_registration=False,
            content_format=content_format_caps,
        )
        parameter_information_caps = lsp.SignatureHelpClientCapabilitiesSignatureInformationTypeParameterInformationType(
            label_offset_support=True,
        )
        document_format_caps = [
            lsp.MarkupKind.Markdown,
            lsp.MarkupKind.PlainText,
        ]
        signature_information_caps = lsp.SignatureHelpClientCapabilitiesSignatureInformationType(
            parameter_information=parameter_information_caps,
            documentation_format=document_format_caps,
            active_parameter_support=True,
        )
        signature_help_caps = lsp.SignatureHelpClientCapabilities(
            dynamic_registration=False,
            signature_information=signature_information_caps,
        )
        references_caps = lsp.ReferenceClientCapabilities(
            dynamic_registration=False,
        )
        definition_caps = lsp.DefinitionClientCapabilities(
            dynamic_registration=False,
            link_support=True,
        )
        declaration_caps = lsp.DeclarationClientCapabilities(
            dynamic_registration=False,
            link_support=True,
        )
        implementation_caps = lsp.ImplementationClientCapabilities(
            dynamic_registration=False,
            link_support=True,
        )
        type_definition_caps = lsp.TypeDefinitionClientCapabilities(
            dynamic_registration=False,
            link_support=True,
        )
        symbol_kind_caps = lsp.DocumentSymbolClientCapabilitiesSymbolKindType(
            [
                lsp.SymbolKind.File,
                lsp.SymbolKind.Module,
                lsp.SymbolKind.Namespace,
                lsp.SymbolKind.Package,
                lsp.SymbolKind.Class,
                lsp.SymbolKind.Method,
                lsp.SymbolKind.Property,
                lsp.SymbolKind.Field,
                lsp.SymbolKind.Constructor,
                lsp.SymbolKind.Enum,
                lsp.SymbolKind.Interface,
                lsp.SymbolKind.Function,
                lsp.SymbolKind.Variable,
                lsp.SymbolKind.Constant,
                lsp.SymbolKind.String,
                lsp.SymbolKind.Number,
                lsp.SymbolKind.Boolean,
                lsp.SymbolKind.Array,
                lsp.SymbolKind.Object,
                lsp.SymbolKind.Key,
                lsp.SymbolKind.Null,
                lsp.SymbolKind.EnumMember,
                lsp.SymbolKind.Struct,
                lsp.SymbolKind.Event,
                lsp.SymbolKind.Operator,
                lsp.SymbolKind.TypeParameter,
            ]
        )
        document_symbol_caps = lsp.DocumentSymbolClientCapabilities(
            dynamic_registration=False,
            hierarchical_document_symbol_support=True,
            symbol_kind=symbol_kind_caps,
        )
        document_highlight_caps = lsp.DocumentHighlightClientCapabilities(
            dynamic_registration=False,
        )
        code_action_resolve_support_caps = lsp.CodeActionClientCapabilitiesResolveSupportType(
            [
                'edit',
                'command'
            ]
        )
        code_action_kind_caps = lsp.CodeActionClientCapabilitiesCodeActionLiteralSupportTypeCodeActionKindType(
            value_set=[
                lsp.CodeActionKind.QuickFix,
                lsp.CodeActionKind.Refactor,
                lsp.CodeActionKind.RefactorExtract,
                lsp.CodeActionKind.RefactorInline,
                lsp.CodeActionKind.RefactorRewrite,
                lsp.CodeActionKind.Source,
                lsp.CodeActionKind.SourceOrganizeImports,
            ]
        )
        code_action_literal_support_caps = lsp.CodeActionClientCapabilitiesCodeActionLiteralSupportType(
            code_action_kind=code_action_kind_caps,
        )
        code_action_caps = lsp.CodeActionClientCapabilities(
            dynamic_registration=False,
            resolve_support=code_action_resolve_support_caps,
            data_support=True,
            code_action_literal_support=code_action_literal_support_caps,
            is_preferred_support=True,
        )
        formatting_caps = lsp.DocumentFormattingClientCapabilities(
            dynamic_registration=False,
        )
        range_formatting_caps = lsp.DocumentRangeFormattingClientCapabilities(
            dynamic_registration=False,
        )
        rename_caps = lsp.RenameClientCapabilities(
            dynamic_registration=False,
        )
        inlay_hint_caps = lsp.InlayHintClientCapabilities(
            dynamic_registration=False,
        )
        publish_diagnostics_tag_support_caps = lsp.PublishDiagnosticsClientCapabilitiesTagSupportType(
            [
                lsp.DiagnosticTag.Unnecessary,
                lsp.DiagnosticTag.Deprecated,
            ]
        )
        publish_diagnostics_caps = lsp.PublishDiagnosticsClientCapabilities(
            related_information=False,
            code_description_support=False,
            tag_support=publish_diagnostics_tag_support_caps,
        )
        diagnostic_caps = lsp.DiagnosticClientCapabilities(
            dynamic_registration=False,
            related_document_support=True,
        )
        text_document_caps = lsp.TextDocumentClientCapabilities(
            synchronization=synchronization_caps,
            completion=completion_caps,
            hover=hover_caps,
            signature_help=signature_help_caps,
            references=references_caps,
            definition=definition_caps,
            declaration=declaration_caps,
            implementation=implementation_caps,
            type_definition=type_definition_caps,
            document_symbol=document_symbol_caps,
            document_highlight=document_highlight_caps,
            code_action=code_action_caps,
            formatting=formatting_caps,
            range_formatting=range_formatting_caps,
            rename=rename_caps,
            inlay_hint=inlay_hint_caps,
            publish_diagnostics=publish_diagnostics_caps,
            diagnostic=diagnostic_caps,
        )

        show_document_caps = lsp.ShowDocumentClientCapabilities(
            support=True,
        )
        window_caps = lsp.WindowClientCapabilities(
            show_document=show_document_caps,
            work_done_progress=True,
        )

        position_encoding_caps = [
            lsp.PositionEncodingKind.Utf32,
            lsp.PositionEncodingKind.Utf8,
            lsp.PositionEncodingKind.Utf16,
        ]

        general_caps = lsp.GeneralClientCapabilities(
            position_encodings=position_encoding_caps, # type: ignore
        )

        return lsp.ClientCapabilities(
            workspace=workspace_caps,
            text_document=text_document_caps,
            window=window_caps,
            general=general_caps,
        )

    client_capabilities = prepare_client_capabilities()

    client_info = lsp.InitializeParamsClientInfoType(
        name=CLIENT_NAME,
        version=CLIENT_VERSION,
    )

    root_path = os.path.realpath(WORKSPACE_FOLDER)
    root_uri = from_fs_path(root_path)
    assert root_uri is not None
    workspace_folders = [
        lsp.WorkspaceFolder(
            uri=root_uri,
            name=os.path.basename(root_path)
        )
    ]

    initialize_params = lsp.InitializeParams(
        capabilities=client_capabilities,
        client_info=client_info,
        root_path=root_path,
        root_uri=root_uri,
        workspace_folders=workspace_folders,
    )

    initialize_result = await asyncio.wait_for(
        pyangtlc.initialize_async(
            params=initialize_params,
        ),
        timeout=2.0
    )
    _validate_initialize_result(initialize_result)

    did_change_configuration_params = lsp.DidChangeConfigurationParams(
        settings=None,
    )
    pyangtlc.workspace_did_change_configuration(
        params=did_change_configuration_params
    )

    # Allow textDocument/publishDiagnostics to arrive and be validated in sequence
    # TODO: Should be done in a deterministic way
    await asyncio.sleep(0.5)

    workspace_diagnostic_params = lsp.WorkspaceDiagnosticParams(
        previous_result_ids=[],
    )
    def validate_workspace_diagnostic_result(result: lsp.WorkspaceDiagnosticReport):
        """Validate `workspace/diagnostic` result"""

        logger.info("Received workspace/diagnostic result. Validating...")
        for item in result.items:
            assert item.kind == lsp.DocumentDiagnosticReportKind.Full
            _validate_diagnostics(item.items, _expected_diagnostics_filepath(item.uri)) # type: ignore
            logger.info("Valid workspace/diagnostic result %s!", item.uri)
    workspace_diagnostic_result = await asyncio.wait_for(
        pyangtlc.workspace_diagnostic_async(
            params=workspace_diagnostic_params,
        ),
        timeout=1.0
    )
    validate_workspace_diagnostic_result(workspace_diagnostic_result)

    document_diagnostic_params = lsp.DocumentDiagnosticParams(
        text_document=lsp.TextDocumentIdentifier(
            uri=doc_uri
        ),
    )
    def validate_document_diagnostic_result(result: lsp.RelatedFullDocumentDiagnosticReport
                                            | lsp.RelatedUnchangedDocumentDiagnosticReport):
        """Validate `textDocument/diagnostic` result"""

        logger.info("Received textDocument/diagnostic result. Validating...")
        assert result.kind == lsp.DocumentDiagnosticReportKind.Full
        diagnostics = result.items # type: ignore
        try:
            _validate_diagnostics(diagnostics, _expected_diagnostics_filepath(doc_uri))
        except AssertionError as err:
            traceback.print_exc()
            logger.error("Invalid textDocument/diagnostic result! " + str(err))
            sys.exit(1)

        logger.info("Valid textDocument/diagnostic result %s!", doc_uri)
    document_diagnostic_result = await asyncio.wait_for(
        pyangtlc.text_document_diagnostic_async(
            params=document_diagnostic_params,
        ),
        timeout=1.0
    )
    validate_document_diagnostic_result(document_diagnostic_result)

    document_formatting_params = lsp.DocumentFormattingParams(
        text_document=lsp.TextDocumentIdentifier(
            uri=doc_uri
        ),
        options=lsp.FormattingOptions(
            tab_size=4,
            insert_spaces=True
        ),
    )
    def validate_document_formatting_result(result: List[lsp.TextEdit] | None):
        """Validate `textDocument/formatting` result"""

        logger.info("Received textDocument/formatting result. Validating...")
        assert result
        assert len(result) == 1
        fmt_text = result[0].new_text
        # logger.debug("Received formatted text:\n" + fmt_text)
        exp_file = open('expect/test-a.yang')
        exp_text = exp_file.read()
        exp_file.close()
        assert fmt_text == exp_text
        logger.info("Valid textDocument/formatting result!")
    document_formatting_result = await asyncio.wait_for(
        pyangtlc.text_document_formatting_async(
            params=document_formatting_params,
        ),
        timeout=1.0
    )
    validate_document_formatting_result(document_formatting_result)

    await asyncio.wait_for(
        pyangtlc.shutdown_async(
            params=None
        ),
        timeout=1.0
    )

    pyangtlc.exit(
        params=None
    )

async def test_eglot():
    await asyncio.wait_for(
        pyangtlc.start_io('pyang','--lsp'),
        timeout=2.0
    )

    pyangtlc.test_step = 0

    def prepare_client_capabilities() -> lsp.ClientCapabilities:
        """Prepare reference client capabilities based on GNU Emacs Eglot 1.17"""

        execute_command_caps = lsp.ExecuteCommandClientCapabilities(
            dynamic_registration=False,
        )
        workspace_edit_caps = lsp.WorkspaceEditClientCapabilities(
            document_changes=True,
        )
        did_change_watched_files_caps = lsp.DidChangeWatchedFilesClientCapabilities(
            dynamic_registration=True,
        )
        symbol_caps = lsp.WorkspaceSymbolClientCapabilities(
            dynamic_registration=False,
        )
        workspace_caps = lsp.WorkspaceClientCapabilities(
            apply_edit=True,
            execute_command=execute_command_caps,
            workspace_edit=workspace_edit_caps,
            did_change_watched_files=did_change_watched_files_caps,
            symbol=symbol_caps,
            configuration=True,
            workspace_folders=True,
        )

        synchronization_caps = lsp.TextDocumentSyncClientCapabilities(
            dynamic_registration=False,
            will_save=True,
            will_save_wait_until=True,
            did_save=True,
        )
        completion_item_resolve_support_caps = lsp.CompletionClientCapabilitiesCompletionItemTypeResolveSupportType(
            [
                'documentation',
                'details',
                'additionalTextEdits'
            ]
        )
        completion_item_tag_support_caps = lsp.CompletionClientCapabilitiesCompletionItemTypeTagSupportType(
            [
                lsp.CompletionItemTag.Deprecated
            ]
        )
        completion_item_caps = lsp.CompletionClientCapabilitiesCompletionItemType(
            snippet_support=True,
            deprecated_support=True,
            resolve_support=completion_item_resolve_support_caps,
            tag_support=completion_item_tag_support_caps,
        )
        completion_caps = lsp.CompletionClientCapabilities(
            dynamic_registration=False,
            completion_item=completion_item_caps,
            context_support=True,
        )
        content_format_caps = [
            lsp.MarkupKind.Markdown,
            lsp.MarkupKind.PlainText,
        ]
        hover_caps = lsp.HoverClientCapabilities(
            dynamic_registration=False,
            content_format=content_format_caps,
        )
        parameter_information_caps = lsp.SignatureHelpClientCapabilitiesSignatureInformationTypeParameterInformationType(
            label_offset_support=True,
        )
        document_format_caps = [
            lsp.MarkupKind.Markdown,
            lsp.MarkupKind.PlainText,
        ]
        signature_information_caps = lsp.SignatureHelpClientCapabilitiesSignatureInformationType(
            parameter_information=parameter_information_caps,
            documentation_format=document_format_caps,
            active_parameter_support=True,
        )
        signature_help_caps = lsp.SignatureHelpClientCapabilities(
            dynamic_registration=False,
            signature_information=signature_information_caps,
        )
        references_caps = lsp.ReferenceClientCapabilities(
            dynamic_registration=False,
        )
        definition_caps = lsp.DefinitionClientCapabilities(
            dynamic_registration=False,
            link_support=True,
        )
        declaration_caps = lsp.DeclarationClientCapabilities(
            dynamic_registration=False,
            link_support=True,
        )
        implementation_caps = lsp.ImplementationClientCapabilities(
            dynamic_registration=False,
            link_support=True,
        )
        type_definition_caps = lsp.TypeDefinitionClientCapabilities(
            dynamic_registration=False,
            link_support=True,
        )
        symbol_kind_caps = lsp.DocumentSymbolClientCapabilitiesSymbolKindType(
            [
                lsp.SymbolKind.File,
                lsp.SymbolKind.Module,
                lsp.SymbolKind.Namespace,
                lsp.SymbolKind.Package,
                lsp.SymbolKind.Class,
                lsp.SymbolKind.Method,
                lsp.SymbolKind.Property,
                lsp.SymbolKind.Field,
                lsp.SymbolKind.Constructor,
                lsp.SymbolKind.Enum,
                lsp.SymbolKind.Interface,
                lsp.SymbolKind.Function,
                lsp.SymbolKind.Variable,
                lsp.SymbolKind.Constant,
                lsp.SymbolKind.String,
                lsp.SymbolKind.Number,
                lsp.SymbolKind.Boolean,
                lsp.SymbolKind.Array,
                lsp.SymbolKind.Object,
                lsp.SymbolKind.Key,
                lsp.SymbolKind.Null,
                lsp.SymbolKind.EnumMember,
                lsp.SymbolKind.Struct,
                lsp.SymbolKind.Event,
                lsp.SymbolKind.Operator,
                lsp.SymbolKind.TypeParameter,
            ]
        )
        document_symbol_caps = lsp.DocumentSymbolClientCapabilities(
            dynamic_registration=False,
            hierarchical_document_symbol_support=True,
            symbol_kind=symbol_kind_caps,
        )
        document_highlight_caps = lsp.DocumentHighlightClientCapabilities(
            dynamic_registration=False,
        )
        code_action_resolve_support_caps = lsp.CodeActionClientCapabilitiesResolveSupportType(
            [
                'edit',
                'command'
            ]
        )
        code_action_kind_caps = lsp.CodeActionClientCapabilitiesCodeActionLiteralSupportTypeCodeActionKindType(
            value_set=[
                lsp.CodeActionKind.QuickFix,
                lsp.CodeActionKind.Refactor,
                lsp.CodeActionKind.RefactorExtract,
                lsp.CodeActionKind.RefactorInline,
                lsp.CodeActionKind.RefactorRewrite,
                lsp.CodeActionKind.Source,
                lsp.CodeActionKind.SourceOrganizeImports,
            ]
        )
        code_action_literal_support_caps = lsp.CodeActionClientCapabilitiesCodeActionLiteralSupportType(
            code_action_kind=code_action_kind_caps,
        )
        code_action_caps = lsp.CodeActionClientCapabilities(
            dynamic_registration=False,
            resolve_support=code_action_resolve_support_caps,
            data_support=True,
            code_action_literal_support=code_action_literal_support_caps,
            is_preferred_support=True,
        )
        formatting_caps = lsp.DocumentFormattingClientCapabilities(
            dynamic_registration=False,
        )
        range_formatting_caps = lsp.DocumentRangeFormattingClientCapabilities(
            dynamic_registration=False,
        )
        rename_caps = lsp.RenameClientCapabilities(
            dynamic_registration=False,
        )
        inlay_hint_caps = lsp.InlayHintClientCapabilities(
            dynamic_registration=False,
        )
        publish_diagnostics_tag_support_caps = lsp.PublishDiagnosticsClientCapabilitiesTagSupportType(
            [
                lsp.DiagnosticTag.Unnecessary,
                lsp.DiagnosticTag.Deprecated,
            ]
        )
        publish_diagnostics_caps = lsp.PublishDiagnosticsClientCapabilities(
            related_information=False,
            code_description_support=False,
            tag_support=publish_diagnostics_tag_support_caps,
        )
        text_document_caps = lsp.TextDocumentClientCapabilities(
            synchronization=synchronization_caps,
            completion=completion_caps,
            hover=hover_caps,
            signature_help=signature_help_caps,
            references=references_caps,
            definition=definition_caps,
            declaration=declaration_caps,
            implementation=implementation_caps,
            type_definition=type_definition_caps,
            document_symbol=document_symbol_caps,
            document_highlight=document_highlight_caps,
            code_action=code_action_caps,
            formatting=formatting_caps,
            range_formatting=range_formatting_caps,
            rename=rename_caps,
            inlay_hint=inlay_hint_caps,
            publish_diagnostics=publish_diagnostics_caps,
        )

        show_document_caps = lsp.ShowDocumentClientCapabilities(
            support=True,
        )
        window_caps = lsp.WindowClientCapabilities(
            show_document=show_document_caps,
            work_done_progress=True,
        )

        position_encoding_caps : List[lsp.PositionEncodingKind | str] | None = [
            lsp.PositionEncodingKind.Utf32,
            lsp.PositionEncodingKind.Utf8,
            lsp.PositionEncodingKind.Utf16,
        ]

        general_caps = lsp.GeneralClientCapabilities(
            position_encodings=position_encoding_caps,
        )

        return lsp.ClientCapabilities(
            workspace=workspace_caps,
            text_document=text_document_caps,
            window=window_caps,
            general=general_caps,
        )

    client_capabilities = prepare_client_capabilities()

    client_info = lsp.InitializeParamsClientInfoType(
        name=CLIENT_NAME,
        version=CLIENT_VERSION,
    )

    root_path = os.path.realpath(WORKSPACE_FOLDER)
    root_uri = from_fs_path(root_path)
    assert root_uri is not None
    workspace_folders = [
        lsp.WorkspaceFolder(
            uri=root_uri,
            name=os.path.basename(root_path)
        )
    ]

    initialize_params = lsp.InitializeParams(
        capabilities=client_capabilities,
        client_info=client_info,
        root_path=root_path,
        root_uri=root_uri,
        workspace_folders=workspace_folders,
    )
    initialize_result = await asyncio.wait_for(
        pyangtlc.initialize_async(
            params=initialize_params,
        ),
        timeout=2.0
    )
    _validate_initialize_result(initialize_result)

    test_doc = 'test-a.yang'
    test_doc_path = os.path.join(os.path.realpath(WORKSPACE_FOLDER), test_doc)
    doc_uri = from_fs_path(test_doc_path)
    assert doc_uri is not None
    with open(test_doc_path) as test_fd:
        doc_source = test_fd.read()
        test_fd.close()

    did_open_text_document_params = lsp.DidOpenTextDocumentParams(
        text_document=lsp.TextDocumentItem(
            uri=doc_uri,
            language_id='yang',
            version=0,
            text=doc_source,
        )
    )
    pyangtlc.text_document_did_open(
        params=did_open_text_document_params
    )

    # Allow textDocument/publishDiagnostics to arrive and be validated in sequence
    # TODO: Should be done in a deterministic way
    await asyncio.sleep(0.5)
    pyangtlc.test_step += 1

    did_change_configuration_params = lsp.DidChangeConfigurationParams(
        settings=None,
    )
    pyangtlc.workspace_did_change_configuration(
        params=did_change_configuration_params
    )

    # Allow textDocument/publishDiagnostics to arrive and be validated in sequence
    # TODO: Should be done in a deterministic way
    await asyncio.sleep(0.5)

    document_formatting_params = lsp.DocumentFormattingParams(
        text_document=lsp.TextDocumentIdentifier(
            uri=doc_uri
        ),
        options=lsp.FormattingOptions(
            tab_size=4,
            insert_spaces=True
        ),
    )
    def validate_document_formatting_result(result: List[lsp.TextEdit] | None):
        """Validate `textDocument/formatting` result"""

        logger.info("Received textDocument/formatting result. Validating...")
        assert result
        assert len(result) == 1
        fmt_text = result[0].new_text
        # logger.debug("Received formatted text:\n" + fmt_text)
        exp_file = open('expect/test-a.yang')
        exp_text = exp_file.read()
        exp_file.close()
        assert fmt_text == exp_text
        logger.info("Valid textDocument/formatting result!")
    document_formatting_result = await asyncio.wait_for(
        pyangtlc.text_document_formatting_async(
            params=document_formatting_params,
        ),
        timeout=1.0
    )
    validate_document_formatting_result(document_formatting_result)

    await asyncio.wait_for(
        pyangtlc.shutdown_async(
            params=None
        ),
        timeout=1.0
    )

    pyangtlc.exit(
        params=None
    )

async def test_vscode():
    await asyncio.wait_for(
        pyangtlc.start_io('pyang','--lsp'),
        timeout=2.0
    )

    pyangtlc.test_step = 1

    def prepare_client_capabilities() -> lsp.ClientCapabilities:
        """Prepare reference client capabilities based on VS Code 1.88.1 """

        resource_operations_caps = [
            lsp.ResourceOperationKind.Create,
            lsp.ResourceOperationKind.Rename,
            lsp.ResourceOperationKind.Delete,
        ]
        change_annotation_support_caps = lsp.WorkspaceEditClientCapabilitiesChangeAnnotationSupportType(
            groups_on_label=True
        )
        workspace_edit_caps = lsp.WorkspaceEditClientCapabilities(
            document_changes=True,
            resource_operations=resource_operations_caps,
            failure_handling=lsp.FailureHandlingKind.TextOnlyTransactional,
            normalizes_line_endings=True,
            change_annotation_support=change_annotation_support_caps,
        )
        did_change_configuration_caps = lsp.DidChangeConfigurationClientCapabilities(
            dynamic_registration=True,
        )
        did_change_watched_files_caps = lsp.DidChangeWatchedFilesClientCapabilities(
            dynamic_registration=True,
        )
        workspace_symbol_kind_caps = lsp.WorkspaceSymbolClientCapabilitiesSymbolKindType(
            value_set=[
                lsp.SymbolKind.File,
                lsp.SymbolKind.Module,
                lsp.SymbolKind.Namespace,
                lsp.SymbolKind.Package,
                lsp.SymbolKind.Class,
                lsp.SymbolKind.Method,
                lsp.SymbolKind.Property,
                lsp.SymbolKind.Field,
                lsp.SymbolKind.Constructor,
                lsp.SymbolKind.Enum,
                lsp.SymbolKind.Interface,
                lsp.SymbolKind.Function,
                lsp.SymbolKind.Variable,
                lsp.SymbolKind.Constant,
                lsp.SymbolKind.String,
                lsp.SymbolKind.Number,
                lsp.SymbolKind.Boolean,
                lsp.SymbolKind.Array,
                lsp.SymbolKind.Object,
                lsp.SymbolKind.Key,
                lsp.SymbolKind.Null,
                lsp.SymbolKind.EnumMember,
                lsp.SymbolKind.Struct,
                lsp.SymbolKind.Event,
                lsp.SymbolKind.Operator,
                lsp.SymbolKind.TypeParameter,
            ]
        )
        workspace_tag_support_caps = lsp.WorkspaceSymbolClientCapabilitiesTagSupportType(
            value_set=[
                lsp.SymbolTag.Deprecated
            ]
        )
        symbol_caps = lsp.WorkspaceSymbolClientCapabilities(
            dynamic_registration=True,
            symbol_kind=workspace_symbol_kind_caps,
            tag_support=workspace_tag_support_caps,
        )
        code_lens_caps = lsp.CodeLensWorkspaceClientCapabilities(
            refresh_support=True,
        )
        execute_command_caps = lsp.ExecuteCommandClientCapabilities(
            dynamic_registration=True,
        )
        semantic_tokens_caps = lsp.SemanticTokensWorkspaceClientCapabilities(
            refresh_support=True,
        )
        file_operations_caps = lsp.FileOperationClientCapabilities(
            dynamic_registration=True,
            did_create=True,
            did_rename=True,
            did_delete=True,
            will_create=True,
            will_rename=True,
            will_delete=True,
        )
        workspace_caps = lsp.WorkspaceClientCapabilities(
            apply_edit=True,
            workspace_edit=workspace_edit_caps,
            did_change_configuration=did_change_configuration_caps,
            did_change_watched_files=did_change_watched_files_caps,
            symbol=symbol_caps,
            code_lens=code_lens_caps,
            execute_command=execute_command_caps,
            configuration=True,
            workspace_folders=True,
            semantic_tokens=semantic_tokens_caps,
            file_operations=file_operations_caps,
        )

        publish_diagnostics_tag_support_caps = lsp.PublishDiagnosticsClientCapabilitiesTagSupportType(
            [
                lsp.DiagnosticTag.Unnecessary,
                lsp.DiagnosticTag.Deprecated,
            ]
        )
        publish_diagnostics_caps = lsp.PublishDiagnosticsClientCapabilities(
            related_information=True,
            version_support=False,
            tag_support=publish_diagnostics_tag_support_caps,
            code_description_support=True,
            data_support=True,
        )
        synchronization_caps = lsp.TextDocumentSyncClientCapabilities(
            dynamic_registration=True,
            will_save=True,
            will_save_wait_until=True,
            did_save=True,
        )
        documentation_format_caps = [
            lsp.MarkupKind.Markdown,
            lsp.MarkupKind.PlainText,
        ]
        completion_item_resolve_support_caps = lsp.CompletionClientCapabilitiesCompletionItemTypeResolveSupportType(
            [
                'documentation',
                'detail',
                'additionalTextEdits'
            ]
        )
        completion_item_tag_support_caps = lsp.CompletionClientCapabilitiesCompletionItemTypeTagSupportType(
            [
                lsp.CompletionItemTag.Deprecated
            ]
        )
        insert_text_mode_support_caps = lsp.CompletionClientCapabilitiesCompletionItemTypeInsertTextModeSupportType(
            value_set=[
                lsp.InsertTextMode.AsIs,
                lsp.InsertTextMode.AdjustIndentation,
            ]
        )
        completion_item_caps = lsp.CompletionClientCapabilitiesCompletionItemType(
            snippet_support=True,
            commit_characters_support=True,
            documentation_format=documentation_format_caps,
            deprecated_support=True,
            preselect_support=True,
            tag_support=completion_item_tag_support_caps,
            insert_replace_support=True,
            resolve_support=completion_item_resolve_support_caps,
            insert_text_mode_support=insert_text_mode_support_caps,
        )
        completion_item_kind_caps = lsp.CompletionClientCapabilitiesCompletionItemKindType(
            value_set=[
                lsp.CompletionItemKind.Text,
                lsp.CompletionItemKind.Method,
                lsp.CompletionItemKind.Function,
                lsp.CompletionItemKind.Constructor,
                lsp.CompletionItemKind.Field,
                lsp.CompletionItemKind.Variable,
                lsp.CompletionItemKind.Class,
                lsp.CompletionItemKind.Interface,
                lsp.CompletionItemKind.Module,
                lsp.CompletionItemKind.Property,
                lsp.CompletionItemKind.Unit,
                lsp.CompletionItemKind.Value,
                lsp.CompletionItemKind.Enum,
                lsp.CompletionItemKind.Keyword,
                lsp.CompletionItemKind.Snippet,
                lsp.CompletionItemKind.Color,
                lsp.CompletionItemKind.File,
                lsp.CompletionItemKind.Reference,
                lsp.CompletionItemKind.Folder,
                lsp.CompletionItemKind.EnumMember,
                lsp.CompletionItemKind.Constant,
                lsp.CompletionItemKind.Struct,
                lsp.CompletionItemKind.Event,
                lsp.CompletionItemKind.Operator,
                lsp.CompletionItemKind.TypeParameter,
            ]
        )
        completion_caps = lsp.CompletionClientCapabilities(
            dynamic_registration=True,
            context_support=True,
            completion_item=completion_item_caps,
            completion_item_kind=completion_item_kind_caps,
        )
        content_format_caps = [
            lsp.MarkupKind.Markdown,
            lsp.MarkupKind.PlainText,
        ]
        hover_caps = lsp.HoverClientCapabilities(
            dynamic_registration=True,
            content_format=content_format_caps,
        )
        document_format_caps = [
            lsp.MarkupKind.Markdown,
            lsp.MarkupKind.PlainText,
        ]
        parameter_information_caps = lsp.SignatureHelpClientCapabilitiesSignatureInformationTypeParameterInformationType(
            label_offset_support=True,
        )
        signature_information_caps = lsp.SignatureHelpClientCapabilitiesSignatureInformationType(
            documentation_format=document_format_caps,
            parameter_information=parameter_information_caps,
            active_parameter_support=True,
        )
        signature_help_caps = lsp.SignatureHelpClientCapabilities(
            dynamic_registration=True,
            signature_information=signature_information_caps,
            context_support=True,
        )
        definition_caps = lsp.DefinitionClientCapabilities(
            dynamic_registration=True,
            link_support=True,
        )
        references_caps = lsp.ReferenceClientCapabilities(
            dynamic_registration=True,
        )
        document_highlight_caps = lsp.DocumentHighlightClientCapabilities(
            dynamic_registration=True,
        )
        document_symbol_kind_caps = lsp.DocumentSymbolClientCapabilitiesSymbolKindType(
            [
                lsp.SymbolKind.File,
                lsp.SymbolKind.Module,
                lsp.SymbolKind.Namespace,
                lsp.SymbolKind.Package,
                lsp.SymbolKind.Class,
                lsp.SymbolKind.Method,
                lsp.SymbolKind.Property,
                lsp.SymbolKind.Field,
                lsp.SymbolKind.Constructor,
                lsp.SymbolKind.Enum,
                lsp.SymbolKind.Interface,
                lsp.SymbolKind.Function,
                lsp.SymbolKind.Variable,
                lsp.SymbolKind.Constant,
                lsp.SymbolKind.String,
                lsp.SymbolKind.Number,
                lsp.SymbolKind.Boolean,
                lsp.SymbolKind.Array,
                lsp.SymbolKind.Object,
                lsp.SymbolKind.Key,
                lsp.SymbolKind.Null,
                lsp.SymbolKind.EnumMember,
                lsp.SymbolKind.Struct,
                lsp.SymbolKind.Event,
                lsp.SymbolKind.Operator,
                lsp.SymbolKind.TypeParameter,
            ]
        )
        document_symbol_tag_support_caps = lsp.DocumentSymbolClientCapabilitiesTagSupportType(
            value_set=[
                lsp.SymbolTag.Deprecated,
            ]
        )
        document_symbol_caps = lsp.DocumentSymbolClientCapabilities(
            dynamic_registration=True,
            symbol_kind=document_symbol_kind_caps,
            hierarchical_document_symbol_support=True,
            tag_support=document_symbol_tag_support_caps,
            label_support=True,
        )
        code_action_resolve_support_caps = lsp.CodeActionClientCapabilitiesResolveSupportType(
            [
                'edit'
            ]
        )
        code_action_kind_caps = lsp.CodeActionClientCapabilitiesCodeActionLiteralSupportTypeCodeActionKindType(
            value_set=[
                '',
                lsp.CodeActionKind.QuickFix,
                lsp.CodeActionKind.Refactor,
                lsp.CodeActionKind.RefactorExtract,
                lsp.CodeActionKind.RefactorInline,
                lsp.CodeActionKind.RefactorRewrite,
                lsp.CodeActionKind.Source,
                lsp.CodeActionKind.SourceOrganizeImports,
            ]
        )
        code_action_literal_support_caps = lsp.CodeActionClientCapabilitiesCodeActionLiteralSupportType(
            code_action_kind=code_action_kind_caps,
        )
        code_action_caps = lsp.CodeActionClientCapabilities(
            dynamic_registration=True,
            is_preferred_support=True,
            disabled_support=True,
            data_support=True,
            resolve_support=code_action_resolve_support_caps,
            code_action_literal_support=code_action_literal_support_caps,
            honors_change_annotations=False,
        )
        code_lens_caps = lsp.CodeLensClientCapabilities(
            dynamic_registration=True,
        )
        formatting_caps = lsp.DocumentFormattingClientCapabilities(
            dynamic_registration=True,
        )
        range_formatting_caps = lsp.DocumentRangeFormattingClientCapabilities(
            dynamic_registration=True,
        )
        on_type_formatting_caps = lsp.DocumentOnTypeFormattingClientCapabilities(
            dynamic_registration=True,
        )
        rename_caps = lsp.RenameClientCapabilities(
            dynamic_registration=True,
            prepare_support=True,
            prepare_support_default_behavior=lsp.PrepareSupportDefaultBehavior.Identifier,
            honors_change_annotations=True,
        )
        document_link_caps = lsp.DocumentLinkClientCapabilities(
            dynamic_registration=True,
            tooltip_support=True,
        )
        type_definition_caps = lsp.TypeDefinitionClientCapabilities(
            dynamic_registration=True,
            link_support=True,
        )
        implementation_caps = lsp.ImplementationClientCapabilities(
            dynamic_registration=True,
            link_support=True,
        )
        color_provider_caps = lsp.DocumentColorClientCapabilities(
            dynamic_registration=True,
        )
        folding_range_caps = lsp.FoldingRangeClientCapabilities(
            dynamic_registration=True,
            range_limit=5000,
            line_folding_only=True,
        )
        declaration_caps = lsp.DeclarationClientCapabilities(
            dynamic_registration=True,
            link_support=True,
        )
        selection_range_caps = lsp.SelectionRangeClientCapabilities(
            dynamic_registration=True
        )
        call_hierarchy_caps = lsp.CallHierarchyClientCapabilities(
            dynamic_registration=True,
        )
        semantic_tokens_requests_caps = lsp.SemanticTokensClientCapabilitiesRequestsType(
            range=True,
            full=lsp.SemanticTokensClientCapabilitiesRequestsTypeFullType1(delta=True),
        )
        semantic_tokens_caps = lsp.SemanticTokensClientCapabilities(
            dynamic_registration=True,
            token_types=[
                'namespace',
                'type',
                'class',
                'enum',
                'interface',
                'struct',
                'typeParameter',
                'parameter',
                'variable',
                'property',
                'enumMember',
                'event',
                'function',
                'method',
                'macro',
                'keyword',
                'modifier',
                'comment',
                'string',
                'number',
                'regexp',
                'operator',
            ],
            token_modifiers=[
                'declaration',
                'definition',
                'readonly',
                'static',
                'deprecated',
                'abstract',
                'async',
                'modification',
                'documentation',
                'defaultLibrary',
            ],
            formats=[
                lsp.TokenFormat.Relative,
            ],
            requests=semantic_tokens_requests_caps,
            multiline_token_support=False,
            overlapping_token_support=False,
        )
        linked_editing_range_caps = lsp.LinkedEditingRangeClientCapabilities(
            dynamic_registration=True,
        )
        text_document_caps = lsp.TextDocumentClientCapabilities(
            publish_diagnostics=publish_diagnostics_caps,
            synchronization=synchronization_caps,
            completion=completion_caps,
            hover=hover_caps,
            signature_help=signature_help_caps,
            definition=definition_caps,
            references=references_caps,
            document_highlight=document_highlight_caps,
            document_symbol=document_symbol_caps,
            code_action=code_action_caps,
            code_lens=code_lens_caps,
            formatting=formatting_caps,
            range_formatting=range_formatting_caps,
            on_type_formatting=on_type_formatting_caps,
            rename=rename_caps,
            document_link=document_link_caps,
            type_definition=type_definition_caps,
            implementation=implementation_caps,
            color_provider=color_provider_caps,
            folding_range=folding_range_caps,
            declaration=declaration_caps,
            selection_range=selection_range_caps,
            call_hierarchy=call_hierarchy_caps,
            semantic_tokens=semantic_tokens_caps,
            linked_editing_range=linked_editing_range_caps,
        )

        message_action_item_caps = lsp.ShowMessageRequestClientCapabilitiesMessageActionItemType(
            additional_properties_support=True
        )
        show_message_caps = lsp.ShowMessageRequestClientCapabilities(
            message_action_item=message_action_item_caps,
        )
        show_document_caps = lsp.ShowDocumentClientCapabilities(
            support=True,
        )
        window_caps = lsp.WindowClientCapabilities(
            show_message=show_message_caps,
            show_document=show_document_caps,
            work_done_progress=True,
        )

        regular_expressions_caps = lsp.RegularExpressionsClientCapabilities(
            engine='ECMAScript',
            version='ES2020',
        )
        markdown_caps = lsp.MarkdownClientCapabilities(
            parser='marked',
            version='1.1.0'
        )
        general_caps = lsp.GeneralClientCapabilities(
            regular_expressions=regular_expressions_caps,
            markdown=markdown_caps,
        )

        return lsp.ClientCapabilities(
            workspace=workspace_caps,
            text_document=text_document_caps,
            window=window_caps,
            general=general_caps,
        )

    client_capabilities = prepare_client_capabilities()

    client_info = lsp.InitializeParamsClientInfoType(
        name=CLIENT_NAME,
        version=CLIENT_VERSION,
    )

    root_path = os.path.realpath(WORKSPACE_FOLDER)
    root_uri = from_fs_path(root_path)
    assert root_uri is not None
    workspace_folders = [
        lsp.WorkspaceFolder(
            uri=root_uri,
            name=os.path.basename(root_path)
        )
    ]

    initialize_params = lsp.InitializeParams(
        client_info=client_info,
        locale='en',
        root_path=root_path,
        root_uri=root_uri,
        capabilities=client_capabilities,
        workspace_folders=workspace_folders,
    )
    initialize_result = await asyncio.wait_for(
        pyangtlc.initialize_async(
            params=initialize_params,
        ),
        timeout=2.0
    )
    _validate_initialize_result(initialize_result)

    did_change_configuration_params = lsp.DidChangeConfigurationParams(
        settings=None,
    )
    pyangtlc.workspace_did_change_configuration(
        params=did_change_configuration_params
    )

    # Allow textDocument/publishDiagnostics to arrive and be validated in sequence
    # TODO: Should be done in a deterministic way
    await asyncio.sleep(0.5)

    test_doc = 'test-a.yang'
    test_doc_path = os.path.join(os.path.realpath(WORKSPACE_FOLDER), test_doc)
    doc_uri = from_fs_path(test_doc_path)
    assert doc_uri is not None

    pyangtlc.test_step += 1

    with open(test_doc_path, mode='r') as test_file:
        data = test_file.read()
    data = data.replace('deviate add', 'deviate replace')
    with open(test_doc_path, mode='w') as test_file:
        test_file.write(data)

    # Allow file sync
    # TODO: Should be done in a deterministic way
    await asyncio.sleep(0.5)

    did_change_watched_files_params = lsp.DidChangeWatchedFilesParams(
        changes=[
            lsp.FileEvent(
                uri=doc_uri,
                type=lsp.FileChangeType.Changed
            )
        ]
    )
    pyangtlc.workspace_did_change_watched_files(
        params=did_change_watched_files_params
    )

    # Allow textDocument/publishDiagnostics to arrive and be validated in sequence
    # TODO: Should be done in a deterministic way
    await asyncio.sleep(0.5)

    pyangtlc.test_step += 1

    with open(test_doc_path, mode='a') as test_file:
        test_file.write('garbage')

    # Allow file sync
    # TODO: Should be done in a deterministic way
    await asyncio.sleep(0.5)

    did_change_watched_files_params = lsp.DidChangeWatchedFilesParams(
        changes=[
            lsp.FileEvent(
                uri=doc_uri,
                type=lsp.FileChangeType.Changed
            )
        ]
    )
    pyangtlc.workspace_did_change_watched_files(
        params=did_change_watched_files_params
    )

    # Allow textDocument/publishDiagnostics to arrive and be validated in sequence
    # TODO: Should be done in a deterministic way
    await asyncio.sleep(0.5)

    pyangtlc.test_step += 1

    with open(test_doc_path, mode='r') as test_file:
        data = test_file.read()
    data = data.replace('garbage', '')
    data = data.replace('deviate replace', 'deviate add')
    with open(test_doc_path, mode='w') as test_file:
        test_file.write(data)

    did_change_watched_files_params = lsp.DidChangeWatchedFilesParams(
        changes=[
            lsp.FileEvent(
                uri=doc_uri,
                type=lsp.FileChangeType.Changed
            )
        ]
    )
    pyangtlc.workspace_did_change_watched_files(
        params=did_change_watched_files_params
    )

    # Allow textDocument/publishDiagnostics to arrive and be validated in sequence
    # TODO: Should be done in a deterministic way
    await asyncio.sleep(0.5)

    await asyncio.wait_for(
        pyangtlc.shutdown_async(
            params=None
        ),
        timeout=1.0
    )

    pyangtlc.exit(
        params=None
    )

if __name__ == "__main__":
    logging.basicConfig(
        filename='pyangtlc.log',
        filemode='w',
        format='%(asctime)s.%(msecs)03d %(name)s %(levelname)s %(message)s',
        datefmt='%H:%M:%S',
        level=logging.DEBUG,
    )

    logger.info("------------------")
    logger.info("Generic Test Suite")
    logger.info("------------------")
    asyncio.run(test_generic())

    logger.info("----------------")
    logger.info("Eglot Test Suite")
    logger.info("----------------")
    asyncio.run(test_eglot())

    logger.info("-----------------")
    logger.info("VSCode Test Suite")
    logger.info("-----------------")
    asyncio.run(test_vscode())
