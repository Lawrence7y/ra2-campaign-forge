# W130 独立虚表抽查报告 (gamemd.exe)

## 0. 环境与段核对
- SHA-256: 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476 (期望 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476) => MATCH
- IAT 导入函数数=372; msvcrt _purecall IAT 槽=无; .text 中 FF25 thunk 数=0
- .text  任务给定 00401000..007E038D | 实际 VA 00401000..007E038D (VirtualSize=3DF38D) SizeOfRawData=3E0000 => 文件字节覆盖 00401000..007E0FFF
- .rdata 任务给定 007E1000..00811074 | 实际 VA 007E1000..00811074 (VirtualSize=030074) SizeOfRawData=031000 => 文件字节覆盖 007E1000..00811FFF
- .data  任务给定 00812000..00B79BE4 | 实际 VA 00812000..00B79BE4 (VirtualSize=367BE4) SizeOfRawData=06C000 => 文件字节覆盖 00812000..0087DFFF
- .data SizeOfRawData = 0006C000 (任务称 0x6C000) => 一致
- 读取层: 段表 + 原始文件字节, VA>=ImageBase; 任何超出 SizeOfRawData 的地址一律视为无字节 (BSS 保护)。
- 校验: 0x400000 处前2字节 = b'MZ' (应为 MZ)

## 1. 独立 TD 清单 (交叉核对)
- 独立发现的结构完整 TypeDescriptor: 988 个; 类名(去重) 988 个
- 前缀分布: {'.?AV': 962, '.?AU': 26}
- 仅出现在 TD 清单、无候选虚表的类: 34 个; 例: .?AUIApplication@@, .?AUIChatEvent@WOL@@, .?AUIClassFactory@@, .?AUIConnectionPoint@@, .?AUIConnectionPointContainer@@, .?AUIDownloadEvent@WOL@@, .?AUIEnumConnectionPoints@@, .?AUIEnumConnections@@, .?AUIFlyControl@@, .?AUIGameMap@@
- 候选中有而 TD 清单没有的类名: 0 个

## 2. 候选虚表扫描 (任务口径)
- 候选虚表总数: **1219**
- 涉及类名总数(原始修饰名去重): **954**
- 按段分布: {'.rdata': 1214, '.data': 5}
- COL 内 pTypeDescriptor 解释方式: {'VA': 1219} (VA=绝对指针, RVA=镜像相对)
- COL signature 分布: {0: 1218, 4294967295: 1}
- COL offset 字段分布(前8): [(0, 955), (4, 95), (12, 78), (8, 78), (24, 6), (21784, 3), (1728, 1), (44, 1)]; offset!=0 的候选数=264
- TD 结构佐证 (td_struct_ok, [+4]==0): True=1219 False=0
- 候选 [pos-4] 前值类别: {'C': 985, 'X': 209, 'D': 14, '0': 10, 'B': 1}
- 候选 [pos+4] 后值类别: {'C': 1214, 'D': 1, 'X': 4}
- 相邻候选: pos+4 也是候选的 0 个; pos+8 也是候选的 186 个 (stride-8 成对特征计数)
- 前12槽含 0 的候选数: 163
- 被 >1 个位置引用的 COL 数: 1
- 候选 pos 落在某已验证 COL 对象内部的: 0 个
- 全体候选判定分布: {'REAL_VTABLE': 874, 'UNCERTAIN': 340, 'NOT_VTABLE': 5}
- 最高频代码槽值(潜在 _purecall/公共桩): 
  - 00410260 x300  [C]  mov eax, dword ptr [esp + 0xc] | push ebx | test eax, eax
  - 00410220 x230  [C]  mov eax, dword ptr [esp + 4] | mov eax, dword ptr [eax + 0xc] | ret 4
  - 00410230 x230  [C]  mov ecx, dword ptr [0xa8b230] | test ecx, ecx | jne 0x410246
  - 004105E0 x224  [C]  sub dword ptr [esp + 4], 4 | jmp 0x410260 | int3 
  - 00410210 x224  [C]  mov eax, dword ptr [esp + 4] | mov edx, dword ptr [eax - 4] | lea ecx, [eax - 4]
  - 00410300 x222  [C]  mov eax, 1 | ret 4 | nop 
  - 00410310 x222  [C]  mov eax, 1 | ret 4 | nop 
  - 004105F0 x220  [C]  sub dword ptr [esp + 4], 4 | jmp 0x410300 | int3 

槽值图例: C=.text代码 | P=_purecall跳转(仍在.text) | 0=零 | D=数据指针(.rdata/.data) | X=未映射 | B=无文件字节(BSS) | ?=不可读

## 3. 抽样 40 详查 (random.seed(20261115))
- 抽样判定分布: REAL=32 NOT=1 UNCERTAIN=7

### [1] vt=007ED2E4  类=LoadOptionsClass (.?AVLoadOptionsClass@@)  段=.rdata
- [vt-4]=007ED2E0 -> COL=008053B8: sig=0 offset=0 cdOffset=0 td=00829E80(VA) chd=008053A8(VA) td_struct_ok=True
- xr: text=3 rdata=0 data=0 | [pos-4]=X:unmapped | [pos+4]=0x0055A0D0 C
- 槽 0..11:
  [ 0] 0055A0D0  C     ; push esi | push edi
  [ 1] 00559D60  C     ; mov ecx, dword ptr [0x887640] | push ebx
  [ 2] 00559E40  C     ; push ebx | push esi
  [ 3] 00559EB0  C     ; mov eax, dword ptr [esp + 4] | push eax
  [ 4] 00559ED0  C     ; sub esp, 0x3f4 | push ebx
  [ 5] 0055A050  C     ; push 0x4c0 | push 0x829f5c
  [ 6] 0055A070  C     ; push 0x4c6 | push 0x829f5c
  [ 7] 0055A090  C     ; push 0x4cc | push 0x829f5c
  [ 8] 0055A0B0  C     ; push 0x4d2 | push 0x829f5c
  [ 9] 00805370  D  COL:PAVFileEntryClass::?$DynamicVectorClass(off=0)
  [10] 0055A460  C     ; push esi | mov esi, ecx
  [11] 0055A1B0  C     ; push ebx | push esi
- 连续代码游程 run=9
- **判定: REAL_VTABLE** — 前 9 槽连续代码, slot9=&COL(PAVFileEntryClass::?$DynamicVectorClass): 紧跟下一个虚表的 COL 头 => 本虚表共 9 槽

### [2] vt=007E284C  类=AircraftTypeClass (.?AVAircraftTypeClass@@)  段=.rdata
- [vt-4]=007E2848 -> COL=007FB508: sig=0 offset=4 cdOffset=0 td=00817FB8(VA) chd=007FB5A0(VA) td_struct_ok=True
- xr: text=5 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x004105E0 C
- 槽 0..11:
  [ 0] 004105E0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410260
  [ 1] 004105F0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410300
  [ 2] 00410600  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410310
  [ 3] 00410210  C     ; mov eax, dword ptr [esp + 4] | mov edx, dword ptr [eax - 4]
  [ 4] 00410220  C     ; mov eax, dword ptr [esp + 4] | mov eax, dword ptr [eax + 0xc]
  [ 5] 00410230  C     ; mov ecx, dword ptr [0xa8b230] | test ecx, ecx
  [ 6] 007FB5B0  D  COL:AircraftTypeClass(off=0)
  [ 7] 00410260  C     ; mov eax, dword ptr [esp + 0xc] | push ebx
  [ 8] 00410300  C     ; mov eax, 1 | ret 4
  [ 9] 00410310  C     ; mov eax, 1 | ret 4
  [10] 0041CEB0  C     ; mov eax, dword ptr [esp + 8] | test eax, eax
  [11] 00410450  C     ; mov ecx, dword ptr [esp + 4] | xor eax, eax
- 连续代码游程 run=6
- **判定: REAL_VTABLE** — 前 6 槽连续代码, slot6=&COL(AircraftTypeClass): 紧跟下一个虚表的 COL 头 => 本虚表共 6 槽

### [3] vt=007F3F6C  类=PAVSubTitle::?$DynamicVectorClass (.?AV?$DynamicVectorClass@PAVSubTitle@@@@)  段=.rdata
- [vt-4]=007F3F68 -> COL=0080B530: sig=0 offset=0 cdOffset=0 td=008422D0(VA) chd=0080B520(VA) td_struct_ok=True
- xr: text=1 rdata=0 data=0 | [pos-4]=X:unmapped | [pos+4]=0x006CA9C0 C
- 槽 0..11:
  [ 0] 006CA9C0  C     ; push esi | mov esi, ecx
  [ 1] 006CA820  C     ; push ebx | push esi
  [ 2] 006CA860  C     ; push ebx | push ebp
  [ 3] 006CA7C0  C     ; push ebx | push esi
  [ 4] 006CA910  C     ; mov edx, dword ptr [ecx + 0x10] | xor eax, eax
  [ 5] 006CA7F0  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 006CA810  C     ; mov eax, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 4]
  [ 7] 0080B560  D  COL:PAVSubTitle::?$VectorClass(off=0)
  [ 8] 006CAB50  C     ; push esi | mov esi, ecx
  [ 9] 006CA820  C     ; push ebx | push esi
  [10] 006CAA10  C     ; push ebx | push ebp
  [11] 006CAAC0  C     ; push ebx | push esi
- 连续代码游程 run=7
- **判定: REAL_VTABLE** — 前 7 槽连续代码, slot7=&COL(PAVSubTitle::?$VectorClass): 紧跟下一个虚表的 COL 头 => 本虚表共 7 槽

### [4] vt=007E86DC  类=PAVEgoClass::?$DynamicVectorClass (.?AV?$DynamicVectorClass@PAVEgoClass@@@@)  段=.rdata
- [vt-4]=007E86D8 -> COL=00800360: sig=0 offset=0 cdOffset=0 td=008207A8(VA) chd=00800350(VA) td_struct_ok=True
- xr: text=1 rdata=0 data=0 | [pos-4]=X:unmapped | [pos+4]=0x004C4CB0 C
- 槽 0..11:
  [ 0] 004C4CB0  C     ; push esi | mov esi, ecx
  [ 1] 004C4A00  C     ; push ebx | push esi
  [ 2] 004C4B80  C     ; push ebx | push ebp
  [ 3] 004C49A0  C     ; push ebx | push esi
  [ 4] 004C4C30  C     ; mov edx, dword ptr [ecx + 0x10] | xor eax, eax
  [ 5] 004C49D0  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 004C49F0  C     ; mov eax, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 4]
  [ 7] 00800390  D  COL:PAVEgoClass::?$VectorClass(off=0)
  [ 8] 004C4C60  C     ; push esi | mov esi, ecx
  [ 9] 004C4A00  C     ; push ebx | push esi
  [10] 004C4A40  C     ; push ebx | push ebp
  [11] 004C4AF0  C     ; push ebx | push esi
- 连续代码游程 run=7
- **判定: REAL_VTABLE** — 前 7 槽连续代码, slot7=&COL(PAVEgoClass::?$VectorClass): 紧跟下一个虚表的 COL 头 => 本虚表共 7 槽

### [5] vt=007EEEB0  类=MultiplayerGameMode::VMultiplayerManBattle::?$Initializer (.?AV?$Initializer@VMultiplayerManBattle@@@MultiplayerGameMode@@)  段=.rdata
- [vt-4]=007EEEAC -> COL=008071A8: sig=0 offset=0 cdOffset=0 td=00830AF8(VA) chd=00807198(VA) td_struct_ok=True
- xr: text=1 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x005D8010 C
- 槽 0..11:
  [ 0] 005D8010  C     ; mov al, byte ptr [esp + 4] | push esi
  [ 1] 005D81B0  C     ; push 0x40 | call 0x7c8e17
  [ 2] 008071F8  D  COL:MultiplayerGameMode::VMultiplayerBattle::?$Initializer(off=0)
  [ 3] 005D7FF0  C     ; mov al, byte ptr [esp + 4] | push esi
  [ 4] 005D8170  C     ; push 0x40 | call 0x7c8e17
  [ 5] 00000000  0  
  [ 6] 00000000  0  
  [ 7] 404E0000  X  unmapped
  [ 8] A2529D39  X  unmapped
  [ 9] 3F91DF46  X  unmapped
  [10] 00807278  D  COL:MultiplayerTeam(off=0)
  [11] 005D8D50  C     ; push esi | mov esi, ecx
- 连续代码游程 run=2
- **判定: UNCERTAIN** — 仅 2 个代码槽, slot2=&COL(MultiplayerGameMode::VMultiplayerBattle::?$Initializer): 短代码段后内嵌 COL 指针, 疑似 pos 扫描假阳性(或 2 槽小虚表)

