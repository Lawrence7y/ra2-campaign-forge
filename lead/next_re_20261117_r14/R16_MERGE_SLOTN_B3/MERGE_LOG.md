# R16-MERGE-SLOTN-B3 · MERGE_LOG

> 角色：合并员（`work/cn:hy4flash-free`）—— 本轮 `coverage.tsv` 与 `PANEL.md` 的唯一写者
> 输入：`R16_SLOTN_B3/delta.tsv`（13 行）+ `R16_AUDIT_SLOTN_B3/VERDICT.md`（13 PASS / 0 FAIL / 0 必改；指针 13/13 已是 §12.6，本批无需规范化）
> 硬边界：只改 coverage.tsv 这 13 行第 4 列；PANEL.md 只插入 1 条 M88 披露，既有内容零删除零改字；不改 R14_COMMON/台账/看板/_drafts/_cards；卡目录只读；不做逆向。

## 1. 改前 → 改后（盘上实测）

| 文件 | mtime(本地) | 字节 | sha256 | 行数(LF) | 行尾 |
|---|---|---:|---|---:|---|
| coverage 改前 | 2026-11-20T23:30:33.477506+08:00 | 4034144 | 0046bad980e9055af61cc94db9da72c5346e087a49a00ba0009705807aa6acf9 | 18498 | CRLF=0 LF=18498 CR=0 BOM=False ends_nl=False |
| coverage 改后 | 2026-11-20T23:40:24.841258+08:00 | 4040803 | 95dfac9e6cec2d464691d84df1ef64a0ad850c86500a4cd1348275f0fbc419d1 | 18498 | CRLF=0 LF=18498 CR=0 BOM=False ends_nl=False |
| panel 改前 | 2026-11-20T23:30:33.479023+08:00 | 166404 | 946a8eb2c98de0c5e3704d2a86d9366b107b3f86aa73fcd258bf4b0ebef48d4f | 616 | CRLF=0 LF=616 CR=0 BOM=False ends_nl=True |
| panel 改后 | 2026-11-20T23:40:24.843768+08:00 | 168444 | 3e495b02327e2ab6e454a1941f64c31cb107ffe805225b3a74ccf4bd45ec9799 | 624 | CRLF=0 LF=624 CR=0 BOM=False ends_nl=True |

- 两份文件改前均为 **纯 LF、无 BOM**；改后行尾形态未变、未引入混用（V9）。
- 改前基线不变量（自算）：数据行 18,498 / 列分布 {8:18498} / `[已证]` 1,654 / atlas 内 1,648 / atlas 外 6 —— 与卡面 §2 一致；改后须仍成立（V2）。

## 2. 口径 A/B 五个实测数（卡面 §2.1，绝不照抄预测或旧值）

| 量 | 实测值 | 说明 |
|---|---:|---|
| `N_pre` | 3 | 13 行里改前第 4 列已含字符 `④` 的行数（`006B1850`、`006B8660`、`006F9E50`） |
| `N_A_pre` → `N_A_post` | 337 → 347 | 全表口径 A（`[已证]` 且第 4 列含字符 `④`），净增 +10 |
| `N_B_pre` → `N_B_post` | 121 → 134 | 全表口径 B（`[已证]` 且第 4 列含 `④ 活表槽位见证`），净增 +13 |

- 口径 A 判据原文：`MERGE_M79/verify.py:159` → `sum(1 for r in rows if r[4].strip()=='[已证]' and '④' in r[3])`；口径 B：第 4 列含子串 `④ 活表槽位见证`。
- 五个数改前从 `coverage.before.bak` 字节现算、改后从当前 `coverage.tsv` 字节现算；`N_pre=3` 的 3 行均为「合同闭合 ③b④」分类标签里已有 `④`，故 A 净增 = 13 − 3 = 10（非 +13），B 净增 = 13。
- M88 披露里的所有数字即本节实测值。

## 3. 13 行第 4 列 before → after

> 严格前缀 13/13；其余第 1/2/3/5/6/7/8 列逐字节相同；13 行 grade 改前改后均 `[已证]`。

### 1. `005B3060` MissionClass::slot23
- BEFORE 第 4 列：
  ```text
  任务主分派器：按当前任务号经跳表调用对应处理虚方法并刷新帧时间戳。合同闭合 ③b① 跳表可核：0x5B30B8 处 cmp eax,0x1F 上界守卫、0x5B30C1 处 jmp [eax*4+0x5B34E8]；表 0x5B34E8 共 32 槽、目标全在 .text，各 case 调 vt[+0x204] 等虚方法，时戳统一取 0xA8ED84。
  ```
