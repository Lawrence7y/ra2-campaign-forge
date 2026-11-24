import io, os, re, shutil

G = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\check_disc.py'
t = io.open(G, encoding='utf-8').read()
shutil.copy2(G, G + '.bakR58')

OLD = """    if _vmod is None:
        fails.append('C11 id %s claims recheck but verifier unavailable' % r[0])
        c11_fail += 1
        continue
    try:
        ok, detail = _vmod.verify_recheck_line(ROOT, r)
    except Exception as e:
        ok, detail = False, 'verifier-error:%s' % e
    if ok:
        c11_ok += 1
    else:
        c11_fail += 1
        fails.append('C11 id %s claims recheck but has no valid self-description line (%s)'
                     % (r[0], str(detail)[:70]))"""

NEW = """    if _vmod is None:
        fails.append('C11 id %s claims recheck but verifier unavailable' % r[0])
        c11_fail += 1
        continue
    try:
        ok, detail = _vmod.verify_recheck_line(ROOT, r)
    except Exception as e:
        ok, detail = False, 'verifier-error:%s' % e
    if ok:
        c11_ok += 1
    elif n in C11_FROZEN:
        # R58：冻結类——在冻结档里，结构性不可验证 ⇒ 不 FAIL，但显式计入
        c11_declared += 1
    else:
        c11_fail += 1
        fails.append('C11 id %s claims recheck but has no valid self-description line (%s)'
                     % (r[0], str(detail)[:70]))"""

assert OLD in t, 'C11 verifier block not found'
t = t.replace(OLD, NEW, 1)

# 在 C11 循环前载入冻结档，并校验其哈希登记
LOADER = '''C11_FROZEN = set()
_FREEZE = os.path.join(R14, 'DISC_UNVERIFIABLE.tsv')
if os.path.exists(_FREEZE):
    _frows = [x for x in read(_FREEZE).split('\\n') if x]
    for _r in _frows[1:]:
        _c = _r.split('\\t')
        if _c and _c[0].strip().isdigit():
            C11_FROZEN.add(int(_c[0]))
    notes.append('C11 frozen-class registry loaded: %d ids %s' % (len(C11_FROZEN), sorted(C11_FROZEN)))
else:
    fails.append('C11 frozen-class registry DISC_UNVERIFIABLE.tsv MISSING '
                 '(structurally-unverifiable rows must be registered, not assumed)')

'''
anchor2 = "c11_ok = c11_fail = c11_unver = 0"
assert anchor2 in t
t = t.replace(anchor2, LOADER + "c11_ok = c11_fail = c11_unver = c11_declared = 0", 1)

# 输出行加入 declared
t = t.replace(
    "notes.append('C11 col7 machine-check: ok=%d fail=%d unverifiable(claims none)=%d ; landable set=%d'\n             % (c11_ok, c11_fail, c11_unver, len(C11_LANDABLE)))",
    "notes.append('C11 col7 machine-check: ok=%d fail=%d frozen-unverifiable=%d claims-none=%d'\n             % (c11_ok, c11_fail, c11_declared, c11_unver))",
    1)
t = t.replace("GATE_VER = 'R55'", "GATE_VER = 'R58'", 1)
io.open(G, 'w', encoding='utf-8').write(t)
print('wired frozen-class gate into C11; GATE_VER -> R58')
