# S06-K4 work / 复跑顺序
1. `python work/k4_rtti.py` -> `work/all_rtti.json`, `EVIDENCE/all_rtti.txt`, `EVIDENCE/abstract_type_enum.txt`
2. `python work/k4_candidate_census.py` -> `work/candidate_census.json`, `EVIDENCE/candidate_census.txt`
3. `python work/k4_prove_semantics.py` -> `work/proofs.json`, `EVIDENCE/whatami_proofs.txt`, `EVIDENCE/getsize_proofs.txt`, 22 行 delta
4. `python work/k4_behavior_growth.py` -> `EVIDENCE/growth_behavior.txt`, 追加 1 行 delta（00483710）
5. `python work/k4_validate.py` -> `EVIDENCE/baseline_recompute.txt`, `EVIDENCE/validate_delta.txt`

探索脚本（保留可复跑）：`probe_factories.py`（factory size）、`probe_ctor_alloc.py`（无 factory 的 allocation closure）、`probe_growth.py`/`probe_small_funcs.py`（行为级候选细查）、`k4_behavior_probe.py`（42 个原始行为命中）。
