# R36 Check B · `statement` 列引用清点

共 54 条；`grade` 取值仅有 ['[已证]', '[流程]', '[静态推断]', '未取得'] —— 该列无可引对象，不参与本检查。

含非 ADDR 引用的行数 = 11；各类 token 计数 = {'SECTION': 8, 'DECIDE': 2, 'BARECARD': 3, 'FACT': 3, 'CARD': 2, 'FILE': 1}

## F08 [[静态推断]]
- statement: ②-b 永久以 [静态推断] 收口、依据 D-53(A)、不再投卡探测；书面限制 a–e：a 两路径在闸核内共用同一 0x47C620(§2.10 限定为仅非短路情形成立)、b 三函数体非栈写=0(0x449440 1写/0非栈、0x47C620 0/0、0x47C3D0 8/0)、c bit0=0 可放置对象物理不存在(唯一写点 0x6F322F)、d「虚派发」仅推断(依赖 0x6F2B40 为 TechnoClass ctor)、e 未做动态硬件读断点；§2.10 (a′) 把 (a) 限定为仅非短路情形成立。
- evidence_paths: lead\next_re_20261117_r14\R14_COMMON.md(§2.9一/§2.10一/二);lead\next_re_20261117_r14\R17_LEDGER_1064\SECTION.md(事项4)
  - SECTION   §2.10
  - DECIDE    D-53
  - ADDR(n=5)  0x449440 0x47C3D0 0x47C620 0x6F2B40 0x6F322F

## F11 [[已证]]
- statement: RTTI×coverage 对账第三版双口径并列：口径 S(严格基名)=BOTH 397/COVERAGE_ONLY 32/RTTI_ONLY 383；口径 C(显式复合名 X_Y↔X@Y)=BOTH 403/COVERAGE_ONLY 26/RTTI_ONLY 377；复合名 660 条(模板 634+非模板 26)。第1版 220 与第2版 26 已作废。
- evidence_paths: lead\next_re_20261117_r14\R17_LEDGER_1062\SECTION.md(事项3);lead\next_re_20261117_r14\BOARD_ARCHIVE.md(R17 第 15 轮 段)
  - BARECARD  COVERAGE

## F12 [[已证]]
- statement: R22+审计「② 独立佐证」测量(零 grade 变更)：[已证] 1654/类名可定位 1094/entry 与类身份同 vtable 闭合 433/矛盾信号 141(审计独立复现；敏感性口径 1085/397/168/91)；433 只说明地址锚定成立、不说明 entry 属于该类成员、不构成 ② 支持、不支持任何改判；R19 三桶限制③「BOTH 只说明不矛盾、COVERAGE_ONLY ≠ 名字错」，该对账不是类名正确性判定。
- evidence_paths: lead\next_re_20261117_r14\R17_LEDGER_1062\SECTION.md(事项4);lead\next_re_20261117_r14\BOARD_ARCHIVE.md(R17 第 14 轮 段);lead\next_re_20261117_r14\BOARD_ARCHIVE.md(R17 第 15 轮 段)
  - BARECARD  COVERAGE

## F14 [[已证]]
- statement: §1061 勘误：其 R19 小节的 COVERAGE_ONLY 220 已被 §1062 第三版双口径取代；§1060 的「0x4264C0 在 17 个类」实为 15。
- evidence_paths: lead\next_re_20261117_r14\R17_LEDGER_1062\SECTION.md(事项5);lead\next_re_20261117_r14\BOARD_ARCHIVE.md(R17 第 13 轮 段);lead\next_re_20261117_r14\BOARD_ARCHIVE.md(R17 第 15 轮 段)
  - SECTION   §1060 | §1061 | §1062
  - BARECARD  COVERAGE
  - ADDR(n=1)  0x4264C0

