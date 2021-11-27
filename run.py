import sys

from optparse import OptionParser
from scsm import StatModel
from scsm import FileReadError
from scsm import FileWriteError
from scsm import FileEmptyError
from scsm import DataProcessingError

# parse arguments and options to global variable
parser = OptionParser()
parser.add_option("-d", "--data", dest="data_filename", help="report data input file location")
parser.add_option("-s", "--schedule", dest="schedule_filename", help="schedule data input file name")
parser.add_option("-o", "--output", dest="output_filename", help="output XSLX file name")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="[optional] display verbose result")
parser.add_option("-r", "--routes", dest="routes", help="[optional] routes to use within the model separated by a comma")

(options, args) = parser.parse_args()


# definition for error output
def _error(errmsg, errcode=-1):
    print(f"error: {errmsg}")
    sys.exit(errcode)


# entry point for main execution
if __name__ == '__main__':

    # check required arguments
    if options.data_filename is None:
        _error("option -d/--data missing, see -h/--help for more information")

    if options.schedule_filename is None:
        _error("option -s/--schedules missing, see -h/--help for more information")

    if options.output_filename is None:
        _error("option -o/--output missing, see -h/--help for more information")

    # run SCSM optimization on planned schedules regarding existing report data
    try:
        scsm = StatModel(options.data_filename, options.schedule_filename)

        if options.routes is not None:
            scsm.set_routes(options.routes.split(","))

        scsm.process_schedule()

        if options.verbose:
            scsm.print_disposition_result()

        scsm.write_disposition_result(options.output_filename)

    except FileReadError as e:
        _error(f"input file {e.filename} may not be present or readable")

    except FileEmptyError as e:
        _error(f"input file {e.filename} does not contain any records")

    except FileWriteError as e:
        _error(f"output file {e.filename} may be opened in another application or not writable")

    except DataProcessingError as e:
        _error(str(e))
