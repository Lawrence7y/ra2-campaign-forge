import io, os, re, sys

# 在 check_disc.py 中插入 C11（第 7 列机检），位置在 C10 之后、C5 之前
P = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\check_disc.py'
t = io.open(P, encoding='utf-8').read()
assert 'C11' not in t, 'C11 already present'

BLOCK = r'''
# ---- C11 【R53 新增】第 7 列「是否真回跑」机检（部分落地 + 显式 unverifiable）----
# 现状：0/28 有合规自描述行；12/28 可补；16/28 无自产出机制 ⇒ 显式 unverifiable。
# 规则：col7 以「有」开头者，其产物必须含一条通过 recheck_verify 的自描述行，否则 FAIL。
#       col7 以「无」开头者计入 unverifiable 计数（不 FAIL，但必须在输出里显式可见）。
C11_LANDABLE = {3, 4, 11, 12, 13, 14, 15, 17, 22, 26, 27, 28}
c11_ok = c11_fail = c11_unver = 0
_vmod = None
try:
    sys.path.insert(0, R14)
    import recheck_verify as _vmod
except Exception as _e:
    notes.append('C11 verifier import FAILED: %s' % _e)

for r in rows:
    if len(r) != 7:
        continue
    n = int(r[0]) if r[0].isdigit() else -1
    later = r[6].strip()
    if not later.startswith('\u6709'):
        c11_unver += 1
        continue
    if _vmod is None:
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
                     % (r[0], str(detail)[:70]))
notes.append('C11 col7 machine-check: ok=%d fail=%d unverifiable(claims none)=%d ; landable set=%d'
             % (c11_ok, c11_fail, c11_unver, len(C11_LANDABLE)))
'''

anchor = "# ---- C5 CR 抽查 ----"
assert anchor in t
t = t.replace(anchor, BLOCK + '\n' + anchor, 1)
t = t.replace("GATE_VER = 'R49'", "GATE_VER = 'R53'", 1)
io.open(P, 'w', encoding='utf-8').write(t)
print('inserted C11; GATE_VER -> R53')
