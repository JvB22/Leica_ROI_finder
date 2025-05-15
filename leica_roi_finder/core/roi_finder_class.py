# Default imports
from copy import deepcopy

# External imports 
import numpy as np
from skimage.measure import regionprops_table
import pandas as pd

# Package imports
from leica_roi_finder.core.LIF_metadata import read_lif_metadata
from leica_roi_finder.core.coords_to_xml import generate_coords_xml
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

class ROI_finder():
    """"
    Automatic ROI finder using cellpose and other parameters

    Attributes
    ----------
    diameter : int
        Cellpose diameter
    flow_threshold : float
        Cellpose flow threshold
    cellprob_threshold : float
        Cellpose cell probability threshold
    min_intensity : int
        Minimal average intensity a cell should have
    max_intensity : int
        Maximum average intensity a cell should have
    min_size : int
        The minimal amount of pixels a cell should have
    max_size : int
        The maximum amount of pixels a cell should have
    min_circularity : float
        The minimal circularity a cell should have, circularity ranges from 0 to 1 (perfect circle)
    max_circularity : float
        The maximum circularity a cell should have, circularity ranges from 0 to 1 (perfect circle)
    segmented_mask : ndarray
        Original mask segmented by cellpose
    mask : ndarray
        Mask segmented by cellpose, but removed cells that did not fullfil other criteria (e.g. min/max intensity)
    img : ndarray
        Image extracted from .lif file
    metadata : dict
        Relevant metadata extracted from .lif file
    coords : ndarray
        Numpy array containing coordinates of ROIs, array is of shape (len, 2)

    Notes
    -----
    Not all attributes will be available/calculated until the class is properly initialized using the "run()" method
    Parameters such as diameter can be set during construction, or altered later.
    Once parameters have changed, you can use the "run()" method to calculate the new ROIs
    """

    def __init__(
            self,
            filepath,
            diameter = DEFAULT_DIAMETER,
            flow_threshold = DEFAULT_FLOW_THRESHOLD,
            cellprob_threshold = DEFAULT_CELLPROB_THRESHOLD,
            min_intensity = DEFAULT_MIN_INTENSITY,
            max_intensity = DEFAULT_MAX_INTENSITY,
            min_size = DEFAULT_MIN_SIZE,
            max_size = DEFAULT_MAX_SIZE,
            min_circularity = DEFAULT_MIN_CIRCULARITY,
            max_circularity = DEFAULT_MAX_CIRCULARITY
        ):
        """"
        Parameters
        ----------
        filepath : str
            File path for *.lif file
        diameter : int
            Cellpose diameter
        flow_threshold : float
            Cellpose flow threshold
        cellprob_threshold : float
            Cellpose cell probability threshold
        min_intensity : int
            Minimal average intensity a cell should have
        max_intensity : int
            Maximum average intensity a cell should have
        min_size : int
            The minimal amount of pixels a cell should have
        max_size : int
            The maximum amount of pixels a cell should have
        min_circularity : float
            The minimal circularity a cell should have, circularity ranges from 0 to 1 (perfect circle)
        max_circularity : float
            The maximum circularity a cell should have, circularity ranges from 0 to 1 (perfect circle)
        """

        self._filepath = filepath

        # Share parameters across class
        self.diameter = diameter
        self.flow_threshold = flow_threshold
        self.cellprob_threshold = cellprob_threshold
        self.min_intensity = min_intensity
        self.max_intensity = max_intensity
        self.min_size = min_size
        self.max_size = max_size
        self.min_circularity = min_circularity
        self.max_circularity = max_circularity

        # Store parameters of previous run
        self._previous_diameter = None
        self._previous_flow_threshold = None
        self._previous_cellprob_threshold = None
        self._previous_min_intensity = None
        self._previous_max_intensity = None
        self._previous_min_size = None
        self._previous_max_size = None
        self._previous_min_circularity = None
        self._previous_max_circularity = None

        # Read lif
        self._read_lif()

        # Variables
        self.model=None
        self.segmented_mask = np.zeros_like(self.img)
        self.mask = np.zeros_like(self.img)
        self.coords = []
        self.properties = None

    def run(self):
        """
        Run cellpose segmentation and other criteria

        Notes
        -----
        If parameters for cellpose segmentation have not changed, the segmentation will not be run again to save time.
        """

        run_select_roi=False

        # Check if cellpose parameters have changed - if they have run segmentation again
        if (
            self._previous_diameter != self.diameter or
            self._previous_flow_threshold != self.flow_threshold or
            self._previous_cellprob_threshold != self.cellprob_threshold
        ):
            # Run cellpose
            self._cellpose()
            # Also recalculate properties now
            self._calculate_properties()
            run_select_roi=True # Now also rerun ROI selection

        # Sort cells base on other criteria
        # If nothing has changed, do not run ROI selection
        if (
            self._previous_min_intensity != self.min_intensity or
            self._previous_max_intensity != self.max_intensity or
            self._previous_min_size != self.min_size or
            self._previous_max_size != self.max_size or
            self._previous_min_circularity != self.min_circularity or
            self._previous_max_circularity != self.max_circularity
        ) or (
            run_select_roi
        ):
            self._select_roi()

        # Store parameters
        self._previous_diameter = deepcopy(self.diameter)
        self._previous_flow_threshold = deepcopy(self.flow_threshold)
        self._previous_cellprob_threshold = deepcopy(self.cellprob_threshold)
        self._previous_min_intensity = deepcopy(self.min_intensity)
        self._previous_max_intensity = deepcopy(self.max_intensity)
        self._previous_min_size = deepcopy(self.min_size)
        self._previous_max_size = deepcopy(self.max_size)
        self._previous_min_size = deepcopy(self.min_circularity)
        self._previous_max_size = deepcopy(self.max_circularity)

    def _read_lif(self):
        """
        Read lif metadata and assign values to attributes
        """

        # Read metadata
        metadata = read_lif_metadata(self._filepath)

        if metadata["MicroscopeModel"] != "DMI8-CS":
            raise UserWarning(f"This script was created for the Leica Stellaris 8 microscope, and has only been tested using the Leica Stellaris 8. Using this script on other machines might lead to unexpected outputs due to metadata differences")

        self.dtype =  getattr(np, f'uint{metadata["BitSize"]}')

        # Load memmap
        lif_img = np.memmap(
            self._filepath,
            offset=metadata["Offset"],
            mode='r',
            shape=(metadata["YDim"], metadata["XDim"]),
            dtype=self.dtype
        )

        # Flip image if necessary
        self.flipy = metadata["FlipY"]
        if self.flipy:
            lif_img = np.flipud(lif_img)
        self.flipx = metadata["FlipX"]
        if self.flipx:
            lif_img = np.fliplr(lif_img)

        self.img = lif_img
        self.metadata = metadata
        self._posy = metadata["PosY"]
        self._posx = metadata["PosX"]

    def _cellpose(self):
        """
        Perform segmentation using cellpose
        """

        # Load model if not done yet
        if self.model == None:
            # Lazy imports
            print("Loading cellpose...")
            from cellpose import models
            from torch.cuda import is_available
            if is_available():
                gpu=True
                print("Using GPU...")
            else:
                gpu=False
                print("Using CPU...")
            print("Loading model...")
            self.model = models.Cellpose(gpu=gpu, model_type='cyto3')

        # Run model
        self.mask, flow, styles, diams = self.model.eval(self.img, diameter=self.diameter, flow_threshold=self.flow_threshold, cellprob_threshold=self.cellprob_threshold)
        self.segmented_mask = deepcopy(self.mask)

    def _calculate_properties(self):
        # Calculate builtin regionprops properties
        props = regionprops_table(
            self.segmented_mask, 
            intensity_image=self.img,
            properties=['label', 'area', 'perimeter', 'mean_intensity']
        )
        self.properties = pd.DataFrame(props)

        # Calculate circularity
        self.properties['circularity'] = 4 * np.pi * self.properties['area'] / (self.properties['perimeter'] ** 2)
        self.properties['circularity'] = self.properties['circularity'].fillna(0)

    def _select_roi(self):
        """
        Select regions of interest based on intensity, size and roundness
        """
        self.mask = self.segmented_mask.copy()

        # Filter using conditions
        keep = self.properties[
            (self.properties['mean_intensity'] >= self.min_intensity) &
            (self.properties['mean_intensity'] <= self.max_intensity) &
            (self.properties['area'] >= self.min_size) &
            (self.properties['area'] <= self.max_size) &
            (self.properties['circularity'] >= self.min_circularity) &
            (self.properties['circularity'] <= self.max_circularity)
        ]['label'].values

        # Remove masks
        self.mask[~np.isin(self.segmented_mask, keep)] = 0

    def _find_center(self):
        """
        Find centers of selected ROIs
        """
        temp_mask = self.mask.copy()
        if self.flipy:
            temp_mask = np.flipud(temp_mask)
        if self.flipx:
            temp_mask = np.fliplr(temp_mask)

        labels, counts = np.unique(temp_mask, return_counts=True)
        if labels[0] == 0:
            labels = labels[1:]
            counts = counts[1:]
        
        centers = []
        y_coords, x_coords = np.indices(temp_mask.shape)
        
        for label in labels:
            mask = (temp_mask == label)
            center_y = np.mean(y_coords[mask])
            center_x = np.mean(x_coords[mask])
            centers.append([int(center_x), int(center_y)])
        
        return np.array(centers)
    
    def export_to_rgn(self, outputpath, groupname=None):
        """
        Convert ROIs to Leica coordinates and save to .rgn file

        Parameters
        ----------
        outputpath : str
            Filepath where to save the region file. Should have suffix ".rgn"
        groupname : str, optional
            Group name inside the xml
        """
        xres = self.metadata["XRes"]  # Meters
        yres = self.metadata["YRes"]  # Meters
        
        # Find center of ROIs
        self.coords = self._find_center()

        # Calculate stage coordinates relative to 0, 0 in image
        leica_coords = []
        for pos in self.coords:
            leica_xcoord = pos[0]*xres
            leica_ycoord = pos[1]*yres
            leica_coords.append([leica_xcoord, leica_ycoord])
        leica_coords = np.array(leica_coords)

        # Recalculate coordinates relative to middle of image
        self._posx = self._posx - (self.img.shape[1]/2)*xres
        self._posy = self._posy - (self.img.shape[0]/2)*yres
        
        # Retreive absolute stage position and add to coordinates
        leica_coords[:, 0] += self._posx
        leica_coords[:, 1] += self._posy

        xml = generate_coords_xml(leica_coords, group_name=groupname)

        with open(outputpath, 'w') as f:
            f.write(xml)