from datetime import datetime, timedelta
import pyActigraphy
import os
import re
import pandas as pd
from pandas.io.sql import DatabaseError


# Print iterations progress
def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


def get_name_from_fname_pattern(fname_pattern, path):
    try:
        return re.match(fname_pattern, path).group(1)
    except:
        return None


def read_agd_files(agds, fname_pattern=None):
    from joblib import delayed, Parallel
    import glob

    agd_files = glob.glob(agds + "/*.agd") if type(agds) is str and os.path.isdir(agds) else agds

    def read_agd(fname, fname_pattern=None):
        try:
            raw_agd = pyActigraphy.io.agd.RawAGD(fname)
        except DatabaseError:
            print(f"Could not read in agd file {fname}. File is defective!")
            return None

        if fname_pattern:
            name = get_name_from_fname_pattern(fname_pattern, fname)
            raw_agd.display_name = name
        return raw_agd

    def parallel_reader(n_jobs, file_list, prefer=None, verbose=0, **kwargs):
        return Parallel(n_jobs=n_jobs, prefer=prefer, verbose=verbose)(
            delayed(read_agd)(file, **kwargs) for file in file_list
        )

    readers = parallel_reader(4, agd_files, fname_pattern=fname_pattern)
    readers = [reader for reader in readers if reader is not None]
    return pyActigraphy.io.RawReader("AGD", readers)


def get_wear_time_mask(reader, wear_time_groups):
    if wear_time_groups and reader.display_name in wear_time_groups.groups:
        wear_times = wear_time_groups.get_group(reader.display_name)
        mask = pd.Series(0, index=reader.data.index)
        for index, wear_time in wear_times.iterrows():
            mask.loc[(mask.index >= wear_time.start) & (mask.index <= wear_time.stop)] = 1

        return mask
    else:
        return None


def read_wear_times(wear_time_files, fname_pattern=None):
    fields = ["Subject", "Wear Time Start", "Wear Time End"]

    files = [wear_time_files] if type(wear_time_files) is str else wear_time_files

    all_data = pd.DataFrame()

    for file in files:

        with open(file) as report:
            data = pd.read_csv(report, delimiter=',', quotechar='"', decimal=",",
                               date_parser=lambda dt: datetime.strptime(dt, "%d.%m.%Y %H:%M:%S"),
                               parse_dates=["Wear Time Start", "Wear Time End"])

            data = data[fields]

            data.rename(columns={
                "Subject": "subject",
                "Wear Time Start": "start",
                "Wear Time End": "stop",
            }, inplace=True)

            if fname_pattern:
                data.subject = get_name_from_fname_pattern(fname_pattern, file)

            all_data = pd.concat([all_data, data], ignore_index=True)

    all_data['subject'] = all_data['subject'].astype(str)
    all_data.sort_values(by=['subject'], inplace=True)

    return all_data


