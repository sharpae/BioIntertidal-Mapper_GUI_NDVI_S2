# Load the raster library
library(raster)

# Define the path to the folder where the files are located
# Make sure to include a trailing slash (/) to correctly build the file paths later
folder <- "C:/Users/Sara Haro/Downloads/BioIntertidalMapper/"

# Define the dates of the files to be processed
dates <- c("20220109")  # You can add more dates here

# For each date...
for (date in dates) {
  # Define the paths to the files
  # 'paste0()' is used to concatenate the folder path, filename and date
  # The correct file paths are constructed here because of the trailing slash (/) in the folder path
  file1 <- paste0(folder, "ndvi_", date, "_T16PBC.tif")
  file2 <- paste0(folder, "ndvi_", date, "_T16PCC.tif")
  
  # Load the raster files
  # If the files exist at the given paths, they are loaded as raster objects
  r1 <- raster(file1)
  r2 <- raster(file2)

  
  # Merge the rasters
  # The 'merge()' function is used to combine the two raster objects into one
  merged <- merge(r1, r2)
  
  # Define the path to the output file
  # Again, 'paste0()' is used to build the path for the output file
  output_file <- paste0(folder, "ndvi_", date, "_merged.tif")
  
  # Save the merged raster
  # The 'writeRaster()' function is used to save the merged raster object to the output file
  # If a file with the same name already exists, it will be overwritten due to 'overwrite=TRUE'
  writeRaster(merged, output_file, format='GTiff', overwrite=TRUE)
}