## F16 [未取得]
- statement: 以下语义/身份仍未取得：0x6F4A70 确切游戏语义名(仅字节事实 51 字节/2 call/2 ret/尾界 0x6F4AA3/槽#157 目标不唯一)；0x5A6510 确切游戏语义名与类身份(不在任何 vtable、仅 1 处直接调用 0x5A531E、slot73 返回值被丢弃⇒不是查询)；三个装表 host(0x43B680/0x43B740/0x43BCF0)类名(全文件指向装饰名字符串引用仅 6 处、有效立即数 0 处)；0x449440 调用方(见 F09)。
- evidence_paths: lead\next_re_20261117_r14\BOARD_ARCHIVE.md(R17 第 15 轮 段);lead\next_re_20261117_r14\BOARD_ARCHIVE.md(R17 第 16 轮 段);lead\next_re_20261117_r14\R14_COMMON.md(§2.9三);lead\next_re_20261117_r14\R17_LEDGER_1063\SECTION.md(事项2);lead\next_re_20261117_r14\R17_LEDGER_1062\SECTION.md(事项2)
  - FACT      F09
  - ADDR(n=8)  0x43B680 0x43B740 0x43BCF0 0x449440 0x5A531E 0x5A6510 0x6F4A70 0x6F4AA3

## F17 [[已证]]
- statement: R14_COMMON §2.6 四·「决定性反证」中「两路径在闸层不可分、共用同一 0x47C620」一句，其适用范围已被 §2.10 (a′) 收窄为「仅非短路情形」；0x449440 的 B 短路路径（0x449459/0x449460 → 0x449493 → 0x4494A3 call [edx+0xA8] → 0x4494B2）不执行 0x47C620。该句不得单独引用。
- evidence_paths: lead\next_re_20261117_r14\R14_COMMON.md(§2.6四 / §2.10一)
  - SECTION   §2.10 | §2.6
  - CARD      R14_COMMON
  - ADDR(n=7)  0x449440 0x449459 0x449460 0x449493 0x4494A3 0x4494B2 0x47C620

## F26 [[流程]]
- statement: DoD 已证不可达，上限 3/22（S15/S16/S17 且这三个已达标）；用户 D-49 正式裁定「DoD 判据不改；接受 3/22 收口，目标改为事实底座可交付完整度」。
- evidence_paths: lead\PENDING_DECISIONS.md(D-49 已裁决);lead\next_re_20261117_r14\R14_COMMON.md
  - DECIDE    D-49

## F33 [[已证]]
- statement: 硬规则：gamemd.exe 导出表 RVA=0/Size=0，无任何导出符号可取；据此「经导出表解析函数地址/名字」的路径恒不可得，判入口归属不得依赖导出表通道。
- evidence_paths: lead\LEAD_LOCK(追加·2026-11-20 21:1x·r15 第 105 轮 段 / 追加·2026-11-20 22:1x·r15 第 111 轮 段)
  - FILE      gamemd.exe

## F36 [[流程]]
- statement: 硬规则：GATE_MAP 是 S02B-GATE 卡「②-b 拒绝闸静态定位」的产物文档（R14_COMMON §2.6 的来源），记载拒绝闸判据；其旧叙述把一处条件跳记为「拒绝分支」，已由 §2.7 字节更正为循环增量+回边。故引用 §2.6 的路径叙述必须同引 §2.7，不得再据旧叙述推「逐格调用直接产生拒绝」。
- evidence_paths: lead\next_re_20261117_r14\R14_COMMON.md(§2.6 来源段 / §2.7);lead\next_re_20261117_r14\COVERAGE\PANEL.md(M103 段)
  - SECTION   §2.6 | §2.7
  - CARD      R14_COMMON

## F49 [[已证]]
- statement: 形态：B8 imm32 C2 04 00（ret 4）与 B8 imm32 C3（ret）是两种不同字节形态——c2 04 00 为 3 字节、callee 清 4 B 栈参；c3 为 1 字节、caller 清栈。凡以「B8 imm32 C3 的 imm」为证据的结论（如 GetSize 双点闭合、WhatAmI 枚举值）都不得套用到 ret 4 形态上；对任意 imm 的 B8 imm32 C2 04 00 体，其返回值一律须读 imm32 本身，不得默认为桩式常量。本条只讲形态，不涉及任何具体槽是否恒定返回；槽级行为判据见 F29
- evidence_paths: lead\next_re_20261117_r14\R14_COMMON.md(§8.3 新增坑);lead\next_re_20261117_r14\HANDOFF_R14_R3.md(九);lead\next_re_20261117_r14\R17_R52_ADJ_D4\VERDICT.md
  - FACT      F29

## F51 [[已证]]
- statement: E8 原始命中数 ≠ 严格形态数：本镜像 E8→0x7C978A 336 处，严格 atexit 桩仅 68、E8→0x5657A0 1439 处（与 F10 同值）
- evidence_paths: lead\next_re_20261117_r14\R17_AUDIT_FI_V5\VERDICT.md(A5 / N2);lead\GOAL_THREE_TARGETS_20261018.md(N9 三条方法论修正 段)
  - FACT      F10
  - ADDR(n=2)  0x5657A0 0x7C978A
