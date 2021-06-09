"""Calculate stats of a specific loadout"""
import sys
import logging
import math
from dataclasses import dataclass
from optimizer import run_optimizer
import numpy as np

@dataclass
class Stats:
    power: int = 0
    toughness: int = 0
    ecap: float = 100
    epow: float = 100
    ebars: float = 100
    mcap: float = 100
    mpow: float = 100
    mbars: float = 100
    ngu: float = 100
    respawn: float = 100
    drops: float = 100
    gold_drops: float = 100
    seeds: float = 100
    yggdrasil: float = 100
    beards: float = 100
    adv_trn: float = 100
    augs: float = 100
    ap: float = 100
    exp: float = 100
    wandoos: float = 100
    cooldown: float = 100
    #quest: float = 0
    #cooking: float = 0

def func_ABC_ADE(L, x):
    return ((1 + np.sum(L[0][x])) * 
            ((1 + np.sum(L[1][x])) * (1 + np.sum(L[2][x])) + (1 + np.sum(L[3][x])) * (1 + np.sum(L[4][x]))))

def func_ABsqrtC_ADsqrtE(L, x):
    term1 = (1 + np.sum(L[1][x])) * math.sqrt(1 + np.sum(L[2][x]))
    term2 = (1 + np.sum(L[3][x])) * math.sqrt(1 + np.sum(L[4][x]))
    return (1 + np.sum(L[0][x])) * (term1 + term2)

def func_ABC(L, x):
    return (1 + np.sum(L[0][x])) *  ((1 + np.sum(L[1][x])) * (1 + np.sum(L[2][x])))

def func_ABsqrtC(L, x):
    return (1 + np.sum(L[0][x])) *  ((1 + np.sum(L[1][x])) * math.sqrt(1 + np.sum(L[2][x])))

def func_AB(L, x):
    return ((1 + np.sum(L[0][x])) * (1 + np.sum(L[1][x])))

def func_AB_CD(L, x):
    return (1 + np.sum(L[0][x])) * (1 + np.sum(L[1][x])) + (1 + np.sum(L[2][x])) * (1 + np.sum(L[3][x]))

def func_AB_AC(L, x):
    return (1 + np.sum(L[0][x])) * ((1 + np.sum(L[1][x])) + (1 + np.sum(L[2][x])))

def func_A(L, x):
    return 1 + np.sum(L[0][x])

def func_negA(L, x):
    return -1 * (1 + np.sum(L[0][x]))

STAT_MAP = {
    'ngu': {
        'stats': ['ngu', 'epow', 'ecap', 'mpow', 'mcap'],
        'func': func_ABC_ADE,
        },
    'e_ngu': {
        'stats': ['ngu', 'epow', 'ecap'],
        'func': func_ABC,
        },
    'm_ngu': {
        'stats': ['ngu', 'mpow', 'mcap'],
        'func': func_ABC,
        },
    'pow_cap': {
        'stats': ['epow', 'ecap', 'mpow', 'mcap'],
        'func': func_AB_CD,
        },
    'e_pow_cap': {
        'stats': ['epow', 'ecap'],
        'func': func_AB,
        },
    'm_pow_cap': {
        'stats': ['mpow', 'mcap'],
        'func': func_AB,
        },
    'beards': {
        'stats': ['beards', 'ebars', 'epow', 'mbars', 'mpow'],
        'func': func_ABsqrtC_ADsqrtE,
        },
    'e_beards': {
        'stats': ['beards', 'ebars', 'epow'],
        'func': func_ABsqrtC,
        },
    'm_beards': {
        'stats': ['beards', 'mbars', 'mpow'],
        'func': func_ABsqrtC,
        },
    'wandoos': {
        'stats': ['wandoos', 'ecap', 'mcap'],
        'func': func_AB_AC,
        },
    'e_wandoos': {
        'stats': ['wandoos', 'ecap'],
        'func': func_AB,
        },
    'e_wandoos': {
        'stats': ['wandoos', 'mcap'],
        'func': func_AB,
        },
    'adv_trn': {
        'stats': ['adv_trn', 'ecap', 'epow'],
        'func': func_ABsqrtC,
        },
    'augs': {
        'stats': ['augs', 'epow', 'ecap'],
        'func': func_ABC,
        },
    'respawn': {
        'stats': ['respawn'],
        'func': func_negA,
        },
    'cooldown': {
        'stats': ['cooldown'],
        'func': func_negA,
        },
    }

