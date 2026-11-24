# R16-D1-FINAL 执行报告 —— 静态 ④ 线收官批

> 角色：执行器 `work/cn:hy4flash-free` · 日期 2026-11-21（R16 第 19 轮）
> 写域：`lead\next_re_20261117_r14\R16_D1_FINAL\`（仅此目录）；**未写 `COVERAGE\coverage.tsv`**；`gamemd.exe` 仅 `open('rb')` 只读打开。
> 披露指针：每行 ④ 自带 D-47 披露并指向 **§12.6**（`见 R14_COMMON §12.6 与 PANEL 对应披露`）。

## 0. 一句话结论
**只补第 4 列 ④ 成文、未改 grade/判定、未并表。** 派生 17 行（F1 12 + F2 5）与探针一致；
其中 12 行改前 live 第4列已含 ④（`R16_F1_OTHER14` 于 09:11 已并表），本卡不重复追加；
5 行净新增 ④ 写入 `delta.tsv`。本批是**静态 ④ 线收官批**。

## 1. 四阶段派生计数（含与 17 的差异说明）
| 阶段 | 实测 | 卡面预期 | 结论 |
|---|---:|---:|---|
| 1 D1 集合（final.tsv `has_ring4==D1`）| 317 | 317 | 一致 |
| 2 来源类别 join（F1/F2/F3/F4）| F1=12 F2=5 F3=1 F4=299 | — | F1/F2 合计 17 |
| 3 口径二筛（② 有独立审计链，排除 YRpp 代理）| 17 | 17 | 一致 |
| 4 盘态复核（live coverage 改前含 ④）| 12 已含 / 5 净新增 | — | delta 只放净新增 |

与 17 的差异：**派生数完全等于 17，无差异**；差异只在『盘态』——12 行 F1 已被并行卡 `R16_F1_OTHER14` 写入并表，
故本卡 delta 只有 5 行净新增。若不复核盘态而照抄 17 行，会对那 12 行重复追加 ④。

## 2. 每行 ② 的审计记录出处
| entry | name | source_class | ② 审计记录 | ring2 独立 |
|---|---|---|---|---|
| 0040BC10 | DynamicVectorClass<BombClass*>::scalar_deleting_dtor | F1 | `S13_K8RECHK/_audit/VERDICT.md:37` | 是 |
| 0040F8F0 | DynamicVectorClass<WarheadTypeClass*>::scalar_deleting_dtor | F1 | `S13_K8RECHK/_audit/VERDICT.md:37` | 是 |
| 0040FEC0 | DynamicVectorClass<WeaponTypeClass*>::scalar_deleting_dtor | F1 | `S13_K8RECHK/_audit/VERDICT.md:37` | 是 |
| 00422CA0 | AnimClass::Draw | F1 | `S20-K1/EVIDENCE/T4_vtable_slots.tsv:71` | 是 |
| 0046B910 | DynamicVectorClass<BulletClass*>::scalar_deleting_dtor | F1 | `S13_K8RECHK/_audit/VERDICT.md:37` | 是 |
| 0048AFD0 | VectorClass<DamageGroup*>::scalar_deleting_dtor | F1 | `S13_K8RECHK/_audit/VERDICT.md:37` | 是 |
| 0048B020 | DynamicVectorClass<DamageGroup*>::scalar_deleting_dtor | F1 | `S13_K8RECHK/_audit/VERDICT.md:37` | 是 |
| 0054EBA0 | DynamicVectorClass<KamikazeControl*>::scalar_deleting_dtor | F1 | `S13_K8RECHK/_audit/VERDICT.md:37` | 是 |
| 0062B380 | DynamicVectorClass<ParasiteClass*>::scalar_deleting_dtor | F1 | `S13_K8RECHK/_audit/VERDICT.md:37` | 是 |
| 0065BED0 | RadSiteClass::scalar_deleting_dtor | F1 | `S13_K8RECHK/_audit/VERDICT.md:37` | 是 |
| 0065C200 | DynamicVectorClass<RadSiteClass*>::scalar_deleting_dtor | F1 | `S13_K8RECHK/_audit/VERDICT.md:37` | 是 |
| 0075E510 | WarheadTypeClass::scalar_deleting_dtor | F1 | `S13_K8RECHK/_audit/VERDICT.md:37` | 是 |
| 0051B1F0 | InfantryClass::RetargetWithMissionFallback_behavior | F2 | `S10_K12/EVIDENCE/ROW_PROOFS.txt:67` | 是 |
| 0051DAF0 | InfantryClass::StopAfterAirborneMissionState_behavior | F2 | `S10_K12/EVIDENCE/ROW_PROOFS.txt:52` | 是 |
| 00522340 | InfantryClass::ApplyOccupantTargetMissionFallback_behavior | F2 | `S10_K12/EVIDENCE/ROW_PROOFS.txt:109` | 是 |
| 0070B570 | TechnoClass::ClampAndAdvancePairedFloatState_behavior | F2 | `S10_K16/EVIDENCE/PROOF_0070B570.txt:9` | 是 |
| 00748190 | UnitTypeClass::slot8 | F2 | `NAMED_PUSH_AUDIT3/verdict.tsv:2` | 是 |

## 3. 装配形态分类计数（17 行全量）
| install_form | 行数 |
|---|---:|
| ctor_body | 10 |
| mov_abs | 7 |
| reg | 0 |
| other | 0 |

净新增 5 行的形态：{'ctor_body': 5}

## 4. 六项字节复核结果
17 行逐行回 `gamemd.exe`（只读）复算 6 项：① `u32(vt+slot*4)==entry` ② COL sig==0 ③ COL offset==0 
④ `TD=u32(COL+12)`、`cstr(TD+8)` 以 `.?A` 开头 ⑤ 装表点在 entry 体外 ⑥ vt 取得。
**17/17 × 6 项全 True**（all_chk6=True）。

## 5. 行行不同自检（entry 归一后）
| 检查 | 结果 |
|---|---|
| 完整 ④ 正文 set() | 17/17 不同 |
| 8 位十六进制归一为 ENTRY 后 set() | 17/17 不同 |

## 6. 字节复核与哈希
| 项 | 值 |
|---|---|
| coverage.tsv 读入字节数 | 4095388 |
| coverage.tsv sha256（未改）| `E4F111B6643661D01C66DB1889172437A06A563233F0A252AD0DB4A54FD51C8A` |
| gamemd.exe sha256（未改，只读打开）| `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` |
| pin coverage sha256 | `2F498B18E64E7EF568A0EB7888CE9F8D710CABC91038E52A8167F8826B53B36E` |

## 7. 样例 ④（ctor_body / mov_abs 各一）

- **ctor_body（ctor 实例装表 reg，净新增）** `0051B1F0`：
  ```