### [6] vt=007E9344  类=LinkClass (.?AVLinkClass@@)  段=.rdata
- [vt-4]=007E9340 -> COL=00800AE0: sig=0 offset=0 cdOffset=0 td=0081B790(VA) chd=00800AD0(VA) td_struct_ok=True
- xr: text=3 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x004E1AD0 C
- 槽 0..11:
  [ 0] 004E1AD0  C     ; push esi | mov esi, ecx
  [ 1] 00556620  C     ; mov eax, dword ptr [ecx + 4] | ret 
  [ 2] 00556630  C     ; mov eax, dword ptr [ecx + 8] | ret 
  [ 3] 005566A0  C     ; push esi | mov esi, ecx
  [ 4] 00556700  C     ; push esi | mov esi, ecx
  [ 5] 005566D0  C     ; push esi | mov esi, ecx
  [ 6] 00556640  C     ; mov eax, dword ptr [ecx + 8] | lea edx, [ecx + 8]
  [ 7] 00556670  C     ; mov eax, dword ptr [ecx + 4] | lea edx, [ecx + 4]
  [ 8] 005565F0  C     ; xor eax, eax | mov dword ptr [ecx + 4], eax
  [ 9] 00556730  C     ; push ebx | push esi
  [10] 00000000  0  
  [11] 00000000  0  
- 连续代码游程 run=12
- **判定: REAL_VTABLE** — 槽0..11 全为代码或0; 连续代码指针

### [7] vt=007F3A50  类=VScriptClass::?$TClassFactory (.?AV?$TClassFactory@VScriptClass@@@@)  段=.rdata
- [vt-4]=007F3A4C -> COL=0080A618: sig=0 offset=0 cdOffset=0 td=00841588(VA) chd=0080A608(VA) td_struct_ok=True
- xr: text=1 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x006C1CD0 C
- 槽 0..11:
  [ 0] 006C1CD0  C     ; mov eax, dword ptr [esp + 0xc] | push ebx
  [ 1] 006C1D40  C     ; mov eax, dword ptr [esp + 4] | add eax, 4
  [ 2] 006C1D60  C     ; push esi | push edi
  [ 3] 006C1D90  C     ; push esi | push edi
  [ 4] 006C1E10  C     ; mov eax, dword ptr [esp + 8] | test eax, eax
  [ 5] 0080A668  D  COL:VScriptTypeClass::?$TClassFactory(off=0)
  [ 6] 006C1E50  C     ; mov eax, dword ptr [esp + 0xc] | push ebx
  [ 7] 006C1EC0  C     ; mov eax, dword ptr [esp + 4] | add eax, 4
  [ 8] 006C1EE0  C     ; push esi | push edi
  [ 9] 006C1F10  C     ; push esi | push edi
  [10] 006C1F90  C     ; mov eax, dword ptr [esp + 8] | test eax, eax
  [11] 0080A6B8  D  COL:VTagClass::?$TClassFactory(off=0)
- 连续代码游程 run=5
- **判定: REAL_VTABLE** — 前 5 槽连续代码, slot5=&COL(VScriptTypeClass::?$TClassFactory): 紧跟下一个虚表的 COL 头 => 本虚表共 5 槽

### [8] vt=007E9EC4  类=PAVUnitClass::?$VectorClass (.?AV?$VectorClass@PAVUnitClass@@@@)  段=.rdata
- [vt-4]=007E9EC0 -> COL=008013E0: sig=0 offset=0 cdOffset=0 td=00823310(VA) chd=008013D0(VA) td_struct_ok=True
- xr: text=3 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x004EFF30 C
- 槽 0..11:
  [ 0] 004EFF30  C     ; push esi | mov esi, ecx
  [ 1] 004EB980  C     ; push ebx | push esi
  [ 2] 004EB9C0  C     ; push ebx | push ebp
  [ 3] 004EBA70  C     ; push ebx | push esi
  [ 4] 004EBAA0  C     ; mov al, byte ptr [ecx + 0xc] | push esi
  [ 5] 004EBAE0  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 004E88F0  C     ; mov eax, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 4]
  [ 7] 00801448  D  COL:PAVHouseClass::?$DynamicVectorClass(off=0)
  [ 8] 004F0020  C     ; push esi | mov esi, ecx
  [ 9] 004EBBE0  C     ; push ebx | push esi
  [10] 004EBD60  C     ; push ebx | push ebp
  [11] 004E8900  C     ; push ebx | push esi
- 连续代码游程 run=7
- **判定: REAL_VTABLE** — 前 7 槽连续代码, slot7=&COL(PAVHouseClass::?$DynamicVectorClass): 紧跟下一个虚表的 COL 头 => 本虚表共 7 槽

### [9] vt=007E5480  类=G::?$RLEBlitTransLucent25ZReadWrite (.?AV?$RLEBlitTransLucent25ZReadWrite@G@@)  段=.rdata
- [vt-4]=007E547C -> COL=007FEA18: sig=0 offset=0 cdOffset=0 td=0081E9B8(VA) chd=007FEA08(VA) td_struct_ok=True
- xr: text=1 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x0049A9E0 C
- 槽 0..11:
  [ 0] 0049A9E0  C     ; mov al, byte ptr [esp + 4] | push esi
  [ 1] 00497760  C     ; push ecx | mov eax, dword ptr [esp + 0x14]
  [ 2] 00497880  C     ; mov edx, dword ptr [esp + 0x28] | mov eax, dword ptr [ecx]
  [ 3] 007FE798  D  COL:G::?$RLEBlitTransLucent50ZReadWrite(off=0)
  [ 4] 0049A9C0  C     ; mov al, byte ptr [esp + 4] | push esi
  [ 5] 00497610  C     ; push ecx | mov eax, dword ptr [esp + 0x1c]
  [ 6] 00497720  C     ; mov edx, dword ptr [esp + 0x28] | mov eax, dword ptr [ecx]
  [ 7] 007FDC58  D  COL:G::?$RLEBlitTransLucent75ZReadWrite(off=0)
  [ 8] 0049A9A0  C     ; mov al, byte ptr [esp + 4] | push esi
  [ 9] 004974B0  C     ; push ecx | mov eax, dword ptr [esp + 0x14]
  [10] 004975D0  C     ; mov edx, dword ptr [esp + 0x28] | mov eax, dword ptr [ecx]
  [11] 007FED88  D  COL:G::?$RLEBlitTransDarkenZReadWrite(off=0)
- 连续代码游程 run=3
- **判定: REAL_VTABLE** — 前 3 槽连续代码, slot3=&COL(G::?$RLEBlitTransLucent50ZReadWrite): 紧跟下一个虚表的 COL 头 => 本虚表共 3 槽

### [10] vt=007E3AA4  类=BuildingLightClass (.?AVBuildingLightClass@@)  段=.rdata
- [vt-4]=007E3AA0 -> COL=007FBFA0: sig=0 offset=12 cdOffset=0 td=00818BE0(VA) chd=007FC030(VA) td_struct_ok=True
- xr: text=4 rdata=0 data=0 | [pos-4]=X:unmapped | [pos+4]=0x00410590 C
- 槽 0..11:
  [ 0] 00410590  C     ; ret 4 | nop 
  [ 1] 007FBFB8  D  COL:BuildingLightClass(off=8)
  [ 2] 00410580  C     ; xor al, al | ret 8
  [ 3] 007FBFD0  D  COL:BuildingLightClass(off=4)
  [ 4] 004105E0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410260
  [ 5] 004105F0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410300
  [ 6] 00410600  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410310
  [ 7] 00410210  C     ; mov eax, dword ptr [esp + 4] | mov edx, dword ptr [eax - 4]
  [ 8] 00410220  C     ; mov eax, dword ptr [esp + 4] | mov eax, dword ptr [eax + 0xc]
  [ 9] 00410230  C     ; mov ecx, dword ptr [0xa8b230] | test ecx, ecx
  [10] 007FC040  D  COL:BuildingLightClass(off=0)
  [11] 00410260  C     ; mov eax, dword ptr [esp + 0xc] | push ebx
- 连续代码游程 run=1
- **判定: UNCERTAIN** — 仅 1 个代码槽, slot1=&COL(BuildingLightClass): 短代码段后内嵌 COL 指针, 疑似 pos 扫描假阳性(或 1 槽小虚表)

### [11] vt=007EABE8  类=PBVUnitTypeClass::?$TypeList (.?AV?$TypeList@PBVUnitTypeClass@@@@)  段=.rdata
- [vt-4]=007EABE4 -> COL=00802FA0: sig=0 offset=0 cdOffset=0 td=00825190(VA) chd=00802F90(VA) td_struct_ok=True
- xr: text=17 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x00512A40 C
- 槽 0..11:
  [ 0] 00512A40  C     ; push esi | mov esi, ecx
  [ 1] 00513010  C     ; push ebx | push esi
  [ 2] 00513240  C     ; push ebx | push ebp
  [ 3] 00512900  C     ; push ebx | push esi
  [ 4] 00513340  C     ; mov edx, dword ptr [ecx + 0x10] | xor eax, eax
  [ 5] 00512930  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 00512950  C     ; mov eax, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 4]
  [ 7] 00803020  D  COL:PBVInfantryTypeClass::?$TypeList(off=0)
  [ 8] 005129F0  C     ; push esi | mov esi, ecx
  [ 9] 00512C40  C     ; push ebx | push esi
  [10] 00512E70  C     ; push ebx | push ebp
  [11] 005128A0  C     ; push ebx | push esi
- 连续代码游程 run=7
- **判定: REAL_VTABLE** — 前 7 槽连续代码, slot7=&COL(PBVInfantryTypeClass::?$TypeList): 紧跟下一个虚表的 COL 头 => 本虚表共 7 槽

### [12] vt=007F55DC  类=TextButtonClass (.?AVTextButtonClass@@)  段=.rdata
- [vt-4]=007F55D8 -> COL=0080C638: sig=0 offset=0 cdOffset=0 td=00844720(VA) chd=0080C628(VA) td_struct_ok=True
- xr: text=2 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x00720210 C
- 槽 0..11:
  [ 0] 00720210  C     ; push esi | mov esi, ecx
  [ 1] 004E14A0  C     ; jmp 0x556620 | nop 
  [ 2] 004E14B0  C     ; jmp 0x556630 | nop 
  [ 3] 005566A0  C     ; push esi | mov esi, ecx
  [ 4] 00556700  C     ; push esi | mov esi, ecx
  [ 5] 005566D0  C     ; push esi | mov esi, ecx
  [ 6] 00556640  C     ; mov eax, dword ptr [ecx + 8] | lea edx, [ecx + 8]
  [ 7] 00556670  C     ; mov eax, dword ptr [ecx + 4] | lea edx, [ecx + 4]
  [ 8] 005565F0  C     ; xor eax, eax | mov dword ptr [ecx + 4], eax
  [ 9] 004E1480  C     ; push esi | mov esi, ecx
  [10] 004E1640  C     ; sub esp, 0xc | push ebx
  [11] 004E1570  C     ; push esi | mov esi, ecx
- 连续代码游程 run=12
- **判定: REAL_VTABLE** — 槽0..11 全为代码或0; 连续代码指针

### [13] vt=007E9D64  类=PAVParticleClass::?$DynamicVectorClass (.?AV?$DynamicVectorClass@PAVParticleClass@@@@)  段=.rdata
- [vt-4]=007E9D60 -> COL=008010B8: sig=0 offset=0 cdOffset=0 td=00823138(VA) chd=008010A8(VA) td_struct_ok=True
- xr: text=4 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x004EF850 C
- 槽 0..11:
  [ 0] 004EF850  C     ; push esi | mov esi, ecx
  [ 1] 004E9DE0  C     ; push ebx | push esi
  [ 2] 004E9F60  C     ; push ebx | push ebp
  [ 3] 004E8470  C     ; push ebx | push esi
  [ 4] 004EA010  C     ; mov edx, dword ptr [ecx + 0x10] | xor eax, eax
  [ 5] 004E84A0  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 004E84C0  C     ; mov eax, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 4]
  [ 7] 008010E8  D  COL:PAVParticleClass::?$VectorClass(off=0)
  [ 8] 004EF800  C     ; push esi | mov esi, ecx
  [ 9] 004E9DE0  C     ; push ebx | push esi
  [10] 004E9E20  C     ; push ebx | push ebp
  [11] 004E9ED0  C     ; push ebx | push esi
- 连续代码游程 run=7
- **判定: REAL_VTABLE** — 前 7 槽连续代码, slot7=&COL(PAVParticleClass::?$VectorClass): 紧跟下一个虚表的 COL 头 => 本虚表共 7 槽

