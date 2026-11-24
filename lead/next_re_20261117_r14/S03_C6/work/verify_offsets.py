"""Verify the cited entry-relative offsets in THREE_B_DETERMINATION.md against bytes.
For each (entry, offset, expected_mnemonic/substring) print what is actually there.
Read-only on exe.
"""
import os, sys, csv
sys.path.insert(0, os.path.dirname(__file__))
import common as C

CLS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv"
ext = {}
for r in csv.DictReader(open(CLS, encoding="utf-8"), delimiter="\t"):
    try: ext[r["entry"]] = (int(r["ext_lo"],16), int(r["ext_hi"],16))
    except Exception: pass

# (entry, [(offset, note), ...])
CHECKS = {
 "00432050": [(0x4F,"cmp eax,1"),(0x56,"je err0xd"),(0x5C,"mov ebx,count"),(0x60,"cmp ebx,edi"),
              (0x69,"loop head mov eax,[esi+0x34]"),(0x71,"sub edi,edx"),(0x73,"cmp ebx,edi"),
              (0x79,"cmp edi,eax"),(0x84,"test cl"),(0x8F,"cmp ecx,eax"),
              (0xA9,"test eax=[esi+0x50]"),(0xBB,"call [vptr+0x28]"),
              (0x125,"call 0x7ca090 memmove"),(0x13D,"sub ebx,edi"),(0x141,"mov [esi+0x28],1"),
              (0x17F,"call 0x431dd0"),(0x1FC,"jne backedge"),(0x212,"call [vptr+0x40] err0xd")],
 "004322A0": [(0x47,"cmp eax,2"),(0x4E,"je err0xd"),(0x58,"cmp ebx,edi"),
              (0x61,"loop head"),(0x6B,"cmp ebx,eax"),(0x76,"test al"),(0x81,"cmp eax,ecx"),
              (0xAD,"call [vptr+0x28]"),(0xBC,"call [vptr+0x24]"),(0xC9,"call [vptr+0x28]"),
              (0x119,"call 0x7ca090 memmove"),(0x122,"mov [esp+0x1c],edx"),(0x139,"mov [esi+0x4c],ecx"),
              (0x142,"mov [esi+0x38],eax"),(0x137,"sub ebx,edi"),(0x1C1,"jne backedge"),(0x1D7,"call [vptr+0x40]")],
 "0047AE10": [(0x16,"test [ebx+0x54]"),(0x26,"test [0x89e410]"),(0x32,"call 0x431f10"),
              (0x49,"loop head"),(0x55,"repne scasb"),(0x68,"rep movsd"),(0x7D,"repne scasb"),
              (0x94,"rep movsd"),(0xA4,"call 0x431e80"),(0xAD,"call 0x431f10"),(0xB4,"test al"),
              (0xB9,"mov ebp,[ebp]"),(0xBB,"jne backedge"),(0xD0,"call [vptr+4]")],
 "0065CDD0": [(0x18,"call [vptr+0x18]"),(0x1D,"jne"),(0x25,"call [vptr+0x1c]"),
              (0x52,"call WriteFile"),(0x5E,"test eax"),(0x58,"GetLastError load"),(0x6F,"call [edi+0x40]"),
              (0x72,"cmp [esi+0x10],-1"),(0x81,"call [vptr+0x18]"),(0xA9,"call SetFilePointer"),(0xAB,"cmp eax,-1")],
 "0065D0D0": [(0x09,"cmp eax,-1"),(0x0C,"jne"),(0x10,"call [vptr+0x18]"),(0x15,"je"),
              (0x1C,"call GetFileSize"),(0x24,"cmp edi,-1"),(0x32,"call GetLastError"),(0x3B,"call [ebx+0x40]"),
              (0x43,"sub eax,[esi+0xc]"),(0x46,"mov [esi+0x10],eax")],
 "0065D190": [(0x05,"call [vptr+0x34]"),(0x0B,"test [esi+0x18]"),(0x0D,"jne"),(0x19,"call [vptr+0x40]"),
              (0x22,"call [vptr+0x14]"),(0x2B,"jne"),(0x35,"call DeleteFileA"),(0x3D,"jne success"),
              (0x47,"call GetLastError"),(0x50,"call [edi+0x40]"),(0x58,"mov eax,1")],
 "0065D240": [(0x09,"cmp [esi+0x14],-1"),(0x0C,"je common_ret"),(0x14,"call GetFileInfoByHandle"),
              (0x1C,"je common_ret"),(0x2C,"call DosDateTimeToFileTime"),(0x34,"je common_ret"),
              (0x49,"call SetFileTime"),(0x4F,"neg"),(0x51,"sbb"),(0x54,"neg"),(0x5C,"xor al,al common_ret")],
}
for e, checks in CHECKS.items():
    lo, hi = ext[e]
    print("=== %s extent %08X..%08X ===" % (e,lo,hi))
    for off, note in checks:
        va = lo + off
        ins = list(C.md().disasm(C.read_bytes(va, 16), va))
        if ins:
            i = ins[0]
            print("  +0x%03X %-8s %-34s ; %-24s [%s]" % (off, i.mnemonic, i.op_str, i.bytes.hex()[:24], note))
        else:
            print("  +0x%03X NO-DECODE [%s]" % (off, note))
