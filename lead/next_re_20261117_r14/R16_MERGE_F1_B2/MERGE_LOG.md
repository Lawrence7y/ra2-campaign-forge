# R16-MERGE-F1 B2 合并日志

> 角色：合并员（唯一写者）· 批次 B2 = 派生集合第 19–36 行 · PANEL 披露编号 M90
> 审计裁决：`R16_AUDIT_F1_B2/VERDICT.md` = PASS 18 / FAIL 0 / 必改 0（已确认）

## 0. 两份文件改前 → 改后

| 文件 | mtime | bytes | sha256 | 行数(LF) | 行尾 |
|---|---|---|---:|---:|---|
| coverage.tsv BEFORE | 2026-11-21 00:03:28 | 4,049,509 | `bb62a995447a5d87c9a03adcae99e348e08b480bce6e9a368973543ba47f01f2` | 18498 | LF-only(CRLF=0) |
| coverage.tsv AFTER  | 2026-11-21 00:13:54 | 4,058,895 | `6428b4eb06280bd56c250cc1156e0b24a72e6bc4a11b5e9fd17e500718642d5f` | 18498 | LF-only(CRLF=0) |
| PANEL.md BEFORE | 2026-11-21 00:03:28 | 170,502 | `7f64c083f5bbdf7143812e37dc5e17601044aab337a0a01d92d908a4be4b7ab4` | 631 | LF-only(CRLF=0) |
| PANEL.md AFTER  | 2026-11-21 00:13:54 | 172,885 | `755767162376f1aee3b93b9089d8df05cd77b342425d0c186a12e271c317f168` | 638 | LF-only(CRLF=0) |

覆盖行：`coverage.tsv` 第 4 列（one_line_semantics），18 行；PANEL.md 第 246–252 行插入 1 条 M90 披露（紧接 M89 块之后）。

## 1. 18 行第 4 列 before / after（完整文本）

每行的改前第 4 列 ≡ 盘上原值；改后第 4 列 = 改前原值 + 追加段（严格前缀 18/18，追加段均以 `；④ 活表槽位见证` 起，含 §12.6 不含 §12.4）。
grade 第 5 列保持 `[已证]`，其余 7 列逐字节不变。

### 1. 005FEAF0（+315 字节）

**before 第4列：**
```text
OverlayTypeClass 虚槽5（流读入）：以 0x5f9720→0x410380 校验流并整体读入 OverlayType；空/失败返负 HRESULT 原样早退，成功则装 vt 0x7ef600 并逐字段读入后返 0。
```

**after 第4列：**
```text
OverlayTypeClass 虚槽5（流读入）：以 0x5f9720→0x410380 校验流并整体读入 OverlayType；空/失败返负 HRESULT 原样早退，成功则装 vt 0x7ef600 并逐字段读入后返 0。；④ 活表槽位见证：OverlayTypeClass::slot5（vt=007EF600，槽 5 值=005FEAF0，COL=008076F0 offset=0，RTTI=008334B0→.?AVOverlayTypeClass@@；装表点 005FE2F1 位于 005FE250 体内，entry 体外） ④升级句：OverlayTypeClass::slot5（④ 表属类与行名类一致，均为 OverlayTypeClass；该槽即其 vt=007EF600 表 slot5，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

追加段：`；④ 活表槽位见证：OverlayTypeClass::slot5（vt=007EF600，槽 5 值=005FEAF0，COL=008076F0 offset…`

### 2. 00629FD0（+307 字节）

**before 第4列：**
```text
ParasiteClass 分配并初始化寄生体：operator new 分配，失败（NULL）跳过初始化，成功则用返回指针构造；③b② 的分配空指针返回约定由 test/je 分支消费。
```

**after 第4列：**
```text
ParasiteClass 分配并初始化寄生体：operator new 分配，失败（NULL）跳过初始化，成功则用返回指针构造；③b② 的分配空指针返回约定由 test/je 分支消费。；④ 活表槽位见证：ParasiteClass::slot23（vt=007EF890，槽 23 值=00629FD0，COL=00807B30 offset=0，RTTI=00836640→.?AVParasiteClass@@；装表点 00629231 位于 00629210 体内，entry 体外） ④升级句：ParasiteClass::slot23（④ 表属类与行名类一致，均为 ParasiteClass；该槽即其 vt=007EF890 表 slot23，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

追加段：`；④ 活表槽位见证：ParasiteClass::slot23（vt=007EF890，槽 23 值=00629FD0，COL=00807B30 offset=…`

### 3. 0062D7A0（+303 字节）

**before 第4列：**
```text
ParticleClass::slot5 —— ③b② 成立（流**读入**构造）：站点 `0062D7AB e8d086fcff call 0x5F5E80`，该 helper 首条即 `005F5E8B e8f0a4e1ff call 0x410380`（流读封装，内部 `0041039E ff500c` 走 **+0xC = Read**），其失败路径 `005F5E92 7c65 jl 0x5F5EF9` 原样抛出（空指针时 `00410389 b803400080 mov eax,0x80004003` = E_POINTER）；零间隔 `0062D7B0 85c0 test eax,eax` / `0062D7B2 7c4f jl 0x62D803`（无 eax 覆写）——失败路直接收尾返错误码，成功路真做别的事：`0062D7BF call 0x5F3B50` 构造基类、`0062D7C4 c70654f97e00` 等 4 条装 0x7EF954/0x7EF938/0x7EF930/0x7EF928、`0062D7EB`/`0062D7FC` 两次 `0x6CF240` 构造 [+0xAC] 与 [+0x124] 成员、`0062D801 33c0` 返 0。语义：ParticleClass 流读入构造——先经 0x5F5E80 从流读入并对 5 个成员做读入构造，失败原样返回错误码；成功则构造基类、装 4 表、再构造两个成员对象，返 0。② 槽 007EF968（vt 007EF954 +0x14，slot#5）4B 值 = 本 entry，COL=00807BE8(sig=0)→TD=008366E8→`.?AVParticleClass@@`；④ 0062B767（in_func=0062B5E0，宿主 0062B5E9 `call 0x5F3900` 基类构造后装表，atexit=False、行外；行内 0062D7C4 自身装表已排除）。
```