### [14] vt=007E6114  类=DisplayClass (.?AVDisplayClass@@)  段=.rdata
- [vt-4]=007E6110 -> COL=007FFCB8: sig=0 offset=0 cdOffset=0 td=00816BD8(VA) chd=007FFCA8(VA) td_struct_ok=True
- xr: text=2 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x004F4240 C
- 槽 0..11:
  [ 0] 004F4240  C     ; mov edx, dword ptr [esp + 0xc] | push esi
  [ 1] 0040D230  C     ; mov eax, 1 | ret 4
  [ 2] 0040D240  C     ; mov eax, 1 | ret 4
  [ 3] 005656D0  C     ; push ecx | mov ax, word ptr [esp + 0xe]
  [ 4] 004AEBF0  C     ; push esi | mov esi, ecx
  [ 5] 004A8850  C     ; sub esp, 0x20 | push esi
  [ 6] 004F42B0  C     ; push esi | mov esi, ecx
  [ 7] 004A88C0  C     ; push esi | mov esi, ecx
  [ 8] 004A8930  C     ; push esi | mov esi, ecx
  [ 9] 004F4320  C     ; sub esp, 8 | push ebp
  [10] 004A9700  C     ; mov eax, dword ptr [esp + 8] | mov edx, dword ptr [esp + 4]
  [11] 004F43F0  C     ; mov ecx, dword ptr [esp + 4] | mov eax, dword ptr [ecx]
- 连续代码游程 run=12
- **判定: REAL_VTABLE** — 槽0..11 全为代码或0; 连续代码指针

### [15] vt=007E4EC0  类=CellClass (.?AVCellClass@@)  段=.rdata
- [vt-4]=007E4EBC -> COL=007FCFE0: sig=0 offset=12 cdOffset=0 td=0081CD70(VA) chd=007FD068(VA) td_struct_ok=True
- xr: text=4 rdata=0 data=0 | [pos-4]=X:unmapped | [pos+4]=0x00410590 C
- 槽 0..11:
  [ 0] 00410590  C     ; ret 4 | nop 
  [ 1] 007FCFF8  D  COL:CellClass(off=8)
  [ 2] 00410580  C     ; xor al, al | ret 8
  [ 3] 007FD010  D  COL:CellClass(off=4)
  [ 4] 004105E0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410260
  [ 5] 004105F0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410300
  [ 6] 00410600  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410310
  [ 7] 00487E50  C     ; mov eax, 0xb | ret 4
  [ 8] 00410220  C     ; mov eax, dword ptr [esp + 4] | mov eax, dword ptr [eax + 0xc]
  [ 9] 00410230  C     ; mov ecx, dword ptr [0xa8b230] | test ecx, ecx
  [10] 007FD078  D  COL:CellClass(off=0)
  [11] 00410260  C     ; mov eax, dword ptr [esp + 0xc] | push ebx
- 连续代码游程 run=1
- **判定: UNCERTAIN** — 仅 1 个代码槽, slot1=&COL(CellClass): 短代码段后内嵌 COL 指针, 疑似 pos 扫描假阳性(或 1 槽小虚表)

### [16] vt=007F69F8  类=WalkLocomotionClass (.?AVWalkLocomotionClass@@)  段=.rdata
- [vt-4]=007F69F4 -> COL=0080D240: sig=0 offset=4 cdOffset=0 td=00847BF0(VA) chd=0080D298(VA) td_struct_ok=True
- xr: text=4 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x0075CC30 C
- 槽 0..11:
  [ 0] 0075CC30  C     ; sub dword ptr [esp + 4], 4 | jmp 0x75c7f0
  [ 1] 0075CC40  C     ; sub dword ptr [esp + 4], 4 | jmp 0x75cb80
  [ 2] 0075CC50  C     ; sub dword ptr [esp + 4], 4 | jmp 0x75cb90
  [ 3] 0055A710  C     ; mov ecx, dword ptr [esp + 4] | mov eax, dword ptr [esp + 8]
  [ 4] 0075AB30  C     ; mov eax, dword ptr [esp + 4] | mov al, byte ptr [eax + 0x30]
  [ 5] 0075ABA0  C     ; push esi | mov esi, dword ptr [esp + 8]
  [ 6] 0075AC00  C     ; mov eax, dword ptr [esp + 4] | mov edx, dword ptr [0xb45be8]
  [ 7] 0055ABF0  C     ; xor eax, eax | ret 8
  [ 8] 0055ABE0  C     ; mov al, 1 | ret 4
  [ 9] 0055A730  C     ; sub esp, 0x34 | push esi
  [10] 0055A7D0  C     ; sub esp, 0x74 | push ebx
  [11] 0055ABD0  C     ; mov eax, dword ptr [esp + 8] | xor ecx, ecx
- 连续代码游程 run=12
- **判定: REAL_VTABLE** — 槽0..11 全为代码或0; 连续代码指针

### [17] vt=007F4664  类=TaskForceClass (.?AVTaskForceClass@@)  段=.rdata
- [vt-4]=007F4660 -> COL=0080BD38: sig=0 offset=4 cdOffset=0 td=00842D98(VA) chd=0080BD98(VA) td_struct_ok=True
- xr: text=6 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x004105E0 C
- 槽 0..11:
  [ 0] 004105E0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410260
  [ 1] 004105F0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410300
  [ 2] 00410600  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410310
  [ 3] 00410210  C     ; mov eax, dword ptr [esp + 4] | mov edx, dword ptr [eax - 4]
  [ 4] 00410220  C     ; mov eax, dword ptr [esp + 4] | mov eax, dword ptr [eax + 0xc]
  [ 5] 00410230  C     ; mov ecx, dword ptr [0xa8b230] | test ecx, ecx
  [ 6] 0080BDA8  D  COL:TaskForceClass(off=0)
  [ 7] 00410260  C     ; mov eax, dword ptr [esp + 0xc] | push ebx
  [ 8] 00410300  C     ; mov eax, 1 | ret 4
  [ 9] 00410310  C     ; mov eax, 1 | ret 4
  [10] 006E8710  C     ; mov eax, dword ptr [esp + 8] | test eax, eax
  [11] 00410450  C     ; mov ecx, dword ptr [esp + 4] | xor eax, eax
- 连续代码游程 run=6
- **判定: REAL_VTABLE** — 前 6 槽连续代码, slot6=&COL(TaskForceClass): 紧跟下一个虚表的 COL 头 => 本虚表共 6 槽

### [18] vt=007E856C  类=PAUButtonFadeEffect::?$DynamicVectorClass (.?AV?$DynamicVectorClass@PAUButtonFadeEffect@@@@)  段=.rdata
- [vt-4]=007E8568 -> COL=00800210: sig=0 offset=0 cdOffset=0 td=00820458(VA) chd=00800200(VA) td_struct_ok=True
- xr: text=1 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x004BA200 C
- 槽 0..11:
  [ 0] 004BA200  C     ; push esi | mov esi, ecx
  [ 1] 004B9CA0  C     ; push ebx | push esi
  [ 2] 004B9E20  C     ; push ebx | push ebp
  [ 3] 004B9BE0  C     ; push ebx | push esi
  [ 4] 004B9ED0  C     ; mov edx, dword ptr [ecx + 0x10] | xor eax, eax
  [ 5] 004B9C10  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 004B9C30  C     ; mov eax, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 4]
  [ 7] 008000E0  D  COL:PAVTechnoTypeClass::?$DynamicVectorClass(off=0)
  [ 8] 004BA160  C     ; push esi | mov esi, ecx
  [ 9] 00477FC0  C     ; push ebx | push esi
  [10] 00478140  C     ; push ebx | push ebp
  [11] 004778A0  C     ; push ebx | push esi
- 连续代码游程 run=7
- **判定: REAL_VTABLE** — 前 7 槽连续代码, slot7=&COL(PAVTechnoTypeClass::?$DynamicVectorClass): 紧跟下一个虚表的 COL 头 => 本虚表共 7 槽

### [19] vt=007F550C  类=PAVTEventClass::?$DynamicVectorClass (.?AV?$DynamicVectorClass@PAVTEventClass@@@@)  段=.rdata
- [vt-4]=007F5508 -> COL=0080C500: sig=0 offset=0 cdOffset=0 td=008446C0(VA) chd=0080C4F0(VA) td_struct_ok=True
- xr: text=1 rdata=0 data=0 | [pos-4]=X:unmapped | [pos+4]=0x0071FEB0 C
- 槽 0..11:
  [ 0] 0071FEB0  C     ; push esi | mov esi, ecx
  [ 1] 0071FC00  C     ; push ebx | push esi
  [ 2] 0071FD80  C     ; push ebx | push ebp
  [ 3] 0071FBA0  C     ; push ebx | push esi
  [ 4] 0071FE30  C     ; mov edx, dword ptr [ecx + 0x10] | xor eax, eax
  [ 5] 0071FBD0  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 0071FBF0  C     ; mov eax, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 4]
  [ 7] 0080C530  D  COL:PAVTEventClass::?$VectorClass(off=0)
  [ 8] 0071FE60  C     ; push esi | mov esi, ecx
  [ 9] 0071FC00  C     ; push ebx | push esi
  [10] 0071FC40  C     ; push ebx | push ebp
  [11] 0071FCF0  C     ; push ebx | push esi
- 连续代码游程 run=7
- **判定: REAL_VTABLE** — 前 7 槽连续代码, slot7=&COL(PAVTEventClass::?$VectorClass): 紧跟下一个虚表的 COL 头 => 本虚表共 7 槽

### [20] vt=007EEA74  类=PAVMSAnimEntry::?$DynamicVectorClass (.?AV?$DynamicVectorClass@PAVMSAnimEntry@@@@)  段=.rdata
- [vt-4]=007EEA70 -> COL=008068C0: sig=0 offset=0 cdOffset=0 td=008301C8(VA) chd=008068B0(VA) td_struct_ok=True
- xr: text=1 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x005D1990 C
- 槽 0..11:
  [ 0] 005D1990  C     ; push esi | mov esi, ecx
  [ 1] 005D1200  C     ; push ebx | push esi
  [ 2] 005D1380  C     ; push ebx | push ebp
  [ 3] 005D0730  C     ; push ebx | push esi
  [ 4] 005D1430  C     ; mov edx, dword ptr [ecx + 0x10] | xor eax, eax
  [ 5] 005D0760  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 005D0780  C     ; mov eax, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 4]
  [ 7] 00806928  D  COL:PAVMapStage::?$DynamicVectorClass(off=0)
  [ 8] 005D18F0  C     ; push esi | mov esi, ecx
  [ 9] 005D0FA0  C     ; push ebx | push esi
  [10] 005D1120  C     ; push ebx | push ebp
  [11] 005D06D0  C     ; push ebx | push esi
- 连续代码游程 run=7
- **判定: REAL_VTABLE** — 前 7 槽连续代码, slot7=&COL(PAVMapStage::?$DynamicVectorClass): 紧跟下一个虚表的 COL 头 => 本虚表共 7 槽

### [21] vt=007EEB54  类=VPoint2D::?$DynamicVectorClass (.?AV?$DynamicVectorClass@VPoint2D@@@@)  段=.rdata
- [vt-4]=007EEB50 -> COL=00806A88: sig=0 offset=0 cdOffset=0 td=008303A8(VA) chd=00806A78(VA) td_struct_ok=True
- xr: text=6 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x005D1710 C
- 槽 0..11:
  [ 0] 005D1710  C     ; push esi | mov esi, ecx
  [ 1] 005D07F0  C     ; mov eax, dword ptr [esp + 4] | push ebx
  [ 2] 005D09C0  C     ; push ebx | push ebp
  [ 3] 005D05A0  C     ; push ebx | push esi
  [ 4] 005D0AA0  C     ; mov edx, dword ptr [ecx + 0x10] | push ebx
  [ 5] 005D05D0  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 005D05F0  C     ; mov edx, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 8]
  [ 7] 00806B88  D  COL:VPoint2D::?$VectorClass(off=0)
  [ 8] 005D16C0  C     ; push esi | mov esi, ecx
  [ 9] 005D07F0  C     ; mov eax, dword ptr [esp + 4] | push ebx
  [10] 005D0850  C     ; push ebx | push ebp
  [11] 005D0920  C     ; push ebx | push esi
- 连续代码游程 run=7
- **判定: REAL_VTABLE** — 前 7 槽连续代码, slot7=&COL(VPoint2D::?$VectorClass): 紧跟下一个虚表的 COL 头 => 本虚表共 7 槽

