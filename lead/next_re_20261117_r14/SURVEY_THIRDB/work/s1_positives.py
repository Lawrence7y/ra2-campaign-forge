"""Extended positive controls: rows the project already proved as ③b (ledger/KPROVED whitelists).
Used only as external validation of the detector, NOT as pool rows."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import core as C
import b3

C.build_jt()

# (entry, expected ③b channel, source)
POS = [
    (0x0053AF40, '①', 'R14_COMMON §8.6 条3 举例 jt6'),
    (0x00702D40, '①', 'S10_KPROVED3 jt5 / SEMFIX_SLOTS2'),
    (0x00706640, '①', 'S10_KPROVED3 jt4'),
    (0x00708C30, '①', 'S10_KPROVED3 jt5'),
    (0x004D74E0, '①', 'S10_KPROVED2 jt13体'),
    (0x004D82B0, '④', 'S10_KPROVED3 循环写'),
    (0x004D5690, '④', 'S10_KPROVED3 循环写'),
    (0x004DB260, '④', 'S10_KPROVED3 循环8偏移'),
    (0x004D94B0, '②', 'S10_KPROVED3 HRESULT E_NOINTERFACE'),
    (0x00595740, '③', 'R14_COMMON §8.6 条3 举例 13ctor+2vt+0x318'),
]
print('entry      expect  verdict  cats            b1/hits                         b3(n_ctor,n_vt,size)')
ok = 0
for e, exp, src in POS:
    r = b3.classify(e)
    got = [c[-1] for c in r['cats']]   # ① ② ③ ④
    hit = exp in got
    ok += hit
    print('%08X   %s      %-7s  %-14s  %-32s %s   [%s]' % (
        e, exp, r['verdict'], ','.join(r['cats']) or '-',
        (str(r['b1'])[:32]), (r['b3']['n_ctor'], r['b3']['n_vt'], r['b3']['size'][:1]), src))
    if r['b2']: print('        b2=%s' % (r['b2'],))
    if r['b4'].get('ok'): print('        b4=%s' % (r['b4'],))
print('\n扩展阳性命中 %d/%d' % (ok, len(POS)))