- AFTER 第 4 列：
  ```text
  任务主分派器：按当前任务号经跳表调用对应处理虚方法并刷新帧时间戳。合同闭合 ③b① 跳表可核：0x5B30B8 处 cmp eax,0x1F 上界守卫、0x5B30C1 处 jmp [eax*4+0x5B34E8]；表 0x5B34E8 共 32 槽、目标全在 .text，各 case 调 vt[+0x204] 等虚方法，时戳统一取 0xA8ED84。；④ 活表槽位见证：MissionClass::slot23（vt=007EDCC0，槽 23 值=005B3060，COL=00805D28 offset=0，RTTI=00817B18→.?AVMissionClass@@；装表点 005B2DE9 位于 005B2DA0 体内，entry 体外） ④升级句：MissionClass::slot23（④ 表属类与行名类一致，均为 MissionClass；该槽即其 vt=007EDCC0 表 slot23，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- 追加段（475 B）：`；④ 活表槽位见证：MissionClass::slot23（vt=007EDCC0，槽 23 值=005B3060，COL=00805D28 offset=0，RTTI=00817B18→.?AVMissionClass@@；装表点 005B2DE9 位于 005B2DA0 体内，entry 体外） ④升级句：MissionClass::slot23（④ 表属类与行名类一致，均为 MissionClass；该槽即其 vt=007EDCC0 表 slot23，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段内 `§12.6` 命中 1 / `§12.4` 命中 0；改前已含 `④`=False、已含 `④ 活表槽位见证`=False。

### 2. `005B3570` InfantryClass::slot123
- BEFORE 第 4 列：
  ```text
  排队任务出列转当前任务：把 +0xB4 排队任务搬到 +0xAC，清排队位并刷新时间戳；无排队则可证伪返回。合同闭合 ③b① 状态转移+返回：0x5B3579 处 cmp eax,-1 / je 0x5B35CC 为可证伪空返回；非空分支写 +0xAC、+0xB4=-1、+0xB8、+0xBC、+0xC0/+0xC4，并自 +0xC8 写帧戳三字段(取 0xA8ED84)。
  ```
- AFTER 第 4 列：
  ```text
  排队任务出列转当前任务：把 +0xB4 排队任务搬到 +0xAC，清排队位并刷新时间戳；无排队则可证伪返回。合同闭合 ③b① 状态转移+返回：0x5B3579 处 cmp eax,-1 / je 0x5B35CC 为可证伪空返回；非空分支写 +0xAC、+0xB4=-1、+0xB8、+0xBC、+0xC0/+0xC4，并自 +0xC8 写帧戳三字段(取 0xA8ED84)。；④ 活表槽位见证：InfantryClass::slot123（vt=007EB058，槽 123 值=005B3570，COL=008033B8 offset=0，RTTI=00825508→.?AVInfantryClass@@；装表点 00517D9D 位于 00517D90 体内，entry 体外） ④升级句：InfantryClass::slot123（④ 表属类与行名类一致，均为 InfantryClass；该槽即其 vt=007EB058 表 slot123，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- 追加段（483 B）：`；④ 活表槽位见证：InfantryClass::slot123（vt=007EB058，槽 123 值=005B3570，COL=008033B8 offset=0，RTTI=00825508→.?AVInfantryClass@@；装表点 00517D9D 位于 00517D90 体内，entry 体外） ④升级句：InfantryClass::slot123（④ 表属类与行名类一致，均为 InfantryClass；该槽即其 vt=007EB058 表 slot123，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段内 `§12.6` 命中 1 / `§12.4` 命中 0；改前已含 `④`=False、已含 `④ 活表槽位见证`=False。

### 3. `005B35E0` InfantryClass::slot122
- BEFORE 第 4 列：
  ```text
  任务排队的多路过滤：态 0x1C+参数 5、态 0x13、参数 -1 三种情况直接跳过，否则写排队槽后按参数字节虚调用分派。合同闭合 ③b① 多路可核：0x5B35ED 处 cmp ecx,0x1C + cmp eax,5、0x5B35F7 处 cmp ecx,0x13、0x5B35FC 处 cmp eax,-1；通过则写 +0xB4/+0xB8，再按 arg 调 vt[+0x200]/vt[+0x1EC]。
  ```
