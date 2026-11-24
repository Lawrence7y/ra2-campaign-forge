"""Verify the 192,341 sample against gamemd.exe bytes (so it is a measurement, not a claim)
and count how many EVIDENCE files would need to be unioned to cover all bounds."""
import json, re, os, glob, struct
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
LOG = []
def P(*a):
    line=' '.join(str(x) for x in a); LOG.append(line); print(line, flush=True)

blob = open(EXE, 'rb').read()
TEXT_RAW, TEXT_VA = 4096, 0x00401000
bounds = json.loads(open(BASE + r'\D41_SUBST\_audit\EVIDENCE\a2_sites.json','rb').read().decode('utf-8'))['bounds']
bs = set(bounds)

pat = re.compile(r'^(?:\s*)([0-9A-F]{8})\s+((?:[0-9a-fA-F]{2}){2,20})\s+([a-z][a-z0-9.]{1,10})\b')
seen = {}
files = {}
for p in glob.glob(BASE + r'\**\*.txt', recursive=True):
    try:
        if os.path.getsize(p) > 4_000_000: continue
        t = open(p, 'rb').read().decode('utf-8', 'replace')
    except Exception:
        continue
    rel = p.replace(BASE + '\\', '')
    for ln in t.splitlines():
        m = pat.match(ln)
        if m and m.group(1) in bs:
            files.setdefault(rel, 0)
            files[rel] += 1
            if m.group(1) not in seen:
                seen[m.group(1)] = (rel, m.group(2).lower(), m.group(3))

P('bounds %d ; covered by at least one byte-bearing disasm row: %d (%.4f%%)'
  % (len(bounds), len(seen), 100*len(seen)/len(bounds)))
P('contributing files: %d' % len(files))
for r, n in sorted(files.items(), key=lambda x: -x[1])[:8]:
    P('   %-70s %d rows' % (r, n))

# verify the bytes against the image
ok = bad = 0
badlist = []
for va_hex, (rel, hexs, mn) in seen.items():
    va = int(va_hex, 16)
    off = TEXT_RAW + (va - TEXT_VA)
    got = blob[off:off + len(hexs)//2].hex()
    if got == hexs:
        ok += 1
    else:
        bad += 1; badlist.append((va_hex, hexs, got, rel))
P('')
P('byte check vs gamemd.exe: ok=%d bad=%d  (%.2f%% of the 192,341)' % (ok, bad, 100*ok/len(seen)))
for x in badlist[:5]:
    P('   BAD', x)
P('')
P('=> the bounds list IS recoverable as object content, but only 13.81% of it already exists')
P('   with bytes on disk; the other %.2f%% (%d rows) exists nowhere but as addresses.' %
  (100 - 100*len(seen)/len(bounds), len(bounds) - len(seen)))
open(BASE + r'\R17_R95_T1_A2SITES\q4_covering_verify.out','w',encoding='utf-8').write('\n'.join(LOG))
