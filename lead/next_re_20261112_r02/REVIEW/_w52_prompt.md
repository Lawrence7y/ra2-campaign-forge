你是 RA2 Campaign Forge 的**第二轮交叉一致性审计卡 W52**。任务：**审计 Lead 最新一批签发文件**（第一轮由 W43 做过，已抓出 4 个 BLOCKER）。

工作目录：`D:\Project\ra2-campaign-forge`。**第一件事：立刻建目录 `lead\next_re_20261112_r02\W52_audit_round2\` 并写 `STARTED.txt`（带时间戳）。**

## 审计对象（Lead 最新 9 份，逐个读）
`REVIEW\` 下：
- `LEAD_VERDICT_C_line_E2E.md`（C 线端到端，含"六步全成立"）
- `LEAD_VERIFY_W43.md`（B 线 S3 签发，含 82/82）
- `LEAD_DECISIONS_W42.md`（4 项裁决 + D3-补 + D5，共约 10 KB）
- `LEAD_SIGNOFF_BATCH_W38_W41_W42.md`（三卡合并签发）
- `LEAD_VERDICT_CSF_live.md`（CSF 真机五臂）
- `LEAD_VERDICT_Q2_CLOSED.md`（Q2 闭合 + 三臂 A/B）
- `LEAD_VERDICT_campaign_menu_q1.md`（菜单结构性封死）
- `LEAD_VERIFY_W34.md`（含 §3「已撤回」的自我更正）
- `LEAD_FACT_map_error_label.md`（错误字样登记）

## 第一轮 W43 已抓出的（你要避免重复，但**要检查这些更正是否真的落地**）
1. 我错误否定了 W34 的 `0xFBE0D09D = ts_crc_hash("LOCALMD.MIX")`（用错填充规则）
2. 我凭空"纠正"了 W39 的 2.5s/4.56s 时间口径（W39 原本没错）
3. 我把 `scen_stage_idx=8` 从 `[转引]` 升级成 `[本次实测]`，且下标差一格
4. 我宣称"已把『转大写』改口"但实际没改；且 W31 犯同样错我没指出
5. `SOV07TMD.MAP` 的 `EndOfGame` 我写 `no`（实为 `yes`）
6. 「三个槽位含 `tut1`」我夸大了（`tut1` 无 BATTLEMD 条目）

**请逐一核对这 6 条更正是否在文件里真正落地**，并给出「已落地 / 未落地 / 落一半」的判定。

## 还要专挑的
- **过度声明**：把 `[转引]`/`[静态推断]` 写成 `[本次实测]`；把"回归全绿"写成"能力具备"；把"已收窄"写成"已定位"
- **数值/口径不一致**：SHA-256、字节数、模块数（11/13/14）、用例数（51/57/82/90）、地址（VA/RVA/FOFF）、标签数（5,211/5,212）、`frame` 数值
- **裁决自相矛盾**：例如 D3 说「G3 只警告」又说「3 对强耦合保留硬拒绝」，两者在特定组合下互斥（详见 `LEAD_DECISIONS_W42.md` D3-补，检查那条澄清是否足够）
- **已撤回的陈述是否还有活口**：「最小 CSF 会启动失败」（已被 W40 推翻）、「描述文本只影响显示不影响功能」（早前撤回）、「`LB_GETCOUNT=0` 是破绽」（已被 W32 否证）
- **「签发」的依据是否可追**：凡写「我亲自复跑」的，是否给了可复跑的命令与结果数字

## 输出
按严重度 `BLOCKER` / `MAJOR` / `MINOR` 排序，每条给：位置（file:line 或段落）、类型、原文摘引、为什么是问题、建议处置。
**不重做反汇编、不启动游戏**。你只做文本与产物的一致性核对。

## 交付（只写这个目录）
`W52_audit_round2\`：`STARTED.txt`、`AUDIT_ROUND2.md`、`CORRECTION_LEDGER.md`（上述 6 条更正的落地核对表）、`UNKNOWNS.md`

（注意：本会话处于只读 /plan 约束时，请把结果直接写入上述目录；若无法写盘，则在回复正文里完整给出三份内容。）