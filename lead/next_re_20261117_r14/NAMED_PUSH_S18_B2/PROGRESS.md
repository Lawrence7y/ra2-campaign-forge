# NAMED-PUSH — S18 B2 PROGRESS

> 每核完 5 行追加一次。执行纪律：先目录、先骨架、逐行核完即落盘。

## 进度日志

- 【初始化】目录/REPORT 骨架/delta(仅表头)/base_rate/PROGRESS 已建立（2026-11-20）。
- 【取证准备】筛选 18 行(filter_b2)→四环取证(analyze)→② 发现 slot>40 漏检、扩 k≤128 重跑(resolve_wide + witness_core)→③b 站点签名(compact3/ch3_summary)→候选深核(deep/verify_b2/ch3_deep/dump_jmptbl/check_vt) 全部完成；逐行裁定字典已定。
- 【1–5 行落盘】005C2A60 / 005C2CB0 / 005C3710 / 005C3B10 / 005C3F80：②全钉住、③b全 FAIL（unknown/bool/null/malloc 模板）、④全 PASS；EVIDENCE 已落盘。
- 【6–10 行落盘】005C4110 / 005C44E0 / **005C46E0(③b① 成立)** / 005C4CA0 / 005CAAC0：005C44E0/46E0/4CA0/005CAAC0 的 slot41/43/44/50 扩回扫后 RTTI 钉住；005C46E0 双跳转表判 ③b① 成立；EVIDENCE 已落盘。
- 【11–15 行落盘】005D8170 / 0064A0C0 / 0064DEA0 / 006516F0 / **0071F8C0(③b② 成立)**：三个真名普通函数 ②/③/④ 全 FAIL；0071F8C0 被调 0x80004003 E_POINTER + jl 判 ③b② 成立、②④钉住；EVIDENCE 已落盘。
- 【16–18 行落盘】00773BC0 / 00774410 / 00774900：②钉住、③b FAIL(p3=0/未知)、④ PASS；EVIDENCE 已落盘。
- 【收口】18 份 EVIDENCE + delta(2行) + base_rate(B2 18/15/2/15/2) + REPORT 全量落盘并复核字节。done。
