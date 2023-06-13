import os
import sys
from pathlib import Path

from PySide6.QtCore import QThread, QObject, Signal, QTimer
from PySide6.QtGui import QFont, Qt, QAction, QCursor
from PySide6.QtWidgets import (QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox, QToolBar,
                               QSplitter, QStyle)

from add_plugin import AddPluginDialog
from add_version import AddVersionDialog
from asdf import ASDF
from log import LogWidget
from utils import semver_sort


__version__ = "1.1.0"


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = LogWidget()
        self.log.info(f"asdfg {__version__}")
        self.log.info("© 2023 Don Welch <dwelch91@gmail.com>")
        self.log.info(f"CWD: {Path(os.curdir).resolve().as_posix()}")
        self.asdf = ASDF(self.log)
        self.latest_versions: dict[str, str] = {}
        self.asdf.info()
        self.tree = QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setColumnWidth(0, 250)
        self.tree.setColumnWidth(1, 250)
        self.tree.setColumnWidth(2, 250)
        self.tree.setHeaderLabels(['plugin/installed version(s)', 'current version', 'latest version', '.tool-versions path'])
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
        update_all_action.triggered.connect(self.update_all_plugins)
        self.toolbar.addAction(update_all_action)

        update_asdf_action = QAction(self.style().standardIcon(QStyle.SP_MediaSeekForward), "Update asdf", self)
        update_asdf_action.setToolTip("asdf update")
        update_asdf_action.triggered.connect(self.update_asdf)
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
        self.latest_thread = None

        QTimer.singleShot(0, self.refresh_tree)


    def get_latest(self, plugin: str) -> str:
        try:
            return self.latest_versions[plugin]
        except KeyError:
            latest = self.latest_versions[plugin] = self.asdf.latest_version(plugin)
            return latest


    def clear_latest(self):
        self.latest_versions.clear()


    def add_plugin(self):
        dlg = AddPluginDialog(self.asdf)
        if dlg.exec():
            plugin = dlg.plugin
            self.asdf.add_plugin(plugin)
            if dlg.install_latest_checkbox:
                latest_version = self.get_latest(plugin)
                self.asdf.add_version(plugin, latest_version)
                self.asdf.set_global_version(plugin, latest_version)
            self.clear_latest()
            self.refresh_tree()


    def add_version(self, plugin: str):
        dlg = AddVersionDialog(self.asdf, plugin)
        if dlg.exec():
            version = dlg.version
            self.asdf.add_version(plugin, version)
            if dlg.set_global_version:
                self.asdf.set_global_version(plugin, version)
            if dlg.set_local_version:
                self.asdf.set_local_version(plugin, version)
            self.refresh_tree()


    def where_version(self, plugin: str, version: str):
        where = self.asdf.where_version(plugin, version)
        box = QMessageBox(self)
        box.setWindowTitle(f"{plugin} {version}")
        box.setText(where)
        box.exec()


    def update_asdf(self):
        self.asdf.update_asdf()
        self.clear_latest()
        self.refresh_tree()


    def update_plugin(self, plugin: str):
        self.asdf.update_plugin(plugin)
        self.clear_latest()
        self.refresh_tree()


    def update_all_plugins(self):
        self.asdf.update_all_plugins()
        self.clear_latest()
        self.refresh_tree()


    def add_latest_version_and_set_global(self, plugin):
        latest_version = self.get_latest(plugin)
        if latest_version is None:
            self.log.error(f"Invalid version for plugin {plugin}.")
            return []

        self.asdf.add_version(plugin, latest_version)
        self.asdf.set_global_version(plugin, latest_version)


    def show_context_menu(self, position):
        item = self.tree.itemAt(position)
        menu = QMenu(self.tree)
        #menu.setWindowFlag(Qt.FramelessWindowHint)
        #menu.setAttribute(Qt.WA_TranslucentBackground)
        # menu.setStyleSheet("""
        #     QMenu{
        #           border-radius: 5px;
        #     }
        #     QMenu::item {
        #             background-color: transparent;
        #             padding:3px 20px;
        #             margin:5px 10px;
        #     }
        # """)
        menu.setStyleSheet("""
        QMenu{
            background-color:palette(window);
            border:1px solid palette(shadow);
        }
        
        QMenu::item{
            padding:3px 25px 3px 25px;
            border:1px solid transparent;
        }
                
        QMenu::item:selected{
            border-color:rgba(147,191,236,127);
            background:palette(highlight);
        }
        
        QMenu::separator{
            height:1px;
            background:palette(alternate-base);
            margin-left:5px;
            margin-right:5px;
        }
        
        QMenu::indicator{
            width:18px;
            height:18px;
        }
        """)
        if item.parent() is None:  # Top-level (ie, plugin)
            plugin = item.text(0)

            add_latest_version_action = QAction(f"Update {plugin} to latest version and set as GLOBAL")
            add_latest_version_action.triggered.connect(lambda: self.add_latest_version_and_set_global(plugin))
            menu.addAction(add_latest_version_action)

            add_version_action = QAction(f"Add {plugin} version...")
            add_version_action.triggered.connect(lambda: self.add_version(plugin))
            menu.addAction(add_version_action)

            set_local_system_action = QAction(f"Set local {plugin} version to system (in {self.current_path})")
            set_local_system_action.triggered.connect(lambda: self.asdf.set_local_system(plugin))
            menu.addAction(set_local_system_action)

            remove_local_version_action = QAction(f"Remove local {plugin} version, if set (use GLOBAL version)")
            remove_local_version_action.triggered.connect(lambda: self.asdf.remove_local_version(plugin))
            menu.addAction(remove_local_version_action)

            menu.addSeparator()

            set_global_system_action = QAction(f"Set GLOBAL {plugin} version to system version")
            set_global_system_action.triggered.connect(lambda: self.asdf.set_global_system(plugin))
            menu.addAction(set_global_system_action)

            menu.addSeparator()

            update_plugin_action = QAction(f"Update plugin {plugin}")
            update_plugin_action.triggered.connect(lambda: self.update_plugin(plugin))
            menu.addAction(update_plugin_action)

            uninstall_plugin_action = QAction(f"Remove plugin {plugin} (and versions)")
            uninstall_plugin_action.triggered.connect(lambda: self.asdf.remove_plugin(plugin))
            menu.addAction(uninstall_plugin_action)

        else:  # Nested (ie, version)
            parent = item.parent()
            plugin = parent.text(0)
            version = item.text(0)
            set_global_version_action = QAction(f"Set GLOBAL {plugin} version to {version}")
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

        #if menu.exec(self.tree.mapToGlobal(position)):
        if menu.exec(QCursor.pos()):
        #if menu.popup(self.tree.mapToGlobal(position)):
        #if menu.popup(self.mapToGlobal(position)):
            self.refresh_tree()


    def refresh_tree(self):
        self.tree.clear()
        current_versions = self.asdf.current_versions()
        bold_font = QFont()
        bold_font.setPointSize(12)
        bold_font.setBold(True)
        #items = []
        plugins = sorted(current_versions.keys())
        for index, plugin in enumerate(plugins):
            current, path = current_versions[plugin]
            latest = self.get_latest(plugin) or "(unknown)"
            item = QTreeWidgetItem([plugin, current, latest, path])
            if current == latest:
                item.setFont(1, bold_font)
            versions, current = self.asdf.versions_list_installed(plugin)
            for ver in semver_sort(versions):
                if 'No versions installed' not in ver:  # TODO: REVISIT!
                    child = QTreeWidgetItem([ver])
                    if ver == current:
                        child.setFont(0, bold_font)
                    item.addChild(child)
            #items.append(item)
            self.tree.insertTopLevelItem(index, item)

        #self.tree.insertTopLevelItems(0, items)

        # if self.latest_thread is None:
        #     self.latest_thread = LatestThread(plugins, self.log, self)
        #     self.latest_thread.latestSignal.connect(self.latest_thread_result)
        #     self.latest_thread.start()


    def latest_thread_result(self, plugin: str, latest: str):
        if plugin is None:
            self.latest_thread = None
            return

        print(plugin, latest)


class LatestThread(QThread):
    latestSignal = Signal(str, str)

    def __init__(self, plugins: list, log_widget: LogWidget, parent: QObject=None):
        self.plugins = plugins
        self.asdf = ASDF(None)
        super().__init__(parent)


    def run(self):
        for plugin in self.plugins:
            latest = self.asdf.latest_version(plugin)
            # print(plugin, latest)
            self.latestSignal.emit(plugin, latest)

        self.latestSignal.emit(None, None)


def main() -> int:
    app = QApplication([])
    app.setStyle('Material')
    font = QFont()
    font.setPointSize(12)
    app.setFont(font)
    widget = MainWindow()
    widget.resize(1024, 1024)
    widget.show()
    #app.processEvents()
    #latest_thread = LatestThread()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
