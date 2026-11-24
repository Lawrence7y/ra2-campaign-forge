# R16-D1-WIDE-B4 执行报告（收官批）

> 角色：执行器 · 卡号 R16-D1-WIDE-B（批次 B4）· 日期 2026-11-21（R16 第 22 轮起）
> 写域：`lead\next_re_20261117_r14\R16_D1_WIDE_B4\`（仅此目录）；**未写 `COVERAGE\coverage.tsv`**；`gamemd.exe` 仅只读打开。
> 披露指针：每行 ④ 自带 D-47 披露并指向 **§12.6**（`见 R14_COMMON §12.6 与 PANEL 对应披露`）。

## 0. 一句话结论
**只补第 4 列 ④ 成文、未改 grade/判定、未并表。** 本批 11 行全部取得完整 ④ 数据；盘上复核无 SKIP-ALREADY；6 项字节复核 11/11×6 全通过；宿主身份校验（卡面三条教训）11/11 通过。其中 8 行 OK、3 行 CLASS_FIX；1 行按教训①由决定性栈临时写改取唯一写 this 的析构器宿主，按 D-50 如实标 reg；1 行 mov_abs 目标在 .data（按 VirtualSize 校验）。

## 1. 批次派生（集合相减，非按索引）
| 阶段 | 行数 | 说明 |
|---|---:|---|
| sieve_all.tsv（D-52 宽读集合） | 81 | 判据 S1–S7 在 `R16_SIEVE_D1_WIDE/sieve.py`，直接采用，未重筛 |
| has_ring4_on_disk==是（盘上已有④，跳过） | 16 | 不重做 |
| S = has_ring4_on_disk==否 | 65 | 待做全集 |
| − B1.entries | −18 | R16_D1_WIDE_B1/fields.tsv |
| − B2.entries | −18 | R16_D1_WIDE_B2/fields.tsv |
| − B3.entries | −18 | R16_D1_WIDE_B3/fields.tsv |
| 005F4B10 剔除 | −1 | 已在 B3（CLASS_FIX）；Lead 裁定从集合剔除、不补 |
| **本批 B4** | **11** | `S − B1 − B2 − B3`，assert 与集合相等 |

B4 entry 清单：006C6680 006C9890 006CF430 006F3330 006FC0B0 006FCDB0 006FFEC0 00702D40 00706640 00708C30 007730F0

## 2. 盘上现值复核（SKIP-ALREADY）
逐行读当前 `coverage.tsv` 第 4 列：含④ 行数 = **0**，无④ 行数 = **11**；无并发并表覆盖 ⇒ 无 SKIP-ALREADY，11 行全净新增。

## 3. 装配形态分类计数（D-50，含宿主身份校验）
| install_form | 行数 | 判据 |
|---|---:|---|
| ctor_body | 9 | 写 this(disp0) 且宿主真构造器/工厂、无删除签名 |
| mov_abs | 1 | mov [abs],vt 且 abs 在 .data（VirtualSize） |
| reg | 1 | 写 this 但宿主为析构器（非构造器） |
| other | 0 | 其余 |

说明：`mov_abs` 1 行（006CF430）目标 0xB0C110 在 `.data`（按 VirtualSize 范围 0x812000..0xB79BE4；按文件大小仅到 0x87E000 会误判），由 capstone 实测为静态 global 写，非栈槽。

## 4. 逐行状态计数
| status | 行数 |
|---|---:|
| OK | 8 |
| SKIP-ALREADY | 0 |
| SKIP | 0 |
| CLASS_FIX | 3 |

### 4.1 CLASS_FIX 明细（卡面 §3.4 类一致优先，逐字披露见 fields.tsv note）
| entry | 行名类 | 原决定性表(vt/RTTI) | 改取行名类本表(vt/RTTI) | 装表点/宿主 | 形态 |
|---|---|---|---|---|---|
| 006F3330 | TechnoClass | 007E22A4 / .?AVAircraftClass@@ | 007F4960 / .?AVTechnoClass@@ | 006F3130 / 006F2B40 | ctor_body |
| 006FC0B0 | TechnoClass | 007E8C94 / .?AVFootClass@@ | 007F4960 / .?AVTechnoClass@@ | 006F3130 / 006F2B40 | ctor_body |
| 006FCDB0 | TechnoClass | 007E22A4 / .?AVAircraftClass@@ | 007F4960 / .?AVTechnoClass@@ | 006F3130 / 006F2B40 | ctor_body |

### 4.2 宿主身份校验 / SITE_FIX 明细（教训①②）
| entry | 决定性装表点（缺陷/形态） | 采用装表点/宿主 | 形态 |
|---|---|---|---|
| 006C6680 | 决定性 006C6588 已验真构造器；006C6616/006C6886 为析构器（删除签名）弃用 | 006C6588 / 006C6540 | ctor_body |
| 006C9890 | 决定性 00474223 栈临时写 → 唯一写 this 007BA596；宿主 007BA590 为析构器（包装器 00477770: test byte [esp+8],1 + call 0x7C8B3D + ret 4） | 007BA596 / 007BA590 | reg |
| 006F3330 | 改取类一致表后选真构造器 006F3130/006F2B40，非最低地址析构器 006F450D | 006F3130 / 006F2B40 | ctor_body |
| 006FC0B0 | 改取类一致表后选真构造器 006F3130/006F2B40，非最低地址析构器 006F450D | 006F3130 / 006F2B40 | ctor_body |
| 006FCDB0 | 改取类一致表后选真构造器 006F3130/006F2B40，非最低地址析构器 006F450D | 006F3130 / 006F2B40 | ctor_body |
| 007730F0 | 决定性 00771E77 已验真构造器；007730F7 为 entry 体内 scalar-deleting dtor 弃用 | 00771E77 / 00771C70 | ctor_body |

## 5. 六项字节复核 + 宿主身份复核
11 行回 `gamemd.exe`（只读）复算六项：① `u32(vt+slot*4)==entry` ② COL sig==0 ③ COL offset==0 ④ TD/mangled 以 `.?A` 开头 ⑤ 装表点在 entry 体外 ⑥ vt 取得。
**11/11 × 6 项全 True**（all_chk6=True）；vt 取得行数 = 11/11；宿主身份校验（ctor_body 写 this@disp0 且真构造器无删除签名 / mov_abs 目标在 .data / reg 写 this 且宿主析构器）11/11 通过（all_hv=True）。

## 6. 行行不同自检（entry 归一后）
| 检查 | 结果 |
|---|---|
| 完整 ④ 正文 set() | 11/11 不同 |
| 8 位十六进制归一为 ENTRY 后 set() | 11/11 不同 |

## 7. 字节复核与哈希
| 项 | 值 |
|---|---|
| coverage.tsv 读入字节数 | 4097787 |
| coverage.tsv sha256（未改） | `412ED7E36BC1AD4907763FEBB3A68D5FDABB3F0D2C999800444B57098B1AB2E1` |
| gamemd.exe sha256（未改，只读打开） | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` |
| 第 4 列严格前缀自检 | True |
| 第 1/2/3/5/6/7/8 列逐字节相同 | True |

