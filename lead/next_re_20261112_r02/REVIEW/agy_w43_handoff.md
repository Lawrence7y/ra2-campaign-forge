# Antigravity handoff

## Result

> **执行说明（只读 `/plan` 模式）**：当前会话处于只读 `/plan` 约束下，未在磁盘创建 `lead/next_re_20261112_r02/W43_consistency_audit/` 文件，也未修改任何工作区文件；以下直接呈报 W43 交叉一致性审计的完整 **AUDIT_REPORT**、**CONFLICT_TABLE**、**UNKNOWNS** 与 **处置计划**。

---

# 一、AUDIT_REPORT（按严重度排序：`BLOCKER` → `MAJOR` → `MINOR`）

## BLOCKER（会直接误导工程决策或反证逻辑）

### [BLOCKER-1] Lead 对 `0xFBE0D09D = ts_crc_hash("LOCALMD.MIX")` 的“证伪”本身算错了算法
- **位置**：
  - [LEAD_W33_VERIFY.md:142-152](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L142-L152)
  - [LEAD_VERIFY_W34.md:40-52](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W34.md#L40-L52)
  - [LEAD_VERDICT_map_start_root_cause.md:72](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L72)
  - [LEAD_VERIFY_W37.md:14](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W37.md#L14)
- **问题类型**：1（结论冲突）/ 5（未经证实的因果反转）
- **原文摘引**：
  - [LEAD_VERIFY_W34.md:40-52](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W34.md#L40-L52)：`W34 两次（中途消息 + 最终报告）称 0xFBE0D09D = ts_crc_hash("LOCALMD.MIX")。我逐一变体验算，全部不匹配`（`15 种变体无一命中`）→ `该 id 的来历仍未定谳；连带地，容器名是否真为 LOCALMD.MIX 我也未能独立证实` → `不得把 0xFBE0D09D = ts_crc_hash("LOCALMD.MIX") 当事实引用`
  - [LEAD_VERDICT_map_start_root_cause.md:72](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L72)：`[未定谳] 0xFBE0D09D 这个条目 id 的来历（W34 称 ts_crc_hash("LOCALMD.MIX")，我验算不成立：0x62E98127 等 8 种变体全不匹配。但 W34 的字节产物已用 SHA-256 验证正确，属"结果对、理由错"，该 id 解释不得引用）`
  - 对照仓库真实实现 [mixlib.py:210-217](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W30_csf_capability/ra2forge_patched_v10/ra2forge/mixlib.py#L210-L217)：`if length & 3: b = b + bytes([length - (aligned << 2)]) + bytes([b[aligned << 2]]) * (3 - (length & 3))`，再用 `zlib.crc32(b) & 0xFFFFFFFF`。
- **为什么是问题**：Lead 在 [LEAD_W33_VERIFY.md:142-152](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L142-L152) 用的是 `pad0->4`、`pad0->8`、`plain=0x3BF6887A` 等标准零填充变体，没有按 [mixlib.py:210-217](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W30_csf_capability/ra2forge_patched_v10/ra2forge/mixlib.py#L210-L217) 的 WestWood `ts_crc_hash` 规则（追加 `len % 4` 字节后再重复末组首字节 `3 - (len & 3)` 次，即对 11 字节 `"LOCALMD.MIX"` 补 `0x03 0x4D 0x49`—其中 `b[8] == ord('M') == 0x4D`）验算，却据此错误否决了 W34（[MAPSELMD_SPEC.md:40](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W34_mapselmd/MAPSELMD_SPEC.md#L40)）的正确结论，并将 `"结果对、理由错"` 的错误帽子扣回 W34 头上，连带让 [LEAD_VERIFY_W37.md:14](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W37.md#L14) 继续传播 `容器名的具体字符串仍未定谳`。
- **建议处置**：**撤回**上述 4 个 `REVIEW/` 文件中的假证伪与禁引令，用 `mixlib.ts_crc_hash("LOCALMD.MIX")` 复核后**改口径**确认其确等于 `0xFBE0D09D`。

---

### [BLOCKER-2] `LEAD_VERDICT_Q2_CLOSED.md` §6 对 W39 `2.5s` vs `elapsed_s: 4.56` 的纠偏本身是错的
- **位置**：[LEAD_VERDICT_Q2_CLOSED.md:88-97](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_Q2_CLOSED.md#L88-L97) vs [run_mapsel_live.py:234-280](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/tools/run_mapsel_live.py#L234-L280)、[w39_skip_no.ndjson:33-41](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/out/w39_skip_no.ndjson#L33-L41)、[LIVE_RESULT.md:121](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/LIVE_RESULT.md#L121)
- **问题类型**：6（W39 真机结论与数字误判）/ 3（数值口径）
- **原文摘引**：
  - [LEAD_VERDICT_Q2_CLOSED.md:90-97](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_Q2_CLOSED.md#L90-L97)：
    - `W39 的消息里写「[0xA8ED84] frame 44→123（2.5s，Δ79，≈31.6/s）」。[本次实测] ndjson 里同一条记录写的是 elapsed_s: 4.56、frame_delta: 79、frame_t1: 44、frame_t2: 123。`
    - `Δ79 计数 ÷ 31.25 计数/秒 = 2.53 s 游戏时间（定拍 32 ms 下成立） / 而墙钟窗口是 4.56 s（含加载/切换） / ⇒ 两种说法都对，但混用了两个时间基准... [纪律] 不得把「Δ79 ≈ 31.6/s」当成墙钟速率引用——那会把加载开销算成帧速。`
  - 对照脚本与原始 `ndjson`：
    - [run_mapsel_live.py:234-279](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/tools/run_mapsel_live.py#L234-L279)：`t1 = time.monotonic()` 设在点击 Continue 处；`el = time.monotonic() - t1`（L244）算的是**从点击 Continue 到发现 `ech02` 且 `frame > 10` 的墙钟耗时**；随后才记录 `f1 = cnt.get("frame")`（L270）、执行 **`time.sleep(2.5)`**（L271，真实墙钟睡眠 2.5 秒！）、读取 `f2`（L272），再把之前保存的 `el` 与之后的 `f1`/`f2`/`f2-f1` 写进同一条 `A2_confirmed`（L277-279）。
    - [w39_skip_no.ndjson:33-41](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/out/w39_skip_no.ndjson#L33-L41)：
      - L33 (`click_Continue`): `t_monotonic: 10289.093`
      - L37 (`frame: 44`): `t_monotonic: 10293.656`（`10293.656 - 10289.093 = 4.563 s` → `elapsed_s: 4.56`）
      - L38 (`A2_timer_confirm`, `frame: 123`): `t_monotonic: 10296.156`（**`10296.156 - 10293.656 = 2.500 s` 墙钟！**）
- **为什么是问题**：`2.5 s` 根本不是 Lead 推算的 `Δ79 ÷ 31.25 = 2.53 s 游戏时间`，而是代码里写死的 `time.sleep(2.5)`（精确 2.500 s 墙钟）！`elapsed_s: 4.56` 是 `frame=0 → 44`（点击 Continue 到进入采样分支）那一段加载/切换的墙钟时间，而非 `44 → 123` 的窗口。Lead 反过来指责 W39 `"混用了两个时间基准"` 并立下伪 `[纪律]`，暴露了 Lead 没核对 `run_mapsel_live.py` 与 `t_monotonic` 字段。
- **建议处置**：**撤回** [LEAD_VERDICT_Q2_CLOSED.md:88-97](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_Q2_CLOSED.md#L88-L97) 的“游戏时间 vs 墙钟 4.56 s”解释与对应 `[纪律]`，**改口径**写明：`elapsed_s=4.56` 为 `click_Continue → frame=44` 加载/检测耗时，`frame 44→123` 为随后 `time.sleep(2.5)` 墙钟窗口。

---

### [BLOCKER-3] `LEAD_VERDICT_Q2_CLOSED.md` 严重越权放大 W39 的 `scen_stage_idx=8` 与 `SkipMapSelect=no` 结论（含下标差 1 错误）
- **位置**：[LEAD_VERDICT_Q2_CLOSED.md:13, 51, 55, 120](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_Q2_CLOSED.md#L13) vs [UNKNOWNS.md:30-34, 45](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/UNKNOWNS.md#L30-L34)、[DISAGREE.md:30-32](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/DISAGREE.md#L30-L32)、[MAPSELMD_SPEC.md:65](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W34_mapselmd/MAPSELMD_SPEC.md#L65)、[LIVE_RESULT.md:49-50](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W35_mapselmd_live/LIVE_RESULT.md#L49-L50)
- **问题类型**：2（过度声明）/ 6（W39 真机结论）
- **原文摘引**：
  - [LEAD_VERDICT_Q2_CLOSED.md:51](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_Q2_CLOSED.md#L51)：`scen_stage_idx = 8               ← ★ 正是我们追加的 [Nod] 8=RA2F_ECH01_…`
  - [LEAD_VERDICT_Q2_CLOSED.md:55](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_Q2_CLOSED.md#L55)：`` `[本次实测]` **`scen_stage_idx=8` 是最硬的一条**：引擎确实把当前 stage 落到了我们追加的那一条，不是碰巧命中官方阶段。 ``
  - [LEAD_VERDICT_Q2_CLOSED.md:120](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_Q2_CLOSED.md#L120)：`v11 的生成逻辑（[Nod] 续号 + 独立阶段段 + Scenario= + 数字子项）在真机上可用`
  - 对照 W39 自述边界：
    - [UNKNOWNS.md:30-34](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/UNKNOWNS.md#L30-L34)：`A2 加载后 [Scen+0x35A0] 2 字节读数由 0 变 8 ... 该偏移的「当前阶段」语义来自既有反汇编 [转引]，非符号级证明；也可能是 battle 表索引、颜色索引等。本卡不据此宣称「引擎选中了第 8 阶段」。`
    - [UNKNOWNS.md:45](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/UNKNOWNS.md#L45)：`未测 SkipMapSelect=no 下的交互式 MapSelect 屏幕：本卡成功路径在 Continue 后直接进入 A2，没有出现需要点击的选关画面（脚本 --mapsel-click 未使用、也无需使用）。因此 ClickMap=NODCLK01.PCX + 颜色 2 的可点区域视觉表现仍未验证`
- **为什么是问题**：
  1. **下标差 1 错误**：据 [MAPSELMD_SPEC.md:65](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W34_mapselmd/MAPSELMD_SPEC.md#L65) 与 [LIVE_RESULT.md:49-50](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W35_mapselmd_live/LIVE_RESULT.md#L49-L50)，`DynamicVectorClass<MapStage*>` 是 0-based：`[Nod]` `1..7` 占索引 `0..6`，`8=RA2F_ECH01_2004FB14` 占索引 `7`，`9=RA2F_ECH02_1E0DEBE8` 才是索引 `8`（当前正在加载的 A2）。Lead 在 L51 把 `8` 硬说成 `[Nod] 8=RA2F_ECH01_…`，差了一格。
  2. **把 `[转引]` 语义升级为 `[本次实测]`**：W39（[UNKNOWNS.md:30-34](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/UNKNOWNS.md#L30-L34)）明确声明不据此宣称“选中了第 8 阶段”，Lead 却直接贴 `[本次实测]` 作为“最硬证据”。
  3. **过度外推 `SkipMapSelect=no` 与 `数字子项`**：W39 仅在单后继（`1=ECH02.MAP`）直跳情况下验证 `A1→A2` 跳过选关画面的行为，**从未实测出现可点击 MapSelect 屏幕的多分支 `数字子项`（如 `2=<next>`）或 `ClickMap=NODCLK01.PCX` 选关交互**（同时据 [DISAGREE.md:30-32](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/DISAGREE.md#L30-L32)，RPM 标记也未直接抓到引擎解析追加段的瞬间）。因果结论应限定为“**单变量对照证明 `MAPSELMD.INI` 补全 `RA2F_ECH01/ECH02` 段是消除 `A1→A2` 报错、推进至 `ECH02.MAP` 局内的必要条件（单后继免点击场景已通，交互式选关 `ClickMap`/`2=` 仍未验证）**”。
- **建议处置**：**改口径**——修正 `idx=8 ↔ 9=RA2F_ECH02`（若确为 0-based `MapStage` 索引），将 `[Scen+0x35A0]` 语义降回 `[转引]`，并将 L120 的 `数字子项 在真机上可用` 收窄为“单后继直进已验证，多分支交互式 MapSelect 选关待验”。

---

### [BLOCKER-4] `LEAD_VERIFY_W34.md:34` 虚假声称已修正“转大写”，且 `LEAD_VERDICT_map_start_root_cause.md` 合并了 W31/W33 的不同失败出口、漏掉 W31 同一处错误
- **位置**：
  - [LEAD_VERIFY_W34.md:34](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W34.md#L34)
  - [LEAD_W33_VERIFY.md:89](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L89)
  - [LEAD_VERDICT_map_start_root_cause.md:20-31, 78-80](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L20-L31)
  - 对照 [WHY_MAP_FAILS.md:105-111, 129, 140-141](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/WHY_MAP_FAILS.md#L105-L111) 与 [NEXTSCENARIO_FLOW.md:35-36, 115](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L35-L36)
- **问题类型**：1（结论冲突）/ 5（未经证实的因果：“两卡互证”）
- **原文摘引**：
  - [LEAD_VERIFY_W34.md:34](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W34.md#L34)：`并已在 REVIEW\LEAD_W33_VERIFY.md 与 REVIEW\LEAD_VERDICT_map_start_root_cause.md 里把"转大写"改口。`
  - [LEAD_W33_VERIFY.md:89](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L89)：`用 Scenario= 与 NextScenario 大写比对`（**未改口！**）
  - [WHY_MAP_FAILS.md:129, 141](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/WHY_MAP_FAILS.md#L129)：`0x7B5B30 统一大写后 0x7B4780 比较` / `与 NextScenario 大写比对（0x005AE073 call 0x7b4780）`（W31 犯了与 W33 完全相同的错误，但 Lead 签发裁定时未指出）
  - [LEAD_VERDICT_map_start_root_cause.md:23-30](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L23-L30)：把 `SkipMapSelect=no` 与 `SkipMapSelect=yes` 两条线合并为同一尾端：`→ 未命中 → 0x005AE320 打印 "MapSelect: Invalid stage!" → MapSelect::Init 返回 AL=0 → 0x005ADD95..0x005ADDCF 弹 CSF 标签 MSG:UnableMapSelect`。
- **为什么是问题**：
  1. **已宣布已改实未改**：[LEAD_VERIFY_W34.md:34](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W34.md#L34) 宣称已经改口，但 [LEAD_W33_VERIFY.md:89](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L89) 仍留着 `大写比对`。
  2. **“两卡互证”掩盖了双卡共同错误与分叉差异**：W31 与 W33 的**共同大方向结论**（缺失 `MAPSELMD.INI` 中 `ECH01.MAP`/`ECH02.MAP` 登记、且 H-A/H-B 不成立）确实互证，但**中间判定链并不等价**：
     - 两卡各自独立把 `0x7B5B30` 错认成 `转大写`（实为 `tolower` -> `0x7CAFF4`，直到 W34 才发现）；
     - W31 早期 `s09` 曾误判全局缺少 `MAPSELMD.INI`（靠 `CORRECTION_s09.md` 才纠偏），W33 又将容器 ID `0xFBE0D09D` 误读为加密名 ID（[W34/DISAGREE.md:9-25](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W34_mapselmd/DISAGREE.md#L9-L25)）；
     - Lead 的合图把 `SkipMapSelect=no`（`0x005AE320` + `0x005ADD95..0x005ADDCF`，`MapSel.CPP` `0x86`）与 `SkipMapSelect=yes`（`0x005ADFF3` / `0x005ADEE0..0x005ADEFA`，`MapSel.CPP` `0x98`）强行合并成同一条报错路径，与 [WHY_MAP_FAILS.md:105-111, 140-141](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/WHY_MAP_FAILS.md#L105-L111) 及 [NEXTSCENARIO_FLOW.md:36, 115](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L36) 冲突。
- **建议处置**：**改口径**——真正更新 [LEAD_W33_VERIFY.md:89](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L89) 与批注 W31 的 `转大写` 错误；拆开 [LEAD_VERDICT_map_start_root_cause.md:23-30](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L23-L30) 中 `SkipMapSelect=no` vs `yes` 两个失败退出地址，并明确标出“两卡仅主干原因互证，中间环节均含随后才由 W34 修正的瑕疵”。

---

## MAJOR（口径不实、前后打架或自证存在实质盲区）

### [MAJOR-1] `SOV07TMD.MAP` 的 `EndOfGame` 属性在 Lead 自身文件间直接打架
- **位置**：[LEAD_W33_VERIFY.md:48](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L48) vs [LEAD_VERDICT_map_start_root_cause.md:42](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L42)、[step9_exhaustive_checks.stdout.txt:21](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/EVIDENCE/step9_exhaustive_checks.stdout.txt#L21)
- **问题类型**：1（结论冲突）
- **原文摘引**：
  - [LEAD_W33_VERIFY.md:48](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L48)：`SOV07TMD.MAP     no             no`（表头 `EndOfGame | SkipMapSelect`）
  - [LEAD_VERDICT_map_start_root_cause.md:42](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L42)：`官方 14 张 MD 图：全部 SkipMapSelect=no（仅 ALL07SMD/SOV07TMD 的 EndOfGame=yes）`
  - 原始输出 [step9_exhaustive_checks.stdout.txt:21](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/EVIDENCE/step9_exhaustive_checks.stdout.txt#L21)：`SOV07TMD.MAP.basic.txt: ... b'EndOfGame=yes\r\n' | b'SkipScore=no\r\n' | b'SkipMapSelect=no\r\n'`
- **为什么是问题**：Lead 在 [LEAD_W33_VERIFY.md:48](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L48) 把 `SOV07TMD.MAP` 的 `EndOfGame` 抄成了 `no`，随后自己签发 [LEAD_VERDICT_map_start_root_cause.md:42](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L42) 时按原证据写回 `yes`，但未回改前件。
- **建议处置**：**改口径**——将 [LEAD_W33_VERIFY.md:48](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L48) 更正为 `SOV07TMD.MAP     yes            no`。

---

### [MAJOR-2] `LEAD_VERDICT_campaign_menu_q1.md` 文内自我打架 + `tut1` 3 槽位已被 W37 证伪仍未收回
- **位置**：[LEAD_VERDICT_campaign_menu_q1.md:14, 70-72, 84](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_campaign_menu_q1.md#L14) vs [LEAD_VERIFY_W37.md:22](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W37.md#L22)
- **问题类型**：1（结论冲突）/ 7（已降级/证伪陈述仍活着）
- **原文摘引**：
  - [LEAD_VERDICT_campaign_menu_q1.md:14](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_campaign_menu_q1.md#L14)：`追加 battle id 出现在隐藏 ListBox(1109) 里 | 有条件可达，被一个字节 [0xA8F7AD] 门控 | 可开`
  - [LEAD_VERDICT_campaign_menu_q1.md:70-72](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_campaign_menu_q1.md#L70-L72)：`因此隐藏调试列表不是「条件可达」而是「实测不可达」… 我此前在 §1 表格与 §4 旧稿里写「有条件可达」，据此下调。`
  - [LEAD_VERDICT_campaign_menu_q1.md:84](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_campaign_menu_q1.md#L84)：`1. 借用官方 id（ALL1/SOV1/tut1 三槽之一）`
  - [LEAD_VERIFY_W37.md:22](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W37.md#L22)：`没有 tut1 条目，也没有任何 [TUT*] 段`（`可借用入口只有 2 个，不是 3 个`）
- **为什么是问题**：§4.2 明明写着已将 §1 表格下调为“实测不可达”，但同文件 §1 第 14 行摘要表仍原封不动写着 `"有条件可达，被一个字节 [0xA8F7AD] 门控"`；同时 §4.3 L84 仍写“三槽之一（含 `tut1`）”，而 W37 已证实官版 `BATTLEMD.INI` 并无 `tut1` 槽位。
- **建议处置**：**改口径**——同步修订 [LEAD_VERDICT_campaign_menu_q1.md:14](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_campaign_menu_q1.md#L14) 摘要表（标明零售实测不可达、需 patch）与 L84（改为 `ALL1`/`SOV1` 两槽之一）。

---

### [MAJOR-3] `LoadBattleMdIni (0x52CB90)` 回退触发条件在 W29 与 W37（及对应 VERIFY 文档）间冲突
- **位置**：
  - [LEAD_W29_VERIFY.md:44](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W29_VERIFY.md#L44)、[OVERRIDE_ORDER.md:22, 197-198](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W29_override_order/OVERRIDE_ORDER.md#L22)
  - vs [LEAD_VERIFY_W37.md:31, 76](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W37.md#L31)、[BORROW_FEASIBILITY.md:235-237](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W37_official_id_borrow/BORROW_FEASIBILITY.md#L235-L237)
- **问题类型**：1（结论冲突）
- **原文摘引**：
  - [LEAD_W29_VERIFY.md:44](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W29_VERIFY.md#L44)（同 [OVERRIDE_ORDER.md:22, 198](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W29_override_order/OVERRIDE_ORDER.md#L22)）：`回退分支（CCFileClass("BATTLEMD.INI")，mix 感知）仅当目录里一个 BATTLEMD*.INI 都没有时才执行`
  - [OVERRIDE_ORDER.md:197](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W29_override_order/OVERRIDE_ORDER.md#L197) 自己紧挨着写的指令译文却是：`已见 BATTLEMD.INI → 跳过回退`
  - [BORROW_FEASIBILITY.md:235-237](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W37_official_id_borrow/BORROW_FEASIBILITY.md#L235-L237)（及 [LEAD_VERIFY_W37.md:31, 76](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W37.md#L31)）：依据 `0x52CC54`（`_stricmp` 比对 `"BATTLEMD.INI"`）与 `0x52CCC7 jne 0x52CD5F`，只要目录中没有名为 `BATTLEMD.INI` 的散件，**即使存在 `BATTLEMD98.INI` 也会执行回退**（进而决定 B 线(a)原位改写 `BATTLEMD.INI` vs (b)写 `BATTLEMD98.INI` 后被回退覆盖的风险）。
- **为什么是问题**：直接影响 B 线设计方案选型（方案(a) vs 方案(b)）。W29 报告自己第 197 行与第 198 行就已经矛盾，Lead 签发 [LEAD_W29_VERIFY.md:44](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W29_VERIFY.md#L44) 时照搬了错误概括，后来签发 [LEAD_VERIFY_W37.md:31, 76](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W37.md#L31) 时发现该差异，但未回改 W29 签发文。
- **建议处置**：**改口径**——修正 [LEAD_W29_VERIFY.md:44](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W29_VERIFY.md#L44) 为“仅当目录中未枚举到 `BATTLEMD.INI` 本身时才执行回退（并非一个 `BATTLEMD*.INI` 都没有）”。

---

### [MAJOR-4] 已修正的误读字符串 `"無法啟動選取地圖!"` 在多份卡片正文中仍未标废
- **位置**：
  - [NEXTSCENARIO_FLOW.md:43, 45](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L43)（对比同文 L18、L49 `無法啟始選取地圖！\n`）
  - [CAMPAIGN_LIVE.md:12, 97, 105, 152](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W27_campaign_live/CAMPAIGN_LIVE.md#L12)
  - [NEXTSCENARIO_FORM.md:5, 15](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W28_nextscenario_form/NEXTSCENARIO_FORM.md#L5)
  - 对照勘误依据：[LEAD_FACT_map_error_label.md:21, 27-28](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_FACT_map_error_label.md#L21)、[W31/DISAGREE.md:5-17](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/DISAGREE.md#L5-L17)、[W39/DISAGREE.md:7-12](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/DISAGREE.md#L7-L12)
- **问题类型**：7（已撤回/纠偏陈述仍活着）
- **原文摘引**：[NEXTSCENARIO_FLOW.md:43, 45](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L43) 在同一份报告前 18 行还正确引用了 `「無法啟始選取地圖！\n」`，后文 L43、L45 却又退回 `「無法啟動選取地圖!」`；W27、W28 主体报告则全面使用 `無法啟動選取地圖!` 且未附勘误尾注。
- **为什么是问题**：Lead 在 [LEAD_FACT_map_error_label.md:21, 27-28](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_FACT_map_error_label.md#L21) 与 [LEAD_W27_RAW_VERDICT.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W27_RAW_VERDICT.md) 已专门锁定真机文本为 `「無法啟始選取地圖！\n」`（第 3 字是**始**非**動**、全角感叹号+换行），W33 自相矛盾尤为明显。
- **建议处置**：**改口径**——在 [NEXTSCENARIO_FLOW.md:43, 45](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L43) 改回 `無法啟始選取地圖！\n`，并在 W27/W28 文档顶部或引用处加注以 [LEAD_FACT_map_error_label.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_FACT_map_error_label.md) 为准。
- **核查补充（其余 7 类已知撤回项均已确认清理）**：
  - `描述文本只影响显示不影响功能`：已在 [LEAD_W27_RAW_VERDICT.md:192, 223](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W27_RAW_VERDICT.md#L192) 明确撤回；
  - `LB_GETCOUNT=0 是破绽`：已在 W32 与 [LEAD_VERDICT_campaign_menu_q1.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_campaign_menu_q1.md) 降格并证伪为零售设计；
  - `永久冻结 / 229 s` 与 `3.104e9 cyc/ms`：在全部 11 份 `REVIEW/` 与所查卡片中**未见残留**（W39 使用 32 ms 定时节拍 31.25/s）。

---

### [MAJOR-5] 纪律自证与隔离证据存在范围缺口（W38 `git status` 只扫 `W21*`、部分真机/分析卡缺事前事后快照）
- **位置**：
  - [VERSION_GUARD_CONTRACT.md:4](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W38_version_guard_s1/VERSION_GUARD_CONTRACT.md#L4)、[UNCOVERED.md:51](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W38_version_guard_s1/UNCOVERED.md#L51) vs [ACCEPTANCE.md:79](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W38_version_guard_s1/ACCEPTANCE.md#L79)、[git_before.txt:1](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W38_version_guard_s1/EVIDENCE/git_before.txt#L1)、[git_after.txt:1](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W38_version_guard_s1/EVIDENCE/git_after.txt#L1)
  - [manifest.py:36-39](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/tools/manifest.py#L36-L39)、[verify_pre.log:1-21](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/out/verify_pre.log#L1-L21)、[verify_post.log:1-17](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/out/verify_post.log#L1-L17)
  - 无快照纯口述卡：[W31/UNKNOWNS.md:53-54](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/UNKNOWNS.md#L53-L54)、[B_LINE_PLAN.md:5, 396](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W36_b_line_kickoff/B_LINE_PLAN.md#L5)、[BORROW_FEASIBILITY.md:542-545](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W37_official_id_borrow/BORROW_FEASIBILITY.md#L542-L545)
- **问题类型**：8（纪律自证可信度）
- **原文摘引与事实核对**：
  1. **W38 自证与实际 `pathspec` 严重不符**：[VERSION_GUARD_CONTRACT.md:4](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W38_version_guard_s1/VERSION_GUARD_CONTRACT.md#L4) 与 [UNCOVERED.md:51](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W38_version_guard_s1/UNCOVERED.md#L51) 宣称 `未动 W21–W37 任何目录`，但 [ACCEPTANCE.md:79](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W38_version_guard_s1/ACCEPTANCE.md#L79) 及 `git_before.txt` / `git_after.txt` 实际执行的是 `git status --porcelain -- ra2forge/ ra2youli/ 'lead/next_re_20261112_r02/W21*'`——只覆盖 `W21*`，**根本没有检查 `W22–W37`**！
  2. **W27 / W35 / W39 `IDENTICAL_TREE=True` 核验结果**：经查 [W39/tools/diff_real.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/tools/diff_real.py) 与 [W39/tools/manifest.py:1-68](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/tools/manifest.py#L1-L68)，它**不是**空集 `all()`、也**不是**只比对文件数，而是逐文件比对 `pre["files"] == post["files"]`（647 项包含 `size`、`mtime_ns`、`sha256`）。但需注意两处局限：
     - [manifest.py:36-39](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/tools/manifest.py#L36-L39) 存在 `except OSError: continue` 静默吞异常分支（若遇权限/锁文件会跳过）；
     - W39 的 [verify_pre.log](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/out/verify_pre.log) 与 [verify_post.log](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/out/verify_post.log) 跑的是 v9 `verify`，仅核验 manifest 内 4 个文件（`BATTLEMD98.INI`、`ECH01.MAP`、`ECH02.MAP`、`expandmd98.mix`），把 `MAPSELMD.INI` 标为 untracked（好在 W39 另有 `prep_check` / `restore_file` 与整树 647 项哈希比对兜底）。
  3. **W31 / W36 / W37** 仅在文档中口头声明未改 `ra2youli` 或其它目录，无对应的 `git status` 或哈希快照证据保存。
- **建议处置**：**补证据 / 改口径**——W38 将声明范围改实为 `W21*` 或补充全 `lead/next_re_20261112_r02/` 的 `git status` 证据；后续真机卡在 `manifest.py` 中移除/记录 `OSError` 而不是静默 `continue`。

---

## MINOR（笔误、编号跳跃、未对齐的时间性旧注）

1. **[MINOR-1] `MAPSELMD.INI` SHA-256 缩写多打一个 `9`**
   - **位置**：[LEAD_VERDICT_map_start_root_cause.md:46](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L46)、[BORROW_FEASIBILITY.md:473](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W37_official_id_borrow/BORROW_FEASIBILITY.md#L473)
   - **类型**：3（数值不一致）
   - **原文**：`074ccccd…6919d52`（[LEAD_W33_VERIFY.md:131](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L131) 与 [LEAD_VERIFY_W34.md:16](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W34.md#L16) 完整哈希尾缀实为 `…691d52`，无中间那个 `9`）。
   - **处置**：**改口径**（笔误修正为 `…691d52`）。

2. **[MINOR-2] Lead 签发文件章节序号跳跃/错序**
   - **位置**：[LEAD_VERDICT_campaign_menu_q1.md:89-91](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_campaign_menu_q1.md#L89-L91)（`4.3` 直接跳到 `6.`，缺少 `§5`）；[LEAD_W27_RAW_VERDICT.md:218-260](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W27_RAW_VERDICT.md#L218-L260)（编号顺序为 `7. → 9. → 8.`）。
   - **类型**：3（编号不一致）
   - **处置**：**改口径**（整理章节号）。

3. **[MINOR-3] W35 产物状态的过时时间注记**
   - **位置**：[B_LINE_PLAN.md:98](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W36_b_line_kickoff/B_LINE_PLAN.md#L98)、[LEAD_VERIFY_W36.md:20](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W36.md#L20)
   - **类型**：1（时间性旧注未标记）
   - **原文**：称 W35 尚无 `LIVE_RESULT.md` / `REAL_DIR_PROOF.txt`（18:30 时点正确，W35 完成后已在 [LEAD_VERDICT_Q2_CLOSED.md:149](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_Q2_CLOSED.md#L149) 更新）。
   - **处置**：**改口径**（在 [LEAD_VERIFY_W36.md:20](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W36.md#L20) 补注“撰写时点 18:30，后续已由 W35/W39 收口”）。

4. **[MINOR-4] `MAPSELMD.INI` 打印输出行数 vs 物理行数口径差**
   - **位置**：[LEAD_W33_VERIFY.md:185](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L185) 引用 [step10_close_gaps.stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/EVIDENCE/step10_close_gaps.stdout.txt) `第 10–533 行` vs W34/W37/W39 的 `261 行全 CRLF`。
   - **类型**：3（行数口径）
   - **原因**：`step10` 控制台回显每行后带空行导致行号翻倍，并非文件本身 524 行。建议注明为“回显含空行，文件本体 261 行 CRLF”。

---

# 二、CONFLICT_TABLE（跨文件关键事实对照表）

| 核查主题 | 一致部分（多处已核对一致） | 冲突 / 偏差方 A | 冲突 / 偏差方 B | 裁定与归因 |
| :--- | :--- | :--- | :--- | :--- |
| **`MAPSELMD.INI` 物理属性** | 同体文件，`261` 行 CRLF（SHA-256 完整尾缀 `…691d52`；`zlib.crc32 = 0x922b8ce7`） | [LEAD_VERDICT_map_start_root_cause.md:46](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L46)、[BORROW_FEASIBILITY.md:473](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W37_official_id_borrow/BORROW_FEASIBILITY.md#L473)：简写 `074ccccd…6919d52` | [LEAD_W33_VERIFY.md:131](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L131)、[LEAD_VERIFY_W34.md:16](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W34.md#L16)：完整尾缀 `…691d52` | **冲突（MINOR-1）**：`6919d52` 为笔误；`step10` `533 行` 系打印隔行空行（MINOR-4）。 |
| **`0xFBE0D09D` 来历** | 十六进制 ID 值本身一致 | [MAPSELMD_SPEC.md:40](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W34_mapselmd/MAPSELMD_SPEC.md#L40)：`= mixlib.ts_crc_hash("LOCALMD.MIX")` | [LEAD_W33_VERIFY.md:142-152](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L142-L152)、[LEAD_VERIFY_W34.md:40-52](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W34.md#L40-L52)、[LEAD_VERDICT_map_start_root_cause.md:72](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L72)：称“验算不成立、不得引用” | **冲突（BLOCKER-1）**：Lead 用零填充变体误测，[mixlib.py:210-217](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W30_csf_capability/ra2forge_patched_v10/ra2forge/mixlib.py#L210-L217) 的 `ts_crc_hash` 确能算出 `0xFBE0D09D`。 |
| **`SOV07TMD.MAP EndOfGame`** | 其余 13 张官方 MD 图与 `SkipMapSelect=no` 一致 | [LEAD_W33_VERIFY.md:48](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L48)：`no` | [LEAD_VERDICT_map_start_root_cause.md:42](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L42)、[step9_exhaustive_checks.stdout.txt:21](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/EVIDENCE/step9_exhaustive_checks.stdout.txt#L21)：`yes` | **冲突（MAJOR-1）**：原始转储为 `EndOfGame=yes`。 |
| **`0x7B5B30` 归一化语义** | W34 查出实为 `tolower` (`0x7CAFF4`) | [WHY_MAP_FAILS.md:129,141](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/WHY_MAP_FAILS.md#L129)、[NEXTSCENARIO_FLOW.md:35](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L35)、[LEAD_W33_VERIFY.md:89](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L89)：`转大写` / `大写比对` | [LEAD_VERIFY_W34.md:34](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W34.md#L34)：声称已把 `LEAD_W33_VERIFY` 改口 | **冲突（BLOCKER-4）**：`LEAD_W33_VERIFY.md:89` 未改口，且 W31 同病漏改。 |
| **`LoadBattleMdIni` 回退条件** | 函数地址 `0x52CB90`，按 `BATTLEMD*.INI` 顺序加载 | [LEAD_W29_VERIFY.md:44](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W29_VERIFY.md#L44)、[OVERRIDE_ORDER.md:22,198](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W29_override_order/OVERRIDE_ORDER.md#L22)：仅当一个 `BATTLEMD*.INI` 都没有时 | [LEAD_VERIFY_W37.md:31,76](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W37.md#L31)、[BORROW_FEASIBILITY.md:235-237](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W37_official_id_borrow/BORROW_FEASIBILITY.md#L235-L237)、[OVERRIDE_ORDER.md:197](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W29_override_order/OVERRIDE_ORDER.md#L197)：缺 `BATTLEMD.INI` 即回退 | **冲突（MAJOR-3）**：W29 L197 自证 L198 有误。 |
| **Q1 菜单槽位与隐藏 ListBox 1109** | `0xA8F7AD` 门控、零售 `LB_GETCOUNT=0` 为原版设计 | [LEAD_VERDICT_campaign_menu_q1.md:14,84](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_campaign_menu_q1.md#L14)：1109“有条件可达”、可借 `ALL1/SOV1/tut1` 三槽 | [LEAD_VERDICT_campaign_menu_q1.md:70-72](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_campaign_menu_q1.md#L70-L72)（实测不可达）；[LEAD_VERIFY_W37.md:22](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W37.md#L22)（无 `tut1`，仅 2 槽） | **冲突（MAJOR-2）**：摘要表与正文中后段及后续 W37 未同步。 |
| **W39 `frame 44→123` 与 `elapsed_s=4.56`** | `f1=44`, `f2=123`, `Δ79`, `elapsed_s=4.56` 数值一致 | [LEAD_VERDICT_Q2_CLOSED.md:90-97](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_Q2_CLOSED.md#L90-L97)：称 `2.5s` 为游戏时间、`4.56s` 为同一窗口墙钟 | [run_mapsel_live.py:244,271](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/tools/run_mapsel_live.py#L244)、[w39_skip_no.ndjson:33-41](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/out/w39_skip_no.ndjson#L33-L41)：`4.563s` 在 `44` 之前，`2.500s` 为 `sleep(2.5)` 墙钟 | **冲突（BLOCKER-2）**：Lead 误读时序。 |
| **W39 `scen_stage_idx=8` 与 `数字子项`** | `[Scen+0x35A0]` 由 `0` 变 `8` | [LEAD_VERDICT_Q2_CLOSED.md:51,55,120](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_Q2_CLOSED.md#L51)：标 `[Nod] 8=RA2F_ECH01`、称 `[本次实测]` 最硬证据及 `数字子项` 可用 | [W39/UNKNOWNS.md:30-34,45](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W39_mapselmd_live2/UNKNOWNS.md#L30-L34)（不宣称选中第8阶段、未测交互选关）、[MAPSELMD_SPEC.md:65](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W34_mapselmd/MAPSELMD_SPEC.md#L65)（0-based idx `8` 是 `9=RA2F_ECH02`） | **冲突（BLOCKER-3）**：下标差 1 + 口径过度放大。 |
| **错误框 CSF 标签全文** | key=`MSG:UnableMapSelect`, `5,211` 条（`332,973 B`；`v10` 前 `4,479` 条） | [CAMPAIGN_LIVE.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W27_campaign_live/CAMPAIGN_LIVE.md)、[NEXTSCENARIO_FORM.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W28_nextscenario_form/NEXTSCENARIO_FORM.md)、[NEXTSCENARIO_FLOW.md:43,45](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L43)：`無法啟動選取地圖!` | [LEAD_FACT_map_error_label.md:21,27-28](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_FACT_map_error_label.md#L21)、[NEXTSCENARIO_FLOW.md:18,49](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L18)：`無法啟始選取地圖！\n` | **冲突（MAJOR-4）**：第 3 字为 `始`。 |
| **W38 自证与真机 tree 校验** | W27/W35/W39 `diff_real.py` 比对整树 647 项（含 `sha256`） | [VERSION_GUARD_CONTRACT.md:4](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W38_version_guard_s1/VERSION_GUARD_CONTRACT.md#L4)：宣称未动 `W21–W37` | [ACCEPTANCE.md:79](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W38_version_guard_s1/ACCEPTANCE.md#L79)、[git_before.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W38_version_guard_s1/EVIDENCE/git_before.txt)：`pathspec` 仅查 `W21*` | **冲突（MAJOR-5）**：W38 自证范围窄于声明。 |
| **地址换算口径、模块数与用例数演进** | `.text`：`FOFF = VA - 0x400000`；`.rsrc`：`FOFF = RVA - 0x2FC000`（[MENU_ENTRIES.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W32_campaign_menu_entries/MENU_ENTRIES.md)）。用例数增量一致：`39` → `45`（`+6`, W30 `v10`）→ `51`（`+6`, W34 `v11`）。 | — | — | **经核查无混用/无冲突**（注：模块数 `11/12/13/14` 跨文件演进详情未逐卡做全库统计，归入 UNKNOWNS）。 |

---

# 三、UNKNOWNS（W43 在当前约束下无法裁定的部分）

1. **只读 `/plan` 约束下未重跑代码与真机**：
   - 未重新执行 `ra2forge_patched_v10` / `v11` 的 45 / 51 个离线单测，无法核实当前工作区测试实际通过情况（仅见报告文字记录）。
   - 未重跑反汇编验证 W31/W33 之外的其它未知调用点，或确认 `[Scen+0x35A0]==8` 在游戏进程内除 `MapStage` 0-based 索引 `8`（`[Nod] 9=RA2F_ECH02`）外是否受其它字段别名影响（仍从 W39 之 `[转引]` 口径）。
2. **未启动多 branches 交互式 `MapSelect` 选关界面**：
   - W39 仅跑通单后继（`1=ECH02.MAP`）直进场景，因此 `2=<next>` 等多分支选关渲染、`ClickMap=NODCLK01.PCX` 与颜色 2 热区点击、以及 W39 为何在 `SkipMapSelect=no` 下跳过界面而非弹出选关图，均属现阶段未实测空白。
3. **未逐个打开图像或范围外早期卡片**：
   - 截图文件（如 W27 `screen_p3_I1_briefing_or_later.png`、W39 `crop_w39_error_text.png`）与本次 11 份 `REVIEW/` + `W27–W39` 主报告范围之外的文件（如 `LEAD_STATUS_W25_incomplete.md`、`LEAD_FINDING_campaign_text_is_csf.md`、`LEAD_CORRECTION_campaign_blockers.md`、以及各卡的 `APPLY.md` / 全量 `DISAGREE` 附件和模块数 `11/12/13/14` 演进全貌）未全面展开核查，W43 不对其做无证据推断。

---

# 四、建议处置计划（待切换可执行状态后按此落地）

1. **优先修订 Lead 4 处 BLOCKER 裁定**：
   - 用 [mixlib.py:210-217](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W30_csf_capability/ra2forge_patched_v10/ra2forge/mixlib.py#L210-L217) 的 `ts_crc_hash("LOCALMD.MIX")` 复核后，撤销 [LEAD_W33_VERIFY.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md)、[LEAD_VERIFY_W34.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W34.md)、[LEAD_VERDICT_map_start_root_cause.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md)、[LEAD_VERIFY_W37.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W37.md) 中对 `0xFBE0D09D` 的错判。
   - 修正 [LEAD_VERDICT_Q2_CLOSED.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_Q2_CLOSED.md)：删除 `2.5s` 为游戏时间的错误 §6 批注；将 `scen_stage_idx=8` 对齐到 0-based `9=RA2F_ECH02` 且恢复 `[转引]` 标签；将 `v11` 真机可用范围收窄到“单后继直接进入 A2”。
   - 真正把 `tolower`（非“转大写”）同步回 [LEAD_W33_VERIFY.md:89](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L89) 并批注 W31 的 `WHY_MAP_FAILS.md:129,141`；拆分 [LEAD_VERDICT_map_start_root_cause.md:20-31](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L20-L31) 中 `SkipMapSelect=no` vs `yes` 两个失败退出分支。
2. **对齐 MAJOR 遗留**：更新 `SOV07TMD.MAP EndOfGame=yes`、[LEAD_VERDICT_campaign_menu_q1.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_campaign_menu_q1.md) 第 14/84 行、`LoadBattleMdIni` 回退条件、`無法啟始選取地圖！\n` 统一标注，并补齐 W38 全目录 `git status` 检查。

---

### Handoff
- **Outcome**: 完成 `NEXT_RE_20261112_R02` 全部 11 份 `REVIEW/` 签发文与 `W27–W39` 产物的交叉一致性审计，识别出 **4 项 `BLOCKER`、5 项 `MAJOR`、4 项 `MINOR`** 与完整冲突对照表及未知边界清单。
- **Files Changed**: **无**（严格遵守只读 `/plan` 约束，未创建 `lead/next_re_20261112_r02/W43_consistency_audit/`，也未改动任何代码或文档）。
- **Verification Performed**: 使用只读工具核对了 [step9_exhaustive_checks.stdout.txt:1-30](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/EVIDENCE/step9_exhaustive_checks.stdout.txt#L1-L30) 原始 `mapsmd03.mix` 转储，并逐字回对了全部 11 份 `REVIEW/`、W27–W39 报告、`run_mapsel_live.py`、`manifest.py`、`mixlib.py`、`git_before.txt`/`git_after.txt` 及 `w39_skip_no.ndjson`。
- **Blockers / Remaining Risks**: 若要将上述 `AUDIT_REPORT.md` / `CONFLICT_TABLE.md` / `UNKNOWNS.md` 写入 `lead/next_re_20261112_r02/W43_consistency_audit/` 并落地修正 Lead 签发件，需退出 `/plan` 只读模式并明确授权写入。

## Prompt sent to Antigravity

```text
你是 RA2 Campaign Forge 的**交叉一致性审计卡 W43**。任务：**以第三方视角审计本会话（run_id `NEXT_RE_20261112_R02`）全部签发文件与卡片产物之间的一致性，专门找互相矛盾、过度声明、以及"结论超出证据"的地方。**

工作目录：`D:\Project\ra2-campaign-forge`

## 为什么要你做
本项目贯穿一条纪律：**代理的自我总结不可信，必须回对原始证据**。本次已有多个实例：W25 自述全绿实为 36/39；W27 脚本 `chain_results.q2` 自述"未出现胜利/结算屏"实为假阴性（截图里「任務完成」清晰可见）；某卡把 `0x922B8CE7` 的来历解释错了但产物是对的。**现在要让一个不同的模型来挑 Lead 自己的判断。**

## 审计对象

### A. Lead 的签发文件（在 `lead\next_re_20261112_r02\REVIEW\`）
- `LEAD_VERDICT_map_start_root_cause.md`（关卡推进根因，W31+W33 双卡互证）
- `LEAD_VERDICT_campaign_menu_q1.md`（战役菜单结构性封死）
- `LEAD_W27_RAW_VERDICT.md`（W27 真机卡复核）
- `LEAD_W28_VERIFY.md`、`LEAD_W29_VERIFY.md`、`LEAD_W33_VERIFY.md`
- `LEAD_VERIFY_W34.md`、`LEAD_VERIFY_W36.md`、`LEAD_VERIFY_W37.md`
- `LEAD_FACT_map_error_label.md`

### B. 卡片产物（各自目录）
`W27_campaign_live\`、`W28_nextscenario_form\`、`W29_override_order\`、`W30_csf_capability\`、`W31_map_start_failure\`、`W32_campaign_menu_entries\`、`W33_nextscenario_dataflow\`、`W34_mapselmd\`、`W35_mapselmd_live\`、`W36_b_line_kickoff\`、`W37_official_id_borrow\`、`W38_version_guard_s1\`、`W39_mapselmd_live2\`（含 `LIVE_RESULT.md` / `out\*.ndjson`）

## 要专门查的 8 类问题

1. **结论冲突**：两个文件对同一事实给出不同说法。例：`MAPSELMD.INI` 的物理位置（文件偏移、长度、SHA-256、行数）在各处是否一致？`0xFBE0D09D` 的来历是否被某处当"事实"写了？
2. **过度声明**：把 `[静态推断]`/`[转引]` 写成 `[本次实测]`；把"离线回归全绿"写成"功能可用"；把"已收窄到某分支"写成"已定位根因"。
3. **数值不一致**：镜像/文件 SHA-256、字节数、模块数（11/13/14）、用例数（39/45/51）、地址（VA/RVA/FOFF）、`frame` 数值、标签数（5,211）等在多处是否一致。
4. **地址口径**：是否有把 RVA 当 VA（或反之）的地方？`.text` 内 `FOFF = VA − 0x400000` 这条是否被一致使用？
5. **未经证实的因果**：`LEAD_VERDICT_map_start_root_cause.md` 说"两卡互证"，请核对 W31 与 W33 的**判定链是否真的等价**，还是只是结论相同、路径不同、其中一卡的中间步骤有错但被另一卡掩盖。
6. **W39 的真机结论**：`run_outcome=A2_loaded` 与负对照 `error_dialog_GUI_OK` 是否足以支撑"MAPSELMD 登记是成功原因"？检查 `out\w39_skip_no.ndjson` 与 `out\w39_control_official.ndjson`，注意 `scen_stage_idx`、`scen_filename`、`frame` 的实际数值与报告描述是否一致（**报告里有个说法是 "frame 44→123（2.5s，Δ79，≈31.6/s）"，而 ndjson 里 `elapsed_s` 是 4.56 —— 请核对这是口径问题还是错误**）。
7. **已撤回/已降级的陈述是否还在某处活着**：例：「描述文本只影响显示不影响功能」（应已撤回）、「永久冻结/229 s」旧定性、「3.104e9 cyc/ms」单位错误、「LB_GETCOUNT=0 是破绽」（已被 W32 否证为零售设计）。
8. **纪律自证是否可信**：各卡声称"未写 ra2youli / 未改仓库"，`LEAD_W27_RAW_VERDICT.md` 与 `W35`/`W39` 都有 `IDENTICAL_TREE=True` 的自证；核对是否存在**自证方式本身不可靠**（例如 `all()` 遍历空集为真、只比对了文件数没比哈希）。

## 输出要求

- 每条问题给：**位置（file:line 或 file 段落）**、**问题类型**（1–8 之一）、**原文摘引**、**为什么是问题**、**建议处置**（改口径 / 补证据 / 撤回）
- 按**严重度**排序：`BLOCKER`（会误导工程决策）/ `MAJOR`（口径不实但方向对）/ `MINOR`（笔误）
- **不要重做反汇编**，不要启动游戏。你只做文本与产物的一致性核对；对代码级结论只核"引用是否自洽"，不核"代码是否真的如此"
- 若你发现 Lead 的判断有错，**直接说，不要客气**。这份审计的价值就在于挑错

## 交付（只写这个目录）
`lead\next_re_20261112_r02\W43_consistency_audit\`
- `AUDIT_REPORT.md`（按严重度排序的问题清单 + 每条的建议处置）
- `CONFLICT_TABLE.md`（同一事实在不同文件的取值对照表，标出不一致项）
- `UNKNOWNS.md`（你无法判断的部分，以及为什么）



Workspace: D:\Project\ra2-campaign-forge
- For a text-only or connectivity task, reply directly without inspecting files or running tools.
- Report changed workspace paths relative to this workspace.
- Treat additional accessible directories as context unless the task explicitly targets one; report an explicit external target by absolute path.
- This is a planning/read-only posture: do not create, edit, delete, or rename workspace files.
- Prefer native read-only file tools for inspection. Do not use a shell command merely to list or read files.
- Return the plan or findings in the final response rather than writing a deliverable file.

At the end, return a concise handoff covering: outcome, files changed (if any), verification performed, and any blockers or remaining risks.
Keep inspection proportional to the task: avoid unbounded recursive enumeration, and if remaining time is limited, stop exploring and deliver the evidence already gathered.
```

## Run

- status: `SUCCESS`
- process_exit_code: `0`
- conversation_id: `9d60efa6-ac9e-4bb1-890a-aea1ff938973`
- model: `gemini-4-hydrogen-high`
- mode: `plan`
- permission_mode: `always-proceed`
- receipt_path: `C:\Users\Administrator\AppData\Local\Temp\call-agy\.staging\20261113-105452-8148-cea3bfedf8d08f1f-receipt.md`
- wrapper_watchdog: `2730.0s`
- agy_total_timeout: `2700s`
- idle_warning: `10m`
- idle_grace: `5m`
- elapsed: `613.1s`
- agy_cumulative_duration_seconds: `599.5725053`
- agy_cumulative_num_turns: `1`

## Tools used

- `read_file` ×202

## Attempt history

- attempt 1: native_status=SUCCESS, exit=0, elapsed=613.062s, conversation_id=9d60efa6-ac9e-4bb1-890a-aea1ff938973, tools={'read_file': 202}

## Usage reported by AGY

_These are native AGY counters. On resumed conversations they may be cumulative; do not add cache_read_tokens to total_tokens or infer billing without provider evidence._

- input_tokens: `1324168`
- output_tokens: `106547`
- thinking_tokens: `32903`
- cache_read_tokens: `2468829`
- total_tokens: `1430715`

---
Generated by `call-agy` via the official local `agy` CLI. Raw tool arguments/outputs are omitted by default.
