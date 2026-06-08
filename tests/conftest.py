import sys

import pytest

try:
    from PyQt6.QtWidgets import QApplication
    _HAS_QT = True
except ImportError:
    _HAS_QT = False


@pytest.fixture(scope="session")
def qapp():
    if not _HAS_QT:
        pytest.skip("PyQt6 not installed")
    app = QApplication.instance() or QApplication(sys.argv)
    yield app
