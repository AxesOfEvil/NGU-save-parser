# Parse NGU save games
There are 2 capabilities here:
 - Generate historical graphs from a set of save files
 - Generate optimal equipment lists (similar to the [Equipment Optimizer](https://gmiclotte.github.io/gear-optimizer) from a save-game file

## Clone & environment
You should clone the repository using git, and have Python3 installed.

## Install
There are two dependencies:
- `pymoo==0.4.2`;
- `seaborn==0.11.2` for the graph feature only, and it needs your Python distribution to have [TCL](https://docs.python.org/3/library/tkinter.html) installed to display graphs.

You can either install them individually by doing:
- `pip install pymoo==0.4.2`;
- `pip install seaborn==0.11.2`.

Or your can install them by using the `requirements.txt` file: `pip install -r requirements.txt`
## Usage
### Parse save files
To parse save files, you can use the `parse_saves.py` script:

```bash
python parse_saves.py [--help/-h] [--csv or --json or --graph] [--outfile <path to outfile>] [--debug] <path to NGU Saves/NGUSave-Build*.txt>
```

Options:
- `--help` or `-h` displays a help message.
- export option (mutually exclusive):
  - `--csv` prints the data in the console as CSV for the fields configured to be queried, one line per save file;
  - `--json` prints the raw data in the console as JSON;
  - `--graph` generate graphs from the data, note that in this case [`seaborn` must be installed, and to display them on screen TCL must be installed as well](#install);
- `--outfile` saves the exported graphs as images. It does nothing for JSON or CSV;
- `--debug` logs extra debug information.

For example:
```
python parse_saves.py --csv <path to NGU Saves>/NGUSave-Build*.txt
```

will print something like:
```csv
playtime,exp,boss,cumulative_gold,base_power,base_toughness,base_energy_cap,base_energy_power,base_energy_bars,base_magic_cap,base_magic_power,base_magic_bars,itopod_maxlvl,itopod_end
66562686.25624098,1613108143291,301,5.598561186647892e+88,150701637632.0,68668215296.0,11250000000000,753000000.0,306000000,5012501000000,467000032.0,300000000,1408,1389
```

#### Customizing the fields queried
To customize the fields queried (in the csv file & in what the graph can be configured to display), you can adjust the `HEADERS` dictionary in `parse_saves.py`. 

#### Generating graphs
To generate a relevant graph, make sure you have multiple save files, otherwise it is quite useless as only the current state of each save file can be displayed.

To customize the graphs generated you can adjust the `GRAPH` dictionary in `parse_saves.py`

To plot calculated fields (like total-power or total-cap) you would need to do the calculations yourself based on the raw inputs.

Here is an example command and the generated graph:
```
python parse_saves.py --graph --outfile graph.png <path to NGU Saves>/NGUSave-Build*.txt
```
![Idlinng BAE](https://i.imgur.com/MwCG3lJ.png)

### Run the gear optimizer
Run:

```
python optimize.py --inf <path to .sav file> --stat <stat>[,# accs] ...
```
  
For example, to optimize for drop-chance using 3 accessory slots, and gold_drops for any remaining slots, run:

```
python optimize.py --inf NGUIdle-SteamBackup.sav --stat drops,3 gold_drops
```
  
The optimizer is a single-objective knapsack optimizer.  It will fill as many apparel/weapon/accessory slots with the 1st objective, and then loop on each objective until all slots are full. So order is important in specifying the stats.
  
A full list of allowed stats can be found via:

```
python optimize.py --list-stats
```