- AFTER 第 4 列：
  ```text
  任务排队的多路过滤：态 0x1C+参数 5、态 0x13、参数 -1 三种情况直接跳过，否则写排队槽后按参数字节虚调用分派。合同闭合 ③b① 多路可核：0x5B35ED 处 cmp ecx,0x1C + cmp eax,5、0x5B35F7 处 cmp ecx,0x13、0x5B35FC 处 cmp eax,-1；通过则写 +0xB4/+0xB8，再按 arg 调 vt[+0x200]/vt[+0x1EC]。；④ 活表槽位见证：InfantryClass::slot122（vt=007EB058，槽 122 值=005B35E0，COL=008033B8 offset=0，RTTI=00825508→.?AVInfantryClass@@；装表点 00521A11 位于 00521960 体内，entry 体外） ④升级句：InfantryClass::slot122（④ 表属类与行名类一致，均为 InfantryClass；该槽即其 vt=007EB058 表 slot122，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- 追加段（483 B）：`；④ 活表槽位见证：InfantryClass::slot122（vt=007EB058，槽 122 值=005B35E0，COL=008033B8 offset=0，RTTI=00825508→.?AVInfantryClass@@；装表点 00521A11 位于 00521960 体内，entry 体外） ④升级句：InfantryClass::slot122（④ 表属类与行名类一致，均为 InfantryClass；该槽即其 vt=007EB058 表 slot122，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段内 `§12.6` 命中 1 / `§12.4` 命中 0；改前已含 `④`=False、已含 `④ 活表槽位见证`=False。

### 4. `005B3650` MissionClass::slot125
- BEFORE 第 4 列：
  ```text
  任务队列三路互斥搬运：态 0x1C+参数 5 或态 0x13 跳过；否则按排队槽是否非空决定 0xB4→0xB0 覆盖当前，或双向交换 0xB0←0xAC/0xAC←arg。合同闭合 ③b① 多路可核：0x5B365B 处 cmp eax,0x1C + cmp esi,5、0x5B3665 处 cmp eax,0x13、0x5B366A 处 cmp edx,-1；三路 ret 0xC 出口互斥。
  ```
- AFTER 第 4 列：
  ```text
  任务队列三路互斥搬运：态 0x1C+参数 5 或态 0x13 跳过；否则按排队槽是否非空决定 0xB4→0xB0 覆盖当前，或双向交换 0xB0←0xAC/0xAC←arg。合同闭合 ③b① 多路可核：0x5B365B 处 cmp eax,0x1C + cmp esi,5、0x5B3665 处 cmp eax,0x13、0x5B366A 处 cmp edx,-1；三路 ret 0xC 出口互斥。；④ 活表槽位见证：MissionClass::slot125（vt=007EDCC0，槽 125 值=005B3650，COL=00805D28 offset=0，RTTI=00817B18→.?AVMissionClass@@；装表点 005B2DE9 位于 005B2DA0 体内，entry 体外） ④升级句：MissionClass::slot125（④ 表属类与行名类一致，均为 MissionClass；该槽即其 vt=007EDCC0 表 slot125，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- 追加段（479 B）：`；④ 活表槽位见证：MissionClass::slot125（vt=007EDCC0，槽 125 值=005B3650，COL=00805D28 offset=0，RTTI=00817B18→.?AVMissionClass@@；装表点 005B2DE9 位于 005B2DA0 体内，entry 体外） ④升级句：MissionClass::slot125（④ 表属类与行名类一致，均为 MissionClass；该槽即其 vt=007EDCC0 表 slot125，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段内 `§12.6` 命中 1 / `§12.4` 命中 0；改前已含 `④`=False、已含 `④ 活表槽位见证`=False。

### 5. `005B36B0` MissionClass::slot126
- BEFORE 第 4 列：
  ```text
  排队任务落地为当前任务的转移：+0xB0 有效则搬到 +0xAC、清空 +0xB0/+0xB8 并 ret al=1，否则 ret al=0。合同闭合 ③b② 可证伪返回约定：0x5B36B6 处 cmp eax,-1 / je 0x5B36D7 为失败出口；成功路径 0x5B36BB/0x5B36C1/0x5B36CB 写 +0xAC、+0xB0=-1、+0xB8=0，al 真值可证伪。
  ```
