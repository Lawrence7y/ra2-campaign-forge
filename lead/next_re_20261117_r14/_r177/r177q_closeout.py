# -*- coding: utf-8 -*-
"""R177 收口补（同轮第二段）：把 S-648..S-650 与归档/指针两项补记进四件套。
纪律：只追加、CR 保持、行数上限、写前全断言。"""
import hashlib, os, re, sys
ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead/next_re_20261117_r14')
P = F = 0
def ck(n, c, d=''):
    global P, F
    if c: P += 1; print('PASS', n, d)
    else: F += 1; print('FAIL', n, d)

COMMON_NOTE = '''
**收口补（同轮第二段）：三项自错与两处补给.** ① **S-648**：LEAD_LOCK 段头我照 `PB` 的带 `## ` 前缀写法，而最新五段（`PC`..`PG`）都是**行首无前缀**的 `P? · R17 第 N 轮` ⇒ 被「`PG` 仍在」的锚串当场抓出，改为行首式并加「前缀写法与 `PG` 一致」的等价断言。② **S-649**：归档时把 `re.finditer` 给的**字符**偏移 6,896 当成**字节**数写死（实测字节 11,556）⇒ 两种口径都写死。看板写入后 261 行 ≥ 260 触发归档，搬走文件顺序最早两段（166、165）共 **11,556 B / 53 行**，看板 261 → **208 行**、归档 9,570 → **9,623 行**（CR 2952 保持；被搬走段内 CR = 0，这是归档 CR 不漂的前提，已写成断言）。③ **S-650**：无孤儿进程自检首版把「正在跑本脚本的自己 + 外层 `bash -c` + `timeout` 包装」都算成孤儿（S-611..S-613 同族**第三次复发**）⇒ 改为经 `/proc/<pid>/status` 的 `PPid` 回溯自身链并排除本脚本文件名。④ 指针 `FACT_INDEX_CURRENT.md` 已补到 **V560**（sha `ede48f3c…` / 130,510 B / R177 / 530..560 共 **31** 份），其「声明依据」段本轮**第四次订正**（R128 下同一轮内已生成 V556..V560 五份，「只有这一个目录」「三份」「四份」三种旧写法全部失效）；**该文件仍不被任何门禁读取（第六次确认：三个门禁 `FACT_INDEX_CURRENT` 命中数各 0）**，加门是裁定、须单独一卡。⑤ 收口校验 `r177p` **32 断言 0 FAIL**：五 CR 全等（1081/337/137/0/2952）、看板 208 行、三段门禁 exit 0（C16 NOTE 逐字 `176 sections measured (pinned 176)`、unpinned 0）、`V559→V560` 差分行恰 F29 差列恰 limitations、F29 段内声明 3/4 与实测 3/4 重合（不动点）、无 r177 残留进程。
'''

LEDGER_NOTE = '''
**收口补（同轮第二段）：三项自错与五 CR.** **S-648** LEAD_LOCK 段头前缀写法照 `PB` 而非最新五段（`PC`..`PG` 行首无 `## `），被「`PG` 仍在」锚串抓出；**S-649** 归档把 `finditer` 的**字符**偏移 6,896 当**字节**数写死（实测 **11,556 B**）；**S-650** 无孤儿进程自检把自身与外层包装算成孤儿（S-611..S-613 同族第三次复发），改为 `PPid` 回溯排除自身链。看板 261 ≥ 260 触发归档，搬走 166/165 两段（53 行 / 11,556 B），看板 → **208 行**、归档 → **9,623 行**（CR 2952 保持，前提「被搬走段内 CR=0」已成断言）。指针补到 **V560**（`ede48f3c…` / 130,510 B / 31 份），其「声明依据」第四次订正；指针仍无门禁读（第六次确认）。收口 `r177p` **32 断言 0 FAIL**，五 CR 全等（1081/337/137/0/2952）。
'''

LOCK_NOTE = '''
**收口补（同轮第二段）.** **S-648** 段头前缀照 `PB`（带 `## `）而最新五段 `PC`..`PG` 是行首式 ⇒ 被「`PG` 仍在」锚串抓出。**S-649** 归档把字符偏移 6,896 当字节数写死（实测 11,556 B）。**S-650** 无孤儿进程自检把自身/外层 `bash -c`/`timeout` 算孤儿（S-611..S-613 同族**第三次复发**）⇒ 改 `PPid` 回溯排除自身链。看板 261 ≥ 260 ⇒ 搬走 166/165（53 行 / 11,556 B），看板 → **208 行**、归档 → **9,623 行**（CR 2952 保持）。指针 → **V560**（`ede48f3c…` / 130,510 B / 530..560 共 31 份，「声明依据」第四次订正），仍无门禁读（第六次确认）。`r177p` **32 断言 0 FAIL**、五 CR 全等（1081/337/137/0/2952）。
'''

