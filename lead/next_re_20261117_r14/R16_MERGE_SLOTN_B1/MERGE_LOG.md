# R16-MERGE-SLOTN-B1 · MERGE LOG

> 合并员：agent-11 · 2026-11-20（R16 第 4 轮）
> 写域：`COVERAGE/coverage.tsv`（仅 15 行第 4 列）+ `COVERAGE/PANEL.md`（1 指针 + 1 插入）+ 本产物目录

## 1 · 并表概览

- 输入：`R16_SLOTN_B1/delta.tsv`（1 表头 + 15 数据行，8 列），审计 `R16_AUDIT_SLOTN_B1` 裁 **PASS 15 / FAIL 0 / 必改 0**（90/90 字节项为真）。
- 规则：第 4 列 = 盘上原第 4 列（严格前缀）+ 追加段；第 1/2/3/5/6/7/8 列逐字节不动。
- **必需替换**：追加段里的 `R14_COMMON §12.4` → `R14_COMMON §12.6`，**替换发生次数 = 15**（预期 15）。
  - 替换前 1 例：`…见 R14_COMMON §12.4 与 PANEL 对应披露）`
  - 替换后 1 例：`…见 R14_COMMON §12.6 与 PANEL 对应披露）`
  - 仅替换该字样一处/行，其余字节不改。

## 2 · 15 行逐行 before/after 第 4 列

说明：`before` 为盘上原值（严格前缀）；`after` = before + 追加段（追加段已含 §12.6）。前缀校验逐行 PASS。

### 行 1 · entry `0045A560`

- before（原第 4 列，326 B）：`动态数组 SetCapacity：为新容量分配后备缓冲、逐元素拷贝旧数组、按需释放旧缓冲并改挂 Items/Count，成功返回 true。合同闭合 ③b④ 完整循环 I/O：0x45A5AE 处 mov edx,[esi+4]/inc eax/mov [edi+eax*4-4],edx/jl 回边读-写-推进齐备；0x7C8E17 分配、0x7C8B3D 释放，ret8。`
- after（新第 4 列，905 B）：`动态数组 SetCapacity：为新容量分配后备缓冲、逐元素拷贝旧数组、按需释放旧缓冲并改挂 Items/Count，成功返回 true。合同闭合 ③b④ 完整循环 I/O：0x45A5AE 处 mov edx,[esi+4]/inc eax/mov [edi+eax*4-4],edx/jl 回边读-写-推进齐备；0x7C8E17 分配、0x7C8B3D 释放，ret8。；④ 活表槽位见证：T_DynamicVectorClass_PAVInfantryClass__::slot2（vt=007E43C8，槽 2 值=0045A560，COL=007FC298 offset=0，RTTI=00818D28→.?AV?$DynamicVectorClass@PAVInfantryClass@@@@；装表点 0043B6DB 位于 0043B680 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVInfantryClass__::slot2（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVInfantryClass__；该槽即其 vt=007E43C8 表 slot2，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段（579 B）：`；④ 活表槽位见证：T_DynamicVectorClass_PAVInfantryClass__::slot2（vt=007E43C8，槽 2 值=0045A560，COL=007FC298 offset=0，RTTI=00818D28→.?AV?$DynamicVectorClass@PAVInfantryClass@@@@；装表点 0043B6DB 位于 0043B680 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVInfantryClass__::slot2（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVInfantryClass__；该槽即其 vt=007E43C8 表 slot2，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 严格前缀：`before == after[:len(before)]` → **PASS**；其余 7 列逐字节相同 → **PASS**；改前已含字符 ④ = **是**。

### 行 2 · entry `0045A610`

