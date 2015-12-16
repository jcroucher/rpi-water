#
# Used for running watering programs and triggering the hardware relays
#

import RPi.GPIO as GPIO
import time

import config
import core.Database


#
# Main class for all our bits!
#
class ZoneProgramRunner:

    class __ZoneProgramRunner:

        sleepTime = 60  # seconds. Used for main loop timeout. Changing this value will affect calculations.

        failSafeCount = 0       # The number of ticks passed since the last zone was turned off.
        programsRunningCount = 0   # Store the number of programs running
        running_zones = set([])

        activePins = []     # This list is so we can quickly turn off any active pins when the progam exists

        flow_pulses = 0
        flow_rate = 0.0

        db = None   # Hold our database connection

        def __init__(self):
            self.db = core.Database.DatabaseConnection()

            if config._safe_mode is False:
                self.setup_pins();
                self.reset_programs();
            else:
                print("Running in safe mode")

        # Find all the pins defined and set them up for output
        def setup_pins(self):

            print("Setting up output pins")
            sql = """select setting_value from settings where setting_key = 'board_mode'"""
            cursor = self.db.query(sql)

            row = cursor.fetchone()
            if row is not None:
                if row[0] == "bcm":
                    GPIO.setmode(GPIO.BCM)
                else:
                    GPIO.setmode(GPIO.BOARD)

            # Relay/Valve Pins
            sql = """select zone_id, pin_number from zones where active = 1 and pin_number > 0"""
            cursor = self.db.query(sql)

            for (zone_id, pin_number) in cursor:
                self.activePins.append(pin_number)
                GPIO.setup(pin_number, GPIO.OUT)
                GPIO.output(pin_number, config._relay_off)

            # Flow rate sensor
            sql = """select setting_value from settings where setting_key = 'gpio_flow_sensor'"""
            cursor = self.db.query(sql)

            flow_sensor_pin = 0

            row = cursor.fetchone()
            if row is not None:
                flow_sensor_pin = int(row[0])
            else:
                print("Flow sensor is not configured")

            if flow_sensor_pin > 0:
                print("Flow sensor configured on pin: " + str(flow_sensor_pin))
                GPIO.setup(int(flow_sensor_pin), GPIO.IN, pull_up_down = GPIO.PUD_UP) 
                GPIO.add_event_detect(int(flow_sensor_pin), GPIO.FALLING, callback=self.count_pulse)

        def count_pulse(self,channel):
            self.flow_pulses += 1
            print(self.flow_pulses)

        # Make sure all the programs are turned off when we start
        def reset_programs(self):

            print("Reseting program states")
            sql = """update zone_programs set running = 0"""
            self.db.query(sql)

        # Needed for cleanup
        def zero_active_pins(self):

            for(pin_number) in self.activePins:
                GPIO.output(pin_number, config._relay_off)

        # Looopy
        def main_loop(self):

            while True:

                self.run_program()
                self.end_program()

                print("Tick")

                # Only use the fail safe if there are zones running
                if self.programsRunningCount > 0:
                    self.failSafeCount += 1

                if self.failSafeCount > config.failSafe:
                    print("Been watering too long. Something maybe wrong. Quitting")
                    self.cleanup()
                    quit()

                # Todo: Make get the calculation reflect the amount specified by user from database
                self.flow_rate = round(self.flow_pulses / 450, 2)
                self.flow_pulses = 0.0

                time.sleep(self.sleepTime)

        # Find all the programs that need to be turned on
        def run_program(self):

            # Todo: More run options and checking. Fields exist in settings but are not implemented
            #
            sql = """select program_id, zone_id, start_time from zone_programs where
                    time('now','localtime') > time(start_time)
                    and time('now','localtime') < time(start_time, '+'||duration||' minute')
                    and ( last_run is null or date('now') >= datetime(last_run, '+'||day_interval||' days') )
                    and active = 1 and running = 0"""

            cursor = self.db.query(sql)

            for (program_id, zone_id, start_time) in cursor:
                self.toggle_zone(zone_id, "on")      # Trigger relay
                self.update_program_status(1,program_id)    # Mark the program as running

                self.programsRunningCount += 1

                print("Zone turned on " + str(zone_id))

        # Find all the zones that need to be turned off
        def end_program(self):

            sql = """select program_id, zone_id, start_time, run_once from zone_programs where
                    (time('now','localtime') > time(start_time, '+'||duration||' minute')) and
                    active = 1 and running = 1"""
            cursor = self.db.query(sql)

            for (program_id, zone_id, start_time, run_once) in cursor:
                self.toggle_zone(zone_id, "off")     # Trigger relay
                self.update_program_status(0,program_id)    # Mark the program as not running

                self.failSafeCount = 0
                self.programsRunningCount -= 1

                if run_once == 1:
                    self.delete_program(program_id)

                print("Zone turned off " + str(zone_id))

        # The actual turning on and off of the Pi pins
        def toggle_zone(self, zone_id, mode):

            # Get the pin number for the zone
            sql = """select zone_id, pin_number from zones where zone_id = ?"""
            cursor = self.db.query(sql, (int(zone_id),))

            (zone_id, pin_number) = cursor.fetchone()

            if pin_number > 0:

                print(pin_number)

                if mode == "on":
                    if zone_id not in self.running_zones:

                        if config._relay_pulse:
                            GPIO.output(pin_number, config._relay_on)
                            time.sleep(config._pulse_time)
                            GPIO.output(pin_number, config._relay_off)
                        else:
                            GPIO.output(pin_number, config._relay_on)

                        self.running_zones.add(zone_id)

                        sql = """update zones set last_run = datetime('now') where zone_id = ?"""
                        self.db.query(sql, (int(zone_id),))

                        self.log_zone(zone_id,'turning on zone')  # Create a log entry

                    else:
                        print("Zone " + str(zone_id) + " already running")

                else:
                    if config._relay_pulse:
                        GPIO.output(pin_number, config._relay_on)
                        time.sleep(config._pulse_time)
                        GPIO.output(pin_number, config._relay_off)
                    else:
                        GPIO.output(pin_number, config._relay_off)

                    if zone_id in self.running_zones:
                        self.running_zones.remove(zone_id)

                    self.log_zone(zone_id,'turning off zone')  # Create a log entry

        def deactivate_zone(self, zone_id, mode):

            if mode == "enable":
                sql = """update zones set active = 1 where zone_id = ?"""
            else:
                sql = """update zones set active = 0 where zone_id = ?"""

            self.db.query(sql, (int(zone_id)))

        # Logs so we can see a history of the zones
        def log_zone(self,zone_id,log):

            sql = """insert into zone_log(log_time,zone_id,note) values(datetime('now'),?,?);"""
            self.db.query(sql, (int(zone_id), str(log)))

            print("Logging")

        # Change the program running status
        def update_program_status(self,status,program_id):

            sql = """update zone_programs set last_run = datetime('now'), running = ? where program_id = ?"""

            self.db.query(sql, (int(status), int(program_id)))

        # Delete a program
        def delete_program(self, program_id):

            sql = """delete from zone_programs where program_id = ?"""
            self.db.query(sql,(int(program_id),))

            print("Program deleted")

        def cleanup(self):
            self.zero_active_pins()
            GPIO.cleanup() # this ensures a clean exit

    instance = None

    def __init__(self):
        if not ZoneProgramRunner.instance:
            ZoneProgramRunner.instance = ZoneProgramRunner.__ZoneProgramRunner()

    def __getattr__(self, name):
        return getattr(self.instance, name)
