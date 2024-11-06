from supabase import create_client, Client
from dronekit import connect, VehicleMode, LocationGlobalRelative
import time
from threading import Thread
import tkinter as tk

# Supabase credentials
SUPABASE_URL = "https://wwpozvjnhkreypawoeox.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind3cG96dmpuaGtyZXlwYXdvZW94Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjQ2NDcyMjAsImV4cCI6MjA0MDIyMzIyMH0.wARfqQNaLN5mt3K2QKjs82QP0Cav39PdBlc3GsrtUWw"

# Connect to Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch the latest coordinates (latitude, longitude) from Supabase
def fetch_latest_coordinates():
    response = supabase.table('coordinates').select("latitude, longitude").order('id', desc=True).limit(1).execute()
    
    if response.data:
        latest_entry = response.data[0]
        latitude = latest_entry['latitude']
        longitude = latest_entry['longitude']
        print(f"Latest coordinates fetched from Supabase: Latitude={latitude}, Longitude={longitude}")
        return latitude, longitude
    else:
        print("No coordinates found in the database.")
        return None, None

# Connect to the Vehicle
connection_string = '/dev/ttyACM0'
vehicle = connect(connection_string, baud=57600, wait_ready=True)

# Function to arm the drone and take off
def arm_and_takeoff(target_altitude):
    print("Basic pre-arm checks")
    
    # Check if vehicle is armable
    while not vehicle.is_armable:
        print(" Waiting for vehicle to initialize...")
        time.sleep(1)

    print("Arming vehicle")
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.arm()

    # Wait until vehicle is armed
    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)

    print("Taking off!")
    vehicle.simple_takeoff(target_altitude)

    # Wait until the vehicle reaches a safe height
    while True:
        print(" Altitude: ", vehicle.location.global_relative_frame.alt)
        if vehicle.location.global_relative_frame.alt >= target_altitude * 0.95:
            print("Reached target altitude")
            break
        time.sleep(1)

# Function to navigate to a specified location
def goto_location(lat, lon):
    print(f"Navigating to Latitude: {lat}, Longitude: {lon}")
    target_location = LocationGlobalRelative(lat, lon, vehicle.location.global_relative_frame.alt)
    vehicle.simple_goto(target_location)

# Function to hover
def hover():
    print("Drone hovering at the target location")

# Function to return to launch
def return_to_launch():
    print("Enabling RTL (Return to Launch)")
    vehicle.mode = VehicleMode("RTL")

# GUI functions
def takeoff_button_action():
    # Fetch the latest coordinates from Supabase
    latitude, longitude = fetch_latest_coordinates()

    if latitude is not None and longitude is not None:
        target_altitude = 5  # meters
        print("Takeoff initiated...")

        # Run takeoff and go to location in a separate thread
        thread = Thread(target=lambda: [arm_and_takeoff(target_altitude), goto_location(latitude, longitude), hover()])
        thread.start()
    else:
        print("No valid coordinates to navigate to.")

def rtl_button_action():
    # Run RTL in a separate thread
    thread = Thread(target=return_to_launch)
    thread.start()

# GUI setup
def setup_gui():
    root = tk.Tk()
    root.title("Drone Control")

    # Takeoff button
    takeoff_button = tk.Button(root, text="Takeoff", command=takeoff_button_action, width=20, height=2)
    takeoff_button.pack(pady=20)

    # RTL button
    rtl_button = tk.Button(root, text="RTL", command=rtl_button_action, width=20, height=2)
    rtl_button.pack(pady=20)

    # Start the GUI main loop
    root.mainloop()

# Start the GUI
setup_gui()

# Close vehicle object before exiting script
vehicle.close()

