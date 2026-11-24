# -*- coding: utf-8 -*-
"""生成 B2 批 18 行 EVIDENCE/ROW_<entry>.txt；每行独立事实，逐行落盘。
并同步把 ③b② PASS 行追加到 delta.tsv（只放四环齐全者）。
"""
import os, json
WORK = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(WORK)
EV = os.path.join(ROOT, 'EVIDENCE')
os.makedirs(EV, exist_ok=True)
A = {r['entry']: r for r in json.load(open(os.path.join(WORK,'analysis.json'), encoding='utf-8'))}

# 每行的 ②（RTTI）与 ④（构造器安装点）由 analysis.json + verify_ring2/witness_check 取证结果固化
R2 = {
 '005FEAF0':('007EF614','007EF600',0x14,5,'008076F0','008334B0','.?AVOverlayTypeClass@@'),
 '005FEC10':('007EF618','007EF600',0x18,6,'008076F0','008334B0','.?AVOverlayTypeClass@@'),
 '005FEF30':('007EF620','007EF600',0x20,8,'008076F0','008334B0','.?AVOverlayTypeClass@@'),
 '006B4FA0':('007F331C','007F32FC',0x20,8,'008098E8','0083FFE0','.?AVSmudgeClass@@'),
 '006B5550':('007F35A8','007F3528',0x80,32,'008099A0','00840008','.?AVSmudgeTypeClass@@'),
 '006B55C0':('007F35B4','007F3528',0x8c,35,'008099A0','00840008','.?AVSmudgeTypeClass@@'),
 '006B5850':('007F353C','007F3528',0x14,5,'008099A0','00840008','.?AVSmudgeTypeClass@@'),
 '006B58B0':('007F3540','007F3528',0x18,6,'008099A0','00840008','.?AVSmudgeTypeClass@@'),
 '006B6160':('007F3548','007F3528',0x20,8,'008099A0','00840008','.?AVSmudgeTypeClass@@'),
 '006BF210':('007F37A4','007F3798',0x0c,3,'00809D08','00840FC8','.?AV?$TClassFactory@VTerrainTypeClass@@@@'),
 '006BF390':('007F37BC','007F37B0',0x0c,3,'00809D58','00841000','.?AV?$TClassFactory@VTerrainClass@@@@'),
 '0071B920':('007F5398','007F522C',0x16c,91,'0080C3E0','00842D48','.?AVTerrainClass@@'),
 '0071C1B0':('007F5340','007F522C',0x114,69,'0080C3E0','00842D48','.?AVTerrainClass@@'),
 '0071C730':('007F5288','007F522C',0x5c,23,'0080C3E0','00842D48','.?AVTerrainClass@@'),
 '0071CDA0':('007F5240','007F522C',0x14,5,'0080C3E0','00842D48','.?AVTerrainClass@@'),
 '0071DDD0':('007F54D8','007F5458',0x80,32,'0080C498','008445E8','.?AVTerrainTypeClass@@'),
 '0071DE10':('007F54E4','007F5458',0x8c,35,'0080C498','008445E8','.?AVTerrainTypeClass@@'),
 '0071DEA0':('007F54BC','007F5458',0x64,25,'0080C498','008445E8','.?AVTerrainTypeClass@@'),
}
# vt -> (构造器安装点 write_va, 所在函数, base ctor 证据, 字节)
R4 = {
 '007EF600':('005FE2F1','005FE250','call 0x5f7090 base ctor@005FE259 + field init','c7 06 00 f6 7e 00'),
 '007F32FC':('006B4A5C','006B4A50','call 0x5f3900 base ctor@006B4A53 + field init','c7 06 fc 32 7f 00'),
 '007F3528':('006B529B','006B5260','call 0x5f7090 base ctor@006B5269 + field init','c7 06 28 35 7f 00'),
 '007F3798':('006BF149','006BF140','size16 ctor: mov [eax+4],0@006BF142; mov eax,ecx@006BF140','c7 00 98 37 7f 00'),
 '007F37B0':('006BF2C9','006BF2C0','size16 ctor: mov [eax+4],0@006BF2C2; mov eax,ecx@006BF2C0','c7 00 b0 37 7f 00'),
 '007F522C':('0071B7BC','0071B7B0','ctor: mov dl,1@0071B7B7 + multi-vptr install + call 0x7258d0@0071B7D6','c7 06 2c 52 7f 00'),
 '007F5458':('0071DAF7','0071DA80','call 0x5f7090 base ctor@0071DA89 + field init','c7 06 58 54 7f 00'),
}

