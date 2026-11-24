# DISAGREE · W41 与任务书 / 前序卡片措辞的出入与取舍

> 分级：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` / `[待运行验证]`
> 本文件只记录**措辞校正、语义取舍、刻意的边界收窄/放宽**，不粉饰结果。
> 全部结论均为离线文件系统层面；**不涉及真机引擎行为**（归 W40）。

---

## 1 · 「只允许基于官方基底克隆这一条路径」——实现里多了一条「就地更新」分支

任务书需求 1 末句：「更推荐：**只允许"基于官方基底克隆"这一条路径**」。

`[本次读码]` v12 的 `_emit_csf_artifacts()` 实际有三条分支：

| 条件 | 行为 |
|---|---|
| `--csf-base B` 给出 | 读 B、`assert_complete_csf(B)`、克隆到 `--csf-out`（覆盖） |
| 无 base、`--csf-out` **已存在** | `read_csf(--csf-out, strict=True)` + `assert_complete_csf(...)`，**就地追加**（不覆盖基底） |
| 无 base、`--csf-out` **不存在** | 克隆**内置**官方 `RA2MD.OFFICIAL.CSF` |

「就地更新」看起来不是「克隆」，但**不是对约束的放松**：它要求该现有文件
**本身已通过完整守卫**（5,211 官方标签齐全、v3、魔数/计数/值类型全对），
所以它在语义上等价于「一个已存在的完整官方基底克隆」。真正的从零/最小 CSF
路径（`create_if_missing=True`）**已彻底删除**。

**为什么必须保留这条分支（硬约束）**：`[本次读码]` 继承的 51 例里
`CSF5` 的 CLI 子用例是 `--csf-out <已存在的坏魔数文件>`（无 base），
期望 rc=1 + `bad CSF magic` / `CSF emission failed` + **原文件逐字节未动**。
若按「一律用内置基底覆盖」实现，会先把坏文件覆盖成官方克隆，直接打断
`CSF5: CLI failure leaves corrupt file untouched`，且 rc 变成 0。
`[本次实测]` v12 走「就地更新」分支 → `read_csf(strict=True)` 先在坏魔数上
抛错 → 零写入 → `CSF5` 5/5 判据仍全过（见 `out/CSF5.log`）。

⇒ 结论：约束的**实质**（不允许最小/部分 CSF 成为产物）完全满足；
「一条路径」的**字面**被解释为「任何产物都必须等价于完整官方基底克隆」。

---

## 2 · 「默认拒绝」被实现成「永不释放」——按 W34 既有语义的更严读法

任务书需求 2：「若游戏目录**已有非我方** `ra2md.csf`，按既有语义判
**definite preflight conflict**，默认拒绝」。

`[本次读码]` 字面「默认拒绝」暗示存在 `--allow-content-conflict` 这个
唯一逃生口（W34 对**普通** definite conflict 的语义确实如此）。但 v12 把
`ra2md.csf` 的冲突与 `MAPSELMD.INI` 并列进 `csf_conflicts`，
在 `install_package()` 里**无条件** `raise InstallBlocked`，即
**`--allow-content-conflict` 也不释放**。

**依据**：`[本次读码]` W34 为「散装 WHOLE-FILE 覆盖」立的「既有语义」
正是 `mapsel_conflicts` = **never-releasable**（`install.py:1864-1869`
注释 + MS6g 用例）。任务书用的是「**按既有语义**判 definite preflight
conflict」，所以以 W34 的 never-releasable 为准，而不是普通 releasable
conflict。

**风险权衡** `[静态推断]`：一个非我方散装 `ra2md.csf` 完全可能是**部分/最小**
CSF —— 放行覆盖虽然会先备份，但 `--allow-content-conflict` 的语义是
「用户知道自己在覆盖」，而 W29 的结论是「散装部分 CSF ⇒ 引擎 `" FSC"`
检查失败 ⇒ 启动失败」，不是单纯的内容覆盖。放行一个逃生口在此处收益低、
风险高。故取更严读法。

`[本次实测]` `CSF_INST3g` 明确断言 `--allow-content-conflict` 仍 rc=1 且
游戏目录 `sha_tree` 零变化；`CSF_INST3i` 对照「无散装 csf 时安装成功」。
若后续裁决要求「可释放」，改动点只有 `install.py` 的
`if plan.get("csf_conflicts")` 一处 + 相应回归断言。

---

## 3 · W38 CRITICAL 标的是 `csf.py` 内部行，守卫却落在 `builder.py`

`[转引]` W38 `WRITE_ENTRY_AUDIT.tsv:18-22` 把
`csf.py:410`（`parent.mkdir`）/ `:416`（stage）/ `:417`（`os.replace`）
/ `:475`（`append_or_set_label`）标为 **CRITICAL / NO-IDENTITY / no_guard**，
`:11-13` 把 `builder.py:434-437` 与 `cli.py:140-146`（原样传参）标 CRITICAL。

`[本次读码]` v12 的**路径归属/身份判定**放在
`builder._csf_out_ownership_guard()`（在 `build()` 第一个文件系统写之前
调用），而 **没有**塞进 `csf.write_csf()` 内部。

**为什么**：`csf.py` 是纯格式读写原语，**没有「游戏目录」的概念**
（它不知道 `gamemd.exe`、不知道 `--install`、不知道 install 的
`_dest_safety_error` 别名门）。把 install 级路径身份硬塞进低层 CSF 写入
会造成分层倒置，且会打断 W30 的 `CSF1/CSF3/CSF4`（它们把最小 CSF 写到
sandbox 临时路径，本就不是游戏目录）。

v12 对 W38 各行的实际处置：

| W38 行 | 处置 |
|---|---|
| `cli.py:140-146` 原样传参 | `cli.py` 增 `--allow-csf-out-in-game`（默认关）+ 把 `args.install` 作为 `install_game_dir` 传入；`build()` 早守卫 |
| `builder.py:434-437` 零守卫 | 重写 `_emit_csf_artifacts()`；全部写出走 `require_complete=True`；守卫前置到首个写之前 |
| `csf.py:410/416/417` 直写任意路径 | `csf.py` 增 `require_complete` 参数（**正确性**守卫在此层）；**路径归属**守卫在 builder 层（见上） |
| `csf.py:475` `create_if_missing` | 构建链路改为 `create_if_missing=False`；最小 CSF 路径消失 |

⇒ 这是**有意的边界划分**：「写出的 CSF 是否完整合法」由 `csf.py` 的
`assert_complete_csf()` 保证（需求 1），「写目标是不是游戏目录」由
builder 层保证（需求 3）。`[静态推断]` 若裁决要求守卫必须物理落在
`csf.write_csf()` 内，需要把「游戏目录判定」注入 `csf.py`，属更大的重构，
且会改变 51 例语义 —— 本卡未做，记为开放取舍。

---

## 4 · `MSG:UnableMapSelect` 的实测值带尾随换行（字节级校正）

`[转引]` 任务书 `[本次实测]`：「`MSG:UnableMapSelect` = 「無法啟始選取地圖！」」。

`[本次实测]` `EVIDENCE/step1.stdout.txt`：
`'無法啟始選取地圖！\n'` —— 官方 CSF 里该标签的 UTF-16LE 文本**末尾有
一个 `\n`**（`char_count` 含它，逐字节反转编码后读出）。任务书的转述省略了
这个换行。属显示层抄录差异，不影响任何判断（本卡只把它当抽样证据，
不依赖其精确值做校验）。

---

## 5 · 启用 CSF 开关后，`--csf-out` 的语义被**有意**改变（仅开关 ON 时）

`[本次读码]` v11（W30）：`--csf-out NEWPATH` 且无 `--csf-base`、文件不存在
→ `append_or_set_label(..., create_if_missing=True)` → 产出**只有 1 个标签**
的最小 CSF。

`[本次读码]` v12：同一命令 → 克隆内置完整官方 CSF（5,211 标签）+ 追加
1 个标签 → **5,212 标签**。

这是需求 1「最小 CSF 是危险的」的直接结果，**是刻意的破坏性变更**。
`[本次实测]` 需求 4 只要求「**不启用** CSF 相关开关时逐字节相同」，
`CSF_INST5` / `MS4` 已证明 OFF 时 8/8 产物 MATCH；ON 时的语义变化不在
兼容承诺内，但必须写明，避免被当成「回归」。

---

## 6 · `verify.py` 未改，却自动覆盖了 `ra2md.csf`

任务书需求 2 说「清单 / 备份 / 卸载还原都要包含 `ra2md.csf`」，并
`[签发]` 「`verify.py` 自 v10 起逐字节未改（`051C2E21…`）」，且纪律
「不得削弱 `verify.py` 语义」。

`[本次读码]` `verify.py:254-270` 本就遍历 `manifest["files"]` 逐个做
磁盘 sha256 比对，`_entry_structural_error()` 只要求「纯文件名 + 64-hex
sha256」，**没有硬编码文件白名单**。所以只要 `package_files()` 把
`ra2md.csf` 纳入清单，`verify` 就自动校验它 —— 无需改 `verify.py` 一行。

`[本次实测]` `out/CSF_INST2.log:34-39`：`files: 5 ok`，
`ok ra2md.csf`，`exit code: 0`；`verify.py` sha256 仍为
`051c2e21…`。⇒ 「纳入清单」= 「纳入 verify」，无须额外接线；
这一点与「W30 明确留下的缺口是 install.py 没写入游戏目录」一致。

---

## 7 · 未提供的开关（与任务书一致，无分歧，仅记录）

- `[本次实测]` **未**实现 `--allow-partial-csf`：任务书「不建议」，本卡
  同意 —— 它会重新打开 W29 启动失败风险。完整性守卫**无逃生口**。
- `[本次实测]` 新增的是 `--allow-csf-out-in-game`（**路径归属**开关，
  默认关闭、需显式确认 + 目标身份判定），与「部分 CSF」无关；
  `CSF_INST4e` 证明该路径仍产完整克隆。它绕开 install 清单会产生
  **未登记孤儿文件**（W21 风险），已在 `BUILD_REPORT.txt` 打 `[WARN]`
  + `UNCOVERED.md U3` 明示 —— 这是本卡唯一新增的危险开关，且默认关闭。

---

## 8 · 与 W30 `UNCOVERED.md §2` 的关系（缺口已补，措辞需更新）

`[转引]` W30 §2：「`install.py` 安装/备份/卸载链路尚未接入 `ra2md.csf`」，
理由是「避免在未真机确认覆盖规则前引入游戏目录 `ra2md.csf` 冲突」。

`[本次读码]` W41 已把它接入，并把「未真机确认」这个前提**显式保留**：
- 散装覆盖规则仍是 `[转引]` W29 静态结论 + `[转引]` 字节级自证
  （`CCFileClass::Get_File 0x473D10` 磁盘优先），本卡**未**真机复验；
- 本卡只保证「写进去的是完整合法 CSF」+「离线文件系统链路正确」；
- 因此 W30 §2 应更新为「已接入离线链路；真机覆盖/启动仍待 W40」，
  而不是「已解决」。本卡全文不写「CSF 功能可用」。

---

## 9 · 一处测试期望的校正（非产品缺陷）

`[本次实测]` 新增 `CSF_INST6h` 初版把清单里**没有** `original_absent` 键
误判成 `True`（用了 `.get(..., True)` 默认值）。实际 v12 的
`install.py` 在「存在真实原版」时**不写**该键（等价 `False`），
`CSF_INST6i/j` 的 restore 也确实成功。已把断言改为
`.get("original_absent", False)` 并复跑 57/57。属**测试期望**校正，
产品代码未因此改动；记录以免后续读者误以为 `original_absent` 语义有变。
