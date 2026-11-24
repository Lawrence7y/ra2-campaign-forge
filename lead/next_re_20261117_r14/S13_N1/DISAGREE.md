# S13-N1 DISAGREE

- 卡面“预期 28 条左右”与现场复算 26 条不一致；统一大小写 + atlas 求交、分母排除 atlas 外行后为 26。见 EVIDENCE/baseline_recompute.tsv。
- 0065B1E0 在 C02/C07 旧 census 中以 `RadSiteClass::noinit_t` 记录，在 N_FIX 中以 `RadSiteClass::RadSiteClass()` 记录；二者为同一 noinit ctor 的别名/源声明，本卡采用 N_FIX 的源级名并记 conflict=0，非新冲突。
- 00773030 旧台账只有 sub_ 与弱调用图标签，未发现既有真名；本卡按 YRpp FindIndex 契约定名，conflict=0。
