# -*- coding: utf-8 -*-
# R68 · 追加 R14_COMMON §2.74：wx 独占备份 -> 断言旧 sha256 与 CR -> 一次性写入 -> 回读校验
import io, os, hashlib, time, sys

DRY = '--dry' in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
P = os.path.join(R14, 'R14_COMMON.md')
CR_EXP = 1081

fails, buf = [], []
def W(s=''):
    print(s); buf.append(s)
def ck(n, c, d=''):
    W(('  PASS ' if c else '  FAIL ') + n + (('  ' + d) if d else ''))
    if not c: fails.append(n)

raw = open(P, 'rb').read()
ck('旧 R14_COMMON CR=%d' % CR_EXP, raw.count(b'\r') == CR_EXP)
ck('旧 R14_COMMON 可 UTF-8 解码', True)
old = raw.decode('utf-8')
ck('旧文件以换行结尾', old.endswith('\n'))
ck('旧文件不含 §2.74 标题（防重复追加）', '## 2.74' not in old)
W('[before] %d B CR=%d LF=%d sha=%s' % (len(raw), raw.count(b'\r'), raw.count(b'\n'),
                                        hashlib.sha256(raw).hexdigest()[:16]))

SEC = """## 2.74 【R17 追加，2026-11-22】归档器只认一种段头、门禁的 5 个 FAIL 卡在窗口表上、5 处「永远通过」逐项实测完毕；其中三处我的断言自己写错了

### 一 · 归档器：不是「只认 🔴」，是「按段头前缀硬编码」

R67 记录「归档器只认 `🔴` 未修」。本轮重写为 `_r68/archive_r68.py`，实测原因比记录更具体：
盘上第 61 轮段头是 `## 🔴 R17 第 61 轮`、第 66 轮是 `## 🔴 …`、第 67 轮是 `## 🟢 …`，
而第 62–65 轮**根本不是 `##` 段头**，是 `> 📌 **第 62 轮（19:2x）**：…` 这样的笔记行。
⇒ 只看前缀会同时漏两类：漏「🟢 段头」与漏「笔记行形态」。新归档器用
`^## (?:[emoji]\\s*)*R17 第 (\\d+) 轮` + `^> 📌 \\*\\*第 (\\d+) 轮` 两条正则联合取轮次记录，
并且**只归档顶格 `##` 段**（笔记行内嵌在第 61 轮段里，逐字搬即可）。

### 二 · 归档实测（本轮已落盘）

| 项 | 前 | 后 |
|---|---:|---:|
| `STATUS_BOARD` 字节 | 59,004 | **40,567（−18,437）** |
| `STATUS_BOARD` 行数 | 269 | **234** |
| `STATUS_BOARD` CR | 0 | **0** |
| `BOARD_ARCHIVE` 字节 | 598,161 | **617,308（+19,147）** |
| `BOARD_ARCHIVE` CR | 2,952 | **2,952** |

第 61、66 轮（非空 16 + 17 行）逐字搬入两个 `<details>`，`missing=0`。

### 三 · 归档器自测里我自己犯了两个错（都已抓住并改）

1. **空行被当成「命中」**：`missing_count` 原本 `sum(1 for l in seg if l not in hay)`，而空串在任何文本里都「存在」⇒ 17 行里有 1 个空行被算作命中，反控因此报 `missing=16/17` 而不是 `16/16`。**修法：只数非空行**。这与「分母口径」同族，但更隐蔽 —— 它不是算错，是**恒真项混进了计数**。
2. **反控指向了错的 hay**：第一版把「丢段头的切片」拿去 `new_arch` 里查，可正文本来就在、只丢了标题行，于是 `missing=0`，反控 FAIL。**正确的反控是让检测器指向一个确实不含该内容的 hay（旧归档）**，不是构造变形切片。⇒ **反控要测「内容不在时会报缺」，不是「内容变形时会报缺」。**

### 四 · 门禁的 5 个 FAIL：卡在窗口表，而且是「起点/终点错配」

Linux 上 `check_disc.py` 根本跑不起来（`ROOT` 硬编码 `D:\\`），本轮用只替换 `ROOT` 与路径分隔符两处的探针复现出与 Windows 完全一致的 `ok=0 fail=5 frozen=12 none=11`，
5 条 FAIL 串全部是 `R4 at outside R055 window [17:41:46, 17:46:45)`。

判别性测量（`_r68/window_r68.py`）：**35 份无 add 后缀的规范快照，内容里最后一轮的编号全部 = N−1**，
「最后一轮 = N」的 0 份。⇒ `before_rN` 是**第 N 轮写板之前**的快照，即第 N 轮的窗口起点就应当是 `before_rN`，
现行表这一点没错。**错的是「第 55 轮的工作为什么落在 17:39」**：`before_r54=17:34:00`、`before_r55=17:41:46`，
按现行表 17:39 属于**第 54 轮**窗口，而那 5 条自述行标的是 `round=R55`。
两个候选解释（窗口错 / round 字段错）只能选一，本轮**没有选**——缺一份「第 54 轮封口时刻」的独立材料。

### 五 · §2.57 与 §2.59 的矛盾，用自测本身判清了：§2.57 是错的

四组对照（同一份代码、只改 `_ROUND_ROWS`）：

| 变体 | POS | NEG1 | NEG2 | NEG3 | NEG4 | 自测 |
|---|---|---|---|---|---|---|
| 原样 | PASS | PASS | PASS | PASS | PASS | **5/5** |
| 只前移 r55（§2.57 的直接做法） | PASS | PASS | PASS | PASS | PASS | **5/5** |
| 20 条全量重映射（§2.57 的文字描述） | **FAIL** | PASS | PASS | PASS | PASS | **4/5** |
| 全部放宽到全天 | PASS | PASS | PASS | FAIL | PASS | **4/5** |

- **全量重映射打破 POS 的原因可算**：POS 固定 `at=16:20:00` 断言落在 R52；原表 R52 = `[16:17:50, 16:28:03)` 含它，重映射后 R52 = `[16:01:44, 16:17:50)` 不含。⇒ **自测把「R52 起点 = before_r52」这个语义固化成了可执行断言，全量重映射把它推翻**。
- 而第四节已独立证明「起点 = before_rN」是对的 ⇒ **全量重映射错、§2.57 的「off-by-one」说法错**。
- **同时纠正我在 §2.59 的一处过度声称**：我当时写「NEG4 不再测它声称要测的 R5」。实测：重映射下 NEG4 仍报 PASS，但拦截理由确实变成 `R4 at outside`（`R5 anchors mismatch` 不再出现）⇒ **这一句是对的**；但我另一句隐含「放宽抓不到」是错的 —— **放宽到全天时 NEG3 明确 FAIL**（`ok=True expect=False`），**自测抓得住放宽，抓在 NEG3 一侧**。

### 六 · 5 处「永远通过」逐项实测（`_r68/alwayspass_r68.py`，沙箱跑，所有项均带正控+反控）

| # | 子项 | 实测结论 | 反控 |
|---|---|---|---|
| ① | C7 `bytes=N` 死分支 | 28 行校验式前缀实测 `grep=21 / grepcount=3 / rows=4 / bytes=0` ⇒ **确实无人使用，但从不是死代码** | 改一行成 `bytes=999999` ⇒ 被抓，FAIL 由 5 增至 6 |
| ② | C11 frozen 可摘帽 | **成立，且门槛是「时刻」**：写真实时刻 17:39:19 ⇒ 仍不摘帽；写窗口内 17:42:00 ⇒ `ok 0→1`、`frozen 12→11` | 同一行只改 `at` 一个字段，其余（纪律号/格式/哈希）全对 |
| ③ | C11 claims-none 免检 | **成立**：11 条写「无」者完全不进 C11；把冻结纪律 5 的「有」改成「无」⇒ `frozen 12→11` 且 **FAIL 数不变** | 反向：把真做过的 3/4/22/27/28 五条改「无」⇒ 门禁**立刻 exit 0**、`C11=(0,0,12,16)` |
| ④ | C9 占位精确匹配 | **成立**：`GARBAGE-CRITERION-OTHER` / `GARBAGE-ANCHOR-OTHER` 照过 | 字面量 `TBD` 会被抓；空串会被抓 ⇒ 判据活着，只是太窄 |
| ⑤ | C10 门自检可自证 | **成立**：只改常量 ⇒ FAIL；常量+登记串同改 ⇒ `ok(R99)`、C10 无 FAIL | 两步分开做，证明它只做「两处一致性」比对 |

**③ 的反向反控是本轮最重要的一条**：门禁的 exit 码可以被「把真工作改标成『无』」这一动作直接清零 —— **变绿的最短路径是删掉声称，而不是完成工作**。

### 七 · 未取得（不掩盖）

1. **第 55 轮那 5 条到底属第 54 还是第 55 轮 —— 未判**。缺「第 54 轮封口时刻」的独立材料，两个解释都缺决定性证据，**不推断填空**。
2. **窗口表一处真实不一致未修**：`_ROUND_ROWS` 的注释串（第 4/5 字段）在 r56/r57 两行写成「乙」形态（`before_r55` / `before_r56` 作起点），而这两行的数字仍是「甲」。**注释与数据分裂**（§2.59 已记过同类），本轮未改 —— 改注释不改数据会让人以为语义变了。
3. **r57 的终点仍是占位 `235959`**（下一份快照 `before_r58` 是 17:52:00，本可填）。**未改**：改它会让 r57 窗口收窄，属判据变更，须与第 1 项一并裁。
4. **①③④⑤ 四处均未修**，只做了实测与最小修法方向。理由同 `§2.60`：每一条都要设计，不是改一行；且本轮先要把「改哪一处不会让门禁失去抓造假能力」说清。
5. **Linux 上 `check_disc.py` / `recheck_verify.py` 仍不可直接运行**（`ROOT` 硬编码、`rel.replace('/','\\\\')` 反向转换）。本轮全部实测靠两处等值替换的探针，**这是口径偏差，不是等价物**。
6. 「引用义务 vs 证据声称」仍是判读（**第五十四次**记）。
"""