**after 第4列：**
```text
ParticleClass::slot5 —— ③b② 成立（流**读入**构造）：站点 `0062D7AB e8d086fcff call 0x5F5E80`，该 helper 首条即 `005F5E8B e8f0a4e1ff call 0x410380`（流读封装，内部 `0041039E ff500c` 走 **+0xC = Read**），其失败路径 `005F5E92 7c65 jl 0x5F5EF9` 原样抛出（空指针时 `00410389 b803400080 mov eax,0x80004003` = E_POINTER）；零间隔 `0062D7B0 85c0 test eax,eax` / `0062D7B2 7c4f jl 0x62D803`（无 eax 覆写）——失败路直接收尾返错误码，成功路真做别的事：`0062D7BF call 0x5F3B50` 构造基类、`0062D7C4 c70654f97e00` 等 4 条装 0x7EF954/0x7EF938/0x7EF930/0x7EF928、`0062D7EB`/`0062D7FC` 两次 `0x6CF240` 构造 [+0xAC] 与 [+0x124] 成员、`0062D801 33c0` 返 0。语义：ParticleClass 流读入构造——先经 0x5F5E80 从流读入并对 5 个成员做读入构造，失败原样返回错误码；成功则构造基类、装 4 表、再构造两个成员对象，返 0。② 槽 007EF968（vt 007EF954 +0x14，slot#5）4B 值 = 本 entry，COL=00807BE8(sig=0)→TD=008366E8→`.?AVParticleClass@@`；④ 0062B767（in_func=0062B5E0，宿主 0062B5E9 `call 0x5F3900` 基类构造后装表，atexit=False、行外；行内 0062D7C4 自身装表已排除）。；④ 活表槽位见证：ParticleClass::slot5（vt=007EF954，槽 5 值=0062D7A0，COL=00807BE8 offset=0，RTTI=008366E8→.?AVParticleClass@@；装表点 0062B767 位于 0062B5E0 体内，entry 体外） ④升级句：ParticleClass::slot5（④ 表属类与行名类一致，均为 ParticleClass；该槽即其 vt=007EF954 表 slot5，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

追加段：`；④ 活表槽位见证：ParticleClass::slot5（vt=007EF954，槽 5 值=0062D7A0，COL=00807BE8 offset=0，…`

### 4. 0062D9A0（+303 字节）

**before 第4列：**
```text
ParticleClass::slot8 —— ③b② 标量删除析构：从 DynamicVectorClass<ParticleClass*>（全局注册容器 0xA83DC8 / 计数 0xA83DD8 / 数组 0xA83DCC）里 Find 自身，未命中返 -1 直接跳过、命中则计数减一并前移压缩数组摘链，随后 call 0x5F3B80 基类析构，按 `test byte [esp+0xC],1` 的 delete 标志 call 0x7C8B3D 释放自身。② 槽 007EF974（vt 007EF954+0x20，slot#8）4B 值=本 entry，COL=00807BE8→TD=008366E8→`.?AVParticleClass@@`；④ 0062B767（构造器 0062B5E0，首条 0062B5E9 call 0x5F3900 基类构造后装表，atexit=False、行外；行内 0062D9A4 已排除）。
```

**after 第4列：**
```text
ParticleClass::slot8 —— ③b② 标量删除析构：从 DynamicVectorClass<ParticleClass*>（全局注册容器 0xA83DC8 / 计数 0xA83DD8 / 数组 0xA83DCC）里 Find 自身，未命中返 -1 直接跳过、命中则计数减一并前移压缩数组摘链，随后 call 0x5F3B80 基类析构，按 `test byte [esp+0xC],1` 的 delete 标志 call 0x7C8B3D 释放自身。② 槽 007EF974（vt 007EF954+0x20，slot#8）4B 值=本 entry，COL=00807BE8→TD=008366E8→`.?AVParticleClass@@`；④ 0062B767（构造器 0062B5E0，首条 0062B5E9 call 0x5F3900 基类构造后装表，atexit=False、行外；行内 0062D9A4 已排除）。；④ 活表槽位见证：ParticleClass::slot8（vt=007EF954，槽 8 值=0062D9A0，COL=00807BE8 offset=0，RTTI=008366E8→.?AVParticleClass@@；装表点 0062B767 位于 0062B5E0 体内，entry 体外） ④升级句：ParticleClass::slot8（④ 表属类与行名类一致，均为 ParticleClass；该槽即其 vt=007EF954 表 slot8，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

追加段：`；④ 活表槽位见证：ParticleClass::slot8（vt=007EF954，槽 8 值=0062D9A0，COL=00807BE8 offset=0，…`

### 5. 0062FE90（+331 字节）

