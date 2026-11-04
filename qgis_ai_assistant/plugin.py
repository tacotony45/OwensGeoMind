from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QAction, QDockWidget, QWidget, QVBoxLayout,
    QLabel, QTextEdit, QLineEdit, QPushButton,
    QMessageBox, QInputDialog
)
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsProcessingFeedback
)
from qgis import processing


class QGISAIPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dock = None

    def initGui(self):
        self.action = QAction("OwensGeoMind", self.iface.mainWindow())
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

        layout.addWidget(QLabel("OwensGeoMind | v0.1"))

        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setPlainText(
            "Welcome to OwensGeoMind!\n\n"
            "Ask about buffers, clipping, CRS, or layers.\n"
            "This first version uses built-in guidance, not an AI model."
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

        self.dock.setWidget(widget)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

    def say(self, message):
        self.chat.append("\n" + message)

    def answer(self):
        question = self.question.text().strip()
        if not question:
            return

        self.say("YOU: " + question)
        self.question.clear()

        q = question.lower()

        if "buffer" in q:
            response = (
                "A buffer creates an area around geographic features.\n"
                "Example: 500 meters around a road.\n"
                "Use the Create Buffer button to run this operation.\n"
                "For accurate distances, use a suitable projected CRS."
            )
        elif "clip" in q:
            response = (
                "Clip extracts features within a polygon boundary.\n"
                "Open Processing Toolbox and search for Clip.\n"
                "Choose an input layer and polygon overlay layer."
            )
        elif "crs" in q or "projection" in q:
            response = (
                "A Coordinate Reference System defines how spatial "
                "coordinates relate to locations on Earth.\n"
                "Check layer properties under Source to view its CRS."
            )
        elif "layer" in q:
            response = (
                "Layers contain spatial data such as points, lines, "
                "polygons, or rasters.\n"
                "Use Inspect Project Layers to examine your project."
            )
        else:
            response = (
                "I don't have a verified answer yet.\n"
                "The upcoming AI version will search official QGIS "
                "documentation and explain more complex workflows."
            )

        self.say("ASSISTANT: " + response)

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