- AFTER 第 4 列：
  ```text
  排队任务落地为当前任务的转移：+0xB0 有效则搬到 +0xAC、清空 +0xB0/+0xB8 并 ret al=1，否则 ret al=0。合同闭合 ③b② 可证伪返回约定：0x5B36B6 处 cmp eax,-1 / je 0x5B36D7 为失败出口；成功路径 0x5B36BB/0x5B36C1/0x5B36CB 写 +0xAC、+0xB0=-1、+0xB8=0，al 真值可证伪。；④ 活表槽位见证：MissionClass::slot126（vt=007EDCC0，槽 126 值=005B36B0，COL=00805D28 offset=0，RTTI=00817B18→.?AVMissionClass@@；装表点 005B2DE9 位于 005B2DA0 体内，entry 体外） ④升级句：MissionClass::slot126（④ 表属类与行名类一致，均为 MissionClass；该槽即其 vt=007EDCC0 表 slot126，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- 追加段（479 B）：`；④ 活表槽位见证：MissionClass::slot126（vt=007EDCC0，槽 126 值=005B36B0，COL=00805D28 offset=0，RTTI=00817B18→.?AVMissionClass@@；装表点 005B2DE9 位于 005B2DA0 体内，entry 体外） ④升级句：MissionClass::slot126（④ 表属类与行名类一致，均为 MissionClass；该槽即其 vt=007EDCC0 表 slot126，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段内 `§12.6` 命中 1 / `§12.4` 命中 0；改前已含 `④`=False、已含 `④ 活表槽位见证`=False。

### 6. `005B4630` MixFileClass::slot0
- BEFORE 第 4 列：
  ```text
  MixFileClass 析构与资源所有权释放：vt 0x7EDF50 写回，[+0xC] 无条件 free(0x7C93E8/0x7C8B3D)，[+0x24] 仅当 byte[+0x12] 置位才 free 并清标志，[+0x20] free 后清 0；字段级所有权形状可断言，③b③。
  ```
- AFTER 第 4 列：
  ```text
  MixFileClass 析构与资源所有权释放：vt 0x7EDF50 写回，[+0xC] 无条件 free(0x7C93E8/0x7C8B3D)，[+0x24] 仅当 byte[+0x12] 置位才 free 并清标志，[+0x20] free 后清 0；字段级所有权形状可断言，③b③。；④ 活表槽位见证：MixFileClass::slot0（vt=007EDF50，槽 0 值=005B4630，COL=00805DE0 offset=0，RTTI=0082C318→.?AVMixFileClass@@；装表点 005B3C52 位于 005B3C20 体内，entry 体外） ④升级句：MixFileClass::slot0（④ 表属类与行名类一致，均为 MixFileClass；该槽即其 vt=007EDF50 表 slot0，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- 追加段（471 B）：`；④ 活表槽位见证：MixFileClass::slot0（vt=007EDF50，槽 0 值=005B4630，COL=00805DE0 offset=0，RTTI=0082C318→.?AVMixFileClass@@；装表点 005B3C52 位于 005B3C20 体内，entry 体外） ④升级句：MixFileClass::slot0（④ 表属类与行名类一致，均为 MixFileClass；该槽即其 vt=007EDF50 表 slot0，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段内 `§12.6` 命中 1 / `§12.4` 命中 0；改前已含 `④`=False、已含 `④ 活表槽位见证`=False。

### 7. `00653100` RadarClass::slot16
- BEFORE 第 4 列：
  ```text
  RadarClass 雷达命令分派：跳表 0x653734 共 4 槽、cmp bound=3，41 个条件跳转与 15 次调用，各目标均落 .text 可逐路核；③b① 跳表多路分支。
  ```
- AFTER 第 4 列：
  ```text
  RadarClass 雷达命令分派：跳表 0x653734 共 4 槽、cmp bound=3，41 个条件跳转与 15 次调用，各目标均落 .text 可逐路核；③b① 跳表多路分支。；④ 活表槽位见证：RadarClass::slot16（vt=007F0344，槽 16 值=00653100，COL=008083C0 offset=0，RTTI=00816BF8→.?AVRadarClass@@；装表点 00652B45 位于 00652960 体内，entry 体外） ④升级句：RadarClass::slot16（④ 表属类与行名类一致，均为 RadarClass；该槽即其 vt=007F0344 表 slot16，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- 追加段（467 B）：`；④ 活表槽位见证：RadarClass::slot16（vt=007F0344，槽 16 值=00653100，COL=008083C0 offset=0，RTTI=00816BF8→.?AVRadarClass@@；装表点 00652B45 位于 00652960 体内，entry 体外） ④升级句：RadarClass::slot16（④ 表属类与行名类一致，均为 RadarClass；该槽即其 vt=007F0344 表 slot16，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段内 `§12.6` 命中 1 / `§12.4` 命中 0；改前已含 `④`=False、已含 `④ 活表槽位见证`=False。

