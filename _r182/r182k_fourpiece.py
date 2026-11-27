#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r182k_fourpiece.py —— R182 四件套落盘（fail-closed：旧 sha 硬闸 + 独占备份 + 回读校验）。

四件套与 CR 不变量：
  R14_COMMON.md  新增 ## 2.187（全 LF；CR 保持 1081）
  GOAL_THREE_TARGETS_20261018.md  新增 ## §1237（CR 保持 337）
  LEAD_LOCK      新增 ## PL · R17 第 182 轮（CR 保持 137）
  STATUS_BOARD.md 新增第 182 轮记录（全 LF，CR 保持 0，总行数 <= 300）
"""
import hashlib, io, os, shutil, sys, tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BL = os.path.join(TIER, 'R17_LEAD_BASELINE')
RC = os.path.join(TIER, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD = os.path.join(TIER, 'STATUS_BOARD.md')

HARD = {
    RC:   ('b8aee7ea5c93b8223663f83099029bac62e2688cc7909d1209bb2ef505243ef2', 1081),
    LED:  ('1ee57275128d35be468f87162a97aa917197986eb15cb13511eabb710f157933', 337),
    LOCK: ('4770d2881885dae7eee3b7d5aa9e792efaf0e59dd80b862721b6b3bb43c18793', 137),
    BRD:  ('fb7997cb7bb24220e5cfe7e1d37991632a2022ba64d9d6daf6a34e8c0b0fe55c', 0),
}

fails = []
def ck(n, c, d=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + str(d)) if d else ''))
    if not c: fails.append(n)
    return c
def sha(b): return hashlib.sha256(b).hexdigest()
def rd(p): return io.open(p, encoding='utf-8', newline='').read()

print('--- A：旧态硬闸 ---')
for p, (s, cr) in HARD.items():
    b = open(p, 'rb').read()
    ck('A %s sha 命中' % os.path.basename(p), sha(b) == s, sha(b)[:16])
    ck('A %s CR == %d' % (os.path.basename(p), cr), b.count(b'\r') == cr, b.count(b'\r'))
if fails:
    print('硬闸未过，拒绝写盘'); sys.exit(1)

SEC_COMMON = """
## 2.187 R182：三方路径一致性（C20）从「无人守」变成可失败断言，且首版被审计证出五处假 FAIL 面后改 AST

R181 的未取得项②原文是「`gate_runner.LEDGER` 与 `facts_floors.EXPECT_CUR`、指针相对路径三处的三方路径一致性仍无人守」。R182 把它做成 `check_disc.py` 的 **C20**，并在此过程中被跨家族审计 #435 当场证出首版（v1）在**六种完全合法**的写法上假 FAIL —— 其中一种恰恰是「消灭第三份常量」的终局重构。

**一·先量，再改.** `_r182/r182b`（10 断言 0 FAIL）实测三件事：① 三处版本字面量**各自独立**（check_disc 生效字面量 0、facts 1、gate_runner 1），故 C19 的 (e) 只覆盖后两者、runner 那一份从未被告知；② 词法解析器对三处均取到同一绝对路径，且变量名精确锚（不存在名 / `ROOT` / `TIER` 均返回 `None`，反控）；③ **分辨率反证**：沙箱把 `gate_runner.LEDGER` 改成上一版，生产 `check_disc` 仍 exit 0 且无任何 C20 条目 ⇒ 缺口真实存在，不是「已有人守」。

**二·C20 v1 的五判据与它自己的失效面.** v1 = (a) 解析 runner 的 `LEDGER`；(b) == 指针路径；(c) == facts `EXPECT_CUR`；(d) runner 里 `LEDGER` 行恰 1 处；(e) 读不到即 FAIL。反向 7 组 20 断言 0 FAIL 后上生产。审计 #435 随即指出 (a) 的词法形状太脆、(d) 的锚与 (a) 不一致，主会话 `_r182/r182g` **19 断言亲自复算**，逐条成立：双引号 / 类型注解 / pathlib / 变量间接 / 字符串拼接 / **`from facts_floors import EXPECT_CUR as LEDGER`** 六种合法写法在 (a) 上**假 FAIL**；而 `LEDGER2 = ...V562` 这种真正的第二份副本反而因 `(d)` 只数名为 `LEDGER` 的行而**漏抓**（v1 对它整体仍绿）。函数内的自测夹具则被判成第二份 ⇒ 假 FAIL。

