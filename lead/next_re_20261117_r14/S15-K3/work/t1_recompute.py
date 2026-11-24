#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T1: recompute S15 named(S)/proved from disk, independently.
named_L  = name non-empty and not startswith('sub_')
named_S  = named_L AND not of form Class::sub_XXXXXXXX (placeholder)
          (task phrasing: exclude 'sub_' prefix AND 'Class::sub_' form)
proved   = grade == '[已证]'
denominator = coverage(subsystem==S15) INTERSECT function_atlas.tsv
"""
import csv, re, sys

ROOT = r"D:\Project\ra2-campaign-forge"
COV  = ROOT + r"\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATL  = ROOT + r"\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"

def load_atlas():
    s = set()
    with open(ATL, 'r', encoding='utf-8-sig') as f:
        r = csv.DictReader(f, delimiter='\t')
        for row in r:
            e = (row.get('entry') or '').strip().lower()
            if e:
                s.add(e)
    return s

# Class::sub_XXXXXXXX strict form, plus broader Class::sub_ prefix detection
RE_CLASS_SUB_HEX = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*::sub_[0-9A-Fa-f]{8}$')
RE_CLASS_SUB_ANY = re.compile(r'::sub_')

def named_L(name):
    return bool(name) and not name.startswith('sub_')

def named_S_strict(name):
    return named_L(name) and not bool(RE_CLASS_SUB_HEX.match(name))

def named_S_broad(name):
    return named_L(name) and not bool(RE_CLASS_SUB_ANY.search(name))

def main():
    atlas = load_atlas()
    rows = []
    with open(COV, 'r', encoding='utf-8-sig') as f:
        r = csv.DictReader(f, delimiter='\t')
        for row in r:
            if (row.get('subsystem') or '').strip() == 'S15':
                e = (row.get('entry') or '').strip().lower()
                row['_e'] = e
                row['_in_atlas'] = e in atlas
                rows.append(row)

    s15_all = rows
    s15_atlas = [x for x in rows if x['_in_atlas']]
    outside = [x for x in rows if not x['_in_atlas']]

    n_all = len(s15_all)
    n_atlas = len(s15_atlas)

    # counts on atlas subset
    namedL = sum(1 for x in s15_atlas if named_L((x.get('name') or '').strip()))
    namedS_strict = sum(1 for x in s15_atlas if named_S_strict((x.get('name') or '').strip()))
    namedS_broad = sum(1 for x in s15_atlas if named_S_broad((x.get('name') or '').strip()))
    proved = sum(1 for x in s15_atlas if (x.get('grade') or '').strip() == '[已证]')

    # class::sub_ count strict/broad
    csub_strict = [x for x in s15_atlas if bool(RE_CLASS_SUB_HEX.match((x.get('name') or '').strip()))]
    csub_any = [x for x in s15_atlas if bool(RE_CLASS_SUB_ANY.search((x.get('name') or '').strip()))]

    print("=== T1 COUNTS (atlas denominator) ===")
    print(f"atlas total entries loaded        : {len(atlas)}")
    print(f"S15 rows in coverage (all)        : {n_all}")
    print(f"S15 rows NOT in atlas             : {len(outside)}")
    print(f"S15 ∩ atlas (denominator)         : {n_atlas}")
    print(f"named_L                           : {namedL}  ({100*namedL/n_atlas:.2f}%)")
    print(f"named_S (strict Class::sub_XXXX)  : {namedS_strict}  ({100*namedS_strict/n_atlas:.2f}%)")
    print(f"named_S (broad  ::sub_ anywhere)  : {namedS_broad}  ({100*namedS_broad/n_atlas:.2f}%)")
    print(f"Class::sub_ strict count          : {len(csub_strict)}")
    print(f"::sub_ broad count                : {len(csub_any)}")
    print(f"proved [已证]                     : {proved}  ({100*proved/n_atlas:.2f}%)")
    print(f"need for named>=90% (ceil 0.9*158): {-(-90*n_atlas//100)}  => shortfall = {-(-90*n_atlas//100) - namedS_strict}")
    print()

    print("=== rows NOT named(S) (strict) [entry | name | grade] ===")
    not_named = [x for x in s15_atlas if not named_S_strict((x.get('name') or '').strip())]
    for x in sorted(not_named, key=lambda z: z['_e']):
        print(f"{x['entry']}\t{x.get('name','')}\t{x.get('grade','')}")
    print(f"COUNT NOT named(S): {len(not_named)}")
    print()

    print("=== rows NOT named(S) (broad) [entry | name | grade] ===")
    not_named_b = [x for x in s15_atlas if not named_S_broad((x.get('name') or '').strip())]
    for x in sorted(not_named_b, key=lambda z: z['_e']):
        print(f"{x['entry']}\t{x.get('name','')}\t{x.get('grade','')}")
    print(f"COUNT NOT named(S) broad: {len(not_named_b)}")
    print()

    print("=== S15 rows outside atlas (informational) ===")
    for x in sorted(outside, key=lambda z: z['_e']):
        print(f"{x['entry']}\t{x.get('subsystem','')}\t{x.get('name','')}\t{x.get('grade','')}")

if __name__ == '__main__':
    main()
