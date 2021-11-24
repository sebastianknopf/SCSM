# Main execution script of SCSM project.
import sys
import os

from optparse import OptionParser

# parse arguments and options to global variable
parser = OptionParser()
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="show verbose output")
parser.add_option("-d", "--data", dest="data_filename", help="report data input file location")
parser.add_option("-s", "--schedule", dest="schedule_filename", help="schedule data input file name")

(options, args) = parser.parse_args()


# definition for error output
def _error(errmsg, errcode=-1):
    print(f"error: {errmsg}")
    sys.exit(errcode)


# definition for verbose output
def _verbose(vbsmsg):
    print(f"info: {vbsmsg}")


# entry point for main execution
if __name__ == '__main__':

    # check required arguments
    if options.data_filename is None:
        _error("option -d/--data missing, see -h/--help for more information")

    if options.schedule_filename is None:
        _error("option -s/--schedules missing, see -h/--help for more information")

    # check whether input files are existing and readable
    if not os.path.isfile(options.data_filename) or not os.access(options.data_filename, os.R_OK):
        _error(f"data input file {options.data_filename} is does not exist or is not readable")

    if not os.path.isfile(options.schedule_filename) or not os.access(options.schedule_filename, os.R_OK):
        _error(f"schedule input file {options.schedule_filename} is does not exist or is not readable")

    # check whether output folder exists and is writable or at least the working dir is writable
    if not os.access("./output", os.W_OK) or not os.path.exists("./output"):
        _error("output folder is not available or not writable")

    # run SCSM optimization on planned schedules regarding existing report data