- before（原第 4 列，285 B）：`动态数组 FindItemIndex：按指针线性扫描 Items 至 Count，命中返回下标、未命中返回 -1（ret4）。合同闭合 ③b② 可证伪返回约定：0x45A623 处 cmp [ecx],esi/inc eax/add ecx,4/jl 回边比对，未命中走 0x45A62F 的 or eax,-1；Count 取 +0x10。`
- after（新第 4 列，864 B）：`动态数组 FindItemIndex：按指针线性扫描 Items 至 Count，命中返回下标、未命中返回 -1（ret4）。合同闭合 ③b② 可证伪返回约定：0x45A623 处 cmp [ecx],esi/inc eax/add ecx,4/jl 回边比对，未命中走 0x45A62F 的 or eax,-1；Count 取 +0x10。；④ 活表槽位见证：T_DynamicVectorClass_PAVInfantryClass__::slot4（vt=007E43C8，槽 4 值=0045A610，COL=007FC298 offset=0，RTTI=00818D28→.?AV?$DynamicVectorClass@PAVInfantryClass@@@@；装表点 0043B6DB 位于 0043B680 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVInfantryClass__::slot4（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVInfantryClass__；该槽即其 vt=007E43C8 表 slot4，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段（579 B）：`；④ 活表槽位见证：T_DynamicVectorClass_PAVInfantryClass__::slot4（vt=007E43C8，槽 4 值=0045A610，COL=007FC298 offset=0，RTTI=00818D28→.?AV?$DynamicVectorClass@PAVInfantryClass@@@@；装表点 0043B6DB 位于 0043B680 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVInfantryClass__::slot4（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVInfantryClass__；该槽即其 vt=007E43C8 表 slot4，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 严格前缀：`before == after[:len(before)]` → **PASS**；其余 7 列逐字节相同 → **PASS**；改前已含字符 ④ = **否**。

### 行 3 · entry `0045A680`

- before（原第 4 列，335 B）：`T_DynamicVectorClass_PAVFoggedObjectClass__ 虚表槽 2(+0x8)：迷雾/可见性/雷达 方法（③b④ 按目标容量整体重建迷雾对象向量：6 道守卫校验外部缓冲/新分配/旧数组后逐项深拷贝元素并回写容量标志〔锚 +0x54 mov edx,[edx+eax*4-4] / +0x58 mov [edi+eax*4-4],edx / +0x5C jl 回边〕）`
- after（新第 4 列，930 B）：`T_DynamicVectorClass_PAVFoggedObjectClass__ 虚表槽 2(+0x8)：迷雾/可见性/雷达 方法（③b④ 按目标容量整体重建迷雾对象向量：6 道守卫校验外部缓冲/新分配/旧数组后逐项深拷贝元素并回写容量标志〔锚 +0x54 mov edx,[edx+eax*4-4] / +0x58 mov [edi+eax*4-4],edx / +0x5C jl 回边〕）；④ 活表槽位见证：T_DynamicVectorClass_PAVFoggedObjectClass__::slot2（vt=007E44F4，槽 2 值=0045A680，COL=007FC528 offset=0，RTTI=00819230→.?AV?$DynamicVectorClass@PAVFoggedObjectClass@@@@；装表点 00457BFD 位于 00457AA0 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVFoggedObjectClass__::slot2（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVFoggedObjectClass__；该槽即其 vt=007E44F4 表 slot2，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段（595 B）：`；④ 活表槽位见证：T_DynamicVectorClass_PAVFoggedObjectClass__::slot2（vt=007E44F4，槽 2 值=0045A680，COL=007FC528 offset=0，RTTI=00819230→.?AV?$DynamicVectorClass@PAVFoggedObjectClass@@@@；装表点 00457BFD 位于 00457AA0 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVFoggedObjectClass__::slot2（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVFoggedObjectClass__；该槽即其 vt=007E44F4 表 slot2，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 严格前缀：`before == after[:len(before)]` → **PASS**；其余 7 列逐字节相同 → **PASS**；改前已含字符 ④ = **是**。

### 行 4 · entry `0045A730`

