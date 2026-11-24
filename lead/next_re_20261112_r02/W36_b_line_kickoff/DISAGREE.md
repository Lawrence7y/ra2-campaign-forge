# DISAGREE · W36 与任务书前提 / 既有转述的事实出入

> 卡 `W36_b_line_kickoff`｜2026-11-13｜纯离线只读
> 依据：`docs\re\NEXT_RE_TASKS_20261112.md`、本卡 `B_LINE_PLAN.md` §2、以及下列盘上原文。
> **本卡不迁就前提**：凡与盘面/原文不符处逐条登记，并给出后续卡片应如何引用。等级口径同 `B_LINE_PLAN.md` §0。

## 总表

| # | 任务书 / 卡面前提 | 实际事实 | 等级 | 处置 |
|---|---|---|---|---|
| D1 | 「`W30_csf_capability\ra2forge_patched_v10\` 是**当前最高版本**（`TOOL_VERSION="1.0"`）」 | 同轮还有 `W34_mapselmd\ra2forge_patched_v11\`（14 个 `.py`，新增 `mapselmd.py` + bundled `data\MAPSELMD.OFFICIAL.INI`），`regress_dlc_v11.py` 51/51 PASS；`v11\install.py:388` 的 `TOOL_VERSION` **同为 `"1.0"`**（`MAPSELMD_SPEC.md:175` 明写「v11 只是目录版本号」）。另有 `W35_mapselmd_live\` 真机卡目录（见 D8） | `[本次实测]` + `[本次读码]` | 按 `TOOL_VERSION` 口径 v10 与 v11 **并列 1.0**；按包演进口径 **v11 更高**。后续卡写「当前最高版本」须指明口径，或写「v11（`TOOL_VERSION=1.0`）」并连带 v10 的 45 例与 v11 的 51 例 |
| D2 | 「v10 **12 个模块**（新增 `csf.py`、`verify.py`）」 | 本卡只读枚举：仓库基线 **11** 个 `.py`；v10 **13** 个（11 + `csf.py` + `verify.py`）；v11 **14** 个（+ `mapselmd.py`）。基线 11 个与用户列举的 11 个名字完全一致 | `[本次实测]` | 「12」应为 **13**。若口径是「不含 `__init__.py` 的功能模块」则为 11，仍不是 12。建议统一按「目录下 `*.py` 文件数」计数 |
| D3 | 「仓库 `ra2forge\` 是 **0.4 版**」 | `ra2forge\install.py:262` `TOOL_VERSION = "0.4"`；但 `ra2forge\__init__.py:9` `__version__ = "0.3.0"`。W21 `APPLY.md` / `W30\APPLY.md:6` 用「仓库 0.4」指 `TOOL_VERSION` | `[本次读码]` | 前提本身成立，但须写明「0.4 = `TOOL_VERSION`（清单/工具世代），不是包 `__version__`」；两字段不可混用，否则版本矩阵会错位 |
| D4 | 「已有能力（W21–W26 累计）：… **版本守卫** …」；`PAUSE_STATE_20261113.md` §2「B 线…当前实际具备的是：**版本守卫**、`verify`、seal、独立卸载」 | `patch_capability_audit_20261112\FINAL_RULING.md` §4 最终裁定：第 2 条「安装前验构建身份+原始字节；未知构建拒装」= **部分有**（`identity()` 存在但 `apply()` 全函数体不调用它，「能识别 ≠ 会拒绝」）；第 3 条独立开关/遥测/完整回滚 = **部分有**；第 5 条确定性对拍 = **没有**。分布「有 0 / 部分有 6 / 没有 1」。`ra2forge` 侧更弱：`v11\install.py:1140-1143` 只有 `(game/"gamemd.exe").is_file()` 存在性检查，无镜像哈希 / 版本矩阵 | `[本次读码]` + `[转引]` | **不能写「版本守卫已具备」**。正确表述：「有识别函数、无写入口接线；`ra2forge` 侧只有目录有效性检查」。RE-N09 L278 本身也写明「审计已提示 ra2opt 的识别功能与 apply 路径**可能未接通**，需按当前版本验证」——本卡确认**确实未接通** |
| D5 | 把 `verify` / 回归全绿当作「行为验证」 | `verify` 是**只读文件层**五项（结构 / digest 自洽 / 磁盘 sha256 / 孤儿 / seal，`W23\VERIFY.md:26-34`）；`W23\VERIFY.md:31` 明写 digest「只能证明清单内部一致，不能证明磁盘上是什么」；`W34\UNCOVERED.md` U9 明写「回归是**离线文件级**…沙箱内 `gamemd.exe` 是 inert 占位文件，从不执行」；`FINAL_RULING.md` §4 第 5 条判函数级/场景级确定性对拍样例 **= 0** | `[本次读码]` + `[转引]` | **回归全绿 ≠ 行为正确**。RE-N09 通过条件（L287）「安装态、执行态、行为态三项分别有证据；文档门禁 PASS 不代替游戏行为对照」；任务书 L374「行为结论必须包含有区分力的对照，不能以"脚本成功退出"替代」；`PROJECT_DIRECTION.md` L30 同。本卡全程仅在 `[转引]` + `[待运行验证]` 下引用 39/45/51 全绿 |
| D6 | 「**W25 发现**『复合故障下会留下配不上的记录/seal 对』」 | 该句出自 `REVIEW\LEAD_STATUS_W25_incomplete.md:30-33`，是 **Lead 依据 W25 的 `R1`（17/17 PASS）作出的判定**；W25 卡自身报告缺失（同文件 L12-13「报告类交付…**缺失**（代理死在写报告之前）」）。W25 盘上只有 `out\SUMMARY.txt` / `regress_dlc_v8.py` / `tools\` / `sandbox\` / `BASELINE_V8.sha256.txt` | `[本次实测]` + `[本次读码]` | 引用应写「Lead 在 `REVIEW\LEAD_STATUS_W25_incomplete.md` 依据 W25 `R1` 实测判定」。另见 D7 的勘误 |
| D7 | （承 D6 的常见连读）「W25 的 `R2` 证明**包文件没被回滚**；`F7` 证明 uninstall 收尾缺陷」 | `W26\DISAGREE.md` §1：`R2` FAIL 的直接原因是 `sha_tree()` 按 `Path` 序、`tree_lines_without()` 按 SHA-256 hex 序导致**行序不一致**；`install.py:1979-1980` 的 `except OSError: pass` 吞掉记录回滚异常后，外层 `_rollback()` **当时实际已移除全部 4 个包文件**。§3：`F7` FAIL 出自**夹具错配**（卸载的是 A1 的 4 个 `created` 文件，正确动作本就是 `removed    Y.MAP`）。§4：第 3 项失败是 `V5`（`DRIVER` 错指 `v8_rollback_fault_driver.py`）。生产隐患真实存在，但**不是「文件没回滚」** | `[本次读码]` | 下一卡**不得**继承「回滚会删一部分就不删了」（`LEAD_STATUS_W25_incomplete.md` §2.2 的当时的解读）作为前提；应写「吞异常 + 撒谎报错 + 缺乏复合失败聚合」，并以 `W26\UNSEAL_FIX.md` §1.1 / §4.1 的修复前后对照为准 |
| D8 | 「W21 发现**「错还原」**缺陷」 | `W21\DISAGREE.md:17-24` 原文用词是「**过度还原（over-restore）**」，且明确「**未发现任何误删**」；早期转述「卸载时可能删错」被实测否证。`HANDOFF.md` §9.1 用「错还原」概括，可用，但须连带限定 | `[本次读码]` | 写「过度还原 / 错还原（over-restore）」，并连带「不是误删、是 A 自己创建的字节被当成原版还原」；机制侧还须连带 `W21\DISAGREE.md:10-15`「清单条目被整体丢弃，不是仍被旧清单记录」 |
| D9 | 「**C 线**（战役包）两条阻塞**已定谳**」 | 判定文件自身是**受限定谳**：`REVIEW\LEAD_VERDICT_map_start_root_cause.md:50-57`「**静态判定链完整，但运行时分支未直接观测**…**不得写「已定位根因」的绝对化措辞**」；`LEAD_VERDICT_campaign_menu_q1.md` §7 列 4 项「未签发 / 待办」（含 `[0xA8F7AD]` 运行时取值与打开效果）。`W35_mapselmd_live\` 目录存在、`out\` 有 13 个产物，但**缺** `LIVE_RESULT.md` / `UNKNOWNS.md` / `DISAGREE.md` / `REAL_DIR_PROOF.txt`（对照 `REVIEW\_w35_prompt.md` §六）⇒ 按任务卡口径**未交付 / 未签发** | `[本次读码]` + `[本次实测]` | 「已定谳」应限定为「**静态/结构可达性判定已签发，运行时证据未定谳**」；W35 是否跑过真机本卡 `[待运行验证]`，其产物未复核、不得引用结论 |
| D10 | 「W26 回归 **39 例**、W30 回归 **45 例**（`regress_dlc_v10.py`），**全部离线可复跑**」 | 数字与盘上 `out\SUMMARY.txt` 一致（39/39、387 断言；45/45、413 断言）；但 W34 另有 `regress_dlc_v11.py` **51/51、462 断言**。本卡纪律为纯离线只读 + 不动 `W21`–`W35`，**未复跑任何套件** | `[本次实测]`（读 SUMMARY） + `[转引]` + `[待运行验证]` | 数字无误，补记 v11 的 51 例；「可复跑」本卡标 `[待运行验证]`，不写「已复跑」 |

## 已核对、无分歧的前提（留痕）

`[本次实测]` / `[本次读码]`，避免后续重复核验：

1. 仓库 `ra2forge\` 为 11 个 `.py` 模块，名字与用户列举一致，**没有** `verify.py`。
2. `W30\ra2forge_patched_v10\ra2forge\verify.py` 与 `csf.py` 均在盘；`TOOL_VERSION = "1.0"`。
3. W21–W26 累计能力（安装事务 / 零写预检、seal、`verify` 五项、`ra2forge_uninstall`、`--allow-content-conflict`、原子替换）与 `HANDOFF.md` §9 / `W26\UNSEAL_FIX.md` 一致。
4. A 线已停放（`REVIEW\LEAD_VERDICT_Aline_FINAL.md` §7 建议「转 B/C 交付线」；`PAUSE_STATE_20261113.md` §2）。
5. C 线两条判定文件确实在 `lead\next_re_20261112_r02\REVIEW\` 下（用户写的是 `REVIEW\…`，相对 r02 根目录）。
6. 「不得把回归全绿写成行为正确」是本项目反复强调的红线，任务书 L287 / L374、`PROJECT_DIRECTION.md` L30、`PAUSE_STATE_20261113.md` §1 均有一致表述。

## 处置原则

- 以上均为**措辞 / 口径 / 归因的精度修正**，不改变 RE-N09 的目标与通过条件，也不否定 W21–W34 的既有交付。
- 与任务书前提不符处**不迁就**：本卡 `B_LINE_PLAN.md` 的 §2 现状表、§3 四问判定、§4 切片计划均按「实际事实」写，不按「已具备 / 已定谳 / 已复跑」写。
- D4 / D5 是 B 线起步的**方向性修正**：B 线的起点是「补写入口接线 + 划清离线/真机边界」，不是「在已具备的版本守卫与行为验证之上加功能」。
