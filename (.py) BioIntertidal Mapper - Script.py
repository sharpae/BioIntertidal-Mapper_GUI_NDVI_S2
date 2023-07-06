import subprocess
import sys

try:
    import ee
except ImportError:
    print("Installing library earthengine-api...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "earthengine-api"])
    import ee

import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import requests
from tkinter import messagebox
from tkinter import ttk
import threading
import re

# Class definition for writing text to a Tkinter text widget
class OutputText:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, s):
        self.text_widget.config(state="normal")  # Enable text widget for writing
        self.text_widget.insert(tk.END, s)  # Insert text
        self.text_widget.see(tk.END)  # Scroll view to end
        self.text_widget.config(state="disabled")  # Disable text widget for read-only
    
    def flush(self):
        pass

# Function definition for clearing the contents of two Tkinter text widgets
def clear_console_output():
    console_output_text.config(state="normal")
    console_output_text.delete(1.0, tk.END)
    console_output_text.config(state="disabled")
    tide_dates_text.config(state="normal")
    tide_dates_text.delete(1.0, tk.END)
    tide_dates_text.config(state="disabled")
    progress_bar['value'] = 0    

def show_help():
    messagebox.showinfo("Help", "Assuming the Sentinel-2 satellite passes over the study area at 11:00 UTC, and the study area observes a time difference of +1 UTC, the satellite would have acquired the image at 12:00 UTC (+1). To ensure that only images captured during low tide are selected, a 2-hour time window will be applied. Consequently, in the aforementioned example, solely those images will be chosen where low tide took place 2 hours prior or post image acquisition, i.e., between 10:00 and 14:00. The satellite acquisition time is indicated in the image filename.")

# Function definition for authenticating a connection to the Google Earth Engine API
def authenticate():
    ee.Authenticate()
    ee.Initialize()
    login_button.config(state="disabled")
    enable_fields()

# Default values for a list of parameters used in a function
default_values = [
    "53.35293", "-6.16435", "eacc6042-df40-489b-935c-cc60685994ef", "10", "14", "2021-06-01", "2021-08-30", "30", "T29UPV", "0.10", "1", "projects/ee-saraharo/assets/DollymountStrand_32629", "32629", "Dollymount_Strand"
]

# Function definition for enabling and filling in default values for text input fields
def enable_fields():
    for i, entry in enumerate(entry_fields):
        entry.config(state="normal")
        entry.insert(0, default_values[i])  # Insert default value
    run_button.config(state="normal")  # Enable button to execute process function

# Function definition for getting a filtered and clipped Sentinel-2 image collection
def get_image_collection(geometry, cloudy_percentage, start_date, end_date):
    return (ee.ImageCollection('COPERNICUS/S2_SR')
            .filterDate(start_date, end_date)
            .filterBounds(geometry)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloudy_percentage))
            .map(lambda image: image.clip(geometry)))

# Function definition for getting low tide extremes for a specific date and coordinates
def get_low_tide_extremes(date, lat, lon, key):
    keys = [
        "cc44e94c-1ebb-4bd6-a024-4bdc00cd9374",
        "77bcfbff-3479-4d19-ae25-ade4f8cdf66e"
    ]

    url = f'https://www.worldtides.info/api/v3?extremes&date={date}&lat={lat}&lon={lon}&days={1}&key={key}'
    response = requests.get(url)
    data = response.json()

    while 'error' in data and data['error'] == 'Not enough credits' and keys:
        key = keys.pop(0)
        url = f'https://www.worldtides.info/api/v3?extremes&date={date}&lat={lat}&lon={lon}&days={1}&key={key}'
        response = requests.get(url)
        data = response.json()

    if 'error' in data:
        error_message = ""
        if data['error'] == 'Not enough credits':
            error_message = ("All provided API keys for WorldTides have run out of credits. "
                             "Please log in to your WorldTides account and top up your credits "
                             "before trying again or enter a new API key. Thank you.")
        elif data['error'] == 'API key is invalid':
            error_message = ("The API key for WorldTides is invalid. "
                             "Please enter a valid API key and try again. Thank you.")

        if error_message:
            messagebox.showerror("Error", error_message)
            return

    low_tide_extremes = [extreme for extreme in data['extremes'] if extreme['type'] == 'Low']
    return low_tide_extremes