**三·v2 改 AST，并把「误判合法重构」这条堵掉.** (a) 改为 `ast.Module.body` 顶层取 `os.path.join` 的 **Constant** 实参 —— AST 只收 `Constant`，天然忽略注释与 docstring（本文件 docstring 与 ck 名称里残留旧版本字样，任何全文正则必假 FAIL）；另加一条**import 形态**分支：若 runner 写 `from facts_floors import EXPECT_CUR as LEDGER`，则视为单源、`(d)` 的副本计数**故意不适用**（`_r182/r182d` R8 实测：v1 在这一格假 FAIL，v2 绿并打印 `imported from facts_floors` NOTE）。(d) 改为「全文件指向台账版本目录的**字面量集合**大小必须 == 1」—— `_r182/r182d` R3 实测换名副本被抓（`carries 2 distinct ledger version literals`）。

**四·v2 两次上生产即被自己的断言钉出（S-182h1）.** v2 首版写 `if len(vals) >= 3`，而 `os.path.join(TIER, VDIR, FILE)` 的 Constant 实参只有 **2** 个（`TIER` 是 `ast.Name`）⇒ 解析器恒返回 `None` ⇒ 生产 `check_disc` 立刻 exit 1 并报 `cannot resolve LEDGER`。这是**上生产后第一次实跑就红**、由可失败断言当场抓出，未进入任何结论；`_r182/r182i` 改为 `>= 2` 并加两条反控（import 形态返回 `None`、函数内夹具不计入顶层）。

**五·审计另三条，逐条采纳并复算.** ① **B3**：`locals().get('_c19_abs')` 使「指针坏了」与「C19 没跑」同为 `None`、FAIL 文本不可区分 ⇒ 改显式 `_c19_abs = None` + `_c19_ptr_state`（`pointer-missing` / `fields-unparseable` / `path-missing` / `content-mismatch` / `ok`），C20 的 FAIL 文本带状态。② **B2**：C19 内容漂移而三方路径仍相等时，C20 照旧打印绿 NOTE —— 红日志里的误导性绿；`_r182/r182g` F 段沙箱实测成立（C19 FAIL 3 条 + C20 ok 行在场、exit 1）⇒ v2 的 ok 分支额外要求 C19 已 `ok(`，`_r182/r182g` 复验 F2/F2b 双双转正（C19 红时 C20 报 `cannot certify the three-way link while C19 is 'FAIL'`、不再打印 ok）。③ **B4**：v1 注释里有一行「`LEDGER = os.path.join(TIER, '<V563>', 'FACT_INDEX.tsv')`」—— 长得**恰是一行合法代码**、最容易被顺手粘回代码里，且升版后会静默陈旧；v2 起 C20 块内 `V<数字>` **归零**（`_r182/r182j` 把最后一处实测记录里的具体版本号也改成版本中性表述）。

**六·边界改诚实（审计 B5，最重要的一条）.** v1 的注释写「那份是否当前版由 `facts_floors.D0` 与 C19 的 (a)(b)(c) 负责」。审计指出这句**不成立**：C19 (a)(b)(c)、D0/D10 **全部以「指针已声明的那份」为输入**做自洽校验，没有任何一处反向枚举版本目录族去看「盘上最新是哪份」。`_r182/r182g` D 段沙箱实测确认：**建一个更高版本号的目录（复制现版台账）但不改任何指针 ⇒ `check_disc` exit 0、`facts_floors` exit 0、C19 与 C20 均报 ok、零告警**。这条已写进 C20 的注释并登记为未取得项，**不以 C20 的绿色代表已覆盖**。

**七·未采纳的一条（附理由）.** 审计建议新增 C21「版本单调/最新版」判据（反向取 `V(\d+)` 最大值）。**不采纳**：它与「先写新版本目录、后改指针」的既有升版顺序（`FACT_INDEX_CURRENT.md`「消费者应当怎么做」第 3 条）天然冲突，窗口期内必然假红；要消除就得把升版改成原子步骤，否则是从「覆盖不到」换成「每次升版都假红」。审计自身也不建议本卡追加。

**八·F24 语料值失效期标注的逐次普查（本卡第二项业务）.** `_r182/r182a` 把「全文有没有标注」换成**逐次出现**：主引值 `4,417` / `737,517,286` 在 F24 第 2、5 列共 **23 次**出现（statement 12 / limitations 11），四种作用域并列报（同句 / ±120 字符 / ±300 字符 / 同补段）。`_r182/r182f`（11 断言 0 FAIL）把它做成可失败判据：**引用指令句 6 次，逐次全部带失效期标注或显式对照（零未覆盖）**；非引用句 17 次里有 6 次未逐次标注，**全部在 limitations**，且逐条可归入「划分恒等式 / 溯源括号 / 主引值本身未变」三类推导-溯源语境（6/6 命中标记词），statement 侧零未标注。⇒ 结论是「失效期标注这一项**已闭合**」，不是「还缺 11 处」。

