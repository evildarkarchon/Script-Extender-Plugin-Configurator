import configparser
from pathlib import Path

import tomlkit
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QToolTip,
    QVBoxLayout,
    QWidget,
)


class ConfigEditor(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Config File Editor")
        self.setGeometry(100, 100, 600, 400)

        self.main_layout = QVBoxLayout()
        self.init_ui()
        self.current_file_path = ""
        self.original_ini_content: list[str] = []
        self.original_toml_content = ""

    def init_ui(self) -> None:
        self.main_layout = QVBoxLayout()
        self.load_button = QPushButton("Load Config File")
        self.load_button.clicked.connect(self.load_config_file)
        self.main_layout.addWidget(self.load_button)

        self.save_button = QPushButton("Save Config File")
        self.save_button.clicked.connect(self.save_config_file)
        self.save_button.setEnabled(False)
        self.main_layout.addWidget(self.save_button)

        self.main_widget = QWidget()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

    def load_config_file(self) -> None:
        file_dialog = QFileDialog()
        options = QFileDialog().options()
        file_path, _ = file_dialog.getOpenFileName(self, "Open Config File", "", "Config Files (*.ini *.toml);;All Files (*)", options=options)

        if file_path:
            self.current_file_path = file_path
            if file_path.endswith(".ini"):
                self.load_ini_file(file_path)
            elif file_path.endswith(".toml"):
                self.load_toml_file(file_path)

        self.save_button.setEnabled(True)

    def load_ini_file(self, file_path: str) -> None:
        self.original_ini_content = Path(file_path).read_text().splitlines() or []

        parser = configparser.ConfigParser()
        parser.read_file(self.original_ini_content if self.original_ini_content else [])

        for section in parser.sections():
            section_label = QLabel(f"[{section}]")
            section_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            self.main_layout.addWidget(section_label)

            for key, value in parser.items(section):
                comment = None
                for line in self.original_ini_content:
                    if line.strip().startswith(f";{key}"):
                        comment = line.strip()
                        break
                key_line_edit = QLineEdit()
                key_line_edit.setPlaceholderText(f"{key} = {value}")
                key_line_edit.setToolTip(comment if comment else "No comment available")
                key_line_edit.setObjectName(f"{section}.{key}")
                self.main_layout.addWidget(key_line_edit)

    def load_toml_file(self, file_path: str) -> None:
        self.original_toml_content = Path(file_path).read_text() or ""
        data = tomlkit.parse(self.original_toml_content)
        self.parse_toml_data_recursive(data)

    def parse_toml_data_recursive(self, data: dict, parent_key: str = "") -> None:
        for key, value in data.items():
            full_key = f"{parent_key}.{key}" if parent_key else key
            if isinstance(value, dict):
                section_label = QLabel(f"[{full_key}]")
                section_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                self.main_layout.addWidget(section_label)
                self.parse_toml_data_recursive(value, full_key)
            else:
                key_line_edit = QLineEdit()
                key_line_edit.setPlaceholderText(f"{key} = {value}")
                comment = value.trivia.comment if hasattr(value, 'trivia') and value.trivia.comment else None
                key_line_edit.setToolTip(comment if comment else "No comment available")
                key_line_edit.setObjectName(full_key)
                self.main_layout.addWidget(key_line_edit)

    def save_config_file(self) -> None:
        if not self.current_file_path:
            QMessageBox.warning(self, "Warning", "No file loaded to save.", QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.NoButton)
            return

        if self.current_file_path.endswith(".ini"):
            self.save_ini_file()
        elif self.current_file_path.endswith(".toml"):
            self.save_toml_file()

    def save_ini_file(self) -> None:
        parser = configparser.ConfigParser()
        parser.read_file(self.original_ini_content)

        for section in parser.sections():
            for key in parser[section]:
                line_edit = self.findChild(QLineEdit, f"{section}.{key}")
                if line_edit:
                    parser[section][key] = line_edit.text() if line_edit.text() else parser[section][key]

        with Path(self.current_file_path).open('w', encoding='utf-8') as file:
            if self.original_ini_content:
                for line in self.original_ini_content:
                    file.write(line)
                    if line.strip().startswith('['):
                        section = line.strip()[1:-1]
                        if section in parser:
                            for key, value in parser.items(section):
                                file.write(f"{key} = {value}\n")

    def save_toml_file(self) -> None:
        self.original_toml_content = Path(self.current_file_path).read_text() or ""
        data = tomlkit.parse(self.original_toml_content)

        for key in data:
            line_edit = self.findChild(QLineEdit, key)
            if line_edit:
                data[key] = line_edit.text() if line_edit.text() else data[key]

        Path(self.current_file_path).write_text(tomlkit.dumps(data), encoding='utf-8')


if __name__ == "__main__":
    app = QApplication([])
    QToolTip.setFont(QFont("Arial", 10))

    editor = ConfigEditor()
    editor.show()

    app.exec()
