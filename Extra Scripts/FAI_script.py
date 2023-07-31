# Log in to Google Earth Engine
import ee
ee.Authenticate()
ee.Initialize()

import requests

def get_image_collection(geometry, cloudy_percentage, start_date, end_date):
    # Get the filtered and cropped Sentinel-2 image collection
    return (ee.ImageCollection('COPERNICUS/S2_SR')
            .filterDate(start_date, end_date)
            .filterBounds(geometry)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloudy_percentage))
            .map(lambda image: image.clip(geometry)))

def get_low_tide_extremes(date, lat, lon, key):
    # Get low tide extremes for specific date and coordinates
    url = f'https://www.worldtides.info/api/v3?extremes&date={date}&lat={lat}&lon={lon}&days={1}&key={key}'
    response = requests.get(url)
    data = response.json()
    low_tide_extremes = [extreme for extreme in data['extremes'] if extreme['type'] == 'Low']
    return low_tide_extremes

def is_time_within_range(time, start_hour, end_hour):
    # Check if the given time is within the specified hour range
    hour = int(time[11:13])
    return start_hour <= hour <= end_hour

def export(img, img_date, geometry, folder_name, epsg, fai_low, fai_high):
    # Calculate FAI
    R_NIR = img.select('B8')  # Near Infrared (NIR) - Band 8
    R_RedEdge = img.select('B5')  # Red Edge - Band 5
    R_SWIR = img.select('B11')  # Short Wave Infrared (SWIR) - Band 11

    lambda_NIR = 0.842  # Central wavelength for NIR band (in micrometers)
    lambda_RedEdge = 0.705  # Central wavelength for RedEdge band (in micrometers)
    lambda_SWIR = 1.610  # Central wavelength for SWIR band (in micrometers)

    FAI = R_NIR.subtract(R_RedEdge.add(R_SWIR.subtract(R_RedEdge).multiply(lambda_NIR - lambda_RedEdge).divide(lambda_SWIR - lambda_RedEdge)))

    # Apply a mask to remove FAI values below a certain threshold
    maskedFAI = FAI.updateMask(FAI.gt(fai_low))
    maskedFAI = FAI.updateMask(FAI.lt(fai_high))

    # Define the output file name
    nameFAI = (f"fai_{img_date}").replace('-', '')

    # Export image to Google Drive
    task = ee.batch.Export.image.toDrive(
        image=maskedFAI,
        description=nameFAI,
        scale=10,
        fileNamePrefix=nameFAI,
        folder=folder_name,
        maxPixels=1e13,
        crs=f"EPSG:{epsg}",
        region=geometry.first().geometry().getInfo()['coordinates']
    )
    task.start()

def main():
    # Those parameters must be fulfilled
    lat = 53.11
    lon = -5.86
    keyAPIWorldTides = '62746739-810a-4bc6-8351-1414dc164a1d'
    start_hour = 10
    end_hour = 14
    start_date = '2021-07-15'
    end_date = '2021-07-25'
    cloudy_percentage = 30
    folder_name = "Dollymount_Strand_withoutGUI"
    tiles = ["T29UPV","T29UQV"]
    shapefile = "projects/ee-saraharo/assets/DollymountStrand_32629"
    epsg = "32629"
    fai_low = 0
    fai_high = 3

    geometry = ee.FeatureCollection(shapefile)
    imgs = get_image_collection(geometry, cloudy_percentage, start_date, end_date)
    img_count = imgs.size().getInfo()
    imgs_list = imgs.toList(img_count)
    
    low_tide_dates = []

    for i in range(img_count):
        img = ee.Image(imgs_list.get(i))
        img_id = img.id().getInfo()

        if any(tile in img_id for tile in tiles):
            img_date = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd').getInfo()
            low_tide_extremes = get_low_tide_extremes(img_date, lat, lon, keyAPIWorldTides)

            if low_tide_extremes:
                for extreme in low_tide_extremes:
                    if is_time_within_range(extreme['date'], start_hour, end_hour):
                        hour = extreme['date'][11:16]
                        print()
                        print(f"For image '{img_id}', the first low tide between {start_hour:02d}:00 and {end_hour:02d}:00 is on the day {img_date} at {hour}")
                        low_tide_dates.append(img_date)
                        print()
                        
                        for tile in tiles:
                            if tile in img_id:
                                export(img, img_date, geometry, folder_name, epsg, fai_low, fai_high)
                                break
            
            else:
                return

    if not low_tide_dates:
        print("No images were found that meet the conditions.")
    else:
        print("Dates with low tides found: " + ", ".join(low_tide_dates))
        
main()