### 8. `0065CBF0` RawFileClass::slot5
- BEFORE 第 4 列：
  ```text
  RawFileClass 打开状态查询：多出口可证伪——[+0x18]==0 则早退 al=0；vt[+0x18] 为真走 0x65CC94；参数非零经 0x65CB50 后重查 vt[+0x18] 再经 [0x7E11E0]；成功/失败路径互斥，③b② 返回约定。
  ```
- AFTER 第 4 列：
  ```text
  RawFileClass 打开状态查询：多出口可证伪——[+0x18]==0 则早退 al=0；vt[+0x18] 为真走 0x65CC94；参数非零经 0x65CB50 后重查 vt[+0x18] 再经 [0x7E11E0]；成功/失败路径互斥，③b② 返回约定。；④ 活表槽位见证：RawFileClass::slot5（vt=007F0904，槽 5 值=0065CBF0，COL=00808790 offset=0，RTTI=00815DF8→.?AVRawFileClass@@；装表点 0065CA03 位于 0065CA00 体内，entry 体外） ④升级句：RawFileClass::slot5（④ 表属类与行名类一致，均为 RawFileClass；该槽即其 vt=007F0904 表 slot5，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- 追加段（471 B）：`；④ 活表槽位见证：RawFileClass::slot5（vt=007F0904，槽 5 值=0065CBF0，COL=00808790 offset=0，RTTI=00815DF8→.?AVRawFileClass@@；装表点 0065CA03 位于 0065CA00 体内，entry 体外） ④升级句：RawFileClass::slot5（④ 表属类与行名类一致，均为 RawFileClass；该槽即其 vt=007F0904 表 slot5，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段内 `§12.6` 命中 1 / `§12.4` 命中 0；改前已含 `④`=False、已含 `④ 活表槽位见证`=False。

### 9. `006B1850` T_DynamicVectorClass_PAVSlaveManagerClass__::slot2
- BEFORE 第 4 列：
  ```text
  SlaveManager 指针动态数组 SetCapacity：分配后备缓冲、逐元素拷贝旧数组、按需释放旧缓冲并改挂 Items/Count。合同闭合 ③b④ 完整循环 I/O：0x6B189E 处 mov edx,[esi+4]/inc eax/mov [edi+eax*4-4],edx/jl 回边读-写-推进齐备；0x7C8E17 分配、0x7C8B3D 释放，ret8。
  ```
- AFTER 第 4 列：
  ```text
  SlaveManager 指针动态数组 SetCapacity：分配后备缓冲、逐元素拷贝旧数组、按需释放旧缓冲并改挂 Items/Count。合同闭合 ③b④ 完整循环 I/O：0x6B189E 处 mov edx,[esi+4]/inc eax/mov [edi+eax*4-4],edx/jl 回边读-写-推进齐备；0x7C8E17 分配、0x7C8B3D 释放，ret8。；④ 活表槽位见证：T_DynamicVectorClass_PAVSlaveManagerClass__::slot2（vt=007F315C，槽 2 值=006B1850，COL=00809620 offset=0，RTTI=0083FCD0→.?AV?$DynamicVectorClass@PAVSlaveManagerClass@@@@；装表点 006AF13D 位于 006AF120 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVSlaveManagerClass__::slot2（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVSlaveManagerClass__；该槽即其 vt=007F315C 表 slot2，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- 追加段（595 B）：`；④ 活表槽位见证：T_DynamicVectorClass_PAVSlaveManagerClass__::slot2（vt=007F315C，槽 2 值=006B1850，COL=00809620 offset=0，RTTI=0083FCD0→.?AV?$DynamicVectorClass@PAVSlaveManagerClass@@@@；装表点 006AF13D 位于 006AF120 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVSlaveManagerClass__::slot2（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVSlaveManagerClass__；该槽即其 vt=007F315C 表 slot2，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段内 `§12.6` 命中 1 / `§12.4` 命中 0；改前已含 `④`=True、已含 `④ 活表槽位见证`=False。

### 10. `006B1900` T_DynamicVectorClass_PAVSlaveManagerClass__::slot4
- BEFORE 第 4 列：
  ```text
  SlaveManager 指针动态数组 FindItemIndex：按指针线性扫描至 Count，命中返回下标、未命中 -1(ret4)。合同闭合 ③b② 可证伪返回约定：0x6B1900 起取 +0x10=Count、+4=Items，0x6B1913 处 cmp [ecx],esi/inc/add ecx,4/jl 回边，未命中 0x6B191F 处 or eax,-1。
  ```
