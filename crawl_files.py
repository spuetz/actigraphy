import os
import glob
import json


def search_file(wildcard):
    file_list = glob.glob(wildcard)
    file = file_list[0] if len(file_list) > 0 else None
    if not file:
        print(wildcard)
    return file


def search_folder(folder,
                  agd_search_pattern='/*.agd',
                  reports_search_pattern='/*sleep-report.csv',
                  wear_times_search_pattern='/*/*WearTimeValidationDetails.csv'):
    items = os.listdir(folder)
    group_map = {}

    for item in items:
        subfolder = folder + "/" + item
        if os.path.isdir(subfolder):
            agd_file = search_file(subfolder + agd_search_pattern)
            sleep_report = search_file(subfolder + reports_search_pattern)
            wear_times = search_file(subfolder + wear_times_search_pattern)

            group_map[item] = {'agd_file': agd_file,
                               'sleep_report': sleep_report,
                               'wear_time': wear_times}

            if agd_file is None:
                print("agd file is None for", item)

            if sleep_report is None:
                print("sleep report is None for", item)

            if wear_times is None:
                print("wear times file is None for", item)

    return group_map


if __name__ == '__main__':

    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='Iterates over sub-folders of the specified folder to search for agd, sleep-report, and war time '
                    'validation files.')

    parser.add_argument('-s', '--search-folder', dest="search_folder", required=True,
                        help='Folder containing sub-folders for each subject')

    args = parser.parse_args(sys.argv[1:])

    group_map = search_folder(args.search_folder)
    print(json.dumps(group_map, sort_keys=True, indent=4))
