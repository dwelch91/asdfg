from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QListWidget, QListWidgetItem, QHBoxLayout, \
    QCheckBox

from utils import semver_sort
from asdf import ASDF


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
        self.check_layout = QHBoxLayout()
        self.set_global_version = QCheckBox("Set as GLOBAL version")
        self.set_global_version.setChecked(True)
        self.set_local_version = QCheckBox("Set as local version")
        self.check_layout.addWidget(self.set_global_version)
        self.check_layout.addWidget(self.set_local_version)
        self.layout = QVBoxLayout()
        self.listbox = QListWidget()
        self.layout.addWidget(self.listbox)
        self.layout.addLayout(self.check_layout)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)
        all_versions = set(asdf.versions_list_all(plugin))
        all_installed_versions = set(asdf.versions_list_installed(plugin)[0])
        not_installed_versions = semver_sort(list(all_versions - all_installed_versions))
        self.listbox.addItems(not_installed_versions)
        self.listbox.currentItemChanged.connect(self.current_item_changed)


    def current_item_changed(self, current: QListWidgetItem):
        self.version = current.text()
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