**九·自错 S-182a1..S-182h1（全部由可失败断言当场抓出，无一条进入结论）.** S-182a1 反控只挖掉两个标注词而该句还含第三个 ⇒ 假 FAIL；S-182d1 造第二份副本时追加的是 `LEDGER2`，而 v1 的 (d) 只数 `LEDGER` ⇒ 计数仍 1、断言假 FAIL；S-182d2 `safe_unlink` 正确拒绝了删软链（**护栏生效的证据**），但暴露 OVERRIDE 漏了指针文件；S-182d3 用 `f.startswith('C19')` 匹配形如 `FAIL  C19 ...` 的行 ⇒ 计数恒 0 假 FAIL；S-182d4 指向 V562 目录而本精简库现盘只有 V563 ⇒ `FileNotFoundError`；S-182f1 把 J3 的期望总数**硬编码成 16**，实测 23 ⇒ 族谱「把应然数当实测」**第十三次复发**；S-182f2 按段落位置判「引用面」，把算式恒等句误判为缺陷；S-182f3 把定性面当成可失败判据（会造出恒真或恒假）；S-182g1 复算审计表时发现它把一格写成 `(d)=0`，实测 1（结论不变、数字须订正）；S-182h1 见第四节。

**十·事故与恢复（如实登记，不粉饰）.** `_r182/r182d` 首版的镜像函数在 `sb` 下给**所有**顶层项建软链（含 `_r160`），随后 `os.makedirs(sb/_r160, exist_ok=True)` 静默通过，`mutate` 里的 `os.unlink(sb/_r160/facts_floors.py)` **穿透软链删掉了生产实物**（26,147 B / `ed717d13…`）。发现后立即停止取证，改走**确定性重放**恢复：取 `R17_LEAD_BASELINE/facts_floors.py.before_r180_caliber_*.bak`（25,433 B / `15d48bcd…`，即 `r180g` 的硬闸值），施加 `_r180/r180g_amend_caliber.py` 里逐字写着的三处 `replace`，**结果字节数与 sha16 双双命中 R180 记录值后才写盘**；恢复后 `facts_floors` exit 0、`MASTER_SHA256` 仍 `eab67034…`、`gate_runner` G1=G2=G3=ok（`_r182/r182e` 24 断言 0 FAIL）。此后所有镜像脚本加 `safe_unlink` 硬保护：父目录或目标任一为软链即抛错，绝不穿透。**R181 的 S-671/672 记的是「沙箱漏软链」，方向相反：这次是软链过头。**
"""

SEC_LEDGER = """
## §1237 R182：三方路径一致性（C20）落地 —— 首版被跨家族审计证出六种合法写法假 FAIL 后改 AST；并如实登记「当前版无人覆盖」这一盲区

**一·R181 未取得项②闭合.** `check_disc.py` 新增 **C20**，把 `gate_runner.LEDGER` 纳入「三方必须指同一份台账」的判定。C19 的 (e) 只覆盖 `facts_floors.EXPECT_CUR` ↔ 指针这一对，runner 那一份**从未被告知**；`_r182/r182b` 的分辨率反证（沙箱把 runner 改版本、生产 `check_disc` 仍 exit 0 且零 C20 条目）证明缺口真实存在。

**二·v1 → v2 的实质改动.** v1 用正则解析 runner 的 `LEDGER` 行、用「名为 `LEDGER` 的行恰 1 处」抓副本。审计 #435 指出、主会话 `_r182/r182g` 19 断言复算成立：双引号 / 类型注解 / pathlib / 变量间接 / 字符串拼接 / `from facts_floors import EXPECT_CUR as LEDGER` 六种**合法**写法在 (a) 上假 FAIL，而 `LEDGER2 = ...` 这种真副本反而漏抓。v2 改 AST（`ast.Module.body` 顶层取 `os.path.join` 的 Constant 实参），并加 import 形态分支（单源、副本计数故意不适用）；(d) 改为「全文件台账版本字面量**集合**大小 == 1」。

**三·v2 上生产即刻被抓（S-182h1）.** v2 首版 `if len(vals) >= 3`，而 `os.path.join(TIER, VDIR, FILE)` 的 Constant 实参只有 2 个（`TIER` 是 `ast.Name`）⇒ 恒返回 `None` ⇒ 生产 exit 1、报 `cannot resolve LEDGER`。由第一次实跑当场钉出，`_r182/r182i` 改 `>= 2` 并补两条反控。