BOARD_NOTE = '''
**收口补（同轮第二段）**：**S-648** LEAD_LOCK 段头前缀照 `PB` 而最新五段为行首式（被「`PG` 仍在」锚串抓出）；**S-649** 归档把字符偏移 6,896 当字节数（实测 **11,556 B**）；**S-650** 无孤儿自检把自身与外层包装算孤儿（S-611..S-613 同族第三次复发）。看板写入后 261 行 ≥ 260 ⇒ 搬走 166/165 两段（53 行 / 11,556 B），看板 → **208 行**、归档 → **9,623 行**（CR 2952 保持）。指针 → **V560**（`ede48f3c…` / 130,510 B / 530..560 共 31 份；「声明依据」第四次订正），**仍无门禁读（第六次确认）**。`r177p` **32 断言 0 FAIL**、五 CR 全等。
'''

def do(path, note, exp_cr, marker, also=None):
    raw = open(path, 'rb').read()
    txt = raw.decode('utf-8')
    ck('%s CR=%d' % (os.path.basename(path), exp_cr), raw.count(b'\r') == exp_cr, raw.count(b'\r'))
    ck('%s 已含 marker' % os.path.basename(path), marker in txt)
    ck('%s 该补记尚未存在' % os.path.basename(path), note not in txt)
    new = txt + ('' if txt.endswith('\n') else '\n') + note.lstrip('\n')
    ck('%s 前缀保留' % os.path.basename(path), new.startswith(txt))
    ck('%s CR 保持 %d' % (os.path.basename(path), exp_cr), new.count('\r') == exp_cr, new.count('\r'))
    ck('%s 补记唯一' % os.path.basename(path), new.count(note.strip()) == 1)
    if also:
        ck('%s %s' % (os.path.basename(path), also[0]), also[1](new))
    return raw, new

c1 = do(os.path.join(R14, 'R14_COMMON.md'), COMMON_NOTE, 1081, '## 2.182')
c2 = do(os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'), LEDGER_NOTE, 337, '## §1232')
c3 = do(os.path.join(ROOT, 'lead/LEAD_LOCK'), LOCK_NOTE, 137, 'PH · R17 第 177 轮')
c4 = do(os.path.join(R14, 'STATUS_BOARD.md'), BOARD_NOTE, 0, 'R17 第 177 轮')

lines = c4[1].count('\n')
print('  看板补记后行数 =', lines)
ck('看板 <= 300', lines <= 300, lines)

# §2.182 增长后 floor 仍是下界
rc = c4[0].decode('utf-8')  # 未用
comm = c1[1]
secs = {}
cur = None; buf = []
for ln in comm.split('\n'):
    m = re.match(r'^##\s+2\.(\d+)\b', ln)
    if m:
        if cur is not None: secs[cur] = len('\n'.join(buf).encode())
        cur = int(m.group(1)); buf = [ln]
    elif cur is not None: buf.append(ln)
if cur is not None: secs[cur] = len('\n'.join(buf).encode())
print('  §2.182 补记后 = %d B（floor 3488 仍是下界）' % secs[182])
ck('§2.182 >= floor 3488', secs[182] >= 3488, secs[182])
ck('§2.182 未缩水（相对 6976）', secs[182] > 6976, secs[182])

if F:
    print('ABORT %d FAIL' % F); sys.exit(1)
for (path, _), (raw, new) in zip(((os.path.join(R14, 'R14_COMMON.md'), 0),), (c1,)):
    pass
for path, (raw, new) in ((os.path.join(R14, 'R14_COMMON.md'), c1),
                         (os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'), c2),
                         (os.path.join(ROOT, 'lead/LEAD_LOCK'), c3),
                         (os.path.join(R14, 'STATUS_BOARD.md'), c4)):
    with open(path, 'wb') as f:
        f.write(new.encode('utf-8'))
    ck('回读 %s' % os.path.basename(path), open(path, 'rb').read() == new.encode('utf-8'))
print('---- %d PASS / %d FAIL ----' % (P, F))