- before（原第 4 列，271 B）：`T_DynamicVectorClass_PAVFoggedObjectClass__ 虚表槽 4(+0x10)：迷雾/可见性/雷达 方法（③b②+④ 在迷雾对象向量中线性查找目标指针、按命中返回下标或 -1 哨兵〔锚 +0x13 cmp [ecx],esi / +0x1D jl 回边 / +0x1F or eax,0xffffffff〕）`
- after（新第 4 列，866 B）：`T_DynamicVectorClass_PAVFoggedObjectClass__ 虚表槽 4(+0x10)：迷雾/可见性/雷达 方法（③b②+④ 在迷雾对象向量中线性查找目标指针、按命中返回下标或 -1 哨兵〔锚 +0x13 cmp [ecx],esi / +0x1D jl 回边 / +0x1F or eax,0xffffffff〕）；④ 活表槽位见证：T_DynamicVectorClass_PAVFoggedObjectClass__::slot4（vt=007E44F4，槽 4 值=0045A730，COL=007FC528 offset=0，RTTI=00819230→.?AV?$DynamicVectorClass@PAVFoggedObjectClass@@@@；装表点 00457BFD 位于 00457AA0 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVFoggedObjectClass__::slot4（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVFoggedObjectClass__；该槽即其 vt=007E44F4 表 slot4，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段（595 B）：`；④ 活表槽位见证：T_DynamicVectorClass_PAVFoggedObjectClass__::slot4（vt=007E44F4，槽 4 值=0045A730，COL=007FC528 offset=0，RTTI=00819230→.?AV?$DynamicVectorClass@PAVFoggedObjectClass@@@@；装表点 00457BFD 位于 00457AA0 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVFoggedObjectClass__::slot4（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVFoggedObjectClass__；该槽即其 vt=007E44F4 表 slot4，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 严格前缀：`before == after[:len(before)]` → **PASS**；其余 7 列逐字节相同 → **PASS**；改前已含字符 ④ = **是**。

### 行 5 · entry `00473BA0`

- before（原第 4 列，342 B）：`CCFileClass 文件定位 Seek：按 whence 三路分派 0=文件头/2=文件尾/其它=当前位置，0x473BAB sub eax,0→0x473BB5 取长度[+0x5C]作基址，0x473BB0 sub eax,2 判尾，0x473BCB add 叠加位移后 sets/dl/dec/and 做有符号溢出钳位、0x473BE1 cmp [+0x5C]/jle 封顶写回游标[+0x64]；③b① 三路互斥可核。`
- after（新第 4 列，813 B）：`CCFileClass 文件定位 Seek：按 whence 三路分派 0=文件头/2=文件尾/其它=当前位置，0x473BAB sub eax,0→0x473BB5 取长度[+0x5C]作基址，0x473BB0 sub eax,2 判尾，0x473BCB add 叠加位移后 sets/dl/dec/and 做有符号溢出钳位、0x473BE1 cmp [+0x5C]/jle 封顶写回游标[+0x64]；③b① 三路互斥可核。；④ 活表槽位见证：CCFileClass::slot10（vt=007E16B0，槽 10 值=00473BA0，COL=007FA590 offset=0，RTTI=00815E58→.?AVCCFileClass@@；装表点 004014AC 位于 004011C0 体内，entry 体外） ④升级句：CCFileClass::slot10（④ 表属类与行名类一致，均为 CCFileClass；该槽即其 vt=007E16B0 表 slot10，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段（471 B）：`；④ 活表槽位见证：CCFileClass::slot10（vt=007E16B0，槽 10 值=00473BA0，COL=007FA590 offset=0，RTTI=00815E58→.?AVCCFileClass@@；装表点 004014AC 位于 004011C0 体内，entry 体外） ④升级句：CCFileClass::slot10（④ 表属类与行名类一致，均为 CCFileClass；该槽即其 vt=007E16B0 表 slot10，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 严格前缀：`before == after[:len(before)]` → **PASS**；其余 7 列逐字节相同 → **PASS**；改前已含字符 ④ = **否**。

### 行 6 · entry `00473C50`

