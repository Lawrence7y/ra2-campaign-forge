# S11_K4 work 复跑顺序

1. python work/baseline_recompute.py > EVIDENCE/baseline_recompute.txt
2. python work/rebuild_layout.py（写 work/layout.json 与 EVIDENCE/layout.txt）
3. python work/fresh_proof.py（写 work/closure.json、work/entry_evidence.json、work/shape_scan.json 与对应 EVIDENCE）
4. python work/shape_counterexamples.py（写全 RTTI vtable 反例扫描）
5. python work/classify_nonvtable.py（未覆盖入口保守分类）
6. python work/build_delta.py（生成 coverage_delta.tsv 与 work/build_delta.log）
7. python work/validate_delta.py（只读校验并计算合入后指标）

所有脚本只读 ra2youli/gamemd.exe、COVERAGE/coverage.tsv、function_atlas.tsv；只写 S11_K4\。
