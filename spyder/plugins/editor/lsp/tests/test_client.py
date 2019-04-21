# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

import os
from textwrap import dedent

import pytest
from qtpy.QtCore import QObject, Signal, Slot

from spyder.config.lsp import PYTHON_CONFIG
from spyder.plugins.editor.lsp.client import LSPClient
from spyder.plugins.editor.lsp import LSPRequestTypes, SERVER_CAPABILITES


class LSPEditor(QObject):
    """Dummy editor that can handle the responses of an LSP client."""
    sig_response = Signal(str, dict)

    @Slot(str, dict)
    def handle_response(self, method, params):
        self.sig_response.emit(method, params)


@pytest.fixture
def lsp_client_and_editor():
    """Create an LSP client/editor pair."""

    editor = LSPEditor()
    client = LSPClient(parent=None,
                       server_settings=PYTHON_CONFIG,
                       language='python')

    yield client, editor

    # Teardown
    client.stop()


@pytest.mark.slow
def test_initialization(lsp_client_and_editor, qtbot):
    client, editor = lsp_client_and_editor

    # Wait for the client to be started
    with qtbot.waitSignal(client.sig_initialize, timeout=30000) as blocker:
        client.start()
    options, _ = blocker.args

    # Assert the response has what we expect
    assert all([option in SERVER_CAPABILITES for option in options.keys()])


@pytest.mark.slow
def test_get_signature(lsp_client_and_editor, qtbot):
    client, editor = lsp_client_and_editor

    # Wait for the client to be started
    with qtbot.waitSignal(client.sig_initialize, timeout=30000):
        client.start()

    # Parameters to perform a textDocument/didOpen request
    open_params = {
        'file': 'test.py',
        'language': 'python',
        'version': 1,
        'text': "import os\nos.walk(\n",
        'codeeditor': editor,
        'requires_response': False
    }

    # Perform the request
    with qtbot.waitSignal(editor.sig_response, timeout=30000) as blocker:
        client.perform_request(LSPRequestTypes.DOCUMENT_DID_OPEN, open_params)

    # Parameters to perform a textDocument/signatureHelp request
    signature_params = {
        'file': 'test.py',
        'line': 1,
        'column': 10,
        'requires_response': True,
        'response_codeeditor': editor
    }

    # Perform the request
    with qtbot.waitSignal(editor.sig_response, timeout=30000) as blocker:
        client.perform_request(LSPRequestTypes.DOCUMENT_SIGNATURE,
                               signature_params)
    _, response = blocker.args

    # Assert the response has what we expect
    assert response['params']['signatures']['label'].startswith('walk')


@pytest.mark.slow
def test_get_completions(lsp_client_and_editor, qtbot):
    client, editor = lsp_client_and_editor

    # Wait for the client to be started
    with qtbot.waitSignal(client.sig_initialize, timeout=30000):
        client.start()

    # Parameters to perform a textDocument/didOpen request
    open_params = {
        'file': 'test.py',
        'language': 'python',
        'version': 1,
        'text': "import o",
        'codeeditor': editor,
        'requires_response': False
    }

    # Perform the request
    with qtbot.waitSignal(editor.sig_response, timeout=30000) as blocker:
        client.perform_request(LSPRequestTypes.DOCUMENT_DID_OPEN, open_params)

    # Parameters to perform a textDocument/completion request
    completion_params = {
        'file': 'test.py',
        'line': 0,
        'column': 8,
        'requires_response': True,
        'response_codeeditor': editor
    }

    # Perform the request
    with qtbot.waitSignal(editor.sig_response, timeout=30000) as blocker:
        client.perform_request(LSPRequestTypes.DOCUMENT_COMPLETION,
                               completion_params)
    _, response = blocker.args

    # Assert the response has what we expect
    completions = response['params']
    assert 'os' in [x['label'] for x in completions]


@pytest.mark.slow
def test_go_to_definition(lsp_client_and_editor, qtbot):
    client, editor = lsp_client_and_editor

    # Wait for the client to be started
    with qtbot.waitSignal(client.sig_initialize, timeout=30000):
        client.start()

    # Parameters to perform a textDocument/didOpen request
    open_params = {
        'file': 'test.py',
        'language': 'python',
        'version': 1,
        'text': "import os\nos.walk\n",
        'codeeditor': editor,
        'requires_response': False
    }

    # Perform the request
    with qtbot.waitSignal(editor.sig_response, timeout=30000) as blocker:
        client.perform_request(LSPRequestTypes.DOCUMENT_DID_OPEN, open_params)

    # Parameters to perform a textDocument/definition request
    go_to_definition_params = {
        'file': 'test.py',
        'line': 0,
        'column': 19,
        'requires_response': True,
        'response_codeeditor': editor
    }

    # Perform the request
    with qtbot.waitSignal(editor.sig_response, timeout=30000) as blocker:
        client.perform_request(LSPRequestTypes.DOCUMENT_DEFINITION,
                               go_to_definition_params)
    _, response = blocker.args

    # Assert the response has what we expect
    definition = response['params']
    assert 'os.py' in definition['file']


@pytest.mark.slow
def test_local_signature(lsp_client_and_editor, qtbot):
    client, editor = lsp_client_and_editor

    # Wait for the client to be started
    with qtbot.waitSignal(client.sig_initialize, timeout=30000):
        client.start()

    # Parameters to perform a textDocument/didOpen request
    text = dedent('''
    def test(a, b):
        """Test docstring"""
        pass
    test''')
    open_params = {
        'file': 'test.py',
        'language': 'python',
        'version': 1,
        'text': text,
        'codeeditor': editor,
        'requires_response': False
    }

    # Perform the request
    with qtbot.waitSignal(editor.sig_response, timeout=30000) as blocker:
        client.perform_request(LSPRequestTypes.DOCUMENT_DID_OPEN, open_params)

    # Parameters to perform a textDocument/hover request
    signature_params = {
        'file': 'test.py',
        'line': 4,
        'column': 0,
        'requires_response': True,
        'response_codeeditor': editor
    }

    # Perform the request
    with qtbot.waitSignal(editor.sig_response, timeout=30000) as blocker:
        client.perform_request(LSPRequestTypes.DOCUMENT_HOVER,
                               signature_params)
    _, response = blocker.args

    # Assert the response has what we expect
    definition = response['params']
    assert 'Test docstring' in definition
