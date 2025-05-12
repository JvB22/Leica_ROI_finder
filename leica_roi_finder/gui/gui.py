# Default imports
import sys
import traceback
from pathlib import Path

# External imports
import numpy as np

# Package imports
from leica_roi_finder.core.roi_finder_class import ROI_finder
from leica_roi_finder.core._defaults import(
    DEFAULT_CELLPROB_THRESHOLD,
    DEFAULT_DIAMETER,
    DEFAULT_FLOW_THRESHOLD,
    DEFAULT_MIN_INTENSITY,
    DEFAULT_MAX_INTENSITY,
    DEFAULT_MIN_SIZE,
    DEFAULT_MAX_SIZE,
    DEFAULT_MIN_CIRCULARITY,
    DEFAULT_MAX_CIRCULARITY
)
import leica_roi_finder

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QPushButton, QLabel, QLineEdit, QGroupBox,
    QFileDialog, QGridLayout, QMessageBox,
    QHBoxLayout, QVBoxLayout, QLabel,
    QSlider, QPushButton, QGroupBox
    )

from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtGui import QAction, QPalette, QColor

# Other QT imports
import pyqtgraph as pg
from pyqtgraph.widgets.HistogramLUTWidget import HistogramLUTWidget
from superqt import QRangeSlider

class main_window(QMainWindow):
    """
    Main window for Leica ROI selector
    """
    def __init__(self):
        super().__init__()

        self.img = np.zeros((600, 600))
        self.roi_mask = np.zeros((600, 600))

        self.window_title = f"Leica ROI finder - Version: {leica_roi_finder.__version__}"
        self.setWindowTitle(self.window_title)

        # Variables
        self.bit_depth = 16
        self.loaded_image = False

        self.init_ui()

    def init_ui(self):
        """
        Initialize main UI components (menubar, sidebar, image display)
        """
        # Create menu bar
        self.create_menubar()

        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)
        
        # Create sidebar widget
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # Create image display widget
        self.image_widget = self.create_image_display()
        main_layout.addWidget(self.image_widget, 1)
        
        # Initialize
        self.update_display()

    def create_menubar(self):
        """
        Initialize menubar
        """
        # Create menu bar
        menubar = self.menuBar()
        
        # Create file menu
        file_menu = menubar.addMenu("File")
        
        # Create open action
        open_action = QAction("Open file", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_image)
        file_menu.addAction(open_action)
        
        # Create exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def create_sidebar(self):
        """
        Initialize sidebar
        """
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create groups for controls
        image_controls = QGroupBox("Image Controls")
        image_layout = QVBoxLayout(image_controls)

        # Image controls
        image_label = QLabel("Min/Max:")
        self.image_slider = QRangeSlider(Qt.Orientation.Horizontal)
        self.image_slider.setMinimum(int(np.min(self.img)))
        self.image_slider.setMaximum(int(np.max(self.img)))
        self.image_slider.setValue((int(np.min(self.img)), int(np.max(self.img))))
        self.image_slider.valueChanged.connect(self.update_levels)
        image_layout.addWidget(image_label)
        image_layout.addWidget(self.image_slider)

        opacity_label = QLabel("Mask Opacity:")
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(50)
        self.opacity_slider.valueChanged.connect(self.update_mask_opacity)
        image_layout.addWidget(opacity_label)
        image_layout.addWidget(self.opacity_slider)

        # Cellpose settings group
        cellpose_controls = QGroupBox("Cellpose settings:")
        cellpose_layout = QGridLayout(cellpose_controls)

        # Diameter input
        diameter_label = QLabel("Diameter:")
        self.diameter_input = QLineEdit()
        self.diameter_input.setText(str(DEFAULT_DIAMETER))
        cellpose_layout.addWidget(diameter_label, 0, 0)
        cellpose_layout.addWidget(self.diameter_input, 0, 1)

        # Flow threshold input
        flow_label = QLabel("Flow threshold:")
        flow_label.setToolTip("Set higher to get more cells, ranges from 0.0 to 3.0")
        self.flow_input = QLineEdit()
        self.flow_input.setText(str(DEFAULT_FLOW_THRESHOLD))
        cellpose_layout.addWidget(flow_label, 1, 0)
        cellpose_layout.addWidget(self.flow_input, 1, 1)

        # Cellprob threshold input
        cellprob_label = QLabel("Cellprob threshold:")
        cellprob_label.setToolTip("Set lower to include more pixels, ranges from -6.0 to 6.0")
        self.cellprob_input = QLineEdit()
        self.cellprob_input.setText(str(DEFAULT_CELLPROB_THRESHOLD))
        cellpose_layout.addWidget(cellprob_label, 2, 0)
        cellpose_layout.addWidget(self.cellprob_input, 2, 1)

        """Intensity settings group"""
        intensity_controls = QGroupBox("Intensity")
        intensity_layout = QGridLayout(intensity_controls)

        # Min intensity input
        min_intensity_label = QLabel("Min intensity:")
        self.min_intensity_input = QLineEdit()
        self.min_intensity_input.setText(str(DEFAULT_MIN_INTENSITY))
        intensity_layout.addWidget(min_intensity_label, 0, 0)
        intensity_layout.addWidget(self.min_intensity_input, 0, 1)

        # Min intensity input
        max_intensity_label = QLabel("Max intensity:")
        self.max_intensity_input = QLineEdit()
        self.max_intensity_input.setText(str(DEFAULT_MAX_INTENSITY))
        intensity_layout.addWidget(max_intensity_label, 1, 0)
        intensity_layout.addWidget(self.max_intensity_input, 1, 1)

        """Size settings group"""
        size_controls = QGroupBox("Size (pixels)")
        size_layout = QGridLayout(size_controls)

        # Min size input
        min_size_label = QLabel("Min size:")
        self.min_size_input = QLineEdit()
        self.min_size_input.setText(str(DEFAULT_MIN_SIZE))
        size_layout.addWidget(min_size_label, 0, 0)
        size_layout.addWidget(self.min_size_input, 0, 1)

        # Max size input
        max_size_label = QLabel("Max size:")
        self.max_size_input = QLineEdit()
        self.max_size_input.setText(str(DEFAULT_MAX_SIZE))
        size_layout.addWidget(max_size_label, 1, 0)
        size_layout.addWidget(self.max_size_input, 1, 1)

        """Circularity settings group"""
        circularity_controls = QGroupBox("Circularity (0-1)")
        circularity_layout = QGridLayout(circularity_controls)

        # Min circularity input
        min_circularity_label = QLabel("Min circularity:")
        self.min_circularity_input = QLineEdit()
        self.min_circularity_input.setText(str(DEFAULT_MIN_CIRCULARITY))
        circularity_layout.addWidget(min_circularity_label, 0, 0)
        circularity_layout.addWidget(self.min_circularity_input, 0, 1)

        # Max circularity input
        max_circularity_label = QLabel("Max circularity:")
        self.max_circularity_input = QLineEdit()
        self.max_circularity_input.setText(str(DEFAULT_MAX_CIRCULARITY))
        circularity_layout.addWidget(max_circularity_label, 1, 0)
        circularity_layout.addWidget(self.max_circularity_input, 1, 1)

        # Detected ROIs label
        self.detected_rois_label = QLabel()
        self.detected_rois_label.setText(f'<b><span style="font-size:15px;">Detected ROIs: 0</span></b>')

        # Button to run the segmentation/roi selection
        run_button = QPushButton("Run ROI finder")
        run_button.clicked.connect(self.run)

        # Export button
        export_button = QPushButton("Export to .rgn")
        export_button.clicked.connect(self.export)
        
        # Add everything to sidebar
        sidebar_layout.addWidget(image_controls)
        sidebar_layout.addWidget(cellpose_controls)
        sidebar_layout.addWidget(intensity_controls)
        sidebar_layout.addWidget(size_controls)
        sidebar_layout.addWidget(circularity_controls)
        sidebar_layout.addWidget(self.detected_rois_label)
        sidebar_layout.addStretch(1)  # Push everything up
        sidebar_layout.addWidget(run_button)
        sidebar_layout.addWidget(export_button)

        # Collect all QLineEdits and bind the "run" command
        qlineedits = [
            self.diameter_input,
            self.flow_input,
            self.cellprob_input,
            self.min_intensity_input,
            self.max_intensity_input,
            self.min_size_input,
            self.max_size_input,
            self.min_circularity_input,
            self.max_circularity_input,
        ]

        for lineedit in qlineedits:
            lineedit.returnPressed.connect(self.run)

        
        return sidebar_widget
    
    def create_image_display(self):
        """
        Initialize image display
        """
        # Create a GraphicsLayoutWidget
        graphics_layout = pg.GraphicsLayoutWidget()
        
        # Add a ViewBox
        self.view_box = graphics_layout.addViewBox()
        self.view_box.setAspectLocked(True)
        
        # Create ImageItem for the base image
        self.image_item = pg.ImageItem()
        self.view_box.addItem(self.image_item)
        
        # Create ImageItem for the mask overlay
        self.mask_item = pg.ImageItem()
        self.view_box.addItem(self.mask_item)
        
        # Create and link a HistogramLUTWidget
        self.histogram_widget = HistogramLUTWidget()
        self.histogram_widget.setImageItem(self.image_item)
        self.histogram_widget.gradient.loadPreset("grey")

        self.histogram_widget.sigLevelChangeFinished.connect(self.update_levels_from_histogram)

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(graphics_layout, 14)
        layout.addWidget(self.histogram_widget, 1)

        return container
    
    def update_levels_from_histogram(self):
        """
        Update image display based on histogram slider
        """
        levels = self.histogram_widget.getLevels()
        if levels:
            self.image_item.setLevels(levels)
            self.image_slider.setValue(tuple(map(int, levels)))  # Sync QRangeSlider

    def update_levels(self, values):
        """
        Update image display based on sidebar Min/Max slider
        """
        min_val, max_val = values
        self.image_item.setLevels([min_val, max_val])
        self.histogram_widget.setLevels(min_val, max_val)  # Sync histogram

    def update_mask_opacity(self, value):
        """
        Update segmentation mask opacity
        """
        opacity = value / 100.0
        self.mask_item.setOpacity(opacity)

    def update_display(self):
        """
        Display mask and image
        """
        self.image_item.setImage(self.img.T)
        self.mask_item.setImage(self.roi_mask.T)
        self.histogram_widget.setImageItem(self.image_item)  # Ensure link
        self.histogram_widget.setLevels(np.min(self.img), np.max(self.img))
    
    def open_image(self):
        """
        Open image file and initialize ROI_finder class
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open LIF file",
            "",
            "Image Files (*.lif)"
        )
        
        if file_path:
            try:
                self.ROI_finder = ROI_finder(filepath=file_path)
                self.img = self.ROI_finder.img
                self.roi_mask = self.ROI_finder.mask
                
                self.bit_depth = int(self.ROI_finder.metadata["BitSize"])

                # Mask colormap
                rng = np.random.default_rng()
                lut = rng.integers(0, 256, size=(2**self.bit_depth, 3), dtype=np.uint8)
                
                alpha = np.full((2**self.bit_depth, 1), 255, dtype=np.uint8)
                alpha[0] = 0  # Make value 0 transparent
                
                rgba_lut = np.hstack((lut, alpha))
                self.mask_item.setLookupTable(rgba_lut)

                self.image_slider.setMinimum(int(np.min(self.img)))
                self.image_slider.setMaximum(int(np.max(self.img)))
                self.image_slider.setValue((int(np.min(self.img)), int(np.max(self.img))))

                self.max_intensity_input.setText(str(2**self.bit_depth))

                self.max_size_input.setText(str(self.img.shape[0]*self.img.shape[1]))

                self.update_display()
                file_path = Path(file_path)
                self.setWindowTitle(f"{self.window_title} - {file_path.name}")
                self.loaded_image = True

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image: {str(e)}")
                traceback.print_exc()

    def run(self):
        """
        Pass parameters to ROI_finder class and run segmentation/criteria
        """
        # Check if ROI finder has been initialized
        if not self.loaded_image:
            return

        try:
            # Collect values and alter ROI finder object
            self.ROI_finder.diameter = int(self.diameter_input.text())
            self.ROI_finder.flow_threshold = float(self.flow_input.text())
            self.ROI_finder.cellprob_threshold = float(self.cellprob_input.text())
            self.ROI_finder.min_intensity = int(self.min_intensity_input.text())
            self.ROI_finder.max_intensity = int(self.max_intensity_input.text())
            self.ROI_finder.min_size = int(self.min_size_input.text())
            self.ROI_finder.max_size = int(self.max_size_input.text())
            self.ROI_finder.min_circularity = float(self.min_circularity_input.text())
            self.ROI_finder.max_circularity = float(self.max_circularity_input.text())
        except Exception as error:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Error")
            msg_box.setText(f"Could not convert all inputs to the correct datatype:\n{error}")
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.show()
            return

        # Run detection
        self.ROI_finder.run()

        # Update image
        self.roi_mask = self.ROI_finder.mask
        self.mask_item.setImage(self.roi_mask.T)
        self.update_mask_opacity(self.opacity_slider.value())
        self.detected_rois_label.setText(f'<b><span style="font-size:15px;">Detected ROIs: {len(np.unique(self.roi_mask))-1}</span></b>')

    def export(self):
        """
        Export selected regions to Leica .rgn format
        """
        # Check if there are coords
        if not self.loaded_image:
            return
        if len(np.unique(self.ROI_finder.mask))-1 < 1:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Error")
            msg_box.setText(f"No regions found")
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.show()
            return

        file_filter = "Region Files (*.rgn)"
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            "custom_roi.rgn",
            file_filter
        )
        if filename:
            try:
                filename = Path(filename)
                self.ROI_finder.export_to_rgn(filename, filename.stem)
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Saved regions")
                msg_box.setText(f"Regions succesfully saved at:\n{filename}")
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.show()
            except Exception as error:
                traceback.print_exc()
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Error")
                msg_box.setText(f"Could not save regions:\n{error}")
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.show()

def roi_finder_gui():
    """
    Initialize ROI_finder gui and set styles
    """

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Set up dark palette
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))

    app.setPalette(dark_palette)

    window = main_window()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    roi_finder_gui()