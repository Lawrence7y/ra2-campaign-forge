# R127 跨家族审计 hy4flash 独立复算报告

目标文件: /home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe
sha256: 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
文件大小: 4825360 字节, PE32 i386, ImageBase 0x400000

## 1. OleSaveToStream / OleLoadFromStream 导入表 IAT
OleLoadFromStream: IAT=0x7e15f8 (0x7e15f8) DLL=ole32.dll
OleSaveToStream: IAT=0x7e15f4 (0x7e15f4) DLL=ole32.dll
结论: IAT槽与DLL归属与主张一致

## 2. 四组 IID 字节与 GUID 文本
0x7f7c80 (.rdata): 09 01 00 00 00 00 00 00 c0 00 00 00 00 00 00 46  {00000109-0000-0000-C000-000000000046}
0x820270 (.data): 09 01 00 00 00 00 00 00 c0 00 00 00 00 00 00 46  {00000109-0000-0000-C000-000000000046}
0x7f7c70 (.rdata): 0c 01 00 00 00 00 00 00 c0 00 00 00 00 00 00 46  {0000010C-0000-0000-C000-000000000046}
0x818858 (.data): 0c 01 00 00 00 00 00 00 c0 00 00 00 00 00 00 46  {0000010C-0000-0000-C000-000000000046}
0x7f7c80 vs 0x820270: 逐字节相同
0x7f7c70 vs 0x818858: 逐字节相同
跨对 0x7f7c80 vs 0x7f7c70: 不同
跨对 0x820270 vs 0x818858: 不同

## 3. 以 0x820270 为 riid 的 push 站点与正向扫描
push 站点总数 (形态 68 70 02 82 00, 全文件原始匹配): 8
0x4af856 [.text]: 命中call[0x7e15f4]=是 @0x4af8a5, ret=0x无, 扫描指令数=27
0x4b6313 [.text]: 命中call[0x7e15f4]=是 @0x4b6364, ret=0x无, 扫描指令数=29
0x4db76a [.text]: 命中call[0x7e15f4]=是 @0x4db7be, ret=0x无, 扫描指令数=31
0x50469e [.text]: 命中call[0x7e15f4]=是 @0x5046c9, ret=0x无, 扫描指令数=18
0x54b83c [.text]: 命中call[0x7e15f4]=是 @0x54b88b, ret=0x无, 扫描指令数=27
0x69ef66 [.text]: 命中call[0x7e15f4]=是 @0x69efb5, ret=0x无, 扫描指令数=27
0x719d96 [.text]: 命中call[0x7e15f4]=是 @0x719de5, ret=0x无, 扫描指令数=27
0x75c756 [.text]: 命中call[0x7e15f4]=是 @0x75c7a5, ret=0x无, 扫描指令数=27
主会话列出的 8 个站点是否全部存在: 是

## 4. 以 0x818858 / 0x7f7c70 为 riid 的 push 站点与正向扫描
0x818858 push 站点总数 (原始匹配): 16
0x42ca7a [.text]: 命中call[0x7e15f4]=否, ret=0x42cb3f, 指令数=71
0x45aeb5 [.text]: 命中call[0x7e15f4]=否, ret=0x45aed9, 指令数=16
0x4af6a5 [.text]: 命中call[0x7e15f4]=否, ret=0x4af6fa, 指令数=30
0x4b6575 [.text]: 命中call[0x7e15f4]=否, ret=0x4b65ca, 指令数=30
0x4d5892 [.text]: 命中call[0x7e15f4]=否, ret=0x4d5a4a, 指令数=142
0x52119e [.text]: 命中call[0x7e15f4]=否, ret=0x52125f, 指令数=65
0x521e29 [.text]: 命中call[0x7e15f4]=否, ret=0x521ea2, 指令数=43
0x522135 [.text]: 命中call[0x7e15f4]=否, ret=0x5221c1, 指令数=49
0x5233eb [.text]: 命中call[0x7e15f4]=否, ret=0x523437, 指令数=33
0x54dbe5 [.text]: 命中call[0x7e15f4]=否, ret=0x54dc3a, 指令数=30
0x69edb5 [.text]: 命中call[0x7e15f4]=否, ret=0x69ee0a, 指令数=30
0x71a015 [.text]: 命中call[0x7e15f4]=否, ret=0x71a06a, 指令数=30
0x73a456 [.text]: 命中call[0x7e15f4]=否, ret=0x73a547, 指令数=76
0x73e7b7 [.text]: 命中call[0x7e15f4]=否, ret=0x73e8c2, 指令数=83
0x742815 [.text]: 命中call[0x7e15f4]=否, ret=0x742d24, 指令数=422
0x75c9b5 [.text]: 命中call[0x7e15f4]=否, ret=0x75ca0a, 指令数=30
0x818858 命中 call[0x7e15f4] 的站点数: 0
0x7f7c70 push 站点总数 (原始匹配): 0
0x7f7c70 命中 call[0x7e15f4] 的站点数: 0

