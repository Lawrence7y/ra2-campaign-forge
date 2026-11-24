# S10-K4 work 复跑说明

只读 `ra2youli/gamemd.exe` 与共享 coverage/atlas；所有输出写回本卡目录。Windows 控制台设 `PYTHONIOENCODING=utf-8`。

1. `python work/baseline_recompute.py > EVIDENCE/baseline_recompute.txt`
2. `python work/probe_mission_strings.py > EVIDENCE/probe_mission_strings.txt`
3. `python work/probe_vtable.py` / `probe_all_dispatch.py` / `probe_timer_dispatch.py` 产生命名与 Timer 证据。
4. `python work/prove_corrections.py` 生成 `coverage_delta.tsv` 与 `EVIDENCE/mission_rows_corrected.txt`。
5. `python work/validate_delta.py` 写 `EVIDENCE/validate_delta.txt`。
6. `python work/task3_exhaustive.py` 写 `EVIDENCE/task3_exhaustive.txt`。
7. `python work/verify_esi_trace.py` 写 `EVIDENCE/register_trace.txt`。

`all_rtti.json` 是只读索引副本；RTTI 证据在脚本中由 PE 字节独立复算。
