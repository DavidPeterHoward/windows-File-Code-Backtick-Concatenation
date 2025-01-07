import pytest
import os
import tempfile
import shutil
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox, QToolBar
from PyQt5.QtCore import Qt, QSettings, QPoint, QMimeData, QSize
from PyQt5.QtGui import QDrag
from file_concatenator import MainWindow, DraggableTextEdit

@pytest.fixture(scope="session")
def app():
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def window(app, qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    yield window
    window.close()

@pytest.fixture
def temp_files(tmp_path):
    # Create test files with different extensions
    files = {
        'python': ("test1.py", "def test1():\n    return 'test1'"),
        'javascript': ("test2.js", "function test2() {\n    return 'test2';\n}"),
        'text': ("test3.txt", "Plain text content"),
        'markdown': ("test4.md", "# Markdown Test\nContent"),
    }
    
    created_files = []
    for _, (filename, content) in files.items():
        file_path = tmp_path / filename
        file_path.write_text(content, encoding='utf-8')
        created_files.append(str(file_path))
    
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    nested_file = subdir / "nested.py"
    nested_file.write_text("def nested():\n    return 'nested'", encoding='utf-8')
    created_files.append(str(nested_file))
    
    yield str(tmp_path), created_files

def test_window_initialization(window):
    assert window.windowTitle() == "File Concatenator"
    assert hasattr(window, 'file_tree')
    assert hasattr(window, 'content_tabs')
    assert hasattr(window, 'recent_folders_widget')
    assert isinstance(window.content_tabs.content_editor, DraggableTextEdit)

def test_path_toggle(window):
    assert window.show_absolute_paths == True
    window.path_toggle.setChecked(False)
    assert window.show_absolute_paths == False

def test_file_selection(window, temp_files, qtbot):
    tmp_dir, files = temp_files
    py_file = next(f for f in files if f.endswith('.py'))
    
    window.file_tree.setRootIndex(window.file_tree.model.index(tmp_dir))
    qtbot.wait(100)  # Allow file system model to update
    
    index = window.file_tree.model.index(py_file)
    window.file_tree.selectionModel().select(index, window.file_tree.selectionModel().Select)
    qtbot.wait(100)  # Allow for content update
    
    content = window.content_tabs.content_editor.toPlainText()
    assert '# File:' in content
    assert 'def test1()' in content
    assert '```python' in content

def test_language_detection(window):
    test_files = {
        'test.py': 'python',
        'test.js': 'javascript',
        'test.md': 'markdown',
        'test.txt': 'text',
        'test.unknown': ''
    }
    
    for file_path, expected_lang in test_files.items():
        detected_lang = window._get_language_from_extension(file_path)
        assert detected_lang == expected_lang

def test_recent_folders(window, temp_files, qtbot):
    tmp_dir, _ = temp_files
    window._add_recent_folder(tmp_dir)
    qtbot.wait(100)
    assert window.recent_folders[0] == tmp_dir
    assert window.recent_folders_widget.item(0).text() == tmp_dir

def test_clipboard_operations(window, qtbot):
    test_content = "Test clipboard content"
    window.content_tabs.content_editor.setPlainText(test_content)
    window._copy()
    assert QApplication.clipboard().text() == test_content
    
    new_content = "New test content"
    QApplication.clipboard().setText(new_content)
    window._paste()
    assert window.content_tabs.content_editor.toPlainText() == new_content

def test_invalid_path_handling(window, qtbot, monkeypatch):
    def mock_warning(*args, **kwargs):
        pass
    monkeypatch.setattr(QMessageBox, "warning", mock_warning)
    
    invalid_path = r"X:\invalid\path"
    window.path_input.setText(invalid_path)
    window._navigate_to_path()
    assert window.file_tree.model.filePath(window.file_tree.rootIndex()) != invalid_path

def test_multiple_file_selection(window, temp_files, qtbot):
    tmp_dir, files = temp_files
    window.file_tree.setRootIndex(window.file_tree.model.index(tmp_dir))
    qtbot.wait(100)  # Allow file system model to update
    
    # Select first two files
    for file_path in files[:2]:
        index = window.file_tree.model.index(file_path)
        window.file_tree.selectionModel().select(
            index,
            window.file_tree.selectionModel().Select
        )
    
    qtbot.wait(100)  # Allow for content update
    content = window.content_tabs.content_editor.toPlainText()
    assert content.count('# File:') == 2
    assert content.count('```python') >= 1

@pytest.mark.parametrize("show_paths", [True, False])
def test_settings_persistence(qtbot, show_paths):
    # Clear any existing settings
    settings = QSettings('FileConcatenator', 'Settings')
    settings.clear()
    settings.sync()
    
    # First window - set settings
    first_window = MainWindow()
    qtbot.addWidget(first_window)
    first_window.show()
    qtbot.wait(100)
    
    # Modify settings
    first_window._toggle_path_mode(Qt.Checked if show_paths else Qt.Unchecked)
    first_window.resize(900, 700)
    qtbot.wait(100)
    
    # Properly close first window
    first_window.close()
    qtbot.wait(100)
    
    # Create second window to verify settings
    second_window = MainWindow()
    qtbot.addWidget(second_window)
    second_window.show()
    qtbot.wait(100)
    
    # Verify settings were preserved
    assert second_window.show_absolute_paths == show_paths
    assert second_window.size().width() >= 800
    assert second_window.size().height() >= 600
    
    # Cleanup
    second_window.close()
    qtbot.wait(100)
    
    # Clear settings after test
    settings.clear()
    settings.sync()

def test_initial_path_handling(temp_files, qtbot):
    tmp_dir, _ = temp_files
    window = MainWindow(initial_path=tmp_dir)
    qtbot.addWidget(window)
    assert window.path_input.text() == tmp_dir
    
    # Normalize path separators for comparison
    tree_path = window.file_tree.model.filePath(window.file_tree.rootIndex()).replace('/', os.sep)
    expected_path = tmp_dir.replace('/', os.sep)
    assert tree_path == expected_path
    
    window.close()
    qtbot.wait(100)

def test_drag_and_drop_initialization(window):
    editor = window.content_tabs.content_editor
    assert hasattr(editor, 'mousePressEvent')
    assert hasattr(editor, 'mouseMoveEvent')

def test_layout_margins(window):
    main_widget = window.centralWidget()
    layout = main_widget.layout()
    assert layout.contentsMargins().left() == 0
    assert layout.contentsMargins().top() == 0
    assert layout.contentsMargins().right() == 0
    assert layout.contentsMargins().bottom() == 0

    left_panel = layout.itemAt(0).widget().widget(0)
    left_layout = left_panel.layout()
    assert left_layout.contentsMargins().left() == 0
    assert left_layout.contentsMargins().top() == 0
    assert left_layout.contentsMargins().right() == 0
    assert left_layout.contentsMargins().bottom() == 0

def test_toolbar_alignment(window):
    main_toolbar = window.findChild(QToolBar, "MainToolBar")
    nav_bar = window.findChild(QToolBar, "NavigationBar")
    
    assert main_toolbar.iconSize() == QSize(16, 16)
    assert main_toolbar.maximumHeight() == 28
    assert "background-color: #f8f9fa" in nav_bar.styleSheet()
    assert "border-bottom: 1px solid #dee2e6" in nav_bar.styleSheet()