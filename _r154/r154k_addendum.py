# -*- coding: utf-8 -*-
"""R154 · 补记 S-395 / S-396（门禁回归阶段新发现的两条自错），追加到本轮四件套各自段的尾部。

为什么用「追加到 EOF」而不是改已写的段：四件套都是 append-only，改已落盘的句子属于改写历史节；
而本轮四件套的段恰好在文件末尾，追加正文段落（不带新标题）仍属于同一节，满足 append-only。
幂等：先判 marker 是否已存在。
"""
import hashlib, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = ROOT + '/lead/next_re_20261117_r14'
RC, LED = D + '/R14_COMMON.md', ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md'
LOCK, BRD = ROOT + '/lead/LEAD_LOCK', D + '/STATUS_BOARD.md'
BAKDIR = D + '/R17_LEAD_BASELINE'
fail = []
def ck(n, c, d=''):
    ok = bool(c); print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fail.append(n)
    return ok

def backup(p, tag):
    b = os.path.join(BAKDIR, os.path.basename(p) + '.before_r154%s_%s.bak' % (tag, time.strftime('%Y%m%d_%H%M%S')))
    fd = os.open(b, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(open(p, 'rb').read())
    ck('备份 wx %s' % os.path.basename(b), os.path.exists(b))

def append_tail(p, marker, block, cr, tag):
    raw = open(p, 'rb').read()
    ck('%s 旧 CR == %d' % (os.path.basename(p), cr), raw.count(b'\r') == cr, raw.count(b'\r'))
    txt = raw.decode('utf-8')
    if marker in txt:
        ck('%s 幂等：marker 已存在，跳过' % os.path.basename(p), True); return
    backup(p, tag)
    new = (txt if txt.endswith('\n') else txt + '\n') + block
    open(p, 'wb').write(new.encode('utf-8'))
    back = open(p, 'rb').read()
    ck('%s 回读一致' % os.path.basename(p), back == new.encode('utf-8'))
    ck('%s CR 未变 == %d' % (os.path.basename(p), cr), back.count(b'\r') == cr, back.count(b'\r'))
    ck('%s marker 已写入' % os.path.basename(p), marker in back.decode('utf-8'))

SUF = """
**【R154 补记 · S-395 / S-396（门禁回归阶段才发现，上一节列的「八条」应为十条）】**

**S-395（假 FAIL，与我上轮 S-383 同族）**：`r154j` 断言「`GATE_VER = 'R153'` 在脚本里恰 1 处」得 **2** —— 第 2 处是 `check_disc.py` L532 注释里的同一子串。但 `str.replace` 是**全量替换**，两处都已正确改到 R154，**结果反而对**，真正该用的是行首锚定 `(?m)^GATE_VER = 'R154'`（实测恰 1 处，该断言 PASS）。⇒ 这已是我连续第二轮踩同一个坑：**对「会被注释引用到的常量」用朴素子串计数**，得到的数不代表代码里的常量数。

**S-396（假 FAIL，与 S-384/S-385 同族）**：孤儿进程判据把 `timeout 600 python3 _r154/r154j_gate.py` 这一行本身报成孤儿 —— **测量者又把自己算进了被测集合**。正确做法是排除自身 PID 与自身命令行前缀（`timeout … _r154/${script}`）。⇒ 这是**连续第三轮**同族（S-384 命中 claude 命令行、S-385 命中脚本自身 PID、S-396 命中包装用的 timeout 进程）。

**两条都不是数据错，且两条都指向同一个可复用判据**：凡「计数」类断言，先问「这个字符串会不会被别处顺带引用」；凡「扫描进程/文件」类断言，先问「被测对象会不会就是测量者本身」。
"""

SUF_LED = """
- **补记 S-395 / S-396（门禁回归阶段，两条假 FAIL，上一节「八条」应为十条）**：**S-395** `r154j` 用朴素子串数 `GATE_VER = 'R153'` 得 **2**（第 2 处是 `check_disc.py` L532 注释），但 `str.replace` 全量替换已把两处都改对，**结果反而正确**，正确判据是行首锚定（实测 1 处）。**S-396** 孤儿进程判据把 `timeout … r154j_gate.py` 自身报成孤儿 —— 测量者把自己算进被测集合；排除自身 PID 与命令行前缀后为 0。⇒ 与 S-383 / S-384 / S-385 连续三轮同族：**计数类断言先问「字符串会不会被别处引用」，扫描类断言先问「被测对象会不会就是测量者」**。两条均为判据缺陷，无数据错。
"""

SUF_LOCK = """
OL10. 🔴 **补记 S-395 / S-396（门禁回归阶段，两条假 FAIL；上一节「八条」应为十条）.** **S-395**：`r154j` 断言「`GATE_VER = 'R153'` 恰 1 处」得 **2** —— 第 2 处是 `check_disc.py` L532 的**注释**里的同一子串；但 `str.replace` 是**全量替换**，两处都已正确改到 R154，**结果反而对**，正确判据是行首锚定 `(?m)^GATE_VER = 'R154'`（实测恰 1 处 PASS）。**S-396**：孤儿进程判据把 `timeout 600 python3 _r154/r154j_gate.py` **这一行本身**报成孤儿 —— 测量者把自己算进了被测集合，排除自身 PID 与命令行前缀后为 0。⇒ **与 S-383（注释里的子串被计数）/ S-384（命中 claude 命令行）/ S-385（命中脚本自身 PID）连续三轮同族**：计数类断言要先问「这个字符串会不会被别处顺带引用」，扫描类断言要先问「被测对象会不会就是测量者本身」。两条均为判据缺陷，**无数据错**。
"""

SUF_BRD = """
### 十一 · 补记 S-395 / S-396（门禁回归阶段才发现，第九节「八条」应为十条）

**S-395（假 FAIL）**：`r154j` 断言「`GATE_VER = 'R153'` 恰 1 处」得 **2** —— 第 2 处是 `check_disc.py` **L532 的注释**。但 `str.replace` 是**全量替换**，两处都改对了，**结果反而正确**；正确判据是行首锚定（实测 1 处 PASS）。
**S-396（假 FAIL）**：孤儿进程判据把 `timeout … r154j_gate.py` **自身**报成孤儿 —— 测量者把自己算进了被测集合。
⇒ **与 S-383 / S-384 / S-385 连续三轮同族**：计数类断言先问「字符串会不会被别处引用」，扫描类断言先问「被测对象会不会就是测量者」。**两条都是判据缺陷，无数据错。**
"""

append_tail(RC, '【R154 补记 · S-395 / S-396', SUF, 1081, 'f')
append_tail(LED, '补记 S-395 / S-396（门禁回归阶段', SUF_LED, 337, 'g')
append_tail(LOCK, 'OL10.', SUF_LOCK, 137, 'h')
append_tail(BRD, '### 十一 · 补记 S-395 / S-396', SUF_BRD, 0, 'i')
print('\nFAIL %d：%s' % (len(fail), fail))
sys.exit(1 if fail else 0)
