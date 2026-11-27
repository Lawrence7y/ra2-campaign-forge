#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R148 I：看板追加第 148 轮段。写前 129 行 + 本段 <= 300，CR 保持 0。"""
import hashlib, io, json, os, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
BRD = os.path.join(R14, 'STATUS_BOARD.md')
fails = []


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


SEC = """## 🟢 R17 第 148 轮（2026-11-27 03:2x–04:0x）· FACT_INDEX 四条正文全部收口（v5.39 → v5.40）；F35 的「缺一手权威」是伪命题已撤回；F23 的记录数被我差点改错 —— 实测是**两个口径**不是错数

> 本轮不做新测量，做「正文口径收口」：四条 R137 看板第九节列出的待办一次落定。最值钱的一条不是写进去什么，而是**我差点删掉一个正确的数**。

### 一 · 落盘：FACT_INDEX v5.40

| 项 | 值 |
|---|---:|
| 字节 | 83,637 → **88,786**（+5,149） |
| sha256 | `ec0a63a4…` → **`fabd1e57…`** |
| 改动行 | **4**（F23 / F24 / F29 / F35 的 `statement` 列） |
| 未动列 | `fact_id` / `grade` / `evidence_paths` / `limitations` **逐字节** |
| 其余 50 行 | **逐字节相同**，全 LF，54 数据行不变 |

### 二 · F23：三条一起补

1. 分解 **6 + 2 + 3 = 11 ≠ 12**（差 **1 行无归属**）；换读法 **6+2+3+3 = 14 > 12** ⇒ **两读法都不闭合**、缺口对读法不敏感。
2. 全部计数（458 / 291 / 293 / 1,196 / 12 / 2 / 9 与分母 1,654）依赖 `coverage.tsv`（4,147,334 B），该件**已失**（文件名 **0** 命中、按字节 **0** 命中、三目录不在）⇒ 只能证**算术闭合**。
3. **记录数有两个口径**：basename 精确 = **18**（主份 1 + 备份 17）；路径含 `/COVERAGE/` = **4**（主份 1 + `_hygiene` 下 COVERAGE 子目录 3）。**R138 原文的「4 条」是后一口径、逐位可复现。**

### 三 · F35：撤一句、拆两条

- **「缺一手权威」已撤回（是伪命题）**：`strict_panel.py:78` 的 `if "[未证]" not in sem:` 就是**带方括号字面**的一手代码权威，嵌在 `:76` 的 `if grade == "[已证]":` 内；全文 `[未证]` 恰 **2 次**（`:14` 散文 + `:78` 代码）、代码形态恰 **1 次**。
- 另 3 脚本同判据但**写法不同**（`precheck.py:60` 用 `not in sem`；`simulate.py:72`、`verify.py:83` 用 `not in r[3]`）；四者共用同一 `PROJ` 与同一对输入 ⇒ **同血缘克隆，只能互证判据串、不能当交叉验证**。`merge_panel.py` **不含**该判据（反控 0 命中）。
- **拆两条**：① 定义**在盘**；② 失联的是**两个输入**（`COVERAGE/coverage.tsv`、`next_re_20261112_r10/W130_atlas/function_atlas.tsv`）。
- **F35 与 F23 不再并列**：F35 evidence **5 项只 1 项失联** ⇒ 已不是整行失联项；F23 evidence **2 项全失联**且 `grade` 仍是 `[已证]` —— **本轮只登记，改 grade 须单独一卡**。

### 四 · F24：撤数、保判据、标失效期

- **86.19% 撤下**（R136 实测 **99.992% = 1,392,481/1,392,592** 有字节对应）；`bounds` **仍剔**，依据改为**结构判据「单列地址、无可回原址复核的第二列」** —— **数字错、方向对，分开处理**。
- **4,417 件 / 737,517,286 B 是 11-22 快照**。按 rel 相对 `lead/` 解析：**存在 65 件 / 44,470,975 B**（**同字节 64 件 / 26,846,620 B**；差 1 件 = `a2_sites.json`，+16,711,118 B 恰为被剔 bounds 段）、**不存在 4,352 件 / 709,757,429 B**。
- 两式闭合：清单(65) 27,759,857 + 清单(4,352) 709,757,429 = **737,517,286**；现盘 44,470,975 − 16,711,118 + 709,757,429 = **737,517,286**。
- 反控：rel 拼到**仓库根**得 **0 件 / 0 B** ⇒ 引用必须带「相对 `lead/` 根解析」。

### 五 · F29：四处作用域从 limitations 提进正文

「两份拷贝」= `.text` 全镜像 **80 次**中的两份（逐节切片：`.text` 80 / 其它节 0 / 负控改 1 字节得 0）；`idx=62` = **DLL 内 0-based**（另有全局 0-based 63、全局 1-based 64）；「40」是**字节串出现次数**、**不是 40 个桩函数**；「40 次桩体」与「63/77」**非因果**（77 mod 40 = 37）。

### 六 · 规则 D：两家独立，主会话 27 断言复算

- **#331（hy4, exec）succeeded**：七项与主会话逐项相同，另给 5 个文件 sha256。
- **#332（deepseek, audit）succeeded**：五条主张三条成立、两条部分成立。**两条批评经复算成立**：① 我原写「两个父目录亦不存在」指的是 **F35 输入侧**，措辞会被读成连 `next_re_20261117_r14/` 都不存在 ⇒ 已改为点名两个具体目录；② **4,147,334 B 的字节数与 sha 在现盘有 215 个文件台账**（`_r67/unique_content_4417.tsv:1022` = `c2ee063f…`），真正不可重数的是**计数本身**，不是字节数 ⇒ 正文已分层。

### 七 · 自错 S-339..S-344（六条）

- **S-342（最危险）**：我一开始把 F23「4 条记录」判成**原文错**，实测是**口径不同**（R138 的 4 条逐位可复现）—— **差点改掉一个正确的数**。
- **S-341**：用**子串**筛 `coverage.tsv` 得 41 行，据此断言「4 行」假 FAIL；改 `basename ==` 后得 18 行 ⇒ 顺带挖出双口径。
- **S-339**：判据串写死 `not in sem`，漏了 `not in r[3]` 形态 ⇒ **2 条假 FAIL**。
- **S-340**：闭合式漏差异件修正项，得 754,228,404 ≠ 737,517,286。
- **S-343**：`r148f` 重跑生成**第二个 .bak**（DST 字节相同）—— 备份冗余无害，但「重跑无副作用」这个假设不成立。
- **S-344**：沿用 R147「写前 210 < 260 不归档」的**记忆**，实测写前 **286 ≥ 260** 且 `286 + 34 = 320 > 300` ⇒ **必须归档**。

### 八 · 门禁与归档

按 R138F 判据（**写前行数 + 本轮追加 ≤ 300 才免归档**）归档最早两段（144 / 145）：看板 **286 → 129 行**，`BOARD_ARCHIVE` CR 保持 **2952**（`r148g` 16 断言 0 FAIL）。四件套 CR：R14_COMMON **1081**、台账 **337**、LEAD_LOCK **137**、看板 **0**。

### 九 · 下轮优先（禁写元审计待办）

1. **F23 的 `grade` 裁定**：`[已证]` 与「evidence 2/2 全失联」并存 —— 要么补在盘证据，要么降级，**须单独一卡 + 门禁回归**。
2. **F24 的 65/64/4,352 三桶漂移**：现为当前盘读数，需给一个「测量时刻 + 清单 sha」的可重跑入口。
3. **F29 的 6 个桩体作用域**：R135 审计自报的「6 个不同桩体」是否该进正文，需先证明它是可复算量（现判定为中间数字，未采用）。
4. 动态项（虚表运行期读取、3,805 处寄存器 call/jmp 落点、35 个静态容器运行期值、窗口表 r66 后快照、0x8871E0 首赋与释放时刻）留 `win-main`。
5. 已判死线继续禁投：具名池、无名池、direct-only(D2)、D4结构性无、静态④、动态④、证据指针791行、D-48攻②-b。

"""