### [22] vt=007E5BE4  类=PAD::PAV?$DynamicVectorClass::?$DynamicVectorClass (.?AV?$DynamicVectorClass@PAV?$DynamicVectorClass@PAD@@@@)  段=.rdata
- [vt-4]=007E5BE0 -> COL=007FF5C8: sig=0 offset=0 cdOffset=0 td=0081F2C8(VA) chd=007FF5B8(VA) td_struct_ok=True
- xr: text=2 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x0049F040 C
- 槽 0..11:
  [ 0] 0049F040  C     ; push esi | mov esi, ecx
  [ 1] 0049EB50  C     ; push ebx | push esi
  [ 2] 0049ED30  C     ; push ebx | push ebp
  [ 3] 0049E9B0  C     ; push ebx | push esi
  [ 4] 0049EDE0  C     ; mov edx, dword ptr [ecx + 0x10] | xor eax, eax
  [ 5] 0049E9E0  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 0049EA00  C     ; mov eax, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 4]
  [ 7] 007FF5F8  D  COL:PAD::PAV?$DynamicVectorClass::?$VectorClass(off=0)
  [ 8] 0049EFF0  C     ; push esi | mov esi, ecx
  [ 9] 0049EB50  C     ; push ebx | push esi
  [10] 0049EB90  C     ; push ebx | push ebp
  [11] 0049EC40  C     ; push ebx | push esi
- 连续代码游程 run=7
- **判定: REAL_VTABLE** — 前 7 槽连续代码, slot7=&COL(PAD::PAV?$DynamicVectorClass::?$VectorClass): 紧跟下一个虚表的 COL 头 => 本虚表共 7 槽

### [23] vt=007EF720  类=OwnerDraw::DialogControl (.?AVDialogControl@OwnerDraw@@)  段=.rdata
- [vt-4]=007EF71C -> COL=008077D0: sig=0 offset=0 cdOffset=0 td=00836408(VA) chd=008077C0(VA) td_struct_ok=True
- xr: text=5 rdata=0 data=0 | [pos-4]=X:unmapped | [pos+4]=0x006244A0 C
- 槽 0..11:
  [ 0] 006244A0  C     ; mov al, byte ptr [esp + 4] | push esi
  [ 1] 004C9150  C     ; xor eax, eax | ret 
  [ 2] 004C9150  C     ; xor eax, eax | ret 
  [ 3] 004C9150  C     ; xor eax, eax | ret 
  [ 4] 004C9150  C     ; xor eax, eax | ret 
  [ 5] 00807820  D  COL:OwnerDraw::SimpleDialogControl(off=0)
  [ 6] 006244C0  C     ; mov al, byte ptr [esp + 4] | push esi
  [ 7] 00624140  C     ; mov eax, dword ptr [esp + 8] | push esi
  [ 8] 006241C0  C     ; mov al, byte ptr [ecx + 8] | ret 
  [ 9] 006241D0  C     ; mov eax, dword ptr [ecx + 4] | ret 
  [10] 006241E0  C     ; xor al, al | ret 
  [11] 00807888  D  COL:VHSVClass::?$DynamicVectorClass(off=0)
- 连续代码游程 run=5
- **判定: REAL_VTABLE** — 前 5 槽连续代码, slot5=&COL(OwnerDraw::SimpleDialogControl): 紧跟下一个虚表的 COL 头 => 本虚表共 5 槽

### [24] vt=007F3C00  类=VInfantryClass::?$TClassFactory (.?AV?$TClassFactory@VInfantryClass@@@@)  段=.rdata
- [vt-4]=007F3BFC -> COL=0080ABB8: sig=0 offset=0 cdOffset=0 td=00841928(VA) chd=0080ABA8(VA) td_struct_ok=True
- xr: text=1 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x006C37D0 C
- 槽 0..11:
  [ 0] 006C37D0  C     ; mov eax, dword ptr [esp + 0xc] | push ebx
  [ 1] 006C3840  C     ; mov eax, dword ptr [esp + 4] | add eax, 4
  [ 2] 006C3860  C     ; push esi | push edi
  [ 3] 006C3890  C     ; push esi | push edi
  [ 4] 006C3910  C     ; mov eax, dword ptr [esp + 8] | test eax, eax
  [ 5] 0080AC08  D  COL:VAnimClass::?$TClassFactory(off=0)
  [ 6] 006C3950  C     ; mov eax, dword ptr [esp + 0xc] | push ebx
  [ 7] 006C39C0  C     ; mov eax, dword ptr [esp + 4] | add eax, 4
  [ 8] 006C39E0  C     ; push esi | push edi
  [ 9] 006C3A10  C     ; push esi | push edi
  [10] 006C3A90  C     ; mov eax, dword ptr [esp + 8] | test eax, eax
  [11] 0080AC58  D  COL:VAnimTypeClass::?$TClassFactory(off=0)
- 连续代码游程 run=5
- **判定: REAL_VTABLE** — 前 5 槽连续代码, slot5=&COL(VAnimClass::?$TClassFactory): 紧跟下一个虚表的 COL 头 => 本虚表共 5 槽

### [25] vt=007EF770  类=PAVSchemeNode::VHashString::U?$HashObject::?$DynamicVectorClass (.?AV?$DynamicVectorClass@U?$HashObject@VHashString@@PAVSchemeNode@@@@@@)  段=.rdata
- [vt-4]=007EF76C -> COL=008078F0: sig=0 offset=0 cdOffset=0 td=00836520(VA) chd=008078E0(VA) td_struct_ok=True
- xr: text=4 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x00628690 C
- 槽 0..11:
  [ 0] 00628690  C     ; mov al, byte ptr [esp + 4] | push ebx
  [ 1] 006288A0  C     ; push ebx | push ebp
  [ 2] 00628BB0  C     ; sub esp, 8 | push ebx
  [ 3] 00628800  C     ; push ebx | push esi
  [ 4] 00628D80  C     ; push ebx | push ebp
  [ 5] 00628830  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 00628860  C     ; mov eax, dword ptr [esp + 8] | push esi
  [ 7] 00807988  D  COL:PAVColorScheme::?$DynamicVectorClass(off=0)
  [ 8] 00628640  C     ; push esi | mov esi, ecx
  [ 9] 00627E10  C     ; push ebx | push esi
  [10] 00627F90  C     ; push ebx | push ebp
  [11] 00627D20  C     ; push ebx | push esi
- 连续代码游程 run=7
- **判定: REAL_VTABLE** — 前 7 槽连续代码, slot7=&COL(PAVColorScheme::?$DynamicVectorClass): 紧跟下一个虚表的 COL 头 => 本虚表共 7 槽

### [26] vt=007E920C  类=PAVAbstractClass::?$VectorClass (.?AV?$VectorClass@PAVAbstractClass@@@@)  段=.rdata
- [vt-4]=007E9208 -> COL=008009E0: sig=0 offset=0 cdOffset=0 td=008225B8(VA) chd=008009D0(VA) td_struct_ok=True
- xr: text=21 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x004E02D0 C
- 槽 0..11:
  [ 0] 004E02D0  C     ; push esi | mov esi, ecx
  [ 1] 004E0320  C     ; push ebx | push esi
  [ 2] 004E0360  C     ; push ebx | push ebp
  [ 3] 004E0410  C     ; push ebx | push esi
  [ 4] 004E0440  C     ; mov al, byte ptr [ecx + 0xc] | push esi
  [ 5] 004E0480  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 004E01E0  C     ; mov eax, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 4]
  [ 7] 9999999A  X  unmapped
  [ 8] 40719999  X  unmapped
  [ 9] 33333333  X  unmapped
  [10] 40733333  X  unmapped
  [11] 9999999A  X  unmapped
- 连续代码游程 run=7
- **判定: UNCERTAIN** — 前 7 槽连续代码, slot7=0x9999999A 为 X(unmapped); xr_text=21

### [27] vt=007F6B04  类=WarheadTypeClass (.?AVWarheadTypeClass@@)  段=.rdata
- [vt-4]=007F6B00 -> COL=0080D2C0: sig=0 offset=12 cdOffset=0 td=00847C18(VA) chd=0080D350(VA) td_struct_ok=True
- xr: text=5 rdata=0 data=0 | [pos-4]=X:unmapped | [pos+4]=0x00410590 C
- 槽 0..11:
  [ 0] 00410590  C     ; ret 4 | nop 
  [ 1] 0080D2D8  D  COL:WarheadTypeClass(off=8)
  [ 2] 00410580  C     ; xor al, al | ret 8
  [ 3] 0080D2F0  D  COL:WarheadTypeClass(off=4)
  [ 4] 004105E0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410260
  [ 5] 004105F0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410300
  [ 6] 00410600  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410310
  [ 7] 00410210  C     ; mov eax, dword ptr [esp + 4] | mov edx, dword ptr [eax - 4]
  [ 8] 00410220  C     ; mov eax, dword ptr [esp + 4] | mov eax, dword ptr [eax + 0xc]
  [ 9] 00410230  C     ; mov ecx, dword ptr [0xa8b230] | test ecx, ecx
  [10] 0080D360  D  COL:WarheadTypeClass(off=0)
  [11] 00410260  C     ; mov eax, dword ptr [esp + 0xc] | push ebx
- 连续代码游程 run=1
- **判定: UNCERTAIN** — 仅 1 个代码槽, slot1=&COL(WarheadTypeClass): 短代码段后内嵌 COL 指针, 疑似 pos 扫描假阳性(或 1 槽小虚表)

### [28] vt=007E38D0  类=VCell::?$VectorClass (.?AV?$VectorClass@VCell@@@@)  段=.rdata
- [vt-4]=007E38CC -> COL=007FBE90: sig=0 offset=0 cdOffset=0 td=00818938(VA) chd=007FBE80(VA) td_struct_ok=True
- xr: text=64 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x0042FBA0 C
- 槽 0..11:
  [ 0] 0042FBA0  C     ; push esi | mov esi, ecx
  [ 1] 0042F620  C     ; mov eax, dword ptr [esp + 4] | push ebx
  [ 2] 0042F6F0  C     ; push ebx | push ebp
  [ 3] 0042F7C0  C     ; push ebx | push esi
  [ 4] 0042F7F0  C     ; mov al, byte ptr [ecx + 0xc] | push ebx
  [ 5] 0042F840  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 0042F470  C     ; mov eax, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 8]
  [ 7] 007FBEC0  D  COL:VBaseNodeClass::?$VectorClass(off=0)
  [ 8] 0042FB50  C     ; push esi | mov esi, ecx
  [ 9] 0042F490  C     ; mov eax, dword ptr [esp + 4] | push ebx
  [10] 0042F9C0  C     ; push ecx | push ebx
  [11] 0042FAB0  C     ; push ebx | push esi
- 连续代码游程 run=7
- **判定: REAL_VTABLE** — 前 7 槽连续代码, slot7=&COL(VBaseNodeClass::?$VectorClass): 紧跟下一个虚表的 COL 头 => 本虚表共 7 槽

### [29] vt=007F317C  类=PAVSlaveManagerClass::?$VectorClass (.?AV?$VectorClass@PAVSlaveManagerClass@@@@)  段=.rdata
- [vt-4]=007F3178 -> COL=00809650: sig=0 offset=0 cdOffset=0 td=0083FC98(VA) chd=00809640(VA) td_struct_ok=True
- xr: text=3 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x006B19D0 C
- 槽 0..11:
  [ 0] 006B19D0  C     ; push esi | mov esi, ecx
  [ 1] 006B16D0  C     ; push ebx | push esi
  [ 2] 006B1710  C     ; push ebx | push ebp
  [ 3] 006B17C0  C     ; push ebx | push esi
  [ 4] 006B17F0  C     ; mov al, byte ptr [ecx + 0xc] | push esi
  [ 5] 006B1830  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 006B1460  C     ; mov eax, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 4]
  [ 7] 00809668  D  COL:SlaveManagerClass(off=12)
  [ 8] 00410590  C     ; ret 4 | nop 
  [ 9] 00809680  D  COL:SlaveManagerClass(off=8)
  [10] 00410580  C     ; xor al, al | ret 8
  [11] 00809698  D  COL:SlaveManagerClass(off=4)
- 连续代码游程 run=7
- **判定: REAL_VTABLE** — 前 7 槽连续代码, slot7=&COL(SlaveManagerClass): 紧跟下一个虚表的 COL 头 => 本虚表共 7 槽

