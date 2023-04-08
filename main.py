import os
import re
import sys
from pathlib import Path
from subprocess import check_output, CalledProcessError, STDOUT

from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QFont, Qt, QAction, QCursor
from PySide6.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox, QToolBar, \
    QDialog, QListWidget, QDialogButtonBox, QVBoxLayout, QListWidgetItem, QSplitter, QPlainTextEdit, QStyle

cwd = Path(__file__).parent
__version__ = "0.0.1"

CURRENT_PATTERN = re.compile(r"""(\S+)\s+(\S+)\s+(.*)""")


class LogWidget(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)


    def appendLogLine(self, line: str):
        self.appendPlainText(line)
        vert_scrollbar = self.verticalScrollBar()
        vert_scrollbar.setValue(vert_scrollbar.maximum())
        QCoreApplication.processEvents()


class ASDF:
    def __init__(self, log_widget: LogWidget, path: Path | None = None):
        self.log_widget = log_widget
        self.asdf_bin_path = path or Path('~/.asdf/bin/asdf').expanduser()


    def run(self, params: list[str] | None = None, log_output: bool = True) -> list[str]:
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            params = params or []
            cmd = [self.asdf_bin_path.as_posix()] + params
            self.log_widget.appendLogLine(f"CMD: {' '.join(cmd)}")
            try:
                output = check_output(cmd, cwd=Path(os.curdir).resolve().as_posix(), stderr=STDOUT)
            except CalledProcessError as e:
                self.log_widget.appendLogLine(f"ERROR: {e}")
                return []

            output_lines = [p.decode() for p in output.splitlines()]
            if log_output:
                if output:
                    [self.log_widget.appendLogLine(line) for line in output_lines]
                else:
                    self.log_widget.appendLogLine("OK.")

            return output_lines
        finally:
            QApplication.restoreOverrideCursor()


    def info(self):
        return self.run(['info'])


    def plugins_list_all(self):
        return [p.split()[0] for p in self.run(['plugin', 'list', 'all'], log_output=False)]


    def plugins_list_installed(self) -> list[str]:
        return self.run(['plugin', 'list'], log_output=False)


    def versions_list_installed(self, plugin: str) -> tuple[list[str], str | None]:
        output = self.run(['list', plugin], log_output=False)
        current = None
        versions = []
        for line in output:
            striped_line = line.strip()
            if striped_line.startswith('*'):
                current = striped_line[1:]
                versions.append(current)
            else:
                versions.append(striped_line)
        return versions, current


    def versions_list_all(self, plugin: str) -> list[str]:
        return self.run(['list', 'all', plugin], log_output=False)


    def set_global_version(self, plugin: str, version: str) -> list[str]:
        return self.run(['global', plugin, version])


    def set_local_version(self, plugin: str, version: str) -> list[str]:
        return self.run(['local', plugin, version])


    def uninstall_plugin(self, plugin: str) -> list[str]:
        return self.run(['plugin', 'remove', plugin])


    def update_plugin(self, plugin: str) -> list[str]:
        return self.run(['plugin', 'update', plugin])


    def add_version(self, plugin: str, version: str):
        return self.run(['install', plugin, version])


    def add_plugin(self, plugin: str) -> list[str]:
        return self.run(['plugin', 'add', plugin])


    def remove_plugin(self, plugin: str) -> list[str]:
        return self.run(['plugin', 'remove', plugin])


    def where_version(self, plugin: str, version: str) -> str:
        return self.run(['where', plugin, version])[0]


    def uninstall_version(self, plugin: str, version: str) -> list[str]:
        return self.run(['uninstall', plugin, version])


    def reshim_version(self, plugin: str, version: str) -> list[str]:
        return self.run(['reshim', plugin, version])


    def update_all_plugins(self) -> list[str]:
        return self.run(['plugin', 'update', '--all'])


    def current_versions(self) -> dict:
        current = {}
        for line in self.run(['current'], log_output=False):
            if (m := CURRENT_PATTERN.match(line)) is not None:
                current[m.group(1)] = (m.group(2), m.group(3))
        return current


    def update_asdf(self) -> list[str]:
        return self.run(['update'])


    def latest_version(self, plugin: str) -> str:
        return self.run(['latest', plugin])[0]


    def set_local_system(self, plugin: str):
        return self.run(['local', plugin, 'system'])


    def set_global_system(self, plugin: str):
        return self.run(['global', plugin, 'system'])