# Function definition for checking whether a given time falls within a certain range of hours
def is_time_within_range(time, start_hour, end_hour):
    hour = int(time[11:13])
    return start_hour <= hour < end_hour

# Function definition for exporting an image to Google Drive after applying some processing steps
def export(img, img_date, geometry, folder_name, epsg, start_ndvi, end_ndvi):
    # Calculate NDVI and create masks
    ndvi = img.normalizedDifference(['B8','B4'])
    maskNDVIgt = ndvi.gt(start_ndvi)
    maskNDVIlt = ndvi.lt(end_ndvi)
    maskedNDVI = ndvi.updateMask(maskNDVIgt).updateMask(maskNDVIlt)

    # Define the output file name
    nameNDVI = (f"ndvi_{img_date}").replace('-', '')

    # Export image to Google Drive
    task = ee.batch.Export.image.toDrive(
        image=maskedNDVI,
        description=nameNDVI,
        scale=10,
        fileNamePrefix=nameNDVI,
        folder=folder_name,
        maxPixels=1e13,
        crs=f"EPSG:{epsg}",
        region = geometry.first().geometry().getInfo()['coordinates'])
    task.start()

    print(f"Image '{folder_name}/{nameNDVI}' exported successfully")
    print()

# Function definition for processing Sentinel-2 images to find low tide dates and export NDVI images to Google Drive
def process(lat, lon, keyAPIWorldTides, start_hour, end_hour, start_date, end_date, cloudy_percentage, tile, start_ndvi, end_ndvi, geometry, epsg, folder_name):  
    run_button.config(state="disabled")  
    
    # Initialize an empty list to store dates with low tide extremes
    dates_with_low_tides = []

    # Convert the input geometry to an ee.FeatureCollection
    geometry = ee.FeatureCollection(geometry)

    progress_bar['value'] = 10

    # Get the image collection and count the number of images
    imgs = get_image_collection(geometry, cloudy_percentage, start_date, end_date)
    img_count = imgs.size().getInfo()
    imgs_list = imgs.toList(img_count)

    if img_count != 0:
        progress_bar['value'] = 40
        progress_increment = 60 / img_count
        progress = 40

    # Iterate over the images in the collection
    for i in range(img_count):
        img = ee.Image(imgs_list.get(i))
        img_id = img.id().getInfo()

        progress_bar['value'] = progress + progress_increment
        progress += progress_increment

        # Check if the img_id contains the value of the tile
        if tile in img_id:
            img_date = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd').getInfo()
            low_tide_extremes = get_low_tide_extremes(img_date, lat, lon, keyAPIWorldTides)
            
            if low_tide_extremes:
                # Iterate over the low tide extremes for the image date
                for extreme in low_tide_extremes:
                    if is_time_within_range(extreme['date'], start_hour, end_hour):
                        hour = extreme['date'][11:16]
                        print()
                        print(f"For image '{img_id}', the first low tide between {start_hour:02d}:00 and {end_hour:02d}:00 on {img_date} is at {hour}")
                        dates_with_low_tides.append(img_date)
                        print()
                        export(img, img_date, geometry, folder_name, epsg, start_ndvi, end_ndvi)
                        break
            else:
                return

    if not dates_with_low_tides:
        print("No images were found that meet the conditions.")
    else:
        print()
        update_tide_dates_text(dates_with_low_tides)

# Function definition for updating a tkinter text widget with a list of dates
def update_tide_dates_text(dates):
    tide_dates_text.config(state="normal")
    tide_dates_text.delete(1.0, tk.END)
    tide_dates_text.insert(tk.END, "\n".join(dates))
    tide_dates_text.config(state="disabled")