### [30] vt=007E1964  类=MouseClass (.?AVMouseClass@@)  段=.rdata
- [vt-4]=007E1960 -> COL=007FAB38: sig=0 offset=0 cdOffset=0 td=00816C90(VA) chd=007FAB28(VA) td_struct_ok=True
- xr: text=4 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x004F4240 C
- 槽 0..11:
  [ 0] 004F4240  C     ; mov edx, dword ptr [esp + 0xc] | push esi
  [ 1] 0040D230  C     ; mov eax, 1 | ret 4
  [ 2] 0040D240  C     ; mov eax, 1 | ret 4
  [ 3] 005656D0  C     ; push ecx | mov ax, word ptr [esp + 0xe]
  [ 4] 0040D290  C     ; push ebx | mov ebx, ecx
  [ 5] 005BDF30  C     ; call 0x6d0260 | mov edx, 0xabf2dc
  [ 6] 004F42B0  C     ; push esi | mov esi, ecx
  [ 7] 005BDF50  C     ; push esi | mov esi, ecx
  [ 8] 0040D270  C     ; jmp 0x6d03a0 | nop 
  [ 9] 004F4320  C     ; sub esp, 8 | push ebp
  [10] 005BDDC0  C     ; sub esp, 0x10 | push ebx
  [11] 004F43F0  C     ; mov ecx, dword ptr [esp + 4] | mov eax, dword ptr [ecx]
- 连续代码游程 run=12
- **判定: REAL_VTABLE** — 槽0..11 全为代码或0; 连续代码指针

### [31] vt=007EF3A8  类=OverlayClass (.?AVOverlayClass@@)  段=.rdata
- [vt-4]=007EF3A4 -> COL=00807598: sig=0 offset=12 cdOffset=0 td=00833458(VA) chd=00807628(VA) td_struct_ok=True
- xr: text=4 rdata=0 data=0 | [pos-4]=D | [pos+4]=0x00410590 C
- 槽 0..11:
  [ 0] 00410590  C     ; ret 4 | nop 
  [ 1] 008075C8  D  COL:OverlayClass(off=4)
  [ 2] 004105E0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410260
  [ 3] 004105F0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410300
  [ 4] 00410600  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410310
  [ 5] 00410210  C     ; mov eax, dword ptr [esp + 4] | mov edx, dword ptr [eax - 4]
  [ 6] 00410220  C     ; mov eax, dword ptr [esp + 4] | mov eax, dword ptr [eax + 0xc]
  [ 7] 00410230  C     ; mov ecx, dword ptr [0xa8b230] | test ecx, ecx
  [ 8] 008075B0  D  COL:OverlayClass(off=8)
  [ 9] 00410580  C     ; xor al, al | ret 8
  [10] 00807638  D  COL:OverlayClass(off=0)
  [11] 00410260  C     ; mov eax, dword ptr [esp + 0xc] | push ebx
- 连续代码游程 run=1
- **判定: UNCERTAIN** — 仅 1 个代码槽, slot1=&COL(OverlayClass): 短代码段后内嵌 COL 指针, 疑似 pos 扫描假阳性(或 1 槽小虚表)

### [32] vt=007F6F6C  类=WorldDominationTour::VCampaignProperties::?$rc_ptr (.?AV?$rc_ptr@VCampaignProperties@WorldDominationTour@@@@)  段=.rdata
- [vt-4]=007F6F68 -> COL=0080D7A0: sig=0 offset=0 cdOffset=0 td=00848120(VA) chd=0080D790(VA) td_struct_ok=True
- xr: text=7 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x00765710 C
- 槽 0..11:
  [ 0] 00765710  C     ; push esi | mov esi, ecx
  [ 1] 0080D870  D  COL:WorldDominationTour::VHistory::?$rc_ptr(off=0)
  [ 2] 00765740  C     ; push esi | mov esi, ecx
  [ 3] 0080D820  D  COL:WorldDominationTour::VConflict::V?$rc_ptr::?$VectorClass(off=0)
  [ 4] 00765B60  C     ; push esi | mov esi, ecx
  [ 5] 007657F0  C     ; mov eax, dword ptr [esp + 4] | push ebx
  [ 6] 00765840  C     ; push ecx | push ebx
  [ 7] 00765960  C     ; push ebx | push esi
  [ 8] 00765990  C     ; mov al, byte ptr [ecx + 0xc] | push esi
  [ 9] 007659D0  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [10] 007656D0  C     ; mov eax, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 8]
  [11] 0080D8B8  D  COL:WorldDominationTour::VConflict::V?$rc_ptr::V?$DynamicVectorClass::WorldDominationTour::VConflict::V?$rc_ptr::?$VectorCursor(off=0)
- 连续代码游程 run=1
- **判定: UNCERTAIN** — 仅 1 个代码槽, slot1=&COL(WorldDominationTour::VHistory::?$rc_ptr): 短代码段后内嵌 COL 指针, 疑似 pos 扫描假阳性(或 1 槽小虚表)

### [33] vt=007ED1DC  类=PBG::?$DynamicVectorClass (.?AV?$DynamicVectorClass@PBG@@)  段=.rdata
- [vt-4]=007ED1D8 -> COL=00805280: sig=0 offset=0 cdOffset=0 td=00829DD0(VA) chd=00805270(VA) td_struct_ok=True
- xr: text=3 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x00558130 C
- 槽 0..11:
  [ 0] 00558130  C     ; push esi | mov esi, ecx
  [ 1] 00558240  C     ; push ebx | push esi
  [ 2] 005583C0  C     ; push ebx | push ebp
  [ 3] 005581E0  C     ; push ebx | push esi
  [ 4] 00558470  C     ; mov edx, dword ptr [ecx + 0x10] | xor eax, eax
  [ 5] 00558210  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 00558230  C     ; mov eax, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 4]
  [ 7] 008052B0  D  COL:PBG::?$VectorClass(off=0)
  [ 8] 005584A0  C     ; push esi | mov esi, ecx
  [ 9] 00558240  C     ; push ebx | push esi
  [10] 00558280  C     ; push ebx | push ebp
  [11] 00558330  C     ; push ebx | push esi
- 连续代码游程 run=7
- **判定: REAL_VTABLE** — 前 7 槽连续代码, slot7=&COL(PBG::?$VectorClass): 紧跟下一个虚表的 COL 头 => 本虚表共 7 槽

### [34] vt=007EE350  类=PAVCoopCampaignClass::?$DynamicVectorClass (.?AV?$DynamicVectorClass@PAVCoopCampaignClass@@@@)  段=.rdata
- [vt-4]=007EE34C -> COL=008061A8: sig=0 offset=0 cdOffset=0 td=0082DB70(VA) chd=00806198(VA) td_struct_ok=True
- xr: text=1 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x005C5990 C
- 槽 0..11:
  [ 0] 005C5990  C     ; push esi | mov esi, ecx
  [ 1] 005C55F0  C     ; push ebx | push esi
  [ 2] 005C5770  C     ; push ebx | push ebp
  [ 3] 005C50D0  C     ; push ebx | push esi
  [ 4] 005C5820  C     ; mov edx, dword ptr [ecx + 0x10] | xor eax, eax
  [ 5] 005C5100  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 005C5120  C     ; mov eax, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 4]
  [ 7] 00806210  D  COL:PAUNodeNameType::?$DynamicVectorClass(off=0)
  [ 8] 005C58F0  C     ; push esi | mov esi, ecx
  [ 9] 005C5390  C     ; push ebx | push esi
  [10] 005C5510  C     ; push ebx | push ebp
  [11] 005C5070  C     ; push ebx | push esi
- 连续代码游程 run=7
- **判定: REAL_VTABLE** — 前 7 槽连续代码, slot7=&COL(PAUNodeNameType::?$DynamicVectorClass): 紧跟下一个虚表的 COL 头 => 本虚表共 7 槽

### [35] vt=0087B17C  类=DropPodLocomotionClass (.?AVDropPodLocomotionClass@@)  段=.data
- [vt-4]=0087B178 -> COL=00800040: sig=0 offset=4 cdOffset=0 td=008202F8(VA) chd=00800098(VA) td_struct_ok=True
- xr: text=0 rdata=0 data=0 | [pos-4]=0 | [pos+4]=0x010000C0 X:unmapped
- 槽 0..11:
  [ 0] 010000C0  X  unmapped
  [ 1] 00000000  0  
  [ 2] 00000000  0  
  [ 3] 00800040  D  COL:DropPodLocomotionClass(off=4)
  [ 4] 010000C0  X  unmapped
  [ 5] 00000000  0  
  [ 6] 00000000  0  
  [ 7] 00A00060  B  no-raw
  [ 8] 012000E0  X  unmapped
  [ 9] 00000000  0  
  [10] 00000000  0  
  [11] 00A00060  B  no-raw
- 连续代码游程 run=0
- **判定: NOT_VTABLE** — slot0=0x010000C0 为 X(unmapped), 不是代码也不是0

### [36] vt=007EEF50  类=PBVMultiMission::?$VectorClass (.?AV?$VectorClass@PBVMultiMission@@@@)  段=.rdata
- [vt-4]=007EEF4C -> COL=00807310: sig=0 offset=0 cdOffset=0 td=00831A00(VA) chd=00807300(VA) td_struct_ok=True
- xr: text=6 rdata=0 data=0 | [pos-4]=D | [pos+4]=0x005EEEC0 C
- 槽 0..11:
  [ 0] 005EEEC0  C     ; push esi | mov esi, ecx
  [ 1] 005EEC10  C     ; push ebx | push esi
  [ 2] 005EEC50  C     ; push ebx | push ebp
  [ 3] 005EED00  C     ; push ebx | push esi
  [ 4] 005EED30  C     ; mov al, byte ptr [ecx + 0xc] | push esi
  [ 5] 005EED70  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 005EEC00  C     ; mov eax, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 4]
  [ 7] 008072C8  D  COL:PBVMultiMission::?$DynamicVectorClass(off=0)
  [ 8] 005EEF10  C     ; push esi | mov esi, ecx
  [ 9] 005EEC10  C     ; push ebx | push esi
  [10] 005EED90  C     ; push ebx | push ebp
  [11] 005EEBB0  C     ; push ebx | push esi
- 连续代码游程 run=7
- **判定: REAL_VTABLE** — 前 7 槽连续代码, slot7=&COL(PBVMultiMission::?$DynamicVectorClass): 紧跟下一个虚表的 COL 头 => 本虚表共 7 槽

### [37] vt=007EFE64  类=PAVPlanningNodeClass::?$VectorClass (.?AV?$VectorClass@PAVPlanningNodeClass@@@@)  段=.rdata
- [vt-4]=007EFE60 -> COL=00807F08: sig=0 offset=0 cdOffset=0 td=008368F8(VA) chd=00807EF8(VA) td_struct_ok=True
- xr: text=9 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x0063ED90 C
- 槽 0..11:
  [ 0] 0063ED90  C     ; push esi | mov esi, ecx
  [ 1] 0063E310  C     ; push ebx | push esi
  [ 2] 0063E350  C     ; push ebx | push ebp
  [ 3] 0063E400  C     ; push ebx | push esi
  [ 4] 0063E430  C     ; mov al, byte ptr [ecx + 0xc] | push esi
  [ 5] 0063E470  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 0063DC70  C     ; mov eax, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 4]
  [ 7] 00807F70  D  COL:PAVPlanningTokenClass::?$DynamicVectorClass(off=0)
  [ 8] 0063EF20  C     ; push esi | mov esi, ecx
  [ 9] 0063E950  C     ; push ebx | push esi
  [10] 0063EAD0  C     ; push ebx | push ebp
  [11] 0063DCE0  C     ; push ebx | push esi
- 连续代码游程 run=7
- **判定: REAL_VTABLE** — 前 7 槽连续代码, slot7=&COL(PAVPlanningTokenClass::?$DynamicVectorClass): 紧跟下一个虚表的 COL 头 => 本虚表共 7 槽

### [38] vt=007EE370  类=PAUNodeNameType::?$DynamicVectorClass (.?AV?$DynamicVectorClass@PAUNodeNameType@@@@)  段=.rdata
- [vt-4]=007EE36C -> COL=00806210: sig=0 offset=0 cdOffset=0 td=0082DBE0(VA) chd=00806200(VA) td_struct_ok=True
- xr: text=3 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x005C58F0 C
- 槽 0..11:
  [ 0] 005C58F0  C     ; push esi | mov esi, ecx
  [ 1] 005C5390  C     ; push ebx | push esi
  [ 2] 005C5510  C     ; push ebx | push ebp
  [ 3] 005C5070  C     ; push ebx | push esi
  [ 4] 005C55C0  C     ; mov edx, dword ptr [ecx + 0x10] | xor eax, eax
  [ 5] 005C50A0  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 005C50C0  C     ; mov eax, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 4]
  [ 7] 00806270  D  COL:PAUNodeNameType::?$VectorClass(off=0)
  [ 8] 005C58A0  C     ; push esi | mov esi, ecx
  [ 9] 005C5390  C     ; push ebx | push esi
  [10] 005C53D0  C     ; push ebx | push ebp
  [11] 005C5480  C     ; push ebx | push esi
