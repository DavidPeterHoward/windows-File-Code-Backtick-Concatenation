import pytest
import os
import tempfile
import json
from PyQt5.QtWidgets import QApplication, QListWidgetItem
from PyQt5.QtCore import Qt, QSettings
from file_concatenator import FileConcatenator, RecentFilesList

@pytest.fixture
def app():
    return QApplication([])

@pytest.fixture
def window(app):
    return FileConcatenator()

@pytest.fixture
def recent_files_list(app):
    return RecentFilesList()

@pytest.fixture
def temp_files():
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create test files
        file1_path = os.path.join(tmp_dir, "test1.py")
        file2_path = os.path.join(tmp_dir, "test2.py")
        
        with open(file1_path, 'w') as f1:
            f1.write("def test1():\n    return 'test1'")
        
        with open(file2_path, 'w') as f2:
            f2.write("def test2():\n    return 'test2'")
        
        # Create a subdirectory with a file
        subdir = os.path.join(tmp_dir, "subdir")
        os.mkdir(subdir)
        file3_path = os.path.join(subdir, "test3.py")
        with open(file3_path, 'w') as f3:
            f3.write("def test3():\n    return 'test3'")
        
        yield tmp_dir, [file1_path, file2_path, file3_path]

def test_recent_files_list_add(recent_files_list, temp_files):
    tmp_dir, files = temp_files
    
    # Add files to recent list
    for file_path in files:
        recent_files_list.add_recent_file(file_path)
    
    # Check if files were added
    assert recent_files_list.count() == len(files)
    
    # Check if the most recent file is at the top
    assert recent_files_list.item(0).data(Qt.UserRole) == files[-1]

def test_recent_files_list_star(recent_files_list, temp_files):
    tmp_dir, files = temp_files
    
    # Add a file and star it
    recent_files_list.add_recent_file(files[0])
    item = recent_files_list.item(0)
    recent_files_list.toggle_star(item)
    
    # Check if file is starred
    assert files[0] in recent_files_list.starred_items
    
    # Unstar the file
    recent_files_list.toggle_star(item)
    assert files[0] not in recent_files_list.starred_items

def test_recent_files_list_max_items(recent_files_list):
    # Create more files than the max limit
    max_files = recent_files_list.max_items + 5
    test_files = []
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        for i in range(max_files):
            file_path = os.path.join(tmp_dir, f"test{i}.txt")
            with open(file_path, 'w') as f:
                f.write(f"test{i}")
            test_files.append(file_path)
            recent_files_list.add_recent_file(file_path)
    
    # Check if list is limited to max items
    assert recent_files_list.count() == recent_files_list.max_items

def test_format_options(window):
    # Test language selection
    window.language_combo.setCurrentText('javascript')
    assert window.language_combo.currentText() == 'javascript'
    
    # Test format options persistence
    window.current_format['use_backticks'] = False
    window.save_settings()
    
    # Create new window instance
    new_window = FileConcatenator()
    # Note: Format settings would be loaded in initialization

def test_rabbitmq_integration(window):
    # Test sending message
    test_message = {
        'action': 'concatenate',
        'files': ['test1.py', 'test2.py']
    }
    window.send_rabbitmq_message(test_message)
    
    # Test receiving message
    window.handle_rabbitmq_message(json.dumps(test_message))

def test_file_tree_navigation(window, temp_files):
    tmp_dir, files = temp_files
    
    # Set root path
    window.tree_view.setRootIndex(window.model.index(tmp_dir))
    
    # Check if files are visible
    model = window.tree_view.model()
    root_index = window.tree_view.rootIndex()
    visible_files = []
    
    for i in range(model.rowCount(root_index)):
        index = model.index(i, 0, root_index)
        file_path = model.filePath(index)
        visible_files.append(file_path)
    
    # Check if test files are in the visible files
    assert any(os.path.basename(files[0]) in f for f in visible_files)
    assert any(os.path.basename(files[1]) in f for f in visible_files)

def test_path_combobox(window, temp_files):
    tmp_dir, files = temp_files
    
    # Set current path
    window.path_combo.addItem(tmp_dir)
    window.path_combo.setCurrentText(tmp_dir)
    
    assert window.path_combo.currentText() == tmp_dir

def test_window_state_persistence(window):
    # Modify window state
    window.resize(800, 600)
    window.save_settings()
    
    # Create new window instance
    new_window = FileConcatenator()
    
    # Check if size was restored
    assert new_window.size().width() >= 800
    assert new_window.size().height() >= 600

def test_concatenate_with_format(window, temp_files):
    tmp_dir, files = temp_files
    
    # Select files in tree view
    model = window.tree_view.model()
    for file_path in files[:2]:  # Select first two files
        index = model.index(file_path)
        window.tree_view.selectionModel().select(index, 
            window.tree_view.selectionModel().Select)
    
    # Set format options
    window.current_format['language'] = 'python'
    window.current_format['use_backticks'] = True
    window.current_format['show_filename'] = True
    
    # Concatenate files
    window.concatenate_files()
    
    # Check output
    output = window.text_output.toPlainText()
    assert '```python' in output
    assert '# File:' in output
    assert 'test1()' in output
    assert 'test2()' in output

def test_status_bar_updates(window, temp_files):
    tmp_dir, files = temp_files
    
    # Select a file
    model = window.tree_view.model()
    index = model.index(files[0])
    window.tree_view.selectionModel().select(index, 
        window.tree_view.selectionModel().Select)
    
    # Check if status bar updates
    assert window.status_label.text() != ""

def test_cleanup(window):
    # Test proper cleanup on window close
    window.close()
    assert not window.rabbitmq_thread.isRunning()