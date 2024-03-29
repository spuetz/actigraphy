
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

### Usage

There are two scripts. One script (read_reports.py) reads the report csv files and calculates the mean values of all values that are in the CSV file and additional values like the sleep midpoint.
The other script (actigraphy_batch.py) reads the AGD files and the sleep validatoin files and calculates values like L5 and M10 and the mean values of them. Both scripts also calculate correct averages of the times and durations.
In addition, both scripts have two modes how to find the input files, i.e. the CSV files.
Generally the parameters of the scripts can be displayed by using the flag `-h` (for help), e.g. `python3 read_reports.py -h`.

#### Correct Folder and Virtual Environment
If the terminal says that it cannot find the file (i.e. the script), then you are probably not in the correct folder. Make sure that you are in the folder with the scripts. 
With `cd` you can navigate into the folder as described above. If you have cloned the repository into the home folder (default example above), then you can change into the folder with `cd ~/actigraphy`. Otherwise you could find the folder in the finder and drag and drop the folder into the terminal after you typed `cd `.

You should also have the virtual envionemnt soured so that the script can find all dependencies. You can source the environment as described above with: `source env/bin/activate`.
Now, there should be an `(env)` at the beginning of the line in the terminal.


#### Computed Values

The script `read_reports.py` computs sleep report averages for all days and for weekends and weekdays separately.
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

The script `actigraphy_batch.py` computes the following values and its average values for each subject: 
- ADAT
- L5
- L5 Midpoint
- M10
- M10 Midpoint
- RA
- IS
- IV
- ISm
- IVm

#### Script Parameters and Usage

The script searches either in a folder for csv files (parameter `-r`), so a valid call would be e.g. `python3 read_reports.py -r data/reports/`, where after the -r the path to the folder where the reports are located is given.
In the terminal you can also get the path by dragging and dropping the folder into the terminal. It is important that the cursor in the terminal is at the place where the path should be inserted, in our example above behind the `-r`.
That means you have already typed `python3 read_reports.py -r` in the terminal and then drag and drop the folder from the Finder into the terminal.
With the `-r` parameter the sktip assumes that all report files are in the same folder, exactly the one you specify after the parameter.


With the `-o` parameter you can specify the output path and name...so where the result should be written to. 
A complete possible call of the script would be `python3 read_reports.py -r data/reports/ -o results/report_averages`.
So the result will be written to the folder `results` to the files `report_averages.xlsx`, `report_averages.csv` and `report_averages.html`.


There is also the possibility to search for report, agd and wear time validation files in the subfolders with the parameter `-s` (for search).
The script assumes that each subfolder of the folder specified with -s stands for a subject containing exactly one report.

It will use the folder name as subject name when using the search option.
A possible call would then be, for example, `python3 read_reports.py -o results/output_reports -s /search/path/`.
So it would search the subfolders in the `/search/path/` folder for report file.



#### Example usages of the `read_reports.py` script:

Using the search option (`-s`):
```
python3 read_reports.py -o results/output_reports -s /search/path/ 
```

Using the one folder option (`-r`):
```
python3 read_reports.py -o results/output_reprots -r data/reports/

```

#### Sample usage of `actigraphy_batch.py`

Using the search option (`-s`):
```
python3 actigraphy_batch.py -o results/output_acti -s /search/path/ 

```

Using the one folder option (`-r` and `-w`):
```
python3 actigraphy_batch.py -o results/output_acti -a data/agd_files/ -w data/wear_time_validation.csv
```