- 连续代码游程 run=7
- **判定: REAL_VTABLE** — 前 7 槽连续代码, slot7=&COL(PAUNodeNameType::?$VectorClass): 紧跟下一个虚表的 COL 头 => 本虚表共 7 槽

### [39] vt=007E5380  类=G::?$RLEBlitTransLucent75AlphaZReadWrite (.?AV?$RLEBlitTransLucent75AlphaZReadWrite@G@@)  段=.rdata
- [vt-4]=007E537C -> COL=007FDC08: sig=0 offset=0 cdOffset=0 td=0081E140(VA) chd=007FDBF8(VA) td_struct_ok=True
- xr: text=2 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x0049ADC0 C
- 槽 0..11:
  [ 0] 0049ADC0  C     ; push esi | mov esi, ecx
  [ 1] 00499650  C     ; push ecx | mov eax, dword ptr [esp + 0x24]
  [ 2] 00499820  C     ; mov edx, dword ptr [esp + 0x28] | mov eax, dword ptr [ecx]
  [ 3] 007FF008  D  COL:G::?$RLEBlitTransZRemapXlatAlphaZReadWrite(off=0)
  [ 4] 0049AD80  C     ; push esi | mov esi, ecx
  [ 5] 00499430  C     ; sub esp, 8 | push ebx
  [ 6] 00499610  C     ; mov edx, dword ptr [esp + 0x28] | mov eax, dword ptr [ecx]
  [ 7] 007FD438  D  COL:G::?$RLEBlitTransXlatAlphaZReadWrite(off=0)
  [ 8] 0049AD40  C     ; push esi | mov esi, ecx
  [ 9] 004990E0  C     ; push ecx | push ebx
  [10] 00499280  C     ; push ecx | push ebx
  [11] 007FEAB8  D  COL:G::?$RLEBlitTransLucent25AlphaZReadWarp(off=0)
- 连续代码游程 run=3
- **判定: REAL_VTABLE** — 前 3 槽连续代码, slot3=&COL(G::?$RLEBlitTransZRemapXlatAlphaZReadWrite): 紧跟下一个虚表的 COL 头 => 本虚表共 3 槽

### [40] vt=007EA344  类=PAVInfantryTypeClass::?$VectorClass (.?AV?$VectorClass@PAVInfantryTypeClass@@@@)  段=.rdata
- [vt-4]=007EA340 -> COL=00801E90: sig=0 offset=0 cdOffset=0 td=00823AB0(VA) chd=00801E80(VA) td_struct_ok=True
- xr: text=7 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x004F09D0 C
- 槽 0..11:
  [ 0] 004F09D0  C     ; push esi | mov esi, ecx
  [ 1] 004EE1E0  C     ; push ebx | push esi
  [ 2] 004EE220  C     ; push ebx | push ebp
  [ 3] 004EE2D0  C     ; push ebx | push esi
  [ 4] 004EE300  C     ; mov al, byte ptr [ecx + 0xc] | push esi
  [ 5] 004EE340  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
  [ 6] 004E8F50  C     ; mov eax, dword ptr [ecx + 4] | mov ecx, dword ptr [esp + 4]
  [ 7] 00801EF8  D  COL:PAVBulletTypeClass::?$DynamicVectorClass(off=0)
  [ 8] 004F0AC0  C     ; push esi | mov esi, ecx
  [ 9] 004EE440  C     ; push ebx | push esi
  [10] 004EE5C0  C     ; push ebx | push ebp
  [11] 004E8F60  C     ; push ebx | push esi
- 连续代码游程 run=7
- **判定: REAL_VTABLE** — 前 7 槽连续代码, slot7=&COL(PAVBulletTypeClass::?$DynamicVectorClass): 紧跟下一个虚表的 COL 头 => 本虚表共 7 槽

## 4. 列表A: 槽0为代码但槽1/2既非代码也非0 (疑似假阳性)
- 总数: **208**
- 全部地址: 007E195C(MouseClass), 007E1AF4(CCINIClass), 007E1AFC(INIClass::PAUINISection::?$List), 007E1B04(GenericList), 007E1B0C(GenericNode), 007E1F24(AbstractClass), 007E1F2C(AbstractClass), 007E1FB4(INoticeSource), 007E1FBC(INoticeSink), 007E1FD4(AbstractTypeClass), 007E1FDC(AbstractTypeClass), 007E2278(AircraftClass), 007E2280(AircraftClass), 007E283C(AircraftTypeClass), 007E2844(AircraftTypeClass), 007E297C(AirstrikeClass), 007E2984(AirstrikeClass), 007E2A24(AITriggerTypeClass), 007E2A2C(AITriggerTypeClass), 007E3278(AlphaShapeClass), 007E3280(AlphaShapeClass), 007E3328(AnimClass), 007E3330(AnimClass), 007E35DC(AnimTypeClass), 007E35E4(AnimTypeClass), 007E3A78(BitFont), 007E3AA4(BuildingLightClass), 007E3AAC(BuildingLightClass), 007E3CE4(BombClass), 007E3CEC(BombClass), 007E3DC4(NeuronClass), 007E3DCC(NeuronClass), 007E3E74(BrainClass), 007E3E90(BuildingClass), 007E3E98(BuildingClass), 007E4544(BuildingTypeClass), 007E454C(BuildingTypeClass), 007E46B8(BulletClass), 007E46C0(BulletClass), 007E491C(BulletTypeClass)
### [A1] vt=007E195C  类=MouseClass (.?AVMouseClass@@)  段=.rdata
- [vt-4]=007E1958 -> COL=007FA9B8: sig=0 offset=21784 cdOffset=0 td=00816C90(VA) chd=007FAB28(VA) td_struct_ok=True
- xr: text=4 rdata=0 data=0 | [pos-4]=X:unmapped | [pos+4]=0x006D1770 C
- 槽 0..11:
  [ 0] 006D1770  C     ; mov eax, dword ptr [esp + 4] | cmp eax, 0x11c7
  [ 1] 007FAB38  D  COL:MouseClass(off=0)
  [ 2] 004F4240  C     ; mov edx, dword ptr [esp + 0xc] | push esi
  [ 3] 0040D230  C     ; mov eax, 1 | ret 4
  [ 4] 0040D240  C     ; mov eax, 1 | ret 4
  [ 5] 005656D0  C     ; push ecx | mov ax, word ptr [esp + 0xe]
  [ 6] 0040D290  C     ; push ebx | mov ebx, ecx
  [ 7] 005BDF30  C     ; call 0x6d0260 | mov edx, 0xabf2dc
  [ 8] 004F42B0  C     ; push esi | mov esi, ecx
  [ 9] 005BDF50  C     ; push esi | mov esi, ecx
  [10] 0040D270  C     ; jmp 0x6d03a0 | nop 
  [11] 004F4320  C     ; sub esp, 8 | push ebp
- 连续代码游程 run=1
- **判定: UNCERTAIN** — 仅 1 个代码槽, slot1=&COL(MouseClass): 短代码段后内嵌 COL 指针, 疑似 pos 扫描假阳性(或 1 槽小虚表)

### [A2] vt=007E1AF4  类=CCINIClass (.?AVCCINIClass@@)  段=.rdata
- [vt-4]=007E1AF0 -> COL=007FAC88: sig=0 offset=0 cdOffset=0 td=008174C8(VA) chd=007FAC78(VA) td_struct_ok=True
- xr: text=39 rdata=0 data=0 | [pos-4]=X:unmapped | [pos+4]=0x0040E4A0 C
- 槽 0..11:
  [ 0] 0040E4A0  C     ; push esi | mov esi, ecx
  [ 1] 007FAC20  D  COL:INIClass::PAUINISection::?$List(off=0)
  [ 2] 0040E4C0  C     ; push esi | push edi
  [ 3] 007FAD18  D  COL:GenericList(off=0)
  [ 4] 0040E3E0  C     ; push esi | push edi
  [ 5] 007FACD0  D  COL:GenericNode(off=0)
  [ 6] 0040E390  C     ; push esi | mov esi, ecx
  [ 7] 00000000  0  
  [ 8] 404E0000  X  unmapped
  [ 9] A2529D39  X  unmapped
  [10] 3F91DF46  X  unmapped
  [11] 007FAD80  D  COL:PAVScriptClass::?$DynamicVectorClass(off=0)
- 连续代码游程 run=1
- **判定: UNCERTAIN** — 仅 1 个代码槽, slot1=&COL(INIClass::PAUINISection::?$List): 短代码段后内嵌 COL 指针, 疑似 pos 扫描假阳性(或 1 槽小虚表)

### [A3] vt=007E1AFC  类=INIClass::PAUINISection::?$List (.?AV?$List@PAUINISection@INIClass@@@@)  段=.rdata
- [vt-4]=007E1AF8 -> COL=007FAC20: sig=0 offset=0 cdOffset=0 td=00817480(VA) chd=007FAC10(VA) td_struct_ok=True
- xr: text=54 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x0040E4C0 C
- 槽 0..11:
  [ 0] 0040E4C0  C     ; push esi | push edi
  [ 1] 007FAD18  D  COL:GenericList(off=0)
  [ 2] 0040E3E0  C     ; push esi | push edi
  [ 3] 007FACD0  D  COL:GenericNode(off=0)
  [ 4] 0040E390  C     ; push esi | mov esi, ecx
  [ 5] 00000000  0  
  [ 6] 404E0000  X  unmapped
  [ 7] A2529D39  X  unmapped
  [ 8] 3F91DF46  X  unmapped
  [ 9] 007FAD80  D  COL:PAVScriptClass::?$DynamicVectorClass(off=0)
  [10] 0040EB00  C     ; push esi | mov esi, ecx
  [11] 0040E850  C     ; push ebx | push esi
- 连续代码游程 run=1
- **判定: UNCERTAIN** — 仅 1 个代码槽, slot1=&COL(GenericList): 短代码段后内嵌 COL 指针, 疑似 pos 扫描假阳性(或 1 槽小虚表)

### [A4] vt=007E1B04  类=GenericList (.?AVGenericList@@)  段=.rdata
- [vt-4]=007E1B00 -> COL=007FAD18: sig=0 offset=0 cdOffset=0 td=00817508(VA) chd=007FAD08(VA) td_struct_ok=True
- xr: text=45 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x0040E3E0 C
- 槽 0..11:
  [ 0] 0040E3E0  C     ; push esi | push edi
  [ 1] 007FACD0  D  COL:GenericNode(off=0)
  [ 2] 0040E390  C     ; push esi | mov esi, ecx
  [ 3] 00000000  0  
  [ 4] 404E0000  X  unmapped
  [ 5] A2529D39  X  unmapped
  [ 6] 3F91DF46  X  unmapped
  [ 7] 007FAD80  D  COL:PAVScriptClass::?$DynamicVectorClass(off=0)
  [ 8] 0040EB00  C     ; push esi | mov esi, ecx
  [ 9] 0040E850  C     ; push ebx | push esi
  [10] 0040E9D0  C     ; push ebx | push ebp
  [11] 0040E7F0  C     ; push ebx | push esi
- 连续代码游程 run=1
- **判定: UNCERTAIN** — 仅 1 个代码槽, slot1=&COL(GenericNode): 短代码段后内嵌 COL 指针, 疑似 pos 扫描假阳性(或 1 槽小虚表)

### [A5] vt=007E1B0C  类=GenericNode (.?AVGenericNode@@)  段=.rdata
- [vt-4]=007E1B08 -> COL=007FACD0: sig=0 offset=0 cdOffset=0 td=008174E8(VA) chd=007FACC0(VA) td_struct_ok=True
- xr: text=54 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x0040E390 C
- 槽 0..11:
  [ 0] 0040E390  C     ; push esi | mov esi, ecx
  [ 1] 00000000  0  
  [ 2] 404E0000  X  unmapped
  [ 3] A2529D39  X  unmapped
  [ 4] 3F91DF46  X  unmapped
  [ 5] 007FAD80  D  COL:PAVScriptClass::?$DynamicVectorClass(off=0)
  [ 6] 0040EB00  C     ; push esi | mov esi, ecx
  [ 7] 0040E850  C     ; push ebx | push esi
  [ 8] 0040E9D0  C     ; push ebx | push ebp
  [ 9] 0040E7F0  C     ; push ebx | push esi
  [10] 0040EA80  C     ; mov edx, dword ptr [ecx + 0x10] | xor eax, eax
  [11] 0040E820  C     ; mov al, byte ptr [ecx + 0xc] | test al, al
- 连续代码游程 run=2
- **判定: UNCERTAIN** — 前 2 槽连续代码, slot2=0x404E0000 为 X(unmapped); xr_text=54