④ 活表槽位见证：InfantryClass::slot242（vt=007EB058，槽 242 值=0051B1F0，COL=008033B8 offset=0，RTTI=00825508→.?AVInfantryClass@@；装表点 00517ACC 位于 00517A50 体内，entry 体外） ④升级句：InfantryClass::slot242（④ 表属类与行名类一致，均为 InfantryClass；该槽即其 vt=007EB058 表 slot242，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- **mov_abs（绝对地址装表，已由 R16_F1_OTHER14 并表）** `0040BC10`：
  ```
④ 活表槽位见证：DynamicVectorClass<BombClass*>::slot0（vt=007E17CC，槽 0 值=0040BC10，COL=007FA6A8 offset=0，RTTI=00816918→.?AV?$DynamicVectorClass@PAVBombClass@@@@；装表点 0040B563 位于 0040B540 体内，装表指令为 mov [abs], vt，entry 体外） ④升级句：DynamicVectorClass<BombClass*>::slot0（④ 表属类与行名类一致，均为 DynamicVectorClass<BombClass*>；该槽即其 vt=007E17CC 表 slot0，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```

## 8. 产物清单
- `derive.txt` / `delta.tsv`（5 净新增行）/ `fields.tsv`（17 行）/ `REPORT.md` / `generate.py`

**本批是静态 ④ 线收官批。**
