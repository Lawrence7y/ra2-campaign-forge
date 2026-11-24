# LAYOUT.md — S15-K2 目录与复跑说明

```
S15-K2\
  PROGRESS.md            结论表 + 3 个核心数字（≤60 行）
  TARGETS.tsv            158 行：entry/现名/现grade/缺什么/取证计划
  coverage_delta.tsv     42 行：entry/S15/新名/一行语义/[已证]/证据路径（无表头）
  DOD.md                 PLAN §1 六条逐条对账
  UNKNOWNS.md            未决项 U1–U8
  DISAGREE.md            异议 D1–D7
  LAYOUT.md              本文件
  EVIDENCE\              原始输出（不截断）
    T1_inventory_stdout.txt / T1_discrepancy_stdout.txt / T1_S15_full_list.txt
    T1_S15_coverage_dump.tsv
    T2_dispatch_tables.txt        派发表全 dword (Action145/Team65/Event L1-L4)
    T2_slot_disasm.txt            54 个 slot 函数逐条反汇编
    T2_alloc_sites.txt            push<size>→call 全 .text 扫描（6A/68 两形态）
    T2_vtable_verify.txt          6 类 vtable 槽位索引 + COL + push 目标
    T2_rtti_and_sub_callers.txt   COL+0xC→TD→RTTI 名 + sweep_calls 调用者
    T2_sub_bodies.txt             51 个 sub_ 函数体 + 调用点归属
    T2_action_map.txt             sub_ → 动作索引映射（全 dword + 逐行）
    T2_action_handlers.txt        25 个 handler 薄壳反汇编
    T2_action_index_verify.txt    Execute 序言 dec edx + 关键 handler
    T2_verify_promotions.txt      逐条验证 + 重名/多调用剔除记录
    T2_strict_filter.txt          严格薄壳判据 PASS/FAIL 全表
    T2_constructor_candidates.txt 5 个构造器完整反汇编 + vtable 写
    T2_event_dispatch_tables.txt  事件两表（L1 12 / L2 49 byte）字节全文
    PROMOTIONS_FINAL.tsv          42 条升证全表（新名/理由/证据）
    FINAL_COUNTS.txt              最终计数与逐 entry 名
    *_stdout.txt                  各脚本控制台原样输出
  work\                  可复跑 Python 脚本（按 t1_* → t2_* → finalize 顺序）
```

## 复跑顺序（Python 3.12.10 + capstone 5.0.7 + pefile 2024.8.26）
1. `t1_inventory.py` / `t1_discrepancy.py` — 基线计数与 159-vs-158 口径核验
2. `t2_dispatch.py` / `t2_slot_disasm.py` / `t2_alloc_scan.py` / `t2_vtable_verify.py` / `t2_rtti_mine.py` — 字节取证
3. `t2_action_map.py` / `t2_action_handlers.py` / `t2_action_index_verify.py` — 动作实现映射
4. `t2_final_promote.py`（产出初版）→ `t2_verify_promotions.py` / `t2_strict_filter.py`（剔除歧义）→ `t2_constructor_check.py`
5. `add_ctors_final.py` — 合并 42 条、写 coverage_delta.tsv + FINAL_COUNTS.txt
6. `make_targets_and_tables.py` — TARGETS.tsv + 事件两表字节全文

## 只读/写域
- 目标 `ra2youli\gamemd.exe` 只读（SHA-256 已核）。
- 仅写 `S15-K2\`；未改 `COVERAGE/coverage.tsv`、未写台账、未 git commit、未建 KB。
- 未使用 Ghidra（capstone/pefile 静态已完成，无需复制副本）。
