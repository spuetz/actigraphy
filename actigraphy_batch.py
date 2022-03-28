import math
from datetime import datetime
from datetime import timedelta

import pyActigraphy
import plotly.graph_objects as go
import os
import re
import numpy as np
import pandas as pd
from pyActigraphy.analysis import FLM
from pyActigraphy.analysis import Cosinor


def read_agd_files(agd_folder, wear_times):

    agd_files = [os.path.join(agd_folder, file) for file in os.listdir(agd_folder) if
                 file.endswith('.agd')]

    # try to sort files by number in the name
    agd_files.sort(key=lambda name: int(re.search(r"\d+", name).group()))

    # read agd files
    raw_reader = pyActigraphy.io.read_raw(agd_folder + "/*.agd", reader_type='AGD', n_jobs=3)

    wear_time_groups = wear_times.groupby('subject')

    for reader in raw_reader.readers:
        wear_time_mask = get_wear_time_mask(reader, wear_time_groups)
        reader.mask = wear_time_mask


def get_wear_time_mask(reader, wear_time_groups):
    wear_times = wear_time_groups.get_group(int(reader.name))
    mask = pd.Series(0, index=reader.data.index)
    for index, wear_time in wear_times.iterrows():
        mask.loc[(mask.index >= wear_time.start) & (mask.index <= wear_time.stop)] = 1

    return mask


def read_wear_times(wear_time_file):
    fields = ["Subject", "Wear Time Start", "Wear Time End"]

    with open(wear_time_file) as report:

        data = pd.read_csv(report, delimiter=',', quotechar='"', decimal=",",
                           date_parser=lambda dt: datetime.strptime(dt, "%d.%m.%Y %H:%M:%S"),
                           parse_dates=["Wear Time Start", "Wear Time End"])

        data = data[fields]

        data.rename(columns={
            "Subject": "subject",
            "Wear Time Start": "start",
            "Wear Time End": "stop",
        }, inplace=True)

        data.subject = data.subject.astype(int)
        data.sort_values(by=['subject'], inplace=True)

        return data


def read_param():
    import sys
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('-a', '--agd-folder', dest="agd_folder", help='Folder containing all agd files',
                        default="./data/agd_files")
    parser.add_argument('-w', '--wear_times_file', dest="wear_times_file",
                        help='The wear time validation details file.',
                        default="./data/wear_time_validation.csv")

    args = parser.parse_args(sys.argv[1:])

    wrong_param = False
    if not os.path.exists(args.agd_folder):
        print('agd folder "{}" does not exist!'.format(args.agd_folder))
        wrong_param = True

    if not os.path.exists(args.wear_times_file):
        print('wear time validation details file "{}" does not exist!'.format(args.wear_times_file))
        wrong_param = True

    if wrong_param:
        parser.print_help()
        exit()

    return args


if __name__ == '__main__':

    # read program parameters
    args = read_param()

    # read wear times
    wear_times = read_wear_times(args.wear_times_file)

    read_agd_files(args.agd_folder, wear_times)