b0 = open(BRD, 'rb').read()
ck('1 写前 CR == 0', b0.count(b'\r') == 0, b0.count(b'\r'))
ck('2 写前 129 行', b0.count(b'\n') == 129, b0.count(b'\n'))
ck('3 写前 2 段', sum(1 for l in b0.decode('utf-8').split('\n') if l.startswith('## ')) == 2,
   sum(1 for l in b0.decode('utf-8').split('\n') if l.startswith('## ')))
ck('4 本段不含 148 轮标题（幂等）', '第 148 轮' not in b0.decode('utf-8'))
ck('5 本段不含 CR', '\r' not in SEC, SEC.count('\r'))
add = SEC.encode('utf-8')
b1 = b0 + add
n_after = b1.count(b'\n')
ck('6 写后行数 <= 300', n_after <= 300, n_after)

bakp = os.path.join(BASE, 'STATUS_BOARD.md.before_R148_board_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
fd = os.open(bakp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(b0)
ck('7 备份 wx 且逐字节相同', open(bakp, 'rb').read() == b0, os.path.basename(bakp))

with open(BRD, 'wb') as f:
    f.write(b1)
b2 = open(BRD, 'rb').read()
ck('8 回读逐字节相同', b2 == b1)
ck('9 回读 CR == 0', b2.count(b'\r') == 0, b2.count(b'\r'))
ck('10 回读行数 == 写前 + 追加', n_after == b0.count(b'\n') + add.count(b'\n'),
   (b0.count(b'\n'), n_after, add.count(b'\n')))
s2 = b2.decode('utf-8')
ck('11 第 148 轮标题恰 1 次', s2.count('## 🟢 R17 第 148 轮') == 1, s2.count('## 🟢 R17 第 148 轮'))
ck('12 第 146/147 轮各恰 1 次',
   s2.count('## 🟢 R17 第 146 轮') == 1 and s2.count('## 🟢 R17 第 147 轮') == 1)
ck('13 共 3 段', sum(1 for l in s2.split('\n') if l.startswith('## ')) == 3,
   sum(1 for l in s2.split('\n') if l.startswith('## ')))
NEED = ['88,786', 'fabd1e57', '18', '4 条', '99.992', '44,470,975', '709,757,429',
        'strict_panel.py:78', '同血缘克隆', '63/77', 'S-342']
for s in NEED:
    ck('14 含关键串 %r' % s, s in s2[s2.find('## 🟢 R17 第 148 轮'):])

print('\n看板 %d -> %d 行；sha %s' % (b0.count(b'\n'), n_after, hashlib.sha256(b2).hexdigest()[:16]))
print('=== FAILS: %d ===' % len(fails))
for f in fails:
    print('  ' + f)
json.dump(dict(fails=fails, lines=n_after, cr=b2.count(b'\r'),
               sha=hashlib.sha256(b2).hexdigest()),
          open(os.path.join(ROOT, '_r148', 'r148i_board.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
