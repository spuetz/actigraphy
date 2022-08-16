
# Actigraphy Scripts

For any questions write me an email to spuetz@uos.de Cheers!

## Installation MAC OSX / Linux

Open a terminal, e.g. by using the Spot Light Search using the Apple Key in combination with the space bar key on the keyboard (<#><space>).

### Clone the repository

Hit `git`. If your system is not knowing the command, it will suggest you to install the Command Line Tools. If so, install the Command Line Tools.
After the installation, try again to use the command `git`.
The programm `git` is a version control system to version files and save the history over time.

Now use the `git` tool to clone this software. https://github.com/spuetz/actigraphy
This will "clone" the data from the remote repository to your computer.
To download or clone the data to a folder of your choice, navigate to a folder in the terminal of your choice.
With the command `ls`  you can list the current folder. Usually the terminal opens within the home folder containing the folders desktop, donwload, documents, etc.
Using the command `cd` (change directory) you can change the current directory to a folder of your choice.
Anyway, you could also clone and download the repository with the scripts to the home folder.

Follow the next lines in your terminal to clone the repository and to change the directory to the new cloned folder:
 
```
git clone https://github.com/spuetz/actigraphy.git
cd actigraphy
```

With `ls` you should see the actigraphy scripts.

### Install dependencies

try to use `pip`. Type `pip -V`. This will print out the version of pip installed on your computer. Make sure that you have python3 installed on your computer.
Upgrade pip to the newest version with the following line. This can take a while.
```
python3 -m pip install --upgrade pip
```

For our system we will need a virtual python environment. For this we now need to install the correspodning python package and follow the next steps described here.

```
pip install virtualenv
python3 -m venv env
source env/bin/activate
```

You are now in a virtual environment. With the following line you will install all requirements which are listed in the requirements.txt. Installing the requirements can take a while. Go make yourself a nice cup of coffee!

```
pip install -r requirements.txt
```

Now you are ready to run the scripts. Have fun!

### Read Reports and Compute Averages

The script computs sleep report averages for all days and for weekends and weekdays separately.

Usually the following values are computed:
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

To list the parametres and print the usage of the script, type `read_reports.py -h`. 
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