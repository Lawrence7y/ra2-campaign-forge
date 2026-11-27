#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R175 J：给四件套补三段「本轮收口后才发生」的实测（指针补版、C16 重钉、归档计数）。

为什么必须补：r175g 写四件套时 C16 重钉与指针补版尚未执行；若不在同轮登记，
下一轮读四件套会以为「unpinned 2 仍在」「指针仍指 V556」—— 那是错的。

只做纯追加（各自文件末尾），CR 不变量：R14_COMMON 1081 / LEAD_LOCK 137 / 看板 0。
C16 影响：§2.180 的 floor 是**下界**，追加后正文变长不会 FAIL（下界语义）。
"""
import hashlib, io, json, os, sys, time
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
F1 = os.path.join(TIER, 'R14_COMMON.md')
F3 = os.path.join(ROOT, 'lead/LEAD_LOCK')
F4 = os.path.join(TIER, 'STATUS_BOARD.md')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
CD = os.path.join(TIER, 'check_disc.py')
PT = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
OUT = os.path.join(ROOT, '_r175/r175j_addendum.json')
stamp = time.strftime('%Y%m%d_%H%M%S')
EXP_CR = {F1: 1081, F3: 137, F4: 0}
fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

blobs = {p: io.open(p, 'rb').read() for p in (F1, F3, F4)}
for p, exp in EXP_CR.items():
    ck('W1 %s CR == %d' % (os.path.basename(p), exp), blobs[p].count(b'\r') == exp, blobs[p].count(b'\r'))

cd = io.open(CD, encoding='utf-8').read()
pt = io.open(PT, encoding='utf-8').read()
ck('W2 C16 表现在 174 条（含 179/180）', cd.count('    179: ') == 1 and cd.count('    180: ') == 1,
   (cd.count('    179: '), cd.count('    180: ')))
ck('W3 C16 pin 已是 0bfc18cd…', "C16_FLOORS_SHA256 = '0bfc18cd" in cd, 'C16_FLOORS_SHA256 = \'0bfc18cd' in cd)
ck('W4 指针已指 V557 且 sha 是 fc78f378…', 'R17_R128_FACTINDEX_V557' in pt and 'fc78f3780ef2f320' in pt,
   ('R17_R128_FACTINDEX_V557' in pt, 'fc78f3780ef2f320' in pt))

ADD1 = '''
**十 · R175 收口后补的三条实测（写在 §2.180 之后，不属上文任何小节）.** ① **C16 重钉**：`r175i` **23 断言 0 FAIL**，用旧表重算 sha 命中旧 pin `5a767e7c…` 作硬闸后，只插入 `179: 4939` / `180: 4540` 两行（floor = 实测 9,878 / 9,080 的一半，与既有 172 条同口径），pin → **`0bfc18cd3c2df25f98c8add57819d1d023c8d9408f0c92414ea56176c8ac78db`**；三条反控（180 floor +1 / 删 180 整行 / 179 抄 178 的值）均使表 sha 变化。`check_disc` 复跑：**174 sections measured（pinned 174）**、hollow/deficient 0、missing 0、**unpinned 0**、min margin 20（改前是 pinned 172 / unpinned 2，而 `C16_UNPINNED_MAX == 2` ⇒ 本轮不重钉的话下一轮再加一节就直接 FAIL）。② **指针**：`r175h` **14 断言 0 FAIL** 把 `FACT_INDEX_CURRENT.md` 从 V556 补到 **V557**（`fc78f378…` / 128,363 B / 声明轮次 R175 / 版本范围 V530..V557 共 28 份），并**订正一条已失效的声明依据**：原文写「R128 下只有这一个 FACT_INDEX 目录」——R175 起 V556 与 V557 同属 R128，该条已不成立，改为「版本号最大 + 该目录 sha 与 facts_floors 的 D0 一致」两条同时成立。该文件（第四次确认）**仍不被任何门禁读**。③ **归档**：看板写入后 263 行 ≥ 260 触发归档，搬走最早 2 段（第 168、167 轮）后 **219 行**，归档 9,510 → **9,570 行**（CR 2952 保持）。
'''

ADD3 = '''

PF9. ✅ **交付六（收口后补）：C16 重钉 172 → 174 节、指针补到 V557、看板归档 2 段.** `r175i` **23 断言 0 FAIL**：旧表重算 sha 命中 `5a767e7c…` 作硬闸，只插 `179: 4939` / `180: 4540`（floor = 实测 9,878 / 9,080 的一半），pin → **`0bfc18cd3c2df25f…`**；三反控（180 floor +1 / 删 180 / 179 抄 178）均使表 sha 变。`check_disc` 复跑 **pinned 174 / unpinned 0**（改前 pinned 172 / unpinned 2，而上限 `C16_UNPINNED_MAX == 2` ⇒ 不重钉则下一轮必 FAIL）。`r175h` **14 断言 0 FAIL** 把指针补到 **V557**（`fc78f378…` / 128,363 B / R175），并订正一条**已失效的声明依据**（原文「R128 下只有这一个目录」—— 现 V556/V557 同属 R128）。看板 263 行 ≥ 260 触发归档，搬走最早 2 段（168/167）后 **219 行**，归档 9,510 → **9,570 行**（CR 2952 保持）。
'''

ADD4 = '''
**收口后补（同轮第三段）**：① **C16 重钉** 172 → **174** 节（只插 `179: 4939` / `180: 4540`，旧表重算 sha 命中 `5a767e7c…` 作硬闸，pin → `0bfc18cd3c2df25f…`；三反控均使表 sha 变），`check_disc` 复跑 **pinned 174 / unpinned 0**（改前 pinned 172 / unpinned 2，而 `C16_UNPINNED_MAX == 2` ⇒ 不重钉则下一轮必 FAIL）。② **指针补到 V557**（`fc78f378…` / 128,363 B / R175 / V530..V557 共 28 份），并订正原文里**已失效**的一条声明依据（「R128 下只有这一个目录」—— 现 V556/V557 同属 R128）；该文件仍不被任何门禁读。③ **看板归档**：写入后 263 ≥ 260，搬走最早 2 段（168/167），**219 行**，归档 9,510 → **9,570 行**（CR 2952）。
'''

for tag, p, s, key in (('R14', F1, ADD1, '十 · R175 收口后补的三条实测'),
                       ('LOCK', F3, ADD3, 'PF9. ✅ **交付六'),
                       ('BOARD', F4, ADD4, '收口后补（同轮第三段）')):
    t = blobs[p].decode('utf-8')
    ck('W5 %s 追加前该锚串 0 次' % tag, t.count(key) == 0, t.count(key))
    ck('W6 %s 母本以换行结尾' % tag, t.endswith('\n'), t[-1:] == '\n')

new = {}
new[F1] = blobs[F1].decode('utf-8') + ADD1
new[F3] = blobs[F3].decode('utf-8') + ADD3
new[F4] = blobs[F4].decode('utf-8') + ADD4
for p, exp in EXP_CR.items():
    ck('W7 %s 新 CR 仍 %d' % (os.path.basename(p), exp), new[p].encode('utf-8').count(b'\r') == exp,
       new[p].encode('utf-8').count(b'\r'))
ck('W8 看板新行数 < 260', new[F4].count('\n') < 260, new[F4].count('\n'))
ck('W9 三件新内容都以母本为前缀', all(new[p].startswith(blobs[p].decode('utf-8')) for p in new), True)
for tag, p, key in (('R14', F1, '十 · R175 收口后补的三条实测'), ('LOCK', F3, 'PF9. ✅ **交付六'),
                    ('BOARD', F4, '收口后补（同轮第三段）')):
    ck('W10 %s 追加后锚串恰 1 次' % tag, new[p].count(key) == 1, new[p].count(key))

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails))
    io.open(OUT, 'w', encoding='utf-8').write(json.dumps({'fails': fails}, ensure_ascii=False, indent=1))
    sys.exit(1)

for p in (F1, F3, F4):
    raw = blobs[p]
    osha = hashlib.sha256(raw).hexdigest()
    bak = os.path.join(BASE, '%s.before_r175j_%s.bak' % (os.path.basename(p), stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
    ck('X1 %s 备份 sha 命中旧 sha' % os.path.basename(p),
       hashlib.sha256(io.open(bak, 'rb').read()).hexdigest() == osha, os.path.basename(bak))
    io.open(p, 'w', encoding='utf-8', newline='').write(new[p])
    back = io.open(p, 'rb').read()
    ck('X2 %s 回读一致' % os.path.basename(p), back == new[p].encode('utf-8'), len(back))
    ck('X3 %s 回读 CR == 期望' % os.path.basename(p), back.count(b'\r') == EXP_CR[p], back.count(b'\r'))
    print('     %-22s %d -> %d B / %d 行 / CR %d / sha %s' %
          (os.path.basename(p), len(raw), len(back), back.count(b'\n'), back.count(b'\r'),
           hashlib.sha256(back).hexdigest()[:16]))
io.open(OUT, 'w', encoding='utf-8').write(json.dumps({'fails': fails, 'assertions': n}, ensure_ascii=False, indent=1))
print('\n== %d 断言, %d FAIL ==' % (n, len(fails)))
sys.exit(1 if fails else 0)
