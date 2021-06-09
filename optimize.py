import json
import sys
import logging
from spectype import SpecType
from items import Items, ItemType
from stats import calc_stats, filter_items, optimize_items, calc_priority
from itertools import combinations

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
            "adjval": val  / SpecType[_type].div if SpecType[_type].div else 0,
            }
    return {
        'id': itemid,
        'name': Items[itemid],
        'type': ItemType[itemtype],
        'power': power,
        'toughness': toughness,
        'special': special,
        }


def parse_items(fname):
    with open(fname) as _fh:
        inventory = json.load(_fh)['inventory']['value']

    cube = {
        "power": inventory['cubePower']['value'],
        "toughness": inventory['cubeToughness']['value'],
        }
    items = {}
    for slot in ('head', 'chest', 'legs', 'boots', 'weapon'):
        item = inventory[slot]['value']
        items[slot] = build_item(item)
    for idx, item in enumerate(inventory['accs']['value']['_items']['value']):
        if item != [None, None]:
            items[f'acc{idx+1}'] = build_item(item)
    for idx, item in enumerate(inventory['daycare']['value']['_items']['value']):
        if item != [None, None]:
            items[f'daycare{idx+1}'] = build_item(item)
    for idx, item in enumerate(inventory['inventory']['value']['_items']['value']):
        row = idx // 12
        col = idx % 12
        if item == [None, None] or item['id']['value'] == 0:
            continue
        items[f"{row},{col}"] = build_item(item)
        #items[(row, col)] = build_item(item)

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

def optimize(items, priority=None):
    best_loadout = []
    best_stats = None
    count = 0

    num_accs = len([True for _x in items if _x.startswith('acc')])
    if priority is None:
        priority = {'power': 0.5, 'toughness': 0.5}
    filt_items = filter_items(items, priority.keys())
    res = optimize_items(filt_items, num_accs, priority.keys())
    return res

fname = sys.argv[1]
priority = sys.argv[2]
items = parse_items(fname)
loadout = optimize(items, {priority: 1})
#loadout = [items[_i]
#           for _i in ['head', 'chest', 'legs', 'boots', 'weapon'] + 
#                     [f'acc{_a}' for _a in range(1, 17) if f'acc{_a}' in items]
#           if items.get(_i)]
print(calc_stats(loadout))
print(f"{priority}: {calc_priority(calc_stats(loadout), priority)}")
for i in loadout:
    print(f"    {i['name']}")
#print(json.dumps(items, indent=2))
#print(json.dumps(loadout, indent=2))
