# PROGRESS · M25 合并员（S10_KPROVED，白名单 34 行提级）

## 结果摘要
- 并入行数：**34**（28 direct from VERDICT §2 + 6 exact：0045A560/0045A610/006B1850/006B1900/006B8660/006B8710）
- rejected：**6**（整行不动：0045A420/0045A500/006B1710/006B17F0/006B8520/006B8600）
- 只改 grade [静态推断]→[已证]，name/one_line_semantics/subsystem/evidence_path/n_sources/conflict 逐列零差异。

## 前后 grade 直方图（全表 18,431 行）
| grade | 前 | 后 | 变化 |
|---|---:|---:|---:|
| [已证] | 1,415 | 1,449 | +34 |
| [静态推断] | 5,985 | 5,951 | −34 |
| [未证] | 11,031 | 11,031 | 0 |
| 合计 | 18,431 | 18,431 | 0 |

- conflict=1 前 254 → 后 254（不变）。
- 差异行逐列核对：恰好 34 行，全部只有第 5 列（grade）从 [静态推断] 变为 [已证]，其余 7 列与备份逐字等。

## S10（atlas 分母 526）
- proved: 117 → **151/526 = 28.71%**（门槛 263，差 112）
- named: 513 不变（513/526 = 97.53%）
- 白名单 34 行全在 atlas 内，atlas 内 [已证] 1,410 → 1,444。
- 004CBBA0 仅按 atlas+direct 单通道并入，未声称虚表归属。

## coverage SHA-256 与行数
| 项 | 前 | 后 |
|---|---|---|
| SHA-256 | 36A70C9444E64F63B4C49BA24D6E830528BF857C211636BFC3AD15A49F8DE28E | 502A56FE261108225B1EE975CB26C86ECDF900A5727069A82B67A35A9C27BAF6 |
| 数据行数 | 18,431 | 18,431 |
| 文件字节 | 3,671,713 | 3671509 |

备份：D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/_hygiene/coverage.M25.bak

## PANEL 确认
D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/COVERAGE/PANEL.md 已更新：标题条加 M25 并表说明；全表 [已证] 1,415→1,449、atlas 内 1,410→1,444；S10 proved 117→151/526=28.71%；三分母 A/B/C 不变；conflict=1 254 不变。

## 明细
- 逐行 applied/rejected：见 M25/MERGE_LOG.tsv