- before（原第 4 列，340 B）：`CCFileClass Open 打开：状态机四级尝试阶梯，从 [+0x68] 状态枚举(0/1/2) 起步，先查 vt[+0x18]、vt[+4] 回调 + 0x5B4430/0x431F10 兜底，0x473C59 cmp [esi+0x68],1 为快速返回路径(al=1)；仅当某级打开成功才返回 al=1，失败返回 al=0，结局可证伪；③b② 返回约定 + ③b① 多路阶梯。`
- after（新第 4 列，807 B）：`CCFileClass Open 打开：状态机四级尝试阶梯，从 [+0x68] 状态枚举(0/1/2) 起步，先查 vt[+0x18]、vt[+4] 回调 + 0x5B4430/0x431F10 兜底，0x473C59 cmp [esi+0x68],1 为快速返回路径(al=1)；仅当某级打开成功才返回 al=1，失败返回 al=0，结局可证伪；③b② 返回约定 + ③b① 多路阶梯。；④ 活表槽位见证：CCFileClass::slot5（vt=007E16B0，槽 5 值=00473C50，COL=007FA590 offset=0，RTTI=00815E58→.?AVCCFileClass@@；装表点 004014AC 位于 004011C0 体内，entry 体外） ④升级句：CCFileClass::slot5（④ 表属类与行名类一致，均为 CCFileClass；该槽即其 vt=007E16B0 表 slot5，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段（467 B）：`；④ 活表槽位见证：CCFileClass::slot5（vt=007E16B0，槽 5 值=00473C50，COL=007FA590 offset=0，RTTI=00815E58→.?AVCCFileClass@@；装表点 004014AC 位于 004011C0 体内，entry 体外） ④升级句：CCFileClass::slot5（④ 表属类与行名类一致，均为 CCFileClass；该槽即其 vt=007E16B0 表 slot5，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 严格前缀：`before == after[:len(before)]` → **PASS**；其余 7 列逐字节相同 → **PASS**；改前已含字符 ④ = **否**。

### 行 7 · entry `00473D10`

- before（原第 4 列，246 B）：`CCFileClass 读/写 I/O 分派：以 [esp+0x20] 的标志位(test ,2 @0x473D10 区) 分流为初始化阶梯与多虚调路径，123 指令 7 条件跳转 9 次调用，vt 表逐路派发且各结局互斥；③b① 多路虚派发可逐路核。`
- after（新第 4 列，713 B）：`CCFileClass 读/写 I/O 分派：以 [esp+0x20] 的标志位(test ,2 @0x473D10 区) 分流为初始化阶梯与多虚调路径，123 指令 7 条件跳转 9 次调用，vt 表逐路派发且各结局互斥；③b① 多路虚派发可逐路核。；④ 活表槽位见证：CCFileClass::slot7（vt=007E16B0，槽 7 值=00473D10，COL=007FA590 offset=0，RTTI=00815E58→.?AVCCFileClass@@；装表点 004014AC 位于 004011C0 体内，entry 体外） ④升级句：CCFileClass::slot7（④ 表属类与行名类一致，均为 CCFileClass；该槽即其 vt=007E16B0 表 slot7，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段（467 B）：`；④ 活表槽位见证：CCFileClass::slot7（vt=007E16B0，槽 7 值=00473D10，COL=007FA590 offset=0，RTTI=00815E58→.?AVCCFileClass@@；装表点 004014AC 位于 004011C0 体内，entry 体外） ④升级句：CCFileClass::slot7（④ 表属类与行名类一致，均为 CCFileClass；该槽即其 vt=007E16B0 表 slot7，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 严格前缀：`before == after[:len(before)]` → **PASS**；其余 7 列逐字节相同 → **PASS**；改前已含字符 ④ = **否**。

### 行 8 · entry `004A9890`

- before（原第 4 列，234 B）：`DisplayClass 显示列表批量构建/刷新：3 个严格循环逐元素读 11 字段写 4 字段，首循环 head=0x4A9A3C span=30 带 cmp 边界与推进；渲染/Blitter 列表的读判写推进完整，③b④ 完整循环 I/O。`
- after（新第 4 列，709 B）：`DisplayClass 显示列表批量构建/刷新：3 个严格循环逐元素读 11 字段写 4 字段，首循环 head=0x4A9A3C span=30 带 cmp 边界与推进；渲染/Blitter 列表的读判写推进完整，③b④ 完整循环 I/O。；④ 活表槽位见证：DisplayClass::slot36（vt=007E6114，槽 36 值=004A9890，COL=007FFCB8 offset=0，RTTI=00816BD8→.?AVDisplayClass@@；装表点 004A8830 位于 004A8730 体内，entry 体外） ④升级句：DisplayClass::slot36（④ 表属类与行名类一致，均为 DisplayClass；该槽即其 vt=007E6114 表 slot36，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段（475 B）：`；④ 活表槽位见证：DisplayClass::slot36（vt=007E6114，槽 36 值=004A9890，COL=007FFCB8 offset=0，RTTI=00816BD8→.?AVDisplayClass@@；装表点 004A8830 位于 004A8730 体内，entry 体外） ④升级句：DisplayClass::slot36（④ 表属类与行名类一致，均为 DisplayClass；该槽即其 vt=007E6114 表 slot36，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 严格前缀：`before == after[:len(before)]` → **PASS**；其余 7 列逐字节相同 → **PASS**；改前已含字符 ④ = **是**。

