# model script for SCSM classes and functions
import math
import random

from datetime import datetime
from datetime import timedelta
from pandas import read_csv
from pandas import errors
from xlsxwriter import Workbook
from xlsxwriter import exceptions


class StatModel:

    _df_data = None
    _df_schedules = None

    _routes = []
    _route_num_trips = dict()
    _route_complaint_rate = dict()
    _route_control_performance = dict()
    _route_scheduled_hours = dict()

    _disposition_result = dict()

    def __init__(self, data_filename=None, schedule_filename=None):
        self.load_data(data_filename)
        self.load_schedule(schedule_filename)

        random.seed()

    def load_data(self, data_filename, append=False):
        if data_filename is not None:
            try:
                # read data file and check whether it contains data
                df = read_csv(data_filename, sep=";")

                if df.shape[0] < 1:
                    raise FileEmptyError(data_filename)

                # convert column route_name to string
                df['route_name'] = df['route_name'].astype(str)

                # append corresponding trip hour to data
                df['hour'] = [int(dt[0:2]) for dt in df['departure_time']]

                # try loading routes from data
                self._routes = df['route_name'].unique()
                self._routes.sort()

                # add data to existing data frame depending on append parameter
                if append and self._df_data is not None:
                    self._df_data.append(df)
                else:
                    self._df_data = df

            except errors.EmptyDataError:
                # when the entire file is empty and contains nothing at all
                raise FileEmptyError(data_filename)

            except FileNotFoundError:
                raise FileReadError(data_filename)

    def load_schedule(self, schedule_filename, append=False):
        if schedule_filename is not None:
            try:
                # read schedule file and check whether it contains data
                df = read_csv(schedule_filename, sep=";")

                if df.shape[0] < 1:
                    raise FileEmptyError(schedule_filename)

                # add schedules to existing data frame depending on append parameter
                if append and self._df_schedules is not None:
                    self._df_schedules.append(df)
                else:
                    self._df_schedules = df

            except errors.EmptyDataError:
                # when the entire file is empty and contains nothing at all
                raise FileEmptyError(schedule_filename)

            except FileNotFoundError:
                # when the file does not exists or may not be readable
                raise FileReadError(schedule_filename)

    def set_routes(self, routes):
        if isinstance(routes, list):
            self._routes = [r.strip() for r in routes]
            self._routes.sort()
        else:
            raise DataProcessingError("parameter routes must be a list")

    def process_schedule(self, shuffle_same_priorities=True):

        # reset disposition result to empty list
        self._route_num_trips = dict()
        self._route_complaint_rate = dict()
        self._route_control_performance = dict()
        self._route_scheduled_hours = dict()

        self._disposition_result = dict()

        # calculate general data for each route
        for route in self._routes:
            selection = self._df_data[self._df_data['route_name'] == route]
            num_trips = len(selection.index)
            num_passengers = selection['num_passengers'].sum()
            num_complaints = selection['num_complaints'].sum()
            num_hours = 0

            for i in selection.index:
                start_hour, start_rest = selection['departure_time'][i].split(":", 1)
                start_time = timedelta(hours=int(start_hour)) + datetime.strptime(start_rest, "%M:%S")

                end_hour, end_rest = selection['arrival_time'][i].split(":", 1)
                end_time = timedelta(hours=int(end_hour)) + datetime.strptime(end_rest, "%M:%S")

                minutes = (end_time - start_time).total_seconds() / 60
                num_hours = num_hours + minutes / 60

            self._route_num_trips[str(route)] = num_trips
            self._route_complaint_rate[str(route)] = (num_complaints / num_passengers)
            self._route_control_performance[str(route)] = (num_passengers / num_hours)

        # calculate prioritized route for each hour in schedule entries
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
                    if (hour, selected_route) not in self._route_scheduled_hours.keys():
                        self._route_scheduled_hours[(hour, selected_route)] = 1
                    else:
                        self._route_scheduled_hours[(hour, selected_route)] += 1

                    # each hour should only be set once a day
                    if (si['date'], hour) not in self._disposition_result.keys():
                        self._disposition_result[(si['date'], hour)] = selected_route
                    else:
                        raise DataProcessingError(f"hour {hour} is planned twice on date {si['date']}")
            else:
                raise DataProcessingError("start hour and end hour must be in interval [0, 23]")

    def print_disposition_result(self):
        for date, hour in self._disposition_result:
            dtm = datetime.strptime(str(date), "%Y%m%d")
            print(f"{dtm.strftime('%d.%m.%Y')}, Hour {hour}: Route {self._disposition_result[(date, hour)]}")

    def write_disposition_result(self, output_filename):
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
        dq = self._data_quality(hour, route)

        if dq > 2:
            return 1
        else:
            cr_factor = self._route_complaint_rate[route] / max(self._route_complaint_rate.values())
            nj_factor = 1 - (self._route_num_trips[route] / len(self._df_data.index))

            return cr_factor * (nj_factor / 2)

    def _data_quality(self, hour, route):
        selection = self._df_data[(self._df_data['hour'] == hour) & (self._df_data['route_name'] == route)]
        n = selection['num_passengers'].sum()
        k = selection['num_complaints'].sum()

        # be aware of already planned hours on a route
        np = None
        if (hour, route) in self._route_scheduled_hours:
            np = self._route_scheduled_hours[(hour, route)] * self._route_control_performance[route]

        qs = [0.03, 0.06]

        if n > 500:
            return 1
        elif n < 50:
            return 3
        else:
            cl, cu = self._confidence_interval(n + (np if np is not None else 0), (k / n))
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


class FileEmptyError(_StatModelError):
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
