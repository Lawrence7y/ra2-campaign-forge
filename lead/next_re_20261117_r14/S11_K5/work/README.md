# S11-K5 work 复跑顺序

所有脚本只读 ra2youli/gamemd.exe、COVERAGE/coverage.tsv、function_atlas.tsv；只写 S11_K5\。

1. `python work/baseline_recompute.py > EVIDENCE/baseline_recompute.txt`
2. `python work/scan_entries.py`（逐 coverage 行裸字节/capstone 形态）
3. `python work/rebuild_all_rtti.py`（全 RTTI/COL/vtable + AbstractType 表）
4. `python work/prove_semantics.py`（GetSize 双点闭合、WhatAmI enum+RTTI、双通道候选普查、写 coverage_delta.tsv）
5. `python work/validate_delta.py > work/validate_delta.log`（校验并写 EVIDENCE/validate_delta.txt）

注意：Windows 控制台需 `set PYTHONIOENCODING=utf-8`，否则中文分级 repr 会乱码。