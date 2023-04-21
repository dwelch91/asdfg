from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QTextEdit


class LogWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        font.setPointSize(11)
        self.setFont(font)


    def scroll_to_end(self):
        vert_scrollbar = self.verticalScrollBar()
        vert_scrollbar.setValue(vert_scrollbar.maximum())
        QCoreApplication.processEvents()


    def info(self, line: str):
        self.append(line)
        self.scroll_to_end()


    def cmd(self, line: str):
        self.append(f"<font color=cyan>CMD: {line}</font>")
        self.scroll_to_end()


    def ok(self, line: str | None = None):
        self.append(f"<font color=green>{line or 'OK'}</font>")
        self.scroll_to_end()


    def warning(self, line: str):
        self.append(f"<font color=orange>WARNING: {line}</font>")
        self.scroll_to_end()


    def error(self, line: str):
        self.append(f"<font color=red>ERROR: {line}</font>")
        self.scroll_to_end()


    def stderr(self, line: str):
        self.append(f"<font color=yellow>STDERR: {line}</font>")
        self.scroll_to_end()
