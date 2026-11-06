from qgis.PyQt.QtCore import Qt, QObject, QThread, pyqtSignal, pyqtSlot
from qgis.PyQt.QtGui import QIcon
import os
from qgis.PyQt.QtWidgets import (
    QAction, QDockWidget, QWidget, QVBoxLayout,
    QLabel, QTextEdit, QLineEdit, QPushButton,
    QMessageBox, QInputDialog
)
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsProcessingFeedback
)
from qgis import processing



from .ai_engine import ask_ai
from .clip_tool import create_clip
from .verified_workflows import get_workflow, format_workflow
from .chat_formatter import format_chat_message

from .fieldproof.scanner import scan_layer
from .fieldproof.report import export_issues_csv

from .ai_setup_wizard import AISetupWizard


class AIWorker(QObject):
    finished = pyqtSignal(str)

    def __init__(self, question, context):
        super().__init__()
        self.question = question
        self.context = context

    @pyqtSlot()
    def run(self):
        try:
            response = ask_ai(
                self.question,
                learning_level="Beginner",
                project_context=self.context
            )
        except Exception as error:
            response = "AI request failed: " + str(error)

        self.finished.emit(response)


class QGISAIPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dock = None
        self.ai_thread = None
        self.ai_worker = None

    def initGui(self):
        icon_path = os.path.join(
            os.path.dirname(__file__),
            "icon.png"
        )
        self.action = QAction(
            QIcon(icon_path),
            "OwensGeoMind",
            self.iface.mainWindow()
        )
        self.action.triggered.connect(self.show_panel)
        self.iface.addPluginToMenu("OwensGeoMind", self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        if self.dock:
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
            self.dock = None
        if self.action:
            self.iface.removePluginMenu("OwensGeoMind", self.action)
            self.iface.removeToolBarIcon(self.action)

    def show_panel(self):
        if self.dock:
            self.dock.show()
            self.dock.raise_()
            return

        self.dock = QDockWidget("OwensGeoMind", self.iface.mainWindow())
        self.dock.setObjectName("QGISAIChatDock")

        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("OwensGeoMind | v0.3 - Local AI"))

        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setPlainText(
            "Welcome to OwensGeoMind!\n\n"
            "Ask about buffers, clipping, CRS, or layers.\n"
            "Powered by local Llama 3.2 through Ollama.\n""AI explanations may contain mistakes; verify GIS workflows."
        )
        layout.addWidget(self.chat)

        self.question = QLineEdit()
        self.question.setPlaceholderText("Ask a GIS question...")
        self.question.returnPressed.connect(self.answer)
        layout.addWidget(self.question)

        ask_button = QPushButton("Ask Question")
        ask_button.clicked.connect(self.answer)
        layout.addWidget(ask_button)

        inspect_button = QPushButton("Inspect Project Layers")
        inspect_button.clicked.connect(self.inspect_layers)
        layout.addWidget(inspect_button)

        buffer_button = QPushButton("Create Buffer")
        buffer_button.clicked.connect(self.create_buffer)
        layout.addWidget(buffer_button)

        clip_button = QPushButton("Create Clip")
        clip_button.clicked.connect(self.create_clip)
        layout.addWidget(clip_button)

        fieldproof_button = QPushButton("Run FieldProof QA/QC")
        fieldproof_button.clicked.connect(self.run_fieldproof)
        layout.addWidget(fieldproof_button)

        ai_setup_button = QPushButton("AI Setup - Ollama")
        ai_setup_button.clicked.connect(self.open_ai_setup)
        layout.addWidget(ai_setup_button)

        self.dock.setWidget(widget)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

    def open_ai_setup(self):
        """Open the OwensGeoMind AI Setup Wizard."""
        wizard = AISetupWizard(self.iface.mainWindow())
        wizard.exec()


    def run_fieldproof(self):
        """Run read-only QA/QC on the selected GIS layer."""

        layer = self.iface.activeLayer()

        if not isinstance(layer, QgsVectorLayer):
            QMessageBox.warning(
                self.iface.mainWindow(),
                "FieldProof Lite",
                "Please select a vector layer first."
            )
            return

        try:
            issues = scan_layer(layer)
        except Exception as error:
            QMessageBox.critical(
                self.iface.mainWindow(),
                "FieldProof Scan Error",
                str(error)
            )
            return

        self.say(
            f"FieldProof scanned '{layer.name()}' "
            f"and detected {len(issues)} issue(s)."
        )

        for issue in issues[:50]:
            self.say(
                f"Feature {issue['feature_id']}: "
                f"{issue['rule']} - {issue['message']}"
            )

        if len(issues) > 50:
            self.say(
                f"{len(issues) - 50} more issues "
                "are available in the report."
            )

        if not issues:
            return

        choice = QMessageBox.question(
            self.iface.mainWindow(),
            "FieldProof Lite",
            "Would you like to export the QA/QC report?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if choice != QMessageBox.Yes:
            return

        from qgis.PyQt.QtWidgets import QFileDialog

        output_path, _ = QFileDialog.getSaveFileName(
            self.iface.mainWindow(),
            "Save FieldProof QA/QC Report",
            "",
            "CSV Files (*.csv)"
        )

        if not output_path:
            return

        if not output_path.lower().endswith(".csv"):
            output_path += ".csv"

        try:
            saved_path = export_issues_csv(
                issues, output_path
            )
            self.say(
                f"FieldProof report saved: {saved_path}"
            )
        except Exception as error:
            QMessageBox.critical(
                self.iface.mainWindow(),
                "FieldProof Export Error",
                str(error)
            )


    def say(self, message):
        self.chat.append(format_chat_message(str(message)))

    def answer(self):
        question = self.question.text().strip()

        if not question:
            return

        if self.ai_thread is not None:
            self.say("OwensGeoMind is still processing your last question.")
            return

        self.say("YOU: " + question)

        words = set(
            question.lower()
            .replace("?", " ")
            .replace(",", " ")
            .replace(".", " ")
            .split()
        )

        buffer_terms = {"buffer", "buffering", "buffers", "buffered"}
        instruction_terms_for_buffer = {
            "how", "steps", "use", "using", "perform",
            "run", "explain", "workflow", "create", "make"
        }

        if words & buffer_terms and words & instruction_terms_for_buffer:
            workflow = get_workflow("Buffer")
            if workflow:
                self.question.clear()
                self.say(format_workflow(workflow))
                return

        clip_terms = {"clip", "clipping", "clipped"}
        instruction_terms = {
            "how", "steps", "use", "using", "perform",
            "run", "explain", "workflow"
        }

        if words & clip_terms and words & instruction_terms:
            workflow = get_workflow("Clip")
            if workflow:
                self.question.clear()
                self.say(format_workflow(workflow))
                self.say(
                    "Documentation: QGIS 3.40 User Guide. "
                    "Algorithm native:clip was tested in QGIS 3.40.5."
                )
                return
        self.question.clear()
        self.say("OwensGeoMind: Thinking locally...")

        # Collect project details on the QGIS main thread.
        project = QgsProject.instance()
        context_lines = [
            "Project CRS: " + project.crs().authid()
        ]

        for layer in list(project.mapLayers().values())[:20]:
            context_lines.append(
                "Layer: " + layer.name()
                + " | CRS: " + layer.crs().authid()
                + " | Type: " + str(layer.type())
            )

        context = "\\n".join(context_lines)

        self.ai_thread = QThread()
        self.ai_worker = AIWorker(question, context)
        self.ai_worker.moveToThread(self.ai_thread)

        self.ai_thread.started.connect(self.ai_worker.run)
        self.ai_worker.finished.connect(self.on_ai_finished)
        self.ai_worker.finished.connect(self.ai_thread.quit)
        self.ai_worker.finished.connect(self.ai_worker.deleteLater)
        self.ai_thread.finished.connect(self.on_ai_thread_finished)
        self.ai_thread.finished.connect(self.ai_thread.deleteLater)

        self.ai_thread.start()

    def on_ai_finished(self, response):
        if self.dock is not None:
            self.say("OWENSGEOMIND: " + response)

    def on_ai_thread_finished(self):
        self.ai_thread = None
        self.ai_worker = None

    def inspect_layers(self):
        layers = list(QgsProject.instance().mapLayers().values())

        if not layers:
            self.say("No layers are loaded.")
            return

        results = ["PROJECT LAYERS:"]
        for layer in layers:
            results.append(
                f"{layer.name()} | {layer.type().name} | "
                f"CRS: {layer.crs().authid()}"
            )

        self.say("\n".join(results))

    def create_buffer(self):
        layer = self.iface.activeLayer()

        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Select a layer",
                "Select a valid vector layer first."
            )
            return

        if layer.crs().isGeographic():
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Projected CRS required",
                "This starter tool requires a projected CRS "
                "with meter units. Reproject the layer first."
            )
            return

        if layer.crs().mapUnits() != 0:
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Meter units required",
                "Use a projected CRS with meter units."
            )
            return

        distance, ok = QInputDialog.getDouble(
            self.iface.mainWindow(),
            "Buffer Distance",
            "Distance in meters:",
            100.0, 0.01, 1000000.0, 2
        )
        if not ok:
            return

        confirm = QMessageBox.question(
            self.iface.mainWindow(),
            "Confirm Buffer",
            f"Create a {distance} meter buffer around "
            f"features in '{layer.name()}'?\n"
            "The output will be a temporary layer."
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            result = processing.run(
                "native:buffer",
                {
                    "INPUT": layer,
                    "DISTANCE": distance,
                    "SEGMENTS": 12,
                    "END_CAP_STYLE": 0,
                    "JOIN_STYLE": 0,
                    "MITER_LIMIT": 2,
                    "DISSOLVE": False,
                    "OUTPUT": "memory:"
                },
                feedback=QgsProcessingFeedback()
            )

            output = result["OUTPUT"]
            output.setName(f"{layer.name()} Buffer {distance}m")
            QgsProject.instance().addMapLayer(output)

            self.say(
                f"SUCCESS: Created a {distance}m buffer.\n"
                "The result is temporary. Save it to keep it."
            )

        except Exception as error:
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Processing Error",
                str(error)
            )

    def create_clip(self):
        create_clip(self.iface, self.say)
