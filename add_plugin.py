from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QListWidget, QListWidgetItem, QCheckBox

from asdf import ASDF


class AddPluginDialog(QDialog):
    def __init__(self, asdf: ASDF):
        super().__init__()
        self.plugin = None
        self.setWindowTitle("Add plugin")
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(super().reject)
        self.install_latest_checkbox = QCheckBox("Install latest version and set as GLOBAL version")
        self.install_latest_checkbox.setChecked(True)
        self.layout = QVBoxLayout()
        self.listbox = QListWidget()
        self.layout.addWidget(self.listbox)
        self.layout.addWidget(self.install_latest_checkbox)
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