- AFTER 第 4 列：
  ```text
  SlaveManager 指针动态数组 FindItemIndex：按指针线性扫描至 Count，命中返回下标、未命中 -1(ret4)。合同闭合 ③b② 可证伪返回约定：0x6B1900 起取 +0x10=Count、+4=Items，0x6B1913 处 cmp [ecx],esi/inc/add ecx,4/jl 回边，未命中 0x6B191F 处 or eax,-1。；④ 活表槽位见证：T_DynamicVectorClass_PAVSlaveManagerClass__::slot4（vt=007F315C，槽 4 值=006B1900，COL=00809620 offset=0，RTTI=0083FCD0→.?AV?$DynamicVectorClass@PAVSlaveManagerClass@@@@；装表点 006AF13D 位于 006AF120 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVSlaveManagerClass__::slot4（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVSlaveManagerClass__；该槽即其 vt=007F315C 表 slot4，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- 追加段（595 B）：`；④ 活表槽位见证：T_DynamicVectorClass_PAVSlaveManagerClass__::slot4（vt=007F315C，槽 4 值=006B1900，COL=00809620 offset=0，RTTI=0083FCD0→.?AV?$DynamicVectorClass@PAVSlaveManagerClass@@@@；装表点 006AF13D 位于 006AF120 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVSlaveManagerClass__::slot4（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVSlaveManagerClass__；该槽即其 vt=007F315C 表 slot4，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段内 `§12.6` 命中 1 / `§12.4` 命中 0；改前已含 `④`=False、已含 `④ 活表槽位见证`=False。

### 11. `006B8660` T_DynamicVectorClass_PAVSpawnManagerClass__::slot2
- BEFORE 第 4 列：
  ```text
  SpawnManager 指针动态数组 SetCapacity：分配/复用后备缓冲、逐元素拷贝、按需释放旧缓冲并改挂 Items/Count。合同闭合 ③b④ 完整循环 I/O：0x6B86AE 处 mov edx,[esi+4]/inc eax/mov [edi+eax*4-4],edx/jl 回边读-写-推进齐备；0x7C8E17 分配、0x7C8B3D 释放，ret8。
  ```
- AFTER 第 4 列：
  ```text
  SpawnManager 指针动态数组 SetCapacity：分配/复用后备缓冲、逐元素拷贝、按需释放旧缓冲并改挂 Items/Count。合同闭合 ③b④ 完整循环 I/O：0x6B86AE 处 mov edx,[esi+4]/inc eax/mov [edi+eax*4-4],edx/jl 回边读-写-推进齐备；0x7C8E17 分配、0x7C8B3D 释放，ret8。；④ 活表槽位见证：T_DynamicVectorClass_PAVSpawnManagerClass__::slot2（vt=007F35E4，槽 2 值=006B8660，COL=00809A08 offset=0，RTTI=008400E0→.?AV?$DynamicVectorClass@PAVSpawnManagerClass@@@@；装表点 006B6C2D 位于 006B6C10 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVSpawnManagerClass__::slot2（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVSpawnManagerClass__；该槽即其 vt=007F35E4 表 slot2，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- 追加段（595 B）：`；④ 活表槽位见证：T_DynamicVectorClass_PAVSpawnManagerClass__::slot2（vt=007F35E4，槽 2 值=006B8660，COL=00809A08 offset=0，RTTI=008400E0→.?AV?$DynamicVectorClass@PAVSpawnManagerClass@@@@；装表点 006B6C2D 位于 006B6C10 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVSpawnManagerClass__::slot2（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVSpawnManagerClass__；该槽即其 vt=007F35E4 表 slot2，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段内 `§12.6` 命中 1 / `§12.4` 命中 0；改前已含 `④`=True、已含 `④ 活表槽位见证`=False。

### 12. `006B8710` T_DynamicVectorClass_PAVSpawnManagerClass__::slot4
- BEFORE 第 4 列：
  ```text
  SpawnManager 指针动态数组 FindItemIndex：按指针扫描至 Count，命中返回下标、未命中 -1(ret4)。合同闭合 ③b② 可证伪返回约定：0x6B8723 处 cmp [ecx],esi/inc eax/add ecx,4/jl 回边，未命中 0x6B872F 处 or eax,-1；Count 取 +0x10。
  ```
