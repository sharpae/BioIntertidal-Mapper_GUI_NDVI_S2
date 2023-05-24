# BioIntertidal Mapper (with GUI)

## Description
BioIntertidal Mapper is a user-friendly tool, with a graphical user interface, that automates the selection and processing of Sentinel-2 imagery, to generate intertidal habitat maps. The software uses Google Earth Engine API and the WorldTides API to select imagery acquired at low tide within a specified timeframe. These images are subsequently processed to calculate a Normalized Difference Vegetation Index (NDVI), which is masked, based on a shapefile defining the area of interest. Maps are exported to a Google Drive folder. The program offers a simple solution for scientific and environmental manager to map intertidal photosynthetic communities, i.e. microphytobenthos, seaweeds, seagrasses, habitats using free and publicly available satellite imagery. 

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

Sample results:

![Results](https://github.com/sharpae/NDVI_S2_IntertidalMapping_GUI/blob/main/screenshots/Fig3.png?raw=true)
