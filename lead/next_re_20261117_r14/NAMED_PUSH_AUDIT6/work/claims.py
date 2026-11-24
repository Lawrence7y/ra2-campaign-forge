"""Cross-check every claim address in column 4 against my measured anchors."""
import csv, io, re, json, sys
import core, idx

DELTA = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S22_B2\delta.tsv"
rows = list(csv.DictReader(io.open(DELTA, encoding='utf-8'), delimiter='\t'))
ring2 = json.load(open('rows_all.json'))
ring4 = json.load(open('ring4b.json'))

ADDR = re.compile(r'\b([0-9A-Fa-f]{8})\b')


def hexes(s):
    return [h.upper() for h in ADDR.findall(s)]


def classify(h):
    """What is at address h? short description from bytes/context."""
    v = int(h, 16)
    if core.in_text(v):
        ins = idx.dis_at(v, 1)
        return 'text:' + (ins[0] if ins else '?')
    sec = core.sec_of(v)
    if sec:
        val = core.u32(v)
        return '%s:u32=%08X' % (sec, val or 0)
    return 'outside'


for r in rows:
    e = r['entry']
    sem = r['one_line_semantics']
    print('=' * 100)
    print(e, r['name'])
    print('SEM:', sem)
    print('ADDRS in sem:', len(hexes(sem)))
    for h in hexes(sem):
        print('   %s  %s' % (h, classify(h)[:110]))
