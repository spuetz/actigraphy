
# Actigraphy Scripts


### Read Reports and Compute Averages

The script computs sleep report averages for all days and for weekends and weekdays separately.

Usually the following values are:
 - \# Nights (Numbers of Nights)
 - \# Sleeps (Number of Sleeps)
 - Latency
 - Total Counts
 - Efficiency
 - TBT (Total Bed Time)
 - TST (Total Sleep Time)
 - WASO (Wake After Sleep Onset)
 - Awakenings (Number of Awakeings)
 - AAL (Average Awakening Length)
 - Movement Index
 - Fragmentation Index
 - SFI (Sleep Fragmentation Index)
 - In Bed (In Bed Time)
 - Onset (Onset Time)
 - MPOS (Mid Point Of Sleep Time)
 - Out Bed (Out Bed Time)

For the parametres type `read_reports.py -h`. 
The script searches either in a folder for csv files (-r parameter).
The script assumes that all CSV files in the folder are sleep reports, if this is not the case, the script crashes.
There is also the possibility to search for report files in subfolders with the search parameter (-s).
The script assumes that each subfolder of the folder specified with -s is for a subject containing exactly one report.

Example usages of the `read_reports.py` script:

```
python3 read_reports.py -r data/reports/ -o output_test1.xlsx

python3 read_reports.py -o output_test2.xlsx -s /search/path/to/folder/with/sub/folders/ 

python3 read_reports.py -o output_test3.xlsx -s /search/path/to/folder/with/sub/folders/ --subject-filename-pattern "(.*)-sleep-report*"

```

Sample usage of "actigraphy_batch.py"

```
python3 actigraphy_batch.py -s /search/path/to/folder/with/subfolders-xyz/ --subject-filename-pattern ".*/subfolders-xyz/(.*?)/.*"

python3 actigraphy_batch.py -a data/agd_files/ -w data/wear_time_validation.csv

```