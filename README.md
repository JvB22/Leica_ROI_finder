# Leica_ROI_finder
Automatic ROI finder for Leica Stellaris 8
- Automatic segmentation using cellpose 3
- ROI filtering using intensity, size and circularity
- Exports ROIs to Leica .rgn files, can be imported into LAS X navigator

![](./assets/images/leica_roi_finder.png)

# Workflow
Load LIF image into ROI finder:

<img src="./assets/images/image_loaded.png" width="65%" height="50%">

Perform segmentation using cellpose, filter ROIs using intensity, size and circularity:

<img src="./assets/images/segmentation.png" width="65%" height="50%">

Export ROIs to Leica .rgn format and import into LAS X Navigator:

<img src="./assets/images/regions_loaded.png" width="65%" height="50%">

Perform imaging on all regions:

<img src="./assets/images/experiment.png" width="65%" height="50%">