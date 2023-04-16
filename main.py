import os
import re
import sys
from pathlib import Path
from subprocess import run

from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QFont, Qt, QAction, QCursor, QFontDatabase
from PySide6.QtWidgets import (QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox, QToolBar,
                               QDialog, QListWidget, QDialogButtonBox, QVBoxLayout, QListWidgetItem, QSplitter, QStyle,
                               QTextEdit)

__version__ = "0.0.5"


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


class ASDF:
    def __init__(self, log_widget: LogWidget, path: Path | None = None):
        self.log_widget = log_widget
        self.asdf_bin_path = path or Path('~/.asdf/bin/asdf').expanduser()
        self.current_path = Path(os.curdir).resolve()
        self.current_pattern = re.compile(r"""(\S+)\s+(\S+)\s+(.*)""")


    def asdf(self, params: list[str] | None = None, log_output: bool = True, log_success: bool = False) -> list[str]:
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        if not self.asdf_bin_path.exists():
            self.log_widget.error(f"asdf binary not found at {self.asdf_bin_path}.")
            return []

        try:
            params = params or []
            cmd = [self.asdf_bin_path.as_posix()] + params
            if log_output:
                self.log_widget.cmd(' '.join(cmd))

            process = run(cmd, capture_output=True, cwd=self.current_path.as_posix())

            stdout_lines = [p.decode() for p in process.stdout.splitlines()]
            if log_output:
                if stdout_lines:
                    [self.log_widget.info(line) for line in stdout_lines]
                # else:
                #    self.log_widget.info("(stdout empty)")

            stderr_lines = [p.decode() for p in process.stderr.splitlines()]
            if log_output:
                if stderr_lines:
                    [self.log_widget.error(line) for line in stderr_lines]
                # else:
                #    self.log_widget.info("(stderr empty)")

            if process.returncode != 0:
                self.log_widget.error(f"Command {' '.join(cmd)!r} returned error code {process.returncode}.")
                return []

            if log_success:
                self.log_widget.ok(f"Command {' '.join(cmd)!r} completed successfully.")

            return stdout_lines + stderr_lines
        finally:
            QApplication.restoreOverrideCursor()


    def info(self):
        return self.asdf(['info'])


    def plugins_list_all(self):
        return [p.split()[0] for p in self.asdf(['plugin', 'list', 'all'], log_output=False)]


    def plugins_list_installed(self) -> list[str]:
        return self.asdf(['plugin', 'list'], log_output=False)


    def versions_list_installed(self, plugin: str) -> tuple[list[str], str | None]:
        output = self.asdf(['list', plugin], log_output=False)
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
        return self.asdf(['list', 'all', plugin], log_output=False)


    def set_global_version(self, plugin: str, version: str) -> list[str]:
        return self.asdf(['global', plugin, version])


    def set_local_version(self, plugin: str, version: str) -> list[str]:
        return self.asdf(['local', plugin, version])


    def update_plugin(self, plugin: str) -> list[str]:
        return self.asdf(['plugin', 'update', plugin])


    def add_version(self, plugin: str, version: str) -> list[str]:
        self.log_widget.warning(f"Installing {plugin} {version}. This may take a few moments...")
        output = self.asdf(['install', plugin, version], log_success=True)
        return output


    def add_plugin(self, plugin: str) -> list[str]:
        return self.asdf(['plugin', 'add', plugin])


    def remove_plugin(self, plugin: str) -> list[str]:
        return self.asdf(['plugin', 'remove', plugin])


    def where_version(self, plugin: str, version: str) -> str | None:
        output = self.asdf(['where', plugin, version])
        return output[0] if output else None


    def uninstall_version(self, plugin: str, version: str) -> list[str]:
        return self.asdf(['uninstall', plugin, version])


    def reshim_version(self, plugin: str, version: str) -> list[str]:
        return self.asdf(['reshim', plugin, version])


    def update_all_plugins(self) -> list[str]:
        return self.asdf(['plugin', 'update', '--all'])


    def current_versions(self) -> dict:
        current = {}
        output = self.asdf(['current'], log_output=False)
        for line in output:
            if (m := self.current_pattern.match(line)) is not None:
                current[m.group(1)] = (m.group(2), m.group(3))
        return current


    def update_asdf(self) -> list[str]:
        return self.asdf(['update'])


    def latest_version(self, plugin: str) -> str | None:
        output = self.asdf(['latest', plugin])
        return output[0] if output else None


    def set_local_system(self, plugin: str):
        return self.asdf(['local', plugin, 'system'])


    def set_global_system(self, plugin: str):
        return self.asdf(['global', plugin, 'system'])


    def install_versions(self):
        return self.asdf(['install'])


    def remove_local_version(self, plugin: str):
        tool_version_path = self.current_path / '.tool-versions'
        if not tool_version_path.exists():
            self.log_widget.error(f".tool-versions file not found in {self.current_path}.")
            return

        current_lines = tool_version_path.read_text('utf-8').splitlines()
        if current_lines:
            self.log_widget.info(f"Existing {tool_version_path} file:")
            [self.log_widget.info(line) for line in current_lines]
        else:
            self.log_widget.error(f"{tool_version_path} file is empty.")
            return

        new_lines = [line for line in current_lines if not line.startswith(plugin)]
        if new_lines != current_lines:
            if not new_lines:
                self.log_widget.warning(f"Updated {tool_version_path} file is now empty.")
            else:
                self.log_widget.info(f"Updated {tool_version_path} file:")
                [self.log_widget.info(line) for line in new_lines]
            tool_version_path.write_text('\n'.join(new_lines), 'utf-8')
        else:
            self.log_widget.error(f"{plugin} not found in {tool_version_path}.")


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
        latest = asdf.latest_version(plugin) or "(unknown)"
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
        pattern = re.compile(r"""([^\-.0-9]+)?[\-.]?(\d+)?\.?(\d+)?\.?(\d+)?[\-.]?(.*)?""")

        def key_func(x: str):
            m = pattern.match(x)
            return [m.group(1) or '', int(m.group(2) or '0'), int(m.group(3) or '0'), int(m.group(4) or '0'),
                    m.group(5) or '~']

        not_installed_versions = sorted(list(all_versions - all_installed_versions), key=key_func)
        self.listbox.addItems(not_installed_versions)
        self.listbox.currentItemChanged.connect(self.current_item_changed)


    def current_item_changed(self, current: QListWidgetItem):
        self.version = current.text()
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = LogWidget()
        self.log.info(f"asdfg {__version__}")
        self.log.info(f"CWD: {Path(os.curdir).resolve().as_posix()}")
        self.asdf = ASDF(self.log)
        self.asdf.info()
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setColumnWidth(0, 250)
        self.tree.setColumnWidth(1, 250)
        self.tree.setHeaderLabels(['plugin/installed version(s)', 'current version', '.tool-versions path'])
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.setWindowTitle(f"asdfg - {self.asdf.current_path}")

        self.toolbar = QToolBar("asdfg")
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        refresh_action = QAction(self.style().standardIcon(QStyle.SP_BrowserReload), "Refresh", self)
        refresh_action.triggered.connect(self.refresh_tree)
        self.toolbar.addAction(refresh_action)

        install_versions_action = QAction(self.style().standardIcon(QStyle.SP_MediaPlay), "Install versions", self)
        install_versions_action.setToolTip("asdf install")
        install_versions_action.triggered.connect(self.asdf.install_versions)
        self.toolbar.addAction(install_versions_action)

        update_all_action = QAction(self.style().standardIcon(QStyle.SP_MediaSeekForward), "Update plugins", self)
        update_all_action.setToolTip("asdf plugin update --all")
        update_all_action.triggered.connect(self.asdf.update_all_plugins)
        self.toolbar.addAction(update_all_action)

        update_asdf_action = QAction(self.style().standardIcon(QStyle.SP_MediaSeekForward), "Update asdf", self)
        update_asdf_action.setToolTip("asdf update")
        update_asdf_action.triggered.connect(self.asdf.update_asdf)
        self.toolbar.addAction(update_asdf_action)

        add_plugin_action = QAction(self.style().standardIcon(QStyle.SP_FileDialogListView), "Add plugin", self)
        add_plugin_action.setToolTip("asdf plugin add")
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

        self.current_path = Path(os.curdir).resolve()
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

            set_local_system_action = QAction(f"Set local {plugin} version to system (in {self.current_path})")
            set_local_system_action.triggered.connect(lambda: self.asdf.set_local_system(plugin))
            menu.addAction(set_local_system_action)

            remove_local_version_action = QAction(f"Remove local {plugin} version, if set (use global version)")
            remove_local_version_action.triggered.connect(lambda: self.asdf.remove_local_version(plugin))
            menu.addAction(remove_local_version_action)

            menu.addSeparator()

            set_global_system_action = QAction(f"Set global {plugin} version to system")
            set_global_system_action.triggered.connect(lambda: self.asdf.set_global_system(plugin))
            menu.addAction(set_global_system_action)

            menu.addSeparator()

            update_plugin_action = QAction(f"Update plugin {plugin}")
            update_plugin_action.triggered.connect(lambda: self.asdf.update_plugin(plugin))
            menu.addAction(update_plugin_action)

            uninstall_plugin_action = QAction(f"Remove plugin {plugin} (and versions)")
            uninstall_plugin_action.triggered.connect(lambda: self.asdf.remove_plugin(plugin))
            menu.addAction(uninstall_plugin_action)

        else:  # Nested (ie, version)
            parent = item.parent()
            plugin = parent.text(0)
            version = item.text(0)
            set_global_version_action = QAction(f"Set global {plugin} version to {version}")
            set_global_version_action.triggered.connect(lambda: self.asdf.set_global_version(plugin, version))
            menu.addAction(set_global_version_action)

            set_local_version_action = QAction(f"Set local {plugin} version to {version} (in {self.current_path})")
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

        if menu.exec(self.tree.mapToGlobal(position)):
            self.refresh_tree()


    def refresh_tree(self):
        self.tree.clear()
        current_versions = self.asdf.current_versions()
        bold_font = QFont()
        bold_font.setPointSize(12)
        bold_font.setBold(True)
        items = []
        for plugin in sorted(current_versions.keys()):
            version, path = current_versions[plugin]
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
    app = QApplication([])
    font = QFont()
    font.setPointSize(12)
    app.setFont(font)
    widget = MainWindow()
    widget.resize(1024, 1024)
    widget.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
