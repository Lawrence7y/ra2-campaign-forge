# work 复跑说明

环境：Python 3.12 + capstone 5.0.7 + pefile。所有脚本从本目录运行（`python <script>.py`）。

1. `python t0_recompute.py` → `EVIDENCE/t0_baseline.txt`（核心数字 158/137/95/141/need 143/shortfall 2）。
2. `python disasm_targets.py` → `EVIDENCE/disasm_residual_targets.txt` 与 `EVIDENCE/disasm_targets/*.txt`。
3. `python scan_call_xrefs.py` → `EVIDENCE/call_xrefs_residual_targets.tsv`。
4. `python dump_strings.py` → `EVIDENCE/strings_trigger_candidates.txt`。
5. `python inspect_source_xref_sites.py` → `EVIDENCE/source_string_xref_sites.txt`。
6. `python inspect_save_load_sites.py` → `EVIDENCE/save_load_call_sites.txt`。
7. `python extra_channels.py` → `EVIDENCE/yrpp_residual_addr_matches.txt`、`eva_xrefs.txt`、`ini_key_xrefs.txt`、`residual_channel_matrix.tsv`。

`scan_xrefs.py` 是按需查询原始 dword xref 的通用脚本；默认参数会覆盖 `EVIDENCE/xrefs_residual_targets.txt`，本卡最终汇总已写回该文件。
