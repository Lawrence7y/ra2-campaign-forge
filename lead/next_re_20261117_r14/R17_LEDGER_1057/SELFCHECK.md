# SELFCHECK · §1057 草稿（书记员自检）

## 一、12 个事项覆盖（12/12，无遗漏）
| 事项 | 主题 | 是否已写入 SECTION.md | 关键证据路径（相对仓库根） |
|---|---|---|---|
| 1 | R8 四问 + 三处锚点陷阱 | 是 | lead/next_re_20261117_r14/R17_R8_RESIDUAL/ |
| 2 | 审计 R8 五判定 + 五必改 | 是 | lead/next_re_20261117_r14/R17_AUDIT_R8/ |
| 3 | 地址权威表（A1 实质） | 是 | R17_AUDIT_R8/addr_authority.tsv, byte_checks.tsv |
| 4 | R9 卡（独立复现 + 表形态否定，350 槽/#85/#119/零取用/RTTI 未取得） | 是 | R17_R9_VTABLE_CONSUMER/ |
| 5 | 第三方裁决（322 槽/#73/#107/甲对乙错/两口径一致） | 是 | R17_ADJ_RDATA_RUN/ |
| 6 | 审计 R9 四判定 + 四必改 | 是 | R17_AUDIT_R9/ |
| 7 | B3 边界：12 处装表写=串首附近、非 #73/#107、审计单源 | 是 | R17_AUDIT_R9/VERDICT.md, controls.tsv |
| 8 | 本轮净结论（各 1 引用、E8/E9=0、立即数装载 0、未取得+推断） | 是 | 五份报告汇总 + numbers.tsv |
| 9 | §1056 四项现状并列（两已得/两未得、须同引 §1057） | 是 | STATUS_BOARD.md, LEAD_LOCK, R17_R8_RESIDUAL/ |
| 10 | Lead 环境发现（1.7.20 tgz、mtime、无 @deepseek-ai/*、来源未取得） | 是 | profiles/desktop/package.json 等 + LEAD_LOCK §R |
| 11 | 派发通道切换（内部 subagent、4 模型、身份不可校验） | 是 | LEAD_LOCK P–S + cordis.patch.yml |
| 12 | 方法学三条（正控反控/单源降级/裁决卡） | 是 | R17_AUDIT_R8, R17_AUDIT_R9, R17_ADJ_RDATA_RUN |

- 逐条理由互异：事项 1=闭合卡依赖独立证据；2=审计增量在表述纪律；3=口径差 vs 真错二选一；4=先复现再否定的方法论；5=第三方自算不可替代；6=四类判定取证方式不同；7=单源+口径差双标注；8=否定性结论的双层表述；9=四项两状态防整体误引；10=截面非结论、来源留白；11=配置层 vs 运行层分离；12=三条各堵一类具体失误。

## 二、写「未取得」的项目（严禁编造，均写未取得）
- 事项 4：R9 的 `call [reg+off]` 与槽偏移、RTTI 类名 —— 未取得。
- 事项 8：entry `43F180`/`449440` 的调用者与槽偏移 —— 未取得；虚派发为推断（强度中），非已证。
- 事项 9：`0x6F4A70` 语义 —— 未取得（仅推断）；两函数调用者 —— 未取得。
- 事项 10：live profile 的安装来源 —— 未取得（当前截面 dsh-purge-community=1.7.20 tgz、无 @deepseek-ai/*，与 LEAD_LOCK §R 记录不符，不可追溯来源）；不把 LEAD_LOCK 装后核对当当前截面。
- 事项 11：探测回执自报模型 —— 未回报 ⇒ 身份不可校验（回执文件在只读目录内未找到，按未取得处理）。

## 三、数字与卡面一致性（复算 vs 卡面）
- **与卡面不一致的数字个数：0。** 所有可复算数字均由书记员从盘上 independently 复算，与卡面（及来源报告）逐项一致，详见 `numbers.tsv`（62 行：exe size/hash、A1 六处字节、Q2 尾界与 10 条 ret、Q1 唯一引用与 E8 正控、ADJ 322 槽/#73/#107/两口径/灰区 0、R9 350 槽/#85/#119、B1 12 候选 0 命中 + 三正控、B3 12 处写与四槽内容、B4 装饰名 0、环境 1.7.20/mtime/无 @deepseek-ai/*、4 模型）。
- 需要并列报出的口径/差异说明（非数字不符，已写入正文）：
  1. 事项 7：审计 B3 表内 site 地址（`0x43B721` 等）是立即数地址；书记员复算对应指令起始早 2–3 B（如 `C7 06 …` @ `0x43B71F`）。两种口径均满足 `host <= site < fn_end`，故不影响结论，但正文已并列标注，避免下游把 site 当指令起始。
  2. 事项 11：卡面称 4 个模型可选——书记员实读 `cordis.patch.yml` 确认 4 条（deepseek-v4.1-flash / hy4flash-free / hy4flash / GLM-5.3-Flash，均 magpie-anthropic），卡面正确；LEAD_LOCK §S 步骤 1 只点名 3 个、漏 `work/cn:hy4flash`，属 LEAD_LOCK 与卡面之间的记载差（书记员不改 LEAD_LOCK，仅如实记录）。
  3. 事项 4/5：R9 自报 350 槽/#85/#119 是被裁决推翻的败方口径，卡面已明确其为错；书记员复算确认 322 槽/#73/#107 为权威，R9 数字保留在正文中仅为并列展示败方说法，不作引用依据。

## 四、边界遵守
- 只写 `lead/next_re_20261117_r14/R17_LEDGER_1057/` 下三份产物（SECTION.md / numbers.tsv / SELFCHECK.md）；未改台账正文、未改任何控制文件（LEAD_LOCK/STATUS_BOARD/COMMON/PANEL 均未动）。
- 未执行逆向、未启动 gamemd、未写仓库根；gamemd.exe 只读打开。
- 先落 numbers.tsv 再写正文（SECTION.md）；自检最后写。