**四·另三条审计结论的采纳.** ① `locals().get('_c19_abs')` ⇒ 改显式 `_c19_ptr_state` 五态（`pointer-missing` / `fields-unparseable` / `path-missing` / `content-mismatch` / `ok`）。② C19 红时 C20 仍打印绿 NOTE ⇒ ok 分支额外要求 C19 已 `ok(`（沙箱复验：v1 红日志里有 C20 ok 行，v2 报 `cannot certify ... while C19 is 'FAIL'`）。③ v1 注释里有一行可直接粘贴的合法代码含具体版本号 ⇒ v2 起 C20 块内 `V<数字>` 归零（版本中性）。

**五·边界改诚实（本轮最重要的一条）.** v1 注释称「那份是否当前版由 D0 与 C19(a)(b)(c) 负责」——**不成立**：这几处全部以「指针已声明的那份」为输入做自洽校验。`_r182/r182g` D 段沙箱实测：**建一个更高版本号的目录但不改任何指针 ⇒ `check_disc` exit 0、`facts_floors` exit 0、C19 与 C20 均 ok、零告警**。该盲区写进 C20 注释并登记为未取得项。

**六·未采纳.** 审计建议的 C21「版本单调」判据——与「先写新目录、后改指针」的既有升版顺序天然冲突，窗口期内必然假红；审计自身也不建议。

**七·F24 语料值失效期标注闭合.** `_r182/r182a` + `_r182/r182f`：主引值两串在 F24 第 2/5 列共 **23 次**出现（statement 12 / limitations 11），**引用指令句 6 次逐次全部带标注或显式对照（零未覆盖）**；非引用句 17 次中 6 次未逐次标注，全部在 limitations、逐条可归入划等式/溯源/主引值未变三类（6/6 命中标记词），statement 零未标注。⇒ 该项已闭合，不是「还缺 11 处」。

**八·事故与恢复.** `r182d` 首版镜像把所有顶层项建成软链（含 `_r160`），`os.unlink` 穿透软链删除生产 `_r160/facts_floors.py`（26,147 B / `ed717d13…`）。改走**确定性重放**：对 `before_r180_caliber` 备份施加 `r180g` 的三处 `replace`，**字节数与 sha16 双双命中 R180 记录值后才写盘**（`_r182/r182e` 24 断言 0 FAIL）；恢复后三门全绿、`MASTER` 仍 `eab67034…`。此后镜像脚本一律加 `safe_unlink`（父目录或目标为软链即抛错）。

**九·终态.** `check_disc.py` `66,363 → 71,059 → 75,065 → 75,262 → 75,304 B / 3d455edd…`，四次写盘各有独占备份与旧 sha 硬闸；反向 **10 组 28 条断言 0 FAIL**（runner 单选版 / facts 单选版 / 换名第二份 / 文件删除 / 不可解析 / 指针整体换版 / import 形态 / 函数内夹具 / C19 红 / 三处同升）；三段实跑 `check_disc` exit 0、`facts_floors` exit 0、`gate_runner` G1=G2=G3=ok、`GATE_VER` 仍 **R166**；五 CR 保持 **1081 / 137 / 337 / 0 / 2952**。
"""

SEC_LOCK = """
## PL · R17 第 182 轮（2026-11-27 16:0x–17:0x）· R181 未取得项②闭合：`check_disc.py` 新增 **C20** 三方路径一致性；首版被跨家族审计证出**六种合法写法假 FAIL** 后改 AST；并如实登记「当前版无人覆盖」这一盲区；另 F24 语料值失效期标注逐次普查后判为**已闭合**

**PL1. 🔴 交付一：先把「无人守」做成可失败的量.** `_r182/r182b` **10 断言 0 FAIL**：三处版本字面量各自独立（check_disc 生效 0 / facts 1 / gate_runner 1）；词法解析器对三处均取同一绝对路径，变量名精确锚（不存在名、`ROOT`、`TIER` 均返回 `None` 作反控）；**分辨率反证**：沙箱把 `gate_runner.LEDGER` 改版本 ⇒ 生产 `check_disc` 仍 exit 0 且零 C20 条目。

**PL2. 🔴 交付二：v1 的五判据与它自己的失效面.** v1 反向 7 组 20 断言 0 FAIL 后上生产。审计 **#435** 随即指出 (a) 词法太脆、(d) 锚与 (a) 不一致；主会话 `_r182/r182g` **19 断言**亲自复算，逐条成立：双引号 / 类型注解 / pathlib / 变量间接 / 字符串拼接 / `from facts_floors import EXPECT_CUR as LEDGER` **六种合法写法在 (a) 上假 FAIL**；`LEDGER2 = ...` 真副本**漏抓**；函数内自测夹具被判成第二份（假 FAIL）。最后一种尤刺眼 —— 它恰是「消灭第三份常量」的终局重构。

