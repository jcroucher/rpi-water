import RPi.GPIO as GPIO
import os

_safe_mode = False

# Defined here as this may need to change depending on wiring
_relay_on = GPIO.LOW
_relay_off = GPIO.HIGH
_relay_pulse = False
_pulse_time = 0.5

# Used to try and prevent endless watering. This is number of sleepTime ticks.
# So if sleepTime is set to 60 seconds, then failSafe would be in minutes
failSafe = 120

path = os.path.abspath(os.path.dirname(__file__))

webconf = {
        '/': {
         'tools.sessions.on': True,
         'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/public': {
         'tools.staticdir.on': True,
         'tools.staticdir.dir': './public'
        }
    }