### 行 9 · entry `004D24A0`

- before（原第 4 列，273 B）：`FoggedObjectClass 虚表槽 6(+0x18)：迷雾/可见性/雷达 方法（③b④ 按 0x10 步长逐单元遍历迷雾可见性数组、对每个单元调用虚方法并在任一负返回时整批中止〔锚 +0x4F call [ecx+0x10] / +0x5B add edi,0x10 / +0x60 jl 回边〕）`
- after（新第 4 列，764 B）：`FoggedObjectClass 虚表槽 6(+0x18)：迷雾/可见性/雷达 方法（③b④ 按 0x10 步长逐单元遍历迷雾可见性数组、对每个单元调用虚方法并在任一负返回时整批中止〔锚 +0x4F call [ecx+0x10] / +0x5B add edi,0x10 / +0x60 jl 回边〕）；④ 活表槽位见证：FoggedObjectClass::slot6（vt=007E8B38，槽 6 值=004D24A0，COL=00800768 offset=0，RTTI=00822438→.?AVFoggedObjectClass@@；装表点 004D088D 位于 004D0860 体内，entry 体外） ④升级句：FoggedObjectClass::slot6（④ 表属类与行名类一致，均为 FoggedObjectClass；该槽即其 vt=007E8B38 表 slot6，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段（491 B）：`；④ 活表槽位见证：FoggedObjectClass::slot6（vt=007E8B38，槽 6 值=004D24A0，COL=00800768 offset=0，RTTI=00822438→.?AVFoggedObjectClass@@；装表点 004D088D 位于 004D0860 体内，entry 体外） ④升级句：FoggedObjectClass::slot6（④ 表属类与行名类一致，均为 FoggedObjectClass；该槽即其 vt=007E8B38 表 slot6，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 严格前缀：`before == after[:len(before)]` → **PASS**；其余 7 列逐字节相同 → **PASS**；改前已含字符 ④ = **是**。

### 行 10 · entry `004D2510`

- before（原第 4 列，241 B）：`FoggedObjectClass 虚表槽 5(+0x14)：迷雾/可见性/雷达 方法（③b④ 跨多来源枚举迷雾单元、逐段虚调用汇总可见性并对负返回提前退出〔锚 +0x84 call [edx+0xc] / +0x14F jl 回边 / +0x207 jl 回边〕）`
- after（新第 4 列，732 B）：`FoggedObjectClass 虚表槽 5(+0x14)：迷雾/可见性/雷达 方法（③b④ 跨多来源枚举迷雾单元、逐段虚调用汇总可见性并对负返回提前退出〔锚 +0x84 call [edx+0xc] / +0x14F jl 回边 / +0x207 jl 回边〕）；④ 活表槽位见证：FoggedObjectClass::slot5（vt=007E8B38，槽 5 值=004D2510，COL=00800768 offset=0，RTTI=00822438→.?AVFoggedObjectClass@@；装表点 004D088D 位于 004D0860 体内，entry 体外） ④升级句：FoggedObjectClass::slot5（④ 表属类与行名类一致，均为 FoggedObjectClass；该槽即其 vt=007E8B38 表 slot5，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段（491 B）：`；④ 活表槽位见证：FoggedObjectClass::slot5（vt=007E8B38，槽 5 值=004D2510，COL=00800768 offset=0，RTTI=00822438→.?AVFoggedObjectClass@@；装表点 004D088D 位于 004D0860 体内，entry 体外） ④升级句：FoggedObjectClass::slot5（④ 表属类与行名类一致，均为 FoggedObjectClass；该槽即其 vt=007E8B38 表 slot5，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 严格前缀：`before == after[:len(before)]` → **PASS**；其余 7 列逐字节相同 → **PASS**；改前已含字符 ④ = **是**。

