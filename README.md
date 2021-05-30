# Parse NGU save games

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


The fields queried are listed in `HEADERS`.  The graphs are controlled by the `GRAPH` dictionary

### Example graph:
![Idlinng BAE](https://i.imgur.com/MwCG3lJ.png)
