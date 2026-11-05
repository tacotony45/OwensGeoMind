
import json
import platform
import webbrowser
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

from qgis.PyQt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
)

from .ai_engine import MODEL


OLLAMA_BASE_URL = "http://127.0.0.1:11434"


class AISetupWizard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("OwensGeoMind - AI Setup")
        self.resize(480, 350)

        layout = QVBoxLayout(self)

        title = QLabel("OwensGeoMind AI Setup Wizard")
        layout.addWidget(title)

        description = QLabel(
            "Set up your local AI assistant in four steps.\n"
            "FieldProof Lite and GIS tools work without Ollama."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        self.status = QLabel("AI connection has not been checked.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        check_button = QPushButton("1. Check Ollama")
        check_button.clicked.connect(self.check_ollama)
        layout.addWidget(check_button)

        download_button = QPushButton("2. Download Ollama")
        download_button.clicked.connect(self.download_ollama)
        layout.addWidget(download_button)

        model_button = QPushButton("3. Install AI Model - Instructions")
        model_button.clicked.connect(self.show_model_instructions)
        layout.addWidget(model_button)

        test_button = QPushButton("4. Test AI Connection")
        test_button.clicked.connect(self.test_connection)
        layout.addWidget(test_button)

        close_button = QPushButton("Close / Continue Without AI")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def check_ollama(self):
        try:
            with urlopen(
                OLLAMA_BASE_URL + "/api/tags",
                timeout=3
            ) as response:
                data = json.load(response)

            models = [
                item.get("name", "")
                for item in data.get("models", [])
            ]

            installed = any(
                name == MODEL or name == MODEL + ":latest"
                for name in models
            )

            if installed:
                self.status.setText(
                    "Ollama is running.\n"
                    "AI model found: " + MODEL
                )
                QMessageBox.information(
                    self,
                    "OwensGeoMind",
                    "Ollama and the required AI model are available."
                )
            else:
                self.status.setText(
                    "Ollama is running, but the required model "
                    + MODEL + " is missing."
                )

        except (URLError, HTTPError, TimeoutError, ValueError) as error:
            self.status.setText(
                "Cannot connect to Ollama.\n" + str(error)
            )

    def download_ollama(self):
        webbrowser.open("https://ollama.com/download")

    def show_model_instructions(self):
        system = platform.system()
        command = "ollama pull " + MODEL

        QMessageBox.information(
            self,
            "Install AI Model",
            "Operating system: " + system + "\n\n"
            "Install and start Ollama first.\n\n"
            "Open Terminal (Mac/Linux) or PowerShell (Windows).\n"
            "Run:\n\n"
            + command
            + "\n\nWait until the download finishes."
        )

    def test_connection(self):
        self.check_ollama()