def expand_stypes(stypes):
    if not stypes:
        stypes = ['power', 'toughness']
    elif isinstance(stypes, str):
        stypes = [stypes]
    keys = {}
    for stype in stypes:
        expanded_stypes = STAT_MAP[stype]['stats'] if stype in STAT_MAP else [stype]
        for _t in expanded_stypes:
            keys[_t] = 1
    return list(keys.keys())

def filter_items(items, stypes=None):
    filtered = []
    stypes = expand_stypes(stypes)
    for stype in stypes:
        if not hasattr(Stats, stype):
            logging.error(f"{stype} is not a valid filter type")
            sys.exit(1)
    for item in items.values():
        stats = calc_stats(item)
        for stype in stypes:
            val = getattr(stats, stype)
            if stype in ('power', 'toughness') and val:
                filtered.append(item)
                break
            elif val != 100:
                filtered.append(item)
                break
    return filtered

def calc_stats(loadout):
    stats = Stats()
    if not isinstance(loadout, (list, tuple)):
        loadout = [loadout]
    for item in loadout:
        stats.power += item['power']
        stats.toughness += item['toughness']
        for spec in item['special'].values():
            stype = spec['type']
            adjval = spec['adjval']
            if stype == 'None':
                continue
            if "AllPower" in stype:
                stats.epow += adjval
                stats.mpow += adjval
            elif 'EnergyPower' in stype:
                stats.epow += adjval
            elif 'MagicPower' in stype:
                stats.mpow += adjval
            elif "AllCap" in stype:
                stats.ecap += adjval
                stats.mcap += adjval
            elif 'EnergyCap' in stype:
                stats.ecap += adjval
            elif 'MagicCap' in stype:
                stats.mcap += adjval
            elif "AllPerBar" in stype:
                stats.ebars+= adjval
                stats.mbars += adjval
            elif 'EnergyPerBar' in stype:
                stats.ebars += adjval
            elif 'MagicPerBar' in stype:
                stats.mbars += adjval
            elif 'NGU' in stype:
                stats.ngu += adjval
            elif 'Looting' in stype:
                stats.drops += adjval
            elif 'Seeds' in stype:
                stats.seeds += adjval
            elif 'Yggdrasil' in stype:
                stats.yggdrasil += adjval
            elif 'Augs' in stype:
                stats.augs += adjval
            elif 'AP' in stype:
                stats.ap += adjval
            elif 'EXP' in stype:
                stats.exp += adjval
            elif 'Wandoos' in stype:
                stats.wandoos += adjval
            elif 'Beards' in stype:
                stats.beards += adjval
            elif 'Respawn' in stype:
                stats.respawn -= adjval
            elif 'AdvTraining' in stype:
                stats.adv_trn += adjval
            elif 'Cooldown' in stype:
                stats.cooldown -= adjval
            elif 'GoldDrop' in stype:
                stats.gold_drops += adjval
            #QuestDrop
            #DaycareSpeed
            #Blood
            #Res3Power
            #Res3Cap
            #Res3Bars
            #Cooking
            #HackSpeed
            #WishSpeed
            #GoldRNG
            #EnergySpeed
            #MagicSpeed
            else:
                logging.critical(f"Can't handle item type {stype}")
                sys.exit(1)
    return stats

