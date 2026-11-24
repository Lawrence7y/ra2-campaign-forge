# Emit per-row disassembly context snippets around verified anchors, read-only.
import os, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_SLOTS3\EVIDENCE"
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True
data = open(EXE, "rb").read()

def va2off(va):
    rva = va - IB
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    raise ValueError(hex(va))

def disasm(entry, length):
    off = va2off(entry); blob = data[off:off+length]
    ins = []
    for i in md.disasm(blob, entry):
        ins.append((i.address - entry, i.bytes.hex(), (i.mnemonic + " " + i.op_str).strip()))
    return ins

# entry -> (name, subsystem, ③b档位, [(anchor_rel, label), ...])
ROWS = {
 "006F3330": ("TechnoClass::slot185","S05","③b②",[(0xBD,"+0xBD gate"),(0xE0,"+0xBD je landing = 对象选择续行"),(0x478,"-1 return gate"),(0x47D,"-1->0 return")]),
 "006F8DF0": ("TechnoClass::slot241","S05","③b④",[(0x3FC,"loop head"),(0x50B,"+0x50B 扩容尺寸计算"),(0x522,"计数写"),(0x525,"元素写"),(0x552,"+0x552 扩容尺寸计算"),(0x57B,"界判"),(0x595,"回跳")]),
 "006FC0B0": ("TechnoClass::slot240","S05","③b②",[(0x717,"-1哨兵1"),(0x87C,"-1哨兵2"),(0x887,"-1哨兵3"),(0x8AB,"-1哨兵4")]),
 "006FFEC0": ("TechnoClass::slot29","S05","③b②",[(0x1F9,"有界循环"),(0x3D3,"+0x3D3 时间戳-1哨兵"),(0x3D6,"je"),(0x3E6,"落点 test eax,eax / setne bl 谓词")]),
 "0070BF50": ("TechnoClass::slot5","S05","③b②",[(0xC,"helper call"),(0x13,"cmp eax,ebx"),(0x15,"jl 负值返回"),(0x3F,"清字段循环"),(0x2F9,"ret 8 站点")]),
 "00712170": ("TechnoTypeClass::slot25","S05","③b②+③b④",[(0x76C,"写循环头"),(0x7DA,"显式写1"),(0x811,"显式写2"),(0x822,"推进 add edi,0x1c"),(0x826,"界判"),(0xCC2,"-1哨兵样例")]),
 "00716150": ("TechnoTypeClass::slot42","S05","③b④",[(0x5E,"0x7fff哨兵1"),(0x65,"0x7fff哨兵2"),(0x77,"推进"),(0x85,"累加器写"),(0x104,"回跳")]),
 "006D0270": ("MouseClass::slot50","S09","③b④",[(0xE,"循环头 读标志"),(0x16,"je跳过"),(0x2A,"汇合点 dword[esi]=0"),(0x33,"推进"),(0x34,"界判"),(0x3A,"回跳")]),
 "006D04F0": ("MouseClass::slot54","S09","③b①+③b④",[(0x15,"闸1 je尾"),(0x23,"+0x23=mov al,[esi+0x5544]"),(0x29,"+0x29 闸2 je(订正)"),(0xE6,"循环1 call"),(0xE9,"循环1推进"),(0xEC,"循环1界判"),(0x105,"循环2读"),(0x12E,"循环2推进"),(0x131,"循环2界判")]),
 "00653850": ("RadarClass::slot10","S09","③b①",[(0x38,"坐标域闸"),(0x64,"call 0x5bdc80"),(0xAE,"WhatAmI闸"),(0xEA,"写8"),(0xF6,"写9"),(0x109,"写1"),(0x138,"call 0x656cb0"),(0x152,"call 0x6578f0")]),
 "004F4480": ("MouseClass::slot15","S09","③b①",[(0x2F,"setne/sete锁存"),(0x49,"闸1 jne→+0x9B"),(0x5F,"0x6d3d10 arg0"),(0x74,"arg1"),(0x95,"arg2"),(0xBD,"虚调[edx+0x40]"),(0xC0,"旗标清0"),(0xFE,"call 0x55f1e0")]),
 "004A8960": ("TabClass::slot42","S09","③b①",[(0x27,"滚动原点写1"),(0x5D,"call 0x6d5f60"),(0x7A,"释放旧对象"),(0xA4,"分配结果"),(0xDA,"构造0x7bc970"),(0xE8,"写0x8000"),(0x12B,"call 0x410e50")]),
 "006C6680": ("StaticButtonClass::slot33","S09","③b①",[(0xA,"闸1 [esi+0x30]"),(0xF,"free 0x7c8b3d"),(0x31,"分配0x7c8e17"),(0x3C,"test(订正)"),(0x3E,"je(订正)"),(0x42,"拷贝call(订正)"),(0x4E,"虚调[edx+0x48]"),(0x64,"虚调[eax+0x88]")]),
 "004F4320": ("MouseClass::slot9","S09","③b①",[(0x10,"虚调1"),(0x31,"闸[0xa8ef54]"),(0x37,"真域call[edx+0x5c]"),(0x44,"真域虚调[eax+0x38]"),(0x7A,"假域call 0x54f000"),(0x92,"假域call 0x54f050"),(0xB9,"汇合虚调[eax+0x28]")]),
 "006AC210": ("SidebarClass::slot33","S09","③b①",[(0xA,"首闸call 0x640450"),(0x19,"case 0xc8"),(0x72,"call 0x7ca564"),(0x85,"case 0xc9"),(0xAC,"范围[0xcb,0xcf)"),(0xC8,"子支0"),(0x110,"子支3")]),
}
LENS = {k:0x5000 for k in ROWS}

for entry,(name,sub,grade,anchors) in ROWS.items():
    ins = disasm(int(entry,16), LENS[entry])
    idx = {rel:i for i,(rel,b,t) in enumerate(ins)}
    lines = []
    lines.append("# SEMFIX-SLOTS3 EVIDENCE entry=%s name=%s subsystem=%s grade=[已证]" % (entry,name,sub))
    lines.append("目标 gamemd.exe 只读 SHA-256 73201CC0...F67476；capstone 5.0.7(skipdata=True)+pefile 2024.8.26 现场反汇编。")
    lines.append("③b档位=%s；下列锚点均为入口相对偏移 +0xNN，逐条核对实际指令字节。" % grade)
    for rel,label in anchors:
        lines.append("")
        lines.append("## +0x%03X  %s" % (rel,label))
        i = idx.get(rel)
        if i is None:
            lines.append("   [锚点不在反汇编窗口内]"); continue
        lo = max(0,i-2); hi = min(len(ins),i+3)
        for j in range(lo,hi):
            r,b,t = ins[j]
            mark = ">>" if j==i else "  "
            lines.append("  %s +0x%04X  %-20s %s" % (mark,r,b,t))
    p = os.path.join(OUT,"ROW_%s.txt"%entry)
    open(p,"w",encoding="utf-8").write("\n".join(lines)+"\n")
    print("wrote",p,"anchors",len(anchors))
