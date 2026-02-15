# Environmental sensing with Python & Bluetooth Low Energy sensors

The aim of this project is to collect temperature, humidity & pressure data from inexpensive sensors into a SQLite3 database and then create a modern dashboard to review the data. Ultimately I plan to reconcile these data against NOAA data from the nearest weather station to examine the deviation at the test location.

There are 3 Python scripts:

###code.py
Runs on adafruit feather sense boards running circuit python.
This code reads the sensors and encodes the data into a BLE advertisement that is transmitted regularly and reflects state of sensors at time of transmission. Note the current version of this file in this repo is a stub that will be updated soon!

###receiver.py
Currently runs on a beaglebone black revision C (but will run on a raspberry Pi or any similar SBC.)
This code receives the BLE advertisements from the feather sense boards, parses them and logs to a SQLite3 database named weather_data.db  Sensor board IDs must be hard coded into the script to filter out extraneous BLE packets in noisy environments.

###dashboard.py
This code runs on a Linux machine with a GUI.
Presently, I grab the weather_data.db file to my laptop and run the dashboard there. The Streamlit dashboard allows to select an individual sensor and plot data from any subset of sensors, plus the signal strength for debugging/development purposes.

## Installation
I'm using pixi to manage my environment. The dependencies described in pixi.toml include some that are not needed to run this project (e.g. spyder-kernels, jupyterlab, numpy, scipy, altair & paramiko are not needed, but may be used as I develop the project further to automate grabbing the db, etc.)


## Usage
upload code.py to the feather sense board(s), which must have circuit Python installed
run receiver.py on your SBC of choice
sftp or otherwise make available 'weather_data.db' on a machine with a GUI and run:
pixi run streamlit run dashboard.py

An representative plot of 5,477 data points (a few days) is shown in example_plot.png

## Future direction
The sensor code needs to be more optimized for low power by increasing the period between BLE advertisements and removing the LED blinking. Add a function to read battery voltage and transmit that value every 6 hours.

I would like to modify recevier.py to also parse the BLE packets from a Xiaomi Thermometer LYWSD03MMC running custom firmware since for indoor sensors, these are cheap and effective. See: https://github.com/atc1441/ATC_MiThermometer  Add parsing of battery voltage.

Having the SBC serve the Streamlit as a web page available on my LAN would also be preferred from a UX perspective.

Eventually I would like to pull data from NOAA for the 'official' weather in my area and be able to plot it next to my own sensor data. The most interesting scenerio here would be if I can get enough BLE range to sample various microclimates at the target location. This would help me understand the local variability.

## Acknowledgement
This project was inspired by the IoT garden project from Python Playground 2nd Ed. by Mahesh Venkitachalam. I decided to modify how the sensor data were encoded, adjust the receiver script, delete the "if this then that" alerts and use a more modern dashboard approach.