# Function for validating the input parameters
def validate_parameters(lat, lon, keyAPIWorldTides, tile, geometry, epsg, start_hour, end_hour, start_date, end_date, cloudy_percentage, start_ndvi, end_ndvi, folder_name):
    # Check if the fields are not empty
    if not all([lat, lon, keyAPIWorldTides, tile, geometry, epsg, folder_name]):
        return False, "Fields must not be empty."

    # Validate start_hour and end_hour of low tide time range
    try:
        if not (0 <= int(start_hour) <= 24 and 0 <= int(end_hour) <= 24 and len(start_hour) == 2 and len(end_hour) == 2):
            return False, "Low tide time range must be integers between 00 and 24."
    except ValueError: 
        return False, "Invalid input. Please input numbers between 00 and 24."
    
    date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
    if not (date_pattern.fullmatch(start_date) and date_pattern.fullmatch(end_date)):
        return False, "Date range must be in the format 'YYYY-MM-DD'."
    
    # Validate start_date and end_date - Start date must be after march 2017
    if start_date < '2017-03-01':
        return False, "Start date must be after March 2017."

    # Validate cloudy_percentage
    if not (0 <= cloudy_percentage <= 100):
        return False, "Cloudy percentage must be an integer between 0 and 100."

    # Validate start_ndvi and end_ndvi
    if not (-1 <= start_ndvi <= 1 and -1 <= end_ndvi <= 1):
        return False, "NDVI range must be values between -1 and 1. (for example, 0.10 or -0.5 are valid values)"

    return True, ""

# Function for the main program
def main():
    try:
        # Get the values from the input fields
        lat = lat_entry.get()
        lon = lon_entry.get()
        keyAPIWorldTides = key_entry.get()
        start_hour = start_hour_entry.get()
        end_hour = end_hour_entry.get()
        start_date = start_date_entry.get()
        end_date = end_date_entry.get()
        cloudy_percentage = int(cloudy_percentage_entry.get())
        tile = tile_entry.get()
        start_ndvi = float(start_ndvi_entry.get())
        end_ndvi = float(end_ndvi_entry.get())
        geometry = geometry_entry.get()
        epsg = epsg_entry.get()
        folder_name = folder_name_entry.get()

        # Validate the parameters
        valid, error_message = validate_parameters(lat, lon, keyAPIWorldTides, tile, geometry, epsg, start_hour, end_hour, start_date, end_date, cloudy_percentage, start_ndvi, end_ndvi, folder_name)
        if not valid:
            messagebox.showerror("Error", error_message)
            run_button.config(state="normal")
            progress_bar['value'] = 0
            return

        # Call the process function with the input values
        process(lat, lon, keyAPIWorldTides, int(start_hour), int(end_hour), start_date, end_date, cloudy_percentage, tile, start_ndvi, end_ndvi, geometry, epsg, folder_name)
    except ValueError as ve:
        messagebox.showerror("Error", f"Invalid input value: {ve}")
        run_button.config(state="normal")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        run_button.config(state="normal")
    finally:
        progress_bar['value'] = 100
        run_button.config(state="normal")

def run_main_in_thread():
    progress_bar['value'] = 0
    clear_console_output()
    main_thread = threading.Thread(target=main)
    main_thread.start()

########################  View Components  #############################

root = tk.Tk()

root.title("BioIntertidal Mapper")

# Create login button
login_button = tk.Button(root, text="Login in Google Earth Engine", command=authenticate)
login_button.grid(row=0, column=0, columnspan=2, pady=(20, 20))

fields = [
    {"label": "Latitude:", "entry": "lat_entry"},
    {"label": "Longitude:", "entry": "lon_entry"},
    {"label": "API Key of World Tides:", "entry": "key_entry"},
    {"label": "Low Tide Time Range (HH):", "entry": ["start_hour_entry", "end_hour_entry"]},
    {"label": "Date Range (YYYY-MM-DD):", "entry": ["start_date_entry", "end_date_entry"]},
    {"label": "Maximum cloud percentage:", "entry": "cloudy_percentage_entry"},
    {"label": "Tile number field:", "entry": "tile_entry"},
    {"label": "NDVI Range:", "entry": ["start_ndvi_entry", "end_ndvi_entry"]},
    {"label": "Geometry (.shp) url in your GEE:", "entry": "geometry_entry"},
    {"label": "CRS(EPSG):", "entry": "epsg_entry"},
    {"label": "Folder name (in your Google Drive):", "entry": "folder_name_entry"},
]