class AddPluginDialog(QDialog):
    def __init__(self, asdf: ASDF):
        super().__init__()
        self.plugin = None
        self.setWindowTitle("Add plugin")
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(super().reject)
        self.layout = QVBoxLayout()
        self.listbox = QListWidget()
        self.layout.addWidget(self.listbox)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)
        all_plugins = set(asdf.plugins_list_all())
        installed_plugins = set(asdf.plugins_list_installed())
        not_installed_plugins = sorted(list(all_plugins - installed_plugins))
        self.listbox.addItems(not_installed_plugins)
        self.listbox.currentItemChanged.connect(self.current_item_changed)


    def current_item_changed(self, current: QListWidgetItem):
        self.plugin = current.text()
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)


class AddVersionDialog(QDialog):
    def __init__(self, asdf: ASDF, plugin: str):
        super().__init__()
        self.plugin = plugin
        self.version = None
        latest = asdf.latest_version(plugin)
        self.setWindowTitle(f"Add version for {plugin} (latest={latest})")
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(super().reject)
        self.layout = QVBoxLayout()
        self.listbox = QListWidget()
        self.layout.addWidget(self.listbox)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)
        all_versions = set(asdf.versions_list_all(plugin))
        all_installed_versions = set(asdf.versions_list_installed(plugin)[0])
        not_installed_versions = sorted(list(all_versions - all_installed_versions))
        self.listbox.addItems(not_installed_versions)
        self.listbox.currentItemChanged.connect(self.current_item_changed)


    def current_item_changed(self, current: QListWidgetItem):
        self.version = current.text()
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = LogWidget()
        self.asdf = ASDF(self.log)
        self.asdf.info()
        self.log.appendLogLine(f"CWD: {Path(os.curdir).resolve().as_posix()}")
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setColumnWidth(0, 250)
        self.tree.setColumnWidth(1, 250)
        self.tree.setHeaderLabels(['plugin', 'version', 'path/message'])
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.setWindowTitle("asdfg")

        self.toolbar = QToolBar("asdfg")
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        refresh_action = QAction(self.style().standardIcon(QStyle.SP_BrowserReload), "Refresh", self)
        refresh_action.triggered.connect(self.refresh_tree)
        self.toolbar.addAction(refresh_action)

        update_all_action = QAction(self.style().standardIcon(QStyle.SP_MediaSeekForward), "Update plugins", self)
        update_all_action.triggered.connect(self.asdf.update_all_plugins)
        self.toolbar.addAction(update_all_action)

        update_asdf_action = QAction(self.style().standardIcon(QStyle.SP_MediaSeekForward), "Update asdf", self)
        update_asdf_action.triggered.connect(self.asdf.update_asdf)
        self.toolbar.addAction(update_asdf_action)

        add_plugin_action = QAction(self.style().standardIcon(QStyle.SP_FileDialogListView), "Add plugin", self)
        add_plugin_action.triggered.connect(self.add_plugin)
        self.toolbar.addAction(add_plugin_action)

        clear_log_output_action = QAction(self.style().standardIcon(QStyle.SP_DialogResetButton), "Clear log", self)
        clear_log_output_action.triggered.connect(self.log.clear)
        self.toolbar.addAction(clear_log_output_action)

        self.addToolBar(self.toolbar)

        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Vertical)

        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(self.log)

        self.setCentralWidget(self.splitter)

        self.refresh_tree()


    def add_plugin(self):
        dlg = AddPluginDialog(self.asdf)
        if dlg.exec():
            self.asdf.add_plugin(dlg.plugin)
            self.refresh_tree()


    def add_version(self, plugin: str):
        dlg = AddVersionDialog(self.asdf, plugin)
        if dlg.exec():
            self.asdf.add_version(plugin, dlg.version)
            self.refresh_tree()


    def where_version(self, plugin: str, version: str):
        where = self.asdf.where_version(plugin, version)
        box = QMessageBox(self)
        box.setWindowTitle(f"{plugin} {version}")
        box.setText(where)
        box.exec()


    def show_context_menu(self, position):
        item = self.tree.itemAt(position)
        menu = QMenu(self.tree)
        if item.parent() is None:  # Top-level (ie, plugin)
            plugin = item.text(0)
            add_version_action = QAction(f"Add {plugin} version...")
            add_version_action.triggered.connect(lambda: self.add_version(plugin))
            menu.addAction(add_version_action)

            set_local_system_action = QAction(f"Set local {plugin} version to system")
            set_local_system_action.triggered.connect(lambda: self.asdf.set_local_system(plugin))
            menu.addAction(set_local_system_action)

            set_global_system_action = QAction(f"Set global {plugin} version to system")
            set_global_system_action.triggered.connect(lambda: self.asdf.set_global_system(plugin))
            menu.addAction(set_global_system_action)

            update_plugin_action = QAction(f"Update plugin {plugin}")
            update_plugin_action.triggered.connect(lambda: self.asdf.update_plugin(plugin))
            menu.addAction(update_plugin_action)

            uninstall_plugin_action = QAction(f"Uninstall plugin {plugin}")
            uninstall_plugin_action.triggered.connect(lambda: self.asdf.uninstall_plugin(plugin))
            menu.addAction(uninstall_plugin_action)

        else:  # Nested (ie, version)
            parent = item.parent()
            plugin = parent.text(0)
            version = item.text(0)
            set_global_version_action = QAction(f"Set global {plugin} version to {version}")
            set_global_version_action.triggered.connect(lambda: self.asdf.set_global_version(plugin, version))
            menu.addAction(set_global_version_action)

            set_local_version_action = QAction(f"Set local {plugin} version to {version}")
            set_local_version_action.triggered.connect(lambda: self.asdf.set_local_version(plugin, version))
            menu.addAction(set_local_version_action)

            menu.addSeparator()

            reshim_version_action = QAction(f"Re-shim {plugin} version {version}")
            reshim_version_action.triggered.connect(lambda: self.asdf.reshim_version(plugin, version))
            menu.addAction(reshim_version_action)

            uninstall_version_action = QAction(f"Uninstall {plugin} version {version}")
            uninstall_version_action.triggered.connect(lambda: self.asdf.uninstall_version(plugin, version))
            menu.addAction(uninstall_version_action)

            where_version_action = QAction(f"Where is {plugin} version {version}?")
            where_version_action.triggered.connect(lambda: self.where_version(plugin, version))
            menu.addAction(where_version_action)

        menu.exec(self.tree.mapToGlobal(position))
        self.refresh_tree()


    def refresh_tree(self):
        self.tree.clear()
        current_versions = self.asdf.current_versions()
        bold_font = QFont()
        bold_font.setPointSize(14)
        bold_font.setBold(True)
        items = []
        for plugin, (version, path) in current_versions.items():
            item = QTreeWidgetItem([plugin, version, path])
            versions, current = self.asdf.versions_list_installed(plugin)
            for ver in versions:
                if 'No versions installed' not in ver:  # TODO: REVISIT!
                    child = QTreeWidgetItem([ver])
                    if ver == current:
                        child.setFont(0, bold_font)
                    item.addChild(child)
            items.append(item)

        self.tree.insertTopLevelItems(0, items)


def main() -> int:
    print(f"asdfg v{__version__}")
    print("Loading...")
    app = QApplication([])
    font = QFont()
    font.setPointSize(14)
    app.setFont(font)
    widget = MainWindow()
    widget.resize(1024, 1024)
    widget.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