**before 第4列：**
```text
ParticleSystemClass::slot10 —— ③b② 成员容器摘链：先 call 0x5F5230，再在 this 内嵌 DynamicVectorClass（[this+0xBC]，vtable 007E9D64）里按参数 Find（未命中 -1 跳过、命中则 dec 计数并前移压缩数组 mov [ecx+eax*4-4],edx + jl 回边）；随后复位 [this+0xAC]/[this+0xE4]/[this+0xE0] 并置 [this+0xF8]=1。容器 vtable 由 0062E244 `mov dword [edi+0xBC],0x7E9D64` 装入，vt[#4]=004E9F00 处 `or eax,-1` + `ret 4` 可伪证。② 槽 007EFBC4（vt 007EFB9C+0x28，slot#10）4B 值=本 entry，COL=00807CA0→TD=00836748→`.?AVParticleSystemClass@@`；④ 0062DD16（构造器 0062DC50，首条 0062DC59 call 0x5F3900 基类构造后装表，atexit=False、行外）。
```

**after 第4列：**
```text
ParticleSystemClass::slot10 —— ③b② 成员容器摘链：先 call 0x5F5230，再在 this 内嵌 DynamicVectorClass（[this+0xBC]，vtable 007E9D64）里按参数 Find（未命中 -1 跳过、命中则 dec 计数并前移压缩数组 mov [ecx+eax*4-4],edx + jl 回边）；随后复位 [this+0xAC]/[this+0xE4]/[this+0xE0] 并置 [this+0xF8]=1。容器 vtable 由 0062E244 `mov dword [edi+0xBC],0x7E9D64` 装入，vt[#4]=004E9F00 处 `or eax,-1` + `ret 4` 可伪证。② 槽 007EFBC4（vt 007EFB9C+0x28，slot#10）4B 值=本 entry，COL=00807CA0→TD=00836748→`.?AVParticleSystemClass@@`；④ 0062DD16（构造器 0062DC50，首条 0062DC59 call 0x5F3900 基类构造后装表，atexit=False、行外）。；④ 活表槽位见证：ParticleSystemClass::slot10（vt=007EFB9C，槽 10 值=0062FE90，COL=00807CA0 offset=0，RTTI=00836748→.?AVParticleSystemClass@@；装表点 0062DD16 位于 0062DC50 体内，entry 体外） ④升级句：ParticleSystemClass::slot10（④ 表属类与行名类一致，均为 ParticleSystemClass；该槽即其 vt=007EFB9C 表 slot10，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

追加段：`；④ 活表槽位见证：ParticleSystemClass::slot10（vt=007EFB9C，槽 10 值=0062FE90，COL=00807CA0 o…`

### 6. 00630090（+327 字节）

**before 第4列：**
```text
ParticleSystemClass::slot6 —— ③b② 流写出（方向已按槽位复算，**写出**）：call 0x410320 把头部写到流（该封装内部 00410348/0041035E `call [eax+0x10]` 走 Write；空参 0041032B 返 E_POINTER 0x80004003）；`test eax,eax`/`jl` 零间隔——失败路跳 0x6300F3 原样带错误码收尾，成功路真做别的事：按 [edi+0xCC] 计数，对每个元素 call [ecx+0x10] 逐条写出（006300D2 循环 + 006300F1 cmp + 006300F5 jl 回边），任一失败同样跳出。② 槽 007EFBB4（vt 007EFB9C+0x18，slot#6）4B 值=本 entry，COL=00807CA0→TD=00836748→`.?AVParticleSystemClass@@`；④ 0062DD16（构造器 0062DC50，首条 0062DC59 call 0x5F3900 基类构造后装表，atexit=False、行外）。
```

**after 第4列：**
```text
ParticleSystemClass::slot6 —— ③b② 流写出（方向已按槽位复算，**写出**）：call 0x410320 把头部写到流（该封装内部 00410348/0041035E `call [eax+0x10]` 走 Write；空参 0041032B 返 E_POINTER 0x80004003）；`test eax,eax`/`jl` 零间隔——失败路跳 0x6300F3 原样带错误码收尾，成功路真做别的事：按 [edi+0xCC] 计数，对每个元素 call [ecx+0x10] 逐条写出（006300D2 循环 + 006300F1 cmp + 006300F5 jl 回边），任一失败同样跳出。② 槽 007EFBB4（vt 007EFB9C+0x18，slot#6）4B 值=本 entry，COL=00807CA0→TD=00836748→`.?AVParticleSystemClass@@`；④ 0062DD16（构造器 0062DC50，首条 0062DC59 call 0x5F3900 基类构造后装表，atexit=False、行外）。；④ 活表槽位见证：ParticleSystemClass::slot6（vt=007EFB9C，槽 6 值=00630090，COL=00807CA0 offset=0，RTTI=00836748→.?AVParticleSystemClass@@；装表点 0062DD16 位于 0062DC50 体内，entry 体外） ④升级句：ParticleSystemClass::slot6（④ 表属类与行名类一致，均为 ParticleSystemClass；该槽即其 vt=007EFB9C 表 slot6，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

追加段：`；④ 活表槽位见证：ParticleSystemClass::slot6（vt=007EFB9C，槽 6 值=00630090，COL=00807CA0 off…`

### 7. 00644960（+343 字节）

**before 第4列：**
```text
ParticleSystemTypeClass::slot8 —— ③b② 标量删除析构：复位 4 张虚表、call 0x7258D0 解引用后，在 DynamicVectorClass<ParticleSystemTypeClass*>（0xA83D68 / 计数 0xA83D78 / 数组 0xA83D6C）里 Find 自身，未命中 -1 跳过、命中则计数减一并前移压缩数组摘链（jl 回边）；随后 call 0x5F7400 基类析构，按 test byte [esp+0xC],1 的 delete 标志 call 0x7C8B3D 释放。② 槽 007F00C8（vt 007F00A8+0x20，slot#8）4B 值=本 entry，COL=00808238→TD=00836F18→`.?AVParticleSystemTypeClass@@`；④ 0064419C（构造器 006440A0，首条 006440A9 call 0x5F7090 基类构造后装表，atexit=False、行外；行内 00644966 已排除）。
```

