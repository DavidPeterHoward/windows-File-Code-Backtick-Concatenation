import pytest
import os
import tempfile
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QSettings
from file_concatenator import MainWindow

@pytest.fixture
def app():
    return QApplication([])

@pytest.fixture
def window(app):
    return MainWindow()

@pytest.fixture
def temp_files():
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create test files with different extensions
        files = {
            'python': ("test1.py", "def test1():\n    return 'test1'"),
            'javascript': ("test2.js", "function test2() {\n    return 'test2';\n}"),
            'text': ("test3.txt", "Plain text content"),
            'markdown': ("test4.md", "# Markdown Test\nContent"),
        }
        
        created_files = []
        for _, (filename, content) in files.items():
            file_path = os.path.join(tmp_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            created_files.append(file_path)
        
        subdir = os.path.join(tmp_dir, "subdir")
        os.mkdir(subdir)
        nested_file = os.path.join(subdir, "nested.py")
        with open(nested_file, 'w', encoding='utf-8') as f:
            f.write("def nested():\n    return 'nested'")
        created_files.append(nested_file)
        
        yield tmp_dir, created_files

def test_window_initialization(window):
    assert window.windowTitle() == "File Concatenator"
    assert hasattr(window, 'file_tree')
    assert hasattr(window, 'content_tabs')
    assert hasattr(window, 'recent_folders_widget')

def test_path_toggle(window):
    assert window.show_absolute_paths == True
    window.path_toggle.setChecked(False)
    assert window.show_absolute_paths == False

def test_file_selection(window, temp_files, qtbot):
    tmp_dir, files = temp_files
    
    # Select a Python file
    py_file = next(f for f in files if f.endswith('.py'))
    window.file_tree.setRootIndex(window.file_tree.model.index(tmp_dir))
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

def test_settings_persistence(window, qtbot):
    test_size = (900, 700)
    window.resize(*test_size)
    window._toggle_path_mode(Qt.Unchecked)
    window.closeEvent(None)  # Trigger settings save
    
    # Create new window
    new_window = MainWindow()
    assert new_window.show_absolute_paths == False
    assert new_window.size().width() >= 800
    assert new_window.size().height() >= 600