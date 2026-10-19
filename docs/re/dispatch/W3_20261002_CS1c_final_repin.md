# W3-CS1c 派工单 · verify_c1 终局重钉（覆盖 {CS2, CS3} 授权标记集）+ verify_cs1 [11] 同步

> 派发：2026-10-02 21:0x（Lead）· 前置：**CS1b 已验收（§481）** · **CS3/CS3B 已收口**（coverage_ledger 最终态已定，本轮再无台账写者）
> 执行：ZCode（新会话）· 预估 30–50 分钟

## 背景（两个时点的移动靶，现在靶子停了）

- **CS1 时点**：verify_c1 残红 7 条 = CS2 并发追加（CS1b 已按 post-CS2 重钉 → 20:14 全绿）。
- **CS3 时点**：CS3 又追加 12 处 `【W3-CS3】` 标记 + 新键（gate 子块、rpt1_disposition、m34r 规范块等）⇒ verify_c1 再红 5 条（CS1b 如实停手报备，见其 [11] 与 live-red 行）。
- **CS3B 已完成**（gate `pe_header_field_registration` 子块落地，verify_cs3=84 项绿、verify_ledger 绿）⇒ **台账进入稳定终态**。

## 任务

1. 亲跑 `out/re_work/qc/W3_20261001/c1_ledger_fix/verify_c1.py` 记录当刻 FAIL 集合（预期 5 条、全部与 CS3 标记/新键相关；**集合对不上先停手报告**）。
2. 把 verify_c1 的 T2 层重钉到 **{CS2, CS3} 联合授权集**：
   - 三律：① 只动点名断言 ② **更强**：对 `【W3-CS2】`/`【W3-CS3】` 标记做"存在且数量 ≥ 登记值 + 打印实测数"的**单调断言**（CS2=44 处、CS3=12 处以现读为准，不许硬编码过期值 —— 打印出来让断言自证），对 CS3 新键（gate 子块、rpt1_disposition、m34r 规范块等）做"存在 + 结构正确"断言 ③ 改后仍红即回滚。
   - **严禁**删除检查或缩范围换绿。
3. **同步 verify_cs1 [11]**：期望集合从"7 条 CS2 残红"改为"0 残红（{CS2,CS3} 联合括号内）"，并打印所选括号 —— 注意 verify_cs1 其余 63 项一字不动。
4. **负控 ≥2（副本上做）**：① 副本删掉一处 CS3 标记 ⇒ verify_c1 必须 FAIL 指向该条 ② 副本把某个 CS3 新键值投毒 ⇒ 必须 FAIL ③（可选）把 verify_cs1 [11] 的括号改坏 ⇒ 必须 FAIL。
5. **收尾三门同一时点全绿**：`verify_c1.py` EXIT=0 **且** `verify_cs1.py` 64/64 EXIT=0 **且** `verify_ledger.py` EXIT=0（三个命令连跑一次，输出归档）。

## 铁律

- **写域仅**：`c1_ledger_fix/verify_c1.py`、`cs1_cascade/verify_cs1.py`、`out/re_work/zcode_live/W3_20261002/cs1c_repin/`。
- coverage_ledger **只读**（被断言对象）、ATLAS 两份只读、其余全部验证器只读、dispatch 台账只读。
- 空扫描 = INSTRUMENT_FAILED；拿不准停手报备。

## 交付

`out/re_work/zcode_live/W3_20261002/cs1c_repin/`：`CS1C_REPORT.md` + `verify_cs1c.py`（正控=5→0 点名前后断言；负控必咬）+ 三门连跑原文。完成后回报 `[0]`：before/after FAIL 集合 + 三门 EXIT + verdict tally 原文。
