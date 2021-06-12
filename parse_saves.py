import argparse
import base64
import json
import sys
import logging
from deserialize_dot_net import Deserializer

HEADERS = {
    "playtime": "totalPlaytime/value/totalseconds",
    "exp": "stats/value/totalExp",
    "boss": "stats/value/highestBoss",
    "cumulative_gold": "stats/value/totalGold",
    "base_power": "adventure/value/attack",
    "base_toughness": "adventure/value/defense",
    "base_energy_cap": "capEnergy",
    "base_energy_power": "energyPower",
    "base_energy_bars": "energyBars",
    "base_magic_cap": "magic/value/capMagic",
    "base_magic_power": "magic/value/magicPower",
    "base_magic_bars": "magic/value/magicPerBar",
    "itopod_maxlvl": "adventure/value/highestItopodLevel",
    "itopod_end": "adventure/value/itopodEnd",
}

GRAPH = {
  'size': (20, 10),
  'graphs': [
    # Row 1
    [
      {'fields': ["exp"], 'log': True},
      {'fields': ['base_power', 'base_toughness'], 'log': True},
      {'fields': ['base_energy_cap', 'base_magic_cap'], 'log' :True},
    ],
    # Row 2
    [
      {'fields': ['cumulative_gold'], 'log': True},
      {'fields': ['boss']},
      {'fields': ['itopod_maxlvl']},
    ],
  ]
}

LOG = logging.getLogger()
if sys.version_info < (3, 7):
    # We depend on dicts being ordered which requires python 3.7
    LOG.critical("Python >= 3.7 is required")
    sys.exit(1)


def read_savegame(fname):
    """This is a complete hack"""
    LOG.info(f"Reading: {fname}")
    with open(fname, 'rb') as _fh:
        a = _fh.read()
        data = base64.b64decode(a)
        data = base64.b64decode(data[102:])
        ret = []
        des = Deserializer(data, 13+16+5+12)
        des.parse()
        ret = des.get('PlayerData')
        return ret

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("saves", metavar='SAVEFILE', nargs='+',
                        help="List of save files to parse")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--json", action="store_true",
                       help="Generate JSON output")
    group.add_argument("--csv", action="store_true",
                       help="Generate output as CSV")
    group.add_argument("--graph", action="store_true",
                       help="Generate graphs")
    parser.add_argument("--debug", action="store_true",
                        help="Generate extra debug information")
    parser.add_argument("--outfile",
                        help="save results in file")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    if args.graph:
        # graph import can be slow, so only do it if we need it
        try:
            import matplotlib
            if args.outfile:
                matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import seaborn as sns
            import pandas as pd
        except Exception:
            LOG.error("Graphing modules not found.  Install via")
            LOG.error("pip install seaborn")
            sys.exit(1)
        allowed_extensions = (".jpg", ".jpeg", ".gif", ".png", "svg")
        if args.outfile and not any(args.outfile.endswith(_x) for _x in allowed_extensions):
            LOG.error("--outfile must end in one of the allowed extensions: %s",
                      ", ".join(allowed_extensions))
            sys.exit(1)
        try:
            figure = plt.figure(figsize=GRAPH['size'])
        except Exception as _e:
            LOG.error("Displaying plot failed with error:\n    %s", _e)
            LOG.error("You still may be able to save the graph using --outfile <image.png>")
            sys.exit(1)
    jsondata = []
    csvdata = []
    graphdata = {_k: [] for _k in HEADERS}
    
    for fname in args.saves:
        obj = read_savegame(fname)
        if args.json:
            jsondata.append(obj)
            continue
        row = []
        for header, key in HEADERS.items():
            val = obj.get(key + "/value")
            if args.csv:
                row.append(str(val))
                continue
            if args.graph:
                graphdata[header].append(val)
        if args.csv:
            csvdata.append(row)
    if args.json:
        if len(args.saves) == 1:
            jsondata = jsondata[0]
        print(json.dumps(jsondata, sort_keys=True, indent=2))
    elif args.csv:
        csvdata.sort(key=lambda _x: _x[0])
        csvdata = [list(HEADERS.keys())] + csvdata
        for row in csvdata:
            print(",".join(row))
    elif args.graph:
        data = pd.DataFrame(data=graphdata)
        sns.set_theme()
        rows = len(GRAPH['graphs'])
        cols = max([len(_x) for _x in GRAPH['graphs']])
        gridspec = figure.add_gridspec(rows, cols)
        for row in range(0, rows):
            for col in range(0, len(GRAPH['graphs'][row])):
                _ax = figure.add_subplot(gridspec[row, col])
                graph = GRAPH['graphs'][row][col]
                for key in graph['fields']:
                    if key not in HEADERS:
                        LOG.error(f"Cannot plot unknown key '{key}'")
                        continue
                    label = key # if len(graph['fields']) > 1 else None
                    sns.scatterplot(data=data, x='playtime', y=key, label=label, ax=_ax)
                    if graph.get('log'):
                        _ax.set(yscale="log")
        plt.tight_layout()
        if args.outfile:
            figure.savefig(args.outfile)
        else:
            plt.show() 

if __name__ == "__main__":
    main()
