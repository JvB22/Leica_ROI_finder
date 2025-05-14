# Leica_ROI_finder
Automatic ROI finder for Leica Stellaris 8
- Automatic segmentation using cellpose 3
- ROI filtering using intensity, size and circularity
- Exports ROIs to Leica .rgn files, can be imported into LAS X navigator

![](./assets/images/leica_roi_finder.png)

# Workflow
Load LIF image into ROI finder:

![](./assets/images/image_loaded.png)

Perform segmentation using cellpose, filter ROIs using intensity, size and circularity:

![](./assets/images/segmentation.png)

Export ROIs to Leica .rgn format and import into LAS X Navigator:

![](./assets/images/regions_loaded.png)

Perform imaging on all regions:

![](./assets/images/experiment.png)