## 8. 样例 ④（mov_abs / ctor_body 各一）

- **mov_abs** `006CF430`（SwizzleManagerClass::slot0）：
  ```
④ 活表槽位见证：SwizzleManagerClass::slot0（vt=007F4108，槽 0 值=006CF430，COL=0080B730 offset=0，RTTI=00842730→.?AVSwizzleManagerClass@@；装表点 006CF0C8 位于 006CF070 体内，装配方式=mov_abs（mov [绝对地址], vt（绝对地址在 .data）；实测指令 mov dword ptr [0xb0c110], 0x7f4108），entry 体外） ④升级句：SwizzleManagerClass::slot0（④ 表属类与行名类一致，均为 SwizzleManagerClass；该槽即其 vt=007F4108 表 slot0，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```

- **ctor_body** `006C6680`（StaticButtonClass::slot33）：
  ```
④ 活表槽位见证：StaticButtonClass::slot33（vt=007F3EA0，槽 33 值=006C6680，COL=0080B478 offset=0，RTTI=00841F10→.?AVStaticButtonClass@@；装表点 006C6588 位于 006C6540 体内，装配方式=ctor_body（构造器体内 mov [reg], vt（写 this，宿主真构造器/工厂、无删除签名）；实测指令 mov dword ptr [esi], 0x7f3ea0），entry 体外） ④升级句：StaticButtonClass::slot33（④ 表属类与行名类一致，均为 StaticButtonClass；该槽即其 vt=007F3EA0 表 slot33，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```

## 9. 清单异常披露
卡面 §2 要求直接用筛手清单、不重筛；本批未发现明显不该在清单内的行。`005F4B10` 已由 Lead 裁定从集合剔除（在 B3），本执行器未触碰。

## 10. 产物清单
- `delta.tsv`（11 净新增行） / `fields.tsv`（11 行） / `REPORT.md` / `raw_dump.json` / `derive.py`（本生成脚本）

**只补 ④ 成文、未改 grade/判定、未并表。**
