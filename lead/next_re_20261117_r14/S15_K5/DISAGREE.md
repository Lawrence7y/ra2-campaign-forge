# DISAGREE.md — S15-K5 与台账/上游的口径与异议

## D1 · 与台账 §992 / §996 无数字冲突（停机核验通过）

现场复算盘上基线 `158/137/95`，叠加 S15-K3 2 行、S15-K4 2 行后 `named(S)=141/158=89.24%`、`proved=98/158=62.03%`、`need=143`、`143-141=2`，与台账 §992 的 K3 后 139、§996 的跨卡 141/差 2 逐值一致。按纪律 9 不停机、不凑数。证据：`EVIDENCE/t0_baseline.txt`。

## D2 · K4 “余 19”与 K5 “残余 17”不是数字冲突

`..\S15_K4\UNKNOWNS.md` 的“余 19”是**现场 coverage 尚未并 K3 delta** 的口径，包含 K3 已命名的 `006E2A10`/`006E2AA0`；K4 自己又命名 `00726910`/`0071FA30`。本卡按用户指定口径统一到“盘上 + K3 + K4”后，真实残余为 `21-2-2=17`。证据：`EVIDENCE/t0_baseline.txt`; `..\S15-K3\coverage_delta.tsv`; `..\S15_K4\coverage_delta.tsv`。

## D3 · 源文件路径串不是方法名证据（引用 R14_COMMON §6 纪律 8/9、§8.1 ⑨）

`D:\ra2mdpost\TAction.CPP` 与 `D:\ra2mdpost\Event.CPP` 在 `.data` 中存在，且前者有 4 个代码 xref、后者 7 个；但本机没有 `D:\ra2mdpost` 源码树、没有 PDB，字符串本身只证明源文件名与 assert/日志站点，不能推出被命名函数的方法名。按“未见 ≠ 不存在，但也不能把语义当权威名”处理。证据：`EVIDENCE/strings_trigger_candidates.txt`; `EVIDENCE/source_string_neighborhood.txt`; `EVIDENCE/source_string_xref_sites.txt`。

## D4 · EVA / INI 通道不足以过双证据门槛

EVA 串 80 个有效 xref 站点与 17 个残余目标 0 重叠；INI 相关命中仅 `<none>`/`none` 通用哨兵落在 `006E6310`/`006F1920`/`00727AA0`/`00751590`，没有触发器/动作/事件/标签专属键。故不能用 EVA/INI 通道为残余目标命名。证据：`EVIDENCE/eva_xrefs.txt`; `EVIDENCE/ini_key_xrefs.txt`。

## D5 · 不重签 K3/K4 已命名项，也不把旧辅助文档当独立权威

`docs/re/trigger_system_manifest.md` / `anchor_claims.txt` 对 3 条音频/主题 helper 只给“Voc/Vox/Theme 名查找”语义，不是权威方法名；且 K4 已明确 ABI 深挖文档与目标同 MD5，不能当第二独立源（台账 §996 三）。本卡未据此命名。证据：`EVIDENCE/yrpp_residual_addr_matches.txt`; `..\S15_K4\DISAGREE.md` D3。

## D6 · 交付卫生

`coverage_delta.tsv` 为空；未改 `COVERAGE/coverage.tsv`、未写台账、未改 `ra2youli/` 下任何文件、未 git commit。所有写入仅 `lead\next_re_20261117_r14\S15_K5\`。
