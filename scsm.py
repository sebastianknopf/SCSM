# model script for SCSM classes and functions
import math
import random
import sqlite3

from datetime import datetime
from datetime import timedelta
from pandas import read_csv
from pandas import errors
from xlsxwriter import Workbook
from xlsxwriter import exceptions


class StatModel:

    _df_schedules = None
    _sqlite3_database = None
    _ignore_data_quality = False

    _routes = []
    _route_complaint_rate = dict()
    _route_control_performance = dict()
    _route_trips_per_hour = dict()

    _data_quality_map = dict()
    _scheduled_hours_map = dict()

    _disposition_result = dict()

    def __init__(self, data_filename=None, schedule_filename=None):
        self.load_data(data_filename)
        self.load_schedule(schedule_filename)

        random.seed()

    def load_data(self, database_filename):
        if database_filename is not None:
            try:
                # read data file and check whether it contains data
                self._sqlite3_database = sqlite3.connect(database_filename)

                cursor = self._sqlite3_database.cursor()
                cursor.execute("SELECT COUNT(*) FROM report")

                result = cursor.fetchone()
                if result[0] == 0:
                    raise DatabaseEmptyError(database_filename)

                # try loading routes from data
                cursor.execute("SELECT DISTINCT route_name FROM report")
                result = cursor.fetchall()

                self._routes = []
                for r in result:
                    self._routes.append(r[0])

                self._routes.sort()
                self._routes = list(self._routes)

            except sqlite3.Error as e:
                # when the entire file is empty and contains nothing at all
                raise DatabaseEmptyError(database_filename)

            except FileNotFoundError:
                raise FileReadError(database_filename)

    def load_schedule(self, schedule_filename, append=False):
        if schedule_filename is not None:
            try:
                # read schedule file and check whether it contains data
                df = read_csv(schedule_filename, sep=";")

                if df.shape[0] < 1:
                    raise DatabaseEmptyError(schedule_filename)

                # add schedules to existing data frame depending on append parameter
                if append and self._df_schedules is not None:
                    self._df_schedules.append(df)
                else:
                    self._df_schedules = df

            except errors.EmptyDataError:
                # when the entire file is empty and contains nothing at all
                raise DatabaseEmptyError(schedule_filename)

            except FileNotFoundError:
                # when the file does not exists or may not be readable
                raise FileReadError(schedule_filename)

    def set_routes(self, routes):
        if isinstance(routes, list):
            self._routes = [str(r).strip() for r in routes]
            self._routes.sort()
        else:
            raise DataProcessingError("parameter routes must be a list")

    def create_schedule(self):
        pass

    def process_schedule(self, shuffle_same_priorities=True):

        # reset data dicts disposition result to empty list
        self._route_complaint_rate = dict()
        self._route_control_performance = dict()
        self._route_trips_per_hour = dict()

        self._data_quality_map = dict()
        self._scheduled_hours_map = dict()

        self._disposition_result = dict()

        # calculate general data for each route
        for route in self._routes:
            cursor = self._sqlite3_database.cursor()
            cursor.execute("SELECT SUM(num_passengers), SUM(num_complaints) FROM report WHERE route_name=?",
                           (route,))

            result = cursor.fetchone()

            num_passengers = result[0]
            num_complaints = result[1]
            num_trips = 0
            num_hours = 0

            cursor.execute("SELECT DISTINCT (date || trip_id) AS 'id', departure_time, arrival_time "
                           "FROM report WHERE route_name=?",
                           (route,))

            result = cursor.fetchall()
            num_trips = len(result)

            for tr in result:
                start_hour, start_rest = tr[1].split(":", 1)
                start_time = timedelta(hours=int(start_hour)) + datetime.strptime(start_rest, "%M:%S")

                end_hour, end_rest = tr[2].split(":", 1)
                end_time = timedelta(hours=int(end_hour)) + datetime.strptime(end_rest, "%M:%S")

                minutes = (end_time - start_time).total_seconds() / 60
                num_hours = num_hours + minutes / 60

            self._route_complaint_rate[str(route)] = (num_complaints / num_passengers)
            self._route_control_performance[str(route)] = (num_passengers / num_hours)
            self._route_trips_per_hour[str(route)] = (num_trips / num_hours)

        # calculate prioritized route for each hour in schedule entries // TODO: read changed data format
        for i, si in self._df_schedules.iterrows():
            start_hour = int(si['start_hour'])
            end_hour = int(si['end_hour'])

            # every hour of the schedule entry should be filled with a route
            if 0 <= start_hour <= 24 and 0 <= end_hour <= 24:
                for hour in range(start_hour, end_hour):

                    # calculate priority for each route regarding to the current hour
                    priorities = dict()

                    route_list = random.sample(self._routes, len(self._routes)) \
                        if shuffle_same_priorities else self._routes

                    for route in route_list:
                        rp = self._route_priority(hour, route)
                        priorities[route] = rp

                    # select route with highest priority to disposition result
                    selected_route = max(priorities, key=priorities.get)

                    # mark one hour as scheduled on the selected route
                    if (hour, selected_route) not in self._scheduled_hours_map.keys():
                        self._scheduled_hours_map[(hour, selected_route)] = 1
                    else:
                        self._scheduled_hours_map[(hour, selected_route)] += 1

                    # each hour should only be set once a day
                    if (si['date'], hour) not in self._disposition_result.keys():
                        self._disposition_result[(si['date'], hour)] = selected_route
                    else:
                        raise DataProcessingError(f"hour {hour} is planned twice on date {si['date']}")
            else:
                raise DataProcessingError("start hour and end hour must be in interval [0, 23]")

    def print_disposition_result(self): # TODO: remove in order to display result as screen
        for date, hour in self._disposition_result:
            dtm = datetime.strptime(str(date), "%Y%m%d")
            print(f"{dtm.strftime('%d.%m.%Y')}, Hour {hour}: Route {self._disposition_result[(date, hour)]}")

    def write_disposition_result(self, output_filename): # TODO: remove in order to display result as screen
        try:

            with Workbook(output_filename) as workbook:

                # default cell format
                hf = workbook.add_format()
                hf.set_bg_color("#23a740")
                hf.set_color("#ffffff")
                hf.set_align("center")

                cf = workbook.add_format()
                cf.set_align("center")

                cfr = workbook.add_format()
                cfr.set_bg_color("#b4d2ff")
                cfr.set_align("center")

                # prepare output file for displaying a schedule
                worksheet = workbook.add_worksheet("Dienstplan")

                # header row
                worksheet.write(0, 0, "Stunde", hf)
                for h in range(0, 24):
                    worksheet.write(h + 1, 0, h, cf)

                # write schedule data
                last_date = None
                last_index = 1

                time_route_map = dict()

                for date, hour in self._disposition_result.keys():
                    if last_date is None:
                        last_date = date

                    if last_date == date:
                        time_route_map[hour] = self._disposition_result[(date, hour)]
                    else:
                        dtm = datetime.strptime(str(last_date), '%Y%m%d')
                        worksheet.write(0, last_index, dtm.strftime('%d.%m.%Y'), hf)

                        for h in time_route_map.keys():
                            worksheet.write(h + 1, last_index, time_route_map[h], cfr)

                        last_index += 1
                        last_date = date

                        time_route_map = dict()
                        time_route_map[hour] = self._disposition_result[(date, hour)]

                # write last date
                dtm = datetime.strptime(str(last_date), '%Y%m%d')
                worksheet.write(0, last_index, dtm.strftime('%d.%m.%Y'), hf)

                for h in time_route_map.keys():
                    worksheet.write(h + 1, last_index, time_route_map[h], cfr)

                # formatting stuff
                worksheet.set_column(0, last_index, 10)

                for r in range(0, 25):
                    worksheet.set_row(r, 14)

        except exceptions.FileCreateError:
            raise FileWriteError(output_filename)

    def _route_priority(self, hour, route):
        # calculate data quality for the route in the corresponding hour
        dq = self._data_quality(hour, route) if not self._ignore_data_quality else 2
        self._data_quality_map[(hour, route)] = dq

        if dq > 2:
            return 1
        else:
            # be aware of already planned hours on a route
            np_approx = None
            if (hour, route) in self._scheduled_hours_map:
                np_approx = self._scheduled_hours_map[(hour, route)] * self._route_trips_per_hour[route] * 0.5

            # select number of trips per hour/route and per hour in general
            cursor = self._sqlite3_database.cursor()
            cursor.execute("SELECT DISTINCT (date || trip_id) AS 'id', COUNT(*) "
                           "FROM report "
                           "WHERE route_name=? AND SUBSTR(departure_time, 1, 2)=?",
                           (route, "{:02d}".format(hour)))

            result = cursor.fetchone()
            j_hr = result[1]

            cursor.execute("SELECT DISTINCT (date || trip_id) AS 'id', COUNT(*) "
                           "FROM report "
                           "WHERE SUBSTR(departure_time, 1, 2)=?",
                           ("{:02d}".format(hour),))

            result = cursor.fetchone()
            j_h = result[1]

            qc_factor = self._route_complaint_rate[route] / max(self._route_complaint_rate.values())
            nj_factor = 1 - ((j_hr + (np_approx if np_approx is not None else 0)) / j_h)

            return qc_factor * (nj_factor / 2)

    def _data_quality(self, hour, route):
        cursor = self._sqlite3_database.cursor()
        cursor.execute("SELECT SUM(num_passengers), SUM(num_complaints) "
                       "FROM report "
                       "WHERE route_name=? AND SUBSTR(departure_time, 1, 2)=?",
                       (route, "{:02d}".format(hour)))

        selection = cursor.fetchone()

        n = selection[0]
        k = selection[1]

        if n is None or k is None:
            return 3

        # be aware of already planned hours on a route
        np_approx = None
        if (hour, route) in self._scheduled_hours_map:
            np_approx = self._scheduled_hours_map[(hour, route)] * self._route_control_performance[route] * 0.5

        qs = [0.03, 0.06]

        if n + (np_approx if np_approx is not None else 0) > 500:
            return 1
        elif n + (np_approx if np_approx is not None else 0) < 50:
            return 3
        else:
            cl, cu = self._confidence_interval(n + (np_approx if np_approx is not None else 0), (k / n))
            deviation = self._interval_deviation(cl, cu)

            for level in range(0, len(qs)):
                if deviation < qs[level]:
                    return level + 1

            return 3

    def _confidence_interval(self, n, p):
        cl = p - 1.96 * math.sqrt((p * (1-p))/n)
        cu = p + 1.96 * math.sqrt((p * (1-p))/n)

        return cl, cu

    def _interval_deviation(self, lower, upper):
        return (upper - lower) / 2


class _StatModelError(Exception):
    """base error class for SCSM errors"""
    pass


class DatabaseEmptyError(_StatModelError):
    """error indicating an empty file"""

    filename = None

    def __init__(self, filename=None):
        self.filename = filename


class FileReadError(_StatModelError):
    """error indicating an file reading error"""

    filename = None

    def __init__(self, filename=None):
        self.filename = filename


class FileWriteError(_StatModelError):
    """error indicating an file writing error"""

    filename = None

    def __init__(self, filename=None):
        self.filename = filename


class DataProcessingError(_StatModelError):
    """error indicating a issue during data processing"""
    pass
