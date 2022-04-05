# Parse NGU save games
There are 2 capabilities here:
 - Generate historical graphs from a set of save files
 - Generate optimal equipment lists (similar to the [Equipment Optimizer](https://gmiclotte.github.io/gear-optimizer) from a save-game file

### To run the gear optimizer
Install pymoo:

```pip install pymoo==0.4.2```
  
Run:

```python optimize.py --inf <path to .sav file> --stat <stat>[,# accs] ...```
  
I.e to optimize for drop-chance using 3 accessory slots, and gold_drops for any remaining slots, run:

```python ptimize.py --inf NGUIdle-SteamBackup.sav --stat drops,3 gold_drops```
  
The optimizer is a single-objective knapsack optimizer.  It will fill as many apparel/weapon/accessory slots with the 1st objective, and then loop on each objective until all slots are full.  So order is important in specifying the stats.
  
A full list of allowed stats can be found via:

```python optimize.py --list_stats```

### To generate CSV data:
  `python parse_saves.py --csv --outfile data.csv <path to NGU Saves>/NGUSave-Build*.txt`

### To generate graphs:
   ```
   pip install seaborn
  `python parse_saves.py --graph --outfile graph.png <path to NGU Saves>/NGUSave-Build*.txt`
   ```

   If you want the graphs displayed on the screen, ensure you have TCL installed

### To inspect the raw fields:
   `python parse_saves.py --json <save file>.txt`

The fields queried are listed in `HEADERS`.  The graphs are controlled by the `GRAPH` dictionary.

Note that only data stored inside the save-file can be visualised.  To plot calculated fields (like total-power or total-cap) you would need to do the calculations yourself based on the raw inputs.

### Example graph:
![Idlinng BAE](https://i.imgur.com/MwCG3lJ.png)