new = old + SEC
ck('新内容无 CR 字符（全 LF）', '\r' not in SEC)
ck('新内容以换行结尾', new.endswith('\n'))
ck('原文件内容是新文件的前缀（纯追加，未改旧文）', new.startswith(old))
ck('新文件 CR 总数仍 = %d' % CR_EXP, new.count('\r') == CR_EXP, str(new.count('\r')))
ck('新文件含 §2.74 标题', '## 2.74' in new)
ck('新文件 §2.74 只出现 1 次', new.count('## 2.74') == 1, str(new.count('## 2.74')))
# 反控：前缀断言必须有判别力 —— 真的动过一个字符，就必须报 False
_mut = old[:-1] + 'X'
ck('反控「前缀=纯追加」有判别力：改动旧文末字符即判 False', new.startswith(_mut) is False)
ck('反控对照：未改动时判 True', new.startswith(old) is True)
# 反控：CR 断言有判别力 —— 注入一个 CR 必须被抓
ck('反控「CR 不变量」有判别力：注入 1 个 CR 即判 False',
   (new + '\r').count('\r') != CR_EXP)
ck('反控对照：不加 CR 时相等', new.count('\r') == CR_EXP)

ts = time.strftime('%Y%m%d_%H%M%S')
bk = os.path.join(BASE, 'SUPERSEDED.before_r68_write_common_%s.md' % ts)
W('')
W('[backup] wx 独占创建 ' + os.path.basename(bk) + ('  [DRY]' if DRY else ''))
if not DRY:
    with open(bk, 'xb') as f:
        f.write(raw)
    got = open(bk, 'rb').read()
    ck('备份字节与旧文件一致', hashlib.sha256(got).hexdigest() == hashlib.sha256(raw).hexdigest())
    assert got == raw
    open(P, 'wb').write(new.encode('utf-8'))

b2 = open(P, 'rb').read() if not DRY else new.encode('utf-8')
W('[after] %d B CR=%d LF=%d sha=%s' % (len(b2), b2.count(b'\r'), b2.count(b'\n'),
                                       hashlib.sha256(b2).hexdigest()[:16]))
ck('回读字节 == 预期', b2 == new.encode('utf-8'))
ck('回读 CR=%d' % CR_EXP, b2.count(b'\r') == CR_EXP)
ck('回读 前缀仍是旧文件（纯追加）', b2.startswith(raw))
ck('回读 增量 = 新增节字节数',
   len(b2) - len(raw) == len(SEC.encode('utf-8')), '%+d B' % (len(b2) - len(raw)))
W('')
W('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
if not DRY:
    io.open(os.path.join(HERE, 'write_common_r68.log'), 'w', encoding='utf-8',
            newline='\n').write('\n'.join(buf) + '\n')
sys.exit(0 if not fails else 1)
