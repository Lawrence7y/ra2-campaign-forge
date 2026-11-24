# 卡 R17-R19-RTTI-XCHECK · 拿 in-binary RTTI 类名去核 coverage 的类名（事实底座交叉验证）

纯静态 + 表内比对。镜像钉死：`ra2youli\gamemd.exe` sha256 `73201CC0…F67476`；**报告第一行写实际路径与 sha256**。

## 〇、为什么这件事重要
本项目的类名长期部分依赖 YRpp 知识库代理，而 `D-51` 明确「不接受仅靠 YRpp 知识库代理的 ②」。
现在有了**二进制内自证的类名集合**（`R17_R13_NAME_TABLE` + `R17_AUDIT_R13` 已过跨家族审计，A1–A5 全 AGREE）：
`vtable[-4]` → COL → `+12` pTD → `+8` 内联名，共 **988** 个 TypeDescriptor 名字（`.?AV` 962 / `.?AU` 26）。
本卡就是用这份**独立来源**去核对 `coverage.tsv` 里出现的类名。

## 一、要产出的东西
**Q1 · 建 in-binary 类名集合**
 复现 988 个 TD 名字（方法同上；不要求重新发明，用同一链条即可，但**必须自己算一遍**并给总数与前缀分布）。
 归一化：去掉 `.?AV` / `.?AU` 前缀与尾部 `@@`，得到裸类名集合（保留大小写原样；另给一份全小写版本用于比对）。

**Q2 · 抽 coverage 里出现的类名**
 读 `COVERAGE\coverage.tsv`（18,498 数据行 / 8 列，第 4 列是语义文本）。
 从第 4 列里抽取**看起来像类名**的 token：以 `Class` 结尾的标识符（例如 `BuildingClass`、`TechnoClass`、`AnimClass`…）。
 统计：出现过的**不同**类名个数、各自出现的行数（Top 30 列表 + 全量写进 tsv）。

**Q3 · 对账（本卡核心）**
 把 Q2 的类名集合与 Q1 的 in-binary 集合比对，给出三桶：
 - **BOTH**：两边都有（个数 + 举例 ≤10）；
 - **COVERAGE_ONLY**：只在 coverage 出现、in-binary 里没有（个数 + **全量列出**）；
 - **RTTI_ONLY**：只在 in-binary 有、coverage 从未提及（个数 + 举例 ≤10）。
 对 COVERAGE_ONLY 逐个标注可能原因（如：模板类名被展开、名字是子系统名而非类名、YRpp 命名差异、拼写差异），**但不得断言**，只给「可能原因 + 你据此判断的依据」。

**Q4 · 诚实限制**
 写清：① in-binary 名字集合只覆盖**有 RTTI 的类**（无 RTTI 的类不会出现）；② coverage 的类名是**人写的语义文本**，抽取靠 `Class` 后缀，会漏会多；
 ③ 因此 BOTH 只能说明"不矛盾"，COVERAGE_ONLY 也**不等于**"名字错"。这一段必须写，防止下游把本卡当成"类名正确性判定"。

## 二、铁律
1. 报告第一行写实际路径与 sha256；不符即作废。
2. 数据读取限 `.rdata`/`.data`（建名集合）+ 只读 `coverage.tsv`；声明扫描字节数。
3. 只读；不建进程、不调试、不启动 gamemd；产物只写本卡目录；**不得修改 `coverage.tsv`**。
4. 中间结果先落盘，严格 **8 分钟**预算。
5. 取不到写「未取得」，严禁编造。

## 三、产物（只写本目录）
`lead\next_re_20261117_r14\R17_R19_RTTI_XCHECK\`
- `REPORT.md` —— 第一行镜像+sha256；Q1–Q4
- `rtti_names.tsv` —— 裸类名 \t 前缀类型 \t TD VA
- `coverage_classnames.tsv` —— 类名 \t 出现行数
- `reconcile.tsv` —— 类名 \t 桶（BOTH/COVERAGE_ONLY/RTTI_ONLY） \t 备注
- `work.py` —— 可复跑