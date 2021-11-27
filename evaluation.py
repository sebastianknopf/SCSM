from scsm import StatModel
from xlsxwriter import Workbook


def _evaluation_report(scsm, output_filename):

    # calculate data quality for each route and write it into matrix
    # ignore protected access for this case
    with Workbook(output_filename) as workbook:

        # write data quality matrix
        worksheet = workbook.add_worksheet("data_quality")

        for hour in range(0, 24):
            worksheet.write(hour + 1, 0, hour)
            index = 1
            for route in scsm._routes:
                worksheet.write(0, index, route)

                if (hour, route) in scsm._data_quality_map.keys():
                    ap = scsm._data_quality_map[(hour, route)]
                    worksheet.write(hour + 1, index, ap)
                else:
                    worksheet.write(hour + 1, index, 'N/A')

                index += 1

        # write data quality matrix
        worksheet = workbook.add_worksheet("planned_hours")

        for hour in range(0, 24):
            worksheet.write(hour + 1, 0, hour)
            index = 1
            for route in scsm._routes:
                worksheet.write(0, index, route)

                if (hour, route) in scsm._scheduled_hours_map.keys():
                    ap = scsm._scheduled_hours_map[(hour, route)]
                    worksheet.write(hour + 1, index, ap)
                else:
                    worksheet.write(hour + 1, index, 'N/A')

                index += 1

        # additional passengers
        worksheet = workbook.add_worksheet("additional_passengers")

        for hour in range(0, 24):
            worksheet.write(hour + 1, 0, hour)
            index = 1
            for route in scsm._routes:
                worksheet.write(0, index, route)

                if (hour, route) in scsm._scheduled_hours_map.keys():
                    ap = int(scsm._scheduled_hours_map[(hour, route)] * scsm._route_control_performance[route] * 0.5)
                    worksheet.write(hour + 1, index, ap)
                else:
                    worksheet.write(hour + 1, index, 'N/A')

                index += 1


if __name__ == '__main__':

    scsm = StatModel("./input/example_report_data.txt")

    process_files = [
        ("./input/evaluation_1_weeks.txt", "./output/evaluation_1_weeks.xlsx"),
        ("./input/evaluation_2_weeks.txt", "./output/evaluation_2_weeks.xlsx"),
        ("./input/evaluation_3_weeks.txt", "./output/evaluation_3_weeks.xlsx"),
        ("./input/evaluation_4_weeks.txt", "./output/evaluation_4_weeks.xlsx"),
        ("./input/evaluation_8_weeks.txt", "./output/evaluation_8_weeks.xlsx")
    ]

    for ifile, ofile in process_files:
        scsm.load_schedule(ifile)
        scsm.process_schedule()

        _evaluation_report(scsm, ofile)

    # calculate disposition without monitoring the data quality
    scsm.load_schedule("./input/evaluation_8_weeks.txt")
    scsm._ignore_data_quality = True

    scsm.process_schedule(False)
    _evaluation_report(scsm, "./output/evaluation_8_weeks_without_dq.xlsx")
