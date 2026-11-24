#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S09-KPROVED8 core numbers + candidate discovery. Read-only on target and COVERAGE.
Writes only inside S09_KPROVED8/work/.
  - S09 n / named_S(R14) / proved  recomputed from coverage.tsv (atlas A-denominator).
  - exclusion set from 7 KPROVED deltas + SEMFIX_SLOTS2/SLOTS3 S09 rows.
  - candidate pool: S09 [静态推断] rows in atlas, not excluded, has2_rtti=1.
"""
import csv, os, re, json, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SKIPDATA, CS_OPT_SKIPDATA_SETUP
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

ROOT = r'D:\Project\ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
COVERAGE = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
ATLAS = os.path.join(ROOT, 'lead', 'next_re_20261112_r10', 'W130_atlas', 'function_atlas.tsv')
CLASS = os.path.join(R14, 'SURVEY_RING24', 'EVIDENCE', 'classification.tsv')
WORK = os.path.join(R14, 'S09_KPROVED8', 'work')

NAMED_SUB_RE = re.compile(r'::sub_[0-9A-Fa-f]+$')


def load_coverage():
    rows = {}
    with open(COVERAGE, encoding='utf-8') as f:
        lines = f.read().splitlines()
    # first line header comma-separated; data lines tab-separated
    for ln in lines[1:]:
        if not ln.strip():
            continue
        p = ln.split('\t')
        if len(p) < 5:
            continue
        entry = p[0].strip().upper()
        rows[entry] = dict(entry=entry, subsystem=p[1], name=p[2],
                           semantics=p[3], grade=p[4].strip())
    return rows


def load_atlas():
    ents = {}
    with open(ATLAS, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            ents[r['entry'].strip().upper()] = int(r['size'])
    return ents


def named_L(name):
    n = name.strip()
    return bool(n) and not n.startswith('sub_')


def named_S_R14(name):
    return named_L(name) and not NAMED_SUB_RE.search(name)


def load_exclusion():
    ex = {}
    deltas = []
    for i in range(1, 8):
        d = 'S09_KPROVED' if i == 1 else 'S09_KPROVED%d' % i
        deltas.append(os.path.join(R14, d, 'coverage_delta.tsv'))
    deltas += [os.path.join(R14, 'SEMFIX_SLOTS2', 'coverage_delta.tsv'),
               os.path.join(R14, 'SEMFIX_SLOTS3', 'coverage_delta.tsv')]
    for dpath in deltas:
        src = os.path.basename(os.path.dirname(dpath))
        with open(dpath, encoding='utf-8') as f:
            lines = f.read().splitlines()
        for ln in lines[1:]:
            if not ln.strip():
                continue
            p = ln.split('\t')
            e = p[0].strip().upper()
            subsystem = p[1].strip() if len(p) > 1 else ''
            # only S09 rows from SEMFIX_SLOTS2/3; all KPROVED cards are S09
            if src.startswith('SEMFIX_SLOTS'):
                if subsystem != 'S09':
                    continue
            ex.setdefault(e, []).append(src)
    # two explicitly judged invalid
    ex.setdefault('00654320', []).append('CARD_BLACKLIST')
    ex.setdefault('0069DEB0', []).append('CARD_BLACKLIST')
    return ex


def main():
    cov = load_coverage()
    atlas = load_atlas()
    # S09 rows in coverage ∩ atlas
    s09_atlas = {e: r for e, r in cov.items() if r['subsystem'] == 'S09' and e in atlas}
    n = len(s09_atlas)
    named_l = sum(1 for r in s09_atlas.values() if named_L(r['name']))
    named_s = sum(1 for r in s09_atlas.values() if named_S_R14(r['name']))
    named_st = sum(1 for r in s09_atlas.values()
                   if named_S_R14(r['name']) and not re.search(r'::v?slot\d+$', r['name']))
    proved = sum(1 for r in s09_atlas.values() if r['grade'] == '[已证]')
    proved_strict = sum(1 for r in s09_atlas.values()
                        if r['grade'] == '[已证]' and '[未证]' not in r['semantics'])
    s09_all = {e: r for e, r in cov.items() if r['subsystem'] == 'S09'}
    print('coverage total data rows:', len(cov))
    print('atlas total:', len(atlas))
    print('S09 total in coverage:', len(s09_all))
    print('S09 atlas∩coverage n:', n)
    print('S09 named_L:', named_l, '=%.2f%%' % (100.0*named_l/n))
    print('S09 named_S(R14):', named_s, '=%.2f%%' % (100.0*named_s/n))
    print('S09 named_S(strict):', named_st, '=%.2f%%' % (100.0*named_st/n))
    print('S09 proved:', proved, '=%.2f%%' % (100.0*proved/n))
    print('S09 proved_strict:', proved_strict, '=%.2f%%' % (100.0*proved_strict/n))
    ex = load_exclusion()
    print('exclusion set size:', len(ex))
    with open(os.path.join(WORK, 'exclusion_set.tsv'), 'w', encoding='utf-8') as f:
        f.write('entry\tsource\n')
        for e in sorted(ex):
            f.write('%s\t%s\n' % (e, ';'.join(ex[e])))
    # candidate rows: S09 [静态推断] in atlas, not excluded
    cand = {e: r for e, r in s09_atlas.items() if r['grade'] == '[静态推断]' and e not in ex}
    print('S09 [静态推断] in atlas, not excluded:', len(cand))
    # join classification for has2_rtti, rtti_vt, rtti_slot, body extents
    cls = {}
    with open(CLASS, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            cls[r['entry'].strip().upper()] = r
    with open(os.path.join(WORK, 'candidates_base.tsv'), 'w', encoding='utf-8') as f:
        f.write('entry\tname\tsemantics\thas2_rtti\trtti_vt\trtti_slot\trtti_classes\t'
                'has4_strict\tn_direct_out\text_lo\text_hi\tatlas_size\n')
        for e in sorted(cand):
            r = cand[e]
            c = cls.get(e, {})
            f.write('\t'.join([e, r['name'], r['semantics'][:60],
                               c.get('has2_rtti', ''), c.get('rtti_vt', ''), c.get('rtti_slot', ''),
                               c.get('rtti_classes', ''), c.get('has4_strict', ''),
                               c.get('n_direct_out', ''), c.get('ext_lo', ''), c.get('ext_hi', ''),
                               c.get('atlas_size', '')]) + '\n')
    # stats on has2_rtti
    h2 = sum(1 for e in cand if cls.get(e, {}).get('has2_rtti') == '1')
    print('candidates with has2_rtti=1:', h2)
    h2_strict = sum(1 for e in cand if cls.get(e, {}).get('has2_rtti') == '1'
                    and cls.get(e, {}).get('has4_strict') == '1')
    print('candidates with has2_rtti=1 and has4_strict=1:', h2_strict)
    # save core numbers
    core = dict(n=n, named_L=named_l, named_S_R14=named_s, named_S_strict=named_st,
                proved=proved, proved_strict=proved_strict,
                coverage_total=len(cov), atlas_total=len(atlas),
                s09_coverage_total=len(s09_all), exclusion_size=len(ex),
                cand_static_not_excl=len(cand), cand_has2=h2, cand_has2_has4=h2_strict)
    with open(os.path.join(WORK, 'core_numbers.json'), 'w', encoding='utf-8') as f:
        json.dump(core, f, indent=2)


if __name__ == '__main__':
    main()