- AFTER 第 4 列：
  ```text
  SpawnManager 指针动态数组 FindItemIndex：按指针扫描至 Count，命中返回下标、未命中 -1(ret4)。合同闭合 ③b② 可证伪返回约定：0x6B8723 处 cmp [ecx],esi/inc eax/add ecx,4/jl 回边，未命中 0x6B872F 处 or eax,-1；Count 取 +0x10。；④ 活表槽位见证：T_DynamicVectorClass_PAVSpawnManagerClass__::slot4（vt=007F35E4，槽 4 值=006B8710，COL=00809A08 offset=0，RTTI=008400E0→.?AV?$DynamicVectorClass@PAVSpawnManagerClass@@@@；装表点 006B6C2D 位于 006B6C10 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVSpawnManagerClass__::slot4（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVSpawnManagerClass__；该槽即其 vt=007F35E4 表 slot4，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- 追加段（595 B）：`；④ 活表槽位见证：T_DynamicVectorClass_PAVSpawnManagerClass__::slot4（vt=007F35E4，槽 4 值=006B8710，COL=00809A08 offset=0，RTTI=008400E0→.?AV?$DynamicVectorClass@PAVSpawnManagerClass@@@@；装表点 006B6C2D 位于 006B6C10 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVSpawnManagerClass__::slot4（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVSpawnManagerClass__；该槽即其 vt=007F35E4 表 slot4，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段内 `§12.6` 命中 1 / `§12.4` 命中 0；改前已含 `④`=False、已含 `④ 活表槽位见证`=False。

### 13. `006F9E50` TechnoClass::slot23
- BEFORE 第 4 列：
  ```text
  TechnoClass 对象状态批量刷新：2 个严格循环(首 head=0x6FA353 span=15)，1348 指令 207 jcc 73 调用，遍历子对象/状态位并写回；读判写推进完整，③b④ 完整循环 I/O。
  ```
- AFTER 第 4 列：
  ```text
  TechnoClass 对象状态批量刷新：2 个严格循环(首 head=0x6FA353 span=15)，1348 指令 207 jcc 73 调用，遍历子对象/状态位并写回；读判写推进完整，③b④ 完整循环 I/O。；④ 活表槽位见证：TechnoClass::slot23（vt=007F4960，槽 23 值=006F9E50，COL=0080C058 offset=0，RTTI=00817B58→.?AVTechnoClass@@；装表点 006F3130 位于 006F2B40 体内，entry 体外） ④升级句：TechnoClass::slot23（④ 表属类与行名类一致，均为 TechnoClass；该槽即其 vt=007F4960 表 slot23，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- 追加段（471 B）：`；④ 活表槽位见证：TechnoClass::slot23（vt=007F4960，槽 23 值=006F9E50，COL=0080C058 offset=0，RTTI=00817B58→.?AVTechnoClass@@；装表点 006F3130 位于 006F2B40 体内，entry 体外） ④升级句：TechnoClass::slot23（④ 表属类与行名类一致，均为 TechnoClass；该槽即其 vt=007F4960 表 slot23，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段内 `§12.6` 命中 1 / `§12.4` 命中 0；改前已含 `④`=True、已含 `④ 活表槽位见证`=False。

## 4. PANEL.md M88 披露（插于 M87 块之后，共 8 行）

> ✅ **M88 补记：43 行 `slotN` 的 ④ 成文收官（批次 3 并入 13 行，累计 43 / 43）**
> 本批 13 行取自 `PROBE_802\slotN43.tsv` 数据行 31–43，`col_ok=match` / `install_ext=y` 13/13；
> 异族审计（`R16_AUDIT_SLOTN_B3\VERDICT.md`）判 **A/B/D/E/F 五项全 0 不合格，78/78 字节项独立复算为真，0 必改**；指针 13/13 已是 `§12.6`（无需规范化），全文 `§12.4` 命中 0 处；
> ⚠️ 本批有 **2 处对扫描产物 site 的合法改选**：`005B3570`（`InfantryClass::slot123`）与 `005B35E0`（`InfantryClass::slot122`）的 `work_scan.site_of=0043B71F` 实际装的是 BuildingClass 表（`007E3EBC`），与行名类冲突；均改取 InfantryClass 表 `007EB058`，装表点分别为 `00517D9D` / `00521A11`。审计两行均判**成立**，并核实「同一张表有多处装表点（`007EB058` 共 3 处）属正常」。引用这两行时须知情。
> 数字（实测）：口径 A（`[已证]` 且第 4 列含字符 `④`）由 **337 / 1,654（20.37%）升至 347 / 1,654（20.98%）**，本批**净增 = 347 − 337 = 10 行**，**不是简单 +13**：13 行中有 **3 行**（`006B1850`/`006B8660`/`006F9E50`）改前第 4 列已在「合同闭合 ③b④」分类标签里含字符 `④`，改后计数不增；口径 B（`[已证]` 且第 4 列含 `④ 活表槽位见证`）由 **121 / 1,654（7.32%）升至 134 / 1,654（8.10%）**（净增 13 行）。
> **43 行收官**：三批合计 43 行（15 + 15 + 13），`slotN` 类已无剩余可补（D-47(A) 裁决下的上限已兑现）。
> ⚠️ **口径 A 的已知异质性**：口径 A 只要求含字符 `④`，A−B 由 216 → 213 行含 `④` 而非 `④ 活表槽位见证` 形态（含 `③b④` 分类/环标签、`④ N 个 E8 直调站点`、`④ 活 vt 构造安装点` 等）。⇒ **引用 ④ 成文率必须说明用的是 A 还是 B**，不得当作「四环齐全」的等价物。
> **本次只补 ④ 成文，grade / 判定 / named / proved / strict 全不变，无达标翻转**；