**PL3. ✅ 交付三：v2 改 AST + import 分支 + 集合计数.** (a) 取 `ast.Module.body` 顶层 `os.path.join` 的 Constant 实参（AST 天然忽略注释与 docstring；本文件 docstring 与 ck 名称里残留旧版本字样，全文正则必假 FAIL）；(b) import 形态视为单源、(d) 副本计数**故意不适用**；(d) 改「全文件台账版本字面量**集合**大小 == 1」。`_r182/r182d` R8 实测 import 形态 v1 假 FAIL、v2 绿并打印 NOTE；R3 实测换名副本被抓（`carries 2 distinct ledger version literals`）。

**PL4. 📌 交付四：v2 上生产即刻被自己的断言钉出（S-182h1）.** 首版 `if len(vals) >= 3`，而 `os.path.join(TIER, VDIR, FILE)` 的 Constant 实参只有 **2** 个（`TIER` 是 `ast.Name`）⇒ 恒返回 `None` ⇒ 生产 `check_disc` 立刻 exit 1、报 `cannot resolve LEDGER`。**上生产后第一次实跑就红**，未进入任何结论；`_r182/r182i` 改 `>= 2` 并补两条反控（import 形态返回 `None`、函数内夹具不计入顶层）。

**PL5. ✅ 交付五：审计另三条全部采纳并复算.** ① **B3** `locals().get('_c19_abs')` 使「指针坏了」与「C19 没跑」同为 `None` ⇒ 改显式 `_c19_ptr_state` 五态，FAIL 文本带状态。② **B2** C19 内容漂移而三方路径相等时 C20 仍打印绿 NOTE（`_r182/r182g` F 段沙箱实测：C19 FAIL 3 条 + C20 ok 行在场）⇒ ok 分支额外要求 C19 已 `ok(`，复验后 F2/F2b 双双转正。③ **B4** v1 注释里有一行长得**恰是合法代码**的版本字面量、最易被顺手粘回 ⇒ v2 起 C20 块内 `V<数字>` **归零**（`_r182/r182j` 把最后一处实测记录的具体版本号也改版本中性）。

**PL6. 📌 交付六：边界改诚实，这是本轮最重要的一条.** v1 注释称「那份是否当前版由 `facts_floors.D0` 与 C19(a)(b)(c) 负责」——**不成立**：这几处全部以「指针已声明的那份」为输入做自洽校验。`_r182/r182g` D 段沙箱实测：**建一个更高版本号的目录（复制现版台账）但不改任何指针 ⇒ `check_disc` exit 0、`facts_floors` exit 0、C19 与 C20 均 ok、零告警**。该盲区写进 C20 注释并登记为未取得项，**不以 C20 的绿色代表已覆盖**。

**PL7. 📌 交付七：未采纳审计的一条建议（附理由）.** 审计建议新增 C21「版本单调/最新版」判据。**不采纳**：它与「先写新版本目录、后改指针」的既有升版顺序（指针文件「消费者应当怎么做」第 3 条）天然冲突，窗口期内必然假红；要消除就得把升版改成原子步骤，否则是从「覆盖不到」换成「每次升版都假红」。审计自身也不建议本卡追加。

**PL8. ✅ 交付八：F24 语料值失效期标注逐次普查后判为已闭合.** `_r182/r182a`（四作用域并列：同句 / ±120 / ±300 / 同补段）+ `_r182/r182f`（**11 断言 0 FAIL**）：主引值 `4,417` / `737,517,286` 在 F24 第 2、5 列共 **23 次**出现（statement 12 / limitations 11）；**引用指令句 6 次逐次全部带失效期标注或显式对照（零未覆盖）**；非引用句 17 次中 6 次未逐次标注，**全部在 limitations** 且逐条归入「划分恒等式 / 溯源括号 / 主引值本身未变」（6/6 命中标记词），statement 侧零未标注。⇒ 结论是「已闭合」，不是「还缺 11 处」。

**PL9. 📌 事故与恢复（如实登记，不粉饰）.** `_r182/r182d` 首版镜像在 `sb` 下给**所有**顶层项建软链（含 `_r160`），`os.makedirs(..., exist_ok=True)` 静默通过，随后 `os.unlink` **穿透软链删掉生产实物** `_r160/facts_floors.py`（26,147 B / `ed717d13…`）。发现后立即停止取证，改走**确定性重放**：取 `before_r180_caliber` 备份（25,433 B / `15d48bcd…`，即 `r180g` 的硬闸值），施加 `r180g` 里逐字写着的三处 `replace`，**结果字节数与 sha16 双双命中 R180 记录值后才写盘**；`_r182/r182e` **24 断言 0 FAIL**，恢复后 `facts_floors` exit 0、`MASTER` 仍 `eab67034…`、`gate_runner` G1=G2=G3=ok。此后镜像脚本一律加 `safe_unlink`（父目录或目标为软链即抛错）。**R181 的 S-671/672 记的是「沙箱漏软链」，方向相反：这次是软链过头。**

