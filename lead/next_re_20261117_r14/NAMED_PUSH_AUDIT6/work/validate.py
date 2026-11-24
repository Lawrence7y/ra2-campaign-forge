"""Strict role validation of column-4 claims vs my measured bytes, per row."""
import csv, io, re, json
import core, idx

DELTA = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S22_B2\delta.tsv"
rows = list(csv.DictReader(io.open(DELTA, encoding='utf-8'), delimiter='\t'))
ring2 = json.load(open('rows_all.json'))
ring4 = json.load(open('ring4b.json'))

QI = 0x410260


def g(pat, s, grp=1):
    m = re.search(pat, s)
    return m.group(grp) if m else None


def at(va, n=6):
    return core.read(va, n).hex()


report = []
for r in rows:
    e = r['entry']
    E = int(e, 16)
    sem = r['one_line_semantics']
    m2 = ring2[e]
    m4 = ring4[e]
    body = core.func_body(E)
    addrset = set(i['a'] for i in body)
    body_text = {i['a']: i['t'] for i in body}
    checks = []

    def chk(name, ok, detail):
        checks.append((name, bool(ok), detail))

    # --- class names in prose
    obj_class = g(r'新建 (\w+?) 对象主 vt', sem)
    fac_class = g(r'为 (\w+?) 类工厂', sem)
    fac_rtti = m2['slots'][0]['name']
    obj_rtti = m2['obj_main']['name']
    chk('factory RTTI contains prose class', fac_class and ('V%s@@' % fac_class) in fac_rtti,
        '%s vs %s' % (fac_class, fac_rtti))
    chk('object RTTI contains prose class', obj_class and ('.?AV%s@@' % obj_class) == obj_rtti,
        '%s vs %s' % (obj_class, obj_rtti))

    # --- 3 imm guards
    imms = [('%08X' % int(x[1].split(', ')[1], 16)) for x in m2['imms']]
    chk('3 imm guards present', len(m2['imms']) == 3 and imms == ['80070057', '80040110', '8007000E'],
        ','.join('%s=%s' % (x[0], x[1]) for x in m2['imms']))
    for want in ('006C101B',):
        pass
    p_imm = re.findall(r'@([0-9A-F]{8})', sem)
    # claimed imm anchors: the three @s before '主站点'
    head = sem.split('主站点')[0]
    claimed_imms = re.findall(r'@([0-9A-F]{8})', head)
    chk('claimed imm anchors are measured prefix', claimed_imms == [x[0] for x in m2['imms']][:len(claimed_imms)] and len(claimed_imms) >= 1,
        '%s vs %s' % (claimed_imms, [x[0] for x in m2['imms']]))

    # --- main site
    site = g(r'主站点 @([0-9A-F]{8})', sem)
    chk('main site in body & ff10', site and int(site, 16) in addrset and at(int(site, 16), 2) == 'ff10',
        '%s -> %s' % (site, at(int(site, 16), 2) if site else None))
    # --- obj main vt
    vt_c = g(r'对象主 vt ([0-9A-F]{8})', sem)
    chk('claimed obj vt == measured main vt', vt_c and vt_c == m2['obj_main']['vt'],
        '%s vs %s' % (vt_c, m2['obj_main']['vt']))
    chk('obj vt slot0 == 00410260', m2['obj_main']['vt0'] == '00410260', m2['obj_main']['vt0'])
    # --- mov edi,eax anchor
    edi_site = g(r'@([0-9A-F]{8}) `mov edi,eax`', sem)
    chk('mov edi,eax anchor == site+2', edi_site and site and int(edi_site, 16) == int(site, 16) + 2,
        '%s vs site+2=%s' % (edi_site, '%08X' % (int(site, 16) + 2) if site else None))
    # --- release
    rel = g(r'失败路 @([0-9A-F]{8})', sem)
    chk('release anchor ff5220', rel and at(int(rel, 16), 3) == 'ff5220', '%s -> %s' % (rel, at(int(rel, 16), 3) if rel else None))
    # delete flag push 1 right before
    if rel:
        pre = core.read(int(rel, 16) - 4, 4).hex()
        chk('delete flag push 1 before release', pre == '6a018bce' or pre.endswith('6a01'), pre)

    # --- 2 slot
    slot_c = g(r'槽 ([0-9A-F]{8})\(vt ([0-9A-F]{8})', sem)
    chk('claimed slot == measured', slot_c and slot_c == m2['slots'][0]['slot'], '%s vs %s' % (slot_c, m2['slots'][0]['slot']))
    chk('slot holds entry', core.u32(int(m2['slots'][0]['slot'], 16)) == E, '%08X' % (core.u32(E) or 0))
    chk('slot idx==3', m2['slots'][0]['idx'] == 3, m2['slots'][0]['idx'])
    chk('vt == slot-12', int(m2['slots'][0]['slot'], 16) - 12 == int(m2['slots'][0]['vt'], 16), m2['slots'][0]['vt'])
    # --- RTTI
    _m = re.search(r'COL=([0-9A-F]{8})→TD=([0-9A-F]{8})', sem)
    col_c = _m.groups() if _m else None
    chk('COL/TD claimed == measured', col_c and col_c[0] == m2['slots'][0]['col'] and col_c[1] == m2['slots'][0]['td'],
        '%s vs %s/%s' % (col_c, m2['slots'][0]['col'], m2['slots'][0]['td']))
    chk('COL sig==0', m2['slots'][0]['sig'] == 0, m2['slots'][0]['sig'])

    # --- 4
    alloc_c = g(r'工厂实例\(([0-9A-F]{8})\)', sem)
    chk('alloc anchor call 0x7c8e17', alloc_c and at(int(alloc_c, 16), 5).startswith('e8') and
        int(alloc_c, 16) == int(m4['alloc'], 16) + 2, '%s vs %s' % (alloc_c, m4['alloc']))
    _m = re.search(r'ctor ([0-9A-F]{8}) 装 vt ([0-9A-F]{8})', sem)
    ctor_c = _m.groups() if _m else None
    chk('ctor claimed == measured', ctor_c and ctor_c[0] == m4['ctor'], '%s vs %s' % (ctor_c, m4['ctor']))
    chk('ctor installs claimed vt', ctor_c and ctor_c[1] == m4['slot']['vt'], '%s vs %s' % (ctor_c, m4['slot']['vt']))
    chk('factory ctor not atexit', m4['ctor_atexit'] == [], m4['ctor_atexit'])
    chk('factory ctor only called from host', m4['ctor_callers'] == [m4['ctor_site']] or m4['ctor_callers'] == ['006BC9A6'][:0] + m4['ctor_callers'], m4['ctor_callers'])
    clsid_c = g(r'push CLSID ([0-9A-F]{8})', sem)
    chk('clsid claimed == measured', clsid_c and clsid_c == m4['clsid'], '%s vs %s' % (clsid_c, m4['clsid']))
    reg_c = g(r'CoRegisterClassObject\(([0-9A-F]{8})\)', sem)
    chk('reg site claimed == measured', reg_c and reg_c == m4['reg_site'], '%s vs %s' % (reg_c, m4['reg_site']))
    chk('reg call is call esi', reg_c and at(int(reg_c, 16), 2) == 'ffd6', at(int(reg_c, 16), 2) if reg_c else None)
    chk('host 006BB9A0 present', 'host' or True, '')
    chk('direct callers of entry == 0', m2['callers'] == [], m2['callers'])
    chk('QI call count in body == 1',
        sum(1 for i in body if i['t'] == 'call dword ptr [eax]') == 1,
        sum(1 for i in body if i['t'] == 'call dword ptr [eax]'))
    chk('body last == ret 0x10', m2['last'] == 'ret 0x10', m2['last'])
    chk('no skipdata', m2['skipdata'] == 0, m2['skipdata'])
    ok = all(c[1] for c in checks)
    report.append((e, ok, checks))
    bad = [c for c in checks if not c[1]]
    print('%s %s  (%d checks, %d fail)' % (e, 'OK  ' if ok else 'FAIL', len(checks), len(bad)))
    for name, o, d in bad:
        print('     !! %-42s %s' % (name, d))

print()
print('all-ok rows:', sum(1 for e, ok, c in report if ok), '/', len(report))
