# R16-MERGE-SLOTN-B2 · 并表日志

> 角色：合并员（本轮 `coverage.tsv` 与 `PANEL.md` 的唯一写者）
> 写域：`COVERAGE/coverage.tsv`（仅 15 行第 4 列）+ `COVERAGE/PANEL.md`（仅插入 1 条 M87 披露）+ 本产物目录。其余只读。
> 日期：2026-11-20（R16 第 6 轮）· 15 行

## 1 · 改前 / 改后文件状态

| 文件 | 阶段 | 字节 | sha256 | mtime(local) | LF/CRLF |
|---|---|---:|---|---|---|
| coverage.tsv | BEFORE | 4026555 | `c269720f59c07845250a81ca8c6562f62260c1c9ecfc99f160e72f80f58144a5` | 2026-11-20T23:15:29.333330+08:00 | 18498/0 |
| coverage.tsv | AFTER | 4034144 | `0046bad980e9055af61cc94db9da72c5346e087a49a00ba0009705807aa6acf9` | 2026-11-20T23:30:33.477506+08:00 | 18498/0 |
| PANEL.md | BEFORE | 164406 | `b6751c9b1452f607b5a258cb8d6500694c9ccf6a36710f8b767990d11bf66e5a` | 2026-11-20T23:20:12.847712+08:00 | 609/0 |
| PANEL.md | AFTER | 166404 | `946a8eb2c98de0c5e3704d2a86d9366b107b3f86aa73fcd258bf4b0ebef48d4f` | 2026-11-20T23:30:33.479023+08:00 | 616/0 |

## 2 · 指针规范化留痕（Lead 口径：并表环节统一规范化）

- 替换模式：`R14_COMMON §12.4` → `R14_COMMON §12.6`（两字符替换）。
- **替换发生次数：15 处**（15 行各 1 处，均在追加段内）。
- **替换后 `coverage.tsv` 内 `§12.6` 命中：30 行**（改前 15 行 = 批次 1 已入库的 15 entry，改后 30 行 = 批次 1 + 批次 2）。
- 改后 `coverage.tsv` 内 `§12.4` 命中：**0**（改前亦为 0；`R14_COMMON.md` 那边不受影响）。
- 这是流程规范化，取证未重做；异族审计 §A/§B/§C/§E/§F 全部独立复算通过，唯一 FAIL 原因即此指针编号过时。

## 3 · 3.1 节实测四数（不许推算，全部从盘上现算）

| 量 | 实测值 | 说明 |
|---|---:|---|
| N_pre（15 行改前已含字符 ④） | 6 | 改前第 4 列已在「合同闭合 ③b④」标签里含 ④，改后计数不增 |
| N_A_pre（口径 A 改前） | 328 | `[已证]` 且第 4 列含字符 ④ |
| N_A_post（口径 A 改后） | 337 | 净增 9（不是 +15；15 − N_pre = 9） |
| N_B_pre（口径 B 改前） | 106 | `[已证]` 且第 4 列含 `④ 活表槽位见证` |
| N_B_post（口径 B 改后） | 121 | 净增 15（15 行全部新增见证段） |

> 口径 A 判据：`MERGE_M79/verify.py:159` = `grade == "[已证]" and "④" in col4`。
> 口径 B 判据：`grade == "[已证]" and "④ 活表槽位见证" in col4`。
> 四数均由 `verify.py` 从 `coverage.before.bak` 与当前 `coverage.tsv` 字节现算，不引用任何预测值。

## 4 · 9 项验证（逐项 PASS/FAIL）

