# a-S17-ENGFAM — 审计 S17 英文措辞族 34 行的四环实质（VERDICT）

审计人：agent-128（a-S17-ENGFAM 卡）。全部证据为本审计自有反汇编产出；
`S17-F1/EVIDENCE/analysis_deep2.txt` 仅作线索（读过，其结论未作为任何 PASS 依据）。

## 0. 自校验与方法

- 目标二进制 SHA-256 实测 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`，与卡面期望一致。
- pefile 实测段表：ImageBase 0x400000；`.text` VirtualSize=0x3DF38D → `[0x401000,0x7E038D)`，与卡面一致；34 个入口全部落在该区间内（另核：`.data` raw 背书区 `[0x812000,0x87E000)`，`0x87E000` 以上为 .bss 零初始化区——35 个向量实参全部位于 `0x87E000` 以上，真 .bss）。
- 工具链：Python 3.12.10 + capstone 5.0.7（**skipdata=True**）+ pefile 2024.8.26，无 venv、无安装。
- 自有脚本（本目录 `work/`）：a1_bodies / a2_xrefs / a3_rtti / a4_core / a5_alive / a6_root / a7_ctor / a8_final / a9_report。自有证据文件（`EVIDENCE/`）：bodies.txt（34+1 槽全量逐条反汇编）、xrefs.txt、rtti.txt、chain.txt、alive.txt、root.txt、ctors.txt、rows_fragment.md。
- 34 行清单过滤命令（照实执行，得 34 行，全部 grade `[已证]`、全部 evidence_path 指向 analysis_main.txt+analysis_deep2.txt）：

  ```powershell
  Select-String -Path "D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv" -Pattern 'unproven|unverified|not proven' | Where-Object { $_.Line -match "`tS17`t" }
  ```

## 1. 模板体（35 个槽逐字节同体，本审计独立 md5/逐字节 diff 复核）

35 个物理实例（01–35 含 #17 空缺槽 0x6805F0）的 127 字节体两两 diff = **0 字节**，统一 md5(127B)=`9f6770a9cd27b9fa49558adf28c92f10`（a1 自算，非引自任何普查文件）。体长 0x7F、+0x7E=`C3`、+0x7F=填充 `90`、槽距 0x80。以下为体逐字节语义注释（以 #1 入口 0x67FDF0 为基准，偏移 +xx 对全部实例同构；字节见 `EVIDENCE/bodies.txt`）：

```
+00 83 EC 08              sub esp,8 ; push ebx/esi/edi          ; 序言（栈平衡自洽）
+06 8B FA / 8B D9         mov edi,edx ; mov ebx,ecx             ; edi=arg2 向量(.bss) ebx=arg1 IStream*
+0A 6A 00                 push 0                                ; pcbWritten=NULL
+0C 8B 47 10              mov eax,[edi+0x10]                    ; vec->Count（DynamicVectorClass 布局 +0x10）
+0F 8D 54 24 14           lea edx,[esp+0x14]                    ; &局部Count槽
+13 8B 0B                 mov ecx,[ebx]                         ; IStream vftable
+15..+19 push 4 / push edx / push ebx / mov [esp+0x20],eax ; 装参：this=ebx, pv=&Count, cb=4
+1D FF 51 10              call [ecx+0x10]                       ; IStream::Write(&Count,4,NULL)  ← 栈外写
+20 85 C0 / +22 7C 54     test eax,eax ; jl 失败出口            ; HRESULT 可证伪传播
+24 8B 44 24 10           mov eax,[esp+0x10]                    ; 重读 Count
+28 33 F6 / +2A 85 C0 / +2C 7E 48   xor esi,esi ; test ; jle +0x76   ; i=0；Count<=0 跳过（边界）
+2E 8B 47 04              mov eax,[edi+4]                       ; vec->Items（数组 +4）
+31 C7 44 24 0C 00000000  mov [esp+0xC],0 / +39 lea edx         ; &out
+3D 8B 04 B0              mov eax,[eax+esi*4]                   ; eax=Items[i]（元素）
+40..+47 push edx / push 0x7F7C80 / push eax / mov ecx,[eax]
+49 FF 11                 call [ecx]                            ; 元素 QueryInterface(IID)
                                                                ; IID@0x7F7C80={00000109-0000-0000-C000-000000000046}
                                                                ;   = IID_IPersistStream（a2 自读字节）
