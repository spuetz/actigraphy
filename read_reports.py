import os

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import chardet
import pandas as pd
import datetime
import re

subject_pattern = re.compile("Subject Name: (.+)")
header_line_pattern = re.compile("In Bed Date")


def parse_header(report_file):
    subject = None
    header_lines = -1

    # print(f"Try to open {report_file}")
    with open(report_file, 'rb') as rawdata:
        result = chardet.detect(rawdata.read(100000))
    charenc = result['encoding']
    # print(charenc)

    with open(report_file, 'r', encoding=charenc) as report:

        i = 0
        for line in report:
            found_subject = re.findall(subject_pattern, line)
            if found_subject:
                subject = found_subject[0]

            found_header_line = re.findall(header_line_pattern, line)
            if found_header_line:
                header_lines = i - 1
                break
            i += 1

        # print("Subject {}, header lines {}".format(subject, header_lines))
    return subject, header_lines, charenc


def compute_mid_point_of_sleep(row):
    row['MPOS'] = row['Onset'] + pd.Timedelta(minutes=row["TST"] / 2)
    return row


def read_data(report_file, header_lines, charenc):
    date_parser = lambda date, time: pd.datetime.strptime(f"{date} {time}", "%d.%m.%Y %H:%M")

    with open(report_file, 'r', encoding=charenc) as report:
        data = pd.read_csv(report, engine='python', encoding=charenc, encoding_errors='ignore',
                           delimiter=',', quotechar='"', decimal=",",
                           header=header_lines,
                           parse_dates={'In Bed': ['In Bed Date', 'In Bed Time'],
                                        'Out Bed': ['Out Bed Date', 'Out Bed Time'],
                                        'Onset': ['Onset Date', 'Onset Time']},
                           date_parser=date_parser)

        return data


def average_time_48(datetimes, pivot=14):
    times = [dt.time() if type(dt) is datetime else dt for dt in datetimes]
    minutes = sum(
        (int(t.minute) + int(t.hour) * 60) if t.hour > pivot else (int(t.minute) + int(t.hour + 24) * 60) for t in
        times)
    average = minutes / len(times)
    day = 24 * 60
    average = average if average < day else average - day
    h, m = divmod(average, 60)
    return datetime.time(hour=int(h), minute=int(m), second=0)


def compute_time_averages(data, time_names=None, pivot=14):
    # time_names = ['In Bed', 'Onset', 'MPOS', 'Out Bed']

    from numpy import datetime64

    if time_names is None:
        time_names = []
        for column, dtype in dict(data.dtypes).items():
            print(column, ": ", dtype)
            if dtype is datetime64:
                time_names.append(column)

    time_averages = pd.Series()

    for column_name in time_names:
        time_data = data[column_name]
        time_averages[column_name] = average_time_48(time_data.array, pivot)

    print("averages", time_averages)
    return time_averages


def compute_averages(data):
    normal_data_averages = data.mean(numeric_only=True)
    normal_data_averages['TBT'] = (pd.datetime.min + pd.Timedelta(minutes=int(normal_data_averages['TBT']))).time()
    normal_data_averages['TST'] = (pd.datetime.min + pd.Timedelta(minutes=int(normal_data_averages['TST']))).time()

    # normal_data_averages['TST'] = pd.to_datetime(normal_data_averages['TST']).dt.floor('T').time()

    time_names = ['In Bed', 'Onset', 'MPOS', 'Out Bed']
    time_data_averages = compute_time_averages(data, time_names)
    averages = pd.concat([normal_data_averages, time_data_averages])

    return averages


def combine_same_days(data):
    out_bed_group = data.groupby([data['Out Bed'].dt.date])
    ret = out_bed_group.sum()
    ret['In Bed'] = out_bed_group['In Bed'].min()
    ret['Out Bed'] = out_bed_group['Out Bed'].max()
    ret['Onset'] = out_bed_group['Onset'].min()
    return ret