entry_fields = []

initial_state = "disabled"

def create_range_entries(root, initial_state, width):
    start_entry = tk.Entry(root, state=initial_state, width=width)
    start_entry.grid(row=i+1, column=1, padx=(10, 5), pady=(5, 5), sticky="W")
    
    to_label = tk.Label(root, text="to")
    to_label.grid(row=i+1, column=1)
    
    end_entry = tk.Entry(root, state=initial_state, width=width)
    end_entry.grid(row=i+1, column=1, padx=(5, 35), pady=(5, 5), sticky="E")
    
    return start_entry, end_entry

for i, field in enumerate(fields):
    label = tk.Label(root, text=field["label"])
    label.grid(row=i+1, column=0, padx=(25,10), pady=(5, 5), sticky="W")

    if field["label"] == "Low Tide Time Range (HH):":
        help_button = tk.Button(root, text="?", width=1, height=1, command=show_help)        
        help_button.grid(row=i+1, column=0, padx=(0, 5), pady=(5, 5), sticky="E") 

        start_hour_entry, end_hour_entry = create_range_entries(root, initial_state, 8)

    elif field["label"] == "Date Range (YYYY-MM-DD):":
        start_date_entry, end_date_entry = create_range_entries(root, initial_state, 13)

    elif field["label"] == "NDVI Range:":
        start_ndvi_entry, end_ndvi_entry = create_range_entries(root, initial_state, 8)

    else:
        entry = tk.Entry(root, state=initial_state, width=38)
        entry.grid(row=i+1, column=1, padx=(0,25), pady=(5, 5))

    entry_fields.extend([start_hour_entry, end_hour_entry] if field["label"] == "Low Tide Time Range (HH):" else
                        [start_date_entry, end_date_entry] if field["label"] == "Date Range (YYYY-MM-DD):" else
                        [start_ndvi_entry, end_ndvi_entry] if field["label"] == "NDVI Range:" else
                        [entry])

lat_entry, lon_entry, key_entry, start_hour_entry, end_hour_entry, start_date_entry, end_date_entry, cloudy_percentage_entry, tile_entry, start_ndvi_entry, end_ndvi_entry, geometry_entry, epsg_entry, folder_name_entry = entry_fields

# Create execute button
run_button = tk.Button(root, text="Execute", command=run_main_in_thread, state="disabled", width=20, height=2)
run_button.grid(row=len(fields)+2, column=1, pady=(25,0))

# Create label "Output"
console_output_title = tk.Label(root, text="Output:")
console_output_title.grid(row=0, column=3)

# Create the text widget to display the console output
console_output_text = ScrolledText(root, wrap=tk.WORD, width=50, height=15, state="disabled")
console_output_text.grid(row=1, column=3, rowspan=len(fields)//2, padx=25, sticky="N")

# Create the label "Dates with images acquired during low tide":
tide_dates_title = tk.Label(root, text="Dates with images acquired during low tide:")
tide_dates_title.grid(row=len(fields)//2 + 1, column=3, pady=(10,5))

# Create the text widget to display the dates with tides
tide_dates_text = ScrolledText(root, wrap=tk.WORD, width=50, height=9, state="disabled")
tide_dates_text.grid(row=len(fields)//2 + 2, column=3, rowspan=len(fields)//2, padx=25, pady=(0,5), sticky="N")

# Create the Clear button
clear_button = tk.Button(root, text="Clear console", command=clear_console_output, width=10, height=1)
clear_button.grid(row=len(fields) + 2, column=3, padx=25, pady=(25, 25), sticky="NE")

# Create labels Haro, S. and email
sara_label = tk.Label(root, text="Haro, S.")
sara_label.grid(row=len(fields) + 3, column=3, padx=25, sticky="E")
sara_label2 = tk.Label(root, text="haropaez.sara@gmail.com")
sara_label2.grid(row=len(fields) + 4, column=3, padx=25, pady=(2,15), sticky="E")

progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
progress_bar.grid(row=len(fields) + 3, column=1, columnspan=2, pady=(15, 0))

# Redirect standard output (stdout) to the text widget
sys.stdout = OutputText(console_output_text)

root.mainloop()
