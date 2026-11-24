"""AUDIT7: classify host functions of candidate vtable-install sites, and dump candidate host bodies."""
import sys, os
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT7\work")
from core import *
import fast

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT7\work\hosts"
os.makedirs(OUT, exist_ok=True)

CAND = {
    0x007EF954: [0x0062B767, 0x0062BC4A, 0x0062BCC4, 0x0062D7C4, 0x0062D9A4],
    0x007EFB9C: [0x0062DD16, 0x0062DFA6, 0x0062E077, 0x0062FF6D],
    0x007F00A8: [0x0064419C, 0x0064422D, 0x00644256, 0x00644804, 0x00644966],
    0x007F0188: [0x00644CF4, 0x00644E12, 0x00644E46, 0x006456A3, 0x00645956],
    0x007F6318: [0x00749434, 0x00749957, 0x007499F6, 0x0074A997],
    0x007F6548: [0x0074AE6B, 0x0074AF76, 0x0074B838, 0x0074BA36],
    0x007F5458: [0x0071DAF7, 0x0071DBDD, 0x0071DC0A, 0x0071E1F4, 0x0071E36A],
    0x007F5728: [0x007217A6, 0x00721888, 0x00721FC7],
    0x007F59B0: [0x00727FFD, 0x007280D6, 0x007281BF, 0x00728716],
    0x007F6E70: [0x0076375F, 0x007637E4, 0x00763845, 0x007638C6, 0x00763CA7, 0x00763E26],
}

BASE_CTOR = {0x5F3900, 0x5F7090, 0x410170, 0x410800, 0x5F7320, 0x4101E0, 0x5F0B80}
BASE_DTOR = {0x5F3B80, 0x5F7400, 0x4101F0, 0x5F3B50, 0x5F5230}
FREE = 0x7C8B3D


def analyze(site):
    fs = fast.func_start(site)
    b = fast.body(fs)
    end = b[-1][0]
    calls = [r[4][0] for r in b if r[1] == 'call' and r[4]]
    last = b[-1]
    res = {
        'site': site, 'start': fs, 'end': end, 'n': len(b),
        'ret': f"{last[1]} {last[2]}",
        'calls': [f"{hex(c)}" for c in calls],
        'base_ctor': [hex(c) for c in calls if c in BASE_CTOR],
        'base_dtor': [hex(c) for c in calls if c in BASE_DTOR],
        'free': [hex(c) for c in calls if c == FREE],
        'atexit': fast.atexit_sites_for(fs),
    }
    p = f"{OUT}\\host_{fs:08X}.txt"
    with open(p, 'w', encoding='utf-8') as fh:
        for a, mn, opstr, bh, imms in b:
            mark = '  <== install' if a == site else ''
            fh.write(f"{a:08X}  {bh:<24} {mn} {opstr}{mark}\n")
    res['file'] = p
    return res


if __name__ == '__main__':
    for vt, sites in CAND.items():
        print(f"\n#### vt {vt:08X}")
        seen = set()
        for s in sites:
            r = analyze(s)
            if r['start'] in seen:
                print(f"  site {s:08X}: host {r['start']:08X} (dup)")
                continue
            seen.add(r['start'])
            print(f"  site {s:08X} host {r['start']:08X}..{r['end']:08X} n={r['n']} ret={r['ret']}")
            print(f"     base_ctor={r['base_ctor']} base_dtor={r['base_dtor']} free={r['free']} atexit={[hex(x) for x in r['atexit']]}")
            print(f"     calls={r['calls'][:10]}")
