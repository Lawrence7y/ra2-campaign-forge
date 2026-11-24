# 卡 R17-R17-SLOT73-MAP · 槽 73 全类反向映射（谁用 0x43F180 / 0x4D3780 / 0x6F4A70）

纯静态、只读、有界。**镜像钉死**：`ra2youli\gamemd.exe` sha256 `73201CC0…F67476`；**报告第一行写实际路径与 sha256**。

## 〇、背景与已确立的锚点
- 前一轮已用 `vtable[-4]` → COL → TypeDescriptor 建了「类名 → vtable」索引（`R17_R15_SLOT73\class_index.tsv`，自称 1211 vtable / 951 类名，**待审计**）。
- 已知：BuildingClass #73 = `0x43F180`；TechnoClass #73 = `0x6F4A70`；Infantry/Unit/Aircraft #73 = `0x4D3780`。
- 外部线索（需你独立核）：`coverage.tsv` 有一行 `entry 004D3780` 的语义称其是「shared slot73 for RTTI Aircraft/Foot/Infantry/Unit」。

## 一、要产出的东西
**Q1 · 全量反向映射**：对所有**槽数 ≥ 108** 的 vtable，读出槽 **#73** 与槽 **#107** 的值；
 按「值」反向分组，输出：给定函数地址 → 出现在哪些类的哪些 vtable 的 #73/#107。
 重点给这三个函数的完整反向清单（一个都不能漏）：`0x43F180`、`0x449440`、`0x4D3780`、`0x6F4A70`。

**Q2 · FootClass 补齐**：`.?AVFootClass@@` 的主 vtable（索引里疑似 `0x7E8C94`，槽数 341）—— 其 #73 与 #107 各是什么？
 并把 Aircraft / Foot / Infantry / Unit **四个类**的 #73 值并排列出。

**Q3 · 与外部线索对账（重要，防误读）**：
 外部线索称某行 `entry 004D3780` 的 slot73 位于 `0x7E23C8` / `0x7E8DB8` / `0x7EB17C` / `0x7F5D94`。
 请核：这四个地址是否恰好等于 Aircraft / Foot / Infantry / Unit 四个类**主 vtable 基址 + 0x124**（即槽 73 的字节位置）？
 逐项给「主 vtable + 0x124 = ?」与「是否相等」。
 若全部相等，写：「外部线索与本次独立字节分析一致」；若有不等，逐项列出差异。

**Q4 · 结论措辞**：基于 Q1–Q3 回答：
 1. `0x43F180` 是否**仅** BuildingClass 用（其它类 #73 都不是它）？
 2. `0x4D3780` 是否被 Aircraft/Foot/Infantry/Unit 四类共用（其余类有没有也用它）？
 3. 给一句可直接引用的表述，形如「槽 73 上：BuildingClass 用 X，TechnoClass 用 Y，Aircraft/Foot/Infantry/Unit 共用 Z」。
   **只写被字节支持的部分**；类名必须来自索引（若索引对某类给不出名字，写未取得，不要猜）。

## 二、铁律
1. 报告第一行写实际路径与 sha256；不符即作废。
2. 本卡只需读 4 字节槽值 + COL/TD 小结构，**不需要大规模反汇编**；需要时锚点对齐。
3. 数据读取限 `.rdata`，**声明字节数**。
4. 只读；不建进程、不调试、不启动 gamemd；产物只写本卡目录；不改任何既有产物（尤其不得改 `R17_R15_SLOT73` 下文件）。
5. 中间结果先落盘，严格 **7 分钟**预算。
6. 取不到写「未取得」，严禁编造类名。

## 三、产物（只写本目录）
`lead\next_re_20261117_r14\R17_R17_SLOT73_MAP\`
- `REPORT.md` —— 第一行镜像+sha256；Q1–Q4
- `reverse_map.tsv` —— 函数值 \t 类名 \t vtable 基址 \t 槽号（73 或 107）
- `four_classes.tsv` —— Aircraft/Foot/Infantry/Unit 的 主vtable / 槽数 / #73 / #107 / 主vtable+0x124
- `work.py` —— 可复跑