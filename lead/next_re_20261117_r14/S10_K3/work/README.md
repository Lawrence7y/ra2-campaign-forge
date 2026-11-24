# S10-K3 work 复跑说明

所有脚本默认从 `CARD=lead/next_re_20261117_r14/S10_K3` 定位输出；只读 `ra2youli/gamemd.exe` 与共享 coverage/atlas。Windows 控制台请设 `PYTHONIOENCODING=utf-8`。

## 顺序
1. `python work/baseline_recompute.py > EVIDENCE/baseline_recompute.txt`
2. `python work/rebuild_all_rtti.py`（TD/COL/vtable/AbstractType 全量重建，输出 work/all_rtti.json）
3. `python work/candidate_census.py`（S10 B8C3 / vtable 锚点普查）
4. `python work/prove_semantics_s10.py`（WhatAmI / GetSize / Mission no-op 严格证明，写 coverage_delta.tsv）
5. `python work/nonupgraded_dump.py`（28 桩状态与未升级候选反汇编）
6. `python work/validate_delta.py > work/validate_delta.log`（结构校验 + 合入模拟）

## 关键脚本
- `baseline_recompute.py`：盘上基线，大小写归一后取 coverage∩atlas。
- `rebuild_all_rtti.py`：COL+0xC→TD+8；TD+8 是内联名串不是指针。
- `prove_semantics_s10.py`：唯一写 delta 的脚本；只允许四种证明类型；无 vtable-only 升级。
- `validate_delta.py`：检查 8 位大写 entry、S10、目标行为非 [已证]、唯一 name/entry、证据文件存在、模拟 proved/named。