# 每行 ③ 判定（r3_ok, 段落文本）
R3 = {
'005FEAF0':(True, '''③b② E_POINTER 判负、流读入（与 B1 004839F0 同型）：站点 call 0x5f9720@0x005FEB04(e8 17 ac ff ff)；test eax,eax@0x005FEB09(85 c0)；jl 0x005FEBF9@0x005FEB0B(0f 8c e8 00 00 00)。被调 0x005F9720 于 0x005F9847 call 0x410380([eax+0xc] Read 槽=流读入)，0x005F984C cmp eax,ebx(ebx=0)→0x005F984E jl 0x005F993E 失败路原样回传负 HRESULT，成功路 0x005F993C xor eax,eax 返 0，返回约定字节可伪证。站点失败 jl 跳 0x005FEBF9 弹栈 ret 8（跳过成功路 0x005FEBF7 xor eax,eax）原样返负 HRESULT；成功路 test esi,esi@0x005FEB11 后于 0x005FEB21 c7 06 00 f6 7e 00 装 vt 0x7ef600 并 call 0x5f7320/0x6cf240/0x7c9ff0 做真实装载，末尾 xor eax,eax 返 0。两路动作真不同；test 与 jl 相邻无 eax 覆写；单 call 非多路同一 call。语义=流读入（与 0x410380 的 [eax+0xc] Read 槽方向一致，未写反）。'''),
'005FEC10':(False, '''FAIL ③a 纯转发（29B 薄封装，与 B1 005439F0/00549D70 同型）：站点 call 0x5f9950@0x005FEC1F(e8 2c ad ff ff)；test eax,eax@0x005FEC24(85 c0)；jl@0x005FEC26(7c 02)；xor eax,eax@0x005FEC28；ret 0xc@0x005FEC2A。被调 0x5f9950 本身又是 29B 薄封装（call 0x410320→test→jl→xor→ret），本行只是二次转发，成功路除 xor 归零外无任何真实动作，两路仅 HRESULT-vs-0 返回映射差异，属卡面禁的 ③a「纯转发/零+默认」。'''),
'005FEF30':(False, '''FAIL 间接调用返回约定不可伪证：站点 call dword ptr [edx+0x10]@0x005FEF6A(ff 52 10)=INDIRECT，cmp eax,-1@0x005FEF6D(83 f8 ff)，je 0x005FEF9F@0x005FEF70(74 2d)。call 目标来自虚表槽 [0xa83d80]+0x10，不是固定 callee，-1 哨兵不能从被调字节伪证；与 B1 00543B10/005FDF70 同因判负。'''),
'006B4FA0':(False, '''FAIL 间接调用返回约定不可伪证：站点 call dword ptr [edx+0x10]@0x006B4FDA(ff 52 10)=INDIRECT（目标 [0xa8b1e0]+0x10），cmp eax,-1@0x006B4FDD(83 f8 ff)，je 0x006B500F@0x006B4FE0(74 2d)。虚表间接 call，-1 不可字节伪证，与 B1 00543B10 同因。'''),
'006B5550':(False, '''FAIL 分配包装零判断（D-46(A)，与 B1 0x7C8E17 族同型）：站点 call 0x7c8e17@0x006B555B(e8 b7 38 11 00)=分配器（push 1; push 0xb0; call 0x7c9442），test eax,eax@0x006B5563(85 c0)，je 0x006B55B0@0x006B5565(74 49)。分配成功返指针/失败返 0，test/je 是 NULL 零判断而非可伪证错误码；成功路再 call 0x6b4a50 后又一次 test/je 零判断。'''),
'006B55C0':(False, '''FAIL 分配包装零判断（D-46(A)）：站点 call 0x7c8e17@0x006B55C8(e8 4a 38 11 00)=分配器，test eax,eax@0x006B55D0(85 c0)，je 0x006B55E7@0x006B55D2(74 13)，xor eax,eax@0x006B55E7。指针/0 零判断，非错误码返回约定。'''),
'006B5850':(True, '''③b② E_POINTER 判负、流读入（与 B1 004839F0 同型）：站点 call 0x5f9720@0x006B585B(e8 c0 3e f4 ff)；test eax,eax@0x006B5860(85 c0)；jl 0x006B589F@0x006B5862(7c 3b)。被调 0x005F9720 于 0x005F9847 call 0x410380([eax+0xc] Read 槽=流读入)，0x005F984C cmp eax,ebx(0)→0x005F984E jl 失败返负 HRESULT，成功 0x005F993C xor eax,eax 返 0（返回约定字节可伪证）。失败路 jl→0x006B589F 弹栈 ret 8 原样返 HRESULT；成功路 0x006B5874 c7 06 28 35 7f 00 装 vt 0x7f3528 并 call 0x5f7320/0x5f8110/0x5f9070 真实装载，0x006B589D xor eax,eax 返 0。两路真不同；test/jl 相邻无 eax 覆写；单 call。语义=流读入（未写反）。'''),
'006B58B0':(False, '''FAIL ③a 纯转发（29B 薄封装，与 B1 005439F0 同型）：站点 call 0x5f9950@0x006B58BF(e8 8c 40 f4 ff)；test eax,eax@0x006B58C4；jl@0x006B58C6(7c 02)；xor eax,eax@0x006B58C8；ret 0xc。被调 0x5f9950 是 29B 薄封装，本行二次转发，成功路无真实动作，属禁的 ③a。'''),
'006B6160':(False, '''FAIL 间接调用返回约定不可伪证：站点 call dword ptr [edx+0x10]@0x006B61B9(ff 52 10)=INDIRECT（[0xa8ec18]+0x10），cmp eax,-1@0x006B61BC(83 f8 ff)，je 0x006B61EE@0x006B61BF(74 2d)。虚表间接 call，-1 不可字节伪证。'''),
'006BF210':(False, '''FAIL ③b② 无可字节伪证的 callee 错误码返回约定：本行是 COM 工厂 CreateInstance。机械站点 call 0x7c8e17@0x006BF241=分配器，test eax,eax@0x006BF249，je 0x006BF25C@0x006BF24B——指针/0 零判断（D-46(A)）。其余分支均不合格：test edi,edi@0x006BF216 与 test eax,eax@0x006BF22E 是对入参（ppv/pUnkOuter）的检查而非 callee 返回；call dword ptr [eax]@0x006BF26F（虚 QueryInterface）为 INDIRECT，其 edi 的 test/jge@0x006BF273/0x006BF275 返回值不可从固定 callee 字节伪证。硬编码 E_INVALIDARG 0x80070057/E_NOAGGREGATION 0x80040110/E_OUTOFMEMORY 0x8007000E 不挂在任一可伪证 callee 返回分支上。'''),
'006BF390':(False, '''FAIL ③b② 无可字节伪证的 callee 错误码返回约定（与 006BF210 同构）：机械站点 call 0x7c8e17@0x006BF3C1=分配器，test eax,eax@0x006BF3C9，je 0x006BF3DA@0x006BF3CB——零判断（D-46(A)）。test edi,edi@0x006BF396/test eax,eax@0x006BF3AE 为入参检查；call dword ptr [eax]@0x006BF3ED 虚 QI 为 INDIRECT，edi 的 test/jge 返回不可字节伪证。'''),
'0071B920':(False, '''FAIL 状态码分派+分配零判断，非可伪证错误码：站点1 call 0x5f5390@0x0071B986(e8 05 9a ed ff)，cmp eax,5@0x0071B98B(83 f8 05)，jne 0x0071B99E@0x0071B992(75 0a)，随后 cmp eax,4@0x0071B99E/jne 0x0071BB79。被调 0x005F5390 返回 0/1/2/5 等状态值，==5/==4 是状态分派（5、4 均非 is_falsifiable 错误哨兵；0x0071B98E mov [esp+0x10],eax 只写内存不覆写 eax），不构成失败/成功错误码合同。站点2 call 0x7c8e17@0x0071B9C0=分配器 + test/je@0x0071B9CC/CE 零判断。两站点均 FAIL。'''),
'0071C1B0':(False, '''FAIL 间接调用+零判断：机械站点 call dword ptr [edx+0x6c]@0x0071C1E7(ff 52 6c)=INDIRECT（TerrainClass 虚槽），test eax,eax@0x0071C1EA(85 c0)，je 0x0071C353@0x0071C1F0(0f 84 5d 01 00 00)。虚表间接 call 返回约定不可字节伪证，且 test/je 为零判断（D-46(A)）。'''),
'0071C730':(False, '''FAIL 零判断（D-46(A)）：站点 call 0x426630@0x0071C7CA(e8 61 9e d0 ff)，test eax,eax@0x0071C7CF(85 c0)，jne 0x0071C840@0x0071C7D1(75 6d)。被调 0x00426630 于 0x00426635 cmp edx,-1→0x0042664B xor eax,eax 返 0，或 sub eax,ecx 后返计数——即 0/非0 零判断，非可伪证错误码返回约定。'''),
'0071CDA0':(True, '''③b② E_POINTER 判负、流读入（与 B1 004839F0 同型）：站点 call 0x5f5e80@0x0071CE79(e8 02 90 ed ff)；mov edi,eax@0x0071CE7E(8b f8，仅保存返回值，未覆写)；test edi,edi@0x0071CE80(85 ff)；jl 0x0071CF23@0x0071CE82(0f 8c 9b 00 00 00)。被调 0x005F5E80 于 0x005F5E8B call 0x410380([eax+0xc] Read 槽=流读入)，0x005F5E90 test eax,eax→0x005F5E92 jl 0x005F5EF9 失败路原样回传负 HRESULT，成功路 0x005F5EF7 xor eax,eax 返 0（返回约定字节可伪证）。失败路 jl→0x0071CF23 mov eax,edi 原样返负 HRESULT；成功路 0x0071CE98 c7 45 00 2c 52 7f 00 装 vt 0x7f522c、ff 51 10（[ecx+0x10] Read）读入并登记全局表，末 mov eax,edi(=0) 返 0。两路动作真不同；test(edi) 与 jl 相邻无覆写；单 call 非多路同一 call。语义=流读入（未写反）。'''),
'0071DDD0':(False, '''FAIL 分配包装零判断（D-46(A)）：站点 call 0x7c8e17@0x0071DDD8(e8 3a b0 0a 00)=分配器，test eax,eax@0x0071DDE0(85 c0)，je 0x0071DDFB@0x0071DDE2(74 17)。指针/0 零判断，非错误码；成功路 call 0x71bb90 后再 test/je 亦零判断。'''),
'0071DE10':(False, '''FAIL 分配包装零判断（D-46(A)）：站点 call 0x7c8e17@0x0071DE18(e8 fa af 0a 00)=分配器，test eax,eax@0x0071DE20(85 c0)，je 0x0071DE35@0x0071DE22(74 11)，xor eax,eax@0x0071DE35。指针/0 零判断。'''),
'0071DEA0':(False, '''FAIL 间接调用零判断 + bool/al 判断（D-46(A)）：机械站点 call dword ptr [edx+0x9c]@0x0071DFCA(ff 92 9c 00 00 00)=INDIRECT，test eax,eax@0x0071DFD0，je 0x0071DFF8@0x0071DFD2——间接且零判断。另一站点 call 0x5f92d0@0x0071DEBB；test al,al@0x0071DEC0(84 c0)；je 0x0071E0B4@0x0071DEC2——被调 0x005F92D0 返 al=1/0 布尔（0x005F9691 b0 01 / 0x005F969E 32 c0），是 bool 0/1 判断，D-46(A) 排除。无合格 ③b②。'''),
}