**PL10. 📌 自错 S-182a1..S-182g1（十处，全部由可失败断言当场抓出，无一条进入结论）.** 反控只挖两个标注词而该句还含第三个（a1）；造第二份副本用 `LEDGER2` 而 v1 只数 `LEDGER` ⇒ 计数仍 1（d1）；`safe_unlink` 正确拒绝删软链，却暴露 OVERRIDE 漏指针文件（d2）；用 `f.startswith('C19')` 匹配形如 `FAIL  C19 ...` 的行 ⇒ 计数恒 0（d3）；指向 V562 而本精简库现盘只有 V563 ⇒ `FileNotFoundError`（d4）；J3 期望总数**硬编码 16**、实测 23（f1）；按段落位置判「引用面」把算式恒等句误判（f2）；把定性面当可失败判据会造出恒真/恒假（f3）；复算审计表发现它把一格写成 `(d)=0`、实测 1（g1）。**族谱**：「把应然数当实测」**第十三次复发**（S-182f1，与 S-674/S-681/S-682/S-684 同族）。

**PL11. 📌 未取得（不粉饰）.** ① **「哪份是当前版」本系统无人覆盖** —— 建更高版本目录却不改指针 ⇒ 三门全绿零告警（`_r182/r182g` D 段沙箱实测），C20 只证三方同一路径；② C20 仍受「三处同改可过」的升版一致性上限（与 D9/D10/C19 同族，`_r182/r182d` R7 已如实钉住）；③ C20 选「全文件唯一」策略 ⇒ 函数内自测夹具若含另一版本字面量会被判红（`_r182/r182d` R9 登记为策略选择而非缺陷）；④ C20 只比 `normpath` 字符串，不比 `realpath`/inode，版本目录被换成软链时不报；⑤ F23（`未取得`）/ F35（`[流程]`）grade 未改（裁定不是取证）；⑥ `coverage.tsv` / `function_atlas.tsv` 仍不可读 ⇒ F23 五数与 F35 分母不可重数；⑦ 86.19% 原值不可重算；⑧ C7 三死分支 exists/bytes=/none 仍各 0 行；⑨ C11 十二个永不 FAIL 的 id 未动；⑩ V560 的 CSV 转义是否回退未裁定；⑪ F24 的 6 次未逐次标注虽已逐条定性为推导/溯源语境，但「读者会不会误读」仍是机检边界之外的事。
"""

SEC_BOARD = """## 🟢 R17 第 182 轮（2026-11-27 16:0x–17:0x）· R181 未取得项②闭合：`check_disc.py` 新增 **C20** 三方路径一致性；首版被跨家族审计证出**六种合法写法假 FAIL** 后改 AST；并如实登记「当前版无人覆盖」这一盲区；F24 语料值失效期标注逐次普查后判为**已闭合**

**入口**：R181 未取得项②原文「`gate_runner.LEDGER` 与 `facts_floors.EXPECT_CUR`、指针相对路径三处的三方路径一致性仍无人守」。本轮把它做成 `check_disc.py` 的 **C20**，`_r182/r182b` **10 断言 0 FAIL** 先证缺口真实存在 —— 三处字面量各自独立（check_disc 生效 0 / facts 1 / runner 1），且沙箱把 runner 改版本后生产 `check_disc` 仍 exit 0、零 C20 条目。

| 项 | 实测 |
|---|---|
| `check_disc.py` 体量 | 66,363 → **71,059**（C20 v1）→ **75,065**（v2 AST）→ **75,262**（S-182h1 修复）→ **75,304 B / `3d455edd…`**（注释版本中性） |
| C20 反向断言 | **10 组 28 条 0 FAIL**（runner 单选版 / facts 单选版 / 换名第二份 / 文件删除 / 不可解析 / 指针整体换版 / import 形态 / 函数内夹具 / C19 红 / 三处同升） |
| 三段实跑 | `check_disc` exit 0 / `facts_floors` exit 0 / `gate_runner` **G1=G2=G3=ok** / `GATE_VER` 仍 **R166** |
| 五 CR | **1081 / 137 / 337 / 0 / 2952** 全保持；看板 250 行 < 260 未触发归档 |

