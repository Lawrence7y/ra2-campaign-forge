# 第二轮交叉一致性审计报告（AUDIT_ROUND2）

> 审计卡：W52（只做文本与产物一致性核对；不重做反汇编、不启动游戏）  
> 审计对象：`D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\REVIEW\` 下 Lead 最新 9 份签发/裁决/事实文档及其直接引用的关联文档与产物  
> 排序规则：按严重度 `BLOCKER` → `MAJOR` → `MINOR` 排列

---

## BLOCKER

### [BLOCKER-1] `LEAD_DECISIONS_W42.md` D3 / D3-补 / D5.1 自相矛盾，且签发了与裁决口径相反的 v13 实现
- **位置**：[LEAD_DECISIONS_W42.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_DECISIONS_W42.md#L44)、[第 83-88 行](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_DECISIONS_W42.md#L83-L88)、[第 112-113 行](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_DECISIONS_W42.md#L112-L113)；对照 [feature_subset.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W43_b_line_s3/ra2forge_patched_v13/ra2forge/feature_subset.py#L368-L371) 与 [S3_IMPLEMENTATION.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W43_b_line_s3/S3_IMPLEMENTATION.md#L106)
- **类型**：裁决自相矛盾 + 签发结论与实际代码脱节
- **原文摘引**：
  - D3（`LEAD_DECISIONS_W42.md:44`）：
    > `**裁决：不补硬拒绝，保持「警告 + 显式确认」，但要求 resolve() 在 csf 与 MAPSELMD 同时开启、而 BATTLEMD98.INI 被显式关闭时，输出一条**可机检的警告**（进 warnings[]），并在安装摘要里可见。**`
  - D3-补（`LEAD_DECISIONS_W42.md:83-88`）：
    > `**裁决（澄清，不推翻 D3 原意）**：`
    > `1. **K2 保留硬拒绝**（csf 开而 battlemd.mode=off ⇒ 拒绝）。`
    > `2. **G3 的活例子收窄为**：maps 开 + mapselmd 开 + battlemd.mode=off + csf 关 ⇒ **只警告不拒绝**。`
    > `3. W43 提出的实现取舍我认可：**K2 硬拒绝；G3 只写 warnings[]，绝不自行拒绝**；并用 battlemd.mode=inplace 的纯规划夹具证明「不做硬拒绝」这条路径可达。`
  - D5.1（`LEAD_DECISIONS_W42.md:112-113`）：
    > `- **G3（maps + mapselmd 开、battlemd 关、csf 关）= 只警告**：装了却无入口到达，值得告知但不该阻止（用户可能就是要先铺好地图与阶段表）。`
    > `- W43 的实现（K2 硬拒绝 + G3 只写 warnings[]、hard_reject:false）**符合本裁决，无需返工**。`
  - 实际 v13 代码（`feature_subset.py:368-371`）：
    ```python
    g3 = (_mode(f, "csf") == "clone_append"
          and _mode(f, "mapselmd") == "clone_append"
          and "BATTLEMD98.INI" not in sh)
    if g3:
    ```
  - W43 实现说明（`S3_IMPLEMENTATION.md:106`）：
    > `- 触发条件 [静态推断]：csf.mode == clone_append ∧ mapselmd.mode == clone_append ∧ "BATTLEMD98.INI" ∉ shipped(F)（即 battlemd.mode != "append"，文件被显式关闭/改投 BATTLEMD.INI）。`
- **为什么是问题**：
  1. D3 原意要求 `csf` 与 `MAPSELMD` **同时开启**时触发 G3 警告；D3-补虽然宣称「不推翻 D3 原意」，却把 G3 的活例子改写为 `csf 关`（`maps 开 + mapselmd 开 + battlemd.mode=off + csf 关`），D5.1 更直接将 G3 定义为 `maps + mapselmd 开、battlemd 关、csf 关`。两处裁决在 `csf` 开关前提上互相推翻。
  2. 更致命的是，D5.1 明确签发「W43 的实现……**符合本裁决，无需返工**」，但 v13 实际代码 `feature_subset.py:368-370` 依然死锁 `_mode(f, "csf") == "clone_append"`。按照 D3-补与 D5.1 写下的 `maps + mapselmd 开、battlemd 关、csf 关` 组合传入 `resolve()`，`g3` 恒为 `False`，**一条警告都不会产生**。Lead 签发了一个与自己书面裁决逻辑相反的实现。
- **建议处置**：Lead 必须二选一明确拍板并统一文档与代码：若 G3 目标是 `maps + mapselmd 开、battlemd.mode=off、csf 关`，则退回 W43 修改 `feature_subset.py` 的 `g3` 判定（不再要求 `csf == "clone_append"`）并补对应 S3 用例；若保留 `feature_subset.py` 现有逻辑，则必须废止 D3-补第 2 条与 D5.1 中「`csf 关`」的表述，明确 G3 仅覆盖 `csf` 与 `mapselmd` 同时开启且 `battlemd` 未触发 K2（例如 `battlemd.mode=inplace`）的场景。

---

### [BLOCKER-2] `LEAD_SIGNOFF_BATCH_W38_W41_W42.md` 同一文档 §1 与 §3/§4 正面冲突，且 `LEAD_VERIFY_W43.md` 的更正承诺未回写落地
- **位置**：[LEAD_SIGNOFF_BATCH_W38_W41_W42.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_SIGNOFF_BATCH_W38_W41_W42.md#L25-L26) vs [第 70 行](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_SIGNOFF_BATCH_W38_W41_W42.md#L70)、[第 83 行](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_SIGNOFF_BATCH_W38_W41_W42.md#L83)；对照 [LEAD_VERIFY_W43.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W43.md#L32) 与 [第 39 行](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W43.md#L39)
- **类型**：签发文档内部自相矛盾 / 已承诺更正未回写
- **原文摘引**：
  - `LEAD_SIGNOFF_BATCH_W38_W41_W42.md:25-26`（§1 签发 W41 v12）：
    > `- 守卫实体：CsfIncompleteError / official_baseline_labels() / load_official_csf() / **assert_complete_csf()**...`
    > `- **未加** --allow-partial-csf（遵循我的「不建议」）；最小 CSF 路径已从构建链路删除`
  - `LEAD_SIGNOFF_BATCH_W38_W41_W42.md:70`（§3 签发 W42）：
    > `1. [本次实测] **v11 的 CSF 侧没有完整克隆门禁**：append_or_set_label(create_if_missing=True)（csf.py:442-466）+ builder.py:431-437 会生成只含 1 个标签的最小 CSF；全包 grep 5211 零命中。⇒ B8 是**契约新增门禁**，S3 之前必然 FAIL，**不得写成「v11 已拒绝最小 CSF」**。`
  - `LEAD_SIGNOFF_BATCH_W38_W41_W42.md:83`（§4 总览）：
    > `[未达成] 版本守卫未接线、resolve() 未实现、csf 完整性门禁未实现、G3 警告通道未实现、TRACK_B_gates.json 未产出、BASELINE.json 未实算。`
  - `LEAD_VERIFY_W43.md:32, 39`：
    > `1. **[本次读码] v12 其实已有完整性门禁**...（我在 LEAD_SIGNOFF_BATCH 里引用了 W42 的那句，需按此修正）。`
    > `LEAD_SIGNOFF_BATCH_W38_W41_W42.md §3 里我引用了 W42 的「**v11 的 CSF 侧没有完整克隆门禁**」。按 W43 的读码：这句**对 v11 成立、对 v12 不成立**（v12 已有 assert_complete_csf+require_complete=True）。我在此更正——**W41 已经做了门禁，只是理由写错**。`
- **为什么是问题**：
  1. `LEAD_SIGNOFF_BATCH_W38_W41_W42.md` 是三卡合并正式签发件：第 25-26 行签发「`assert_complete_csf()` 已落地、最小 CSF 路径已删除」，第 83 行结论段却赫然写着「`csf 完整性门禁未实现`」。同一份文件直接左右互搏。
  2. Lead 在后发的 `LEAD_VERIFY_W43.md:32, 39` 中承认需修正 `LEAD_SIGNOFF_BATCH_W38_W41_W42.md`，但既未实际回写修改 `LEAD_SIGNOFF_BATCH_W38_W41_W42.md`（导致该文档至今仍处于自相矛盾状态），也遗漏了同文第 83 行「`csf 完整性门禁未实现`」这句错判。
- **建议处置**：直接修订 `LEAD_SIGNOFF_BATCH_W38_W41_W42.md`：在 §3 第 70 行补充加注「对 v11 成立、对 v12 不成立（W41 已在 v12 实现 `assert_complete_csf`）」，并从第 83 行 `[未达成]` 清单中删除「`csf 完整性门禁未实现`」。

---

### [BLOCKER-3] `LEAD_VERDICT_C_line_E2E.md` 对同一对对照截图给出两个互斥 SHA-256（`0bdcfd8c…` vs `0C7FB5FB…`）
- **位置**：[LEAD_VERDICT_C_line_E2E.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_C_line_E2E.md#L35) vs [第 39 行](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_C_line_E2E.md#L39)；对照上游 [E2E_RESULT.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W44_c_line_e2e/E2E_RESULT.md#L197)
- **类型**：数值/指纹自相矛盾 + 独立复核未纠偏
- **原文摘引**：
  - `LEAD_VERDICT_C_line_E2E.md:35`：
    > `- 覆盖 **DESC:SOV1** ⇒ 战役菜单截图与主链臂**逐字节相同**（两文件 SHA-256 均 0bdcfd8c…）`
  - `LEAD_VERDICT_C_line_E2E.md:39`：
    > `[本次实测] 我独立复核了这条：两文件 crop_w44_campaign_menu_content3x.png 与 crop_w44_ctrl_campaign_menu_content3x.png **长度同为 2,562,915 B、SHA-256 均为 0C7FB5FB…**，逐字节相同，成立。`
- **核对实盘产物**：
  - `W44_c_line_e2e\out\crop_w44_campaign_menu_content3x.png` 与 `crop_w44_ctrl_campaign_menu_content3x.png` 实测均为 `2562915 B`，SHA-256 均为 `0C7FB5FB7CE68242212FE3AA0C5A5667468B44218291AB590D240631008F6971`。
  - 原图 `screen_w44_ctrl_campaign_menu.png` 与 `screen_w44_run_S2_campaign_menu.png` 实测均为 `235266 B`，SHA-256 均为 `16F2E0A335DB0D887C25216C74F9FB745EDE1B72C7D865A1E68F908A62F6A261`。
  - 上游 `W44 E2E_RESULT.md:197` 对 `crop_w44_ctrl_campaign_menu_content3x.png` 记录的 `0bdcfd8c18d636d5218fdd5f225351f2021fb416f08d9c9aff0921e6bf12ee76` 在当前 `W44_c_line_e2e\out\` 对应截图文件中并不存在。
- **为什么是问题**：Lead 在第 35 行照抄了上游 W44 的错误哈希 `0bdcfd8c…`，相隔仅 4 行又以 `[本次实测]` 独立核算出了真实的 `0C7FB5FB…`（`2,562,915 B`），却未发现两行哈希冲突，直接写「成立」。这既掩盖了上游报告的指纹失真，也使 C 线端到端签发件出现核心证据哈希打架。
- **建议处置**：删除或更正 `LEAD_VERDICT_C_line_E2E.md:35` 的 `0bdcfd8c…`，统一写明 `crop_w44_*_content3x.png`（`2,562,915 B`，`0C7FB5FB…`）及原图 `screen_w44_*_campaign_menu.png`（`235,266 B`，`16F2E0A3…`），并明确标注上游 `W44 E2E_RESULT.md:197` 所记 `0bdcfd8c…` 与磁盘文件不符。

---

### [BLOCKER-4] 已被推翻/撤回的旧定论在关联现行 `REVIEW/` 文档中仍有无标注活口
- **位置**：
  1. [LEAD_FINDING_campaign_text_is_csf.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_FINDING_campaign_text_is_csf.md#L78)（虽非 9 份主件之一，但属同目录现行结论且无撤回页眉）
  2. [LEAD_W29_VERIFY.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W29_VERIFY.md#L44) 与 [第 95 行](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W29_VERIFY.md#L95)（§6）
  3. 9 份主件内部同类未撤回残留：[LEAD_VERDICT_campaign_menu_q1.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_campaign_menu_q1.md#L14)（见 MAJOR-2，第 14 行保留「有条件可达 | 可开」，而第 77-79 行已宣布下调为「实测不可达」）
- **类型**：已撤回陈述残余活口
- **原文摘引**：
  - `LEAD_FINDING_campaign_text_is_csf.md:78`：
    > `- 这不影响**功能**（战役可注册、可推进），只影响**显示**。`
  - `LEAD_W29_VERIFY.md:95`（§6）：
    > `CSF 散装可覆盖但**必须是完整合法文件**`
  - `LEAD_W29_VERIFY.md:44`：含第一轮 `MAJOR-3` 已指出的未收窄口径（`仅当目录里一个 BATTLEMD*.INI 都没有时`）。
- **为什么是问题**：
  - 「只影响显示、不影响功能」早在 `LEAD_CORRECTION_campaign_blockers.md` §0 中被撤回，但源头定论文件 `LEAD_FINDING_campaign_text_is_csf.md` 第 78 行至今没有任何撤回或更正标识，仍以现行结论面貌存在。
  - 「最小 CSF 会启动失败 / CSF 必须是完整合法文件」已被 W40（及 `LEAD_VERDICT_CSF_live.md`）证伪：1 条标签的最小 CSF 实测可启动且在缺失条目上发生回退（只是生产构建因会回退而不采用最小 CSF），但 `LEAD_W29_VERIFY.md:95` 的绝对化结论仍未加 W40 限定注记。
- **建议处置**：在 `LEAD_FINDING_campaign_text_is_csf.md` 顶部与第 78 行加注「已由 `LEAD_CORRECTION_campaign_blockers.md` §0 撤回」；在 `LEAD_W29_VERIFY.md:95` 补充「已被 W40 真机五臂修正：最小 CSF 不会启动失败，但因回退策略仍坚持完整克隆」并同步处理第 44 行。

---

## MAJOR

### [MAJOR-1] 多份签发文档把子代理/他卡真机结果直接标为 `[本次实测]`，混淆「Lead 本人运行」与「转引下游产物」
- **位置**：
  - [LEAD_VERDICT_C_line_E2E.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_C_line_E2E.md#L20)
  - [LEAD_VERDICT_Q2_CLOSED.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_Q2_CLOSED.md#L13)、[第 17 行](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_Q2_CLOSED.md#L17)、[第 74 行](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_Q2_CLOSED.md#L74)
  - [LEAD_VERDICT_CSF_live.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_CSF_live.md#L9)
- **类型**：过度声明（证据来源/等级拔高）
- **原文摘引**：
  - `LEAD_VERDICT_C_line_E2E.md:20`：
    > `[本次实测] 真机三趟（K1 主链 / K2 读档冷启动 / K3 对照臂），全部 WinSta0\Default 预检 pass=true（EnumWindows 424/428/383、可见 19/19/20、ImageGrab OK）——与 W27/W39/W40 成功侧一致。`
  - `LEAD_VERDICT_Q2_CLOSED.md:13, 17, 74` 处对 W39 真机三臂试验使用 `[本次实测]`。
  - `LEAD_VERDICT_CSF_live.md:9` 处对 W40 真机臂试验使用 `([本次实测])`。
- **为什么是问题**：真机三趟（K1/K2/K3）系 W44（Hy4 子代理）执行，W39 三臂与 W40 五臂分别为 W39、W40 执行；Lead 本人实际只做文本/日志/文件哈希核对，却多处直接打上 `[本次实测]`（在 `LEAD_VERDICT_C_line_E2E.md` 中更与第 39 行 Lead 亲自 `Get-FileHash` 的 `[本次实测]` 混在同一签发里），在 `LEAD_VERDICT_Q2_CLOSED.md` 里还出现第 50-60 行把 `scen_stage_idx=8` 降回 `[转引]` 而第 13/17/74 行仍标 `[本次实测]` 的同文双标。
- **建议处置**：统一证据标签定义：下属工卡真机运行且 Lead 仅复核日志/截图者一律标 `[转引·W39]` / `[转引·W40]` / `[转引·W44]`，只将 Lead 本人实际复跑命令与哈希计算保留 `[本次实测]`。

---

### [MAJOR-2] 第一轮已指出的 3 项过渡概括/遗漏在最新文档中仅「落一半」（详见 `CORRECTION_LEDGER.md` #3/#4/#6）
- **位置**：
  - [LEAD_VERDICT_campaign_menu_q1.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_campaign_menu_q1.md#L14) vs [第 77-79 行](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_campaign_menu_q1.md#L77-L79)、[第 107 行](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_campaign_menu_q1.md#L107)
  - [LEAD_VERDICT_Q2_CLOSED.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_Q2_CLOSED.md#L140)
  - [LEAD_VERIFY_W34.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W34.md#L34) 与 [LEAD_VERDICT_map_start_root_cause.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L23-L30)
- **类型**：同文自相矛盾 + 第一轮更正未彻底收口
- **原文摘引**：
  - `LEAD_VERDICT_campaign_menu_q1.md:14`：
    > `| 追加 battle id 出现在**隐藏 ListBox(1109)** 里 | **有条件可达**，被**一个字节** [0xA8F7AD] 门控 | 可开 |`
  - `LEAD_VERDICT_campaign_menu_q1.md:77-79`：
    > `因此隐藏调试列表**不是「条件可达」而是「实测不可达」**... 我此前在 §1 表格与 §4 旧稿里写「有条件可达」，**据此下调**。`
  - `LEAD_VERDICT_campaign_menu_q1.md:107`：
    > `- 三个槽位替换官方战役后的连带影响（存档、MAPSELMD.INI、BATTLEMD.INI 冲突）`
  - `LEAD_VERDICT_Q2_CLOSED.md:140`：
    > `- v11 的生成逻辑（[Nod] 续号 + 独立阶段段 + Scenario= + 数字子项）在真机上可用`
  - `LEAD_VERIFY_W34.md:34`：
    > `并已在 REVIEW\LEAD_W33_VERIFY.md 与 REVIEW\LEAD_VERDICT_map_start_root_cause.md 里把"转大写"改口`
- **为什么是问题**：
  1. `LEAD_VERDICT_campaign_menu_q1.md` 第 77-79 行明明写着把 §1 表格的「有条件可达」下调，却完全没改第 14 行表格本身；第 18-22 行修正了 `tut1` 后第 107 行仍留着「三个槽位」。
  2. `LEAD_VERDICT_Q2_CLOSED.md:140` 仍把未经多分支 `ClickMap` 真机测试的「数字子项」笼统写成「在真机上可用」，未收窄为「单后继直转路径」。
  3. `LEAD_VERIFY_W34.md:34` 与 `LEAD_VERDICT_map_start_root_cause.md` 仍漏掉 `W31`（[WHY_MAP_FAILS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/WHY_MAP_FAILS.md#L129-L141)）同样的「转大写」错误，且 `LEAD_VERDICT_map_start_root_cause.md:23-30` 仍把 `SkipMapSelect=no`（`0x005AE320` + `0x005ADD95..0x005ADDCF`）与 `SkipMapSelect=yes`（`0x005ADFF3` / `0x005ADEE0..0x005ADEFA`）两条路径混在一起。
- **建议处置**：分别回改 `LEAD_VERDICT_campaign_menu_q1.md:14,107`、`LEAD_VERDICT_Q2_CLOSED.md:140`、`LEAD_VERIFY_W34.md:34` 与 `LEAD_VERDICT_map_start_root_cause.md:23-30`。

---

### [MAJOR-3] `LEAD_VERIFY_W43.md` 引用了不存在的用例名 `S3_COMPAT` 与已不存在的 `__pycache__/*.pyc` 产物记录
- **位置**：[LEAD_VERIFY_W43.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W43.md#L60-L61)；对照 [V13_SOURCE_DELTA.json](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W43_b_line_s3/out/V13_SOURCE_DELTA.json)、[SUMMARY.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W43_b_line_s3/out/SUMMARY.txt#L92)、[s3_cases.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W43_b_line_s3/s3_cases.py#L1172-L1227)
- **类型**：签发依据与磁盘最终产物不一致
- **原文摘引**：
  - `LEAD_VERIFY_W43.md:60-61`：
    > `- SHA256_COMPAT_V13_V12.txt 我未逐行核（它在 S3_COMPAT 用例里，而该用例在我复跑中 PASS）`
    > `- __pycache__/*.pyc 出现在 V13_SOURCE_DELTA.json 的 added 列表里 —— 属打包卫生问题，**不影响功能**，但交付时应清理`
- **为什么是问题**：
  1. 82 个回归用例实为 `57` 个 v12 用例 + `S3_1..S3_25`，其中**并没有名为 `S3_COMPAT` 的独立用例**；生成并校验 `SHA256_COMPAT_V13_V12.txt` 的实际函数是 `case_S3_25`（`s3_cases.py:1172-1227`），`S3_COMPAT` 仅是脚本注释或 `SUMMARY.txt:92` 上的标签说明。
  2. 当前磁盘上的 `W43_b_line_s3/out/V13_SOURCE_DELTA.json`（全文件 15 行）只列了 4 个 `changed` 与 5 个 `added` 文件（`E1_KNOWN_GOOD.json`、`guard_decision_table.json`、`feature_subset.py`、`s3_contract.py`、`version_guard.py`），**不存在 `__pycache__/*.pyc`**，且 `ra2forge_patched_v13` 目录下也不存在 `__pycache__` 目录。该陈述指向某个旧的中间态（或未加 `-B` 前的状态），与最终交付包不符。
- **建议处置**：将第 60 行 `S3_COMPAT` 改写为实际用例编号 `S3_25`；核实当前 `V13_SOURCE_DELTA.json` 后将第 61 行撤回或标注「最终落盘产物已清理，当前 `V13_SOURCE_DELTA.json` 无 `.pyc`」。

---

### [MAJOR-4] 模块计数与真机五臂统计口径错误（`14 = 4 + 9`、`11 个模块` 列 12 文件、`EnumWindows` 漏报 D/E 臂）
- **位置**：
  - [LEAD_SIGNOFF_BATCH_W38_W41_W42.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_SIGNOFF_BATCH_W38_W41_W42.md#L22)
  - [LEAD_FINDING_campaign_text_is_csf.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_FINDING_campaign_text_is_csf.md#L48-L49)
  - [LEAD_VERDICT_CSF_live.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_CSF_live.md#L17)
- **类型**：数值/口径不一致
- **原文摘引**：
  - `LEAD_SIGNOFF_BATCH_W38_W41_W42.md:22`：
    > `- ra2forge_patched_v12\ra2forge\：**14 个 .py，无新增模块**；仅 4 个 MODIFIED（csf.py / builder.py / cli.py / install.py）；其余 9 个 IDENTICAL；TOOL_VERSION="1.0" 未动`
  - `LEAD_FINDING_campaign_text_is_csf.md:48-49`：文字称 `11 个模块`，随后列出 12 个文件名（`__init__, __main__, builder, cli, design, format80, install, lzo, maplib, mixlib, triggers, verify`）。
  - `LEAD_VERDICT_CSF_live.md:17`：以 `EnumWindows=383/382` 概括多臂预检。
- **为什么是问题**：
  1. `4 + 9 = 13 ≠ 14`：实盘 `ra2forge_patched_v12\ra2forge\` 共有 **14** 个 `.py`（除上述 4 个修改文件外，其余 **10** 个 IDENTICAL，含 `__init__.py` 与 `__main__.py`），Lead 沿用了 [APPLY.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W41_csf_install/APPLY.md#L29)「其余 9 个 `.py` + `__init__`/`__main__`」的笔误；同样的问题也出现在 `LEAD_FINDING_campaign_text_is_csf.md:48-49` 的 `11` vs `12` 上。
  2. `LEAD_VERDICT_CSF_live.md` 主审 W40 五臂，但第 17 行的 `383/382` 只包含 A/B 臂（383）与 C 臂（382），漏掉了 D/E 臂的 `381`（五臂可见窗口数亦为 `19/19/20/20/19`）。
- **建议处置**：把 `LEAD_SIGNOFF_BATCH_W38_W41_W42.md:22` 改为「`其余 10 个 IDENTICAL`」，修正 `LEAD_FINDING_campaign_text_is_csf.md:48-49` 模块总数，并在 `LEAD_VERDICT_CSF_live.md:17` 补齐 D/E 臂（381 / visible `19/19/20/20/19`）。

---

### [MAJOR-5] 多份文件保留过期「进行中/待重述」挂起状态，且部分「复核」未提供可复跑命令与输出
- **位置**：
  - [LEAD_VERDICT_Q2_CLOSED.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_Q2_CLOSED.md#L131)
  - [LEAD_VERIFY_W34.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W34.md#L104)
  - [LEAD_VERDICT_CSF_live.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_CSF_live.md#L52)
  - [LEAD_DECISIONS_W42.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_DECISIONS_W42.md#L18)
- **类型**：签发依据不可追 / 文档时态未闭环
- **原文摘引**：
  - `LEAD_VERDICT_Q2_CLOSED.md:131`：写 `(见本文件签发时的 Get-FileHash 输出)`，但正文未附命令与输出值。
  - `LEAD_VERIFY_W34.md:104`：保留 `正在跑`（`18:25`）状态指代 W35。
  - `LEAD_VERDICT_CSF_live.md:52`：保留 `W41 交付后我会按其实际语义重述理由`（`19:15`）。
  - `LEAD_DECISIONS_W42.md:18`：保留 `（我复跑中）`（`19:28`）指代 W41 57/57。
- **为什么是问题**：后续 W39、W41、W43 均已完成交付并进入签发阶段，但上述多份关联文件仍保留「正在跑 / 交付后重述 / 我复跑中」且没有回链闭环注记；`LEAD_VERDICT_Q2_CLOSED.md:131` 指向的 `Get-FileHash 输出` 也未见落盘，令外部复核者无法验证签发时对应的精确命令与摘要结果。
- **建议处置**：为这 3 处过期时态补充「后续状态已由 W39/W41/W43 闭环，见对应文件」的静态注记，并在 `LEAD_VERDICT_Q2_CLOSED.md:131` 补附实际可复跑的 `Get-FileHash` 命令或删除对不存在附件的引用。

---

## MINOR

### [MINOR-1] `LEAD_FACT_map_error_label.md` 全仓排查遗漏早期文档的具体错位标注说明
- **位置**：[LEAD_FACT_map_error_label.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_FACT_map_error_label.md#L51-L70)（尤见第 52 行）
- **类型**：错误字样登记表覆盖面有缺口
- **原文摘引**：
  - `LEAD_FACT_map_error_label.md:52`：以 `不算未更正的错误` 概括处理情况，未点明早期文档 `W33 NEXTSCENARIO_FLOW.md:43,45` 与 `W28 NEXTSCENARIO_FORM.md:5,15` 的对应行位是否已加注更正。
- **为什么是问题**：该文档针对第一轮 `MAJOR-4` 做了全仓扫描，已点名指出 `W27` 与 `LEAD_CORRECTION_campaign_blockers.md` 未加注、`W31`/`W39` 已加注，但遗漏了对 `W33 NEXTSCENARIO_FLOW.md:43,45` 与 `W28 NEXTSCENARIO_FORM.md:5,15` 逐行核对与登记。
- **建议处置**：在 `LEAD_FACT_map_error_label.md` 台账中补全 `W33 NEXTSCENARIO_FLOW.md:43,45` 与 `W28 NEXTSCENARIO_FORM.md:5,15` 的核对状态（已加注或待加注）。

---

### [MINOR-2] 悬空章节交叉引用（不存在的 `§6` 与缺失的 `§5`）
- **位置**：
  - [LEAD_VERDICT_CSF_live.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_CSF_live.md#L109) → 指向 [LEAD_W27_RAW_VERDICT.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W27_RAW_VERDICT.md)
  - [LEAD_VERDICT_campaign_menu_q1.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_campaign_menu_q1.md#L98)
- **类型**：结构编号与交叉引用错误
- **原文摘引**：
  - `LEAD_VERDICT_CSF_live.md:109` 写 `已在那边补注`（引用 `LEAD_W27_RAW_VERDICT.md §6`），但 `LEAD_W27_RAW_VERDICT.md` 实际章节编号为 `1..4, 7, 9, 8`，并无 `§6`。
  - `LEAD_VERDICT_campaign_menu_q1.md:98` 由 `4.3` 直接跳到 `6.`（缺失 `§5`，第一轮 `MINOR-2` 遗留未改）。
- **为什么是问题**：会导致引用跳转失效或让读者误以为文档被截断。
- **建议处置**：修正 `LEAD_VERDICT_CSF_live.md:109` 的真实目标章节号或行号，并重新编号 `LEAD_VERDICT_campaign_menu_q1.md` 第 98 行后的章节号。
