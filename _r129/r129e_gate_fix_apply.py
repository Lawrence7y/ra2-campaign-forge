# -*- coding: utf-8 -*-
"""R129e：把 C11 的 claims-none 通道从「只查自述行」再收紧一档 —— 它的校验式必须真跑通过。

R128 已把 claims-none 从「直接 continue」改成「产物里不得出现本纪律自述行」。那闭合的是
「把有偷偷改成无、产物里还留着自述行」这一种。但另一种仍然敞开：
把某行的校验式改成一条**当前不成立**的式子，同时把第 7 列写成无 —— 门禁照样 exit 0。
本轮先实测（r129d）：14 条 claims-none 的校验式在真产物上 14/14 全成立，
在空产物上 0/14 成立 ⇒ 这条判据有分辨力、且当前零误伤，可以直接接上。

写入纪律：wx 独占备份 -> 断言旧 sha256 与旧 CR -> 一次性写入 -> 回读校验 -> 断言新 CR 不变。
"""
import io, os, sys, hashlib, datetime

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
GATE = os.path.join(R14, 'check_disc.py')
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

OLD_SHA = 'fefe48219c8ed9b00e353a7e'   # 前缀，下面按 64 位全比较
old = io.open(GATE, 'rb').read()
full = hashlib.sha256(old).hexdigest()
assert full.startswith(OLD_SHA), 'check_disc.py 已不是 R128 终态：%s' % full[:16]

ctrls = []
def ck(n, ok, d=''):
    ctrls.append((n, bool(ok), d))

ck('E0 开工前 check_disc.py sha256 前缀 fefe48219c8ed9b0', full.startswith('fefe48219c8ed9b0'), full[:16])

OLD_BLOCK = """            if _hits_none > 0:
                c11_fail += 1
                fails.append('C11 id %s claims-none but its product carries %d '
                             'self-description line(s) for this discipline (R128)'
                             % (r[0], _hits_none))
                continue
        c11_unver += 1
        continue"""
NEW_BLOCK = """            if _hits_none > 0:
                c11_fail += 1
                fails.append('C11 id %s claims-none but its product carries %d '
                             'self-description line(s) for this discipline (R128)'
                             % (r[0], _hits_none))
                continue
        # R129 真修：claims-none 的第二道口子。R128 只挡住了「产物里还留着自述行」，
        # 没挡「校验式本身已经不成立」。实测（_r129/r129d_tautology_probe.py，8/8 PASS）
        # 14 条 claims-none 的校验式在真产物上 14/14 成立、在空产物上 0/14 成立 ⇒
        # 接上它零误伤、且有分辨力。判据：claims-none 行的校验式必须真跑通过。
        _e_none = r[5].strip()
        if _e_none not in ('', 'none') and not _e_none.startswith('none'):
            _ok_none, _det_none = run_expr(r[4].strip(), _e_none)
            if _ok_none is not True:
                c11_fail += 1
                fails.append('C11 id %s claims-none but its check expression no longer holds '
                             '(%s) :: %s (R129)' % (r[0], _det_none, _e_none[:40]))
                continue
        c11_unver += 1
        continue"""
assert old.decode('utf-8').count(OLD_BLOCK) == 1, 'R128 那段在盘上不是恰好一处'
ck('E1 R128 的 claims-none 段在盘上恰 1 处（按逐字匹配计数）', True)

new = old.decode('utf-8').replace(OLD_BLOCK, NEW_BLOCK)
assert new != old.decode('utf-8')
nb = new.encode('utf-8')
ck('E2 新文本零反引号', b'`' not in nb)
ck('E3 新文本 CR 数与旧一致（全 LF 文件，均为 0）', nb.count(b'\r') == old.count(b'\r'), (old.count(b'\r'), nb.count(b'\r')))

dst = os.path.join(BK, 'r129_check_disc.%s.bak' % TS)
fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
try:
    os.write(fd, old)
finally:
    os.close(fd)
ck('E4 wx 独占备份已建（不覆盖任何既有文件）', os.path.isfile(dst) and io.open(dst, 'rb').read() == old, dst)

with io.open(GATE, 'wb') as f:
    f.write(nb)
rb = io.open(GATE, 'rb').read()
ck('E5 回读 == 写入字节', rb == nb)
ck('E6 回读 CR 仍为旧值', rb.count(b'\r') == old.count(b'\r'), rb.count(b'\r'))
ck('E7 回读含新判据标记 (R129)', b'(R129)' in rb)

bad = [c for c in ctrls if not c[1]]
for n, ok, d in ctrls:
    print(('  PASS ' if ok else '  FAIL ') + n + (('  | ' + str(d)) if d else ''))
print('%d/%d PASS' % (len(ctrls) - len(bad), len(ctrls)))
print('sha %s -> %s' % (full[:16], hashlib.sha256(rb).hexdigest()[:16]))
sys.exit(1 if bad else 0)