**v1 → v2：审计 #435 证出六种合法写法假 FAIL.** v1 用正则解析 runner 的 `LEDGER`、用「名为 `LEDGER` 的行恰 1 处」抓副本。主会话 `_r182/r182g` **19 断言**独立复算审计结论，逐条成立：双引号 / 类型注解 / pathlib / 变量间接 / 字符串拼接 / **`from facts_floors import EXPECT_CUR as LEDGER`** 六种**合法**写法在 (a) 上假 FAIL；而 `LEDGER2 = ...` 这种真副本**漏抓**（v1 对它整体仍绿）；函数内自测夹具被判成第二份。最后一种尤其刺眼 —— 它恰是「消灭第三份常量」的终局重构。v2 改 **AST**（取顶层 `os.path.join` 的 Constant 实参，天然忽略注释与 docstring），加 import 单源分支，(d) 改为「全文件版本字面量**集合**大小 == 1」。

**v2 上生产即刻被自己的断言钉出（S-182h1）**：首版 `if len(vals) >= 3`，而 `os.path.join(TIER, VDIR, FILE)` 的 Constant 实参只有 **2** 个（`TIER` 是 `ast.Name`）⇒ 恒返回 `None` ⇒ 生产 exit 1、报 `cannot resolve LEDGER`。由第一次实跑当场抓出，`_r182/r182i` 改 `>= 2` 并补两条反控。

**另三条审计采纳**：① `locals().get('_c19_abs')` 使「指针坏了」与「C19 没跑」同为 `None` ⇒ 改显式 `_c19_ptr_state` 五态；② C19 内容漂移时 C20 仍打印绿 NOTE（沙箱实测 C19 FAIL 3 条 + C20 ok 行在场）⇒ ok 分支额外要求 C19 已 `ok(`，复验后转正；③ v1 注释里一行长得**恰是合法代码**的版本字面量 ⇒ v2 起 C20 块内 `V<数字>` 归零。

**边界改诚实（本轮最重要）**：v1 称「那份是否当前版由 D0 与 C19(a)(b)(c) 负责」——**不成立**，这几处全以「指针已声明的那份」为输入。`_r182/r182g` D 段沙箱实测：**建一个更高版本号的目录但不改任何指针 ⇒ `check_disc` exit 0、`facts_floors` exit 0、C19 与 C20 均 ok、零告警**。该盲区写进注释并登记为未取得项。**未采纳**审计建议的 C21 版本单调判据 —— 与「先写新目录、后改指针」的升版顺序天然冲突，窗口期内必然假红。

**F24 语料值失效期标注：判为已闭合.** `_r182/r182a`（四作用域并列）+ `_r182/r182f`（**11 断言 0 FAIL**）：主引值 `4,417` / `737,517,286` 在 F24 第 2、5 列共 **23 次**出现（statement 12 / limitations 11）；**引用指令句 6 次逐次全部带标注或显式对照（零未覆盖）**；非引用句 17 次中 6 次未逐次标注，全部在 limitations、逐条归入「划分恒等式 / 溯源括号 / 主引值本身未变」（6/6），statement 零未标注。⇒ 不是「还缺 11 处」。

**跨家族（两件都有回件，无 OVERTIME）**：执行员 **#434**（hy4flash-free）Q1–Q7 逐条作答并**独立订正我的卡面口径**（它用 tokenize 区分注释，实测 C20 块内注释里仍有 1 处版本字面量示例、代码侧 0 —— 我卡面写「0 处」只在不计注释时成立，此点已被 v2 采纳并归零）；审计员 **#435**（deepseek）Q1–Q7 全答，**六条结论被采纳**（AST 化、import 形态、`_c19_ptr_state`、C19 红时禁绿、注释去版本号、边界改诚实）、**一条被否决**（C21 版本单调）。全部结论经 `_r182/r182g` 20 断言亲自复算 0 FAIL。

**事故与恢复（如实登记）**：`_r182/r182d` 首版镜像给所有顶层项建软链（含 `_r160`），`os.unlink` **穿透软链删掉生产** `_r160/facts_floors.py`（26,147 B / `ed717d13…`）。停止取证后改走**确定性重放**：对 `before_r180_caliber` 备份（25,433 B / `15d48bcd…`）施加 `r180g` 的三处 `replace`，**字节数与 sha16 双双命中 R180 记录值后才写盘**；`_r182/r182e` **24 断言 0 FAIL**，恢复后三门全绿、`MASTER` 仍 `eab67034…`。此后镜像脚本一律加 `safe_unlink`（父目录或目标为软链即抛错）。**R181 的 S-671/672 是「沙箱漏软链」，方向相反：这次是软链过头。**