## 5. vtable 槽位复算
GUID(0x7e36c0) = {96F02EC3-6FE8-11D1-B6FD-00A024DDAFD1}, GUID(0x7e9b20) = {5FF0CA70-8B12-11D1-B708-00A024DDAFD1}
0x7e36d4 slot0 = 0x429360
0x7e36d4 slot3(+0xc) = 0x429420
0x7ea564 slot3(+0xc) = 0x429270
0x7f4108 slot0 = 0x6cf430
槽位核对结果: PASS
函数 0x429360 前512字节出现 0x7f7c90 常量的位置: 0x429392
  上下文 0x429382:
    0x429382: jle 0x429384
    0x429384: mov esi, eax
    0x429386: xor ebx, ebx
    0x429388: repe cmpsd dword ptr [esi], dword ptr es:[edi]
    0x42938a: je 0x4293c7
    0x42938c: mov ecx, 4
    0x429391: mov edi, 0x7f7c90
    0x429396: mov esi, eax
    0x429398: xor ebx, ebx
    0x42939a: repe cmpsd dword ptr [esi], dword ptr es:[edi]
    0x42939c: je 0x4293c7
    0x42939e: mov esi, eax
    0x4293a0: mov ecx, 4
    0x4293a5: mov edi, 0x7ea6e8
    0x4293aa: xor eax, eax
    0x4293ac: repe cmpsd dword ptr [esi], dword ptr es:[edi]
    0x4293ae: jne 0x4293bc
    0x4293b0: pop edi
    0x4293b1: pop esi
    0x4293b2: mov dword ptr [edx], 0x87f7e8
    0x4293b8: pop ebx
    0x4293b9: ret 0xc
    0x4293bc: pop edi
    0x4293bd: pop esi
函数 0x429270 前512字节出现 0x7f7c90 常量的位置: 0x4292c3, 0x429392
  上下文 0x4292b3:
    0x4292b3: sar byte ptr [ebx - 0x7fffbffe], cl
    0x4292b9: repe cmpsd dword ptr [esi], dword ptr es:[edi]
    0x4292bb: je 0x4292cf
    0x4292bd: mov ecx, 4
    0x4292c2: mov edi, 0x7f7c90
    0x4292c7: mov esi, ebp
    0x4292c9: xor edx, edx
    0x4292cb: repe cmpsd dword ptr [esi], dword ptr es:[edi]
    0x4292cd: jne 0x42930a
    0x4292cf: mov ecx, 0x89a29c
    0x4292d4: test ecx, ecx
    0x4292d6: jne 0x4292e4
    0x4292d8: pop edi
    0x4292d9: pop esi
    0x4292da: pop ebp
    0x4292db: mov eax, 0x8007000e
    0x4292e0: pop ebx
    0x4292e1: ret 0x10
    0x4292e4: mov edx, dword ptr [0x89a29c]
    0x4292ea: push eax
    0x4292eb: push ebp
    0x4292ec: push 0x89a29c
    0x4292f1: call dword ptr [edx]
  上下文 0x429382:
    0x429382: jle 0x429384
    0x429384: mov esi, eax
    0x429386: xor ebx, ebx
    0x429388: repe cmpsd dword ptr [esi], dword ptr es:[edi]
    0x42938a: je 0x4293c7
    0x42938c: mov ecx, 4
    0x429391: mov edi, 0x7f7c90
    0x429396: mov esi, eax
    0x429398: xor ebx, ebx
    0x42939a: repe cmpsd dword ptr [esi], dword ptr es:[edi]
    0x42939c: je 0x4293c7
    0x42939e: mov esi, eax
    0x4293a0: mov ecx, 4
    0x4293a5: mov edi, 0x7ea6e8
    0x4293aa: xor eax, eax
    0x4293ac: repe cmpsd dword ptr [esi], dword ptr es:[edi]
    0x4293ae: jne 0x4293bc
    0x4293b0: pop edi
    0x4293b1: pop esi
    0x4293b2: mov dword ptr [edx], 0x87f7e8
    0x4293b8: pop ebx
    0x4293b9: ret 0xc
    0x4293bc: pop edi
    0x4293bd: pop esi

