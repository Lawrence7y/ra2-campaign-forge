# M28 PROGRESS

## 结论
- 并入行数（applied）：**4**（白名单 0070F1D0 / 0070FD70 / 00739AC0 / 00739CD0，仅 grade `[未证]`→`[已证]`）
- rejected 数：**7**（黑名单整行不动）
- `[已证]` 前后值：**1,452 → 1,456**（+4）
- CONFLICTS 行数：**469 → 470**（wc -l；数据行 468→469，+1 登记 007C978A 子系统归属争议）
- coverage 前后 SHA-256：
  - 前：`2c599504e7025eab3409c643b6c4b99bd29d1938af2bf1c067bc5f5beef30206`
  - 后：`b1089f63e3fc180e35c5a4b7f5036d8ece63af1f5a1ef54856c4f15572f40a59`
  - 备份：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\coverage.M28.bak`

## grade 直方图（全表 coverage.tsv）
| grade | 前 | 后 | 变化 |
|---|---:|---:|---:|
| `[已证]` | 1,452 | 1,456 | +4 |
| `[未证]` | 11,031 | 11,027 | −4 |
| `[静态推断]` | 5,948 | 5,948 | 0 |
| 合计 | 18,431 | 18,431 | 0 |

- atlas 内 `[已证]`：1,447 → 1,451（4 行全在 atlas）
- S20：proved 68 → 72/410=17.56%（门槛 205，差 133）；named(S-R14) 399 不变；strict 42 不变
- `conflict=1` 计数：254 → 254（本卡不新增 coverage conflict 标记）

## 4 applied
| entry | 原 grade | 新 grade | 审计依据（VERDICT §2 ③）|
|---|---|---|---|
| 0070F1D0 | [未证] | [已证] | +0x42 CRT::_new → +0x7c AnimClass::AnimClass → +0x96 AnimClass::SetOwnerObject |
| 0070FD70 | [未证] | [已证] | +0x57/+0x8e ctor、+0xa4 SetOwnerObject |
| 00739AC0 | [未证] | [已证] | +0xed _new、+0x133 ctor、+0x145 SetOwnerObject、+0x1f9 VocClass::PlayAt |
| 00739CD0 | [未证] | [已证] | +0xc0 _new、+0x107 ctor、+0x119 SetOwnerObject、+0x1e3 PlayAt |

## 7 rejected（整行不动，保持盘上现值）
| entry | 盘上 grade | 理由 |
|---|---|---|
| 004C54E0 | [未证] | 四环不足：③ 无 S20 锚，地图/建筑逻辑 |
| 0062DF20 | [静态推断] | 归属对名字错：实为构造器，Update_A 名错 |
| 0062E070 | [静态推断] | 归属对名字错：实为标量删除析构器，Update_B 名错 |
| 0062F230 | [未证] | 四环不足：③ 无 S20 锚 |
| 0075E950 | [未证] | 四环不足：③ 无 S20 锚，更像 tile 构造器 |
| 007610F0 | [未证] | 四环不足：③ 无 S20 锚 |
| 007C978A | [未证] | MSVC CRT atexit 注册包装；0x7C978A%16=10 违入口判据；336 调用者跨 ≥13 子系统 ⇒ S20 归属不成立（另登记 CONFLICTS） |

## 校验
- coverage.tsv：18,431 数据行；表头逗号、数据行 TAB（8 列）保持；仅 4 行第 5 列（grade）变化，其余列逐列零差异。
- 黑名单 7 行与备份逐行一致（整行未改动）。
- CONFLICTS.tsv：5 列格式不变；新增 1 行 `007C978A subsystem coverage:S20 ... OPEN:疑似子系统归属错误`，含全部要求备注；coverage 里 007C978A 的 subsystem 仍为 S20（未改）。
- 备份完成且字节一致；未建 venv、未 pip install。

## 来源
- `S20_DIRECT\_audit\VERDICT.md`（a-S20-DIRECT 裁决 PARTIAL）
- `S20_DIRECT\coverage_delta.tsv`（11 行输入）