def calc_priority(stats, priority):
    # beards: bars + sqrt(power)
    # wandoos: cap
    # advtrn: cap + sqrt(power)
    # ngus: cap + power
    # time_machine: cap + power
    # augs: cap + power
    _p = priority
    if _p == 'augs':
        return stats.augs * (stats.epow / 100) * (stats.ecap / 100)
    elif _p == 'ngu':
        e_val = (stats.epow / 100) * (stats.ecap / 100)
        m_val = (stats.mpow / 100) * (stats.mcap / 100)
        return stats.ngu * (e_val + m_val) / 2
    elif _p == 'e_ngu':
        return stats.ngu * (stats.epow / 100) * (stats.ecap / 100)
    elif _p == 'm_ngu':
        return stats.ngu * (stats.mpow / 100) * (stats.mcap / 100)
    elif _p == 'pow_cap':
        e_val = (stats.epow) * (stats.ecap / 100)
        m_val = (stats.mpow) * (stats.mcap / 100)
        return (e_val + m_val) / 2
    elif _p == 'e_pow_cap':
        return stats.epow * (stats.ecap / 100)
    elif _p == 'm_pow_cap':
        return stats.mpow * (stats.mcap / 100)
    elif _p == 'beards':
        e_val = (stats.ebars / 100) * math.sqrt(stats.epow / 100)
        m_val = (stats.mpow / 100) * math.sqrt(stats.mpow / 100)
        return stats.beards * (e_val + m_val) / 2
    elif _p == 'e_beards':
        return stats.beards * (stats.ebars / 100) * math.sqrt(stats.epow / 100)
    elif _p == 'm_beards':
        return stats.beards * (stats.mbars / 100) * math.sqrt(stats.mpow / 100)
    elif _p == 'wandoos':
        return stats.wandoos / 100 * (stats.ecap + stats.mcap) / 2
    elif _p == 'e_wandoos':
        return stats.wandoos / 100 * stats.ecap
    elif _p == 'm_wandoos':
        return stats.wandoos / 100 * stats.mcap
    elif _p == 'adv_trn':
        return stats.adv_trn * math.sqrt(stats.epow / 100) * stats.ecap / 100
    elif _p == 'respawn' or _p == 'cooldown':
        return stats.respawn if _p == 'respawn' else stats.cooldown
    else:
        return getattr(stats, _p)

def compare_stats(ref_stats, stats, priorities):
    for _p in priorities:
        val = calc_priority(stats, _p)
        ref_val = calc_priority(ref_stats, _p)
        if _p == 'respawn' or _p == 'cooldown':
            if val < ref_val:
                return True
            if val > ref_val:
                return False
            continue
        if val > ref_val:
            return True
        if val < ref_val:
            return False
    return False

def optimize_items(items, num_accs, priority):
    def items_by_type(items, itype):
        return [_ for _ in items if _['type'] == itype]

    def group_items(items, allowed, var_items, item_groups):
        if len(items) > allowed:
            item_groups.append((len(items), allowed))
            #var_items.extend(random.sample(items, k=len(items)))
            var_items.extend(items)
        elif len(items) == allowed:
            new_items = items + var_items
            var_items.clear()
            var_items.extend(new_items)
            return len(items)
        return 0

    head_items = items_by_type(items, "Head") 
    chest_items = items_by_type(items, "Chest") 
    legs_items = items_by_type(items, "Legs")
    boots_items = items_by_type(items, "Boots") 
    weapon_items = items_by_type(items, "Weapon") 
    acc_items = items_by_type(items, "Accessory")
    if False:
        logging.warning(f"head: {len(head_items)}")
        logging.warning(f"chest: {len(chest_items)}")
        logging.warning(f"legs: {len(legs_items)}")
        logging.warning(f"boots: {len(boots_items)}")
        logging.warning(f"accs ({num_accs}): {len(acc_items)}")
    items = []
    item_groups = []
    offset = 0
    offset += group_items(head_items, 1, items, item_groups)
    offset += group_items(chest_items, 1, items, item_groups)
    offset += group_items(legs_items, 1, items, item_groups)
    offset += group_items(boots_items, 1, items, item_groups)
    offset += group_items(weapon_items, 1, items, item_groups)
    offset += group_items(acc_items, num_accs, items, item_groups)

    if offset == len(items):
        # No optimization needed
        return items

    stypes = expand_stypes(priority)
    stats = np.empty([len(stypes), len(items)])
    for _c, item in enumerate(items):
       stat = calc_stats(item)
       for _r, _s in enumerate(stypes):
           if _s in ('toughness', 'power'):
               stats[_r, _c] = getattr(stat, _s)
           else:
               stats[_r, _c] = getattr(stat, _s) / 100.0 - 1.0

    func_priority = list(priority)[0]
    if func_priority in STAT_MAP:
        func = STAT_MAP[list(priority)[0]]['func']
    else:
        func = func_A
    indices, res = run_optimizer(stats, offset, item_groups, func)
    loadout = [items[_] for _ in indices]
    # print(calc_priority(calc_stats(loadout), 'ngu'))
    return loadout