+4B 85 C0 / +4D 7C 29     test eax,eax ; jl 失败
+4F..+54  mov eax,[esp+0xC] ; push ebx ; push eax
+55 FF 15 F4 15 7E 00     call [0x7E15F4]                       ; IAT→ole32!OleSaveToStream(pPersist,pStm)
                                                                ;   （a2 自解 IAT，非引自普查）
+5B 85 C0 / +5D 7C 19     test eax,eax ; jl 失败
+5F..+66  mov eax,[esp+0xC] ; push eax ; mov ecx,[eax] ; call [ecx+8]   ; Release(out)
+69 85 C0 / +6B 7C 0B     test eax,eax ; jl 失败
+6D 8B 44 24 10 / +71 46 / +72 3B F0 / +74 7C B8  ; 重读 Count；inc i；cmp；**jl +0x2E 回边（界：i<Count）**
+76 33 C0                 xor eax,eax                           ; S_OK
+78 5F 5E 5B 83 C4 08 C3  pop×3 ; add esp,8 ; ret               ; 体止于 +0x7E
```

## 2. 逐行五点复核（34 节）

共同依据（对每行均成立，行专属地址在下表/各节中）：

- **① 入口**：地址在 `.text` 内；序言 `sub esp,8; push ebx; push esi; push edi` 与尾声 `pop edi/esi/ebx; add esp,8; ret` 平衡；体 0x7F 止于 `C3`，+0x7F 填充 `90`，槽距 0x80 无越界、无重叠。
- **② 类身份**：本函数族为自由函数（自有扫描：0x67FDF0–0x680F70 区间 0 个虚表条目），函数自身无 RTTI/虚表归属（D-41 形态，物理查不到）；但其服务对象（edx 传入的 .bss 向量）经**构造链**定死：每向量存在 `mov dword ptr [vec], vt` 构造写入，vt 的 RTTI TD 名给出精确类 `DynamicVectorClass<PAV<元素>Class>`（a7 全 35 个向量逐个定死并逐字节复核写入）。**故语义尾缀「class name unproven (arg .bss obj)」属『当时没查』而非『查不到』**——本审计已把 34 行（含 #17 槽）的向量类与元素类全部定死（见下）。
- **③ 整体合同（只认 ③b）**：体即 **③b④ 完整循环 I/O 带边界检查**：`Write(&Count,4,NULL)` → `i=0..Count-1`（`jl` 有界回边）→ 元素 `QI(IID_IPersistStream)` → `OleSaveToStream`（栈外写：写入流对象）→ `Release`；且 **③b② 可证伪返回约定**同时成立：四处 `test/jl` 失败即携 HRESULT 提前返回，成功路径 `xor eax,eax`（S_OK）；上层 Save_Core `test/jge` 再映射为 bool。**写为栈外写**（IStream::Write 经 COM 虚表派发 + ole32!IAT 导入，写对象是流），非「写栈/累加槽/寄存器推进」。与已知陷阱 `0045A640` 类（循环内只 push、非栈写 0）**形态相反**，不适用该陷阱。
- **④ 使用见证**：每行恰有 **1 个 E8 直接调用点**（全部位于 Save_Core `0x67D300`，jmp=0、data 引用=0——a2 有界重扫修正后确认 a2 初版对 `0x88F03C/0x88F19C` 的命中系越界映射伪迹，已作废）；该调用链为**活链**：从 PE 入口 `0x7CD80F` 正向可达性扫描（6366 函数）**同时到达**全部 3 个上游根（0x4C6CB0/0x559C20/0x55D360）；反向闭包 1144 函数中含 **81 个 RTTI 虚表成员**（FootClass/BuildingClass/MouseClass/MapClass/AnimClass 等）。非 direct-only 死链。
- **⑤ 家族**：见 §3——模板成立；`Save_VectorBlock_NN` 为 slotN 式名字，按卡面不构成判行不成立的理由。

行专属数据表（每行各自的入口/调用点/向量/构造写入/RTTI 类；md5 同上）：

| # | entry | call site（E8，site+5+rel32==entry） | edx=.bss 向量 | 构造写入 | RTTI 类（TD 名） | 元素类 |
|---|-------|--------------------------------------|----------------|----------|------------------|--------|
| 01 | 0x0067FDF0 | 0x0067DF0F `E8 DC 1E 00 00`→0x0067FDF0 ✓ | 0x00A83E30 | 0x004E6E7D | `.?AV?$DynamicVectorClass@PAVFactoryClass@@@@` | FactoryClass |
| 02 | 0x0067FE70 | 0x0067DF29 `E8 42 1F 00 00`→0x0067FE70 ✓ | 0x00A8EB28 | 0x004E767D | `.?AV?$DynamicVectorClass@PAVVoxelAnimTypeClass@@@@` | VoxelAnimTypeClass |
| 03 | 0x0067FEF0 | 0x0067DF43 `E8 A8 1F 00 00`→0x0067FEF0 ✓ | 0x00887388 | 0x0040EE5D | `.?AV?$DynamicVectorClass@PAVVoxelAnimClass@@@@` | VoxelAnimClass |
| 04 | 0x0067FF70 | 0x0067DF5D `E8 0E 20 00 00`→0x0067FF70 ✓ | 0x008874C0 | 0x0040F4AD | `.?AV?$DynamicVectorClass@PAVWarheadTypeClass@@@@` | WarheadTypeClass |
| 05 | 0x0067FFF0 | 0x0067DF77 `E8 74 20 00 00`→0x0067FFF0 ✓ | 0x00887568 | 0x0040FB4D | `.?AV?$DynamicVectorClass@PAVWeaponTypeClass@@@@` | WeaponTypeClass |
| 06 | 0x00680070 | 0x0067DF91 `E8 DA 20 00 00`→0x00680070 ✓ | 0x00A83D98 | 0x004E777D | `.?AV?$DynamicVectorClass@PAVParticleTypeClass@@@@` | ParticleTypeClass |
| 07 | 0x006800F0 | 0x0067DFAB `E8 40 21 00 00`→0x006800F0 ✓ | 0x00A83DC8 | 0x004E697D | `.?AV?$DynamicVectorClass@PAVParticleClass@@@@` | ParticleClass |
| 08 | 0x00680170 | 0x0067DFC5 `E8 A6 21 00 00`→0x00680170 ✓ | 0x00A83D68 | 0x004E77FD | `.?AV?$DynamicVectorClass@PAVParticleSystemTypeClass@@@@` | ParticleSystemTypeClass |
| 09 | 0x006801F0 | 0x0067DFDF `E8 0C 22 00 00`→0x006801F0 ✓ | 0x00A80208 | 0x004E66FD | `.?AV?$DynamicVectorClass@PAVParticleSystemClass@@@@` | ParticleSystemClass |
| 10 | 0x00680270 | 0x0067DFF9 `E8 72 22 00 00`→0x00680270 ✓ | 0x00A83C80 | 0x004E75FD | `.?AV?$DynamicVectorClass@PAVBulletTypeClass@@@@` | BulletTypeClass |
| 11 | 0x006802F0 | 0x0067E013 `E8 D8 22 00 00`→0x006802F0 ✓ | 0x00A8ED40 | 0x004E687D | `.?AV?$DynamicVectorClass@PAVBulletClass@@@@` | BulletClass |
| 12 | 0x00680370 | 0x0067E02D `E8 3E 23 00 00`→0x00680370 ✓ | 0x00B72608 | 0x007635AD | `.?AV?$DynamicVectorClass@PAVWaypointPathClass@@@@` | WaypointPathClass |
| 13 | 0x006803F0 | 0x0067E047 `E8 A4 23 00 00`→0x006803F0 ✓ | 0x00A8EC18 | 0x004E727D | `.?AV?$DynamicVectorClass@PAVSmudgeTypeClass@@@@` | SmudgeTypeClass |
| 14 | 0x00680470 | 0x0067E061 `E8 0A 24 00 00`→0x00680470 ✓ | 0x00A83D80 | 0x004E71FD | `.?AV?$DynamicVectorClass@PAVOverlayTypeClass@@@@` | OverlayTypeClass |
| 15 | 0x006804F0 | 0x0067E07B `E8 70 24 00 00`→0x006804F0 ✓ | 0x00ABCA10 | 0x0055465D | `.?AV?$DynamicVectorClass@PAVLightSourceClass@@@@` | LightSourceClass |
| 16 | 0x00680570 | 0x0067E095 `E8 D6 24 00 00`→0x00680570 ✓ | 0x008B4190 | 0x004E667D | `.?AV?$DynamicVectorClass@PAVBuildingLightClass@@@@` | BuildingLightClass |
| 18 | 0x00680670 | 0x0067E0C9 `E8 A2 25 00 00`→0x00680670 ✓ | 0x00B0F4E8 | 0x0072165D | `.?AV?$DynamicVectorClass@PAVTiberiumClass@@@@` | TiberiumClass |
| 19 | 0x006806F0 | 0x0067E0E3 `E8 08 26 00 00`→0x006806F0 ✓ | 0x008A3870 | 0x004C522D | `.?AV?$DynamicVectorClass@PAVEMPulseClass@@@@` | EMPulseClass |
| 20 | 0x00680770 | 0x0067E0FD `E8 6E 26 00 00`→0x00680770 ✓ | 0x00A8E330 | 0x004E787D | `.?AV?$DynamicVectorClass@PAVSuperWeaponTypeClass@@@@` | SuperWeaponTypeClass |
| 21 | 0x006807F0 | 0x0067E117 `E8 D4 26 00 00`→0x006807F0 ✓ | 0x00A83CB8 | 0x004E78FD | `.?AV?$DynamicVectorClass@PAVSuperClass@@@@` | SuperClass |
| 22 | 0x00680870 | 0x0067E1E7 `E8 84 26 00 00`→0x00680870 ✓ | 0x00A8E318 | 0x004E72FD | `.?AV?$DynamicVectorClass@PAVTerrainTypeClass@@@@` | TerrainTypeClass |
| 23 | 0x006808F0 | 0x0067E201 `E8 EA 26 00 00`→0x006808F0 ✓ | 0x00A8E988 | 0x004E6A7D | `.?AV?$DynamicVectorClass@PAVTerrainClass@@@@` | TerrainClass |
| 24 | 0x00680970 | 0x0067E21B `E8 50 27 00 00`→0x00680970 ✓ | 0x008B3D10 | 0x004D076D | `.?AV?$DynamicVectorClass@PAVFoggedObjectClass@@@@` | FoggedObjectClass |
| 25 | 0x006809F0 | 0x0067E235 `E8 B6 27 00 00`→0x006809F0 ✓ | 0x0088A0F0 | 0x004208FD | `.?AV?$DynamicVectorClass@PAVAlphaShapeClass@@@@` | AlphaShapeClass |
| 26 | 0x00680A70 | 0x0067E24F `E8 1C 28 00 00`→0x00680A70 ✓ | 0x00A8EC38 | 0x004E67FD | `.?AV?$DynamicVectorClass@PAVWaveClass@@@@` | WaveClass |
| 27 | 0x00680AF0 | 0x0067E28F `E8 5C 28 00 00`→0x00680AF0 ✓ | 0x0089E0F0 | 0x0047176D | `.?AV?$DynamicVectorClass@PAVCaptureManagerClass@@@@` | CaptureManagerClass |
| 28 | 0x00680B70 | 0x0067E2A9 `E8 C2 28 00 00`→0x00680B70 ✓ | 0x008A0208 | 0x004A6C8D | `.?AV?$DynamicVectorClass@PAVDiskLaserClass@@@@` | DiskLaserClass |
| 29 | 0x00680BF0 | 0x0067E2C3 `E8 28 29 00 00`→0x00680BF0 ✓ | 0x00AC4910 | 0x006291AD | `.?AV?$DynamicVectorClass@PAVParasiteClass@@@@` | ParasiteClass |
| 30 | 0x00680C70 | 0x0067E2DD `E8 8E 29 00 00`→0x00680C70 ✓ | 0x00B0EC60 | 0x0071A3ED | `.?AV?$DynamicVectorClass@PAVTemporalClass@@@@` | TemporalClass |
| 31 | 0x00680CF0 | 0x0067E2F7 `E8 F4 29 00 00`→0x00680CF0 ✓ | 0x00889FB8 | 0x0041D29D | `.?AV?$DynamicVectorClass@PAVAirstrikeClass@@@@` | AirstrikeClass |
| 32 | 0x00680D70 | 0x0067E311 `E8 5A 2A 00 00`→0x00680D70 ✓ | 0x00B0B880 | 0x006B6C2D | `.?AV?$DynamicVectorClass@PAVSpawnManagerClass@@@@` | SpawnManagerClass |
| 33 | 0x00680DF0 | 0x0067E32B `E8 C0 2A 00 00`→0x00680DF0 ✓ | 0x00B0B5F0 | 0x006AF13D | `.?AV?$DynamicVectorClass@PAVSlaveManagerClass@@@@` | SlaveManagerClass |
| 34 | 0x00680E70 | 0x0067E390 `E8 DB 2A 00 00`→0x00680E70 ✓ | 0x0089C668 | 0x0043856D | `.?AV?$DynamicVectorClass@PAVBombClass@@@@` | BombClass |
| 35 | 0x00680EF0 | 0x0067E3AA `E8 41 2B 00 00`→0x00680EF0 ✓ | 0x00B04BD0 | 0x0065B17D | `.?AV?$DynamicVectorClass@PAVRadSiteClass@@@@` | RadSiteClass |

### 2.1 ≥3 个不同实例的独立字节核验（卡面硬要求；bodies.txt 另含全部 34+1 槽逐条清单）

- **#01 @0x0067FDF0**：入口 16 字节 `83 EC 08 53 56 57 8B FA 8B D9 6A 00 8B 47 10 8D`；尾段 +0x70..+0x7E `10 46 3B F0 7C B8 33 C0 5F 5E 5B 83 C4 08 C3`（`33 C0 5F 5E 5B 83 C4 08 C3` 止于 +0x7E）；md5(127B)=`9f6770a9…`；调用点 0x0067DF0F `E8`→本入口 ✓；edx=0x00A83E30，构造写入 0x004E6E7D `mov [vec],0x007E9FA4` → `DynamicVectorClass<PAVFactoryClass>`。三处派发（+0x1D Write / +0x49 QI / +0x55 OleSaveToStream）字节在 bodies.txt 该槽清单内逐条在案。
- **#16 @0x00680570**：入口 16 字节 `83 EC 08 53 56 57 8B FA 8B D9 6A 00 8B 47 10 8D`；尾段 +0x70..+0x7E `10 46 3B F0 7C B8 33 C0 5F 5E 5B 83 C4 08 C3`（`33 C0 5F 5E 5B 83 C4 08 C3` 止于 +0x7E）；md5(127B)=`9f6770a9…`；调用点 0x0067E095 `E8`→本入口 ✓；edx=0x008B4190，构造写入 0x004E667D `mov [vec],0x007E9C24` → `DynamicVectorClass<PAVBuildingLightClass>`。三处派发（+0x1D Write / +0x49 QI / +0x55 OleSaveToStream）字节在 bodies.txt 该槽清单内逐条在案。
- **#35 @0x00680EF0**：入口 16 字节 `83 EC 08 53 56 57 8B FA 8B D9 6A 00 8B 47 10 8D`；尾段 +0x70..+0x7E `10 46 3B F0 7C B8 33 C0 5F 5E 5B 83 C4 08 C3`（`33 C0 5F 5E 5B 83 C4 08 C3` 止于 +0x7E）；md5(127B)=`9f6770a9…`；调用点 0x0067E3AA `E8`→本入口 ✓；edx=0x00B04BD0，构造写入 0x0065B17D `mov [vec],0x007F07A4` → `DynamicVectorClass<PAVRadSiteClass>`。三处派发（+0x1D Write / +0x49 QI / +0x55 OleSaveToStream）字节在 bodies.txt 该槽清单内逐条在案。
- **（加验）#17 空缺槽 @0x6805F0**：同体同 md5（diff vs #1 = 0 字节）；调用点 0x67E0AF `E8`→0x6805F0 ✓；edx=0x8B4120，构造写入 0x004E6F7D `mov [0x8B4120],0x7EA024` → `DynamicVectorClass<PAVSideClass>`——即「Sides」向量；coverage 缺 #17 号是把该槽命名/归档分离所致，物理上模板实为 35 连号。

## 3. 整族结论（模板是否成立、成立范围）

**模板成立。** 成立范围 = **35 个物理实例**（0x67FDF0 起、槽距 0x80、至 0x680EF0 止，含被 coverage 排除在名族外的 #17 槽 0x6805F0）。模板形态：**「写 4 字节 Count → 有界循环（i<Count）逐元素 { QI(IID_IPersistStream) → OleSaveToStream → Release } → HRESULT 可证伪返回」**，实例间**唯一差异是 Save_Core 传入的 edx（各自独立的 .bss 向量，35 个互不相同，已逐个用构造写入定死类）**。因此「模板成立可替代逐行成立」的适用方式是：逐行 PASS 的依据 = 同体字节核验（每行自己的入口在 bodies.txt 有独立清单）+ 每行自己的调用点/向量/构造写入核验（上表），而不是「同族所以都成立」一句带过。

## 4. 已知陷阱对照

- `0045A640` 类（循环内只 push 写栈、非栈写 0）：**不适用**——本体循环内有两个栈外写派发（IStream::Write、OleSaveToStream），非栈写 ≥2。
- 多路进同一 call 仅参数不同（不计细则#1）：**未引用细则#1**——③b 走 ④（完整循环 I/O）+②（可证伪返回），不走跳表/闸道路径。
- slotN 式名字：`Save_VectorBlock_NN` 属之；按卡面记为 `named_pct_S(R14)` 满足、不构成 FAIL 理由。

## 5. 逐行判定

### Save_VectorBlock_01 — 0x0067FDF0 — **PASS**

- ① 入口：0x0067FDF0 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00A83E30，构造写入 0x004E6E7D：`mov dword ptr [0x00A83E30],0x007E9FA4` → RTTI `.?AV?$DynamicVectorClass@PAVFactoryClass@@@@`，元素 FactoryClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067DF0F（E8→0x0067FDF0 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_02 — 0x0067FE70 — **PASS**

- ① 入口：0x0067FE70 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00A8EB28，构造写入 0x004E767D：`mov dword ptr [0x00A8EB28],0x007EA3A4` → RTTI `.?AV?$DynamicVectorClass@PAVVoxelAnimTypeClass@@@@`，元素 VoxelAnimTypeClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067DF29（E8→0x0067FE70 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_03 — 0x0067FEF0 — **PASS**

- ① 入口：0x0067FEF0 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00887388，构造写入 0x0040EE5D：`mov dword ptr [0x00887388],0x007E1E2C` → RTTI `.?AV?$DynamicVectorClass@PAVVoxelAnimClass@@@@`，元素 VoxelAnimClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067DF43（E8→0x0067FEF0 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_04 — 0x0067FF70 — **PASS**

- ① 入口：0x0067FF70 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x008874C0，构造写入 0x0040F4AD：`mov dword ptr [0x008874C0],0x007E1E84` → RTTI `.?AV?$DynamicVectorClass@PAVWarheadTypeClass@@@@`，元素 WarheadTypeClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067DF5D（E8→0x0067FF70 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_05 — 0x0067FFF0 — **PASS**

- ① 入口：0x0067FFF0 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00887568，构造写入 0x0040FB4D：`mov dword ptr [0x00887568],0x007E1ED4` → RTTI `.?AV?$DynamicVectorClass@PAVWeaponTypeClass@@@@`，元素 WeaponTypeClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067DF77（E8→0x0067FFF0 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_06 — 0x00680070 — **PASS**

- ① 入口：0x00680070 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00A83D98，构造写入 0x004E777D：`mov dword ptr [0x00A83D98],0x007EA424` → RTTI `.?AV?$DynamicVectorClass@PAVParticleTypeClass@@@@`，元素 ParticleTypeClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067DF91（E8→0x00680070 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_07 — 0x006800F0 — **PASS**

- ① 入口：0x006800F0 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00A83DC8，构造写入 0x004E697D：`mov dword ptr [0x00A83DC8],0x007E9D64` → RTTI `.?AV?$DynamicVectorClass@PAVParticleClass@@@@`，元素 ParticleClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067DFAB（E8→0x006800F0 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_08 — 0x00680170 — **PASS**

- ① 入口：0x00680170 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00A83D68，构造写入 0x004E77FD：`mov dword ptr [0x00A83D68],0x007EA464` → RTTI `.?AV?$DynamicVectorClass@PAVParticleSystemTypeClass@@@@`，元素 ParticleSystemTypeClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067DFC5（E8→0x00680170 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_09 — 0x006801F0 — **PASS**

- ① 入口：0x006801F0 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00A80208，构造写入 0x004E66FD：`mov dword ptr [0x00A80208],0x007E9C64` → RTTI `.?AV?$DynamicVectorClass@PAVParticleSystemClass@@@@`，元素 ParticleSystemClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067DFDF（E8→0x006801F0 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_10 — 0x00680270 — **PASS**

- ① 入口：0x00680270 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00A83C80，构造写入 0x004E75FD：`mov dword ptr [0x00A83C80],0x007EA364` → RTTI `.?AV?$DynamicVectorClass@PAVBulletTypeClass@@@@`，元素 BulletTypeClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067DFF9（E8→0x00680270 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_11 — 0x006802F0 — **PASS**

- ① 入口：0x006802F0 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00A8ED40，构造写入 0x004E687D：`mov dword ptr [0x00A8ED40],0x007E4678` → RTTI `.?AV?$DynamicVectorClass@PAVBulletClass@@@@`，元素 BulletClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E013（E8→0x006802F0 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_12 — 0x00680370 — **PASS**

- ① 入口：0x00680370 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00B72608，构造写入 0x007635AD：`mov dword ptr [0x00B72608],0x007F6E04` → RTTI `.?AV?$DynamicVectorClass@PAVWaypointPathClass@@@@`，元素 WaypointPathClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E02D（E8→0x00680370 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_13 — 0x006803F0 — **PASS**

- ① 入口：0x006803F0 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00A8EC18，构造写入 0x004E727D：`mov dword ptr [0x00A8EC18],0x007EA1A4` → RTTI `.?AV?$DynamicVectorClass@PAVSmudgeTypeClass@@@@`，元素 SmudgeTypeClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E047（E8→0x006803F0 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_14 — 0x00680470 — **PASS**

- ① 入口：0x00680470 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00A83D80，构造写入 0x004E71FD：`mov dword ptr [0x00A83D80],0x007EA164` → RTTI `.?AV?$DynamicVectorClass@PAVOverlayTypeClass@@@@`，元素 OverlayTypeClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E061（E8→0x00680470 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_15 — 0x006804F0 — **PASS**

- ① 入口：0x006804F0 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00ABCA10，构造写入 0x0055465D：`mov dword ptr [0x00ABCA10],0x007ECF7C` → RTTI `.?AV?$DynamicVectorClass@PAVLightSourceClass@@@@`，元素 LightSourceClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E07B（E8→0x006804F0 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_16 — 0x00680570 — **PASS**

- ① 入口：0x00680570 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x008B4190，构造写入 0x004E667D：`mov dword ptr [0x008B4190],0x007E9C24` → RTTI `.?AV?$DynamicVectorClass@PAVBuildingLightClass@@@@`，元素 BuildingLightClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E095（E8→0x00680570 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_18 — 0x00680670 — **PASS**

- ① 入口：0x00680670 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00B0F4E8，构造写入 0x0072165D：`mov dword ptr [0x00B0F4E8],0x007F56BC` → RTTI `.?AV?$DynamicVectorClass@PAVTiberiumClass@@@@`，元素 TiberiumClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E0C9（E8→0x00680670 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_19 — 0x006806F0 — **PASS**

- ① 入口：0x006806F0 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x008A3870，构造写入 0x004C522D：`mov dword ptr [0x008A3870],0x007E873C` → RTTI `.?AV?$DynamicVectorClass@PAVEMPulseClass@@@@`，元素 EMPulseClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E0E3（E8→0x006806F0 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_20 — 0x00680770 — **PASS**

- ① 入口：0x00680770 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00A8E330，构造写入 0x004E787D：`mov dword ptr [0x00A8E330],0x007EA4A4` → RTTI `.?AV?$DynamicVectorClass@PAVSuperWeaponTypeClass@@@@`，元素 SuperWeaponTypeClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E0FD（E8→0x00680770 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_21 — 0x006807F0 — **PASS**

- ① 入口：0x006807F0 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00A83CB8，构造写入 0x004E78FD：`mov dword ptr [0x00A83CB8],0x007EA4E4` → RTTI `.?AV?$DynamicVectorClass@PAVSuperClass@@@@`，元素 SuperClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E117（E8→0x006807F0 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_22 — 0x00680870 — **PASS**

- ① 入口：0x00680870 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00A8E318，构造写入 0x004E72FD：`mov dword ptr [0x00A8E318],0x007EA1E4` → RTTI `.?AV?$DynamicVectorClass@PAVTerrainTypeClass@@@@`，元素 TerrainTypeClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E1E7（E8→0x00680870 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_23 — 0x006808F0 — **PASS**

- ① 入口：0x006808F0 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00A8E988，构造写入 0x004E6A7D：`mov dword ptr [0x00A8E988],0x007E9DE4` → RTTI `.?AV?$DynamicVectorClass@PAVTerrainClass@@@@`，元素 TerrainClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E201（E8→0x006808F0 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_24 — 0x00680970 — **PASS**

- ① 入口：0x00680970 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x008B3D10，构造写入 0x004D076D：`mov dword ptr [0x008B3D10],0x007E44F4` → RTTI `.?AV?$DynamicVectorClass@PAVFoggedObjectClass@@@@`，元素 FoggedObjectClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E21B（E8→0x00680970 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_25 — 0x006809F0 — **PASS**

- ① 入口：0x006809F0 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x0088A0F0，构造写入 0x004208FD：`mov dword ptr [0x0088A0F0],0x007E3238` → RTTI `.?AV?$DynamicVectorClass@PAVAlphaShapeClass@@@@`，元素 AlphaShapeClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E235（E8→0x006809F0 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_26 — 0x00680A70 — **PASS**

- ① 入口：0x00680A70 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00A8EC38，构造写入 0x004E67FD：`mov dword ptr [0x00A8EC38],0x007E9CE4` → RTTI `.?AV?$DynamicVectorClass@PAVWaveClass@@@@`，元素 WaveClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E24F（E8→0x00680A70 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_27 — 0x00680AF0 — **PASS**

- ① 入口：0x00680AF0 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x0089E0F0，构造写入 0x0047176D：`mov dword ptr [0x0089E0F0],0x007E4AD4` → RTTI `.?AV?$DynamicVectorClass@PAVCaptureManagerClass@@@@`，元素 CaptureManagerClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E28F（E8→0x00680AF0 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_28 — 0x00680B70 — **PASS**

- ① 入口：0x00680B70 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x008A0208，构造写入 0x004A6C8D：`mov dword ptr [0x008A0208],0x007E5EDC` → RTTI `.?AV?$DynamicVectorClass@PAVDiskLaserClass@@@@`，元素 DiskLaserClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E2A9（E8→0x00680B70 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_29 — 0x00680BF0 — **PASS**

- ① 入口：0x00680BF0 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00AC4910，构造写入 0x006291AD：`mov dword ptr [0x00AC4910],0x007EF824` → RTTI `.?AV?$DynamicVectorClass@PAVParasiteClass@@@@`，元素 ParasiteClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E2C3（E8→0x00680BF0 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_30 — 0x00680C70 — **PASS**

- ① 入口：0x00680C70 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00B0EC60，构造写入 0x0071A3ED：`mov dword ptr [0x00B0EC60],0x007F5114` → RTTI `.?AV?$DynamicVectorClass@PAVTemporalClass@@@@`，元素 TemporalClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E2DD（E8→0x00680C70 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_31 — 0x00680CF0 — **PASS**

- ① 入口：0x00680CF0 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00889FB8，构造写入 0x0041D29D：`mov dword ptr [0x00889FB8],0x007E293C` → RTTI `.?AV?$DynamicVectorClass@PAVAirstrikeClass@@@@`，元素 AirstrikeClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E2F7（E8→0x00680CF0 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_32 — 0x00680D70 — **PASS**

- ① 入口：0x00680D70 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00B0B880，构造写入 0x006B6C2D：`mov dword ptr [0x00B0B880],0x007F35E4` → RTTI `.?AV?$DynamicVectorClass@PAVSpawnManagerClass@@@@`，元素 SpawnManagerClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E311（E8→0x00680D70 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_33 — 0x00680DF0 — **PASS**

- ① 入口：0x00680DF0 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00B0B5F0，构造写入 0x006AF13D：`mov dword ptr [0x00B0B5F0],0x007F315C` → RTTI `.?AV?$DynamicVectorClass@PAVSlaveManagerClass@@@@`，元素 SlaveManagerClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E32B（E8→0x00680DF0 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_34 — 0x00680E70 — **PASS**

- ① 入口：0x00680E70 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x0089C668，构造写入 0x0043856D：`mov dword ptr [0x0089C668],0x007E17CC` → RTTI `.?AV?$DynamicVectorClass@PAVBombClass@@@@`，元素 BombClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E390（E8→0x00680E70 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

### Save_VectorBlock_35 — 0x00680EF0 — **PASS**

- ① 入口：0x00680EF0 ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓
- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x00B04BD0，构造写入 0x0065B17D：`mov dword ptr [0x00B04BD0],0x007F07A4` → RTTI `.?AV?$DynamicVectorClass@PAVRadSiteClass@@@@`，元素 RadSiteClass（原语义「class name unproven」= 当时没查，现已查实）
- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）
- ④ 见证：唯一调用点 0x0067E3AA（E8→0x00680EF0 ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立
- 判定：**PASS**（四环齐；③ 只计 ③b，成立）

## 6. 统计

- 34/34 PASS，0 FAIL。无一行属「措辞掩盖了实质」——措辞是保守尾缀，实质（③b④ 循环 I/O）在字节里真实存在；尾缀所声明的「class name unproven」经本审计为**当时没查**且现已查实。
- 对 S17 计数的影响见 `SUMMARY.md`。