### [A6] vt=007E1F24  类=AbstractClass (.?AVAbstractClass@@)  段=.rdata
- [vt-4]=007E1F20 -> COL=007FAFD8: sig=0 offset=12 cdOffset=0 td=008177C8(VA) chd=007FB108(VA) td_struct_ok=True
- xr: text=5 rdata=0 data=0 | [pos-4]=X:unmapped | [pos+4]=0x00410590 C
- 槽 0..11:
  [ 0] 00410590  C     ; ret 4 | nop 
  [ 1] 007FAFF0  D  COL:AbstractClass(off=8)
  [ 2] 00410580  C     ; xor al, al | ret 8
  [ 3] 007FB008  D  COL:AbstractClass(off=4)
  [ 4] 004105E0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410260
  [ 5] 004105F0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410300
  [ 6] 00410600  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410310
  [ 7] 00410210  C     ; mov eax, dword ptr [esp + 4] | mov edx, dword ptr [eax - 4]
  [ 8] 00410220  C     ; mov eax, dword ptr [esp + 4] | mov eax, dword ptr [eax + 0xc]
  [ 9] 00410230  C     ; mov ecx, dword ptr [0xa8b230] | test ecx, ecx
  [10] 007FB118  D  COL:AbstractClass(off=0)
  [11] 00410260  C     ; mov eax, dword ptr [esp + 0xc] | push ebx
- 连续代码游程 run=1
- **判定: UNCERTAIN** — 仅 1 个代码槽, slot1=&COL(AbstractClass): 短代码段后内嵌 COL 指针, 疑似 pos 扫描假阳性(或 1 槽小虚表)

### [A7] vt=007E1F2C  类=AbstractClass (.?AVAbstractClass@@)  段=.rdata
- [vt-4]=007E1F28 -> COL=007FAFF0: sig=0 offset=8 cdOffset=0 td=008177C8(VA) chd=007FB108(VA) td_struct_ok=True
- xr: text=5 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x00410580 C
- 槽 0..11:
  [ 0] 00410580  C     ; xor al, al | ret 8
  [ 1] 007FB008  D  COL:AbstractClass(off=4)
  [ 2] 004105E0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410260
  [ 3] 004105F0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410300
  [ 4] 00410600  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410310
  [ 5] 00410210  C     ; mov eax, dword ptr [esp + 4] | mov edx, dword ptr [eax - 4]
  [ 6] 00410220  C     ; mov eax, dword ptr [esp + 4] | mov eax, dword ptr [eax + 0xc]
  [ 7] 00410230  C     ; mov ecx, dword ptr [0xa8b230] | test ecx, ecx
  [ 8] 007FB118  D  COL:AbstractClass(off=0)
  [ 9] 00410260  C     ; mov eax, dword ptr [esp + 0xc] | push ebx
  [10] 00410300  C     ; mov eax, 1 | ret 4
  [11] 00410310  C     ; mov eax, 1 | ret 4
- 连续代码游程 run=1
- **判定: UNCERTAIN** — 仅 1 个代码槽, slot1=&COL(AbstractClass): 短代码段后内嵌 COL 指针, 疑似 pos 扫描假阳性(或 1 槽小虚表)

### [A8] vt=007E1FB4  类=INoticeSource (.?AVINoticeSource@@)  段=.rdata
- [vt-4]=007E1FB0 -> COL=007FB160: sig=0 offset=0 cdOffset=0 td=008177E8(VA) chd=007FB150(VA) td_struct_ok=True
- xr: text=3 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x004C9150 C
- 槽 0..11:
  [ 0] 004C9150  C     ; xor eax, eax | ret 
  [ 1] 007FAFC0  D  COL:INoticeSink(off=0)
  [ 2] 004C9150  C     ; xor eax, eax | ret 
  [ 3] 00000000  0  
  [ 4] 404E0000  X  unmapped
  [ 5] A2529D39  X  unmapped
  [ 6] 3F91DF46  X  unmapped
  [ 7] 007FB178  D  COL:AbstractTypeClass(off=12)
  [ 8] 00410590  C     ; ret 4 | nop 
  [ 9] 007FB190  D  COL:AbstractTypeClass(off=8)
  [10] 00410580  C     ; xor al, al | ret 8
  [11] 007FB1A8  D  COL:AbstractTypeClass(off=4)
- 连续代码游程 run=1
- **判定: UNCERTAIN** — 仅 1 个代码槽, slot1=&COL(INoticeSink): 短代码段后内嵌 COL 指针, 疑似 pos 扫描假阳性(或 1 槽小虚表)

### [A9] vt=007E1FBC  类=INoticeSink (.?AVINoticeSink@@)  段=.rdata
- [vt-4]=007E1FB8 -> COL=007FAFC0: sig=0 offset=0 cdOffset=0 td=00816B50(VA) chd=007FAFB0(VA) td_struct_ok=True
- xr: text=5 rdata=0 data=0 | [pos-4]=C | [pos+4]=0x004C9150 C
- 槽 0..11:
  [ 0] 004C9150  C     ; xor eax, eax | ret 
  [ 1] 00000000  0  
  [ 2] 404E0000  X  unmapped
  [ 3] A2529D39  X  unmapped
  [ 4] 3F91DF46  X  unmapped
  [ 5] 007FB178  D  COL:AbstractTypeClass(off=12)
  [ 6] 00410590  C     ; ret 4 | nop 
  [ 7] 007FB190  D  COL:AbstractTypeClass(off=8)
  [ 8] 00410580  C     ; xor al, al | ret 8
  [ 9] 007FB1A8  D  COL:AbstractTypeClass(off=4)
  [10] 004105E0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410260
  [11] 004105F0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410300
- 连续代码游程 run=2
- **判定: UNCERTAIN** — 前 2 槽连续代码, slot2=0x404E0000 为 X(unmapped); xr_text=5

### [A10] vt=007E1FD4  类=AbstractTypeClass (.?AVAbstractTypeClass@@)  段=.rdata
- [vt-4]=007E1FD0 -> COL=007FB178: sig=0 offset=12 cdOffset=0 td=00817808(VA) chd=007FB200(VA) td_struct_ok=True
- xr: text=4 rdata=0 data=0 | [pos-4]=X:unmapped | [pos+4]=0x00410590 C
- 槽 0..11:
  [ 0] 00410590  C     ; ret 4 | nop 
  [ 1] 007FB190  D  COL:AbstractTypeClass(off=8)
  [ 2] 00410580  C     ; xor al, al | ret 8
  [ 3] 007FB1A8  D  COL:AbstractTypeClass(off=4)
  [ 4] 004105E0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410260
  [ 5] 004105F0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410300
  [ 6] 00410600  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410310
  [ 7] 00410210  C     ; mov eax, dword ptr [esp + 4] | mov edx, dword ptr [eax - 4]
  [ 8] 00410220  C     ; mov eax, dword ptr [esp + 4] | mov eax, dword ptr [eax + 0xc]
  [ 9] 00410230  C     ; mov ecx, dword ptr [0xa8b230] | test ecx, ecx
  [10] 007FB210  D  COL:AbstractTypeClass(off=0)
  [11] 00410260  C     ; mov eax, dword ptr [esp + 0xc] | push ebx
- 连续代码游程 run=1
- **判定: UNCERTAIN** — 仅 1 个代码槽, slot1=&COL(AbstractTypeClass): 短代码段后内嵌 COL 指针, 疑似 pos 扫描假阳性(或 1 槽小虚表)

## 5. 疑点深查: 0x007E1F24 / 0x007E1F2C (任务称均为 .?AVAbstractClass@@)
- 线索核对: dword[0x7E1F28] = 007FAFF0 (任务线索称 0x007FAFF0) ; dword[0x7E1F30] = 007FB008 (任务线索称 0x007FB008)
- dword[0x7E1F20] = 007FAFD8 -> COL: .?AVAbstractClass@@ off=12 sig=0 td=008177C8
- dword[0x7E1F28] = 007FAFF0 -> COL: .?AVAbstractClass@@ off=8 sig=0 td=008177C8
- 本独立扫描候选集: 0x007E1F24 在 ; 0x007E1F2C 在

### 007E1F24 槽序列
- 候选记录: 类=AbstractClass (.?AVAbstractClass@@) pos=007E1F20 col=007FAFD8 offset=12 sig=0 | xr: text=5 rdata=0 data=0
- 判定: UNCERTAIN — 仅 1 个代码槽, slot1=&COL(AbstractClass): 短代码段后内嵌 COL 指针, 疑似 pos 扫描假阳性(或 1 槽小虚表)
  [ 0] 00410590  C     ; ret 4 | nop  | nop 
  [ 1] 007FAFF0  D  COL:AbstractClass(off=8)
  [ 2] 00410580  C     ; xor al, al | ret 8 | nop 
  [ 3] 007FB008  D  COL:AbstractClass(off=4)
  [ 4] 004105E0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410260 | int3 
  [ 5] 004105F0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410300 | int3 
  [ 6] 00410600  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410310 | int3 
  [ 7] 00410210  C     ; mov eax, dword ptr [esp + 4] | mov edx, dword ptr [eax - 4] | lea ecx, [eax - 4]
  [ 8] 00410220  C     ; mov eax, dword ptr [esp + 4] | mov eax, dword ptr [eax + 0xc] | ret 4
  [ 9] 00410230  C     ; mov ecx, dword ptr [0xa8b230] | test ecx, ecx | jne 0x410246
  [10] 007FB118  D  COL:AbstractClass(off=0)
  [11] 00410260  C     ; mov eax, dword ptr [esp + 0xc] | push ebx | test eax, eax
- slot0=00410590 反汇编: ret 4 | nop  | nop  | nop  | nop 

### 007E1F2C 槽序列
- 候选记录: 类=AbstractClass (.?AVAbstractClass@@) pos=007E1F28 col=007FAFF0 offset=8 sig=0 | xr: text=5 rdata=0 data=0
- 判定: UNCERTAIN — 仅 1 个代码槽, slot1=&COL(AbstractClass): 短代码段后内嵌 COL 指针, 疑似 pos 扫描假阳性(或 1 槽小虚表)
  [ 0] 00410580  C     ; xor al, al | ret 8 | nop 
  [ 1] 007FB008  D  COL:AbstractClass(off=4)
  [ 2] 004105E0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410260 | int3 
  [ 3] 004105F0  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410300 | int3 
  [ 4] 00410600  C     ; sub dword ptr [esp + 4], 4 | jmp 0x410310 | int3 
  [ 5] 00410210  C     ; mov eax, dword ptr [esp + 4] | mov edx, dword ptr [eax - 4] | lea ecx, [eax - 4]
  [ 6] 00410220  C     ; mov eax, dword ptr [esp + 4] | mov eax, dword ptr [eax + 0xc] | ret 4
  [ 7] 00410230  C     ; mov ecx, dword ptr [0xa8b230] | test ecx, ecx | jne 0x410246
  [ 8] 007FB118  D  COL:AbstractClass(off=0)
  [ 9] 00410260  C     ; mov eax, dword ptr [esp + 0xc] | push ebx | test eax, eax
  [10] 00410300  C     ; mov eax, 1 | ret 4 | nop 
  [11] 00410310  C     ; mov eax, 1 | ret 4 | nop 
- slot0=00410580 反汇编: xor al, al | ret 8 | nop  | nop  | nop 

