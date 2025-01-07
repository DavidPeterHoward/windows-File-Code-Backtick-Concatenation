import sys, os
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QSplitter, QVBoxLayout, QWidget,
    QTreeView, QFileSystemModel, QPlainTextEdit, QTabWidget, QCheckBox,
    QLineEdit, QPushButton, QListWidget, QLabel, QMessageBox, QHBoxLayout, QAction, QFrame, QFileDialog
)
from PyQt5.QtCore import Qt, QDir, QSize, pyqtSignal, QSettings, QUrl, QTemporaryFile, QMimeData
from PyQt5.QtGui import QIcon, QPalette, QColor, QFont, QSyntaxHighlighter, QTextCharFormat, QDrag
import qtawesome as qta

class CompactToolBar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MainToolBar")
        self.setIconSize(QSize(16, 16))
        self.setFixedHeight(28)
        self.setStyleSheet("""
            QToolBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                spacing: 2px;
                padding: 2px;
            }
            QToolButton {
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 2px;
            }
            QToolButton:hover {
                background-color: #e9ecef;
                border: 1px solid #dee2e6;
            }
        """)

class EnhancedTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTreeView {
                background-color: white;
                border: none;
            }
            QTreeView::item {
                padding: 2px;
                height: 22px;
            }
            QTreeView::item:hover {
                background-color: #f8f9fa;
            }
            QTreeView::item:selected {
                background-color: #e9ecef;
                color: black;
            }
        """)
        self.model = QFileSystemModel()
        self.model.setRootPath("")
        self.model.setFilter(QDir.AllDirs | QDir.AllEntries | QDir.NoDotAndDotDot)
        self.setModel(self.model)
        self.setRootIndex(self.model.index(""))
        self.setSelectionMode(QTreeView.ExtendedSelection)
        self.header().setDefaultSectionSize(200)
        self.header().setStretchLastSection(True)
        self.expanded.connect(self._auto_resize)
        self.clicked.connect(self._auto_resize)

    def _auto_resize(self):
        for i in range(4):
            self.resizeColumnToContents(i)

class DraggableTextEdit(QPlainTextEdit):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not hasattr(self, 'drag_start_position'):
            return

        if (event.buttons() & Qt.LeftButton) and \
           (event.pos() - self.drag_start_position).manhattanLength() > QApplication.startDragDistance():
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.toPlainText())
            
            # Create temporary file for drag and drop
            temp_file = QTemporaryFile()
            if temp_file.open():
                temp_file.write(self.toPlainText().encode())
                temp_file.flush()
                urls = [QUrl.fromLocalFile(temp_file.fileName())]
                mime_data.setUrls(urls)
                temp_file.setParent(drag)  # This keeps the temp file alive during drag
            
            drag.setMimeData(mime_data)
            drag.exec_(Qt.CopyAction)

class ContentTabs(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDocumentMode(True)
        self.setTabsClosable(False)
        self.content_editor = DraggableTextEdit()
        self.content_editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.content_editor.setFont(QFont("Consolas", 10))
        self.addTab(self.content_editor, "Content")

    def set_content(self, content):
        self.content_editor.setPlainText(content)

class MainWindow(QMainWindow):
    def __init__(self, initial_path=None):
        super().__init__()
        self.setWindowTitle("File Concatenator")
        self.setGeometry(100, 100, 1400, 800)
        
        icon_path = os.path.join(os.path.dirname(__file__), 'file_concatenator.ico')
        self.setWindowIcon(QIcon(icon_path))
            
        self.recent_folders = []
        self.show_absolute_paths = True
        self._create_ui()
        self._load_settings()
        
        if initial_path:
            self._initialize_with_path(initial_path)

    def _initialize_with_path(self, path):
        if os.path.exists(path):
            if os.path.isfile(path):
                path = os.path.dirname(path)
            self.file_tree.setRootIndex(self.file_tree.model.index(path))
            self.path_input.setText(path)
            self._add_recent_folder(path)
            self.statusBar().showMessage(f"Opened path: {path}")

    def _create_ui(self):
        self.setStyleSheet("""
            QMainWindow { background-color: white; }
            QSplitter::handle { background-color: #dee2e6; }
            QStatusBar { background-color: #f8f9fa; color: #495057; }
        """)
        toolbar = CompactToolBar()
        toolbar.setObjectName("MainToolBar")
        self.addToolBar(toolbar)

        actions = [
            ("refresh", "Refresh View (Ctrl+R)", "fa5s.sync", self._refresh),
            ("copy", "Copy to Clipboard (Ctrl+C)", "fa5s.copy", self._copy),
            ("paste", "Paste from Clipboard (Ctrl+V)", "fa5s.paste", self._paste),
            ("open", "Open Folder", "fa5s.folder-open", self._open_folder)
        ]
        for _, tooltip, icon, handler in actions:
            action = QAction(qta.icon(icon), "", self)
            action.setToolTip(tooltip)
            action.triggered.connect(handler)
            toolbar.addAction(action)

        self.path_toggle = QCheckBox("Show Absolute Paths")
        self.path_toggle.setChecked(self.show_absolute_paths)
        self.path_toggle.stateChanged.connect(self._toggle_path_mode)
        toolbar.addWidget(self.path_toggle)

        self.nav_bar = QToolBar("Navigation Bar", self)
        self.nav_bar.setObjectName("NavigationBar")
        self.nav_bar.setMovable(False)
        self.nav_bar.setStyleSheet("""
            QToolBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                spacing: 2px;
                padding: 2px;
            }
        """)
        self.addToolBar(self.nav_bar)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Enter folder path...")
        self.path_input.returnPressed.connect(self._navigate_to_path)
        self.nav_button = QPushButton("Go")
        self.nav_button.clicked.connect(self._navigate_to_path)
        self.nav_bar.addWidget(QLabel("Path: "))
        self.nav_bar.addWidget(self.path_input)
        self.nav_bar.addWidget(self.nav_button)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.file_tree = EnhancedTreeView()
        left_layout.addWidget(self.file_tree)

        self.recent_folders_widget = QListWidget()
        self.recent_folders_widget.setFixedHeight(80)
        self.recent_folders_widget.itemClicked.connect(self._navigate_to_recent)
        recent_label = QLabel("Recently Opened Folders:")
        recent_label.setContentsMargins(2, 0, 0, 0)
        left_layout.addWidget(recent_label)
        left_layout.addWidget(self.recent_folders_widget)

        splitter.addWidget(left_panel)
        self.content_tabs = ContentTabs()
        splitter.addWidget(self.content_tabs)
        splitter.setSizes([400, 800])
        layout.addWidget(splitter)
        self.statusBar().showMessage("Ready")
        self.file_tree.selectionModel().selectionChanged.connect(self._on_selection_changed)

    def _get_language_from_extension(self, file_path):
        ext = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.html': 'html',
            '.css': 'css',
            '.java': 'java',
            '.cpp': 'cpp',
            '.h': 'cpp',
            '.c': 'c',
            '.sh': 'bash',
            '.md': 'markdown',
            '.json': 'json',
            '.xml': 'xml',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.ps1': 'ps1',
            '.sql': 'sql',
            '.ini': 'ini',
            '.txt': 'text'
        }
        return language_map.get(ext, '')

    def _get_formatted_path(self, path):
        if self.show_absolute_paths:
            return os.path.abspath(path)
        root_index = self.file_tree.rootIndex()
        root_path = self.file_tree.model.filePath(root_index)
        return os.path.relpath(path, root_path)

    def _on_selection_changed(self, selected, deselected):
        content = []
        selected_indexes = self.file_tree.selectionModel().selectedIndexes()
        
        unique_paths = set()
        for index in selected_indexes:
            if index.column() == 0:
                path = self.file_tree.model.filePath(index)
                if os.path.isfile(path):
                    unique_paths.add(path)
        
        for file_path in sorted(unique_paths):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    formatted_path = self._get_formatted_path(file_path)
                    language = self._get_language_from_extension(file_path)
                    content.extend([
                        f"# File: {formatted_path}",
                        f"```{language}" if language else "",
                        f.read(),
                        "```" if language else "",
                        ""
                    ])
            except Exception as e:
                content.append(f"# Error reading {formatted_path}: {str(e)}")

        self.content_tabs.set_content('\n'.join(content))
        self.statusBar().showMessage(f"Selected {len(unique_paths)} file(s)")
    
    def _refresh(self): self.file_tree.model.setRootPath("")
    def _copy(self): QApplication.clipboard().setText(self.content_tabs.content_editor.toPlainText())
    def _paste(self): self.content_tabs.content_editor.setPlainText(QApplication.clipboard().text())

    def _open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open Folder", os.getcwd())
        if folder:
            self._add_recent_folder(folder)
            self.file_tree.setRootIndex(self.file_tree.model.index(folder))
            self.path_input.setText(folder)
            self.statusBar().showMessage(f"Opened folder: {folder}")

    def _navigate_to_path(self):
        path = self.path_input.text().strip()
        if os.path.isdir(path):
            self.file_tree.setRootIndex(self.file_tree.model.index(path))
            self._add_recent_folder(path)
        else:
            QMessageBox.warning(self, "Error", "The specified path is invalid.")

    def _add_recent_folder(self, folder):
        if folder not in self.recent_folders:
            self.recent_folders.insert(0, folder)
            if len(self.recent_folders) > 5:
                self.recent_folders.pop()
            self.recent_folders_widget.clear()
            self.recent_folders_widget.addItems(self.recent_folders)

    def _navigate_to_recent(self, item):
        folder = item.text()
        if os.path.exists(folder):
            self.file_tree.setRootIndex(self.file_tree.model.index(folder))
            self.path_input.setText(folder)
        else:
            QMessageBox.warning(self, "Error", "Folder no longer exists.")
            self.recent_folders.remove(folder)
            self.recent_folders_widget.takeItem(self.recent_folders_widget.row(item))

    def _toggle_path_mode(self, state):
        self.show_absolute_paths = state == Qt.Checked
        self._on_selection_changed(self.file_tree.selectionModel().selection(), None)

    def _load_settings(self):
        try:
            settings = QSettings('FileConcatenator', 'Settings')
            if settings.contains('geometry'):
                self.restoreGeometry(settings.value('geometry'))
            if settings.contains('windowState'):
                self.restoreState(settings.value('windowState'))
            if settings.contains('show_absolute_paths'):
                self.show_absolute_paths = settings.value('show_absolute_paths', type=bool)
            else:
                self.show_absolute_paths = True
            self.path_toggle.setChecked(self.show_absolute_paths)
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.show_absolute_paths = True
            self.path_toggle.setChecked(True)

    def closeEvent(self, event):
        try:
            settings = QSettings('FileConcatenator', 'Settings')
            settings.setValue('geometry', self.saveGeometry())
            settings.setValue('windowState', self.saveState())
            settings.setValue('show_absolute_paths', self.show_absolute_paths)
            settings.sync()
        except Exception as e:
            print(f"Error saving settings: {e}")
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    initial_path = None
    if len(sys.argv) > 1:
        initial_path = sys.argv[1]
    
    window = MainWindow(initial_path)
    window.show()
    sys.exit(app.exec_())