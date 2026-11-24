# 第一轮更正落地核对表（CORRECTION_LEDGER）

> 审计卡：W52（第二轮交叉一致性审计）  
> 基线依据：第一轮审计（[agy_w43_handoff.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/agy_w43_handoff.md)）抓出的 6 项更正事项  
> 核对范围：Lead 最新 9 份签发/裁决文档及其直接指向的关联更正位点（`D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\REVIEW\`）

## 总览

| # | 第一轮指出的问题 | 落地判定 | 依据文档与位置 | 残余/未闭合项 |
|---|---|---|---|---|
| 1 | 错误否定 W34 的 `0xFBE0D09D = ts_crc_hash("LOCALMD.MIX")`（用错填充规则） | **已落地** | `LEAD_VERIFY_W34.md` §3、`LEAD_W33_VERIFY.md` §3.1b、`LEAD_VERDICT_map_start_root_cause.md:72`、`LEAD_VERIFY_W37.md:14` | 9 份主审文档中未再见未撤回的否定表述 |
| 2 | 凭空「纠正」W39 的 2.5s / 4.56s 时间口径（W39 原本没错） | **已落地** | `LEAD_VERDICT_Q2_CLOSED.md:93-118`（§6） | 已按 `t_monotonic` 完整撤回原「游戏时间 vs 挂钟时间」误纠 |
| 3 | 把 `scen_stage_idx=8` 从 `[转引]` 升级成 `[本次实测]`，且下标差一格 | **落一半** | `LEAD_VERDICT_Q2_CLOSED.md:50-60`（§3） vs `:140`（§8） | §3 已降格为 `[转引]` 并修正为 `idx=8 ↔ 9=RA2F_ECH02`；但 §8 第 140 行「`数字子项` 在真机上可用」仍未收窄 |
| 4 | 宣称「已把『转大写』改口」但实际没改；且 W31 犯同样错未指出 | **落一半** | `LEAD_W33_VERIFY.md:93`、`LEAD_VERIFY_W34.md:34`、`LEAD_VERDICT_map_start_root_cause.md:23-30,80` | `LEAD_W33_VERIFY.md:93` 已改口为转小写；但 `LEAD_VERIFY_W34.md:34` 与 `LEAD_VERDICT_map_start_root_cause.md` 仍未指出 `W31`（`WHY_MAP_FAILS.md:129,141`）的同错，且 `LEAD_VERDICT_map_start_root_cause.md:23-30` 仍将 `SkipMapSelect=no` 与 `SkipMapSelect=yes` 两条路径混并 |
| 5 | `SOV07TMD.MAP` 的 `EndOfGame` 错写为 `no`（实为 `yes`） | **已落地** | `LEAD_W33_VERIFY.md:48, 51-53` | 已从 `no` 更正为 `yes` |
| 6 | 「三个槽位含 `tut1`」夸大（`tut1` 无 BATTLEMD 条目） | **落一半** | `LEAD_VERDICT_campaign_menu_q1.md:18-22, 32, 91` vs `:14, 107` | 开头更正横幅与 §2/§4 已收口为 `ALL1 / SOV1`（2 个槽位）；但第 107 行仍写「三个槽位替换官方战役后的连带影响」，且同文第 14 行与第 77-79 行对隐藏 ListBox(1109) 仍自相矛盾 |

---

## 逐条核对详情

### 1. `0xFBE0D09D = ts_crc_hash("LOCALMD.MIX")` 误否定 —— **已落地**
- **核对位置**：
  - [LEAD_VERIFY_W34.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W34.md) §3（已撤回自我更正段）
  - [LEAD_W33_VERIFY.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md) §3.1b
  - [LEAD_VERDICT_map_start_root_cause.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L72)
  - [LEAD_VERIFY_W37.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W37.md#L14)
- **核对结论**：上述四处均已按正确填充规则完成重算并撤回此前对 W34 的否定；在本次审计的 9 份最新文档中未发现仍保留未撤回否定表述的活口。

### 2. W39 `2.5s / 4.56s` 时间口径误纠 —— **已落地**
- **核对位置**：[LEAD_VERDICT_Q2_CLOSED.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_Q2_CLOSED.md#L93-L118)（§6）
- **核对结论**：§6 第 93-118 行已引用 `t_monotonic` 明确撤回此前所谓「游戏时间与挂钟时间混用」的错误纠正。

### 3. `scen_stage_idx=8` 证据等级拔高及下标差一格 —— **落一半**
- **已改部分**：[LEAD_VERDICT_Q2_CLOSED.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_Q2_CLOSED.md#L50-L60)（§3）已将该证据从 `[本次实测]` 降回 `[转引]`，并将 0-based `idx=8` 与 `9=RA2F_ECH02` 的对应关系修正。
- **未改部分**：同文第 140 行（§8 结论条）仍原文保留：
  > `- v11 的生成逻辑（[Nod] 续号 + 独立阶段段 + Scenario= + 数字子项）在真机上可用`
  - 第一轮 `BLOCKER-3` 明确要求将「`数字子项` 在真机上可用」收窄为「单后继直转路径」，因为多分支交互式 `2=<next>` / `ClickMap` 并未经过真机测试；该条在 §8 尚未收窄。

### 4. 「已把『转大写』改口」且漏指 W31 同错 —— **落一半**
- **已改部分**：[LEAD_W33_VERIFY.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L93) 已按 `转小写后比较...` 更正；[LEAD_VERDICT_map_start_root_cause.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L80) 已列出 W33「转大写」与 W34「转小写」的对比。
- **未改部分**：
  1. [LEAD_VERIFY_W34.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W34.md#L34) 原文仍只写：
     > `并已在 REVIEW\LEAD_W33_VERIFY.md 与 REVIEW\LEAD_VERDICT_map_start_root_cause.md 里把"转大写"改口`
     并未指明 `W31`（[WHY_MAP_FAILS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/WHY_MAP_FAILS.md#L129-L141) 第 129、141 行）犯了完全相同的 `转大写` 错误。
  2. [LEAD_VERDICT_map_start_root_cause.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L23-L30) 也未补充对 W31 同错的标注，且第 23-30 行仍将 `SkipMapSelect=no`（`0x005AE320` + `0x005ADD95..0x005ADDCF`）与 `SkipMapSelect=yes`（`0x005ADFF3` / `0x005ADEE0..0x005ADEFA`）两条不同失败出口并写在同一尾部口径中。

### 5. `SOV07TMD.MAP` 的 `EndOfGame=no` 误写 —— **已落地**
- **核对位置**：[LEAD_W33_VERIFY.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L48-L53)
- **核对结论**：第 48 及 51-53 行已由 `no` 修正为 `yes`。

### 6. 「三个槽位含 `tut1`」夸大 —— **落一半**
- **已改部分**：[LEAD_VERDICT_campaign_menu_q1.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_campaign_menu_q1.md#L18-L22) 已补充更正说明（`可借用入口只有 2 个：ALL1 / SOV1`），且第 32 行与第 91 行已同步收敛。
- **未改部分**：同文第 107 行仍原文保留旧口径：
  > `- 三个槽位替换官方战役后的连带影响（存档、MAPSELMD.INI、BATTLEMD.INI 冲突）`
- **附带未落地项（同文件第一轮遗留）**：同文第 14 行表格仍写 `有条件可达，被一个字节 [0xA8F7AD] 门控 | 可开`，与第 77-79 行已承认的「实测不可达……据此下调」自相矛盾；第 98 行仍由 `4.3` 直接跳到 `6.`（缺 `§5`）。