### 行 11 · entry `004D27D0`

- before（原第 4 列，302 B）：`FoggedObjectClass 虚表槽 3(+0xC)：迷雾/可见性/雷达 方法（③b② 取全局 16 字节可见性配置到输出指针：入参为空返回 E_POINTER(0x80004003)、否则逐字拷贝并返回成功码〔锚 +0x8 mov eax,0x80004003 / +0x10 mov [eax],ecx / +0x33 xor eax,eax / +0x35 ret 8〕）`
- after（新第 4 列，793 B）：`FoggedObjectClass 虚表槽 3(+0xC)：迷雾/可见性/雷达 方法（③b② 取全局 16 字节可见性配置到输出指针：入参为空返回 E_POINTER(0x80004003)、否则逐字拷贝并返回成功码〔锚 +0x8 mov eax,0x80004003 / +0x10 mov [eax],ecx / +0x33 xor eax,eax / +0x35 ret 8〕）；④ 活表槽位见证：FoggedObjectClass::slot3（vt=007E8B38，槽 3 值=004D27D0，COL=00800768 offset=0，RTTI=00822438→.?AVFoggedObjectClass@@；装表点 004D088D 位于 004D0860 体内，entry 体外） ④升级句：FoggedObjectClass::slot3（④ 表属类与行名类一致，均为 FoggedObjectClass；该槽即其 vt=007E8B38 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段（491 B）：`；④ 活表槽位见证：FoggedObjectClass::slot3（vt=007E8B38，槽 3 值=004D27D0，COL=00800768 offset=0，RTTI=00822438→.?AVFoggedObjectClass@@；装表点 004D088D 位于 004D0860 体内，entry 体外） ④升级句：FoggedObjectClass::slot3（④ 表属类与行名类一致，均为 FoggedObjectClass；该槽即其 vt=007E8B38 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 严格前缀：`before == after[:len(before)]` → **PASS**；其余 7 列逐字节相同 → **PASS**；改前已含字符 ④ = **否**。

### 行 12 · entry `004D2810`

- before（原第 4 列，274 B）：`FoggedObjectClass 虚表槽 13(+0x34)：迷雾/可见性/雷达 方法（③b③ 把对象 14 个迷雾相关成员一次性登记到传入上下文、14 次互斥布局断言式调用覆盖 [esi+0x24..0x6C]〔锚 +0x14/+0x1F/…/+0xA3 call 0x4A1D50 ×14 / +0xAA ret 4〕）`
- after（新第 4 列，769 B）：`FoggedObjectClass 虚表槽 13(+0x34)：迷雾/可见性/雷达 方法（③b③ 把对象 14 个迷雾相关成员一次性登记到传入上下文、14 次互斥布局断言式调用覆盖 [esi+0x24..0x6C]〔锚 +0x14/+0x1F/…/+0xA3 call 0x4A1D50 ×14 / +0xAA ret 4〕）；④ 活表槽位见证：FoggedObjectClass::slot13（vt=007E8B38，槽 13 值=004D2810，COL=00800768 offset=0，RTTI=00822438→.?AVFoggedObjectClass@@；装表点 004D088D 位于 004D0860 体内，entry 体外） ④升级句：FoggedObjectClass::slot13（④ 表属类与行名类一致，均为 FoggedObjectClass；该槽即其 vt=007E8B38 表 slot13，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段（495 B）：`；④ 活表槽位见证：FoggedObjectClass::slot13（vt=007E8B38，槽 13 值=004D2810，COL=00800768 offset=0，RTTI=00822438→.?AVFoggedObjectClass@@；装表点 004D088D 位于 004D0860 体内，entry 体外） ④升级句：FoggedObjectClass::slot13（④ 表属类与行名类一致，均为 FoggedObjectClass；该槽即其 vt=007E8B38 表 slot13，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 严格前缀：`before == after[:len(before)]` → **PASS**；其余 7 列逐字节相同 → **PASS**；改前已含字符 ④ = **否**。

### 行 13 · entry `004D4200`

