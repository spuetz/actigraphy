import os
import pandas as pd
from datetime import datetime
from datetime import timedelta
from datetime import time
import re

subject_pattern = re.compile("Subject Name: (\d+)")
header_line_pattern = re.compile("In Bed Date")


def parse_header(report_file):
    subject = None
    header_lines = -1

    with open(report_file) as report:
        for i, line in enumerate(report):
            found_subject = re.findall(subject_pattern, line)
            if found_subject:
                subject = int(found_subject[0])

            found_header_line = re.findall(header_line_pattern, line)
            if found_header_line:
                header_lines = i - 1
                break

        # print("Subject {}, header lines {}".format(subject, header_lines))
    return subject, header_lines


def date_parser(date, time):
    return datetime.strptime(f"{date} {time}", "%d.%m.%Y %H:%M")


def compute_mid_point_of_sleep(row):
    row['MPOS'] = row['Onset'] + timedelta(minutes=row["Total Sleep Time (TST)"] / 2)
    return row


def read_data(report_file, header_lines):
    with open(report_file) as report:
        data = pd.read_csv(report, delimiter=',', quotechar='"', decimal=",",
                           header=header_lines, date_parser=date_parser,
                           parse_dates={'In Bed': ['In Bed Date', 'In Bed Time'],
                                        'Out Bed': ['Out Bed Date', 'Out Bed Time'],
                                        'Onset': ['Onset Date', 'Onset Time']})

        data = data.apply(compute_mid_point_of_sleep, axis=1)
        return data


def average_time_48(datetimes, pivot=14):
    times = [dt.time() for dt in datetimes]
    minutes = sum(
        (int(t.minute) + int(t.hour) * 60) if t.hour > pivot else (int(t.minute) + int(t.hour + 24) * 60) for t in
        times)
    average = minutes / len(times)
    day = 24 * 60
    average = average if average < day else average - day
    h, m = divmod(average, 60)
    return time(hour=int(h), minute=int(m), second=0)


def compute_time_averages(data):
    time_names = ['In Bed', 'Onset', 'MPOS', 'Out Bed']

    time_averages = pd.Series(dtype=float)

    for column_name in time_names:
        time_data = data[column_name]
        time_averages[column_name] = average_time_48(time_data.array)

    return time_averages


def compute_averages(data):
    normal_data_averages = data.mean(numeric_only=True)
    normal_data_averages['TBT'] = (datetime.min + timedelta(minutes=normal_data_averages['TBT'])).time()
    normal_data_averages['TST'] = (datetime.min + timedelta(minutes=normal_data_averages['TST'])).time()

    time_data_averages = compute_time_averages(data)
    averages = normal_data_averages.append(time_data_averages)
    return averages


def compute_averages_for_all_reports(reports_files):
    average_all = pd.DataFrame()  # averages over all days
    average_we = pd.DataFrame()  # averages over weekend days
    average_wd = pd.DataFrame()  # averages over weekday days

    for report_file in reports_files:
        subject, header_lines = parse_header(report_file)
        data = read_data(report_file, header_lines)

        # there should be seven entries -> seven days a week -> ignore all others
        if len(data.index) != 7:
            continue

        # rename some columns
        data.rename(columns={
            "Total Sleep Time (TST)": "TST",
            "Total Minutes in Bed": "TBT",
            "Number of Awakenings": "Awakenings",
            "Wake After Sleep Onset (WASO)": "WASO",
            "Average Awakening Length": "AAL",
            "Sleep Fragmentation Index": "SFI"
        }, inplace=True)

        # compute averages from all days
        averages = compute_averages(data)

        # compute filter for out bed in the week and not at the weekend
        weekday = data['Out Bed'].dt.weekday
        in_week = ((weekday > 1) & (weekday < 7))

        # compute averages for weekday and weekends separately
        averages_weekday = compute_averages(data[in_week])
        averages_weekend = compute_averages(data[~in_week])

        # set subject columns
        averages_weekday["Subject"] = subject
        averages_weekend["Subject"] = subject
        averages["Subject"] = subject

        # append result for this subject
        average_we = average_we.append(averages_weekend, ignore_index=True)
        average_wd = average_wd.append(averages_weekday, ignore_index=True)
        average_all = average_all.append(averages, ignore_index=True)

    # use integers for the subjects
    average_we['Subject'] = average_we['Subject'].astype(int)
    average_wd['Subject'] = average_wd['Subject'].astype(int)
    average_all['Subject'] = average_all['Subject'].astype(int)

    # set subjects as index field
    average_we.set_index("Subject", inplace=True)
    average_wd.set_index("Subject", inplace=True)
    average_all.set_index("Subject", inplace=True)

    # print results to console
    print("averages over all days")
    print(average_all)
    average_all = average_all.add_suffix(' (All)')
    average_all = average_all.add_prefix('Average ')

    average_wd = average_wd.add_suffix(' (Workdays)')
    average_wd = average_wd.add_prefix('Average ')

    average_we = average_we.add_suffix(' (Weekend)')
    average_we = average_we.add_prefix('Average ')

    average_data = average_all.join(average_wd).join(average_we).sort_index(axis=1)

    average_data.to_excel("averages.xlsx")
    print(average_data)


if __name__ == '__main__':

    import sys
    import argparse

    parser = argparse.ArgumentParser(description='TODO Description')

    parser.add_argument('-r', '--reports', dest="reports_folder",
                        help='Folder containing all report csv files. Default ist "./reports"', default="./reports")
    args = parser.parse_args(sys.argv[1:])

    reports_folder = args.reports_folder
    if not os.path.exists(reports_folder):
        print('folder "{}" does not exist!'.format(reports_folder))
        parser.print_help()
        exit()

    reports_files = [os.path.join(reports_folder, file) for file in os.listdir(reports_folder) if
                     file.endswith('.csv')]

    print("Found", len(reports_files), "report files.")

    reports_files.sort()
    compute_averages_for_all_reports(reports_files)