| # | 项 | 结果 | 关键实测 |
|---|---|---|---|
| 1 | 逐字节还原性(coverage) | **PASS** | restore sha8=c269720f / before sha8=c269720f，重建字节==备份 |
| 2 | 不变量 | **PASS** | 18,498 / {8:18498} / 1,654 / 1,648 / 6 / 15 行 grade 仍 [已证] |
| 3 | 只有 15 行第 4 列变 | **PASS** | 差异行 15，entry 全匹配=True，每行仅第4列=True |
| 4 | 严格前缀 | **PASS** | 15/15 |
| 5 | 口径 A/B 四数 | **PASS** | A 328->337, B 106->121, N_pre=6 |
| 6 | §12.6 替换/命中 | **PASS** | 替换 15 处，§12.6 命中 30 行，§12.4 命中 0 |
| 7 | PANEL.md 还原性 | **PASS** | 删 M87 块后 sha8=b6751c9b / before sha8=b6751c9b，字节==备份 |
| 8 | 达标未翻转 | **PASS** | 名义=S15,S16,S17，严格=S17，rc=0 |
| 9 | 行尾 | **PASS** | cov CRLF=0/LF=18498，pan CRLF=0/LF=616，无混用 |

**合计 PASS 9/9。**

## 5 · strict_panel 复算（达标未翻转）