- before（原第 4 列，327 B）：`任务计时/就绪判定入口：按多道闸决定是否触发默认动作并返回 1 或随机化帧间隔。合同闭合 ③b① 多闸互斥：+0x5A4 计时路径、+0x674 空即 0x4D4217 处 push 0x80004003(E_POINTER)、vt[+0x10] 谓词、+0xB4==-1 则 vt[+0x484] 并 ret1，否则 0x65C7E0 随机段（0x4D424F 起）。`
- after（新第 4 列，794 B）：`任务计时/就绪判定入口：按多道闸决定是否触发默认动作并返回 1 或随机化帧间隔。合同闭合 ③b① 多闸互斥：+0x5A4 计时路径、+0x674 空即 0x4D4217 处 push 0x80004003(E_POINTER)、vt[+0x10] 谓词、+0xB4==-1 则 vt[+0x484] 并 ret1，否则 0x65C7E0 随机段（0x4D424F 起）。；④ 活表槽位见证：FootClass::slot139（vt=007E8C94，槽 139 值=004D4200，COL=00800948 offset=0，RTTI=00817B78→.?AVFootClass@@；装表点 004D345D 位于 004D31E0 体内，entry 体外） ④升级句：FootClass::slot139（④ 表属类与行名类一致，均为 FootClass；该槽即其 vt=007E8C94 表 slot139，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段（467 B）：`；④ 活表槽位见证：FootClass::slot139（vt=007E8C94，槽 139 值=004D4200，COL=00800948 offset=0，RTTI=00817B78→.?AVFootClass@@；装表点 004D345D 位于 004D31E0 体内，entry 体外） ④升级句：FootClass::slot139（④ 表属类与行名类一致，均为 FootClass；该槽即其 vt=007E8C94 表 slot139，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 严格前缀：`before == after[:len(before)]` → **PASS**；其余 7 列逐字节相同 → **PASS**；改前已含字符 ④ = **否**。

### 行 14 · entry `004D4280`

- before（原第 4 列，315 B）：`按任务阶段号四路跳转的调度器：阶段取自 +0xBC，经边界检查后索引跳表执行各阶段动作。合同闭合 ③b① 跳表可核：0x4D42B4 处 cmp eax,3 上界守卫、0x4D42BD 处 jmp [eax*4+0x4D4B04]；四目标全在 .text，阶段返回 0x3C(0x4D451B)/0x2D(0x4D477A) 等互斥出口。`
- after（新第 4 列，782 B）：`按任务阶段号四路跳转的调度器：阶段取自 +0xBC，经边界检查后索引跳表执行各阶段动作。合同闭合 ③b① 跳表可核：0x4D42B4 处 cmp eax,3 上界守卫、0x4D42BD 处 jmp [eax*4+0x4D4B04]；四目标全在 .text，阶段返回 0x3C(0x4D451B)/0x2D(0x4D477A) 等互斥出口。；④ 活表槽位见证：FootClass::slot151（vt=007E8C94，槽 151 值=004D4280，COL=00800948 offset=0，RTTI=00817B78→.?AVFootClass@@；装表点 004D345D 位于 004D31E0 体内，entry 体外） ④升级句：FootClass::slot151（④ 表属类与行名类一致，均为 FootClass；该槽即其 vt=007E8C94 表 slot151，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段（467 B）：`；④ 活表槽位见证：FootClass::slot151（vt=007E8C94，槽 151 值=004D4280，COL=00800948 offset=0，RTTI=00817B78→.?AVFootClass@@；装表点 004D345D 位于 004D31E0 体内，entry 体外） ④升级句：FootClass::slot151（④ 表属类与行名类一致，均为 FootClass；该槽即其 vt=007E8C94 表 slot151，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 严格前缀：`before == after[:len(before)]` → **PASS**；其余 7 列逐字节相同 → **PASS**；改前已含字符 ④ = **否**。

### 行 15 · entry `004D4B20`

