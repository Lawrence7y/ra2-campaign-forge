#!/usr/bin/env python3
# SEMFIX-SLOTS2 anchor verification.
# Reads ra2youli\gamemd.exe READ-ONLY, disassembles each target function with
# capstone from its true entry, and prints entry-relative offsets around the
# audited ③b anchors so they can be compared with the card claims.
import os, sys, hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SKIPDATA

TARGET = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUTDIR = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_SLOTS2\EVIDENCE"
IB = 0x400000

# entry -> (label, [ (anchor_off, note) ], decode_len)
ROWS = {
    "0047AE10": ("S03 CDFileClass::slot2  ③b④ CD路径链循环",
        [(0x16,"前置闸 test [ebx+0x54]"),(0x21,"全局路径表"),(0x55,"repne scasb strlen"),
         (0x68,"rep movsd 拼路径写缓冲"),(0x94,"rep movsd 追加文件名"),(0xA4,"call 设全名"),
         (0xAD,"call is-open 可证伪"),(0xB4,"jne 成功"),(0xBB,"回边"),(0xC7,"审计更正:链尾恢复原名")], 0x120),
    "0065CDD0": ("S03 RawFileClass::slot12  ③b②① WriteFile/GetLastError",
        [(0x18,"is-open"),(0x52,"call WriteFile [7E11A0]"),(0x58,"mov ebx,[7E1200] GetLastError"),
         (0x60,"jne 成功"),(0x6A,"call ebx"),(0x6F,"call [edi+0x40] 虚报错"),(0x72,"cmp [esi+0x10],-1"),
         (0x81,"is-open"),(0x96,"push 9 错误码"),(0xA9,"call edi SetFilePointer"),(0xAB,"cmp eax,-1")], 0x120),
    "0065D0D0": ("S03 RawFileClass::slot11  ③b② GetFileSize -1",
        [(0x06,"mov eax,[esi+0x10] 缓存"),(0x09,"cmp eax,-1"),(0x10,"is-open"),(0x1C,"call GetFileSize [7E1120]"),
         (0x24,"cmp edi,-1"),(0x27,"jne"),(0x32,"call GetLastError [7E1200]"),(0x3B,"call [ebx+0x40] 虚报错"),
         (0x43,"sub eax,ecx"),(0x46,"mov [esi+0x10],eax 写回缓存")], 0x80),
    "0065D190": ("S03 CDFileClass::slot4(disk)/RawFileClass::slot4  ③b②(①不达由②兜底) DeleteFile",
        [(0x05,"call [vptr+0x34] flush"),(0x0D,"jne"),(0x15,"push 2 错误码"),(0x19,"call [vptr+0x40] 虚报错"),
         (0x20,"mov eax,[esi]"),(0x29,"test al"),(0x2B,"jne"),(0x35,"call DeleteFileA [7E10E0]"),
         (0x3D,"jne 成功返回1"),(0x47,"call GetLastError"),(0x50,"call [edi+0x40] 虚报错")], 0x70),

    "004D82B0": ("S10 FootClass::slot289  ③b④ 数组删除左移循环",
        [(0x104,"mov ecx,[esi+0x58c] Items"),(0x10A,"inc eax"),(0x10B,"mov edx,[ecx+eax*4]"),
         (0x10E,"mov [ecx+eax*4-4],edx 写"),(0x118,"cmp eax,[esi+0x598] count"),(0x11A,"jl 回边")], 0x140),
    "004D5690": ("S10 AircraftClass::slot335(disk)/FootClass  ③b④ 数组删除左移循环",
        [(0x3F9,"mov ecx,[ebx+0x58c]"),(0x3FF,"inc eax"),(0x400,"mov edx,[ecx+eax*4]"),
         (0x403,"mov [ecx+eax*4-4],edx 写"),(0x40D,"cmp eax,[ebx+0x598]"),(0x40F,"jl 回边")], 0x430),
    "004DB260": ("S10 AircraftClass::slot53(disk)/FootClass  ③b④ 8邻格overlay写-1循环",
        [(0x3D,"mov dx,word[eax*4+..]"),(0x72,"call GetCellAt"),(0x77,"mov dl,[eax+0x122]"),
         (0x7D,"dec dl"),(0x7F,"inc esi"),(0x80,"cmp esi,8"),(0x83,"mov [eax+0x122],dl 写"),(0x89,"jl 回边")], 0xA0),
    "00702D40": ("S10 AircraftClass::slot56(disk)/TechnoClass  ③b① 5路跳表",
        [(0x2D8,"cmp eax,0xe / ja 默认"),(0x2E8,"审计更正: mov cl,[eax+0x703214] (卡写+0x2EE)"),
         (0x2EE,"jmp [ecx*4+表]"),(0x2F0,"跳表数据/目标")], 0x320),
    "00706640": ("S10 AircraftClass::slot273(disk)/TechnoClass  ③b① 4路跳表+2循环",
        [(0x10,"call [eax+0x68] / dec eax"),(0x1A,"cmp eax,4 / ja 默认"),(0x24,"jmp [eax*4+表]"),
         (0x436,"循环1 写"),(0x50C,"循环2 写")], 0x540),
    "00708C30": ("S10 AircraftClass::slot174(disk)/TechnoClass  ③b① 5路跳表",
        [(0x0C,"dec eax"),(0x0E,"cmp eax,4 / ja 默认"),(0x1E,"jmp [eax*4+0x708d54]"),
         (0x20,"跳表数据/目标")], 0x60),
    "004D94B0": ("S10 FootClass::slot288  ③b② HRESULT返回约定",
        [(0xCC,"call 0x45aea0"),(0xD1,"cmp eax,ebx / jge 放行"),(0xD5,"cmp eax,0x80004002 E_NOINTERFACE"),
         (0xDA,"je 放行"),(0xDC,"push eax"),(0xDD,"call 0x7dc720 断言失败")], 0xF0),
}

