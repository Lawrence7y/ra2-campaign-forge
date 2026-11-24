D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe ｜ SHA-256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476（本次实读打开并计算；未使用 PATCH_D35R 副本）

# R17-COMMON-2.9 成文回执

## 一、做了什么

对 `lead\next_re_20261117_r14\R14_COMMON.md` 执行 **append-only** 写入：仅在文件末尾追加新节 `## 2.9 【D-53(A) 裁决，2026-11-21】②-b 永久以 [静态推断] 收口 + 书面限制`，既有字节一律未改。写盘前先备份并断言「旧长度前缀 sha256 未变」（PASS），写盘后读回复验（size / 前缀 sha / CR 计数 / 尾部一致，全部 PASS）。

## 二、追加内容摘要

- 定谳句：②-b（占格闸两路径行为层不可区分）**永久以 `[静态推断]` 收口**，依据 D-53(A)，不再投卡探测。
- 书面限制 a–e 与定谳句**同框**（§2.9 第一节），禁止拆分引用。
- 三条已排除路径（逐槽立即数装载 / 直接调用 / 运行期索引派发）标「已排除」并给产物路径。
- 类身份维度排除（3 host 类名未取得），不再走「先定类名再反查调用者」。
- `[已证]` 事实 4 项与定谳状态分列，不升格 ②-b。
- 引用纪律：引用 ②-b 必写 `[静态推断]` 并同引 §2.9。
- 第 7 项 coverage 核对：见下。

## 三、字节与哈希

| 项 | before | after |
|---|---|---|
| 字节数 | 236380 | 241825 |
| SHA-256（整文件） | E7253E44CBEFC446FE8C86519406012FADF10359B212AF5F13BD87EA6325CC5D | 5543CD991E2FEF28AB3EB12A15E2D4414A196E7A343067A854C011003F0DB500 |
| CR 计数 | 1081 | 1081 |
| LF 计数 | 1648 | 1704 |

- 追加段：5445 B，CR = 0（只含 LF）。
- 前缀断言（写盘前，旧长度 236380 B 的 sha256 == before sha）：**PASS**。
- 写盘后读回复验：sizeOK=true / prefixOK=true / crOK=true / tailMatches=true。
- 备份：`R17_COMMON_2_9\R14_COMMON.before_2.9.md`，sha256 E7253E44CBEFC446FE8C86519406012FADF10359B212AF5F13BD87EA6325CC5D（与 before 一致）。

## 四、第 7 项（entry 004D3780）判定

**不是同一槽**。coverage 行 `004D3780` 的 slot73 位于 `0x7e23c8`/`0x7e8db8`/`0x7eb17c`/`0x7f5d94`，槽内为 `0x004D3780`；本节 #73 为 `0x7E3FE0`，槽内为 `0x0043F180`（均已由基准镜像字节复核）。两者仅槽序号 73 / 偏移 +0x124 相同；coverage 行 slot 编号出自 `S12-K2` 的 RTTI 取 size 口径，本节编号出自 `(addr−0x7E3EBC)/4`。本节结论不改变任何 coverage 行 grade。详见 `row_004D3780.md`。

## 五、产物清单

`R17_COMMON_2_9\REPORT.md`、`R14_COMMON.before_2.9.md`、`verify.py`、`row_004D3780.md`（全部只写本目录；目标文件仅末尾追加）。
