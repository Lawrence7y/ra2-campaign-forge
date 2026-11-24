# FINDINGS · W67 审计卡（独立审计 Lead 本轮签发件）

> 审计人：W67（GLM-5.3-Flash）｜起 2026-11-14 00:09:34｜止 2026-11-14 01:02（60 分钟时间盒内完成）
> 对象：`lead\next_re_20261112_r02\REVIEW\` 14 份指定文件 + `RUNLOG.md` §14–§17 + `HANDOFF.md` ★增量段
> 方法：不采信 Lead 自述；抽 24 组承重数字去原始产物实测核对（脚本与原始输出存本卡目录 `_w67_verify1..4_out.txt`）
> 纪律：纯只读 + 只写本卡目录；未启动 gamemd、未 attach、未取 `.game_instance.lock`（**I launched 0 / attached 0**）；git 仅 `status --porcelain`（只读）
> ⚠ 审计期间 RUNLOG 被持续追加（00:12 时 650 行 → 00:53 时 783 行，新增 §18–§23）。本报告对 RUNLOG 的行号一律按 **00:53 版（783 行）**；§18–§23 及新出现的 LEAD_VERIFY_W65/W68B/W70 不在本卡审计范围（范围以派卡时刻为准），但 §18 对 HANDOFF ★ 的失效影响属于 ★ 段自身的问题，已列入 B-2。

---

## A 级（承重错误）—— 2 条

### A-1 「21 个配置 21/21 byte_identical」与产物不符；产物与 W63 自己的报告都是 20+1
`[本次实测]` ｜ A 类 1+3（内部矛盾 × 与原始产物不符）
- 文件:行：
  - `REVIEW\LEAD_VERIFY_W63.md:72`（§7 表）原文：「沙箱可写配置还原 | **21 个，逐个 `byte_identical=True`**（含那个 241 B 孤儿 `.bak`，SHA `9f804531…`）」
  - `RUNLOG.md:631`（§17.3）原文：「21 个沙箱配置 **21/21** `byte_identical`」
- 实测（`W63_route_a_e2e\out\FINALIZE.json` `config_restore`，程序化计数）：**共 21 条，`byte_identical:true` 恰 20 条**；第 21 条 `ra2forge_install.json.seal` 的字段是 `{"restored": true, "absent_baseline": true}`，**没有 byte_identical 字段**（还原后按"基线本就缺席"删除）。
- 关键旁证：**W63 卡自己的报告 `W63_route_a_e2e\E2E_RESULT.md` 写的正是**「21 项沙箱可写配置基线收尾处置：**20 项**从 `out\pristine\*` 逐字节还原（`byte_identical=True`，含 241 B 孤儿 `.bak` SHA `9f804531…`）；**1 项** `ra2forge_install.json.seal` 在基线中本就不存在 → 删除」。
- 问题：Lead 的两处汇总把「20 项 byte_identical + 1 项 seal 删除」压成「21 个逐个/21/21 byte_identical」，与 JSON 产物和卡报告双重不符；且 RUNLOG 在我审计期间（00:31、00:53 两次改写）仍未修。
- 建议改法：两处改为「20 项 `byte_identical=True` + 1 项 `ra2forge_install.json.seal` 按 absent_baseline 规则删除（与 `E2E_RESULT.md` 收尾处置节一致）」。
- 影响评估：还原语义本身无恙（seal 该删、删了），是**汇总口径错误**，非还原失败；但它是「收尾闭环」的承重句，必须改。

### A-2 W61 补丁插入量：两处写「33 B」，产物与另两处写「32 B」——同一事实互斥且与产物不符
`[本次实测]` ｜ A 类 1+3
- 文件:行：
  - `RUNLOG.md:556`（§15.7）：「给 `RT_DIALOG 148` 插入 `id=1771` 项（**33 B**），`cDlgItems` 13→14，模板 664→696 B」
  - `REVIEW\LEAD_RULING_C_line_route_a_first.md:10`：「（W61）：`cDlgItems` 13→14、**插 33 B 项**、61/113 个资源数据入口平移」
  - 互斥方：`RUNLOG.md:589`（§16.1 表 Q5）：「`cDlgItems` 13→14、模板 664→696、**插 32 B**」
- 实测（产物）：
  - `W61_third_badge_route\THIRD_BADGE_ROUTE.md` §5.2：五处「**32 字节**」（新 item 32 字节 / file `0x487508` 插入该 32 字节 / 追加 32 字节 DLGITEMTEMPLATEEX / 吃掉 32 字节 padding / 61 个 RVA + 2 个 Size/VS + 2 字节 + 32 字节）；
  - `W61_third_badge_route\work\patch_dlg148.py`：`assert len(item) == 32`、`NEW_SIZE = 664 + 32`、`DELTA = 32`；
  - 算术自洽：696 − 664 = **32**；
  - 补丁项原始字节 `00 00 00 00 20 00 00 00 07 00 00 50 36 01 22 00 6E 00 57 00…` 直接给出 x=0x136=310、y=0x22=34、cx=0x6E=110、cy=0x57=87（与两处「(310,34) 110×87」吻合）。
- 问题：同一个补丁插入量在同一份 RUNLOG 里前后矛盾（556 vs 589），裁决书沿用了错的 33 B；「33 B」在任何产物里都不存在。
- 建议改法：`RUNLOG.md:556` 与 `LEAD_RULING_C_line_route_a_first.md:10` 的「33 B」改「32 B」。

---

## B 级（口径/引用瑕疵）—— 4 条

### B-1 W55B 验收的三条附注与 §0 声明，已被 23:17–23:19 的收尾再生成推翻，未加事后注记
`[本次实测]` ｜ B 类 4/6
- `REVIEW\LEAD_VERIFY_W55B.md:5`（§0）：「本卡**未写** `EQUIVALENCE_RESULT_V2.md`」→ 实测 `W55b_equivalence_rerun\EQUIVALENCE_RESULT_V2.md` **存在**，mtime **23:17:04**（恰在本 verify 文件落盘 23:17:01 的 3 秒后）；另 `RUN_SUMMARY.txt` 亦存在。
- `:61`（§5.1）：「`save_A1_s0_SAVE5802` 的 `arm`/`tag`/`frame_frozen` 记为 `None`（`CFB_COMPARE_TABLE.md` 同）」→ 现 `out\CFB_COMPARE_TABLE.md` 该行为 `| save_A1_s0_SAVE5802 | A | A1 | 2408 | 1397190 | 27c20543 | 1381318 | 3562 | 15 |`（arm/trip/frame 已填）；全表现存 4 个 `None` 全部在 **W45REF 行的 frame_frozen 列**（合理留空）。analysis.json 现也无任何 per-save None。
- `:63`（§5.3）：「`inputs_present.config_restore_post=False` 但 `out\config_restore_post.json` 实际存在（23:12:54）」→ 现 `out\analysis.json:68` 该键 = **true**（analysis.json mtime **23:19:27**，收尾再生成）。
- `:62`（§5.2）：「`story.md` 是 20:50 的旧时间戳」→ 现 W55b 根目录 **已无 story.md**。
- 问题：卡在 Lead 验收后 ~2 分钟内继续写（23:17:04 交报告、23:19:27 再生成 analysis/CFB 表/config_restore_post），Lead 三处引用与 §0 声明都变成了对盘核对会读出反例的"过期真话"；判定本身（`verdict="仍不可判"`）不受影响。
- 建议：§5 加一条后记：「以下三条描述的是 23:15 时点；23:19 收尾再生成后：V2 报告已交、SAVE5802 字段已补、config_restore_post 键已为 true、story.md 已移除」，给每条标引用时点。

### B-2 HANDOFF ★ 段仍写「GLM 端点在本时段不产生任何输出」，被 RUNLOG §18（00:32）明确更正，无回写指针
`[本次读码]` ｜ B 类 4
- `HANDOFF.md:26`：原文「**GLM-5.3-Flash 本时段不可用**：…**全部零产出静默失败**…是**该模型端点在本时段不产生任何输出**」。
- 实测：`RUNLOG.md:654-667`（§18「运维真相更正」）已更正为「**不是不可用，是并发限额 3 + 慢**」，并给反证（00:09 降并发后 GLM 立即产出 = 本卡）。RUNLOG §14.2/§16.2 的旧说法因 §18 有显式指针可以保留；**HANDOFF ★ 段无任何指向 §18 的更正注记**。
- 建议：HANDOFF ★ 「模型路由实况」块加一行「⚠ 23:26 本段的『端点零输出』结论已被 RUNLOG §18（00:32）更正为并发限额问题」。

### B-3 三处「文件自述时间」晚于文件 mtime（写作时凭印象写时间的老毛病残留）＋ W58 引用 INDEX.md 早于其存在
`[本次实测]` ｜ B 类 5
| 文件:行 | 自述时间 | 实测 mtime |
|---|---|---|
| `REVIEW\LEAD_CHECK_W54_CFB.md:3` | 22:35 | **22:32:11** |
| `REVIEW\LEAD_RULING_D5_2_INPLACE_UNFREEZE.md:3` | 22:40 | **22:38:34** |
| `REVIEW\LEAD_RULING_C_line_route_a_first.md:49`（§5 补记） | 「补记（23:32…）」 | **23:30:07** |
| `REVIEW\LEAD_VERIFY_W58.md:4` | 交付清单含 `INDEX.md`（自述 23:03） | 卡根目录无 INDEX.md；实存 `EVIDENCE\INDEX.md`，mtime **23:19:26**（晚于该 md 落盘 23:17:01） |
- 问题：mtime 不可能早于文件内声称的写作时间（mtime=最后一次写入）；这是 RUNLOG §14.7 自立规矩（「写时间戳前先 Get-Date」）的漏网残留。W58 的 INDEX.md 属"引用了尚不存在（或不在所述位置）的交付物"。
- 建议：四处按 mtime/实际路径订正。

### B-4 D5.2 裁决的承重前提当晚被推翻、证据晚于裁决落盘，裁决无更正块
`[本次读码+mtime]` ｜ B 类 4
- `REVIEW\LEAD_RULING_D5_2_INPLACE_UNFREEZE.md:10`（§1.1）：「`[已签发]` 战役菜单**无法新增第 3 个徽章**（W32 三重否证 + 我自己实测门控 `[0xA8F7AD]` 全镜像无静态写入者）」。
- 实测时序：裁决 mtime **22:38:34**；其门控证据的落盘 `LEAD_CHECK_gate_byte.md` 自述 22:42、指令级证据（W57）23:16 才交付——**裁决引用了尚未落盘的"已签发"**；且前提 1 的「引擎层封死」当晚 22:56 被 `LEAD_CHECK_menu_3slot.md` §2/§3、23:03 被 `LEAD_VERIFY_W58.md` §2 推翻（引擎有 3 槽、1771→tut1；仅"只加配置不支持"仍成立）。
- 影响评估：**裁决的执行结论不受影响**——解冻 inplace 与「真机先走 (a)」由其余论据（W37 路线 (b) 跨文件重复 ID + MIX 回退风险、W27 真机先例、(c) 需改 exe）独立支撑，且 23:26 的 `LEAD_RULING_C` 已按收窄后的口径重述。
- 建议：D5.2 加更正块：前提 1 按 W58 收窄版措辞重述；门控证据标注实际落盘时间链（gate_byte 22:42 → W57 23:16）。

---

## C 级（可读性/结构）—— 5 条

### C-1 W63 §8 说「7 个阶段快照」，表只列 6 行
`[本次实测]` `REVIEW\LEAD_VERIFY_W63.md:86` vs `:90-97`。实测 `TRIP_RESULT.json.trajectory` 确为 **7** 项；表格漏掉第 7 项 `final_after_M3_continue`（t=69.8、frame=210、stage=9、eog=1）。建议补行或注明省略。

### C-2 W58 §0 交付枚举与现盘不符
`[本次实测]` `REVIEW\LEAD_VERIFY_W58.md:4`：「`EVIDENCE\`（**14 组**脚本/stdout）」→ 现盘 EVIDENCE 60 个文件、编号组 00–16 + 02b 共 **18** 组（15/16 组 23:03–23:04 才落盘，INDEX.md 23:19:26）；`INDEX.md` 在 EVIDENCE\ 内、卡根目录无。建议改为「18 组 + INDEX.md（EVIDENCE\ 内）」或标引用时点。

### C-3 HANDOFF ★「10 份签发件」计数与表自身对不齐
`[本次读码]` `HANDOFF.md:11`（HANDOFF mtime 23:25:50）。★表具名 9 份；同轮还存在的 `LEAD_VERIFY_W54_INDEPENDENT.md`、`LEAD_CHECK_W54_CFB.md` 未具名 → 共 11 份。10 既不等于 9 也不等于 11。建议写明清单或「10 份（截至 23:25）」。

### C-4 W55B §1 表 ③ 状态「达成」 vs analysis.json 的 P3「部分」
`[本次实测]` `REVIEW\LEAD_VERIFY_W55B.md:13` 状态列「达成」；`W55b_equivalence_rerun\out\analysis.json` `w54_preconditions.P3_contents_comparison_criterion.status="部分"`（结构未解、按任务允许回退整流 sha256）。证据格里已披露退化口径，但两处状态词并读有落差。建议状态列写「达成（CONTENTS 结构解析为"部分"，按任务允许回退）」。

### C-5 命名/编号跳号引用核查——未发现问题
`[本次读码]` W57→W57b 共目录双写（§15.3 + `W57_gate_writer_adjudication\` 内 3 份 `*_W57B.md` + `COLLISION_NOTE.md` 实存）；W64→W64b（RUNLOG:604「目录都没建」指 GLM 版，W64b 复用 `W64_bootcamp_inventory\`，与 `LEAD_VERIFY_W64B.md:3` 一致）；W49/W50/W55/W56 遗留状态在 §14.1 有实测交代；W56 分类表作废声明在 `LEAD_VERIFY_W57.md:47` 闭合。**未发现指错。**

---

## 覆盖矩阵（我核对过什么）

### A. 原始产物实测（`[本次实测]`，脚本 + 原始输出存 `_w67_verify1/2/3/4_out.txt`）
| # | 产物 | 核对项 | 结果 |
|---|---|---|---|
| 1 | `ra2bench\gamemd.exe` | size 4,825,360 / SHA `73201cc0…67476` | ✅ 全符 |
| 2 | 同上 | LE32 `0xA8F7AD` 恰 1 @FOFF 0x12F00C；`A0 AD F7 A8 00` 恰 1 @0x12F00B（VA 0x52F00B）；`0xA8F7AC` 恰 1 @0x2BE030；RVA/页内相对形式全 0 | ✅ 全符（gate_byte/W57） |
| 3 | 同上 | 邻域 [0xA8F7A0,0xA8F7B4] 全偏移 LE32 扫描 = **36** 处，其中覆盖 AD 仅 2 处（均为 A0 读） | ✅ 恰 36 |
| 4 | 同上 | ASCII `all1/sov1/tut1` 各恰 1 次（FOFF 0x425CA0/98/90 → .data VA 0x825CA0/98/90，与 menu_3slot §1.2 表逐项吻合）；`all2/sov2/tut2/all3/sov3` 全 0 | ✅ 全符（W58 §2） |
| 5 | 同上 | `BATTLE.INI` 字面量 0 次；`BATTLEMD*.INI`@VA 0x4261A8、`BATTLEMD.INI\0`@VA 0x426198 | ✅ 全符（W64b §2） |
| 6 | 同上 | W59 十二组字节（0x5CF04F/0x5CF367 cmp …,0x64、0x5AE0B8/0x5AE1FA、0x6859BF、0x6859C7 `74 47`→0x685A10 算术、0x68594B、0x68A11F、0x685C4E、0x685C54 `e8 57 de ff ff`→0x683AB0 算术、0x52F00B、0x6BE02F） | ✅ 12/12 MATCH |
| 7 | 同上 | `STT:CampaignAnimTutorial` 全镜像恰 1 次（VA 0x83567C）；`BootCampSelect` 恰 1 次 | ✅（RULING_C §5 的 0x6041FD 是**引用代码址**：0x604206 处 `mov eax,0x83567C`，±9 B 内，语义成立） |
| 8 | `W63\out\TRIP_RESULT.json` | outcome=FULL_CHAIN_M1_M2_M3、ok=true、M3 advance=false/eog=1、trajectory 7 快照、stage 0/8/9、eog 0/0/1、frame 75/210/92/210/93/210、0x125C 三图名 | ✅ 全符（W63 §1/§2/§8） |
| 9 | `W63\out\run.ndjson`（+finalize/offline） | UnableMapSelect 全 0；冻结期 `(frame=210,stage=9,eog=1)` 样本恰 **47** 个；pid 34668 出现 11 次 | ✅（"47 samples"精确吻合；"71 s"为含收尾窗口口径，冻结期 t=0→69.8 s，见 UNKNOWNS） |
| 10 | `W63\out\FINALIZE.json` | config_restore 21 条=20 BI+1 seal；identical_tree（终态 sandbox/real 均 true）；647 files/1,989,215,270 B；verify exit 0（degraded）；lock_final owner=lead 23:39:42.496；gamemd residual 0；.sav×3 旁证+清理 | ✅（唯 A-1 的 21/21 措辞不符） |
| 11 | `W63\out\INPLACE_INSTALL.json` | 2733→2732、original/post SHA `7e40691a…`/`8fb51769…`、bak=官方 | ✅ |
| 12 | `W63\REAL_DIR_PROOF.txt` | IDENTICAL_TREE×3、647×3、1,989,215,270×3 | ✅ |
| 13 | `W63\out\MAPSELMD.INI.variant_from1` | 296 行；[Nod] Anims/Sounds + 键 1..10，键 8/9/10 = RA2F_RA2F_M1_3B52DC3A / M2_06228782 / M3_1AE84EB9 | ✅（W63 §8 引文逐字吻合） |
| 14 | `W63\out\desktop_probe.ndjson` + robocopy log | 390 windows、ImageGrab 2560×1440、WinSta0\Default；robocopy EXIT 1 | ✅ |
| 15 | `W63\out\pristine\BATTLEMD.INI` + `.bak` | 2733 B / SHA `7e40691a3480…f0791`（与 §7 全文一致）；241 B / SHA `9f804531c1…` | ✅ |
| 16 | `W55b\out\analysis.json` | verdict「仍不可判」、N_A=1,339,784/N_B=1,316,737/N_stable=false、n_aligned=4/unaligned=0、main group [2408]、spread 0、esc_attempts=2×4、D 1,319,300–1,321,641、残差 67–176、P3=部分、config_restore_post=true | ✅（唯 B-1 的两处引用过期） |
| 17 | `W55b\out\CFB_COMPARE_TABLE.md` | SAVE5802 行 A/A1/2408/1,397,190/27c20543/**1,381,318**（CONTENTS 长度）；None 仅 W45REF 4 行 | ✅（B-1 相关） |
| 18 | `W55b\` 根+out 清单/mtime | EQUIVALENCE_RESULT_V2.md 23:17:04 存在、RUN_SUMMARY.txt 存在、story.md 不存在、*_result.json ×4、config_restore_post.json 23:19:30 | ✅（B-1 依据） |
| 19 | `W60\out\SUMMARY.txt` | cases 96/96、assertions 835、exit 0、INPLACE1–6 PASS | ✅ |
| 20 | `W60\out\*.json/.log` | `369592f0`（BATTLEMD.INI.hashes.json/IDEMPOTENCE_CHECK.json/INPLACE3.log/INPLACE_REWRITE_REPORT.json）与 2730 多处 | ✅（RUNLOG §15.6/RULING_C §1 的 SHA/尺寸有产物支撑） |
| 21 | `W61\THIRD_BADGE_ROUTE.md` + `work\patch_dlg148.py` + `readback_14.txt` | 32 字节×5、664→696、61/113、0x18128、b9021544a369…1287 全 SHA、(310,34) 110×87（raw item 字节直接验证）、SOUND.INI `534=BootCampSelect` | ✅（唯 A-2 的两处 33 B 不符） |
| 22 | `W61\work\*.csf` ×2 | DESC:TUT1 / CampaignAnimTutorial / TutorialCampaign 各 1（两份 CSF 均） | ✅（RULING_C §5 CSF 三串有物证） |
| 23 | `W64b\BOOTCAMP_INVENTORY.md` | LOCAL.MIX 34,793,784 B=33.18 MB、BATTLE.INI 4,054 B/SHA a5752a8d…、1,003 候选名/13,007 id/2,125 容器、635 map-like/198、21 位置/17 组/10 顶层 MIX、MAPSELMD 5,573 B/074ccccd…、20 段/14 阶段、exe BATTLE.INI 0 次 | ✅ 全符 |
| 24 | `W45_b_line_equivalence\out\save_*.SAV` ×8 | 8 个尺寸逐一吻合；magic d0cf11e0a1b11ae1、ver 3.62、shift 9/6、cutoff 4096、nFAT 22（B2_SAVE27BB=21） | ✅（W54_CFB 全表复核） |
| 25 | `W44_c_line_e2e\out` | 恰 2 个 2,562,915 B 文件、SHA 均 `0c7fb5fb…7971`；全目录无 0bdcfd8c 前缀；1,989,215,270 出现于 W44 产物 | ✅（TRIAGE §1 BLOCKER-3/§4 复算成立） |
| 26 | mtime 矩阵 | REVIEW 14 文件 + W55b 全 out + HANDOFF/RUNLOG + `lead\PENDING_DECISIONS.md`（git status=`M`，D5.2 §4 的"他人未提交改动"属实）+ W58 EVIDENCE | ✅（B-3/B-4 依据） |

### B. 纯读码核对（`[本次读码]`）
- 14 份指定 REVIEW 文件逐字读毕；RUNLOG §14–§17（按 00:53 版行号）；HANDOFF ★ 段。
- `LEAD_VERIFY_W60*.md` **不存在**（审计清单已预期"若有"；W60 的数值改由 RUNLOG §15.6/RULING_C §1 承载，已对 W60 产物核对，见矩阵 #19/#20）。
- 内部算术抽查：773=740+14+19（W57 §2）；36=2+34（gate_byte §3）；2+6+1+12=21（W64b Q3）；2+6+6=14 条 Battles（W64b Q1）；696−664=32；0x6859C9+0x47=0x685A10；0x685C59−0x21A9=0x683AB0；battle_cnt=14（TRIP_RESULT）与 W64b Q1 官方 14 条一致。
- 措辞边界检查：W63 §6/§17.5、W55B §3、W57 §1、W58 §2、W64b §4、gate_byte §2 的限定条款均在，未发现"未检出→等价成立"或"单包→通用可通关"类越界外推；W55B「CONTENTS 不可跨运行复现」属存在性命题（n=2 即足证），非外推；W63 §8 的 +0x35A0 语义已自标 `[静态推断·较强]` 并写明 3 数据点边界。

## 结论
- **A 级 2 条**（均为汇总口径与产物不符，不动摇任何判定结论本身：W63 的"三关链贯通+收尾还原"与 W61 的"补丁可行"内核都另有正确产物支撑）。
- B 级 4 条（时效/引用过期 ×2、时间戳倒挂 ×1、过期前提无注记 ×1）。
- C 级 4 条 + 1 条"未发现问题"。
- 承重数值抽核 **24 组，23 组完全吻合**；2 组不符（A-1、A-2）均为 Lead 汇总层，原始产物层无一错误。
