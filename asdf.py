import os
import re
from pathlib import Path
from subprocess import run

from PySide6.QtGui import QCursor, Qt
from PySide6.QtWidgets import QApplication

from log import LogWidget


class ASDF:
    def __init__(self, log_widget: LogWidget | None = None, path: Path | None = None):
        self.log_widget = log_widget
        self.asdf_bin_path = path or Path('~/.asdf/bin/asdf').expanduser()
        self.current_path = Path(os.curdir).resolve()
        self.current_pattern = re.compile(r"""(\S+)\s+(\S+)\s+(.*)""")


    def asdf(self, params: list[str] | None = None, log_output: bool = True, log_success: bool = False) -> list[str]:
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        if not self.asdf_bin_path.exists():
            msg = f"asdf binary not found at {self.asdf_bin_path}."
            if self.log_widget is not None:
                self.log_widget.error(msg)
            print(msg)
            return []

        try:
            params = params or []
            cmd = [self.asdf_bin_path.as_posix()] + params

            if log_output and self.log_widget is not None:
                self.log_widget.cmd(' '.join(cmd))

            path = ':'.join([os.environ['PATH'], Path('~/.asdf/bin').expanduser().as_posix()])
            process = run(cmd, capture_output=True, cwd=self.current_path.as_posix(), env={**os.environ, 'PATH': path})

            stdout_lines = [p.decode() for p in process.stdout.splitlines()]
            if log_output:
                if stdout_lines and self.log_widget is not None:
                    [self.log_widget.info(line) for line in stdout_lines]
                # else:
                #    self.log_widget.info("(stdout empty)")

            stderr_lines = [p.decode() for p in process.stderr.splitlines()]
            if log_output:
                if stderr_lines and self.log_widget is not None:
                    [self.log_widget.stderr(line) for line in stderr_lines]
                # else:
                #    self.log_widget.info("(stderr empty)")

            if process.returncode != 0 and self.log_widget is not None:
                self.log_widget.error(f"Command {' '.join(cmd)!r} returned error code {process.returncode}.")
                return []

            if log_success and self.log_widget is not None:
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
