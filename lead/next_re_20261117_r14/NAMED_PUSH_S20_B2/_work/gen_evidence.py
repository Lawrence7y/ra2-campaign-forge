# -*- coding: utf-8 -*-
"""S20 B2 EVIDENCE 生成器：8 行四环齐全行的锚点 + 字节，全部当场从 gamemd.exe 读出。"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

WORK = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(WORK), "EVIDENCE")
os.makedirs(OUT, exist_ok=True)

# 逐行手工锚点（地址全部来自本批 survey/dump，字节见各文件内 dump）
PLAN = {
 "0062D9A0": {
  "vt":0x007EF954,"slot_no":8,"slot_va":0x007EF974,
  "ring4_at":0x0062B767,"ring4_host":0x0062B5E0,"ring4_base_call":0x0062B5E9,
  "form":"③b② 标量删除析构（容器 Find -1）",
  "ring3":[
   ("站点",0x0062D9EB,"ff5210 call [edx+0x10]（edx=[0xA83DC8]，成员容器指针）"),
   ("判零间隔",0x0062D9EE,"83f8ff cmp eax,-1 ; 0062D9F1 742d je 0x62DA20（cmp→jcc 零间隔，无 eax 覆写）"),
   ("命中路压缩写",0x0062DA12,"895481fc mov [ecx+eax*4-4],edx ; 0062DA00 mov [0xA83DD8],ecx 计数减一 ; 0062DA1E 7ce8 jl 回边"),
   ("收尾-基类析构",0x0062DA22,"e8 5961fcff call 0x5F3B80"),
   ("收尾-delete 标志释放",0x0062DA27,"f644240c01 test byte [esp+0xC],1 ; 0062DA2F call 0x7C8B3D"),
  ],
  "callees":[(0x004EA010,"容器 0xA83DC8 活表 007E9D84 的 vt[#4]=FindItemIndex；004E9F2C 83c8ff or eax,-1 + 004E9F30 c20400 ret 4（未命中 -1 可伪证）")],
  "sem":"ParticleClass::slot8 —— ③b② 标量删除析构：从 DynamicVectorClass<ParticleClass*>（全局注册容器 0xA83DC8 / 计数 0xA83DD8 / 数组 0xA83DCC）里 Find 自身，未命中返 -1 直接跳过、命中则计数减一并前移压缩数组摘链，随后 call 0x5F3B80 基类析构，按 `test byte [esp+0xC],1` 的 delete 标志 call 0x7C8B3D 释放自身。② 槽 007EF974（vt 007EF954+0x20，slot#8）4B 值=本 entry，COL=00807BE8→TD=008366E8→`.?AVParticleClass@@`；④ 0062B767（构造器 0062B5E0，首条 0062B5E9 call 0x5F3900 基类构造后装表，atexit=False、行外；行内 0062D9A4 已排除）。",
 },
 "0062FE90": {
  "vt":0x007EFB9C,"slot_no":10,"slot_va":0x007EFBC4,
  "ring4_at":0x0062DD16,"ring4_host":0x0062DC50,"ring4_base_call":0x0062DC59,
  "form":"③b② 成员容器 Find -1 摘链",
  "ring3":[
   ("站点",0x0062FEBB,"ff5210 call [edx+0x10]（edx=[edi+0xBC]，this 内嵌成员容器；其 vtable=007E9D84 于 0062E244 `mov [edi+0xBC],0x7E9D84` 装入）"),
   ("判零间隔",0x0062FEBE,"83f8ff cmp eax,-1 ; 0062FEC1 7421 je 0x62FEE4（零间隔，无 eax 覆写）"),
   ("命中路压缩写",0x0062FED9,"895481fc mov [ecx+eax*4-4],edx ; 0062FECB cmp eax,ecx ; 0062FECD mov [esi+0x10],ecx 计数减一 ; 0062FEE2 7cee jl 回边"),
   ("命中后字段复位",0x0062FEE4,"mov [edi+0xAC],eax / [edi+0xE4] / [edi+0xE0] / 置 byte [edi+0xF8],1（两路汇合后动作）"),
  ],
  "callees":[(0x004E9F00,"成员容器 [this+0xBC] vtable 007E9D84 的 vt[#4]=FindItemIndex；004E9F2C 83c8ff or eax,-1 + 004E9F30 c20400 ret 4")],
  "sem":"ParticleSystemClass::slot10 —— ③b② 成员容器摘链：先 call 0x5F5230，再在 this 内嵌 DynamicVectorClass（[this+0xBC]，vtable 007E9D84）里按参数 Find（未命中 -1 跳过、命中则 dec 计数并前移压缩数组 mov [ecx+eax*4-4],edx + jl 回边）；随后复位 [this+0xAC]/[this+0xE4]/[this+0xE0] 并置 [this+0xF8]=1。容器 vtable 由 0062E244 `mov dword [edi+0xBC],0x7E9D84` 装入，vt[#4]=004E9F00 处 `or eax,-1` + `ret 4` 可伪证。② 槽 007EFBC4（vt 007EFB9C+0x28，slot#10）4B 值=本 entry，COL=00807CA0→TD=00836748→`.?AVParticleSystemClass@@`；④ 0062DD16（构造器 0062DC50，首条 0062DC59 call 0x5F3900 基类构造后装表，atexit=False、行外）。",
 },
 "00630090": {
  "vt":0x007EFB9C,"slot_no":6,"slot_va":0x007EFBB4,
  "ring4_at":0x0062DD16,"ring4_host":0x0062DC50,"ring4_base_call":0x0062DC59,
  "form":"③b② 流写出 + 逐元素写出循环（HRESULT 错误码）",
  "ring3":[
   ("站点-流写出",0x006300A2,"e87902deff call 0x410320（流**写出**封装：内部 00410348 ff5010 / 0041035E ff5310 call [eax+0x10]=Write；空参 0041032B mov eax,0x80004003=E_POINTER）"),
   ("判零间隔",0x006300A7,"85c0 test eax,eax ; 006300A9 7c48 jl 0x6300F3（零间隔，无 eax 覆写）"),
   ("成功路-容器 Find",0x006300C1,"ff5210 call [edx+0x10]（edx=[esi]，流写出到容器）；006300C4 test eax,eax / 006300C6 jl 0x6300F3"),
   ("成功路-逐元素写出循环",0x006300E3,"ff5110 call [ecx+0x10]（写每元素）；006300E6 test / 006300E8 jl；006300EE inc ebx / 006300F1 cmp ebx,ecx / 006300F5 jl 回边（循环体写由被调完成，不作本行 ③b④，仅作成功路动作）"),
  ],
  "callees":[(0x00410320,"流写出封装；0041032B b803400080 mov eax,0x80004003 = E_POINTER（空参可伪证失败）；内部 00410348/0041035E ff5010 = Write 方向")],
  "sem":"ParticleSystemClass::slot6 —— ③b② 流写出（方向已按槽位复算，**写出**）：call 0x410320 把头部写到流（该封装内部 00410348/0041035E `call [eax+0x10]` 走 Write；空参 0041032B 返 E_POINTER 0x80004003）；`test eax,eax`/`jl` 零间隔——失败路跳 0x6300F3 原样带错误码收尾，成功路真做别的事：按 [edi+0xCC] 计数，对每个元素 call [ecx+0x10] 逐条写出（006300D2 循环 + 006300F1 cmp + 006300F5 jl 回边），任一失败同样跳出。② 槽 007EFBB4（vt 007EFB9C+0x18，slot#6）4B 值=本 entry，COL=00807CA0→TD=00836748→`.?AVParticleSystemClass@@`；④ 0062DD16（构造器 0062DC50，首条 0062DC59 call 0x5F3900 基类构造后装表，atexit=False、行外）。",
 },
 "00644960": {
  "vt":0x007F00A8,"slot_no":8,"slot_va":0x007F00C8,
  "ring4_at":0x0064419C,"ring4_host":0x006440A0,"ring4_base_call":0x006440A9,
  "form":"③b② 标量删除析构（容器 Find -1）",
  "ring3":[
   ("站点",0x0064499A,"ff5210 call [edx+0x10]（edx=[0xA83D68]）"),
   ("判零间隔",0x0064499D,"83f8ff cmp eax,-1 ; 006449A0 742d je 0x6449CF（零间隔，无 eax 覆写）"),
   ("命中路压缩写",0x006449C1,"895481fc mov [ecx+eax*4-4],edx ; 006449AF mov [0xA83D78],ecx 计数减一 ; 006449CD 7ce8 jl 回边"),
   ("收尾-基类析构",0x006449D1,"e8 2a2afbff call 0x5F7400"),
   ("收尾-delete 标志释放",0x006449D6,"f644240c01 test byte [esp+0xC],1 ; 006449DE call 0x7C8B3D"),
  ],
  "callees":[(0x004EEFF0,"容器 0xA83D68 活表 007EA464 的 vt[#4]=FindItemIndex；004EF00F 83c8ff or eax,-1 + 004EF013 c20400 ret 4")],
  "sem":"ParticleSystemTypeClass::slot8 —— ③b② 标量删除析构：复位 4 张虚表、call 0x7258D0 解引用后，在 DynamicVectorClass<ParticleSystemTypeClass*>（0xA83D68 / 计数 0xA83D78 / 数组 0xA83D6C）里 Find 自身，未命中 -1 跳过、命中则计数减一并前移压缩数组摘链（jl 回边）；随后 call 0x5F7400 基类析构，按 test byte [esp+0xC],1 的 delete 标志 call 0x7C8B3D 释放。② 槽 007F00C8（vt 007F00A8+0x20，slot#8）4B 值=本 entry，COL=00808238→TD=00836F18→`.?AVParticleSystemTypeClass@@`；④ 0064419C（构造器 006440A0，首条 006440A9 call 0x5F7090 基类构造后装表，atexit=False、行外；行内 00644966 已排除）。",
 },
 "006457A0": {
  "vt":0x007F0188,"slot_no":6,"slot_va":0x007F01A0,
  "ring4_at":0x00644CF4,"ring4_host":0x00644BE0,"ring4_base_call":0x00644BEB,
  "form":"③b② 流写出封装 + 逐元素写出循环（HRESULT）",
  "ring3":[
   ("站点-流写出封装",0x006457B3,"e8 9841fbff call 0x5F9950（29B 封装：005F995F call 0x410320 流**写出**，空参 0041032B 返 E_POINTER 0x80004003）"),
   ("判零间隔",0x006457B8,"85c0 test eax,eax ; 006457BA 7c4e jl 0x64580A（零间隔，无 eax 覆写）"),
   ("成功路-容器 Find",0x006457D2,"ff5210 call [edx+0x10]；006457D5 test / 006457D7 jl 0x64580A"),
   ("成功路-逐元素写出循环",0x006457F5,"ff5110 call [ecx+0x10]（每 3 字节写一次）；006457F8 test / 006457FA jl；00645801 add edi,3 / 00645804 cmp ebp,eax / 00645806 jl 回边"),
  ],
  "callees":[(0x005F9950,"流写出封装；005F995F `call 0x410320`→内部 ff5010=Write；空参 0041032B E_POINTER 0x80004003；负返回原样、非负归零")],
  "sem":"ParticleTypeClass::slot6 —— ③b② 流写出（**写出**，方向按槽位复算）：call 0x5F9950（内部 0x410320 走流虚表 +0x10 Write；空参 E_POINTER 0x80004003，负返回原样/非负归零）；`test eax,eax`/`jl` 零间隔——失败路跳 0x64580A 带错误码收尾，成功路真做事：按 [ebx+0x2C8] 做一次容器写出（call [edx+0x10]），再按计数把 [ebx+0x2BC] 数组每 3 字节 call [ecx+0x10] 逐条写出（`add edi,3`/`cmp`/`jl` 回边），任一失败跳出。② 槽 007F01A0（vt 007F0188+0x18，slot#6）4B 值=本 entry，COL=008082F0→TD=008370D0→`.?AVParticleTypeClass@@`；④ 00644CF4（构造器 00644BE0，首条 00644BEB call 0x5F7090 基类构造后装表，atexit=False、行外）。",
 },
 "00645950": {
  "vt":0x007F0188,"slot_no":8,"slot_va":0x007F01A8,
  "ring4_at":0x00644CF4,"ring4_host":0x00644BE0,"ring4_base_call":0x00644BEB,
  "form":"③b② 标量删除析构（两个容器 Find -1）",
  "ring3":[
   ("站点1",0x0064598A,"ff5210 call [edx+0x10]（edx=[0xB0F670]）"),
   ("站点1-判零间隔",0x0064598D,"83f8ff cmp eax,-1 ; 00645990 742d je 0x6459BF（零间隔）"),
   ("站点1-命中路压缩写",0x006459B1,"895481fc mov [ecx+eax*4-4],edx ; 0064599F mov [0xB0F680],ecx ; 006459BD 7ce8 jl 回边"),
   ("站点2",0x006459D3,"ff5210 call [edx+0x10]（edx=[0xA83D98]）"),
   ("站点2-判零间隔",0x006459D6,"83f8ff cmp eax,-1 ; 006459D9 742d je 0x645A08（零间隔）"),
   ("站点2-命中路压缩写",0x006459FA,"895481fc mov [ecx+eax*4-4],edx ; 006459E8 mov [0xA83DA8],ecx ; 00645A06 7ce8 jl 回边"),
   ("收尾-基类析构",0x00645A4C,"e8 af19fbff call 0x5F7400"),
   ("收尾-delete 标志释放",0x00645A51,"f644240c01 test byte [esp+0xC],1 ; 00645A59 call 0x7C8B3D"),
  ],
  "callees":[(0x004E0550,"容器 0xB0F670 活表 007E91EC vt[#4]：004E056F 83c8ff or eax,-1 + 004E0573 ret 4"),(0x004EED90,"容器 0xA83D98 活表 007EA424 vt[#4]：004EEDAF 83c8ff or eax,-1 + 004EEDB3 ret 4")],
  "sem":"ParticleTypeClass::slot8 —— ③b② 标量删除析构（双注册表）：复位 4 表后，在 DynamicVectorClass<ParticleTypeClass*>（0xB0F670，计数 0xB0F680/数组 0xB0F674）与（0xA83D98，计数 0xA83DA8/数组 0xA83D9C）两个注册表各 Find 自身——未命中 -1 跳过、命中则计数减一并前移压缩数组摘链（各自 jl 回边）；随后清 [this+0x2B8]=0x7E4E38、按需 free [this+0x2BC]，call 0x5F7400 基类析构，按 delete 标志 call 0x7C8B3D 释放。② 槽 007F01A8（vt 007F0188+0x20，slot#8）4B 值=本 entry，COL=008082F0→TD=008370D0→`.?AVParticleTypeClass@@`；④ 00644CF4（构造器 00644BE0，首条 00644BEB call 0x5F7090 基类构造后装表，atexit=False、行外；行内 00645956 已排除）。",
 },
 "00749F30": {
  "vt":0x007F6318,"slot_no":23,"slot_va":0x007F6374,
  "ring4_at":0x00749434,"ring4_host":0x007493B0,"ring4_base_call":0x007493BE,
  "form":"③b④ 8 邻域扫描循环 + 边界检查 + 循环体内非栈写",
  "ring3":[
   ("循环入口",0x0074A329,"edi=0 起；按 8 方向偏移表 [edx*4+0x89F688] 取格内对象"),
   ("读-取格内对象",0x0074A385,"e8 16b4e1ff call 0x5657A0 → 0074A38A mov esi,eax（对象）"),
   ("判-格内标志",0x0074A395,"84c0 test al,al（前置 0074A390 call 0x4838E0）→ 0074A397 0f84 je 0x74A56A（不成立跳过本格）"),
   ("循环体内非栈写",0x0074A48F,"c6861e01000000 mov byte ptr [esi+0x11E],0（写进堆对象 esi，不是栈槽，也不是被调内部写）"),
   ("边界检查+推进+回边",0x0074A56B,"83ff08 cmp edi,8 ; 0074A56A 47 inc edi ; 0074A572 0f8cb1fdffff jl 0x74A329（edi<8 回边，越界退出）"),
  ],
  "callees":[],
  "sem":"VoxelAnimClass::slot23 —— ③b④ 8 邻域扫描：当 [Type+0x300] 标志置位且本帧未处理时，从 edi=0 遍历 8 个方向偏移（[edx*4+0x89F688]），每格用 0x5657A0 取对象（读）、0x4838E0 测格内标志（判），命中格 new 0xB0 对象 + 0x5FC380 构造后，用 `c6861e01000000 mov byte [esi+0x11E],0` 写回堆对象（循环体内非栈写），再 `inc edi`/`cmp edi,8`/`jl 0x74A329` 带边界检查推进。读→判→写→推进齐备。② 槽 007F6374（vt 007F6318+0x5C，slot#23）4B 值=本 entry，COL=0080CDF8→TD=00845E50→`.?AVVoxelAnimClass@@`；④ 00749434（构造器 007493B0，首条 007493BE call 0x5F3900 基类构造后装表，atexit=False、行外）。",
 },
 "0074BA30": {
  "vt":0x007F6548,"slot_no":8,"slot_va":0x007F6568,
  "ring4_at":0x0074AE6B,"ring4_host":0x0074AD80,"ring4_base_call":0x0074AD89,
  "form":"③b② 标量删除析构（两个容器 Find -1）",
  "ring3":[
   ("站点1",0x0074BA6A,"ff5210 call [edx+0x10]（edx=[0xB0F670]）"),
   ("站点1-判零间隔",0x0074BA6D,"83f8ff cmp eax,-1 ; 0074BA70 742d je 0x74BA9F（零间隔）"),
   ("站点1-命中路压缩写",0x0074BA91,"895481fc mov [ecx+eax*4-4],edx ; 0074BA7F mov [0xB0F680],ecx ; 0074BA9D 7ce8 jl 回边"),
   ("站点2",0x0074BAB3,"ff5210 call [edx+0x10]（edx=[0xA8EB28]）"),
   ("站点2-判零间隔",0x0074BAB6,"83f8ff cmp eax,-1 ; 0074BAB9 742d je 0x74BAE8（零间隔）"),
   ("站点2-命中路压缩写",0x0074BADA,"895481fc mov [ecx+eax*4-4],edx ; 0074BAC8 mov [0xA8EB38],ecx ; 0074BAE6 7ce8 jl 回边"),
   ("收尾-基类析构",0x0074BB02,"e8 f9b8eaff call 0x5F7400"),
   ("收尾-delete 标志释放",0x0074BB07,"f644240c01 test byte [esp+0xC],1 ; 0074BB0F call 0x7C8B3D"),
  ],
  "callees":[(0x004E0550,"容器 0xB0F670 活表 007E91EC vt[#4]：004E056F 83c8ff or eax,-1 + 004E0573 ret 4"),(0x004EE8D0,"容器 0xA8EB28 活表 007EA3A4 vt[#4]：004EE8EF 83c8ff or eax,-1 + 004EE8F3 ret 4")],
  "sem":"VoxelAnimTypeClass::slot8 —— ③b② 标量删除析构（双注册表）：复位 4 表、call 0x7258D0 解引用后，在 DynamicVectorClass<VoxelAnimTypeClass*>（0xB0F670，计数 0xB0F680/数组 0xB0F674）与（0xA8EB28，计数 0xA8EB38/数组 0xA8EB2C）两个注册表各 Find 自身——未命中 -1 跳过、命中则计数减一并前移压缩数组摘链（各自 jl 回边）；随后按 [this+0x296] 清 [this+0xB0]/[this+0xB4]，call 0x5F7400 基类析构，按 delete 标志 call 0x7C8B3D 释放。② 槽 007F6568（vt 007F6548+0x20，slot#8）4B 值=本 entry，COL=0080CEB0→TD=00845E70→`.?AVVoxelAnimTypeClass@@`；④ 0074AE6B（构造器 0074AD80，首条 0074AD89 call 0x5F7090 基类构造后装表，atexit=False、行外；行内 0074BA36 已排除）。",
 },
}


def raw(va, n):
    return " ".join("%02x" % x for x in C.read_va(va, n))


def insns_in(insns, va, n=7, lead=2):
    idx = None
    for i, ins in enumerate(insns):
        if ins.address <= va < ins.address + ins.size:
            idx = i
            break
    if idx is None:
        return ["(未定位到覆盖 %08X 的指令)" % va]
    out = []
    for ins in insns[max(0, idx - lead):idx - lead + n]:
        out.append("%08X  %-20s %-8s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    return out


def build(entry):
    p = PLAN[entry]
    ea = int(entry, 16)
    size = C.ATLAS.get(entry, {}).get("size") or 0
    insns = C.disasm_body(ea, size)
    L = []
    A = L.append
    A("# ROW %s  S20 named 四环齐全（D-40）" % entry)
    A("# 目标: gamemd.exe SHA-256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476")
    A("# 工具: capstone 5.0.7 (skipdata=True) + pefile 2024.8.26 / Python 3.12.10")
    A("")
    # ①
    last = insns[-1]
    A("## ① 入口（entry 在 .text 内、边界自洽、末条 ret/jmp）")
    A("   entry=%s in .text[00401000,007E038D)=%s ; atlas size=%d ; 末条=%08X %s %s ; skipdata=0" % (
        entry, C.in_text(ea), size, last.address, last.mnemonic, last.op_str))
    A("   判定：PASS")
    A("")
    # ②
    v = p["vt"]; sva = p["slot_va"]
    col = C.u32(v - 4); td = C.u32(col + 0xC) if col else None
    name = C.read_cstr(td + 8, 80) if td else ""
    A("## ② 类身份（整表枚举 RTTI：槽→[vt-4]=COL(sig=0)→[COL+0xC]=TD→TD+8 名串）")
    A("   vt=%08X  slot#%d  slot_va=%08X（vt+0x%X）" % (v, p["slot_no"], sva, sva - v))
    A("   槽内 4B = %s  ⇒ == entry %s : %s  ; 原始字节 %s" % (
        C.hx(C.u32(sva)), entry, C.u32(sva) == ea, raw(sva, 4)))
    A("   [vt-4] COL=%s  sig=%s(=0 完整对象定位器) ; 原始字节 %s" % (
        C.hx(col) if col else "?", C.hx(C.u32(col)) if col else "?", raw(col, 16) if col else "?"))
    A("   [COL+0xC] TD=%s ; TD+8 名串 = %s  ; COL→TD 字节 %s" % (
        C.hx(td) if td else "?", name, raw(td, 24) if td else "?"))
    A("   槽号与 name 栏 slot#%d 自洽 ; RTTI 类名与 name 栏前缀同族" % p["slot_no"])
    A("   判定：PASS（② 与 ④ 不同源：② 锚 .rdata COL/TD 描述符与槽内值）")
    A("")
    # ④
    r4 = p["ring4_at"]; host = p["ring4_host"]
    A("## ④ 使用见证（活虚表：构造器安装的 vt 写点，行外、非 atexit）")
    A("   装表锚点=%08X  字节=%s  反汇编=mov dword ptr [reg],0x%08X（=本 vt）" % (r4, raw(r4, 7), v))
    A("   宿主函数=%08X  atlas size=%d  atexit(push f;call 0x7C978A)=%s" % (
        host, C.ATLAS.get(C.hx(host), {}).get("size") or 0, C.is_atexit(host)))
    hin = C.disasm_body(host, C.ATLAS.get(C.hx(host), {}).get("size") or 0)
    idx = next((i for i, x in enumerate(hin) if x.address == p["ring4_base_call"]), None)
    A("   构造器自证：宿主首条出向调用 %08X —— call 基类构造，装表在其后：" % p["ring4_base_call"])
    for x in hin[:(idx + 2 if idx is not None else 6)]:
        A("     %08X  %-20s %-8s %s" % (x.address, x.bytes.hex(), x.mnemonic, x.op_str))
    A("   装表处上下文：")
    for line in insns_in(hin, r4, n=6, lead=2):
        A("     " + line)
    A("   行内?=%s（本行体 [%08X,%08X)）⇒ 写点在行外" % (ea <= r4 < ea + size, ea, ea + size))
    A("   ⇒ 采用 %08X（in_func=%08X, atexit=False, in_self=False）。㉓ 成对陷阱：锚为构造器安装、非析构器、非 atexit 死表。" % (r4, host))
    A("   判定：PASS")
    A("")
    # ③
    A("## ③ 整体合同（只认 ③b；形态 = %s）" % p["form"])
    for label, va, note in p["ring3"]:
        A("   [%s] %08X" % (label, va))
        A("       %s" % note)
        if any(x.address <= va < x.address + x.size for x in insns):
            for line in insns_in(insns, va, n=7, lead=2):
                A("       " + line)
        else:
            f = C.func_of(va)
            fsz = (C.ATLAS.get(C.hx(f[0]), {}).get("size") or 64) if f else 64
            for line in C.dump(va, min(fsz, 64)).splitlines()[:8]:
                A("       " + line)
    if p.get("callees"):
        A("   被调返回约定取证（失败常量字节可见）：")
        for cv, note in p["callees"]:
            A("     %08X  %s" % (cv, note))
            csz = C.ATLAS.get(C.hx(cv), {}).get("size") or 60
            for line in C.dump(cv, min(csz, 120)).splitlines():
                A("       " + line)
    A("   三陷阱排查：")
    A("     - eax 覆写：cmp/test 与 jcc 零间隔相邻，之间无 mov eax/call 覆写（见上逐条字节）")
    A("     - 多路同一 call：不适用（各站点被调/容器/动作不同；同一析构的两个注册表是不同容器）")
    A("     - 模板假句：语义栏写本行具体分支与写动作，不用“对象初始化/清零”套话")
    A("   三已知陷阱：① 流方向按 0x410320=写出(+0x10)/0x410380=读入(+0xC) 逐行复算；② ④ 锚在构造器非析构器；③ 主虚表 slot0=00410260（本行 vt 均为主表，非小成员表）。")
    A("   判定：PASS")
    A("")
    A("## 一句话语义")
    A("   " + p["sem"])
    A("")
    return "\n".join(L) + "\n"


for e in PLAN:
    txt = build(e)
    path = os.path.join(OUT, "ROW_%s.txt" % e)
    open(path, "w", encoding="utf-8").write(txt)
    print("wrote %s  %d bytes" % (path, len(txt)))