def summary(reader, mask_set=False):
    from pyActigraphy.metrics.metrics import _lmx as lmx

    L5_start, L5 = lmx(reader.binarized_data(4), '5H', lowest=True)
    L5_midpoint = datetime(2021, 1, 1) + timedelta(hours=2.5) + L5_start

    M10_start, M10 = lmx(reader.binarized_data(4), '10H', lowest=False)
    M10_midpoint = datetime(2021, 1, 1) + timedelta(hours=5) + M10_start

    data = {
        'subject': reader.display_name,
        'Start_time': reader.start_time,
        'Mask_fraction': reader.mask_fraction() if mask_set else 0,
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


def compute_summary_and_averages(agds, wear_times_files=None, fname_pattern=None):
    # read agd files
    raw_reader = read_agd_files(agds, fname_pattern)

    # read wear times
    if wear_times_files:
        print("read wear times...")
        wear_times = read_wear_times(wear_times_files, fname_pattern)
        print(wear_times)
        wear_time_groups = wear_times.groupby('subject')

    # set masks by wear times
    summaries = []

    for i, reader in enumerate(raw_reader.readers):

        if reader is None:
            continue
        printProgressBar(i + 1, len(raw_reader.readers), prefix='Progress:', suffix='Complete', length=50)
        # print("processing subject {}.".format(int(reader.name)))

        wear_time_mask = get_wear_time_mask(reader, wear_time_groups) if wear_times_files else None

        if wear_time_mask is not None:
            reader.mask = wear_time_mask
            reader.mask_inactivity = True
        try:
            summaries.append(summary(reader, wear_time_mask is not None))
        except ValueError:
            print(f"Could not process subject {reader.display_name}, the agd file data incorrect!")
        i += 1

    data = pd.DataFrame(summaries)

    data.set_index("subject", inplace=True)
    try:
        data.index = data.index.astype(int)
    except TypeError:
        pass

    data.sort_index(inplace=True)

    from read_reports import compute_time_averages

    time_names = ['M10 Midpoint', 'L5 Midpoint']
    normal_data_averages = data.mean(numeric_only=True)
    time_data_averages = compute_time_averages(data, time_names, pivot=5)
    averages = pd.concat([normal_data_averages, time_data_averages])

    return data, averages


if __name__ == '__main__':

    import sys
    import argparse

    parser = argparse.ArgumentParser()

    two_options = parser.add_mutually_exclusive_group(required=True)

    two_options.add_argument('-a', '--agd-folder', dest="agd_folder", help='Folder containing all agd files',
                             default="./data/agd_files")
    parser.add_argument('-w', '--wear_times_file', dest="wear_times_file",
                        help='The wear time validation details file.')

    two_options.add_argument('-s', '--search-folder', dest="search_folder",
                             help='Folder containing sub-folders for each subject')
    parser.add_argument('--subject-filename-pattern', dest="subject_filename_pattern",
                        help='If set, the the subject name will be taken from the file name following this regex pattern')

    parser.add_argument('-o', '--reports-output', dest="reports_output", required=True,
                        help='File for storing the resulting average computations')

    args = parser.parse_args(sys.argv[1:])

    data = None
    averages = None

    if args.search_folder:
        import crawl_files

        subfolder = args.search_folder.split("/")[-1]
        subject_filename_pattern = re.compile(
        args.subject_filename_pattern if args.subject_filename_pattern else f".*/{subfolder}/(.*?)/.*")
        print(subject_filename_pattern)

        groups_map = crawl_files.search_folder(args.search_folder)

        agd_files = [item['agd_file'] for key, item in groups_map.items() if item['agd_file']]
        wear_files = [item['wear_time'] for key, item in groups_map.items() if item['wear_time']]

        #print(wear_files)

        print(f'Found {len(agd_files)} agd files in {args.search_folder}')
        agd_files.sort()
        data, averages = compute_summary_and_averages(agd_files, wear_times_files=wear_files,
                                                      fname_pattern=subject_filename_pattern)

    else:
        wrong_param = False

        if not os.path.exists(args.agd_folder):
            print(f'agd folder {args.ags_folder} does not exist!')
            wrong_param = True

        if args.wear_times_file and not os.path.exists(args.wear_times_file):
            print(f'wear time validation details file {args.wear_times_file} does not exist!')
            wrong_param = True

        if wrong_param:
            parser.print_help()
            exit()

        data, averages = compute_summary_and_averages(args.agd_folder, args.wear_times_file)

    print("Averages")
    print(averages)

    from pathlib import Path
    filepath = Path(args.reports_output)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    # write averages to excel and csv
    averages.to_excel(f"{args.reports_output}_averages.xlsx")
    averages.to_csv(f"{args.reports_output}_averages.csv")

    # write actigraphy summary data to html
    data_html = data.to_html()
    data_html_file = open(f"{args.reports_output}.html", "w")
    data_html_file.write(data_html)
    data_html_file.close()

    # write actigraphy summary data to csv
    data.to_csv(f"{args.reports_output}.csv")

    # write actigraphy summary data to excel
    data.to_excel(f"{args.reports_output}.xlsx")

    print(data)
