# REPORT — R17_R47_GRADE_NORM（FACT_INDEX v5.1）

## 1. 基底与改动范围
- 基底：`R17_R46_FACTINDEX_V5/FACT_INDEX.tsv`（v5.0，F01–F49，49 条）。
- 只改 `grade` 与承载其限定的 `limitations`；`statement`、`evidence_paths`、`fact_id` 未动。
- F01–F49 不增删、不重排，总数仍 49。
- 未修改 R17_R46_FACTINDEX_V5 及更早六个 FACT_INDEX 目录（内容哈希前后对比见 §7）。

## 2. grade 统计
改后仅 4 个取值：[已证]=27，[静态推断]=1，[流程]=19，未取得=2；合计 49。

| grade | 条数 |
|---|---:|
| [已证] | 27 |
| [静态推断] | 1 |
| [流程] | 19 |
| 未取得 | 2 |
| 合计 | 49 |

## 3. 逐条改动（改前 grade → 改后 grade → 搬入 limitations 文本）
说明：带斜杠后缀的原 grade 中，两个限定子句均按原措辞搬入，并以「；」连接；未改写原措辞。F26 的「裁定」已在 statement，不搬入。

| fact_id | 改前 grade | 改后 grade | 搬入 limitations 的文本 | 改后 limitations |
|---|---|---|---|---|
| F18 | [已证]（仅用例数与观测数） | [已证] | 仅用例数与观测数 | 仅用例数与观测数；归因结论不得写「已证」；D 用例是「不可构造/未观测到」、不是「不存在该判据」；A 组 4/6 为前卡读数、非本卡复现；观测数不得外推为行为唯一。 |
| F21 | [已证]（结构）＋未取得（表内容） | [已证] | 表内容未取得 | 表内容未取得；表内容静态不可见（基址在 .data 未初始化尾段、运行期填），不得声称已看到表项；不改变 ②-b 收口。 |
| F22 | [已证]（数字）/ 限定为强制同引 | [已证] | 数字；限定为强制同引 | 数字；限定为强制同引；三项限定不可拆；引 1,654 必须同引①②③。 |
| F24 | [已证]（数字与负结论）/ 归因见 §16.1 | [已证] | 数字与负结论；归因见 §16.1 | 数字与负结论；归因见 §16.1；R_OK 863 是「至少一个路径解析到真实文件」，不等于「逐 entry 专属证据」；引 §16.1 只能引其「判据」，其表内数字是历史快照（旧 478/374/802），数字须取现盘。 |
| F25 | [已证]（数字）/ 界向为强制同引 | [已证] | 数字；界向为强制同引 | 数字；界向为强制同引；界向不可省；对外声明按 D-44 一律用严格列 1/22，名义 3/22 并列报告。 |
| F26 | [流程]（裁定） | [流程] | —（裁定已在 statement，未搬） | 对外口径不变（D-44）：严格 1/22 与名义 3/22 并列报告。 |

搬入 limitations 的条目数：**5**（F18、F21、F22、F24、F25）。

## 4. 路径解析（括号深度切分）
- 解析器对改后 `FACT_INDEX.tsv` 的 `evidence_paths` 逐行处理：ASCII 与全角括号均计入深度，仅在深度为 0 的分号处切分；再剥离括号内节标识，按仓库根相对路径检查存在性。
- 结果：路径项 120，RESOLVED 120，BROKEN 0。
- BROKEN 明细：无。

## 5. SHA-256 自证
- 拼接方法：逐行 `fact_id + "\t" + statement`，行间 `\n`，UTF-8 字节流。
- fact_id + statement 两列拼接 sha256：改前 81aaa861aa37c43f5921b03a17c8b6d6039db51c05a49470fc3b9286ae75244b；改后 81aaa861aa37c43f5921b03a17c8b6d6039db51c05a49470fc3b9286ae75244b；**EQUAL**。
- fact_id 单列拼接 sha256：改前 a4d2ad985b3bc598eca24fe92687200ef129be2d9edcd2225265fd3d61eac75e；改后 a4d2ad985b3bc598eca24fe92687200ef129be2d9edcd2225265fd3d61eac75e；**EQUAL**。
- statement 单列拼接 sha256：改前 f7ee402f876f5d8fda6601c1fc99b80276eae9c668f987b339b2a3c9b975f76a；改后 f7ee402f876f5d8fda6601c1fc99b80276eae9c668f987b339b2a3c9b975f76a；**EQUAL**。
- evidence_paths 单列拼接 sha256：改前 f98cb118c5b2138a3f2b5433966a67b36d3e245d014b36a334b3a59e8014d94a；改后 f98cb118c5b2138a3f2b5433966a67b36d3e245d014b36a334b3a59e8014d94a；**EQUAL**。

## 6. CR 校验
- FACT_INDEX.tsv：CR 字节计数 0。
- README.md：CR 字节计数 0。
- REPORT.md：以 LF 写出并复检，CR 字节计数 0。

## 7. 前置 FACT_INDEX 目录未改动
递归收集每个目录内文件路径与文件内容 SHA-256，再聚合成目录摘要；写产物前后对比如下。

| 目录 | 文件数 | 改前摘要 | 改后摘要 | 结论 |
|---|---:|---|---|---|
| R17_R46_FACTINDEX_V5 | 4 | bd24b17a2a937cced14ab272939fb419e1634740f9d608fa5233aec47bbfdc38 | bd24b17a2a937cced14ab272939fb419e1634740f9d608fa5233aec47bbfdc38 | EQUAL |
| R17_R45_FACTINDEX_V4 | 4 | 63777ed740a9be7106ff42cdc5335c7dd8ce97b1ed6da7d25ec3040a0a594ac8 | 63777ed740a9be7106ff42cdc5335c7dd8ce97b1ed6da7d25ec3040a0a594ac8 | EQUAL |
| R17_R44_FACTINDEX_V32 | 5 | c1375594bd21bc5f0fb32f5bf5452ac81b8248f92c84c7145b7d56e4e14d5b70 | c1375594bd21bc5f0fb32f5bf5452ac81b8248f92c84c7145b7d56e4e14d5b70 | EQUAL |
| R17_R42_F23_FIX | 2 | a195759f1f77ce56891aa1c74c55a00c510db39e528afd2f7e286a68d5cf2eaa | a195759f1f77ce56891aa1c74c55a00c510db39e528afd2f7e286a68d5cf2eaa | EQUAL |
| R17_R40_FACTINDEX_V3 | 4 | f8e057dd770ec7fe106eae3fa29eb4e996ed55bc98bf142f1e7ea92136124953 | f8e057dd770ec7fe106eae3fa29eb4e996ed55bc98bf142f1e7ea92136124953 | EQUAL |
| R17_R38_FACTINDEX_FIX | 4 | cff1a30261ed21cfc8445d1aefc6bf09f6fbe953e65631a09d1166578a798478 | cff1a30261ed21cfc8445d1aefc6bf09f6fbe953e65631a09d1166578a798478 | EQUAL |
| R17_R34_FACT_INDEX | 4 | 072cafc53879ff1e9c189fdb294a634c19fa25256be2b88be171f6998cf04672 | 072cafc53879ff1e9c189fdb294a634c19fa25256be2b88be171f6998cf04672 | EQUAL |

所有前置目录摘要 EQUAL。