- 脚本：`strict_panel_local.py (copy; only OUT redirected to own dir)`；输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_MERGE_SLOTN_B2\strict_out`（严格输出到自己的目录）。
- 名义达标：**S15,S16,S17**（期望 S15,S16,S17）；严格达标：**S17**（期望 S17）；returncode=0。

## 6 · 15 行第 4 列 before / after

> 每行原第 4 列为新第 4 列的严格前缀；其余 7 列逐字节相同。下表 before 为改前原值（截断显示尾部追加段），after 为规范化入库值。

| entry | before 第4列(末尾 60 字) | after 第4列(末尾 60 字) | 改前已含④ |
|---|---|---|---|
| `004D4CB0` | …70D0D0(0xE)；三出口 0x4D4D39/0x4D4D26/0x4D4D86 互斥，尾 0x65C7E0 随机。` | …(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）` | 否 |
| `004D4DC0` | …llAt) → vt[+0x480] 链，随后 byte[+0x68E] 分流；全函数 170 指令 13 处 jcc。` | …(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）` | 否 |
| `004D5070` | …0x158 状态位、0x89F688 坐标表、0x5657A0 取格、0x47C520 校验，inc/cmp 推进边界。` | …(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）` | 是 |
| `004D5350` | …C3] 状态位；各路 vt[+0x480]/vt[+0x1E8]/vt[+0x200]/vt[+0x1EC] 结局互斥。` | …(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）` | 否 |
| `004D6AA0` | …89F688 坐标表、0x5657A0 取格、0x47C520 校验，inc/cmp 推进；尾 0x65C7E0 随机。` | …(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）` | 是 |
| `004D9290` | …x58C 表按 +0x598 计数逐项 inc/cmp/jl 推进；动作走 vt[+0x480]，越界失败有可证伪返回。` | …(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）` | 是 |
| `004DA2C0` | …+0xBC=1、态 1 在 0x4DA2E6 写 +0xBC=0，各态动作链经 +0x5A4/+0x5D4 门控而不同。` | …(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）` | 否 |
| `004DDF90` | …0x4DDFA9(态1)调 vt[+0x1E8]/vt[+0x1EC]；+0x2B4 目标存在为另一道闸，两路动作互斥。` | …(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）` | 否 |
| `0051F3E0` | … byte[+0x1577] 与 byte[+0x1701]；通过后 vt[+0x480]/vt[+0x1E8] 动作。` | …(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）` | 否 |
| `0053C6A0` | … span=6 逐元素读旧缓冲写新缓冲并 cmp 推进，完成 SetCapacity 的搬迁；③b④ 完整循环 I/O。` | …(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）` | 是 |
| `005514B0` | …FE span=6 读旧数组写新数组并 cmp 推进，实现 SetCapacity 扩容搬迁；③b④ 完整循环 I/O。` | …(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）` | 是 |
| `00551560` | …查找 slot4：线性查找循环逐项 cmp 命中返回索引，未命中 or eax,-1；-1 哨兵返回约定可证伪，③b②。` | …(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）` | 否 |
| `00557090` | …x5570DE span=6 读旧缓冲写新缓冲并 cmp 推进，完成 SetCapacity；③b④ 完整循环 I/O。` | …(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）` | 是 |
| `00557140` | …> 查找 slot4：线性查找循环逐项 cmp 命中返回索引，未命中 or eax,-1；-1 哨兵返回可证伪，③b②。` | …(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）` | 否 |
| `005B2FD0` | …3021/0x5B302A 处自 +0xC8 写帧戳/参数/清零；时间戳取 0xA8ED84，字段组固定即内存形状断言。` | …(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）` | 否 |

### 6.1 完整新增段（after 相对 before 的追加部分，含 §12.6）

- `004D4CB0`：
  ```
  ；④ 活表槽位见证：AircraftClass::slot134（vt=007E22A4，槽 134 值=004D4CB0，COL=007FB4C0 offset=0，RTTI=00817B90→.?AVAircraftClass@@；装表点 00413D87 位于 00413D20 体内，entry 体外） ④升级句：AircraftClass::slot134（④ 表属类与行名类一致，均为 AircraftClass；该槽即其 vt=007E22A4 表 slot134，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- `004D4DC0`：
  ```
  ；④ 活表槽位见证：FootClass::slot132（vt=007E8C94，槽 132 值=004D4DC0，COL=00800948 offset=0，RTTI=00817B78→.?AVFootClass@@；装表点 004D345D 位于 004D31E0 体内，entry 体外） ④升级句：FootClass::slot132（④ 表属类与行名类一致，均为 FootClass；该槽即其 vt=007E8C94 表 slot132，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- `004D5070`：
  ```
  ；④ 活表槽位见证：FootClass::slot135（vt=007E8C94，槽 135 值=004D5070，COL=00800948 offset=0，RTTI=00817B78→.?AVFootClass@@；装表点 004D345D 位于 004D31E0 体内，entry 体外） ④升级句：FootClass::slot135（④ 表属类与行名类一致，均为 FootClass；该槽即其 vt=007E8C94 表 slot135，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- `004D5350`：
  ```
  ；④ 活表槽位见证：FootClass::slot138（vt=007E8C94，槽 138 值=004D5350，COL=00800948 offset=0，RTTI=00817B78→.?AVFootClass@@；装表点 004D345D 位于 004D31E0 体内，entry 体外） ④升级句：FootClass::slot138（④ 表属类与行名类一致，均为 FootClass；该槽即其 vt=007E8C94 表 slot138，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- `004D6AA0`：
  ```
  ；④ 活表槽位见证：FootClass::slot136（vt=007E8C94，槽 136 值=004D6AA0，COL=00800948 offset=0，RTTI=00817B78→.?AVFootClass@@；装表点 004D345D 位于 004D31E0 体内，entry 体外） ④升级句：FootClass::slot136（④ 表属类与行名类一致，均为 FootClass；该槽即其 vt=007E8C94 表 slot136，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- `004D9290`：
  ```
  ；④ 活表槽位见证：FootClass::slot144（vt=007E8C94，槽 144 值=004D9290，COL=00800948 offset=0，RTTI=00817B78→.?AVFootClass@@；装表点 004D345D 位于 004D31E0 体内，entry 体外） ④升级句：FootClass::slot144（④ 表属类与行名类一致，均为 FootClass；该槽即其 vt=007E8C94 表 slot144，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- `004DA2C0`：
  ```
  ；④ 活表槽位见证：FootClass::slot140（vt=007E8C94，槽 140 值=004DA2C0，COL=00800948 offset=0，RTTI=00817B78→.?AVFootClass@@；装表点 004D345D 位于 004D31E0 体内，entry 体外） ④升级句：FootClass::slot140（④ 表属类与行名类一致，均为 FootClass；该槽即其 vt=007E8C94 表 slot140，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- `004DDF90`：
  ```
  ；④ 活表槽位见证：AircraftClass::slot150（vt=007E22A4，槽 150 值=004DDF90，COL=007FB4C0 offset=0，RTTI=00817B90→.?AVAircraftClass@@；装表点 00413D87 位于 00413D20 体内，entry 体外） ④升级句：AircraftClass::slot150（④ 表属类与行名类一致，均为 AircraftClass；该槽即其 vt=007E22A4 表 slot150，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- `0051F3E0`：
  ```
  ；④ 活表槽位见证：InfantryClass::slot132（vt=007EB058，槽 132 值=0051F3E0，COL=008033B8 offset=0，RTTI=00825508→.?AVInfantryClass@@；装表点 00517ACC 位于 00517A50 体内，entry 体外） ④升级句：InfantryClass::slot132（④ 表属类与行名类一致，均为 InfantryClass；该槽即其 vt=007EB058 表 slot132，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- `0053C6A0`：
  ```
  ；④ 活表槽位见证：T_DynamicVectorClass_PBVAnimClass__::slot2（vt=007EBFCC，槽 2 值=0053C6A0，COL=008047B8 offset=0，RTTI=00828000→.?AV?$DynamicVectorClass@PBVAnimClass@@@@；装表点 0053959D 位于 00539580 体内，entry 体外） ④升级句：T_DynamicVectorClass_PBVAnimClass__::slot2（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PBVAnimClass__；该槽即其 vt=007EBFCC 表 slot2，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- `005514B0`：
  ```
  ；④ 活表槽位见证：T_DynamicVectorClass_PAVLaserDrawClass__::slot2（vt=007ECEDC，槽 2 值=005514B0，COL=00804DF0 offset=0，RTTI=00829710→.?AV?$DynamicVectorClass@PAVLaserDrawClass@@@@；装表点 0054FDDD 位于 0054FDC0 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVLaserDrawClass__::slot2（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVLaserDrawClass__；该槽即其 vt=007ECEDC 表 slot2，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- `00551560`：
  ```
  ；④ 活表槽位见证：T_DynamicVectorClass_PAVLaserDrawClass__::slot4（vt=007ECEDC，槽 4 值=00551560，COL=00804DF0 offset=0，RTTI=00829710→.?AV?$DynamicVectorClass@PAVLaserDrawClass@@@@；装表点 0054FDDD 位于 0054FDC0 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVLaserDrawClass__::slot4（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVLaserDrawClass__；该槽即其 vt=007ECEDC 表 slot4，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- `00557090`：
  ```
  ；④ 活表槽位见证：T_DynamicVectorClass_PAVLineTrail__::slot2（vt=007ED0CC，槽 2 值=00557090，COL=008051A8 offset=0，RTTI=00829D78→.?AV?$DynamicVectorClass@PAVLineTrail@@@@；装表点 005569BD 位于 005569A0 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVLineTrail__::slot2（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVLineTrail__；该槽即其 vt=007ED0CC 表 slot2，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- `00557140`：
  ```
  ；④ 活表槽位见证：T_DynamicVectorClass_PAVLineTrail__::slot4（vt=007ED0CC，槽 4 值=00557140，COL=008051A8 offset=0，RTTI=00829D78→.?AV?$DynamicVectorClass@PAVLineTrail@@@@；装表点 005569BD 位于 005569A0 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVLineTrail__::slot4（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVLineTrail__；该槽即其 vt=007ED0CC 表 slot4，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- `005B2FD0`：
  ```
  ；④ 活表槽位见证：InfantryClass::slot124（vt=007EB058，槽 124 值=005B2FD0，COL=008033B8 offset=0，RTTI=00825508→.?AVInfantryClass@@；装表点 00517D9D 位于 00517D90 体内，entry 体外） ④升级句：InfantryClass::slot124（④ 表属类与行名类一致，均为 InfantryClass；该槽即其 vt=007EB058 表 slot124，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```

## 7 · 边界自证

- 只改 `coverage.tsv` 这 15 行的第 4 列；其它行、其它列一律未动（V1/V3）。
- 不改 grade、不改判定、不改行序、不增删行（V2/V3）。
- `PANEL.md` 只做一件新增：插入 1 条 M87 披露；既有内容零删除零改字（V7）。
- 未改 `R14_COMMON.md`、台账、看板、`_drafts\`、`_cards\`、任何卡目录；`R16_SLOTN_B2\` 与 `R16_AUDIT_SLOTN_B2\` 全程只读。
- 未做逆向；`strict_panel.py` 仅复制并把 OUT 重定向到本产物目录。