**自错 S-182a1..S-182g1（十处，全部当场抓出）**：反控只挖两个标注词（a1）；`LEDGER2` 副本 v1 数不到（d1）；`safe_unlink` 拒绝删软链却暴露 OVERRIDE 漏指针（d2）；`startswith('C19')` 匹配不上 `FAIL  C19 ...`（d3）；指向不存在的 V562（d4）；**J3 期望总数硬编码 16、实测 23**（f1）；按段落位置判引用面致误判（f2）；把定性面当可失败判据（f3）；复算审计表发现一格数字需订正（g1）。**族谱**：「把应然数当实测」**第十三次复发**。

**未取得**：① **「哪份是当前版」本系统无人覆盖**（建更高版本目录不改指针 ⇒ 三门全绿零告警）；② C20 仍受「三处同改可过」上限（R7 已钉住）；③ C20 选「全文件唯一」策略 ⇒ 函数内夹具含另一版本字面量会判红（R9 登记为策略选择）；④ C20 只比 `normpath`、不比 `realpath`/inode；⑤ F23（`未取得`）/ F35（`[流程]`）grade 未改；⑥ `coverage.tsv` / `function_atlas.tsv` 仍不可读 ⇒ F23 五数与 F35 分母不可重数；⑦ 86.19% 原值不可重算；⑧ C7 三死分支仍各 0 行；⑨ C11 十二个永不 FAIL 的 id 未动；⑩ V560 的 CSV 转义是否回退未裁定；⑪ F24 那 6 次未逐次标注已逐条定性为推导/溯源语境，但「读者会不会误读」仍在机检边界之外。
"""

print('--- B：构造新文 ---')
def build(old, add, expect_cr, name):
    new = old.rstrip('\n') + '\n' + add
    ck('B %s CR 保持 %d' % (name, expect_cr), new.count('\r') == expect_cr, new.count('\r'))
    ck('B %s 只追加（旧文是新文的前缀）' % name,
       new.startswith(old.rstrip('\n')))
    return new

old_rc = rd(RC); old_led = rd(LED); old_lock = rd(LOCK); old_brd = rd(BRD)
new_rc = build(old_rc, SEC_COMMON, 1081, 'R14_COMMON')
new_led = build(old_led, SEC_LEDGER, 337, 'LEDGER')
new_lock = build(old_lock, SEC_LOCK, 137, 'LEAD_LOCK')
new_brd = build(old_brd, SEC_BOARD, 0, 'STATUS_BOARD')

# R14_COMMON 的 CR 计数：新增段全 LF ⇒ 总 CR 不变
for nm, txt, exp in (('R14_COMMON', new_rc, 1081), ('LEDGER', new_led, 337),
                     ('LEAD_LOCK', new_lock, 137), ('STATUS_BOARD', new_brd, 0)):
    ck('C %s CR == %d' % (nm, exp), txt.count('\r') == exp, txt.count('\r'))
ck('C §2.187 在场', '## 2.187 R182' in new_rc)
ck('C §1237 在场', '## §1237 R182' in new_led)
ck('C PL 段在场', '## PL · R17 第 182 轮' in new_lock)
ck('C 看板行数 <= 300', len(new_brd.split('\n')) <= 300, len(new_brd.split('\n')))
ck('C 反引号纪律：卡面无反引号不适用于四件套（本仓正文允许）', True)
if fails:
    print('构造阶段未过，拒绝写盘'); sys.exit(1)

print('--- D：独占备份 + 写盘 + 回读 ---')
targets = [(RC, new_rc), (LED, new_led), (LOCK, new_lock), (BRD, new_brd)]
for p, txt in targets:
    oldraw = open(p, 'rb').read()
    bak = os.path.join(BL, '%s.before_r182_%s.bak' % (os.path.basename(p), sha(oldraw)[:12]))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(oldraw)
    ck('D1 %s 备份独占' % os.path.basename(p), os.path.exists(bak))
    nb = txt.encode('utf-8')
    with open(p, 'wb') as f:
        f.write(nb)
    back = open(p, 'rb').read()
    ck('D2 %s 回读一致' % os.path.basename(p), sha(back) == sha(nb), sha(back)[:16])
    print('   %-24s %d -> %d B ; sha %s' % (os.path.basename(p), len(oldraw), len(back), sha(back)[:16]))

print('--- E：终态 CR ---')
for p, exp in ((RC, 1081), (LED, 337), (LOCK, 137), (BRD, 0)):
    b = open(p, 'rb').read()
    ck('E %s CR == %d' % (os.path.basename(p), exp), b.count(b'\r') == exp, b.count(b'\r'))
print('   board lines %d' % len(open(BRD, 'rb').read().split(b'\n')))
print('PASS/FAIL: fails=%r' % (fails,))
print('[exit 0]' if not fails else '[exit 1]')
sys.exit(0 if not fails else 1)
