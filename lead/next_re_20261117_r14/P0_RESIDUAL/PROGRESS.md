# P0-RESIDUAL · PROGRESS

## 状态
完成（收口裁定卡，不产新语义结论）。

## 写域 / 只读纪律
- 写：仅 `lead\next_re_20261117_r14\P0_RESIDUAL\`。
- 只读：`ra2youli\gamemd.exe`（SHA 现场重算一致）、`COVERAGE\`、`P0_CLOSE\`、`P0_GATE\`、atlas。
- 未改 gamemd.exe / ra2youli / COVERAGE / 台账；未 git commit。

## 环境自校
- python 3.12.10 / capstone 5.0.7 / pefile 2024.8.26（未用 pefile 于主流程）。
- capstone 全程 `skipdata=True`；`.text=[00401000,007E038D)`。
- SHA256 = 73201CC0…F67476 ✓；atlas 12,916 行（size 十进制读取）。
- 虚表自 `.rdata` 定界 = 1214 表 / 14,044 槽（与基线吻合）；未读 `vtables_v2.json`。
- 归属用 `Atlas.owner()`（区间包含）；未用 `entry_at_or_before`。

## 执行步骤与结果
1. 五通道枚举（A E8/E9 rel32 / B EB rel8 / C vftable 槽+裸游程 / D 前向孤儿 / E atlas size 可疑）：
   - 候选并集 distinct = **2,972**（A 404 / B 993 / C 597 / D 1,365 / E 4）。
2. 去重（coverage 13,397 + probe 112 + 非函数容器）：排除 **481**，待裁定 **2,491**。
3. R14-R10 分轨裁定（vt_direct 0 / true_entry 2,491）：
   - **FUNC 1,096 / NOT_FUNC 1,395 / UNDECIDABLE 0**。
4. 停机核验：FUNC 1,096 ≫ 预期 358~395 → 诊断不凑数，定位为估计口径差（见 §6）。
5. 基线测试：leaf_pattern 在合格地址中 12.5% vs 随机 3.6%（~3.5x 富集，非纯噪声）。

## 核心数字
- 候选总数 2,972｜去重后 2,491｜FUNC·NOT_FUNC·UNDECIDABLE = 1,096·1,395·0。
- 通道贡献：A 404 / B 993 / C 597 / D 1,365 / E 4（候选 distinct）。
- 新分母 = 13,397 + 1,096 = **14,493**，**不落入** 13,755~13,792（超 +701）。
- 推翻理由：估计区间基于 c4a-only（361 FW-only，→13,796，仅超 +4）；定稿 R14-R10 含 c4b，额外 697 叶形态入口。

## 三口径交叉核对（EVIDENCE\TWO_READINGS.tsv）
- 严格 R14-R10：1,096（c4a 399 + 有引用 c4b 85 + 无引用叶 c4b 612）→ 14,493。
- 保守（c4a + 有引用 c4b）：484 → 13,881（超 +89）。
- 基线（c4a only）：399 → 13,796（超 +4）。

## 已知冲突 / 未决（留 P1，本卡不裁）
- `0x4824D4`：probe 标 call_site，§926 定洞内真入口；按任务减 probe 排除。
- `0x7775C0`：coverage 非 atlas 真函数，五通道未命中（无标准签名，靠注册入表）⇒ 通道非完备证明。
- 612 条无引用叶形态 FUNC 需 P1 用数据段指针表/异常表/回调复核。

## 交付
CANDIDATES_ALL.tsv · DEDUP_VS_COVERAGE.tsv · RESIDUAL_ADJUDICATION.tsv · RESIDUAL_SUMMARY.md · 本文件 · EVIDENCE\（不截断）· work\（可复跑）。
