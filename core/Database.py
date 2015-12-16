# Used for holding our database connection.
#
# At the moment the class is reused. I have had to put in check_same_thread=False to prevent an error about
# accessing the same sqlite connection from different threads. This should probably be fixed to either use multiple
# connections, as needed connections, or a query queue.
#
import sqlite3


class DatabaseConnection:

    class __DatabaseConnection:

        conn = None

        def __init__(self):
            pass

        def connect(self):

            print("connecting to database")

            self.conn = sqlite3.connect('water.db', check_same_thread=False)
            self.setup_database()

        def query(self, sql, v=()):

            try:
                cursor = self.conn.cursor()
                cursor.execute(sql, v)

            except AttributeError:
                self.connect()
                cursor = self.conn.cursor()
                cursor.execute(sql, v)

            self.conn.commit()

            return cursor

        def setup_database(self):

            self.conn.execute("""CREATE TABLE IF NOT EXISTS `zones` (
                                  `zone_id` INTEGER PRIMARY KEY,
                                  `pin_number` INTEGER NOT NULL DEFAULT '0',
                                  `pin_number_2` INTEGER NOT NULL DEFAULT '0',
                                  `zone_name` TEXT DEFAULT NULL,
                                  `last_run` datetime DEFAULT NULL,
                                  `active` INTEGER DEFAULT '1',
                                  `solenoid_pulse` INTEGER NOT NULL DEFAULT '0',
                                  `solenoid_latching` INTEGER NOT NULL DEFAULT '0',
                                  `zone_type` INTEGER NOT NULL DEFAULT '0'
                                )""")

            self.conn.execute("""CREATE TABLE IF NOT EXISTS `zone_programs` (
                              `program_id` INTEGER PRIMARY KEY,
                              `zone_id` INTEGER NOT NULL,
                              `start_time` TEXT DEFAULT NULL,
                              `day_interval` INTEGER DEFAULT NULL,
                              `duration` INTEGER DEFAULT NULL,
                              `running` INTEGER DEFAULT '0',
                              `active` INTEGER DEFAULT '1',
                              `last_run` date DEFAULT NULL,
                              `run_once` INTEGER DEFAULT '0'
                            )""")

            self.conn.execute("""CREATE TABLE IF NOT EXISTS `zone_log` (
                                  `log_id` INTEGER PRIMARY KEY,
                                  `zone_id` INTEGER,
                                  `log_time` datetime,
                                  `note` TEXT
                                )""")


            self.conn.execute("""CREATE TABLE IF NOT EXISTS `settings` (
                                  `setting_key` TEXT PRIMARY KEY,
                                  `setting_value` text
                                )""")

            self.conn.commit()

            cursor = self.conn.execute("""select setting_key, setting_value from settings""")
            num_rows = len(cursor.fetchall())

            # No settings? Insert the default values
            if num_rows <= 0:
                self.conn.execute("""insert into settings(setting_key,setting_value) values ('fail_safe','120')""")
                self.conn.execute("""insert into settings(setting_key,setting_value) values ('max_zones','1')""")
                self.conn.execute("""insert into settings(setting_key,setting_value) values ('weather_poll_freq','30')""")
                self.conn.execute("""insert into settings(setting_key,setting_value) values ('email_logs','1')""")
                self.conn.execute("""insert into settings(setting_key,setting_value) values ('flow_warning','1')""")
                self.conn.execute("""insert into settings(setting_key,setting_value) values ('off_flow_warning','1')""")
                self.conn.execute("""insert into settings(setting_key,setting_value) values ('extend_program_temp','35')""")
                self.conn.execute("""insert into settings(setting_key,setting_value) values ('extend_program_minutes','0')""")
                self.conn.execute("""insert into settings(setting_key,setting_value) values ('board_mode','bcm')""")
                self.conn.execute("""insert into settings(setting_key,setting_value) values ('unit','lpm')""")

                self.conn.commit()

    instance = None

    def __init__(self):
        if not DatabaseConnection.instance:
            DatabaseConnection.instance = DatabaseConnection.__DatabaseConnection()

    def __getattr__(self, name):
        return getattr(self.instance, name)
