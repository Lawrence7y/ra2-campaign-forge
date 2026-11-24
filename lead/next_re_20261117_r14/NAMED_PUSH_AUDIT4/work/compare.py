"""Compact comparison across the 16 rows."""
import json, glob, os, sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
W = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work"
rows = ['006BF810','006BF990','006BFB10','006BFC90','006BFE10','006BFF90','006C0110',
        '006C0290','006C0410','006C0590','006C0710','006C0890','006C0A10','006C0B90',
        '006C0D10','006C0E90']
print("%-9s %-9s %-5s %-9s %-34s %-9s %-9s %-9s %s" % (
    "entry","vt","slot","slot_va","rtti_name","objctor","objvt","QIcallee","codes/zeros/rets"))
for r in rows:
    d = json.load(open(os.path.join(W, "facts_%s.json" % r)))
    vt = d['vt'][0] if d['vt'] else {}
    q = d.get('qi_callee', {})
    ov = d.get('obj_vts', [{}])[0] if d.get('obj_vts') else {}
    print("%-9s %-9s %-5s %-9s %-34s %-9s %-9s %-9s %d/%d/%d" % (
        r, vt.get('vt'), vt.get('slot'), vt.get('slot_va'), vt.get('name'),
        d.get('obj_ctor'), ov.get('vt'), q.get('addr'),
        len(q.get('codes', [])), len(q.get('zero', [])), len(q.get('rets', []))))
print()
for r in rows:
    d = json.load(open(os.path.join(W, "facts_%s.json" % r)))
    q = d.get('qi_callee', {})
    print("%s  own codes=%s" % (r, [c[1] for c in d['codes']]))
    print("           own rets=%d  QI after=%s" % (len(d['rets']), d.get('qi_after', [])[:5]))
    print("           qicallee codes=%s zeros=%s rets=%d size=%s" % (
        [c[1] for c in q.get('codes', [])], [c[1] for c in q.get('zero', [])],
        len(q.get('rets', [])), q.get('size')))
    print("           objvts=%s" % d.get('obj_vts'))
    print()
