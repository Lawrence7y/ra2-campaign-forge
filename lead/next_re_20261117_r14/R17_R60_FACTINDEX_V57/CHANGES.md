# CHANGES.md — FACT_INDEX v5.6 → v5.7

基底：`R17_R59_FACTINDEX_V56\FACT_INDEX.tsv`（v5.6，54 条）。总条数不变 **54**，改 **6 行** `evidence_paths`；`statement`/`grade`/`limitations` 一字未动。

## 1. 把 13 处「裸目录」全部钉到承载文件

v5.6 把「裸目录无锚」判为可接受形态（`evidence_paths` 可指「产出该事实的卡」）。但它只证明**卡存在**，不证明**证据在卡内某处**。本版逐卡核实承载文件后钉死。

| 条目 | 原（裸目录） | 新（文件） | 核实依据（该文件含条目关键词） |
|---|---|---|---|
| F19 | `R17_R8_RESIDUAL` | `\REPORT.md` | `0x47C620` / `E8` / `正控` |
| F19 | `R17_R10_DISPATCH` | `\REPORT.md` | `派发` / `jmp` / `call [` |
| F19 | `R17_AUDIT_R10` | `\VERDICT.md` | `排除` / `E8` / `正控` |
| F19 | `R17_R26_HOST_ROLE` | `\REPORT.md` | `0x5A6510` / `B1` |
| F19 | `R17_R29_UPSTREAM` | `\REPORT.md` | `上游` / `0x5A5020` / `B1` |
| F20 | `R17_R36_VERIFY_TABLEBASE` | `\VERDICT.md` | `0x87F7E8` / `节表` |
| F20 | `R17_AUDIT_R30` | **`R17_AUDIT_FACTINDEX\VERDICT.md`** | 见 §2（换卡） |
| F21 | `R17_R35_V5657A0_TABLE` | `\REPORT.md` | `0x87F924` / `0x5657A0` / `0x40000` |
| F21 | `R17_R36_VERIFY_TABLEBASE` | `\VERDICT.md` | 同上 |
| F24 | `R16_MEASURE_EVID675` | `\REPORT.md` | `675` / `EVID` |
| F24 | `R16_AUDIT_EVID675` | `\VERDICT.md` | `675` / `EVID` |
| F50 | `R17_R36_VERIFY_TABLEBASE` | `\VERDICT.md` | `0x87F7E8` / `节表` / `Westwood` |
| F54 | `R17_R36_VERIFY_TABLEBASE` | **`NAMED_PUSH_AUDIT15\VERDICT.md`** | 见 §2（换卡） |

## 2. 其中 2 处是**换卡**，因为原锚指错了卡（不是换文件名能解决的）

**F20 的 `R17_AUDIT_R30`** —— 该卡是 `0x449440` 全函数体结构裁定的异族审计（A1–A5、AGREE/PARTIAL、必改项 3 条、②-b 不得升格）。而 F20 讲的是「读二进制数据的硬规则：VA→偏移走节表 / `0F BF C3` 的 C3 是 modrm / 只报存在性会方向相反」。**两者无关**（关键词只命中一个 `AGREE`）。

⇒ 换为 `R17_AUDIT_FACTINDEX\VERDICT.md`：该文件含 `0F BF C3`、`modrm`、`节表`，且原文写的是 **`F13 反例 0x5A680B=24 26 0F BF C3`（C3 为 modrm）成立** —— 注意地址是 **`0x5A680B`**，与 F20 正文里的 `0x5A6810` 不同，这是既有审计给 F20 记过的出处偏差，一并登记于此。

**F54 的 `R17_R36_VERIFY_TABLEBASE`** —— 该卡讲 `dword[0x87F924]`（`.data` 未初始化尾段）与 `ecx=0x87F7E8`，是 F21/F50 的证据。而 F54 讲「`PEFormatError` 是读法错的症状 + 四表实测」。**四表一个都不在该卡里**（0/3 命中）。

⇒ 换为 `NAMED_PUSH_AUDIT15\VERDICT.md`：`R14_COMMON §13.1` 记录的来源就是 `NAMED_PUSH_AUDIT15\SUMMARY.md` 与 `VERDICT.md`，该文件含 `PEFormatError` 与 `0x7E1964`。

## 3. v5.7 核验基线（`anchor_check.txt`，退出码 0）

| 项 | 数 |
|---|---:|
| 路径项 | 138 |
| 文件存在 | **138 / 138** |
| 带锚点 | 116 |
| 　机械核验通过 | **89** |
| 　节号体例通过 | **17** |
| 　人工核验类 | **10** |
| 　池未加载（未核验） | **0** |
| 　目录+锚（NG） | **0** |
| **裸目录（目录即卡）** | **0 ← v5.6 是 13** |
| **MISS** | **0** |

⇒ **全表 138 个路径项现在要么是文件、要么带可解析锚点，没有一项停在目录上。** 8 项自检（4 正控 + 4 反控）全 PASS。

## 4. 三类锚的现状（余下工作讲清楚）

| 类别 | 数 | 状态 |
|---|---:|---|
| 机械可核 | 89 | ✅ 已验证 |
| 节号体例可核 | 17 | ✅ 已验证（但只验「节体内含定位串」，不验内容对应） |
| 人工核验（编号/位置型） | 10 | ⚠ **需人工**，见 REPORT §2 |

## 5. 未改动项（可证）

- 三列零改动；`grade` 仍 27 / 1 / 24 / 2 = 54；条数 54；`fact_id` 连续 F01–F54。
