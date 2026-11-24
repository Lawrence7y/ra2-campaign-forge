# 卡 R17-AUDIT-R20 · 异族审计 R20（本轮改动了台账里的一个数字，必须独立复核）

审计对象：`lead\next_re_20261117_r14\R17_R20_RECON\`（REPORT.md / normalization.tsv / unresolved.tsv / rtti_names.tsv / work.py）。
**禁止 import 或复用执行方 work.py**，自写独立实现。镜像钉死：`ra2youli\gamemd.exe` sha256 `73201CC0…F67476`；**报告第一行写实际路径与 sha256**。

## 〇、为什么必须审
上一轮台账 `§1061` 记的是 **COVERAGE_ONLY 220**。本轮 R20 报纠正值 **26**（BOTH 403 / RTTI_ONLY 383），
并称 194/220 = **88.18%** 是 MSVC 前缀/分段/模板切分产物。**这是一个会写进台账的纠正**，若 R20 自己也算错，就会造成二次污染。

## 一、必须裁定
**A1 · 三桶数是否成立**：独立复算 BOTH / COVERAGE_ONLY / RTTI_ONLY。注意执行方的口径细节 ——
  它写「BOTH 403（按 coverage-token 口径）；RTTI 条目侧 605 覆盖 + 383 = 988」。请判明：**BOTH(403) 与「RTTI 被覆盖的 605」为何不等**？
  这个差（403 vs 605）是口径差（一个 coverage token 命中多个 RTTI 名？）还是算错？必须给明确解释。

**A2 · 归一化是否过度消解**：这是本卡最关键的一项。
  执行方用「MSVC 前缀链 + 下划线分段 + 模板首段基名」把 194 条消解掉。**过度消解会让 COVERAGE_ONLY 假性减小**。
  请抽查**至少 20 条**被消解的条目，逐条判断该消解是否**合理**（例如 `PAVBombClass`→`BombClass` 合理；
  但 `AVRTacticalClass` 若被消解成 `RTacticalClass` 再消成 `TacticalClass` 就可能**过度**）。
  给「合理 / 过度」逐条判定与合计。**若发现过度消解，必须给出纠正后的 COVERAGE_ONLY 数**。

**A3 · 剩余 26 条的归因是否站得住**：执行方分布为 (a)无独立vtable 6 / (b)多重继承复合名 3 / (c)模板类 9 / (d)疑似命名差异 5 / (e)无法判定 3。
  请独立复核其中**至少 12 条**（覆盖五类），判定归因是否正确；特别核 (d) 那 5 条是否真的只是「疑似」而非被无证据地判成「名字错」。

**A4 · 正面结论是否成立**：执行方称「全量 403/429 = 93.94% 的 coverage 类名可在 in-binary RTTI 定位」。
  请判定该表述是否**恰当地受限于**「in-binary 只覆盖有 RTTI 的类」这一前提；若表述会误导，给出应改的措辞。

## 二、铁律
1. 报告第一行写实际路径与 sha256；不符即作废。禁止复用执行方脚本。
2. **不得修改 `coverage.tsv`**；不得修改 `R17_R20_RECON` 下任何文件。
3. 数据读取限 `.rdata`/`.data`，声明字节数；需反汇编时锚点对齐。
4. 只读；不建进程、不调试、不启动 gamemd；产物只写本卡目录。
5. 中间结果先落盘，严格 **8 分钟**预算。
6. 取不到写「未取得」，严禁编造。

## 三、产物（只写本目录）
`lead\next_re_20261117_r14\R17_AUDIT_R20\`
- `VERDICT.md` —— 第一行镜像+sha256；A1–A4 逐项 AGREE/DISAGREE/无法判定 + 必改项
- `norm_spotcheck.tsv` —— A2 的 ≥20 条抽查：原 token \t 消解为 \t 是否合理 \t 理由
- `attrib_check.tsv` —— A3 的 ≥12 条复核
- `audit.py` —— 独立实现