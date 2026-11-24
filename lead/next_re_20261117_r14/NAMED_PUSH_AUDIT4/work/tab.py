import json, os, re
W = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work"
rows = ['006BF810','006BF990','006BFB10','006BFC90','006BFE10','006BFF90','006C0110',
        '006C0290','006C0410','006C0590','006C0710','006C0890','006C0A10','006C0B90',
        '006C0D10','006C0E90']
print("%-9s %-9s %-32s %-9s %-9s %-32s %-9s %s" % ("entry","fac_vt","factory_rtti","ctor","main_vt","main_rtti","slot0","codes/zeros/rets"))
for r in rows:
    d = json.load(open(os.path.join(W, "f3_%s.json" % r)))
    f = d['factory']; mv = d.get('main_vt') or {}; q = d.get('qi_callee', {})
    print("%-9s %-9s %-32s %-9s %-9s %-32s %-9s %d/%d/%d" % (
        r, f['vt'], f['name'], d.get('obj_ctor'), mv.get('vt'), mv.get('name'),
        d.get('main_slot0'), len(q.get('codes',[])), len(q.get('zeros',[])), len(q.get('rets',[]))))
print("\n--- detail: element vs main rtti match, ctor this_reg, stores ---")
for r in rows:
    d = json.load(open(os.path.join(W, "f3_%s.json" % r)))
    mv = d.get('main_vt') or {}
    ok = 'OK' if mv.get('name') == d['expected_obj_rtti'] else 'MISMATCH(%s vs %s)' % (mv.get('name'), d['expected_obj_rtti'])
    q = d.get('qi_callee', {})
    print("%s element=%-22s %s this=%s stores=%d" % (r, d['element'], ok, d.get('ctor_this_reg'), len(d['ctor_vtstores'])))
    print("     main_vt store @%s reg=%s  slot0=%s  qi_callee codes=%s zeros=%s rets=%d" % (
        mv.get('at'), mv.get('reg'), d.get('main_slot0'),
        [c.split(' ',1)[1] for c in q.get('codes',[])], [c.split(' ',1)[1] for c in q.get('zeros',[])], len(q.get('rets',[]))))
