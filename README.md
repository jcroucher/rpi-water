# rpi-water
Raspberry Pi Watering System


Running

Make sure you have the following components installed

$ sudo apt-get install python3 python3-pip python3-rpi.gpio
$ sudo pip3 install sqlite3 cherrypy jinja2

$ python3 service.py

If you have any issues with starting the app you can use 

$ python3 service.py safemode

This will disable a number of things allowing you to modify settings

From your browser navigate to http://PI-IP:8080

