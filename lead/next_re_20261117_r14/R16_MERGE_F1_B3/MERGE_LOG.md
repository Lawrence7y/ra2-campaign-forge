# R16-MERGE-F1-B3 · 合并日志

> 批次 B3（派生集合第 37–54 行，18 行）；PANEL 披露编号 M91，插入点紧接 M90 块之后。
> 审计 R16_AUDIT_F1_B3/VERDICT.md：PASS 18 / FAIL 0 / 必改 0（已核，方可并表）。

## 一、改前 → 改后（两份文件）

| 文件 | 改前 bytes | 改后 bytes | 改前 sha256(前8) | 改后 sha256(前8) |
|---|---:|---:|---|---|
| coverage.tsv | 4058895 | 4068561 | 6428B4EB | 400D211A |
| PANEL.md | 172885 | 175996 | 75576716 | 607BB21F |

## 二、六个实测数（改前盘上自算，非预测/旧值）

- N_pre_A = **16**（18 行中改前第 4 列已含字符 `④` 的行数）
- N_pre_B = **0**（18 行中改前第 4 列已含 `④ 活表槽位见证` 的行数）
- N_A_pre = **354** → N_A_post = **356**（净增 **2**，不是 +18；18 行里 16 行改前已含 `④`，故口径 A 不增）
- N_B_pre = **170** → N_B_post = **188**（净增 **18**）

口径 A = `[已证]` 且第 4 列含字符 `④`（MERGE_M79/verify.py:159）；口径 B = `[已证]` 且第 4 列含子串 `④ 活表槽位见证`。

审计记的两条已接受限制已写进 M91 披露：① 16 行同格并存两条 `④`（按行去重）；② 个位行本 entry 体内也装同一张表（本批实测 0 行，写入以覆盖后续批次）；另按派发要求照实写入 NIT-2：同格内「宿主」一词指两个不同函数（旧 ④ = 调用方注册函数 006BB9A0；新 ④ = 装表点函数 006C37C0/006C37C9 所在函数），两者均实测为真。

## 三、9 项验证（verify.py 可复跑）

| # | 验证 | 结果 | 实测 |
|---|---|---|---|
| 1 | 9. 行尾不混用、LF 一致 | PASS | cov CRLF=0 LF=18498 endsLF=False; pan CRLF=0 LF=645 endsLF=True |
| 2 | 1. coverage.tsv 逐字节还原性 | PASS | reverted_rows=18; recon sha=6428B4EB bytes=4058895; expected 6428B4EB 4058895 |
| 3 | 2. 不变量 18498/{8:18498}/1654/1648/6/18行grade | PASS | n=18498 coldist={8: 18498} proved=1654 in=1648 out=6 grade18=True |
| 4 | 3. 仅 18 行第 4 列变化 | PASS | diff_count=18 diff_entries_match=True bad_other_cols=[] |
| 5 | 4. 严格前缀 18/18 且其它列同 delta | PASS | prefix=18/18 others=18/18 |
| 6 | 5. 六个实测数 | PASS | {"N_pre_A": 16, "N_pre_B": 0, "N_A_pre": 354, "N_A_post": 356, "N_B_pre": 170, "N_B_post": 188} |
| 7 | 6. §12.6/§12.4 命中计数 | PASS | append §12.6=18 §12.4=0; whole-table post §12.6=97 §12.4=0; pre §12.6=79 §12.4=0 |
| 8 | 7. PANEL.md 还原性（删 M91 块） | PASS | m91_at_line=252 rebuilt sha=75576716 bytes=172885 |
| 9 | 8. 达标未翻转 (strict_panel.py) | PASS | 名义=[S15,S16,S17] 严格=[S17] (期望 S15,S16,S17 / S17) |

达标集合（strict_panel.py 口径，输出在本目录）：名义 **S15,S16,S17**，严格 **S17**（未翻转）。

## 四、18 行第 4 列 before / after

每行「改前第 4 列」为盘上原值，「改后第 4 列」为 delta 值（= 原值 + 追加段）。已核 18/18 严格前缀、其余 7 列逐字节相同。

### 006C3890  T_TClassFactory_VInfantryClass__::slot3

