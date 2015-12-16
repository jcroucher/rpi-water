
import cherrypy
import datetime

import config
import core.Database
import core.Hardware
import core.WeatherData
import core.WaterSettings

from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('templates'))


class WaterAdmin(object):

    db = None   # Hold our database connection

    # Status bits
    web_common = {
        '_running_zones': 0,
        '_flow_rate': 0,
        '_soil_moisture': 0
    }

    water = core.Hardware.ZoneProgramRunner()
    weather = core.WeatherData.WeatherData()
    water_settings = core.WaterSettings.WaterSettings()

    def __init__(self):
        cherrypy.config.update({'error_page.404': self.system_error})
        self.db = core.Database.DatabaseConnection()

    @cherrypy.expose
    def index(self, mode="off", zone=0):

        rows = []

        # Request to turn on and off zones
        if int(zone) > 0:
            if mode == 'off' or mode == 'on':
                self.water.toggle_zone(zone, mode)
            elif mode == 'enable' or mode == 'disable':
                self.water.deactivate_zone(zone, mode)

        # Get the zone details
        sql = """select zone_id, pin_number, zone_name, last_run, active, zone_type from zones"""
        cursor = self.db.query(sql)

        for (zone_id, pin_number, zone_name, last_run, active, zone_type) in cursor:

            running = "Off"
            button_running = "On"

            if zone_id in self.water.running_zones:
                running = "On"
                button_running = "Off"

            button_active = "enable"

            if active == 1:
                button_active = "disable"

            rows.append([zone_id, zone_name, last_run, running, button_running, button_active, zone_type])

        params = {'rows': rows}
        return self.render_template("zones.html", params)

    @cherrypy.expose
    def editzone(self, **kwargs):

        # All the editable zone details
        zone_values = {
            'pin_number': 'int',
            'pin_number_2': 'int',
            'zone_name': 'str',
            'last_run': 'str',
            'active': 'int',
            'zone_type': 'int',
            'solenoid_pulse': 'int',
            'solenoid_latching': 'int'
        }

        if 'zone' in kwargs:

            try:
                zone_id = int(kwargs['zone'])
            except ValueError:
                return self.error_page('Invalid Zone')

            # User has requested save
            if 'save' in kwargs:
                update_list = []
                insert_list = []
                insert_placeholder = []
                post_values = []

                # Get all our values from the user
                for value_name in zone_values:
                    if value_name in kwargs:
                        update_list.append(value_name + '=?')

                        insert_list.append(value_name)
                        insert_placeholder.append('?')

                        # Format the post values to the correct types
                        if zone_values[value_name] == "int":
                            try:
                                post_values.append(int(kwargs[value_name]))
                            except ValueError:
                                # User put in a non int value in, default to zero.
                                # It would be better to display an error instead.
                                post_values.append(0)
                        else:
                            post_values.append(str(kwargs[value_name]))

                # Update or insert
                if zone_id > 0:
                    sql_update = """update zones set """
                    sql_update += ', ' .join(update_list)
                    sql_update += """ where zone_id = ?"""

                    post_values.append(zone_id)
                    self.db.query(sql_update, post_values)

                else:
                    sql_update = "insert into zones(zone_id, "
                    sql_update += ', ' .join(insert_list) + ") values(NULL, "
                    sql_update += ', ' .join(insert_placeholder) + ")"
                    cursor = self.db.query(sql_update, post_values)
                    zone_id = cursor.lastrowid

                # Redirect to the edit page after save. This is to prevent resubmission along with
                # sending the user to the new zone if the request was an insert
                raise cherrypy.HTTPRedirect("/editzone?zone=" + str(zone_id))

            # Get the existing values for display
            # Generate the sql query from the list of fields available
            sql = """select """
            sql += ', ' .join(zone_values)
            sql += """ from zones where zone_id = ?"""

            cursor = self.db.query(sql, (zone_id,))

            params = {}
            field_count = 0

            # Get the values in the database and add to the template
            for r in cursor.fetchall():
                for value_name in zone_values:
                    params[value_name] = r[field_count]
                    field_count += 1

            params['zone_id'] = zone_id

            return self.render_template("edit_zone.html", params)
        else:
            return self.error_page('Invalid Zone')

    @cherrypy.expose
    def deletezone(self, **kwargs):

        if 'zone' in kwargs:

            try:
                zone_id = int(kwargs['zone'])
            except ValueError:
                return self.error_page('Invalid Zone')

            sql = "delete from zones where zone_id = ?"
            self.db.query(sql, [zone_id])

            # Zone has been deleted, redirect home
            raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def editprogram(self, **kwargs):

        # Todo: Program list shows the Zone ID instead of the Zone Name

        # All the editable program details
        program_values = {
            'zone_id': 'int',
            'start_time': 'str',
            'day_interval': 'str',
            'duration': 'int',
            'running': 'int',
            'active': 'int',
            'last_run': 'str',
            'run_once': 'int'
        }

        if 'program' in kwargs:

            try:
                program_id = int(kwargs['program'])
            except ValueError:
                return self.error_page('Invalid Program')

            # User has requested save
            if 'save' in kwargs:
                update_list = []
                insert_list = []
                insert_placeholder = []
                post_values = []

                # Get all our values from the user
                for value_name in program_values:
                    if value_name in kwargs:
                        update_list.append(value_name + '=?')

                        insert_list.append(value_name)
                        insert_placeholder.append('?')

                        # Format the post values to the correct types
                        if program_values[value_name] == "int":
                            try:
                                post_values.append(int(kwargs[value_name]))
                            except ValueError:
                                # User put in a non int value in, default to zero.
                                # It would be better to display an error instead.
                                post_values.append(0)
                        else:
                            post_values.append(str(kwargs[value_name]))

                # Update or insert
                if program_id > 0:
                    sql_update = """update zone_programs set """
                    sql_update += ', ' .join(update_list)
                    sql_update += """ where program_id = ?"""

                    post_values.append(program_id)
                    self.db.query(sql_update, post_values)

                else:
                    sql_update = "insert into zone_programs(program_id, "
                    sql_update += ', ' .join(insert_list) + ") values(NULL, "
                    sql_update += ', ' .join(insert_placeholder) + ")"
                    cursor = self.db.query(sql_update, post_values)
                    program_id = cursor.lastrowid

                # Redirect to the edit page after save. This is to prevent resubmission along with
                # sending the user to the new zone if the request was an insert
                raise cherrypy.HTTPRedirect("/editprogram?program=" + str(program_id))

            # Get the existing values for display
            # Generate the sql query from the list of fields available
            sql = """select """
            sql += ', ' .join(program_values)
            sql += """ from zone_programs where program_id = ?"""

            cursor = self.db.query(sql, (program_id,))

            params = {}
            field_count = 0

            # Get the values in the database and add to the template
            for r in cursor.fetchall():
                for value_name in program_values:
                    params[value_name] = r[field_count]
                    field_count += 1

            params['program_id'] = program_id
            params['zones'] = self.get_zones()

            return self.render_template("edit_program.html", params)
        else:
            return self.error_page('Invalid Program')


    @cherrypy.expose
    def deleteprogram(self, **kwargs):

        if 'program' in kwargs:

            try:
                program_id = int(kwargs['program'])
            except ValueError:
                return self.error_page('Invalid Program')

            sql = "delete from zone_programs where program_id = ?"
            self.db.query(sql, [program_id])

            # Program has been deleted, redirect home
            raise cherrypy.HTTPRedirect("/programs")

    @cherrypy.expose
    def programs(self):

        rows = []

        sql = """select
                  program_id,
                  zone_id,
                  start_time,
                  day_interval,
                  duration,
                  running,
                  active,
                  last_run,
                  run_once
                  from zone_programs"""

        cursor = self.db.query(sql)

        for (program_id, zone_id, start_time, day_interval, duration, running, active, last_run, run_once) in cursor:
            rows.append([program_id, zone_id, start_time, day_interval, duration, running, active, last_run, run_once])

        params = {
            'rows': rows
        }
        return self.render_template("programs.html",params)

    @cherrypy.expose
    def settings(self, **kwargs):

        # Everything else is done in WaterSettings.py

        if 'save' in kwargs:
            for key in kwargs:
                self.water_settings.update_setting(key, kwargs[key])

        return self.render_template("settings.html", {})

    @cherrypy.expose
    def logs(self):
        # Todo: Make logs page work
        return self.render_template("logs.html", {})

    @cherrypy.expose
    def calibrate(self):
        # Todo: Finish calibration section
        return self.render_template("calibrate.html", {'message': "Waiting for reading"})

    # There are common things we need on each page, so we do all the rendering through one function
    def render_template(self, template_file,params):

        self.web_common['_running_zones'] = len(self.water.running_zones)
        self.web_common['_flow_rate'] = self.water.flow_rate

        self.web_common['current_temperature'] = self.weather.current_temperature
        self.web_common['max_temp'] = self.weather.max_temp
        self.web_common['min_temp'] = self.weather.min_temp

        self.web_common['pop'] = self.weather.pop
        self.web_common['pre_today'] = self.weather.pre_today

        self.web_common['current_time'] = datetime.datetime.strftime(datetime.datetime.now(), '%d-%m-%Y %I:%M %p')

        params['settings'] = self.water_settings.current_settings

        params.update(self.web_common)
        tmpl = env.get_template(template_file)
        return tmpl.render(params)

    # Used for drop down lists
    def get_zones(self):

        zone_list = []

        sql = """select zone_id, zone_name from zones"""
        cursor = self.db.query(sql)

        for (zone_id, zone_name) in cursor:
            zone_list.append({'zone_id': zone_id, 'zone_name': zone_name})

        return zone_list

    # System error displays the error page
    def system_error(self, status, message, traceback, version):
        return self.error_page(message)

    def error_page(self, message):
        return self.render_template("error_page.html", {'error_message': message})

    def message_page(self, message):
        return self.render_template("message_page.html", {'message': message})

    @cherrypy.expose
    def restart(self, mode='r'):
        if mode == "r" or mode == "h":
            command = "/usr/bin/sudo /sbin/shutdown -" + mode + " now"
            import subprocess
            process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
            output = process.communicate()[0]
            print(output)

            self.water.cleanup()
            cherrypy.engine.exit()

            if mode == "r":
                self.water.log_zone(0, "Rebooting System")
                return self.message_page("Rebooting System")
            else:
                self.water.log_zone(0, "Shutting Down System")
                return self.message_page("Shutting Down System")
        else:
            return self.message_page("Invalid option")


class WebRunner:

    def start_web(self):
        cherrypy.tree.mount(WaterAdmin(), '/', config.webconf)

        # This can be changed if you require the system to listen on a specific IP
        cherrypy.server.socket_host = '0.0.0.0'
        cherrypy.engine.start()
        pass

    def cleanup(self):
        cherrypy.engine.exit()
