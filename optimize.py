import json
import sys
import logging
import argparse
import re
from spectype import SpecType
from items import Items, ItemType
from stats import calc_stats, filter_items, optimize_items, calc_priority, get_stat_list
from parse_saves import read_savegame


def show_stats():
    stats = sorted(list(get_stat_list()))
    print("Available stats:")
    for stat in stats:
        print(f"\t{stat}")


def build_item(item):
    power = item['curAttack']['value']
    toughness = item['curDefense']['value']
    itemid = item['id']['value']
    itemtype = item['type']['value']['value__']['value']
    if itemid == 0:
        return None
    special = {}
    for spec in (1, 2, 3):
        val = item[f'spec{spec}Cur']['value']
        _type = item[f'spec{spec}Type']['value']['value__']['value']
        special[spec] = {
            "type": SpecType[_type].name,
            "typeid": f"{_type} - {SpecType[_type].name}",
            "value": val,
            "adjval": val / SpecType[_type].div if SpecType[_type].div else 0,
        }
    return {
        'id': itemid,
        'name': Items[itemid],
        'type': ItemType[itemtype],
        'power': power,
        'toughness': toughness,
        'special': special,
    }


def parse_items(sav):
    inventory = sav['inventory']['value']

    cube = {
        "power": inventory['cubePower']['value'],
        "toughness": inventory['cubeToughness']['value'],
    }
    items = {}
    for slot in ('head', 'chest', 'legs', 'boots', 'weapon'):
        item = inventory[slot]['value']
        items[slot] = build_item(item)
    for idx, item in enumerate(inventory['accs']['value']['_items']['value']):
        if list(item) != [None, None]:
            items[f'acc{idx + 1}'] = build_item(item)
    for idx, item in enumerate(inventory['daycare']['value']['_items']['value']):
        if list(item) != [None, None]:
            items[f'daycare{idx + 1}'] = build_item(item)
    for idx, item in enumerate(inventory['inventory']['value']['_items']['value']):
        row = idx // 12
        col = idx % 12
        if list(item) == [None, None] or item['id']['value'] == 0:
            continue
        items[f"{row},{col}"] = build_item(item)
        # items[(row, col)] = build_item(item)

    missing = False
    for pos, item in items.items():
        if item == None:
            continue
        for specpos, spec in item['special'].items():
            if spec['value'] != 0 and spec['adjval'] == 0:
                logging.critical(f"No special divisor found for {spec['type']} "
                                 f"(Item: {item['id']} - {item['name']} @ {pos}/{specpos}")
                print(f"{pos}/{specpos}: {spec['type']}")
                missing = True
    if missing:
        sys.exit(1)
    return items


def display_priority(stats, priority):
    priorities = (priority,)
    for _p in ('ngu', 'beards', 'pow_cap', 'wandoos'):
        if _p in priority:
            priorities = (_p, f'e_{_p}', f'm_{_p}')
            break
    print("  ".join([f"{_p}; {calc_priority(stats, _p)}" for _p in priorities]))


def optimize(items, lock=None, priority_list=None, num_accs=None):
    locked = []
    best_loadout = []
    best_stats = None
    count = 0

    if num_accs is None:
        num_accs = len([True for _x in items if _x.startswith('acc')])
    if priority_list is None:
        priority = [('power', num_accs)]
    else:
        priority = []
        for _p in priority_list:
            accs = num_accs
            skew = 1.0  # skew is mjultiplied by 1t term in compound optimizations
            match = re.search(r'^(\S+)(,[\d.]+)', _p)
            if match:
                accs = int(match.group(2)[1:])
                _p = _p.replace(match.group(2), '')
            match = re.search(r'^(\S+)(x[\d.]+)$', _p)
            if match:
                _p = match.group(1)
                skew = float(match.group(2)[1:])
            priority.append((_p, accs, skew))
    if lock:
        for _id in lock:
            item = next((_ for _ in items.values() if _['id'] == _id), None)
            if item:
                locked.append(item)
    # filt_items = filter_items(items, [_[0] for _ in priority])
    res = optimize_items(items.values(), locked, priority)
    return res


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", help="Sav/json file to parse")
    parser.add_argument("--stat", nargs='+', help="Stat to optimize: stat[,num_accessories]")
    parser.add_argument("--lock", nargs='+', type=int, help="enforce certain items be worn (by ID)")
    parser.add_argument("--list-stats", action='store_true', help="List available stats")
    parser.add_argument("--accessories", type=int, help="Override # of accessories")
    args = parser.parse_args()
    if args.list_stats:
        show_stats()
        sys.exit(0)
    try:
        with open(args.infile) as _fh:
            sav = json.load(_fh)
    except:
        try:
            sav = read_savegame(args.infile)
        except Exception as _e:
            logging.critical("Failed to read save_file: %s", _e)
            sys.exit(1)
    items = parse_items(sav)
    loadout = optimize(items, args.lock, args.stat, num_accs=args.accessories)
    stats = calc_stats(loadout)
    print(stats)
    for priority in args.stat:
        priority = re.sub(r'^(\S+)[,x]\d.*', r'\1', priority)
        display_priority(stats, priority)
    for i in loadout:
        print(f"        {i['id']:3d}, # {i['name']}")


# print(json.dumps(items, indent=2))
# print(json.dumps(loadout, indent=2))

main()