### 区域转储 .rdata 0x7E1EC0 .. 0x7E1FC0
| 地址 | 值 | 类别 | 注 | 标记 |
|---|---|---|---|---|
| 007E1EC0 | 00000000 | 0 |  |  |
| 007E1EC4 | 404E0000 | X | unmapped |  |
| 007E1EC8 | A2529D39 | X | unmapped |  |
| 007E1ECC | 3F91DF46 | X | unmapped |  |
| 007E1ED0 | 007FAF48 | D | COL:PAVWeaponTypeClass::?$DynamicVectorClass(off=0) | ==候选vt的[vt-4] |
| 007E1ED4 | 0040FEC0 | C |  | ==候选vt |
| 007E1ED8 | 0040FC10 | C |  |  |
| 007E1EDC | 0040FD90 | C |  |  |
| 007E1EE0 | 0040FBB0 | C |  |  |
| 007E1EE4 | 0040FE40 | C |  |  |
| 007E1EE8 | 0040FBE0 | C |  |  |
| 007E1EEC | 0040FC00 | C |  |  |
| 007E1EF0 | 007FAF78 | D | COL:PAVWeaponTypeClass::?$VectorClass(off=0) | ==候选vt的[vt-4] |
| 007E1EF4 | 0040FE70 | C |  | ==候选vt |
| 007E1EF8 | 0040FC10 | C |  |  |
| 007E1EFC | 0040FC50 | C |  |  |
| 007E1F00 | 0040FD00 | C |  |  |
| 007E1F04 | 0040FD30 | C |  |  |
| 007E1F08 | 0040FD70 | C |  |  |
| 007E1F0C | 0040FC00 | C |  |  |
| 007E1F10 | 00000000 | 0 |  |  |
| 007E1F14 | 404E0000 | X | unmapped |  |
| 007E1F18 | A2529D39 | X | unmapped |  |
| 007E1F1C | 3F91DF46 | X | unmapped |  |
| 007E1F20 | 007FAFD8 | D | COL:AbstractClass(off=12) | ==候选vt的[vt-4] |
| 007E1F24 | 00410590 | C |  | ==候选vt |
| 007E1F28 | 007FAFF0 | D | COL:AbstractClass(off=8) | ==候选vt的[vt-4] |
| 007E1F2C | 00410580 | C |  | ==候选vt |
| 007E1F30 | 007FB008 | D | COL:AbstractClass(off=4) | ==候选vt的[vt-4] |
| 007E1F34 | 004105E0 | C |  | ==候选vt |
| 007E1F38 | 004105F0 | C |  |  |
| 007E1F3C | 00410600 | C |  |  |
| 007E1F40 | 00410210 | C |  |  |
| 007E1F44 | 00410220 | C |  |  |
| 007E1F48 | 00410230 | C |  |  |
| 007E1F4C | 007FB118 | D | COL:AbstractClass(off=0) | ==候选vt的[vt-4] |
| 007E1F50 | 00410260 | C |  | ==候选vt |
| 007E1F54 | 00410300 | C |  |  |
| 007E1F58 | 00410310 | C |  |  |
| 007E1F5C | 004C9150 | C |  |  |
| 007E1F60 | 00410450 | C |  |  |
| 007E1F64 | 004C9150 | C |  |  |
| 007E1F68 | 004C9150 | C |  |  |
| 007E1F6C | 004103E0 | C |  |  |
| 007E1F70 | 004105A0 | C |  |  |
| 007E1F74 | 00410470 | C |  |  |
| 007E1F78 | 00410480 | C |  |  |
| 007E1F7C | 004C9150 | C |  |  |
| 007E1F80 | 004C9150 | C |  |  |
| 007E1F84 | 00410410 | C |  |  |
| 007E1F88 | 00410490 | C |  |  |
| 007E1F8C | 004104A0 | C |  |  |
| 007E1F90 | 004104B0 | C |  |  |
| 007E1F94 | 00410440 | C |  |  |
| 007E1F98 | 004104C0 | C |  |  |
| 007E1F9C | 004104F0 | C |  |  |
| 007E1FA0 | 00410520 | C |  |  |
| 007E1FA4 | 00410530 | C |  |  |
| 007E1FA8 | 00410540 | C |  |  |
| 007E1FAC | 00410570 | C |  |  |
| 007E1FB0 | 007FB160 | D | COL:INoticeSource(off=0) | ==候选vt的[vt-4] |
| 007E1FB4 | 004C9150 | C |  | ==候选vt |
| 007E1FB8 | 007FAFC0 | D | COL:INoticeSink(off=0) | ==候选vt的[vt-4] |
| 007E1FBC | 004C9150 | C |  | ==候选vt |

### 区域转储 .rdata 0x7FAFC0 .. 0x7FB040 (线索中的两个数据指针)
| 地址 | 值 | 类别 | 注 | 标记 |
|---|---|---|---|---|
| 007FAFC0 | 00000000 | 0 |  | ==COL对象(sig=0,off=0) |
| 007FAFC4 | 00000000 | 0 |  |  |
| 007FAFC8 | 00000000 | 0 |  |  |
| 007FAFCC | 00816B50 | D | TD:INoticeSink |  |
| 007FAFD0 | 007FAFB0 | D |  |  |
| 007FAFD4 | 00000000 | 0 |  |  |
| 007FAFD8 | 00000000 | 0 |  | ==COL对象(sig=0,off=12) |
| 007FAFDC | 0000000C | X | unmapped |  |
| 007FAFE0 | 00000000 | 0 |  |  |
| 007FAFE4 | 008177C8 | D | TD:AbstractClass |  |
| 007FAFE8 | 007FB108 | D |  |  |
| 007FAFEC | 00000000 | 0 |  |  |
| 007FAFF0 | 00000000 | 0 |  | ==COL对象(sig=0,off=8) |
| 007FAFF4 | 00000008 | X | unmapped |  |
| 007FAFF8 | 00000000 | 0 |  |  |
| 007FAFFC | 008177C8 | D | TD:AbstractClass |  |
| 007FB000 | 007FB108 | D |  |  |
| 007FB004 | 00000000 | 0 |  |  |
| 007FB008 | 00000000 | 0 |  | ==COL对象(sig=0,off=4) |
| 007FB00C | 00000004 | X | unmapped |  |
| 007FB010 | 00000000 | 0 |  |  |
| 007FB014 | 008177C8 | D | TD:AbstractClass |  |
| 007FB018 | 007FB108 | D |  |  |
| 007FB01C | 00000000 | 0 |  |  |
| 007FB020 | 008177E8 | D | TD:INoticeSource |  |
| 007FB024 | 00000000 | 0 |  |  |
| 007FB028 | 0000000C | X | unmapped |  |
| 007FB02C | FFFFFFFF | X | unmapped |  |
| 007FB030 | 00000000 | 0 |  |  |
| 007FB034 | 00000000 | 0 |  |  |
| 007FB038 | 00816B50 | D | TD:INoticeSink |  |
| 007FB03C | 00000000 | 0 |  |  |

### 结构识别
--- 结构识别 @ 007FAFF0 ---
  +00: 00000000
  +04: 00000008
  +08: 00000000
  +0C: 008177C8
  +10: 007FB108
  +14: 00000000
  +18: 00000000
  +1C: 00000004
  +20: 00000000
  +24: 008177C8
  => 完整对象定位器 COL: sig=0 offset=8 cdOffset=0 pTD=008177C8(VA) pCHD=007FB108(VA) 类名=.?AVAbstractClass@@ td_struct_ok=True
     CHD@007FB108: sig=0 attr=1 num=8 pBCA=007FB0E0
       BCA[0] = 007FB0C8 -> (不可解析为TD)
       BCA[1] = 007FB0B0 -> (不可解析为TD)
       BCA[2] = 007FB098 -> (不可解析为TD)
       BCA[3] = 007FB080 -> (不可解析为TD)
       BCA[4] = 007FB068 -> 
       BCA[5] = 007FB050 -> 
       BCA[6] = 007FB038 -> 
       BCA[7] = 007FB020 -> 

--- 结构识别 @ 007FB008 ---
  +00: 00000000
  +04: 00000004
  +08: 00000000
  +0C: 008177C8
  +10: 007FB108
  +14: 00000000
  +18: 008177E8
  +1C: 00000000
  +20: 0000000C
  +24: FFFFFFFF
  => 完整对象定位器 COL: sig=0 offset=4 cdOffset=0 pTD=008177C8(VA) pCHD=007FB108(VA) 类名=.?AVAbstractClass@@ td_struct_ok=True
     CHD@007FB108: sig=0 attr=1 num=8 pBCA=007FB0E0
       BCA[0] = 007FB0C8 -> (不可解析为TD)
       BCA[1] = 007FB0B0 -> (不可解析为TD)
       BCA[2] = 007FB098 -> (不可解析为TD)
       BCA[3] = 007FB080 -> (不可解析为TD)
       BCA[4] = 007FB068 -> 
       BCA[5] = 007FB050 -> 
       BCA[6] = 007FB038 -> 
       BCA[7] = 007FB020 -> 

--- 结构识别 @ 007FB004 ---
  +00: 00000000
  +04: 00000000
  +08: 00000004
  +0C: 00000000
  +10: 008177C8
  +14: 007FB108
  +18: 00000000
  +1C: 008177E8
  +20: 00000000
  +24: 0000000C
  => 无标准 RTTI 结构解释

### dword[0x7E1F20] 指向对象识别
--- 结构识别 @ 007FAFD8 ---
  +00: 00000000
  +04: 0000000C
  +08: 00000000
  +0C: 008177C8
  +10: 007FB108
  +14: 00000000
  +18: 00000000
  +1C: 00000008
  +20: 00000000
  +24: 008177C8
  => 完整对象定位器 COL: sig=0 offset=12 cdOffset=0 pTD=008177C8(VA) pCHD=007FB108(VA) 类名=.?AVAbstractClass@@ td_struct_ok=True
     CHD@007FB108: sig=0 attr=1 num=8 pBCA=007FB0E0
       BCA[0] = 007FB0C8 -> (不可解析为TD)
       BCA[1] = 007FB0B0 -> (不可解析为TD)
       BCA[2] = 007FB098 -> (不可解析为TD)
       BCA[3] = 007FB080 -> (不可解析为TD)
       BCA[4] = 007FB068 -> 
       BCA[5] = 007FB050 -> 
       BCA[6] = 007FB038 -> 
       BCA[7] = 007FB020 -> 

### stride-8 成对结构探测 (锚 0x7E1F20)
- 成对区间 007E1F20 .. 007E1F38, 共 3 对 {COL指针, 代码}
  - [007E1F20]=&COL(.?AVAbstractClass@@, off=12, td=008177C8) ; [007E1F24]=00410590 (C ) ret 4 | nop 
  - [007E1F28]=&COL(.?AVAbstractClass@@, off=8, td=008177C8) ; [007E1F2C]=00410580 (C ) xor al, al | ret 8
  - [007E1F30]=&COL(.?AVAbstractClass@@, off=4, td=008177C8) ; [007E1F34]=004105E0 (C ) sub dword ptr [esp + 4], 4 | jmp 0x410260

### 引用扫描 (谁引用了这些对象)
- 007FAFD8 被 .rdata/.data 引用 1 处:
  - pos=007E1F20  | 后值=00410590 (C )
- 007FAFF0 被 .rdata/.data 引用 1 处:
  - pos=007E1F28  | 后值=00410580 (C )
- 008177C8 被 .rdata/.data 引用 5 处:
  - pos=007FAFE4 位于 COL@007FAFD8+0x0C | 后值=007FB108 (D )
  - pos=007FAFFC 位于 COL@007FAFF0+0x0C | 后值=007FB108 (D )
  - pos=007FB014 位于 COL@007FB008+0x0C | 后值=007FB108 (D )
  - pos=007FB0C8  | 后值=00000007 (X unmapped)
  - pos=007FB124 位于 COL@007FB118+0x0C | 后值=007FB108 (D )

## 6. 与任务"背景"描述的一致性核对
- [背景] "[vt-4] 存指向 COL 的指针": 成立 — 全部候选均由该关系产生, 扫描按绝对 VA 读 [vt-4]。
- [背景] COL 布局 +0x00 sig/+0x04 offset/+0x08 cdOffset/+0x0C pTD/+0x10 pCHD: pTD 字段按绝对 VA 解释命中 1219 个候选, 按 RVA+ImageBase 解释命中 0 个 => 本镜像实际采用: 绝对 VA
- [背景] COL offset=0 表示主虚表: offset 分布(前5) [(0, 955), (4, 95), (12, 78), (8, 78), (24, 6)], offset!=0 候选 264 个
- [背景] TD +0x08 起为内联字符数组: 成立 — 全部候选都是直接在 td+8 读出 ".?A?" 名字 (若 +8 是指针, 该读法不可能命中)。TD 结构佐证 [+0]=vftable指针/[+4]==0 通过率: 1219/1219
- [背景] 纯虚槽允许 0 或 _purecall: 前 12 槽出现 0 的候选 163 个; IAT _purecall 槽=无; 识别出 FF25 thunk 0 个; 最高频槽值见第 2 节
- [背景] 真虚表槽 0..k 连续指向 .text: slot0 即非代码非 0 的候选 5 个 (NOT_VTABLE 口径)
- [背景] 段范围/.data raw size: 实测见第 0 节。

## 7. NOTES (与任务口径/背景不一致或需注意)
1. 导入表无 _purecall: 纯虚槽识别退化为 "同址高频" 启发式 (P 标签可能缺失)。
2. 34 个类有 TD 但按本口径无候选虚表 (可能: 无虚表/虚表不在扫描段/COL 未被 .rdata/.data 引用)
3. stride-8 相邻候选 186 个 — 存在系统性的 {COL指针, 代码} 成对布局 (证据见第 5 节)
4. 疑点 0x7E1F24/0x7E1F2C: dword[7E1F20]=007FAFD8->COL(.?AVAbstractClass@@) ; dword[7E1F28]=007FAFF0->COL(.?AVAbstractClass@@) ; 详见第 5 节
