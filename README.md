# NDVI S2 Intertidal Habitat Mapping (with GUI)

## Description
The NDVI-S2 Intertidal Habitat Mapping software presented here is a user-friendly tool that automates the processing of Level-2 Sentinel-2 imagery to generate intertidal habitat maps. The program uses Google Earth Engine API and the WorldTides API to select images acquired during low tide within a specified time window. The selected images are then processed to calculate Normalized Difference Vegetation Index (NDVI), which is filtered based on intertidal photosynthetic community and study area. Maps are exported to a Google Drive folder in .tiff format. The program is designed to provide a simple solution for coastal zone managers and researchers to map intertidal habitats using free and publicly available satellite imagery. The graphical user interface facilitates the input of parameters and displays the progress and console output.

## Requeriments
- Google Earth Engine activated account
- [Google Cloud installation](https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe?hl=es-419)
- A GIS Software to map intertidal habitat NDVI
- [World Tides API key](https://www.worldtides.info/home)

## Flow Diagram

![Flow Diagram](https://github.com/sharpae/NDVI_S2_IntertidalMapping_GUI/blob/main/screenshots/Fig2.png?raw=true)

## Video Demo

[![NDVI Demo video](https://img.youtube.com/vi/XXXXXXXXXXX/0.jpg)](https://www.youtube.com/watch?v=XXXXXXXXXXXXX "NDVI Demo video")

## Screenshots

![Interface](https://github.com/sharpae/NDVI_S2_IntertidalMapping_GUI/blob/main/screenshots/Fig1.png?raw=true)

![Results](https://github.com/sharpae/NDVI_S2_IntertidalMapping_GUI/blob/main/screenshots/Fig3.png?raw=true)
