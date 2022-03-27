import os
import pandas as pd
from datetime import datetime


def date_parser(dt):
    return datetime.strptime(dt, "%d.%m.%Y %H:%M:%S")


def read_wear_times(wear_time_file):
    fields = ["Subject", "Wear Time Start", "Wear Time End"]

    with open(wear_time_file) as report:

        data = pd.read_csv(report, delimiter=',', quotechar='"', decimal=",",
                           date_parser=date_parser,
                           parse_dates=["Wear Time Start", "Wear Time End"])

        return data[fields]


if __name__ == '__main__':

    import sys
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--wear_times_file', dest="wear_times_file",
                        help='The wear time validation details file.', default="./Batchfiles_WearTimeValidationDetails.csv")
    args = parser.parse_args(sys.argv[1:])

    wear_times_file = args.wear_times_file
    if not os.path.exists(wear_times_file):
        print('wear time validation details file "{}" does not exist!'.format(wear_times_file))
        parser.print_help()
        exit()

    # read wear times
    wear_times = read_wear_times(wear_times_file)

    wear_times.rename(columns={
        "Subject": "Subject_id",
        "Wear Time Start": "Start_time",
        "Wear Time End": "Stop_time",
    }, inplace=True)

    wear_times['Remarks'] = ""
    wear_times.sort_values(by=['Subject_id'], inplace=True)
    wear_times.to_csv("sstlog.csv", index=False)