> 既有内容零删除零改字：删掉上述 M88 块后重建 sha256 == 改前 sha256（V7）。

## 5. 10 项验证逐项 PASS/FAIL 与实际数字

| 项 | 结果 | 关键实测 |
|---|---|---|
| 逐字节还原性（coverage.tsv）（V1_coverage_byte_restore） | **PASS** | recon_sha8=0046bad9 / before_sha8=0046bad9 / recon_eq_bak=True / locate=True |
| 不变量（V2_invariants） | **PASS** | data_rows=18498 coldist={'8': 18498} 已证=1654 atlas内=1648 atlas外=6 13行[已证]=True |
| 只有 13 行第 4 列变了（V3_only_13_col4） | **PASS** | diff=13 期望=13 entry匹配=True 每行仅col4=True |
| 严格前缀（V4_strict_prefix） | **PASS** | 13/13 |
| 口径 A/B 五个数（V5_five_numbers） | **PASS** | {'N_A_pre': 337, 'N_A_post': 347, 'N_B_pre': 121, 'N_B_post': 134, 'N_pre': 3} net_A=+10 net_B=+13 consistent=True |
| §12.6/§12.4 命中计数（V6_pointer_counts） | **PASS** | 13行内 13/0；全表 §12.6 lines 30→43 hits 30→43；§12.4 0→0 |
| PANEL.md 还原性（V7_panel_restore） | **PASS** | recon_sha8=946a8eb2 / before_sha8=946a8eb2 / recon_eq_bak=True / 删除M88=True / 块行数=8 |
| 达标未翻转（V8_dod_no_flip） | **PASS** | 名义=S15,S16,S17 严格=S17 rc=0 |
| 行尾（V9_line_endings） | **PASS** | cov CRLF/LF/CR=0/18498/0 pan=0/624/0；d_cov_bytes=6659 d_pan_bytes=2040；未混用=True |
| 43 行收官核对（V10_slotN43_closeout） | **PASS** | slotN43 entries=43 命中行=43 unique=43 missing=[] |

**合计：PASS 10 / 10，FAIL 0。**

## 6. 达标集合与边界声明

- strict_panel 口径复算：脚本 `strict_panel_local.py`（`RULING_R15_20261119/work/strict_panel.py` 副本，仅 `OUT` 改到本目录 `strict_out/`）；名义 **S15,S16,S17**（3/22），严格 **S17**（1/22）—— 未翻转。
- 43 行收官：全表第 4 列含 `④ 活表槽位见证` 且 entry ∈ `PROBE_802/slotN43.tsv` 的行 = **43/43**（三批 15+15+13 全覆盖，`slotN` 类已无剩余可补）。
- 本批 2 处合法改选（005B3570 / 005B35E0）已在 M88 披露中知情引用；审计两行判成立。
- 未改 R14_COMMON.md / 台账 / 看板 / `_drafts` / `_cards` / 任何卡目录；未做逆向；strict_panel 输出只在本目录。
- 产物：`MERGE_LOG.md`、`verify.py`、`BEFORE_AFTER.txt`、`before_state.json`、`after_state.json`、`verify_result.json`、`coverage.before.bak`、`PANEL.before.bak`、`merge.py`、`strict_panel_local.py`、`strict_out/`、`measure_pre.py/json`。
