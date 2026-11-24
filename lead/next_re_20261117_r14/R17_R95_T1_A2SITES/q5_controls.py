"""Q5 positive controls + the three-record deep check for Q3."""
import json, struct
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
OUT = BASE + r'\R17_R95_T1_A2SITES'
LOG = []
def P(*a):
    line = ' '.join(str(x) for x in a); LOG.append(line); print(line, flush=True)

blob = open(EXE, 'rb').read()
TEXT_RAW, TEXT_VA, TEXT_VSZ = 4096, 0x00401000, 4060045
foff = lambda va: TEXT_RAW + (va - TEXT_VA)

d = json.loads(open(BASE + r'\D41_SUBST\_audit\EVIDENCE\a2_sites.json', 'rb').read().decode('utf-8'))
calls = d['calls']; bounds = d['bounds']

# ---- Q5-1: two independent implementations of (n_keys, n_pairs, avg bytes) ----
P('=== Q5-1: two independent counts ===')
P('[impl1/json module] keys=%d pairs=%d bounds=%d' % (len(calls), sum(len(v) for v in calls.values()), len(bounds)))
raw = open(BASE + r'\D41_SUBST\_audit\EVIDENCE\a2_sites.json', 'rb').read()
P('[impl1/json module] file_bytes=%d  total_records=%d  avg_bytes=%.4f' %
  (len(raw), len(calls) + len(bounds), len(raw) / (len(calls) + len(bounds))))
# impl2: pure regex, no json parser
import re
s = raw.decode('utf-8')
head, tail = s.split('}, "bounds": ["', 1)
tail = tail[:-2]
keys2 = re.findall(r'"([0-9A-F]{8})": \[', head)
elems2 = re.findall(r'"([0-9A-F]{8})"', tail)
pairs2 = head.count('"0')
# count pair strings inside the calls half only
calls_half = head
pair_strs = re.findall(r'"(0[0-9A-F]{7})"', calls_half)
P('[impl2/regex     ] keys=%d pairs=%d bounds=%d' % (len(keys2), len(pair_strs), len(elems2)))
P('[impl2/regex     ] total_records=%d  file_bytes=%d  avg_bytes=%.4f' %
  (len(keys2) + len(elems2), len(raw), len(raw) / (len(keys2) + len(elems2))))
ok1 = len(keys2) == len(calls) and len(pair_strs) == sum(len(v) for v in calls.values()) and len(elems2) == len(bounds)
P('agree =', ok1)

P('')
P('=== Q5-2: positive controls for the return-to-origin search ===')
def site_ok(t_hex, s_hex):
    sva = int(s_hex, 16); so = foff(sva)
    if blob[so] != 0xE8:
        return False, 'opcode=%02X' % blob[so]
    rel = struct.unpack_from('<i', blob, so + 1)[0]
    calc = (sva + 5 + rel) & 0xFFFFFFFF
    return calc == int(t_hex, 16), '%08X' % calc

# PC-1: a record whose .text target is a REAL function; find it in another EVIDENCE data file
t = '00407100'
print_pairs = calls[t]
P('PC-1 record: target %s (== the first key of every callmap in this tree), sites %s' % (t, print_pairs))
P('  gamemd.exe byte test:', [site_ok(t, x) for x in print_pairs])
# cite the same pair inside another EVIDENCE file (S09_KPROVED7 flat pair list)
o5 = json.load(open(BASE + r'\S09_KPROVED7\_audit\EVIDENCE\e8_sites_audit.json', encoding='utf-8'))
hits = [tuple(p) for p in o5 if ('%08X' % p[1]) == t and ('%08X' % p[0]) in print_pairs]
P('  PC-1 found verbatim in S09_KPROVED7/_audit/EVIDENCE/e8_sites_audit.json : %d/%d pairs' % (len(hits), len(print_pairs)), hits)
# raw text search in that file
raw5 = open(BASE + r'\S09_KPROVED7\_audit\EVIDENCE\e8_sites_audit.json', 'rb').read().decode('utf-8')
P('  PC-1 raw substring "[4198410, 4223232]" present in that file:', '[4198410, 4223232]' in raw5)

# PC-2: THE HARD ONE -- a record whose "target" is NOT a real address (x86 call, rel32 has crossed
# the 32-bit wrap). This is the case where a naive "the value must appear in .text" search says NOT FOUND.
P('')
pc2 = ('C0C5A07E', '00409FF2')
ok2, calc2 = site_ok(*pc2)
P('PC-2 record (wrapped call): target %s site %s -> byte test %s (recomputed %s)' % (pc2[0], pc2[1], ok2, calc2))
# naive search: does the string appear anywhere in bounds (the .text instruction-start list)?
P('  naive in-text search: "%s" present in a2_sites["bounds"] ? %s' % (pc2[0], pc2[0] in set(bounds)))
# the site IS in bounds and IS a call site
P('  site "%s" in bounds ? %s' % (pc2[1], pc2[1] in set(bounds)))
# and the site byte is E8: show the 5 raw bytes
so = foff(int(pc2[1], 16))
P('  raw bytes @file_off %d: %s' % (so, blob[so:so+5].hex().upper()))

# record 3rd case: a target that IS a real .text function, verified independently by disasm_*.txt text
P('')
P('=== PC-3: does a disassembly EVIDENCE text corroborate one of our call records? ===')
import glob, os
files = glob.glob(BASE + r'\D41_SUBST\EVIDENCE\disasm_*.txt')
P('disasm files:', len(files))
hitfile = None
for f in files:
    txt = open(f, 'rb').read().decode('utf-8', 'replace')
    if 'call' in txt.lower() and '0x40100a' in txt.lower():
        hitfile = f; break
P('a disasm file citing a call site VA 0x40100a:', hitfile)
# direct approach: find the disasm of the containing function of site 0040100A
P('calls whose site is 0040100A: ', [k for k, v in calls.items() if '0040100A' in v])

# --- Q3 deep record trace (3 records) ---
P('')
P('=== Q3: 3 sampled records, full trace ===')
rule_keys = [list(calls.keys())[0], list(calls.keys())[len(calls)//2], list(calls.keys())[-1]]
for k in rule_keys:
    sites = calls[k]
    oks = [site_ok(k, x) for x in sites]
    P('REC target=%s  n_sites=%d  all_bytes_match=%s' % (k, len(sites), all(o[0] for o in oks)))
    P('    sites[:6]=%s' % sites[:6])
    # locate same pairs in other EVIDENCE files
    found = {}
    for name, se in [('S16_N1', set(('%08X' % int(a,16), '%08X' % int(b,16)) for a,b in
                                     [(k2, s2) for k2, v2 in json.load(open(BASE + r'\S16_N1\_audit\callmap.json', encoding='utf-8')).items() for s2 in v2])),
                     ('S09_KPROVED7', set(('%08X' % p[1], '%08X' % p[0]) for p in o5))]:
        found[name] = sum(1 for x in sites if (k, x) in se)
    P('    verbatim in other EVIDENCE:', found)

open(OUT + r'\q5_controls.out', 'w', encoding='utf-8').write('\n'.join(LOG))
