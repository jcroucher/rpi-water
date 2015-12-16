#
# This class is used for saving and loading of general settings.
# The settings are stored in the database in a key/value pair
#
import core.Database


class WaterSettings:

    class __WaterSettings:

        db = None

        current_settings = {}  # All settings are stored here, the values are saved and loaded from here

        def __init__(self):
            self.db = core.Database.DatabaseConnection()
            self.load_settings()

        def load_settings(self):
            sql = """select setting_key, setting_value from settings"""
            cursor = self.db.query(sql)

            for (key, value) in cursor:
                self.current_settings[key] = value

        def save_settings(self):

            for key, value in self.current_settings.items():

                sql = """REPLACE INTO settings
                          (setting_key,setting_value)
                        VALUES
                          (?, ?)"""

                values = (str(key), str(value))
                self.db.query(sql, values)

        def get_setting(self,key):

            value = None

            if key in self.current_settings:
                value = self.current_settings

            return value

        def update_setting(self, key, value):
            self.current_settings[key] = value
            self.save_settings()

    instance = None

    def __init__(self):
        if not WaterSettings.instance:
            WaterSettings.instance = WaterSettings.__WaterSettings()

    def __getattr__(self, name):
        return getattr(self.instance, name)