def main():
    h = hashlib.sha256(open(TARGET,"rb").read()).hexdigest().upper()
    print("TARGET SHA256:", h)
    assert h.startswith("73201CC0") and h.endswith("F67476"), "hash mismatch!"
    pe = pefile.PE(TARGET)
    assert pe.OPTIONAL_HEADER.ImageBase == IB
    data = open(TARGET,"rb").read()
    md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True
    os.makedirs(OUTDIR, exist_ok=True)
    summary=[]
    for entry,(label,anchors,n) in ROWS.items():
        va=int(entry,16); rva=va-IB
        off=None
        for s in pe.sections:
            vs=max(s.Misc_VirtualSize,s.SizeOfRawData)
            if s.VirtualAddress <= rva < s.VirtualAddress+vs:
                off=s.PointerToRawData+(rva-s.VirtualAddress); break
        assert off is not None, entry
        code=data[off:off+n]
        insns=list(md.disasm(code,va))
        by_off={}
        for i in insns:
            by_off[i.address-va]=i
        lines=[]
        lines.append("=== %s  %s"%(entry,label))
        lines.append("VA=0x%X RVA=0x%X file_off=0x%X decode_len=0x%X insns=%d"%(va,rva,off,n,len(insns)))
        lines.append("TARGET SHA256: "+h)
        lines.append("")
        for aoff,note in anchors:
            # find nearest decoded instruction at or just before aoff
            cand=[o for o in by_off if o<=aoff]
            o=max(cand) if cand else min(by_off) if by_off else 0
            i=by_off.get(o)
            if i:
                exact = "==" if o==aoff else "(+0x%X实际起于+0x%X)"%(aoff,o)
                lines.append("  锚 +0x%X %-14s %-8s %-40s ; %s"%(aoff,exact,i.mnemonic,i.op_str,note))
            else:
                lines.append("  锚 +0x%X  <解码缺失>  ; %s"%(aoff,note))
        lines.append("")
        lines.append("--- 全量线性解码（入口相对偏移 指令）---")
        for i in insns:
            lines.append("  +0x%04X  %-8s %s"%(i.address-va,i.mnemonic,i.op_str))
        txt="\n".join(lines)+"\n"
        fn=os.path.join(OUTDIR,"ANCHOR_"+entry+".txt")
        open(fn,"w",encoding="utf-8").write(txt)
        # compact summary: anchor -> actual mnemonic at exact offset
        hits=0
        for aoff,note in anchors:
            i=by_off.get(aoff)
            hits+= 1 if i else 0
        summary.append("%s\t%d/%d anchors exact\t%s"%(entry,hits,len(anchors),label))
    open(os.path.join(OUTDIR,"ANCHOR_SUMMARY.txt"),"w",encoding="utf-8").write("\n".join(summary)+"\n")
    print("\n".join(summary))

if __name__=="__main__":
    main()