**改前第 4 列：**
```
S22 T_TClassFactory_VInfantryClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C389B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C38F1 `call dword ptr [eax]`（新建 InfantryClass 对象主 vt 007EB058 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C38F3 `mov edi,eax`/`test edi,edi`/`jge 0x6c3902`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C38FF `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 InfantryClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 InfantryClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3C0C(vt 007F3C00 +12，slot#3) 4B 值即本 entry，RTTI COL=0080ABB8→TD=00841928→名=.?AV?$TClassFactory@VInfantryClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C37C0 装 vt 007F3C00→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**追加段（④ 活表槽位见证 + D-47 披露）：**
```
；④ 活表槽位见证：T_TClassFactory_VInfantryClass__::slot3（vt=007F3C00，槽 3 值=006C3890，COL=0080ABB8 offset=0，RTTI=00841928→.?AV?$TClassFactory@VInfantryClass@@@@；装表点 006C37C9 位于 006C37C0 体内，entry 体外） ④升级句：T_TClassFactory_VInfantryClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VInfantryClass__；该槽即其 vt=007F3C00 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

### 006C3A10  T_TClassFactory_VAnimClass__::slot3

**改前第 4 列：**
```
S22 T_TClassFactory_VAnimClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C3A1B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C3A6D `call dword ptr [eax]`（新建 AnimClass 对象主 vt 007E3354 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C3A6F `mov edi,eax`/`test edi,edi`/`jge 0x6c3a7e`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C3A7B `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 AnimClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 AnimClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3C24(vt 007F3C18 +12，slot#3) 4B 值即本 entry，RTTI COL=0080AC08→TD=00841958→名=.?AV?$TClassFactory@VAnimClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C3940 装 vt 007F3C18→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**追加段（④ 活表槽位见证 + D-47 披露）：**
```
；④ 活表槽位见证：T_TClassFactory_VAnimClass__::slot3（vt=007F3C18，槽 3 值=006C3A10，COL=0080AC08 offset=0，RTTI=00841958→.?AV?$TClassFactory@VAnimClass@@@@；装表点 006C3949 位于 006C3940 体内，entry 体外） ④升级句：T_TClassFactory_VAnimClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VAnimClass__；该槽即其 vt=007F3C18 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

### 006C3B90  T_TClassFactory_VAnimTypeClass__::slot3

**改前第 4 列：**
```
S22 T_TClassFactory_VAnimTypeClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C3B9B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C3BEF `call dword ptr [eax]`（新建 AnimTypeClass 对象主 vt 007E3608 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C3BF1 `mov edi,eax`/`test edi,edi`/`jge 0x6c3c00`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C3BFD `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 AnimTypeClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 AnimTypeClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3C3C(vt 007F3C30 +12，slot#3) 4B 值即本 entry，RTTI COL=0080AC58→TD=00841988→名=.?AV?$TClassFactory@VAnimTypeClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C3AC0 装 vt 007F3C30→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**追加段（④ 活表槽位见证 + D-47 披露）：**
```
；④ 活表槽位见证：T_TClassFactory_VAnimTypeClass__::slot3（vt=007F3C30，槽 3 值=006C3B90，COL=0080AC58 offset=0，RTTI=00841988→.?AV?$TClassFactory@VAnimTypeClass@@@@；装表点 006C3AC9 位于 006C3AC0 体内，entry 体外） ④升级句：T_TClassFactory_VAnimTypeClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VAnimTypeClass__；该槽即其 vt=007F3C30 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

### 006C5210  T_TClassFactory_VFactoryClass__::slot3

**改前第 4 列：**
```
S22 T_TClassFactory_VFactoryClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C521B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C526A `call dword ptr [eax]`（新建 FactoryClass 对象主 vt 007E88D0 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C526C `mov edi,eax`/`test edi,edi`/`jge 0x6c527b`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C5278 `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 FactoryClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 FactoryClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3DA4(vt 007F3D98 +12，slot#3) 4B 值即本 entry，RTTI COL=0080B108→TD=00841CB8→名=.?AV?$TClassFactory@VFactoryClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C5140 装 vt 007F3D98→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**追加段（④ 活表槽位见证 + D-47 披露）：**
```
；④ 活表槽位见证：T_TClassFactory_VFactoryClass__::slot3（vt=007F3D98，槽 3 值=006C5210，COL=0080B108 offset=0，RTTI=00841CB8→.?AV?$TClassFactory@VFactoryClass@@@@；装表点 006C5149 位于 006C5140 体内，entry 体外） ④升级句：T_TClassFactory_VFactoryClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VFactoryClass__；该槽即其 vt=007F3D98 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

### 006C5390  T_TClassFactory_VWarheadTypeClass__::slot3

**改前第 4 列：**
```
S22 T_TClassFactory_VWarheadTypeClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C539B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C53EF `call dword ptr [eax]`（新建 WarheadTypeClass 对象主 vt 007F6B30 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C53F1 `mov edi,eax`/`test edi,edi`/`jge 0x6c5400`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C53FD `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 WarheadTypeClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 WarheadTypeClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3DBC(vt 007F3DB0 +12，slot#3) 4B 值即本 entry，RTTI COL=0080B158→TD=00841CE8→名=.?AV?$TClassFactory@VWarheadTypeClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C52C0 装 vt 007F3DB0→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**追加段（④ 活表槽位见证 + D-47 披露）：**
```
；④ 活表槽位见证：T_TClassFactory_VWarheadTypeClass__::slot3（vt=007F3DB0，槽 3 值=006C5390，COL=0080B158 offset=0，RTTI=00841CE8→.?AV?$TClassFactory@VWarheadTypeClass@@@@；装表点 006C52C9 位于 006C52C0 体内，entry 体外） ④升级句：T_TClassFactory_VWarheadTypeClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VWarheadTypeClass__；该槽即其 vt=007F3DB0 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

### 006C5510  T_TClassFactory_VWeaponTypeClass__::slot3

**改前第 4 列：**
```
S22 T_TClassFactory_VWeaponTypeClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C551B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C556F `call dword ptr [eax]`（新建 WeaponTypeClass 对象主 vt 007F73B8 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C5571 `mov edi,eax`/`test edi,edi`/`jge 0x6c5580`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C557D `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 WeaponTypeClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 WeaponTypeClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3DD4(vt 007F3DC8 +12，slot#3) 4B 值即本 entry，RTTI COL=0080B1A8→TD=00841D20→名=.?AV?$TClassFactory@VWeaponTypeClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C5440 装 vt 007F3DC8→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**追加段（④ 活表槽位见证 + D-47 披露）：**
```
；④ 活表槽位见证：T_TClassFactory_VWeaponTypeClass__::slot3（vt=007F3DC8，槽 3 值=006C5510，COL=0080B1A8 offset=0，RTTI=00841D20→.?AV?$TClassFactory@VWeaponTypeClass@@@@；装表点 006C5449 位于 006C5440 体内，entry 体外） ④升级句：T_TClassFactory_VWeaponTypeClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VWeaponTypeClass__；该槽即其 vt=007F3DC8 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

### 006C5690  T_TClassFactory_VParticleClass__::slot3

**改前第 4 列：**
```
S22 T_TClassFactory_VParticleClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C569B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C56ED `call dword ptr [eax]`（新建 ParticleClass 对象主 vt 007EF954 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C56EF `mov edi,eax`/`test edi,edi`/`jge 0x6c56fe`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C56FB `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 ParticleClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 ParticleClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3DEC(vt 007F3DE0 +12，slot#3) 4B 值即本 entry，RTTI COL=0080B1F8→TD=00841D58→名=.?AV?$TClassFactory@VParticleClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C55C0 装 vt 007F3DE0→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**追加段（④ 活表槽位见证 + D-47 披露）：**
```
；④ 活表槽位见证：T_TClassFactory_VParticleClass__::slot3（vt=007F3DE0，槽 3 值=006C5690，COL=0080B1F8 offset=0，RTTI=00841D58→.?AV?$TClassFactory@VParticleClass@@@@；装表点 006C55C9 位于 006C55C0 体内，entry 体外） ④升级句：T_TClassFactory_VParticleClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VParticleClass__；该槽即其 vt=007F3DE0 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

### 006C5810  T_TClassFactory_VParticleTypeClass__::slot3

**改前第 4 列：**
```
S22 T_TClassFactory_VParticleTypeClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C581B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C586F `call dword ptr [eax]`（新建 ParticleTypeClass 对象主 vt 007F0188 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C5871 `mov edi,eax`/`test edi,edi`/`jge 0x6c5880`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C587D `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 ParticleTypeClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 ParticleTypeClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3E04(vt 007F3DF8 +12，slot#3) 4B 值即本 entry，RTTI COL=0080B248→TD=00841D88→名=.?AV?$TClassFactory@VParticleTypeClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C5740 装 vt 007F3DF8→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**追加段（④ 活表槽位见证 + D-47 披露）：**
```
；④ 活表槽位见证：T_TClassFactory_VParticleTypeClass__::slot3（vt=007F3DF8，槽 3 值=006C5810，COL=0080B248 offset=0，RTTI=00841D88→.?AV?$TClassFactory@VParticleTypeClass@@@@；装表点 006C5749 位于 006C5740 体内，entry 体外） ④升级句：T_TClassFactory_VParticleTypeClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VParticleTypeClass__；该槽即其 vt=007F3DF8 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

### 006C5990  T_TClassFactory_VParticleSystemClass__::slot3

**改前第 4 列：**
```
S22 T_TClassFactory_VParticleSystemClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C599B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C59ED `call dword ptr [eax]`（新建 ParticleSystemClass 对象主 vt 007EFB9C 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C59EF `mov edi,eax`/`test edi,edi`/`jge 0x6c59fe`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C59FB `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 ParticleSystemClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 ParticleSystemClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3E1C(vt 007F3E10 +12，slot#3) 4B 值即本 entry，RTTI COL=0080B298→TD=00841DC0→名=.?AV?$TClassFactory@VParticleSystemClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C58C0 装 vt 007F3E10→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**追加段（④ 活表槽位见证 + D-47 披露）：**
```
；④ 活表槽位见证：T_TClassFactory_VParticleSystemClass__::slot3（vt=007F3E10，槽 3 值=006C5990，COL=0080B298 offset=0，RTTI=00841DC0→.?AV?$TClassFactory@VParticleSystemClass@@@@；装表点 006C58C9 位于 006C58C0 体内，entry 体外） ④升级句：T_TClassFactory_VParticleSystemClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VParticleSystemClass__；该槽即其 vt=007F3E10 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

### 006C5B10  T_TClassFactory_VParticleSystemTypeClass__::slot3

**改前第 4 列：**
```
S22 T_TClassFactory_VParticleSystemTypeClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C5B1B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C5B6F `call dword ptr [eax]`（新建 ParticleSystemTypeClass 对象主 vt 007F00A8 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C5B71 `mov edi,eax`/`test edi,edi`/`jge 0x6c5b80`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C5B7D `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 ParticleSystemTypeClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 ParticleSystemTypeClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3E34(vt 007F3E28 +12，slot#3) 4B 值即本 entry，RTTI COL=0080B2E8→TD=00841DF8→名=.?AV?$TClassFactory@VParticleSystemTypeClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C5A40 装 vt 007F3E28→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**追加段（④ 活表槽位见证 + D-47 披露）：**
```
；④ 活表槽位见证：T_TClassFactory_VParticleSystemTypeClass__::slot3（vt=007F3E28，槽 3 值=006C5B10，COL=0080B2E8 offset=0，RTTI=00841DF8→.?AV?$TClassFactory@VParticleSystemTypeClass@@@@；装表点 006C5A49 位于 006C5A40 体内，entry 体外） ④升级句：T_TClassFactory_VParticleSystemTypeClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VParticleSystemTypeClass__；该槽即其 vt=007F3E28 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

### 006C5C90  T_TClassFactory_VAITriggerTypeClass__::slot3

**改前第 4 列：**
```
S22 T_TClassFactory_VAITriggerTypeClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C5C9B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C5CEF `call dword ptr [eax]`（新建 AITriggerTypeClass 对象主 vt 007E2A50 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C5CF1 `mov edi,eax`/`test edi,edi`/`jge 0x6c5d00`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C5CFD `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 AITriggerTypeClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 AITriggerTypeClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3E4C(vt 007F3E40 +12，slot#3) 4B 值即本 entry，RTTI COL=0080B338→TD=00841E38→名=.?AV?$TClassFactory@VAITriggerTypeClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C5BC0 装 vt 007F3E40→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**追加段（④ 活表槽位见证 + D-47 披露）：**
```
；④ 活表槽位见证：T_TClassFactory_VAITriggerTypeClass__::slot3（vt=007F3E40，槽 3 值=006C5C90，COL=0080B338 offset=0，RTTI=00841E38→.?AV?$TClassFactory@VAITriggerTypeClass@@@@；装表点 006C5BC9 位于 006C5BC0 体内，entry 体外） ④升级句：T_TClassFactory_VAITriggerTypeClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VAITriggerTypeClass__；该槽即其 vt=007F3E40 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

### 006C5E10  T_TClassFactory_VNeuronClass__::slot3

**改前第 4 列：**
```
S22 T_TClassFactory_VNeuronClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C5E1B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C5E6A `call dword ptr [eax]`（新建 NeuronClass 对象主 vt 007E3DF0 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C5E6C `mov edi,eax`/`test edi,edi`/`jge 0x6c5e7b`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C5E78 `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 NeuronClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 NeuronClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3E64(vt 007F3E58 +12，slot#3) 4B 值即本 entry，RTTI COL=0080B388→TD=00841E70→名=.?AV?$TClassFactory@VNeuronClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C5D40 装 vt 007F3E58→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**追加段（④ 活表槽位见证 + D-47 披露）：**
```
；④ 活表槽位见证：T_TClassFactory_VNeuronClass__::slot3（vt=007F3E58，槽 3 值=006C5E10，COL=0080B388 offset=0，RTTI=00841E70→.?AV?$TClassFactory@VNeuronClass@@@@；装表点 006C5D49 位于 006C5D40 体内，entry 体外） ④升级句：T_TClassFactory_VNeuronClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VNeuronClass__；该槽即其 vt=007F3E58 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

### 006C5F90  T_TClassFactory_VFoggedObjectClass__::slot3

**改前第 4 列：**
```
S22 T_TClassFactory_VFoggedObjectClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C5F9B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C5FEA `call dword ptr [eax]`（新建 FoggedObjectClass 对象主 vt 007E8B38 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C5FEC `mov edi,eax`/`test edi,edi`/`jge 0x6c5ffb`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C5FF8 `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 FoggedObjectClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 FoggedObjectClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3E7C(vt 007F3E70 +12，slot#3) 4B 值即本 entry，RTTI COL=0080B3D8→TD=00841EA0→名=.?AV?$TClassFactory@VFoggedObjectClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C5EC0 装 vt 007F3E70→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**追加段（④ 活表槽位见证 + D-47 披露）：**
```
；④ 活表槽位见证：T_TClassFactory_VFoggedObjectClass__::slot3（vt=007F3E70，槽 3 值=006C5F90，COL=0080B3D8 offset=0，RTTI=00841EA0→.?AV?$TClassFactory@VFoggedObjectClass@@@@；装表点 006C5EC9 位于 006C5EC0 体内，entry 体外） ④升级句：T_TClassFactory_VFoggedObjectClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VFoggedObjectClass__；该槽即其 vt=007F3E70 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

### 006C6110  T_TClassFactory_VAlphaShapeClass__::slot3

**改前第 4 列：**
```
S22 T_TClassFactory_VAlphaShapeClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C611B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C616A `call dword ptr [eax]`（新建 AlphaShapeClass 对象主 vt 007E32A4 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C616C `mov edi,eax`/`test edi,edi`/`jge 0x6c617b`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C6178 `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 AlphaShapeClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 AlphaShapeClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3E94(vt 007F3E88 +12，slot#3) 4B 值即本 entry，RTTI COL=0080B428→TD=00841ED8→名=.?AV?$TClassFactory@VAlphaShapeClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C6040 装 vt 007F3E88→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**追加段（④ 活表槽位见证 + D-47 披露）：**
```
；④ 活表槽位见证：T_TClassFactory_VAlphaShapeClass__::slot3（vt=007F3E88，槽 3 值=006C6110，COL=0080B428 offset=0，RTTI=00841ED8→.?AV?$TClassFactory@VAlphaShapeClass@@@@；装表点 006C6049 位于 006C6040 体内，entry 体外） ④升级句：T_TClassFactory_VAlphaShapeClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VAlphaShapeClass__；该槽即其 vt=007F3E88 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

### 006DBD20  Tactical::slot5

**改前第 4 列：**
```
Tactical::slot5（③b② 流读入：call 0x410380@006DBD2E([eax+0xc] IStream::Read 槽)→test eax,eax@006DBD33→jl@006DBD35，失败返负 HRESULT(0x80004003 E_POINTER)/成功返 0 并有 006DBDC7.. 非栈写，两路真不同；读写方向逐字节核定为读入未写反；② vt 007F4348 slot5 RTTI .?AVTactical@@；④ 行外 ctor 006D1C20@006D1D54 装活表，与②不同源）
```

**追加段（④ 活表槽位见证 + D-47 披露）：**
```
；④ 活表槽位见证：Tactical::slot5（vt=007F4348，槽 5 值=006DBD20，COL=0080B9A8 offset=0，RTTI=00842A38→.?AVTactical@@；装表点 006D1D54 位于 006D1C20 体内，entry 体外） ④升级句：Tactical::slot5（④ 表属类与行名类一致，均为 Tactical；该槽即其 vt=007F4348 表 slot5，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

### 006DBE00  Tactical::slot6

**改前第 4 列：**
```
Tactical::slot6（③b② 流写出：call 0x410320@006DBE0F([eax+0x10]=IStream::Write，方向逐字节核定为写出未写反)→test eax,eax@006DBE14→jl@006DBE16，失败原样上抛负HRESULT(0x80004003 E_POINTER)/成功 xor eax,eax@006DBE18 返0，两路真不同；② vt 007F4348 slot6 COL.offset=0 主表 RTTI .?AVTactical@@；④ 行外 ctor 006D1C20@006D1D54 装活表 + push 0xE18/new 实例化，同表析构重装按㉓排除，与②RTTI链不同源）
```

**追加段（④ 活表槽位见证 + D-47 披露）：**
```
；④ 活表槽位见证：Tactical::slot6（vt=007F4348，槽 6 值=006DBE00，COL=0080B9A8 offset=0，RTTI=00842A38→.?AVTactical@@；装表点 006D1D54 位于 006D1C20 体内，entry 体外） ④升级句：Tactical::slot6（④ 表属类与行名类一致，均为 Tactical；该槽即其 vt=007F4348 表 slot6，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

### 006E3E30  TActionClass::slot6

**改前第 4 列：**
```
TActionClass 流写出（Save）：三参转交 00410320 写包装，包装对空流入参返回 E_POINTER 0x80004003；本行 test eax,eax + jl 让负码原样返回、成功路 xor eax,eax 返回 S_OK ⇒ 多值错误码被本行分支消费（③b②）。
```

**追加段（④ 活表槽位见证 + D-47 披露）：**
```
；④ 活表槽位见证：TActionClass::slot6（vt=007F443C，槽 6 值=006E3E30，COL=0080BAF0 offset=0，RTTI=00842B78→.?AVTActionClass@@；装表点 006DD036 位于 006DD000 体内，entry 体外） ④升级句：TActionClass::slot6（④ 表属类与行名类一致，均为 TActionClass；该槽即其 vt=007F443C 表 slot6，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

### 006E57A0  TagClass::slot6

**改前第 4 列：**
```
TagClass 流写出（Save）：三参转交 00410320 写包装，包装对空流入参返回 E_POINTER 0x80004003；本行 test eax,eax + jl 让负码原样返回、成功路 xor eax,eax 返回 S_OK ⇒ 多值错误码被本行分支消费（③b②）。
```

**追加段（④ 活表槽位见证 + D-47 披露）：**
```
；④ 活表槽位见证：TagClass::slot6（vt=007F44E0，槽 6 值=006E57A0，COL=0080BBA0 offset=0，RTTI=008249E8→.?AVTagClass@@；装表点 006E4E07 位于 006E4DE0 体内，entry 体外） ④升级句：TagClass::slot6（④ 表属类与行名类一致，均为 TagClass；该槽即其 vt=007F44E0 表 slot6，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

## 五、边界声明

- 只改 coverage.tsv 这 18 行的第 4 列；其它行/列、grade/判定/行序均未动。
- PANEL.md 只插入 1 条 M91 披露（7 行 `> ` 引用块），既有内容零删除零改字（删 M91 块后 sha 复原为改前值）。
- 未改 R14_COMMON/台账/看板/_drafts/_cards/卡目录；未做逆向；strict_panel 输出在本目录。
