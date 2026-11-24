"""Emit per-row fact blocks (bytes included) for report writing."""
import sys, json, os, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img
img = Img()
W = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work"
chain = json.load(open(os.path.join(W, "chain4.json")))
rows = list(chain.keys())
def ins_at(a):
    l = img.dis(a, 15); return l[0] if l else None
def b(a, n=6):
    return img.hexb(a, n).upper()

for r in rows:
    d = json.load(open(os.path.join(W, "f3_%s.json" % r)))
    q = d['qi_callee']; mv = d['main_vt']; f = d['factory']; ch = chain[r]
    qi_at = int(d['qi_call']['at'], 16)
    rel_at = int(d['rel_call']['at'], 16)
    print("### %s  %s" % (r, f['name']))
    print(" ② facvt=%s slotVa=%s slot=%d col=%s td=%s" % (f['vt'], f['slot_va'], f['slot'], f['col'], f['td']))
    print("    slotVa bytes=%s" % b(int(f['slot_va'], 16), 4))
    print(" ③ codes: %s" % [(c[0], c[1], b(int(c[0], 16), 6)) for c in d['codes']])
    print("    qi   @%08X bytes=%s" % (qi_at, b(qi_at, 2)))
    print("    qi+  " + " | ".join("%08X %s" % (x, b(x, 3)) for x in (qi_at+2, qi_at+4, qi_at+6)))
    print("    rel  @%08X bytes=%s  ctx push1@%s" % (rel_at, b(rel_at, 3),
          [x.split()[0] for x in d.get('rel_ctx', []) if x.split()[1:2] == ['6a', '01']]))
    print("    rets %s" % [(x.split()[0], x.split()[1:]) for x in d['rets']])
    print(" ④ alloc=%s ctor=%s vtstore=%s clsid=%s" % (ch['alloc'], ch['factory_ctor'], ch['vt_store'], ch['clsid']))
    print("    alloc bytes=%s  vtstore bytes=%s" % (b(int(ch['alloc'], 16), 2), b(int(ch['vt_store'], 16), 6)))
    print("    crc=%s bytes=%s" % (ch['crc'], b(int(ch['crc'], 16), 2)))
    print(" ③obj ctor=%s mainvt=%s store=%s reg=%s name=%s" % (d['obj_ctor'], mv['vt'], mv['at'], mv['reg'], mv['name']))
    print("    objslot0=%s  qi_codes=%s zero=%s rets=%s" % (
        d['main_slot0'], [c.split(' ',1)[1] for c in q['codes']],
        [c.split(' ',1)[1] for c in q['zeros']], len(q['rets'])))
    print()