**after 第4列：**
```text
ParticleSystemTypeClass::slot8 —— ③b② 标量删除析构：复位 4 张虚表、call 0x7258D0 解引用后，在 DynamicVectorClass<ParticleSystemTypeClass*>（0xA83D68 / 计数 0xA83D78 / 数组 0xA83D6C）里 Find 自身，未命中 -1 跳过、命中则计数减一并前移压缩数组摘链（jl 回边）；随后 call 0x5F7400 基类析构，按 test byte [esp+0xC],1 的 delete 标志 call 0x7C8B3D 释放。② 槽 007F00C8（vt 007F00A8+0x20，slot#8）4B 值=本 entry，COL=00808238→TD=00836F18→`.?AVParticleSystemTypeClass@@`；④ 0064419C（构造器 006440A0，首条 006440A9 call 0x5F7090 基类构造后装表，atexit=False、行外；行内 00644966 已排除）。；④ 活表槽位见证：ParticleSystemTypeClass::slot8（vt=007F00A8，槽 8 值=00644960，COL=00808238 offset=0，RTTI=00836F18→.?AVParticleSystemTypeClass@@；装表点 0064419C 位于 006440A0 体内，entry 体外） ④升级句：ParticleSystemTypeClass::slot8（④ 表属类与行名类一致，均为 ParticleSystemTypeClass；该槽即其 vt=007F00A8 表 slot8，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

追加段：`；④ 活表槽位见证：ParticleSystemTypeClass::slot8（vt=007F00A8，槽 8 值=00644960，COL=00808238…`

### 8. 006457A0（+319 字节）

**before 第4列：**
```text
ParticleTypeClass::slot6 —— ③b② 流写出（**写出**，方向按槽位复算）：call 0x5F9950（内部 0x410320 走流虚表 +0x10 Write；空参 E_POINTER 0x80004003，负返回原样/非负归零）；`test eax,eax`/`jl` 零间隔——失败路跳 0x64580A 带错误码收尾，成功路真做事：按 [ebx+0x2C8] 做一次容器写出（call [edx+0x10]），再按计数把 [ebx+0x2BC] 数组每 3 字节 call [ecx+0x10] 逐条写出（`add edi,3`/`cmp`/`jl` 回边），任一失败跳出。② 槽 007F01A0（vt 007F0188+0x18，slot#6）4B 值=本 entry，COL=008082F0→TD=008370D0→`.?AVParticleTypeClass@@`；④ 00644CF4（构造器 00644BE0，首条 00644BEB call 0x5F7090 基类构造后装表，atexit=False、行外）。
```

**after 第4列：**
```text
ParticleTypeClass::slot6 —— ③b② 流写出（**写出**，方向按槽位复算）：call 0x5F9950（内部 0x410320 走流虚表 +0x10 Write；空参 E_POINTER 0x80004003，负返回原样/非负归零）；`test eax,eax`/`jl` 零间隔——失败路跳 0x64580A 带错误码收尾，成功路真做事：按 [ebx+0x2C8] 做一次容器写出（call [edx+0x10]），再按计数把 [ebx+0x2BC] 数组每 3 字节 call [ecx+0x10] 逐条写出（`add edi,3`/`cmp`/`jl` 回边），任一失败跳出。② 槽 007F01A0（vt 007F0188+0x18，slot#6）4B 值=本 entry，COL=008082F0→TD=008370D0→`.?AVParticleTypeClass@@`；④ 00644CF4（构造器 00644BE0，首条 00644BEB call 0x5F7090 基类构造后装表，atexit=False、行外）。；④ 活表槽位见证：ParticleTypeClass::slot6（vt=007F0188，槽 6 值=006457A0，COL=008082F0 offset=0，RTTI=008370D0→.?AVParticleTypeClass@@；装表点 00644CF4 位于 00644BE0 体内，entry 体外） ④升级句：ParticleTypeClass::slot6（④ 表属类与行名类一致，均为 ParticleTypeClass；该槽即其 vt=007F0188 表 slot6，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

追加段：`；④ 活表槽位见证：ParticleTypeClass::slot6（vt=007F0188，槽 6 值=006457A0，COL=008082F0 offse…`

### 9. 00645950（+319 字节）

**before 第4列：**
```text
ParticleTypeClass::slot8 —— ③b② 标量删除析构（双注册表）：复位 4 表后，在 DynamicVectorClass<ParticleTypeClass*>（0xB0F670，计数 0xB0F680/数组 0xB0F674）与（0xA83D98，计数 0xA83DA8/数组 0xA83D9C）两个注册表各 Find 自身——未命中 -1 跳过、命中则计数减一并前移压缩数组摘链（各自 jl 回边）；随后清 [this+0x2B8]=0x7E4E38、按需 free [this+0x2BC]，call 0x5F7400 基类析构，按 delete 标志 call 0x7C8B3D 释放。② 槽 007F01A8（vt 007F0188+0x20，slot#8）4B 值=本 entry，COL=008082F0→TD=008370D0→`.?AVParticleTypeClass@@`；④ 00644CF4（构造器 00644BE0，首条 00644BEB call 0x5F7090 基类构造后装表，atexit=False、行外；行内 00645956 已排除）。
```