def compute_averages_for_all_reports(reports_files, output, subject_filename_pattern):
    average_all_list = []  # data list all days
    average_we_list = []  # data list weekend days
    average_wd_list = []  # data list weekday days
    meta_data_list = []  # data list for meta data

    for report_file in reports_files:
        subject, header_lines, charenc = parse_header(report_file)

        if subject_filename_pattern:
            try:
                pathname, extension = os.path.splitext(report_file)
                filename = pathname.split('/')[-1]
                subject = re.match(subject_filename_pattern, filename).group(1)
            except:
                pass

        #print(f"read {report_file}, subject {subject}, with encoding {charenc} and {header_lines} header lines")

        data = read_data(report_file, header_lines, charenc)

        # rename some columns
        data.rename(columns={
            "Total Sleep Time (TST)": "TST",
            "Total Minutes in Bed": "TBT",
            "Number of Awakenings": "Awakenings",
            "Wake After Sleep Onset (WASO)": "WASO",
            "Average Awakening Length": "AAL",
            "Sleep Fragmentation Index": "SFI"
        }, inplace=True)

        # save number of sleeps before combining multiple sleeps for one night.
        meta_data = pd.Series()
        meta_data["# Sleeps"] = num_sleeps = len(data.index)
        meta_data["Subject"] = subject

        data = combine_same_days(data)
        meta_data["# Nights"] = num_nights = len(data.index)

        if num_sleeps is not len(data.index):
            print(f"{subject} has more sleep periods in same nights, combined from {num_sleeps} sleeps to {num_nights} nights.")

        # compute mid point of sleep
        data = data.apply(compute_mid_point_of_sleep, axis=1)

        # compute averages from all days
        averages = compute_averages(data)

        # compute filter for out bed in the week and not at the weekend
        weekday = data['Out Bed'].dt.weekday
        in_week = (weekday < 5)  # 0 = Monday, 5 = Saturday

        # compute averages for weekday and weekends separately
        averages_weekday = compute_averages(data[in_week])
        averages_weekend = compute_averages(data[~in_week])

        # set subject columns
        averages_weekday["Subject"] = subject
        averages_weekend["Subject"] = subject
        averages["Subject"] = subject

        #print(f"Subject {subject}")

        # append result for this subject
        average_we_list.append(averages_weekend)
        average_wd_list.append(averages_weekday)
        average_all_list.append(averages)
        meta_data_list.append(meta_data)

    average_all = pd.DataFrame(average_all_list)  # averages over all days
    average_we = pd.DataFrame(average_we_list)  # averages over weekend days
    average_wd = pd.DataFrame(average_wd_list)  # averages over weekday days
    meta_data = pd.DataFrame(meta_data_list)  # averages over weekday days

    # set subjects as index field
    average_we.set_index("Subject", inplace=True)
    average_wd.set_index("Subject", inplace=True)
    average_all.set_index("Subject", inplace=True)
    meta_data.set_index("Subject", inplace=True)


    # print results to console
    print("averages over all days")
    print(average_all)
    print(list(average_all))

    average_all = average_all.add_suffix(' (All)')
    average_all = average_all.add_prefix('Average ')

    average_wd = average_wd.add_suffix(' (Workdays)')
    average_wd = average_wd.add_prefix('Average ')

    average_we = average_we.add_suffix(' (Weekend)')
    average_we = average_we.add_prefix('Average ')

    average_data = meta_data.join(average_all).join(average_wd).join(average_we).sort_index(axis=1)

    from pathlib import Path
    filepath = Path(args.reports_output)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    average_data.to_excel(f"{args.reports_output}.xlsx")
    average_data.to_csv(f"{args.reports_output}.csv")

    # write data to html
    data_html = average_data.to_html()
    data_html_file = open(f"{args.reports_output}.html", "w")
    data_html_file.write(data_html)
    data_html_file.close()

    print(average_data)


if __name__ == '__main__':

    import sys
    import argparse

    parser = argparse.ArgumentParser(description='TODO Description')

    parser_group = parser.add_mutually_exclusive_group(required=True)

    parser_group.add_argument('-r', '--reports', dest="reports_folder",
                        help='Folder containing all report csv files. Default ist "data/reports"', default="data/reports")
    parser_group.add_argument('-s', '--search-folder', dest="search_folder", help='Folder containing sub-folders for each subject')

    parser.add_argument('-o', '--reports-output', dest="reports_output", required=True,
                        help='File for storing the resulting average computation of all reports')
    parser.add_argument('--subject-filename-pattern', dest="subject_filename_pattern", default="(.*)-sleep-report*",
                        help='If set, the the subject name will be taken from the file name following this regex pattern')

    args = parser.parse_args(sys.argv[1:])

    subject_filename_pattern = re.compile(args.subject_filename_pattern) if args.subject_filename_pattern else None

    if args.search_folder:
        import crawl_files
        groups_map = crawl_files.search_folder(args.search_folder)

        reports_files = [item['sleep_report'] for key, item in groups_map.items() if item['sleep_report']]
        print(f'Found {len(reports_files)} report files in {args.search_folder}')
        reports_files.sort()
        compute_averages_for_all_reports(reports_files, args.reports_output, subject_filename_pattern)

    elif not os.path.exists(args.reports_folder):
        print(f' reports folder {args.reports_folder} does not exist!')
        parser.print_help()
        exit()

    else:
        reports_files = [os.path.join(args.reports_folder, file) for file in os.listdir(args.reports_folder) if file.endswith('.csv')]
        print(f'Found {len(reports_files)} report files in {args.reports_folder}')
        reports_files.sort()
        compute_averages_for_all_reports(reports_files, args.reports_output, None)
