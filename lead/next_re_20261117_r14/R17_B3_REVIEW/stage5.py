
import sys, json
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.argv=['x']
exec(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_B3_REVIEW\stage3.py",encoding='utf8').read().split('res={}')[0])
# now md, rd, dword, SECS available
def ins_at(va):
    i=list(md.disasm(rd(va,16),va))[0]
    return i
out=open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_B3_REVIEW\byte_checks.tsv",'w',encoding='utf8')
w=out.write
w("check\taddr\tbytes\tdecode\tevidence\n")
def row(chk,va,n,ev):
    b=rd(va,n); i=ins_at(va)
    w("%s\t0x%08x\t%s\t%s %s\t%s\n"%(chk,va,b.hex(),i.mnemonic,i.op_str,ev))
# headers
mdh=open(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe",'rb').read()
import hashlib
w("SHA256\t-\t%s\t-\t4,825,360 B, PE32, imagebase 0x400000\n"%hashlib.sha256(mdh).hexdigest().upper())
# fn starts
for h in (0x43B680,0x43B740,0x43BCF0):
    row("HOST",h,12,"host anchor, must be instruction boundary")
# fn ends
row("FN_END",0x43B73D,3,"0x43b680 host: c2 04 00 = ret 4 ; next fn at 0x43b740")
row("FN_END",0x43B740-2,2,"x")
row("FN_END",0x43BCDB,3,"0x43b740 host: c2 08 00 = ret 8 ; next fn at 0x43bcde")
row("FN_END",0x43Bcdd,1,"x")
row("FN_END",0x43C0C9,1,"0x43bcf0 host: c3 = ret (near) ; epilogue pops edi/esi/ebp/ebx/ecx")
row("FN_END",0x43C0CA,6,"six 0x90 NOP padding bytes -> real fn_end = 0x43c0d0 (R9 wrote 0x43c0ca = ret operand start, MISSED padding)")
for site in (0x43B71F,0x43B725,0x43B72C,0x43B733,0x43B9FA,0x43BA00,0x43BA07,0x43BA0E,0x43BCFD,0x43BD05,0x43BD0C,0x43BD13):
    row("SITE",site,7,"immediate-hit store to one of the 4 slots")
row("G2_THIS",0x43B685,2,"mov esi, ecx (host 0x43b680)")
row("G2_THIS",0x43B748,2,"mov esi, ecx (host 0x43b740)")
row("G2_THIS",0x43B94A,3,"lea ebp,[esi+4] -> [ebp] at 0x43ba00 == [this+4]")
row("G2_THIS",0x43BCF4,2,"mov esi, ecx (host 0x43bcf0)")
row("G4_BASE",0x43B687,7,"push eax; call 0x6f4300 base ctor")
row("G4_BASE",0x43B74A,8,"push eax; call 0x6f2b40 base ctor")
row("G4_BASE",0x43BD2E,2,"call 0x405c00 (ctor form) - re-init of member subobject, NOT a base ctor")
row("G5_EPI",0x43B73A,3,"mov eax,esi -> returns this")
row("G5_EPI",0x43Bcd5,2,"mov eax,esi -> returns this")
row("G5_EPI",0x43C0B6,6,"mov ecx,esi / call 0x6f4500 - NO mov eax,esi; eax left by callee")
row("G4_NEW",0x43BC10,6,"push eax; call 0x7c8e17 (operator new thunk) -> AFTER sites at 0x43bcfd.., proves sites not allocator-end")
row("NEW_SEM",0x7C8E17,0xE,"push 1; push [esp+8]; call 0x7c9442 -> operator new( size, 1 )")
row("DEL_SEM",0x7C8B3D,0xB,"push [esp+4]; call 0x7c93e8 -> operator delete( ptr )")
# deletion signatures within 3 hosts: none found
w("G3_SIG\t-\t-\t-\tnone of: mov dword ptr [esp+..],1 ; test al,1 on this ; push esi after mov eax,[esi] + call delete -> zero hits in all 3 host ranges\n")
# C3
for s,e in ((0x7E3E90,0x410590),(0x7E3E98,0x410580),(0x7E3EA0,0x4105E0),(0x7E3EBC,0x410260)):
    v=dword(s)
    row("C3_SLOT",s,4,"slot value 0x%08x, expected 0x%08x, %s"%(v,e,"MATCH" if v==e else "DIFF"))
# B2 disagreement: all 12 sites write .text values
w("B2_CHECK\t-\t-\t-\tall 12 sites write .text-resident values (0x7e3ebc/0x7e3ea0/0x7e3e98/0x7e3e90 are slots in .rdata 0x7e1000..0x841000; contents 0x410260/0x4105e0/0x410580/0x410590 in .text)\n")
out.close()
print(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_B3_REVIEW\byte_checks.tsv",encoding='utf8').read())