**after 第4列：**
```text
ParticleTypeClass::slot8 —— ③b② 标量删除析构（双注册表）：复位 4 表后，在 DynamicVectorClass<ParticleTypeClass*>（0xB0F670，计数 0xB0F680/数组 0xB0F674）与（0xA83D98，计数 0xA83DA8/数组 0xA83D9C）两个注册表各 Find 自身——未命中 -1 跳过、命中则计数减一并前移压缩数组摘链（各自 jl 回边）；随后清 [this+0x2B8]=0x7E4E38、按需 free [this+0x2BC]，call 0x5F7400 基类析构，按 delete 标志 call 0x7C8B3D 释放。② 槽 007F01A8（vt 007F0188+0x20，slot#8）4B 值=本 entry，COL=008082F0→TD=008370D0→`.?AVParticleTypeClass@@`；④ 00644CF4（构造器 00644BE0，首条 00644BEB call 0x5F7090 基类构造后装表，atexit=False、行外；行内 00645956 已排除）。；④ 活表槽位见证：ParticleTypeClass::slot8（vt=007F0188，槽 8 值=00645950，COL=008082F0 offset=0，RTTI=008370D0→.?AVParticleTypeClass@@；装表点 00644CF4 位于 00644BE0 体内，entry 体外） ④升级句：ParticleTypeClass::slot8（④ 表属类与行名类一致，均为 ParticleTypeClass；该槽即其 vt=007F0188 表 slot8，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

追加段：`；④ 活表槽位见证：ParticleTypeClass::slot8（vt=007F0188，槽 8 值=00645950，COL=008082F0 offse…`

### 10. 006B5850（+311 字节）

**before 第4列：**
```text
SmudgeTypeClass 虚槽5（流读入）：以 0x5f9720→0x410380 校验流并整体读入 SmudgeType；失败返负 HRESULT 原样早退，成功装 vt 0x7f3528 并读入后返 0。
```

**after 第4列：**
```text
SmudgeTypeClass 虚槽5（流读入）：以 0x5f9720→0x410380 校验流并整体读入 SmudgeType；失败返负 HRESULT 原样早退，成功装 vt 0x7f3528 并读入后返 0。；④ 活表槽位见证：SmudgeTypeClass::slot5（vt=007F3528，槽 5 值=006B5850，COL=008099A0 offset=0，RTTI=00840008→.?AVSmudgeTypeClass@@；装表点 006B529B 位于 006B5260 体内，entry 体外） ④升级句：SmudgeTypeClass::slot5（④ 表属类与行名类一致，均为 SmudgeTypeClass；该槽即其 vt=007F3528 表 slot5，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

追加段：`；④ 活表槽位见证：SmudgeTypeClass::slot5（vt=007F3528，槽 5 值=006B5850，COL=008099A0 offset=…`

### 11. 006C2B10（+395 字节）

