"""Join exec claims (delta.tsv) with my measurements -> per-row check table."""
import sys, json, os, re
W = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work"
B = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S22_B1"
rows = []
for line in open(os.path.join(B, "delta.tsv"), encoding='utf-8').read().splitlines()[1:]:
    f = line.split('\t')
    rows.append(dict(entry=f[0], sub=f[1], name=f[2], sem=f[3], grade=f[4], ev=f[5]))

def g(pat, s, grp=1):
    m = re.search(pat, s)
    return m.group(grp) if m else None

chain = json.load(open(os.path.join(W, "chain4.json")))
out = []
for r in rows:
    d = json.load(open(os.path.join(W, "f3_%s.json" % r['entry'])))
    s = r['sem']
    e = {}
    e['qi_at'] = g(r'主站点 @([0-9A-F]{8})', s)
    e['qi_callee'] = g(r'slot0=QueryInterface ([0-9A-F]{8})', s)
    e['obj_vt'] = g(r'主 vt ([0-9A-F]{8})', s)
    e['fac_vt'] = g(r'vt ([0-9A-F]{8}) \+0xC', s)
    e['slot_va'] = g(r'槽 ([0-9A-F]{8})\(', s)
    e['col'] = g(r'RTTI COL=([0-9A-F]{8})', s)
    e['td'] = g(r'TD=([0-9A-F]{8})', s)
    e['cls_name'] = g(r'名=([^，]+)', s)
    e['alloc'] = g(r'工厂实例\(([0-9A-F]{8})\)', s)
    e['ctor'] = g(r'ctor ([0-9A-F]{8})', s)
    e['clsid'] = g(r'CLSID ([0-9A-F]{8}|None)', s)
    e['host'] = g(r'宿主 ([0-9A-F]{8})', s)
    e['rel_at'] = g(r'失败路 @([0-9A-F]{8})', s)
    m = {}
    m['fac_vt'] = d['factory']['vt']
    m['slot_va'] = d['factory']['slot_va']
    m['fac_slot'] = d['factory']['slot']
    m['col'] = d['factory']['col']
    m['td'] = d['factory']['td']
    m['name'] = d['factory']['name']
    m['qi_at'] = d.get('qi_call', {}).get('at')
    m['qi_at_bytes'] = d.get('qi_call', {}).get('bytes')
    m['rel_at'] = d.get('rel_call', {}).get('at')
    m['rel_bytes'] = d.get('rel_call', {}).get('bytes')
    m['rel_ctx'] = d.get('rel_ctx', [])
    m['obj_vt'] = (d.get('main_vt') or {}).get('vt')
    m['obj_vt_name'] = (d.get('main_vt') or {}).get('name')
    m['obj_vt_store'] = (d.get('main_vt') or {}).get('at')
    m['obj_vt_reg'] = (d.get('main_vt') or {}).get('reg')
    m['qi_callee'] = d.get('main_slot0')
    m['qi_codes'] = [c.split(' ', 1)[1] for c in d.get('qi_callee', {}).get('codes', [])]
    m['qi_rets'] = len(d.get('qi_callee', {}).get('rets', []))
    m['codes'] = [c[1] for c in d['codes']]
    m['nrets'] = len(d['rets'])
    ch = chain[r['entry']]
    m['alloc'] = ch['alloc']; m['ctor'] = ch['factory_ctor']
    m['clsid'] = ch['clsid']; m['host'] = '006BB9A0'
    chk = {}
    chk['②_fac_vt'] = (e['fac_vt'] == m['fac_vt'])
    chk['②_slot_va'] = (e['slot_va'] == m['slot_va'])
    chk['②_slot3'] = (m['fac_slot'] == 3)
    chk['②_col'] = (e['col'] == m['col'])
    chk['②_td'] = (e['td'] == m['td'])
    chk['②_name'] = (e['cls_name'].strip() == m['name']) if e['cls_name'] else None
    chk['③b_qi_at'] = (e['qi_at'] == m['qi_at'])
    chk['③b_rel_at'] = (e['rel_at'] == m['rel_at'])
    chk['③b_obj_vt'] = (e['obj_vt'] == m['obj_vt'])
    chk['③b_qi_callee'] = (e['qi_callee'] == m['qi_callee'])
    chk['④_alloc'] = (e['alloc'] == m['alloc'])
    chk['④_ctor'] = (e['ctor'] == m['ctor'])
    chk['④_clsid'] = (e['clsid'] == m['clsid'])
    chk['④_host'] = (e['host'] == m['host'])
    out.append(dict(row=r, exec=e, mine=m, chk=chk))

json.dump(out, open(os.path.join(W, "join.json"), 'w'), indent=1)

print("%-9s %-6s %-6s %-6s %-6s %-6s %-6s %-6s %-6s %-6s %-6s %-6s" % (
    "entry","facVt","slotVa","slot3","col","td","name","qiAt","relAt","objVt","qiCal","clsid"))
for o in out:
    c = o['chk']
    f = lambda k: 'ok' if c[k] else 'XX'
    print("%-9s %-6s %-6s %-6s %-6s %-6s %-6s %-6s %-6s %-6s %-6s %-6s" % (
        o['row']['entry'], f('②_fac_vt'), f('②_slot_va'), f('②_slot3'), f('②_col'), f('②_td'),
        f('②_name'), f('③b_qi_at'), f('③b_rel_at'), f('③b_obj_vt'), f('③b_qi_callee'), f('④_clsid')))
print()
for o in out:
    c = o['chk']
    bad = [k for k, v in c.items() if v is False]
    if bad:
        print("%s  MISMATCH %s" % (o['row']['entry'], bad))
        for k in bad:
            ek = k.split('_', 1)[1]
            print("    exec=%s  mine=%s" % (o['exec'].get(ek), o['mine'].get(ek)))
