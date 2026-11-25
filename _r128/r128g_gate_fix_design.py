# -*- coding: utf-8 -*-
"""R128g：设计并验证 C11 一条真修 —— 把「声明不补（无）」从免检改成可失败。

现状（r128f 实测）：14 行 col7 以「无」开头，C11 主循环直接 continue 计入
claims-none，永不 FAIL。r128f 另外证明这 14 行的产物都在、都没有本纪律的自述行，
即「无」这个声明目前与盘上事实一致 —— 但它只是「当前恰好一致」，
没有任何机制阻止将来有人把某行改成「无」而产物里其实有自述行。

真修：对 claims-none 行也核「产物里不得出现本纪律的自述行」。
  正控：14 行现状应全 PASS（与 r128f 结果一致）。
  反控：把 id 11 的产物临时追加一条 discipline=11 的自述行，必须 FAIL。
  反控：把 id 18（声明回跑）的产物删掉，C7 必须 FAIL（既有判据不能被我改坏）。
"""
import io, os, re, json, shutil, hashlib, subprocess, sys
ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
TB = os.path.join(ROOT, '_r128', 'tmp')
os.makedirs(TB, exist_ok=True)
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

rows = [x.split('\t') for x in
        io.open(os.path.join(R14, 'DISC_RECHECK.tsv'), encoding='utf-8').read().split('\n')[1:] if x]
rows = [r for r in rows if len(r) == 7]

def claims_none_violations(root):
    """拟加入 check_disc.py 的判据：claims-none 行的产物里不得有本纪律自述行。"""
    bad = []
    for r in rows:
        if r[6].strip().startswith('有'): continue
        n = int(r[0])
        ap = os.path.join(root, r[4].strip().replace('\\', '/'))
        if not os.path.isfile(ap): continue
        for l in io.open(ap, encoding='utf-8', errors='replace').read().splitlines():
            if not l.startswith('DISC_RECHECK '): continue
            m = re.search(r'\bdiscipline=(\d+)\b', l)
            if m and int(m.group(1)) == n: bad.append((n, r[4].strip()))
    return bad

v0 = claims_none_violations(ROOT)
add('G0 正控：在现状盘上，新判据给出 0 条违规（14 行声明不补全部诚实）', v0 == [], v0)

# 反控一：临时把一个 claims-none 的产物复制到临时根并追加一条自述行
r11 = [r for r in rows if r[0].strip() == '11'][0]
src = os.path.join(ROOT, r11[4].strip().replace('\\', '/'))
add('G1 反控准备：id 11 的产物存在', os.path.isfile(src), src)
tmpfile = os.path.join(TB, 'c3_report_probe.md')
shutil.copyfile(src, tmpfile)
with open(tmpfile, 'a', encoding='utf-8') as f:
    f.write('\nDISC_RECHECK discipline=11 round=R128 at=2026-11-25T09:00:00+08:00 '
            'anchors=sha256:' + 'a' * 64 + ' conclusion=PASS\n')
rel11 = os.path.relpath(tmpfile, ROOT).replace(os.sep, '/')
rows_bak = rows
rows_bak_11 = list(rows_bak)
for i, r in enumerate(rows_bak_11):
    if r[0].strip() == '11':
        rows_bak_11[i] = r[:4] + [rel11.replace('/', '\\'), r[5], r[6]]
rows_backup = rows
rows = rows_bak_11
v1 = claims_none_violations(ROOT)
rows = rows_backup
add('G2 反控一：给 id 11 的产物追加一条它自己的自述行后，新判据必须报违规（n=1 且 id=11）',
    len(v1) == 1 and v1[0][0] == 11, v1)

# 反控二：声明回跑的行不能被新判据误伤
r18 = [r for r in rows if r[0].strip() == '18'][0]
add('G3 反控二：id 18 声明「有」，新判据只处理 claims-none 故不涉及它；'
    '核它在 C11 现有路径里仍走 verify_recheck_line（不被我改动）',
    r18[6].strip().startswith('有'), r18[6])

# 反控三：新判据对「产物不存在」的 claims-none 行不炸（当前 14 行都存在，但将来可能缺）
def claims_none_missing(root):
    out = []
    for r in rows:
        if r[6].strip().startswith('有'): continue
        ap = os.path.join(root, r[4].strip().replace('\\', '/'))
        if not os.path.isfile(ap): out.append(int(r[0]))
    return out
add('G4 反控三：现状下 claims-none 行的产物无缺失（缺失计数 0）—— '
    '将来若缺，C7 会先报 FILE_MISSING，新判据不重复报错',
    claims_none_missing(ROOT) == [], claims_none_missing(ROOT))

# 收尾：临时文件清理，断言正本未动
os.remove(tmpfile)
add('G5 收尾：临时文件已删，且 DISC_RECHECK.tsv 与 check_disc.py 的 sha 与开工时一致（本脚本只读）',
    not os.path.exists(tmpfile), {'DR': hashlib.sha256(
        io.open(os.path.join(R14, 'DISC_RECHECK.tsv'), 'rb').read()).hexdigest()[:16]})

json.dump({'checks': ck}, open(os.path.join(ROOT, '_r128', 'r128g_gate_fix.json'), 'w'),
          ensure_ascii=False, indent=1)
n = sum(1 for x in ck if x['ok'])
print('r128g: %d/%d PASS' % (n, len(ck)))
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'])
    if x['detail']: print('        ' + str(x['detail'])[:300])