semantics = {
'005FEAF0':'OverlayTypeClass 虚槽5（流读入）：以 0x5f9720→0x410380 校验流并整体读入 OverlayType；空/失败返负 HRESULT 原样早退，成功则装 vt 0x7ef600 并逐字段读入后返 0。',
'005FEC10':'OverlayTypeClass 虚槽6（薄转发写出）：把三参转发 0x5f9950→0x410320 写流，失败返 HRESULT、成功返 0；本行无真实 I/O 动作。',
'005FEF30':'OverlayTypeClass 虚槽8（构造/装载）：装 vt 0x7ef600 后经全局表虚槽 [edx+0x10] 取索引，按 -1 哨兵决定移出登记；返回本对象指针。',
'006B4FA0':'SmudgeClass 虚槽8（构造/装载）：装 vt 0x7f32fc 后经全局表虚槽取索引，按 -1 决定移出；返回本对象。',
'006B5550':'SmudgeTypeClass 虚槽32：分配 0xb0 字节并 0x6b4a50 构造 SmudgeClass，成功返 1、失败返 0（NULL 零判断）。',
'006B55C0':'SmudgeTypeClass 虚槽35：分配并构造 SmudgeClass 后返回构造结果，失败返 0（零判断）。',
'006B5850':'SmudgeTypeClass 虚槽5（流读入）：以 0x5f9720→0x410380 校验流并整体读入 SmudgeType；失败返负 HRESULT 原样早退，成功装 vt 0x7f3528 并读入后返 0。',
'006B58B0':'SmudgeTypeClass 虚槽6（薄转发写出）：转发 0x5f9950→0x410320 写流，失败返 HRESULT、成功返 0；无真实动作。',
'006B6160':'SmudgeTypeClass 虚槽8（构造/装载）：装 vt 0x7f3528 后经全局表虚槽取索引并按 -1 移出；返回本对象。',
'006BF210':'TClassFactory<VTerrainTypeClass> 虚槽3（CreateInstance）：校验 ppv/pUnkOuter、分配 0x2bc、0x71da80 构造后虚 QueryInterface，按 HRESULT 决定 Release；错误码 E_INVALIDARG/NOAGGREGATION/OUTOFMEMORY。',
'006BF390':'TClassFactory<VTerrainClass> 虚槽3（CreateInstance）：同上，分配 0xe0、0x71bdf0 构造 TerrainClass 后虚 QueryInterface。',
'0071B920':'TerrainClass 虚槽91：按外部对象状态经 0x5f5390 解析（5/4 状态码分派），分配 0x1c8 并查表/登记/重算 Ceiling；失败静默返回保存的状态值。',
'0071C1B0':'TerrainClass 虚槽69：经虚槽取范围计数，零判断早退；否则按标志计算跨度并 0x4aed70 绘制道路/桥梁段。',
'0071C730':'TerrainClass 虚槽23：先 0x5f3e70 读配置，按 0x426630 计数零判断决定是否重置边界并登记/刷新本对象。',
'0071CDA0':'TerrainClass 虚槽5（流读入）：以 0x5f5e80→0x410380 校验流并整体读入 Terrain；失败返负 HRESULT 原样早退，成功装 vt 0x7f522c、ff 51 10 读入并登记全局表后返 0。',
'0071DDD0':'TerrainTypeClass 虚槽32：分配 0xe0 并 0x71bb90 构造 TerrainTypeClass，成功返 1、失败返 0（NULL 零判断）。',
'0071DE10':'TerrainTypeClass 虚槽35：分配并构造 TerrainTypeClass 后返回构造结果，失败返 0（零判断）。',
'0071DEA0':'TerrainTypeClass 虚槽25（装载）：0x5f92d0 装载 bool 判断早退；否则逐字段从流读入名称/标志/颜色/作战数据等。',
}

