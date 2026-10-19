# W3-DOCFIX-2 · `E-W3-10`：**错 `FileOffset` 公理的影响面处置**（58 份文档，**分流而非刷注**）

> 背景：Lead 自查发现——`FileOffset = VA − 0x400000` 这条**错公理**仍存在于 **58 份文档**，而 `E-W3-01` 勘误只落到 **5 份**（`AGENT_TASK_TEMPLATE.md` + 4 张派工卡）。
> 起源勘误：`out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md`
> **ATLAS 那一份由 W3-DOCFIX-1 负责，本卡不碰 `ARCHITECTURE_ATLAS.md`。**

## 0. 正确口径（不要自行改写）

```
FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)
```
本镜像：`.text`/`.rdata`/`.data` 恰为 `VA − 0x400000`；**`.rsrc`/`.detour` 为 `VA − 0x6FC000`**。
**注意**：`VA − 0x6FC000` 与 `VA − 0x400000 − 0x2FC000` 是同一件事的两种写法（前者是 `VA − rawptr`，后者是 `naive − file_off`），**别把它当成两个不同的数**。

## 1. 第一步：**分类**（不要先动笔）

对下列 58 份文档逐处判定每个出现点属于哪一类：

- **A 类 = 陈述通则**（把它当作通用换算规则写出来，例如"计算公理：`FileOffset = VA − 0x400000`"）⇒ **必须加注**
- **B 类 = 纯 `.text` 上下文**（只是在一个已知落在 `.text` 的 VA 上套用）⇒ **不加注，但必须登记**
- **C 类 = 已经标注过** ⇒ 跳过

已知未加注的文件（Lead 实测，`wrong-axiom` 计数）：
```
ARCHITECTURE_ATLAS.md 3   ← DOCFIX-1 负责，本卡跳过
R1_render_blit.md 2       R2_fog_l4.md 2        R6_weapons_mix.md 2
R3_ai_hooks.md 1          R4_acceptance_standard.md 1   R5_triggers_save.md 1
R8_ui_crt.md 1            execution_runbook.md 1
audio_engine_deep_dive.md 1     audio_throttle_landing.md 1
buffera_shade_table_deep_dive.md 1   building_fog_residual_deep_dive.md 1
cross_doc_consistency_audit.md 1     deep_dive_sweeps_closure.md 1
doc_consistency_fix_list.md 2        fog_firststage_site_locate.md 1
fog_mixing_site_deep_dive.md 1       fs_mix_load_chain_deep.md 1
fx_draw_chain.md 1                   landing_pack_preflight_audit.md 1
lightconvert_0x420140_deep_dive.md 1 net_sync_checksum.md 1
offline_verification_alternatives.md 2   open_items_sweep.md 1
pending_execution_master_table.md 1  re_sprint_S{1,2,3,4,5,6,8,9,10,11,12,14,15,17,19,21}_report.md 各 1
superweapon_re.md 1       trigger_determinism_deep_dive.md 1
trigger_runtime_deep_dive.md 1       trigger_tag_abi_deep_dive.md 1
ui_command_dispatch_deep_dive.md 1   va_claims_p1.md 1
va_claims_sample_p2.md 1  visibility_gap_spysat.md 1
weapons_damage_landing.md 1          weapons_damage_production.md 1
```
（以你自己的 grep 复算为准；若与上表不符，**以你的复算为准并单列勘误**。）

## 2. 第二步：**只给 A 类加注**（严格 append-only）

格式（原句不动，紧随其后插入）：
```
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
```

**B 类一律不动**（改了就是噪音，还会误导"这里以前错过"）。

## 3. 第三步：**加一个可机检守卫**（本卡的重点）

写 `out/re_work/qc/W3_20261001/docfix2/check_fileoffset_axiom.py`，**EXIT=0**，断言：
1. 全库 `grep`：**A 类出现的每一处**其**同一段落内**必须含 `E-W3-01` 字样；
2. **B 类清单固化**在脚本里（文件 + 行号 + 一句"判为 `.text` 上下文"的理由），**若某处 B 类被改动而清单未更新 ⇒ FAIL**；
3. 打印统计：`A 类 N 处（已注 M）/ B 类 K 处 / 未分类 0 处`，**未分类必须为 0**。
⇒ 这样**新增的文档如果再犯，守卫会抓到**。（先放本目录；是否提升进 `tools/**` 由 Lead 复核后决定，**你不要自己写 `tools/**`**。）

## 4. 交付物

- `out/re_work/qc/W3_20261001/docfix2/DOCFIX2_RESULT.md`：**A/B/C 三类逐文件逐行清单**（文件、行号、原文片段、分类、理由、处置）+ **append-only 零删除自证**（before/after 行数 + 有序子序列判定）
- `check_fileoffset_axiom.py`（EXIT=0）+ 其原文输出
- 门禁：`python tools\verify_anchors.py` 须 **323/323 PASS**（原文粘贴）

## 5. 纪律

- 写域：**`docs/re/**`（除 `ARCHITECTURE_ATLAS.md`）** + `out/re_work/qc/W3_20261001/docfix2/**`。
- **禁写** `ARCHITECTURE_ATLAS.md`（DOCFIX-1 在改）、`ra2youli/**`、`ra2bench/**`、`ra2render/**`、`tools/**`、`out/re_work/agy/**`、`out/re_work/zcode_live/**`。
- **只加注、不改原句、不删行**；**不得启动游戏**。
- 回报 ≤2 页，`[0]` 直接答：**A 类几处 / B 类几处 / 未分类几处 / 守卫 EXIT 是多少 / append-only 是否零删除**。
