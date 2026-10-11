"""Estilo estático Qt; sem animações, efeitos ou fontes externas."""
STYLE = '''
QMainWindow, QDialog, QWidget {
    background: #f5f4f0; color: #18251d; font-size: 13px;
}
QPushButton {
    background: #ffffff; border: 1px solid #cbd4cd;
    border-radius: 4px; padding: 7px 10px;
}
QPushButton:hover { background: #e8eee9; }
QPushButton:pressed, QPushButton:checked { background: #dcecdf; }
QPushButton:disabled { color: #8b938d; background: #eeefeb; }
QPushButton:focus { border: 1px solid #1a7a4a; }
QPushButton#primary { background: #0d2b1f; color: white; font-weight: bold; }
QPushButton#primary:hover { background: #1a7a4a; }
QLabel#bookTitle { font-weight: bold; }
QLabel#status { color: #526259; font-size: 12px; }
QListWidget, QTreeWidget { background: white; border: 1px solid #d8ded8; }
QListWidget::item { padding: 8px; }
QListWidget::item:selected, QTreeWidget::item:selected { background: #dcecdf; color: #123923; }
QTabWidget::pane { border: 1px solid #d8ded8; }
QTabBar::tab { padding: 8px 10px; background: #e9ece7; }
QTabBar::tab:selected { background: white; color: #0d2b1f; }
QSpinBox, QDoubleSpinBox, QComboBox {
    background: white; border: 1px solid #cbd4cd;
    border-radius: 3px; padding: 5px; min-height: 20px;
}
QProgressBar { border: none; background: #dce3dd; border-radius: 2px; }
QProgressBar::chunk { background: #1a7a4a; border-radius: 2px; }
QSplitter::handle { background: #e3e7e1; }
'''