order = ['005FEAF0','005FEC10','005FEF30','006B4FA0','006B5550','006B55C0','006B5850','006B58B0',
         '006B6160','006BF210','006BF390','0071B920','0071C1B0','0071C730','0071CDA0','0071DDD0','0071DE10','0071DEA0']

delta_lines = []
for entry in order:
    rec = A[entry]
    r1 = rec['ring1']
    slot,vt,off,slotnum,col,td,rtti = R2[entry]
    wr,wf,wbase,wbytes = R4[vt]
    r3ok, r3text = R3[entry]
    path = os.path.join(EV, 'ROW_%s.txt' % entry).replace('\\','/')
    txt = []
    txt.append('# ROW %s  S06  %s' % (entry, rec['name']))
    txt.append('')
    txt.append('## 环① 入口与函数边界')
    txt.append('- entry=%s（大写十六进制无 0x；delta entry 列原样写此串）' % entry)
    txt.append('- in_text=%s；atlas size=%s B；反汇编 n_instr=%s，skipdata=%s（0=无数据字节误当指令）' % (r1['in_text'],r1['atlas_size'],r1['n_disasm'],r1['n_skipdata']))
    txt.append('- 入口首指令=%s；末指令=%s；ends_with_ret_or_jmp=%s' % (r1['first'],r1['last'],r1['ends_with_ret_or_jmp']))
    txt.append('')
    txt.append('## 环② 类身份（独立取证；Class::slotN 的 Class 仅作线索）')
    txt.append('- 线索=%s::slot%d（槽号 %d）' % (rec['name'].split('::')[0], slotnum, slotnum))
    txt.append('- 槽驻留 %s [.rdata]，vtable base=%s，slot offset=+%d（slot#=%d）%s' % (slot,vt,off,slotnum,' [高槽号：回扫上限提到 130 才命中 COL]' if slotnum>40 else ''))
    txt.append('- 槽值 4B @%s = entry %s（verify_ring2.py 逐行核 MATCH）' % (slot,entry))
    txt.append('- RTTI: COL=%s sig@+0=00000000 pTD@+0xC；TD=%s；name@TD+8 = `%s`' % (col,td,rtti))
    txt.append('- 判定：RTTI 名串与线索类名一致且 slot offset/4=%d=线索槽号，槽值==entry ⇒ ② 钉住（证据为 .rdata RTTI 字节链，非 slotN 字面）。' % slotnum)
    txt.append('')
    txt.append('## 环③ 整体合同（只认 ③b；本行裁定 %s）' % ('PASS' if r3ok else 'FAIL'))
    txt.append('- ' + r3text)
    txt.append('')
    txt.append('## 环④ 使用见证（活 vtable 槽位；㉓ 析构器锚点排除）')
    txt.append('- direct_callers: %s（direct-only 不足，不作本环锚点）' % rec['ring4_direct'])
    txt.append('- vtable %s 的 .text 构造器安装点（行外、atexit=False）：write=%s in_func=%s；%s；字节 %s' % (vt,wr,wf,wbase,wbytes))
    txt.append('- 同 vtable 的其它写点若为行内装载/析构器（全局表注销 / push 1;call [vtable]）按 ㉓ 排除，未用作锚点；构造器安装点与 ② 的 .rdata RTTI 链不同源。')
    txt.append('- 判定：④ **PASS**')
    txt.append('')
    txt.append('## 裁定')
    txt.append('- ①=PASS ②=PASS ③=%s ④=PASS ②④不同源=是' % ('PASS' if r3ok else 'FAIL'))
    txt.append('- **四环齐全=%s**' % ('是 -> [已证]；产出 delta 行' if r3ok else '否；不产出'))
    txt.append('')
    txt.append('## 本行地址锚')
    txt.append('- 0x%s；0x%s；0x%s；0x%s；0x%s' % (entry,slot,col,td,wr))
    open(os.path.join(EV,'ROW_%s.txt'%entry),'w',encoding='utf-8').write('\n'.join(txt)+'\n')
    if r3ok:
        evpath = 'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/NAMED_PUSH_S06_B2/EVIDENCE/ROW_%s.txt' % entry
        delta_lines.append('%s\tS06\t%s\t%s\t[已证]\t%s' % (entry, rec['name'], semantics[entry], evpath))
    print('ROW %s written (③=%s)' % (entry, 'PASS' if r3ok else 'FAIL'))

# append PASS rows to delta.tsv (header already present)
with open(os.path.join(ROOT,'delta.tsv'),'a',encoding='utf-8') as f:
    for line in delta_lines:
        f.write(line+'\n')
print('delta.tsv appended %d PASS rows' % len(delta_lines))
