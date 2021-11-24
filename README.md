# SCSM - Statistics based Crew Scheduling Model

This project called SCSM is a statistics based model providing advices for schedule optimization of ticket inspector or security crews in public transport.

SCSM uses data about certain public transport routes, the amount of passengers controlled and number of complained passengers. All of these data are collected by the ticket inspectors normally. A second file with planned schedules and duties is in advance used in advance to distribute activities over all times and transport routes as well as possible.

## Running the Sample Script

A sample implementation using SCSM can be found in the file ```main.py```. The file is also able to run a simple demo using example data provided in ```./inputs``` directory. To run SCSM using this repo, you need at least

* a file with report data from previous duties
* a file describing planned crew schedules with at least one planned duty in future

To run he SCSM script, you only need to call

```
python main.py -d ./input/example_report_data.txt -s ./input/example_schedule_data.txt
```
in the execution shell. Call ```python main.py -h``` for help and see the next paragraph for format specifications of the input files.

## Input Data Formats

The report data input file must contain at least the columns

* date: date in format yyyyMMdd
* departure_time: time of trip start in format HH:mm:ss
* arrival_time: time of trip end in format HH:mm:ss
* num_passengers: number of passengers controlled during this trip
* num_complaints: number of complaints during this trip
* route_name: an unique route name

The planned schedules input file must contain at least the following columns:

* date: date of the schedule in format yyyyMMdd
* start_hour: start hour for first trip (includes every trip starting from hh:01)
* end_hour: end hour for last trip (includes every trip starting until hh:59)

Both files must be RFC-4158 compliant CSV files using *one header row*, using *```\n``` or ```\r\n```* as new line indicator and be separated by a *semicolon*.