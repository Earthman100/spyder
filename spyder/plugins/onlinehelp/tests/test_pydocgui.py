# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
#

"""
Tests for pydocgui.py
"""
# Standard library imports
import sys
from unittest.mock import MagicMock

# Test library imports
import numpy as np
from numpy.lib import NumpyVersion
import pytest
from flaky import flaky

# Local imports
from spyder.plugins.onlinehelp.widgets import PydocBrowser


@pytest.fixture
def pydocbrowser(qtbot):
    """Set up pydocbrowser."""
    plugin_mock = MagicMock()
    plugin_mock.CONF_SECTION = 'onlinehelp'
    widget = PydocBrowser(parent=None, plugin=plugin_mock, name='pydoc')
    widget._setup()
    widget.setup()
    widget.resize(640, 480)
    widget.show()

    with qtbot.waitSignal(widget.sig_load_finished, timeout=6000):
        widget.initialize()

    qtbot.addWidget(widget)
    return widget


@flaky(max_runs=5)
@pytest.mark.parametrize(
    "lib",
    [('str', 'class str', [0, 1]), ('numpy.testing', 'numpy.testing', [5, 10])]
)
@pytest.mark.skipif(
    (sys.platform == 'darwin' or
     NumpyVersion(np.__version__) < NumpyVersion('1.21.0')),
    reason="Fails on Mac and older versions of Numpy"
)
def test_get_pydoc(pydocbrowser, qtbot, lib):
    """
    Go to the documentation by url.
    Regression test for spyder-ide/spyder#10740
    """
    browser = pydocbrowser
    element, doc, matches = lib

    webview = browser.webview
    element_url = browser.text_to_url(element)
    with qtbot.waitSignal(webview.loadFinished):
        browser.set_url(element_url)

    expected_range = list(range(matches[0], matches[1]))
    qtbot.waitUntil(lambda: webview.get_number_matches(doc) in expected_range)


if __name__ == "__main__":
    pytest.main()