**before 第4列：**
```text
S22 T_TClassFactory_VAircraftTypeClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C2B1B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C2B6F `call dword ptr [eax]`（新建 AircraftTypeClass 对象主 vt 007E2868 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C2B71 `mov edi,eax`/`test edi,edi`/`jge 0x6c2b80`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C2B7D `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 AircraftTypeClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 AircraftTypeClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3B34(vt 007F3B28 +12，slot#3) 4B 值即本 entry，RTTI COL=0080A8E8→TD=00841748→名=.?AV?$TClassFactory@VAircraftTypeClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C2A40 装 vt 007F3B28→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**after 第4列：**
```text
S22 T_TClassFactory_VAircraftTypeClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C2B1B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C2B6F `call dword ptr [eax]`（新建 AircraftTypeClass 对象主 vt 007E2868 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C2B71 `mov edi,eax`/`test edi,edi`/`jge 0x6c2b80`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C2B7D `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 AircraftTypeClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 AircraftTypeClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3B34(vt 007F3B28 +12，slot#3) 4B 值即本 entry，RTTI COL=0080A8E8→TD=00841748→名=.?AV?$TClassFactory@VAircraftTypeClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C2A40 装 vt 007F3B28→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。；④ 活表槽位见证：T_TClassFactory_VAircraftTypeClass__::slot3（vt=007F3B28，槽 3 值=006C2B10，COL=0080A8E8 offset=0，RTTI=00841748→.?AV?$TClassFactory@VAircraftTypeClass@@@@；装表点 006C2A49 位于 006C2A40 体内，entry 体外） ④升级句：T_TClassFactory_VAircraftTypeClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VAircraftTypeClass__；该槽即其 vt=007F3B28 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

追加段：`；④ 活表槽位见证：T_TClassFactory_VAircraftTypeClass__::slot3（vt=007F3B28，槽 3 值=006C2B10…`

### 12. 006C2C90（+395 字节）

**before 第4列：**
```text
S22 T_TClassFactory_VInfantryTypeClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C2C9B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C2CEF `call dword ptr [eax]`（新建 InfantryTypeClass 对象主 vt 007EB610 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C2CF1 `mov edi,eax`/`test edi,edi`/`jge 0x6c2d00`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C2CFD `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 InfantryTypeClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 InfantryTypeClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3B4C(vt 007F3B40 +12，slot#3) 4B 值即本 entry，RTTI COL=0080A938→TD=00841780→名=.?AV?$TClassFactory@VInfantryTypeClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C2BC0 装 vt 007F3B40→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**after 第4列：**
```text
S22 T_TClassFactory_VInfantryTypeClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C2C9B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C2CEF `call dword ptr [eax]`（新建 InfantryTypeClass 对象主 vt 007EB610 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C2CF1 `mov edi,eax`/`test edi,edi`/`jge 0x6c2d00`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C2CFD `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 InfantryTypeClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 InfantryTypeClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3B4C(vt 007F3B40 +12，slot#3) 4B 值即本 entry，RTTI COL=0080A938→TD=00841780→名=.?AV?$TClassFactory@VInfantryTypeClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C2BC0 装 vt 007F3B40→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。；④ 活表槽位见证：T_TClassFactory_VInfantryTypeClass__::slot3（vt=007F3B40，槽 3 值=006C2C90，COL=0080A938 offset=0，RTTI=00841780→.?AV?$TClassFactory@VInfantryTypeClass@@@@；装表点 006C2BC9 位于 006C2BC0 体内，entry 体外） ④升级句：T_TClassFactory_VInfantryTypeClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VInfantryTypeClass__；该槽即其 vt=007F3B40 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

追加段：`；④ 活表槽位见证：T_TClassFactory_VInfantryTypeClass__::slot3（vt=007F3B40，槽 3 值=006C2C90…`

### 13. 006C2E10（+387 字节）

**before 第4列：**
```text
S22 T_TClassFactory_VBulletTypeClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C2E1B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C2E6F `call dword ptr [eax]`（新建 BulletTypeClass 对象主 vt 007E4948 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C2E71 `mov edi,eax`/`test edi,edi`/`jge 0x6c2e80`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C2E7D `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 BulletTypeClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 BulletTypeClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3B64(vt 007F3B58 +12，slot#3) 4B 值即本 entry，RTTI COL=0080A988→TD=008417B8→名=.?AV?$TClassFactory@VBulletTypeClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C2D40 装 vt 007F3B58→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**after 第4列：**
```text
S22 T_TClassFactory_VBulletTypeClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C2E1B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C2E6F `call dword ptr [eax]`（新建 BulletTypeClass 对象主 vt 007E4948 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C2E71 `mov edi,eax`/`test edi,edi`/`jge 0x6c2e80`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C2E7D `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 BulletTypeClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 BulletTypeClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3B64(vt 007F3B58 +12，slot#3) 4B 值即本 entry，RTTI COL=0080A988→TD=008417B8→名=.?AV?$TClassFactory@VBulletTypeClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C2D40 装 vt 007F3B58→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。；④ 活表槽位见证：T_TClassFactory_VBulletTypeClass__::slot3（vt=007F3B58，槽 3 值=006C2E10，COL=0080A988 offset=0，RTTI=008417B8→.?AV?$TClassFactory@VBulletTypeClass@@@@；装表点 006C2D49 位于 006C2D40 体内，entry 体外） ④升级句：T_TClassFactory_VBulletTypeClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VBulletTypeClass__；该槽即其 vt=007F3B58 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

追加段：`；④ 活表槽位见证：T_TClassFactory_VBulletTypeClass__::slot3（vt=007F3B58，槽 3 值=006C2E10，C…`

### 14. 006C2F90（+415 字节）

**before 第4列：**
```text
S22 T_TClassFactory_VIsometricTileTypeClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C2F9B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C2FF7 `call dword ptr [eax]`（新建 IsometricTileTypeClass 对象主 vt 007ECC48 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C2FF9 `mov edi,eax`/`test edi,edi`/`jge 0x6c3008`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C3005 `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 IsometricTileTypeClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 IsometricTileTypeClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3B7C(vt 007F3B70 +12，slot#3) 4B 值即本 entry，RTTI COL=0080A9D8→TD=008417F0→名=.?AV?$TClassFactory@VIsometricTileTypeClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C2EC0 装 vt 007F3B70→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**after 第4列：**
```text
S22 T_TClassFactory_VIsometricTileTypeClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C2F9B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C2FF7 `call dword ptr [eax]`（新建 IsometricTileTypeClass 对象主 vt 007ECC48 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C2FF9 `mov edi,eax`/`test edi,edi`/`jge 0x6c3008`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C3005 `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 IsometricTileTypeClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 IsometricTileTypeClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3B7C(vt 007F3B70 +12，slot#3) 4B 值即本 entry，RTTI COL=0080A9D8→TD=008417F0→名=.?AV?$TClassFactory@VIsometricTileTypeClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C2EC0 装 vt 007F3B70→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。；④ 活表槽位见证：T_TClassFactory_VIsometricTileTypeClass__::slot3（vt=007F3B70，槽 3 值=006C2F90，COL=0080A9D8 offset=0，RTTI=008417F0→.?AV?$TClassFactory@VIsometricTileTypeClass@@@@；装表点 006C2EC9 位于 006C2EC0 体内，entry 体外） ④升级句：T_TClassFactory_VIsometricTileTypeClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VIsometricTileTypeClass__；该槽即其 vt=007F3B70 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

追加段：`；④ 活表槽位见证：T_TClassFactory_VIsometricTileTypeClass__::slot3（vt=007F3B70，槽 3 值=006…`

### 15. 006C3110（+391 字节）

**before 第4列：**
```text
S22 T_TClassFactory_VOverlayTypeClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C311B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C316F `call dword ptr [eax]`（新建 OverlayTypeClass 对象主 vt 007EF600 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C3171 `mov edi,eax`/`test edi,edi`/`jge 0x6c3180`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C317D `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 OverlayTypeClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 OverlayTypeClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3B94(vt 007F3B88 +12，slot#3) 4B 值即本 entry，RTTI COL=0080AA28→TD=00841828→名=.?AV?$TClassFactory@VOverlayTypeClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C3040 装 vt 007F3B88→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**after 第4列：**
```text
S22 T_TClassFactory_VOverlayTypeClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C311B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C316F `call dword ptr [eax]`（新建 OverlayTypeClass 对象主 vt 007EF600 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C3171 `mov edi,eax`/`test edi,edi`/`jge 0x6c3180`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C317D `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 OverlayTypeClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 OverlayTypeClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3B94(vt 007F3B88 +12，slot#3) 4B 值即本 entry，RTTI COL=0080AA28→TD=00841828→名=.?AV?$TClassFactory@VOverlayTypeClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C3040 装 vt 007F3B88→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。；④ 活表槽位见证：T_TClassFactory_VOverlayTypeClass__::slot3（vt=007F3B88，槽 3 值=006C3110，COL=0080AA28 offset=0，RTTI=00841828→.?AV?$TClassFactory@VOverlayTypeClass@@@@；装表点 006C3049 位于 006C3040 体内，entry 体外） ④升级句：T_TClassFactory_VOverlayTypeClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VOverlayTypeClass__；该槽即其 vt=007F3B88 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

追加段：`；④ 活表槽位见证：T_TClassFactory_VOverlayTypeClass__::slot3（vt=007F3B88，槽 3 值=006C3110，…`

### 16. 006C3290（+387 字节）

**before 第4列：**
```text
S22 T_TClassFactory_VSmudgeTypeClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C329B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C32EF `call dword ptr [eax]`（新建 SmudgeTypeClass 对象主 vt 007F3528 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C32F1 `mov edi,eax`/`test edi,edi`/`jge 0x6c3300`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C32FD `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 SmudgeTypeClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 SmudgeTypeClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3BAC(vt 007F3BA0 +12，slot#3) 4B 值即本 entry，RTTI COL=0080AA78→TD=00841860→名=.?AV?$TClassFactory@VSmudgeTypeClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C31C0 装 vt 007F3BA0→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**after 第4列：**
```text
S22 T_TClassFactory_VSmudgeTypeClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C329B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C32EF `call dword ptr [eax]`（新建 SmudgeTypeClass 对象主 vt 007F3528 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C32F1 `mov edi,eax`/`test edi,edi`/`jge 0x6c3300`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C32FD `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 SmudgeTypeClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 SmudgeTypeClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3BAC(vt 007F3BA0 +12，slot#3) 4B 值即本 entry，RTTI COL=0080AA78→TD=00841860→名=.?AV?$TClassFactory@VSmudgeTypeClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C31C0 装 vt 007F3BA0→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。；④ 活表槽位见证：T_TClassFactory_VSmudgeTypeClass__::slot3（vt=007F3BA0，槽 3 值=006C3290，COL=0080AA78 offset=0，RTTI=00841860→.?AV?$TClassFactory@VSmudgeTypeClass@@@@；装表点 006C31C9 位于 006C31C0 体内，entry 体外） ④升级句：T_TClassFactory_VSmudgeTypeClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VSmudgeTypeClass__；该槽即其 vt=007F3BA0 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

追加段：`；④ 活表槽位见证：T_TClassFactory_VSmudgeTypeClass__::slot3（vt=007F3BA0，槽 3 值=006C3290，C…`

### 17. 006C3410（+363 字节）

**before 第4列：**
```text
S22 T_TClassFactory_VUnitClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C341B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C3471 `call dword ptr [eax]`（新建 UnitClass 对象主 vt 007F5C70 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C3473 `mov edi,eax`/`test edi,edi`/`jge 0x6c3482`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C347F `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 UnitClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 UnitClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3BC4(vt 007F3BB8 +12，slot#3) 4B 值即本 entry，RTTI COL=0080AAC8→TD=00841898→名=.?AV?$TClassFactory@VUnitClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C3340 装 vt 007F3BB8→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**after 第4列：**
```text
S22 T_TClassFactory_VUnitClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C341B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C3471 `call dword ptr [eax]`（新建 UnitClass 对象主 vt 007F5C70 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C3473 `mov edi,eax`/`test edi,edi`/`jge 0x6c3482`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C347F `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 UnitClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 UnitClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3BC4(vt 007F3BB8 +12，slot#3) 4B 值即本 entry，RTTI COL=0080AAC8→TD=00841898→名=.?AV?$TClassFactory@VUnitClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C3340 装 vt 007F3BB8→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。；④ 活表槽位见证：T_TClassFactory_VUnitClass__::slot3（vt=007F3BB8，槽 3 值=006C3410，COL=0080AAC8 offset=0，RTTI=00841898→.?AV?$TClassFactory@VUnitClass@@@@；装表点 006C3349 位于 006C3340 体内，entry 体外） ④升级句：T_TClassFactory_VUnitClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VUnitClass__；该槽即其 vt=007F3BB8 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

追加段：`；④ 活表槽位见证：T_TClassFactory_VUnitClass__::slot3（vt=007F3BB8，槽 3 值=006C3410，COL=008…`

### 18. 006C3590（+379 字节）

**before 第4列：**
```text
S22 T_TClassFactory_VBuildingClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C359B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C35F1 `call dword ptr [eax]`（新建 BuildingClass 对象主 vt 007E3EBC 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C35F3 `mov edi,eax`/`test edi,edi`/`jge 0x6c3602`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C35FF `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 BuildingClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 BuildingClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3BDC(vt 007F3BD0 +12，slot#3) 4B 值即本 entry，RTTI COL=0080AB18→TD=008418C8→名=.?AV?$TClassFactory@VBuildingClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C34C0 装 vt 007F3BD0→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。
```

**after 第4列：**
```text
S22 T_TClassFactory_VBuildingClass__::slot3（IClassFactory::CreateInstance）—— ③b② 成立：入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @006C359B；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @006C35F1 `call dword ptr [eax]`（新建 BuildingClass 对象主 vt 007E3EBC 的 slot0=QueryInterface 00410260，主虚表 slot0=00410260 已核），@006C35F3 `mov edi,eax`/`test edi,edi`/`jge 0x6c3602`：失败返 0x80004002/0x80004003、成功返 0，返回约定字节可伪证（常量 00000000,80004002,80004003、3 处 ret）；调用方真拿它分支且两路动作不同——失败路 @006C35FF `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义：为 BuildingClass 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 BuildingClass 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。② 槽 007F3BDC(vt 007F3BD0 +12，slot#3) 4B 值即本 entry，RTTI COL=0080AB18→TD=008418C8→名=.?AV?$TClassFactory@VBuildingClass@@@@；主虚表 slot0=00410260(=00410260，非小成员表)。④ 活 COM 类对象：ctor 006C34C0 装 vt 007F3BD0→注册，宿主 006BB9A0 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。；④ 活表槽位见证：T_TClassFactory_VBuildingClass__::slot3（vt=007F3BD0，槽 3 值=006C3590，COL=0080AB18 offset=0，RTTI=008418C8→.?AV?$TClassFactory@VBuildingClass@@@@；装表点 006C34C9 位于 006C34C0 体内，entry 体外） ④升级句：T_TClassFactory_VBuildingClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VBuildingClass__；该槽即其 vt=007F3BD0 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

追加段：`；④ 活表槽位见证：T_TClassFactory_VBuildingClass__::slot3（vt=007F3BD0，槽 3 值=006C3590，COL…`

## 2. 九个验证（VERIFY.txt）

```text
R16-MERGE-F1 B2 · VERIFY（9 项验证）
generated: 2026-11-21 00:14:28
======================================================================
[1] PASS  coverage.tsv 逐字节还原性（18 行第4列换回改前原值后 sha256 == 改前 sha256）
      recon=bb62a995447a before=bb62a995447a
[2] PASS  不变量 18498/{8:18498}/1654/1648/6 + 18 行 grade 仍 [已证]
      rows=18498 coldist={8: 18498} proved=1654 atlas_in=1648 atlas_out=6 grade18_ok=18/18
[3] PASS  只有 18 行第4列变了（差异 entry 恰为这 18 个，每行仅第4列不同）
      diff_rows=18 entry_match=True only_col4=True
[4] PASS  严格前缀 18/18
      18/18
[5] PASS  六个实测数
      {"N_pre_A": 15, "N_pre_B": 0, "N_A_pre": 351, "N_A_post": 354, "N_B_pre": 152, "N_B_post": 170} netA=3 netB=18
[6] PASS  §12.6/§12.4 命中计数
      18行内 §12.6=18/18 §12.4=0; 全表 §12.6 61->79 §12.4 0->0
[7] PASS  PANEL.md 还原性（删掉 M90 披露块后 sha256 == 改前 sha256）
      block_lines=246-252 block_eq=True recon=7f64c083f5bb before=7f64c083f5bb
[8] PASS  达标未翻转（strict_panel.py 复算：名义 S15,S16,S17 / 严格 S17）
      nominal=S15,S16,S17 strict=S17 proved=1648 strict_n=1331
[9] PASS  行尾（两文件改前改后均 LF-only，无混用）
      cov before LF=18498 after LF=18498 CRLF=0; pan before LF=631 after LF=638 CRLF=0
[0] PASS  改前/改后 sha256 与 state 一致（sanity）
      cov disk=6428b4eb0628 state=6428b4eb0628; pan disk=755767162376 state=755767162376

TOTAL: 10 PASS / 0 FAIL

coverage.tsv: BEFORE 4049509 bb62a995 -> AFTER 4058895 6428b4eb
PANEL.md    : BEFORE 170502 7f64c083 -> AFTER 172885 75576716
六个实测数: {"N_pre_A": 15, "N_pre_B": 0, "N_A_pre": 351, "N_A_post": 354, "N_B_pre": 152, "N_B_post": 170}
达标集合: 名义 S15,S16,S17 / 严格 S17（strict_panel.py 复算）

```

## 3. 六个实测数

| 指标 | 值 |
|---|---:|
| N_pre_A（18 行改前第4列含 ④ 的行数）| 15 |
| N_pre_B（18 行改前第4列含 ④ 活表槽位见证 的行数）| 0 |
| N_A_pre（全表口径A 改前）| 351 |
| N_A_post（全表口径A 改后）| 354 |
| N_B_pre（全表口径B 改前）| 152 |
| N_B_post（全表口径B 改后）| 170 |

净增：口径 A = 354 − 351 = **3 行**（不是 +18：18 行里 15 行改前第 4 列已含 ④，故口径 A 不增）；口径 B = 170 − 152 = **18 行**。

## 4. 达标集合（strict_panel.py 口径复算，输出在本目录 strict_panel.tsv/json）

- 名义达标：**S15,S16,S17**（3/22）
- 严格达标：**S17**（1/22）
- atlas 内 proved 1,648 / proved_strict 1,331；达标未翻转。

## 5. 硬边界确认

- 只改 `coverage.tsv` 该 18 行第 4 列；其它行、其它列零改（验证 [1][3][4]）。
- `PANEL.md` 只新增 1 条 M90 披露，既有内容零删除零改字（验证 [7]）。
- 未改 R14_COMMON / 台账 / 看板 / _drafts / _cards / 任何卡目录；未做逆向。
- strict_panel.py 未改共享原件，副本输出在本目录。