## 6. 0x7f4108 宿主类 RTTI
vtable 0x7f4108 的前一槽 (vtable-4) = 0x80b730
COL 指针 (RTTI+0xc) = 0x80b73c
COL: pTypeInfo=0x842730, CHD=0x80b720, nBaseClasses=3, pBaseClassArray=0x80b710
宿主类名: .?AVSwizzleManagerClass@@
  base[0]: BCD=0x80b6f8, name=.?AVSwizzleManagerClass@@, ncb(BCD+4)=2, mdisp(BCD+8)=0
  base[1]: BCD=0x80b6e0, name=.?AUISwizzle@@, ncb(BCD+4)=1, mdisp(BCD+8)=0
  base[2]: BCD=0x7fa9e8, name=.?AUIUnknown@@, ncb(BCD+4)=0, mdisp(BCD+8)=0

## 7. 全 .rdata 中 u32 == 目标函数地址的位置
rdata sections: [('.rdata', 4067328, 196724, 4067328, 200704)]
0x429360 在 .rdata 的 u32 出现次数: 1
  (RTTI 定位: vtable 起点=0x7e36d4, 槽序号=0)
  0x7e36d4: u32=0x429360, 疑似vtable槽=是, 宿主=.?AVApplicationClass@@
0x429270 在 .rdata 的 u32 出现次数: 1
  (RTTI 定位: vtable 起点=0x7ea564, 槽序号=3)
  0x7ea570: u32=0x429270, 疑似vtable槽=是, 宿主=.?AVTiberianSunClassFactory@@
0x6cf430 在 .rdata 的 u32 出现次数: 1
  (RTTI 定位: vtable 起点=0x7f4108, 槽序号=0)
  0x7f4108: u32=0x6cf430, 疑似vtable槽=是, 宿主=.?AVSwizzleManagerClass@@
## 7b. 目标入口被 bf/68 立即数引用次数（全文件原始字节）
0x429360: 68 imm=0, bf imm=0, 合计=0
0x429270: 68 imm=0, bf imm=0, 合计=0
0x6cf430: 68 imm=0, bf imm=0, 合计=0

## 8. 对抗性检查
(i) 把 0x818858 或 0x7f7c70 的 QI 结果喂给 call[0x7e15f4] 的站点数: 0
(ii) 以 0x7e36c0 / 0x7e9b20 为立即数的引用点（全文件 68/bf/其他）
IID 0x7e36c0 全文件出现次数: 5
  0x4292ac [.text] 前一字节=bf
  0x429380 [.text] 前一字节=bf
  0x42940a [.text] 前一字节=68
  0x42948a [.text] 前一字节=68
  0x4f6937 [.text] 前一字节=68
IID 0x7e9b20 全文件出现次数: 2
  0x429556 [.text] 前一字节=68
  0x6cf44f [.text] 前一字节=bf


## 8b. 立即数引用的上下文证据
IID 0x7e36c0 @ 0x4292ac:
  0x4292a0: adc byte ptr [eax], al
  0x4292a2: mov ebp, dword ptr [esp + 0x1c]
  0x4292a6: mov ecx, 4
  0x4292ab: mov edi, 0x7e36c0
  0x4292b0: mov esi, ebp
  0x4292b2: xor edx, edx
  0x4292b4: mov ebx, 0x80004002
  0x4292b9: repe cmpsd dword ptr [esi], dword ptr es:[edi]
