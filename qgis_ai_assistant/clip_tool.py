from pathlib import Path

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox,
    QPushButton, QFileDialog, QLineEdit,
    QHBoxLayout, QDialogButtonBox, QMessageBox
)
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsWkbTypes,
    QgsProcessingFeedback
)
from qgis import processing


class ClipDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OwensGeoMind - Create Clip")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        layers = [
            layer
            for layer in QgsProject.instance().mapLayers().values()
            if isinstance(layer, QgsVectorLayer)
            and layer.isValid()
            and layer.isSpatial()
        ]

        self.input_combo = QComboBox()
        self.overlay_combo = QComboBox()

        layout.addWidget(QLabel("Input vector layer:"))
        for layer in layers:
            self.input_combo.addItem(layer.name(), layer.id())
        layout.addWidget(self.input_combo)

        layout.addWidget(QLabel("Polygon boundary layer:"))
        for layer in layers:
            if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                self.overlay_combo.addItem(layer.name(), layer.id())
        layout.addWidget(self.overlay_combo)

        layout.addWidget(QLabel("Output GeoPackage (.gpkg):"))

        output_row = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)
        browse = QPushButton("Browse...")
        browse.clicked.connect(self.browse_output)
        output_row.addWidget(self.output_edit)
        output_row.addWidget(browse)
        layout.addLayout(output_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Ok).setText("Review Clip")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def browse_output(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Choose a NEW GeoPackage",
            "",
            "GeoPackage (*.gpkg)"
        )
        if filename:
            if not filename.lower().endswith(".gpkg"):
                filename += ".gpkg"
            self.output_edit.setText(filename)


def create_clip(iface, report):
    dialog = ClipDialog(iface.mainWindow())

    if dialog.exec_() != QDialog.Accepted:
        return

    project = QgsProject.instance()

    input_layer = project.mapLayer(
        dialog.input_combo.currentData()
    )
    overlay_layer = project.mapLayer(
        dialog.overlay_combo.currentData()
    )

    if (
        not isinstance(input_layer, QgsVectorLayer)
        or not input_layer.isValid()
        or not input_layer.isSpatial()
        or not isinstance(overlay_layer, QgsVectorLayer)
        or not overlay_layer.isValid()
        or overlay_layer.geometryType() != QgsWkbTypes.PolygonGeometry
    ):
        QMessageBox.warning(
            iface.mainWindow(),
            "Missing layers",
            "Select an input layer and a polygon boundary."
        )
        return

    if input_layer.id() == overlay_layer.id():
        QMessageBox.warning(
            iface.mainWindow(),
            "Invalid selection",
            "Choose two different layers."
        )
        return

    if not input_layer.crs().isValid() or not overlay_layer.crs().isValid():
        QMessageBox.warning(
            iface.mainWindow(),
            "Invalid CRS",
            "Both layers must have valid coordinate systems."
        )
        return

    output_text = dialog.output_edit.text().strip()

    if not output_text:
        QMessageBox.warning(
            iface.mainWindow(),
            "Missing output",
            "Choose a new GeoPackage destination."
        )
        return

    output_path = Path(output_text).expanduser()

    if output_path.suffix.lower() != ".gpkg":
        QMessageBox.warning(
            iface.mainWindow(),
            "Invalid output",
            "Output must end in .gpkg."
        )
        return

    if output_path.exists():
        QMessageBox.warning(
            iface.mainWindow(),
            "Overwrite blocked",
            "This GeoPackage already exists. Choose a new filename."
        )
        return

    if not output_path.parent.is_dir():
        QMessageBox.warning(
            iface.mainWindow(),
            "Invalid destination",
            "The output folder does not exist."
        )
        return

    confirm = QMessageBox.question(
        iface.mainWindow(),
        "Confirm Clip",
        "Input: " + input_layer.name() + "\n"
        "Boundary: " + overlay_layer.name() + "\n"
        "Output: " + str(output_path) + "\n\n"
        "Run Clip and create this new GeoPackage?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )

    if confirm != QMessageBox.Yes:
        return

    # Check again immediately before processing.
    if output_path.exists():
        QMessageBox.warning(
            iface.mainWindow(),
            "Output already exists",
            "The destination was created before processing started."
        )
        return

    try:
        result = processing.run(
            "native:clip",
            {
                "INPUT": input_layer,
                "OVERLAY": overlay_layer,
                "OUTPUT": str(output_path)
            },
            feedback=QgsProcessingFeedback()
        )

        saved_path = result["OUTPUT"]
        output_layer = QgsVectorLayer(
            saved_path,
            output_path.stem,
            "ogr"
        )

        if not output_layer.isValid():
            raise RuntimeError(
                "Processing finished but the saved layer could not be loaded."
            )

        project.addMapLayer(output_layer)
        report(
            "SUCCESS: Clip completed.\n"
            "Output: " + str(output_path) + "\n"
            "Features: " + str(output_layer.featureCount())
        )

    except Exception as error:
        QMessageBox.warning(
            iface.mainWindow(),
            "Clip Processing Error",
            str(error)
        )