- before（原第 4 列，322 B）：`飞行器任务守卫链：先按类型(WhatAmI)与关联对象多级条件过滤，再择一执行动作并随机化收尾。合同闭合 ③b① 多路互斥：0x4D4B33 取 vt[+0x2C]、0x4D4B38 处 sub edi,0xF 比类型 15、+0x2B4 的 vt[+0x2C]==6、0x70D0D0(0xE) 资格判定，四结局互斥，尾 0x65C7E0 随机。`
- after（新第 4 列，805 B）：`飞行器任务守卫链：先按类型(WhatAmI)与关联对象多级条件过滤，再择一执行动作并随机化收尾。合同闭合 ③b① 多路互斥：0x4D4B33 取 vt[+0x2C]、0x4D4B38 处 sub edi,0xF 比类型 15、+0x2B4 的 vt[+0x2C]==6、0x70D0D0(0xE) 资格判定，四结局互斥，尾 0x65C7E0 随机。；④ 活表槽位见证：AircraftClass::slot133（vt=007E22A4，槽 133 值=004D4B20，COL=007FB4C0 offset=0，RTTI=00817B90→.?AVAircraftClass@@；装表点 00413D87 位于 00413D20 体内，entry 体外） ④升级句：AircraftClass::slot133（④ 表属类与行名类一致，均为 AircraftClass；该槽即其 vt=007E22A4 表 slot133，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 追加段（483 B）：`；④ 活表槽位见证：AircraftClass::slot133（vt=007E22A4，槽 133 值=004D4B20，COL=007FB4C0 offset=0，RTTI=00817B90→.?AVAircraftClass@@；装表点 00413D87 位于 00413D20 体内，entry 体外） ④升级句：AircraftClass::slot133（④ 表属类与行名类一致，均为 AircraftClass；该槽即其 vt=007E22A4 表 slot133，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- 严格前缀：`before == after[:len(before)]` → **PASS**；其余 7 列逐字节相同 → **PASS**；改前已含字符 ④ = **否**。

## 3 · 8 项验证结果与实测数字

| 项 | 结果 | 关键实测 |
|---|---|---|
| V1_coverage_byte_restore | PASS | 重建 sha=2bca3846，改前 sha=2bca3846，与备份字节相等=True |
| V2_invariants | PASS | 18,498 行 / {8:18498} / [已证]1654 / atlas内1648 / 外6 / 15行grade=[已证] |
| V3_only_15_col4 | PASS | 差异行=15（恰 15），entry 集合匹配=True，仅第4列不同 |
| V4_strict_prefix | PASS | 15/15 逐行严格前缀 PASS |
| V5_circled4_chengwen | FAIL(实测偏差，已查清) | 改前 319 → 改后 328（卡面预期 334）；改前已含 ④ 的 6 行不增，净增 9 行 |
| V6_panel_restore | PASS | 重建 sha=ef600f02，改前 sha=ef600f02，删除插入块+回改指针后字节相等=True |
| V7_dod_no_flip | PASS | 名义=S15,S16,S17 严格=S17（rc=0） |
| V8_line_endings | PASS | coverage LF 18498→18498，PANEL LF 599→607，无 CRLF 混用；字节增量 cov=7613 / panel=823 与追加/插入吻合 |

### V5 ④ 已成文计数偏差说明（卡面 §4.5「若不符，报实测值并查清」）

按卡面口径([已证]且col4含字符 ④)实测改前319、改后328；卡面预期334(+15)未达成。原因：15行中有6行改前col4已含字符 ④(位于原文'合同闭合 ③b④'分类标签)，改后仍含该字符故计数不增；仅其余9行净新增。319+9=328。

> 处置：PANEL.md 的 M86 披露按卡面 §3.2(b) 逐字写入「319 / 1,654（19.29%）升至 334 / 1,654（20.19%）」；
> 本验证报告与回复如实给出实测 319 → 328 及原因。该偏差交由 lead 裁量是否需在后续轮次修正披露数字。

## 4 · 还原性与不变量明细

- 改前 sha（coverage）= `2bca384650ac31bcfc9661280a1863c2d51c6548b96f5ee372de94edda8104a6`；把 15 行第 4 列换回后重建 sha = `2bca3846` → **一致**。
- 改前 sha（PANEL）= `ef600f025b63a2cd3d4418e5030e6f66a4cf452ed6abcf3d9ea9887692dc3bc9`；删除 M86 插入块并把指针回改后重建 sha = `ef600f02` → **一致**。
- 达标复算：复制 `strict_panel.py` 到本目录 `strict_panel_local.py`，仅把 `OUT` 重定向到 `strict_out`（口径不变），输出未写原目录。