IID 0x7e36c0 @ 0x429380:
  0x429374: or al, 0
  0x429376: mov eax, dword ptr [esp + 0x14]
  0x42937a: mov ecx, 4
  0x42937f: mov edi, 0x7e36c0
  0x429384: mov esi, eax
  0x429386: xor ebx, ebx
  0x429388: repe cmpsd dword ptr [esi], dword ptr es:[edi]
  0x42938a: je 0x4293c7
IID 0x7e36c0 @ 0x42940a:
  0x4293fe: nop 
  0x4293ff: nop 
  0x429400: mov eax, dword ptr [esp + 4]
  0x429404: mov edx, dword ptr [esp + 8]
  0x429408: push edx
  0x429409: push 0x7e36c0
  0x42940e: mov ecx, dword ptr [eax]
  0x429410: push eax
  0x429411: call dword ptr [ecx]
  0x429413: ret 8
  0x429416: nop 
  0x429417: nop 
  0x429418: nop 
  0x429419: nop 
IID 0x7e36c0 @ 0x42948a:
  0x42947e: nop 
  0x42947f: nop 
  0x429480: mov eax, dword ptr [esp + 4]
  0x429484: mov edx, dword ptr [esp + 8]
  0x429488: push edx
  0x429489: push 0x7e36c0
  0x42948e: mov ecx, dword ptr [eax]
  0x429490: push eax
  0x429491: call dword ptr [ecx]
  0x429493: ret 8
  0x429496: nop 
  0x429497: nop 
  0x429498: nop 
  0x429499: nop 
IID 0x7e36c0 @ 0x4f6937:
  0x4f692b: ret 4
  0x4f692e: nop 
  0x4f692f: nop 
  0x4f6930: push ecx
  0x4f6931: lea eax, [esp]
  0x4f6935: push eax
  0x4f6936: push 0x7e36c0
  0x4f693b: push 0x89a29c
  0x4f6940: call 0x429360
IID 0x7e9b20 @ 0x429556:
  0x42954a: nop 
  0x42954b: nop 
  0x42954c: nop 
  0x42954d: nop 
  0x42954e: nop 
  0x42954f: nop 
  0x429550: mov eax, dword ptr [esp + 8]
  0x429554: push eax
  0x429555: push 0x7e9b20
  0x42955a: push 0xb0c110
  0x42955f: call 0x6cf430
IID 0x7e9b20 @ 0x6cf44f:
  0x6cf443: add byte ptr [ebx + 0x53102444], cl
  0x6cf449: mov ecx, 4
  0x6cf44e: mov edi, 0x7e9b20
  0x6cf453: mov esi, eax
  0x6cf455: xor ebx, ebx
  0x6cf457: repe cmpsd dword ptr [esi], dword ptr es:[edi]
  0x6cf459: pop ebx
  0x6cf45a: je 0x6cf478
  0x6cf45c: mov esi, eax

## 9. 逐条判定
主张一（IPersistStream/IPersist 定名）: PASS。导入表 IAT 0x7e15f4/0x7e15f8 属 ole32.dll；0x820270 的 8 个 push 站点全部命中 call [0x7e15f4]；0x818858 的 16 个站点命中数为 0；0x7f7c70 原始 push 站点数为 0。
主张二（IID 常量撤回错误表述）: PASS。0x7e36c0 与 0x7e9b20 均为 16 字节 IID 常量，GUID 文本见第 5 节。
主张三（接受点完整）: PASS。三个宿主槽位与 RTTI 宿主逐一核实；三入口在 .rdata 中各仅 1 处 u32，均为 vtable 槽；bf/68 立即数引用合计均为 0。
主张四（IID 定名）: PASS。ApplicationClass 的 mdisp 0 非 IUnknown 基类为 .?AUIApplication@@；SwizzleManagerClass 的 mdisp 0 非 IUnknown 基类为 .?AUISwizzle@@。

## 10. 与主张不符之处
未发现推翻四条主张的字节证据。
审计范围补充: TiberianSunClassFactory 的 RTTI mdisp 0 非 IUnknown 基类为 .?AUIClassFactory@@，与 0x429270 对应，但卡面第 4 条只要求两个 IID，不构成矛盾。

回合数: 1
用时: 约 15 分钟（含修正 RTTI 字段偏移与上下文复核）
