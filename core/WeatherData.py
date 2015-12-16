#
# Get the latest weather data from a 3rd party source.
# Currently setup to use weather underground http://wunderground.com
#

import json
import urllib.request
import threading

import config
import core.Database


class WeatherData:

    class __WeatherData:

        db = None

        current_temperature = 0
        max_temp = 0
        min_temp = 0
        pop = 0  # Percent chance of Precipitation
        pre_today = 0

        weather_settings = {
            'weather_api_key': '',
            'weather_city': '',
            'weather_country': '',
            'weather_poll_freq': 30
        }

        def __init__(self):
            self.db = core.Database.DatabaseConnection()

            if config._safe_mode is False:
                self.get_weather_settings()
                self.poll()
            else:
                print("Safe Mode no Weather Data")

        def get_weather_settings(self):

            sql = """select setting_key, setting_value from settings where setting_key like 'weather_%%'"""
            cursor = self.db.query(sql)

            for (setting_key, setting_value) in cursor:
                self.weather_settings[setting_key] = setting_value

        def poll(self):

            print("Updating Weather Data")

            weather_poll_freq = int(self.weather_settings['weather_poll_freq'])

            if weather_poll_freq <= 0:
                weather_poll_freq = 30

            weather_poll_freq *= 60  # Convert minutes to seconds

            threading.Timer(weather_poll_freq, self.poll).start()  # Repeat this function in the time specified

            # Make sure we have settings before going further
            for setting_key in self.weather_settings:
                if self.weather_settings[setting_key] == "" or self.weather_settings[setting_key] == 0:
                    print("No weather settings")
                    return

            # Wrapped up in a block as sometimes there is no response
            try:
                request = 'http://api.wunderground.com/api/'
                request += self.weather_settings['weather_api_key']
                request += '/geolookup/conditions/forecast/q/'
                request += self.weather_settings['weather_country'] + '/'
                request += self.weather_settings['weather_city'] + '.json'

                response = urllib.request.urlopen(request).read().decode('utf8')
                obj = json.loads(response)

                self.current_temperature = obj['current_observation']['temp_c']
                self.max_temp = obj['forecast']['simpleforecast']['forecastday'][0]['high']['celsius']
                self.min_temp = obj['forecast']['simpleforecast']['forecastday'][0]['low']['celsius']

                self.pop = obj['forecast']['simpleforecast']['forecastday'][0]['pop']
                self.pre_today = obj['current_observation']['precip_today_metric']

            except Exception as e:
                print("Error getting weather data")

    instance = None

    def __init__(self):
        if not WeatherData.instance:
            WeatherData.instance = WeatherData.__WeatherData()

    def __getattr__(self, name):
        return getattr(self.instance, name)