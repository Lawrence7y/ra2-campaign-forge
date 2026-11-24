# M24 PROGRESS — S20_KPROVED PARTIAL 并入（白名单 28 / 黑名单 12）

## 写域与前置
- 写域：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\` + `...\M24\`；其余只读。
- 改前备份：`_hygiene\coverage.M24.bak`（与改前 coverage.tsv 逐字节一致，SHA-256 `B903B798D2B68CB0379E4DF054FB5D11F8CA636C0A0A85614CA7F3CA8B83E48F`）。
- 未建 venv、未 pip install（全程 Node 内置 fs/crypto；审计脚本为审计员自写，本卡未运行）。
- coverage.tsv 格式陷阱已验证：表头 8 列**逗号**分隔（`entry,subsystem,name,one_line_semantics,grade,evidence_path,n_sources,conflict`），数据行 8 列 **TAB** 分隔；未按逗号切表。

## 输入与判定
- 唯一输入：`S20_KPROVED\coverage_delta.tsv` 40 行；审计 `a-S20-KPROVED` 裁 **PARTIAL**（exact 通道判据退化为槽号匹配）。
- 白名单 **28** 行 = 直呼 21 + exact 7；黑名单 **12** 行（7 行仅 atexit 析构器安装的虚表、5 行接收者为运行时寄存器/工厂返回值无静态归属）；W∩B=∅，W∪B=40 行全覆盖。
- 全部 28 行改前盘上 grade 均为 `[静态推断]`（幂等校验通过）；12 行黑名单改前改后逐字节一致。

## 改动前后 grade 直方图（第 5 列）
| grade | 改前 | 改后 | Δ |
|---|---:|---:|---:|
| `[已证]` | 1,387 | **1,415** | +28 |
| `[静态推断]` | 6,013 | **5,985** | −28 |
| `[未证]` | 11,031 | 11,031 | 0 |
| 合计 | 18,431 | **18,431** | 0 |

## coverage.tsv SHA-256 与行数
| | SHA-256 | 数据行 |
|---|---|---:|
| 改前（=`_hygiene\coverage.M24.bak`） | `B903B798D2B68CB0379E4DF054FB5D11F8CA636C0A0A85614CA7F3CA8B83E48F` | 18431 |
| 改后 | `36A70C9444E64F63B4C49BA24D6E830528BF857C211636BFC3AD15A49F8DE28E` | 18431 |

- 改动行数 **28**，均仅第 5 列 `[静态推断]`→`[已证]`；header 与其余 18,403 数据行逐字节不变。
- entry 增删 0；name / one_line_semantics / subsystem / evidence_path / n_sources / conflict 对被改 28 行逐列零差异。
- `0075F8B0`：grade→`[已证]`，subsystem 仍 `S20`、name 仍 `WaveClass::slot54`、conflict 仍 `1`；S20/S07 归属 OPEN 争议不裁决（见 MERGE_LOG.tsv 与 PANEL.md M24 段）。
- 黑名单 12 行整行不动（保持 `[静态推断]`，连名字也不动）。

## 计数
- applied **28** / rejected **12**（rejected 12 行逐行审计理由见 `M24\MERGE_LOG.tsv`）。
- S20：proved 40→**68/410 = 16.59%**（门槛 205，仍差 137）；named(S-R14) 399/410=97.32% 不变；strict 42/410=10.24% 不变。
- `conflict=1` 全表 **254→254**（不变）；CONFLICTS/PENDING 未写（不在写域内）。

## PANEL 更新确认
- 文件：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\PANEL.md`
- 已更新：标题 M24 前缀；§三分母 全表/atlas 内 `[已证]` `1,387 / 1,382`→`1,415 / 1,410`；覆盖面板 S20 行 proved `40`→`68`、`9.76`→`16.59`；TOTAL 行 proved `1382`→`1410`、`10.70`→`10.92`、全表 `[已证] 1387（atlas 内 1382）`→`1415（atlas 内 1410）`；新增「M24 并表说明」段与历史行 M24。
- 三分母 A/B/C = 12,916/14,487/18,431 不变；named_pct_S(R14/strict) 双列、S13 240/148 双分母、S22 不参与排名全部保留。
