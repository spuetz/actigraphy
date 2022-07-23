from datetime import datetime, timedelta
import pyActigraphy
import os
import re
import pandas as pd


def read_agd_files(agd_folder):

    agd_files = [os.path.join(agd_folder, file) for file in os.listdir(agd_folder) if
                 file.endswith('.agd')]

    # try to sort files by number in the name
    agd_files.sort(key=lambda name: int(re.search(r"\d+", name).group()))

    # read agd files
    raw_reader = pyActigraphy.io.read_raw(agd_folder + "/*.agd", reader_type='AGD', n_jobs=3)

    return raw_reader


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


def summary(reader):
    from pyActigraphy.metrics.metrics import _lmx as lmx

    L5_start, L5 = lmx(reader.binarized_data(4), '5H', lowest=True)
    L5_midpoint = datetime(2021, 1, 1) + timedelta(hours=2.5) + L5_start

    M10_start, M10 = lmx(reader.binarized_data(4), '10H', lowest=False)
    M10_midpoint = datetime(2021, 1, 1) + timedelta(hours=5) + M10_start

    data = {
        'subject': int(reader.name),
        'Start_time': reader.start_time,
        'Mask_fraction': reader.mask_fraction(),
        'Duration': reader.duration(),
        'ADAT': reader.ADAT(),
        'L5': L5,
        'L5 Midpoint': L5_midpoint,  # L5_midpoint.strftime("%H:%M:%S"),
        'M10': M10,
        'M10 Midpoint': M10_midpoint,  # M10_midpoint.strftime("%H:%M:%S"),
        'RA': reader.RA(),
        'IS': reader.IS(),
        'IV': reader.IV(),
        'ISm': reader.ISm(),
        'IVm': reader.IVm(),
    }
    return data


if __name__ == '__main__':

    # read program parameters
    args = read_param()

    # read agd files
    raw_reader = read_agd_files(args.agd_folder)

    # read wear times
    wear_times = read_wear_times(args.wear_times_file)
    wear_time_groups = wear_times.groupby('subject')

    # set masks by wear times
    summaries = []

    for reader in raw_reader.readers:
        print("processing subject {}.".format(int(reader.name)))
        wear_time_mask = get_wear_time_mask(reader, wear_time_groups)
        reader.mask = wear_time_mask
        reader.mask_inactivity = True
        summaries.append(summary(reader))

    data = pd.DataFrame(summaries)

    data.set_index("subject", inplace=True)
    data.index = data.index.astype(int)
    data.sort_index(inplace=True)

    from read_reports import compute_time_averages

    time_names = ['M10 Midpoint', 'L5 Midpoint']
    normal_data_averages = data.mean(numeric_only=True)
    time_data_averages = compute_time_averages(data, time_names, pivot=5)
    averages = pd.concat([normal_data_averages, time_data_averages])

    print("Averages")
    print(averages)

    # write averages to excel and csv
    averages.to_excel("actigraphy_summary_averages.xlsx")
    averages.to_csv("actigraphy_summery_averages.csv")

    # write actigraphy summary data to html
    data_html = data.to_html()
    data_html_file = open("actigraphy_summary.html", "w")
    data_html_file.write(data_html)
    data_html_file.close()

    # write actigraphy summary data to csv
    data.to_csv("actigraphy_summary.csv")

    # write actigraphy summary data to excel
    data.to_excel("actigraphy_summary.xlsx")


    #print(data)


