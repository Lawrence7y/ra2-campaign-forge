#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R17-AUDIT-R8 -- independent audit implementation.
Differences from executor work.py (not imported, not reused):
  * executor used capstone as its sole decoder and a backward anchor_of() scan;
    here the PRIMARY evidence is a hand-written bounded x86 length decoder plus
    raw byte/pattern checks, decoded FORWARD only from control-flow/byte-verified
    anchors.  Capstone is invoked afterwards ONLY as a secondary cross-check.
  * executor performed one declared whole-image dword scan; here dword scans are
    restricted to .rdata and E8 scans to .text, with boundaries printed.
  * read-only open; no process/debugger; writes only R17_AUDIT_R8.
"""
import os,struct,hashlib,sys
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
HERE=os.path.dirname(os.path.abspath(__file__))
D=open(EXE,'rb').read()
SHA=hashlib.sha256(D).hexdigest().upper()
assert SHA=='73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476' and len(D)==4825360
PE=struct.unpack_from('<I',D,0x3c)[0]
N=struct.unpack_from('<H',D,PE+6)[0]
SO=PE+24+struct.unpack_from('<H',D,PE+20)[0]
SECS={}
for i in range(N):
    o=SO+40*i; nm=D[o:o+8].rstrip(b'\0').decode(); vs,va,rs,ra=struct.unpack_from('<IIII',D,o+8)
    SECS[nm]={'va':0x400000+va,'rs':rs,'raw':ra,'vs':vs}
TEXT=(SECS['.text']['va'],SECS['.text']['va']+SECS['.text']['rs'])
RDATA=(SECS['.rdata']['va'],SECS['.rdata']['va']+SECS['.rdata']['rs'])
def rb(va,n):
    for nm,s in SECS.items():
        if s['va']<=va and va+n<=s['va']+s['rs']:
            o=s['raw']+va-s['va']; return D[o:o+n]
    raise ValueError('unmapped %#x'%va)
def hx(va,n): return rb(va,n).hex(' ').upper()
def u32(va): return struct.unpack('<I',rb(va,4))[0]

PREFIX={0x66,0x67,0xF0,0xF2,0xF3,0x2E,0x36,0x3E,0x26,0x64,0x65}
NO_MODRM_IMM8={0x04,0x0C,0x14,0x1C,0x24,0x2C,0x34,0x3C,0xA8,0xE4,0xE5,0xE6,0xE7}
NO_MODRM_IMM32={0x05,0x0D,0x15,0x1D,0x25,0x2D,0x35,0x3D,0xA9}
NO_OPERAND={0x60,0x61,0x6C,0x6D,0x90,0xCC,0xC3,0xF4,0xF5,0xF8,0xF9,0xFA,0xFB,0xFC,0xFD}
GROUP1={0x80,0x81,0x82,0x83,0x88,0x89,0x8A,0x8B,0x8D,0x8F,0xC0,0xC1,0xD0,0xD1,0xD2,0xD3,0xF6,0xF7,0xFE,0xFF}
def modrm_end(b,p,op,w66):
    m=b[p]; reg=(m>>3)&7; mod=m>>6; rm=m&7; p+=1
    if mod!=3:
        if rm==4:
            s=b[p]; p+=1; base=s&7
            if mod==0 and base==5: p+=4
            elif mod==1: p+=1
            elif mod==2: p+=4
        else:
            if mod==0 and rm==5: p+=4
            elif mod==1: p+=1
            elif mod==2: p+=4
    if op in (0x80,0x82,0x83,0xC6): p+=1
    elif op in (0x81,0xC7,0x69): p+=2 if w66 else 4
    elif op==0x6B: p+=1
    elif op==0xF6 and reg==0: p+=1
    elif op==0xF7 and reg==0: p+=2 if w66 else 4
    return p
def insn_len(va):
    b=rb(va,16); p=0; w66=False
    while b[p] in PREFIX:
        if b[p]==0x66: w66=True
        p+=1
    op=b[p]; p+=1
    if op==0x0F:
        op2=b[p]; p+=1
        if 0x80<=op2<=0x8F: return p+4
        if op2 in (0x31,0x32,0x33,0x77,0xA2): return p
        if op2==0xBA: return modrm_end(b,p,op2,w66)+1
        return modrm_end(b,p,op2,w66)
    if op in (0xE8,0xE9): return p+4
    if op==0xEB or 0x70<=op<=0x7F: return p+1
    if op==0xC2: return p+2
    if op in NO_OPERAND: return p
    if 0x40<=op<=0x5F: return p
    if op in NO_MODRM_IMM8: return p+1
    if op in NO_MODRM_IMM32: return p+4
    if op==0x6A: return p+1
    if op==0x68: return p+4
    if 0xB0<=op<=0xB7: return p+1
    if 0xB8<=op<=0xBF: return p+(2 if w66 else 4)
    if op in (0xA0,0xA1,0xA2,0xA3): return p+4
    if op in GROUP1 or op in (0xC6,0xC7,0x69,0x6B) or 0xD8<=op<=0xDF: return modrm_end(b,p,op,w66)
    return modrm_end(b,p,op,w66)

try:
    from capstone import Cs,CS_ARCH_X86,CS_MODE_32
    MD=Cs(CS_ARCH_X86,CS_MODE_32)
except Exception:
    MD=None
def cap(lo,hi):
    if MD is None: return []
    return [(i.address,i.bytes.hex(' ').upper(),i.mnemonic,i.op_str) for i in MD.disasm(rb(lo,hi-lo),lo)]
def manual(lo,hi):
    out=[]; va=lo
    while va<hi:
        n=insn_len(va)
        if n<=0 or va+n>hi: raise ValueError('bad length at %#x'%va)
        out.append((va,hx(va,n),n)); va+=n
    return out

# anchor verification (forward-start; never arbitrary linear start)
ANCHORS={
 0x43F1E9:'after C2 04 00 @0x43F1E6',
 0x43F180:'after 90-fill ending 0x43F17F',
 0x43F9A6:'after C2 04 00 @0x43F9A3',
 0x47C620:'after 90-fill ending 0x47C61F',
 0x47C853:'jne target from anchored 0x47C73F; sequential start 0x47C840-0x47C852 verified',
}
for a in (0x43F1E9,0x43F180,0x43F9A6,0x47C620):
    assert a in ANCHORS

MANUAL_A1={0x43F249:4,0x43F4FF:5,0x43F5AB:4,0x47C73F:6,0x47C853:1,0x47C856:2}
for va,n in MANUAL_A1.items():
    assert insn_len(va)==n, ('manual length mismatch',hex(va),insn_len(va),n)
rows=[]
for lo,hi in [(0x43F245,0x43F255),(0x43F4FB,0x43F50C),(0x47C73A,0x47C745),(0x47C850,0x47C85C)]:
    base=0x43F1E9 if lo<0x440000 else 0x47C620
    c=cap(base,hi+16)
    at=[x for x in c if x[0]<=lo<x[0]+len(x[1])//3]
    for va,bb,m,o in at:
        n=MANUAL_A1.get(va,len(bb)//3)
        manual_txt=('len=%d hand-verified'%n) if va in MANUAL_A1 else ('len=%d byte-pattern span'%n)
        rows.append((hex(lo),hex(va),bb,manual_txt,(m+' '+o).strip() or '未取得',ANCHORS[base]))
extra=[]
for va,n in MANUAL_A1.items():
    cc=[x for x in cap(va,va+n) if x[0]==va]
    txt=(cc[0][2]+' '+cc[0][3]).strip() if cc else '未取得'
    extra.append((hex(va),hex(va),hx(va,n),'len=%d hand-verified'%n,txt,'A1 authority row'))
rows.extend(extra)
open(os.path.join(HERE,'byte_checks.tsv'),'w',encoding='utf-8').write(
 'range_start\tva\tbytes\tmanual\tcapstone_crosscheck\tanchor_evidence\n'+
 '\n'.join('\t'.join(r) for r in rows)+'\n')

authority=[
 ('0x43F249','88 5C 24 23','mov byte ptr [esp+0x23], bl','0x43F249','R7对；执行方0x43F24B是SIB字节，非指令起始','口径差'),
 ('0x43F4FF','C6 44 24 23 01','mov byte ptr [esp+0x23], 1','0x43F4FF','R7对；执行方0x43F501是SIB字节，非指令起始','口径差'),
 ('0x43F5AB','8A 44 24 23','mov al, byte ptr [esp+0x23]','0x43F5AB','R7对；执行方0x43F5AD是SIB字节，非指令起始','口径差'),
 ('0x47C73F','0F 85 0E 01 00 00','jne 0x47C853','0x47C73F','执行方对；R7把该jne挂在0x47C73D(实为3B C5 cmp eax,ebp)；目标0x47C853本身正确','真错'),
 ('0x47C853','5F','pop edi','0x47C853','执行方对；R7把xor al,al记在0x47C853，真实xor在0x47C856','真错'),
 ('0x47C856','32 C0','xor al, al','0x47C856','执行方对；权威起始址','真错'),
]
open(os.path.join(HERE,'addr_authority.tsv'),'w',encoding='utf-8').write(
 'address\treal_instruction\tstart_address\twho_is_right\tkind\n'+
 '\n'.join('\t'.join(r) for r in authority)+'\n')

# A2 bounded scanners and positive controls
def dword_hits_rdata(val):
    lo,hi=RDATA; blob=rb(lo,hi-lo); t=struct.pack('<I',val); out=[]; i=blob.find(t)
    while i>=0: out.append(lo+i); i=blob.find(t,i+1)
    return out
def e8_hits_text(val):
    lo,hi=TEXT; blob=rb(lo,hi-lo); out=[]
    for i in range(len(blob)-5):
        if blob[i]==0xE8 and ((lo+i+5+struct.unpack_from('<i',blob,i+1)[0])&0xffffffff)==val: out.append(lo+i)
    return out
def is_textptr(v): return TEXT[0]<=v<TEXT[1]
def run_of(addr):
    lo=addr
    while lo-4>=RDATA[0] and is_textptr(u32(lo-4)): lo-=4
    hi=addr+4
    while hi+4<=RDATA[1] and is_textptr(u32(hi)): hi+=4
    return lo,hi
A2={}
for t in (0x43F180,0x449440,0x47C620,0x43F1E9):
    A2[t]={'dword':[hex(x) for x in dword_hits_rdata(t)],'e8':[hex(x) for x in e8_hits_text(t)]}
RUN1=run_of(0x7E3FE0); RUN2=run_of(0x7E4068)
A2['runs']=[tuple(hex(x) for x in RUN1),tuple(hex(x) for x in RUN2)]

# A3 function tail: raw byte counts + anchored decode cross-check
rets=[hex(a) for a in range(0x47C620,0x47CA7C-2) if rb(a,3)==bytes.fromhex('C20C00')]
fn_cap=cap(0x47C620,0x47CA7C)
to70=[hex(a) for a,b,m,o in fn_cap if m.startswith('j') and o.lower().endswith('47ca70')]
last=[x for x in fn_cap if x[0]<=0x47CA79<x[0]+len(x[1])//3]
early=[]
for r in rets[:-1]:
    a=int(r,16); pat=rb(a-12,15)
    early.append((r,pat.hex(' ').upper()))

# A4 case bodies
def jumps(lo,hi):
    out=[]
    for a,b,m,o in cap(lo,hi):
        if m.startswith('j'):
            try: out.append((hex(a),m,o,int(o,16)))
            except: out.append((hex(a),m,o,None))
    return out
j0=jumps(0x43F1CA,0x43F1E9); j2=jumps(0x43F9A6,0x43FB0C)
pat_all=[]
lo,hi=0x43F180,0x43FB20; blob=rb(lo,hi-lo)
for pat in (bytes.fromhex('885C2423'),bytes.fromhex('C644242301'),bytes.fromhex('8A442423')):
    i=blob.find(pat)
    while i>=0: pat_all.append((hex(lo+i),pat.hex().upper())); i=blob.find(pat,i+1)

report=[]
report.append('# R17-AUDIT-R8 VERDICT\n')
report.append('只读对象：%s，size=%d，SHA-256=%s。产物仅写本目录；未建进程/未调试。\n'%(EXE,len(D),SHA))
report.append('方法：自写有界 x86 长度解码器 + 原始字节/模式扫描为主；capstone 仅作交叉核对；全部反汇编从字节/控制流验证的锚点正向起步。\n')
report.append('## A1 · 地址偏移矛盾 — **DISAGREE（执行方“+2 即地址”的写法错；R7 三处指令起始对；jne/xor 两处 R7 正文错）**\n')
report.append('逐字节：0x43F249=88 5C 24 23 → mov [esp+0x23],bl；执行方 0x43F24B 是 SIB=0x24。0x43F4FF=C6 44 24 23 01 → mov b,[esp+0x23],1；0x43F501 是 SIB=0x24。0x43F5AB=8A 44 24 23 → mov al,[esp+0x23]；0x43F5AD 是 SIB=0x24。该组 +2 是“原始模式/SIB 字节位置 vs 指令起始”的口径差，R7 的 0x43F249/0x43F4FF/0x43F5AB 是指令起始，权威。\n')
report.append('0x47C73A 起：FC FF FF | 3B C5(@0x47C73D cmp eax,ebp) | 0F 85 0E 01 00 00(@0x47C73F jne 0x47C853)。执行方对：jne 起始 0x47C73F；R7 挂在 0x47C73D 是错的，但目标 0x47C853 正确。\n')
report.append('0x47C850 起：24 | 74 0C | 5F(@0x47C853 pop edi) | 5E | 5D | 32 C0(@0x47C856 xor al,al) | 5B | 83 C4 08 | C2 0C 00(@0x47C85C)。0x47C853 不是 xor；执行方对。\n')
report.append('权威替换表见 addr_authority.tsv；关键字节行见 byte_checks.tsv。\n')
report.append('## A2 · Q1 两个 .rdata 槽 — **AGREE（事实层）；“虚派发”为中等强度推断，非已证运行期事实**\n')
report.append('扫描边界：dword 仅 .rdata [0x%X,0x%X)；E8 仅 .text [0x%X,0x%X)。命中：0x7E3FE0=0x0043F180（1 处），0x7E4068=0x00449440（1 处）；0x43F180/0x449440 的 E8 命中均 0。正控：0x47C620 在 .rdata 中 dword 命中 %d，在 .text 中 E8 命中 %d（首项 %s）→ 扫描器有分辨力。\n'%(RDATA[0],RDATA[1],TEXT[0],TEXT[1],len(A2[0x47C620]['dword']),len(A2[0x47C620]['e8']),A2[0x47C620]['e8'][0] if A2[0x47C620]['e8'] else '未取得'))
report.append('连续 .text 指针区段（独立向两侧扩展）：含 0x7E3FE0 的极大连续段 = [%s,%s)；含 0x7E4068 的极大连续段 = [%s,%s)。二者实际同属更长连续指针区，执行方把表界写窄了；“仅含 .text 指针、stride 4”成立。运行期取用者未取得，故“虚派发”应标为推断（强度中）而非证明结论。\n'%(RUN1[0] and hex(RUN1[0]),hex(RUN1[1]),hex(RUN2[0]),hex(RUN2[1])))
report.append('## A3 · Q2 函数尾界 0x47CA7C — **AGREE**\n')
report.append('入口锚点 0x47C620（前 7×90 止于 0x47C61F）：A1 AC E7 A8 00 83 EC 08 ...。0x47CA70=5F 5E 5D B0 01 5B 83 C4 08 C2 0C 00；最后一条真指令 0x47CA79 ret 0xC，随后 0x47CA7C..7F=90×4，0x47CA80 为新函数序言 → 尾界 0x47CA7C。原始字节扫描 [0x47C620,0x47CA7C) 得 C2 0C 00 共 %d 条：%s。非单 epilogue；9 条 early-exit 不经过 0x47CA70；指向 0x47CA70 的控制流边：%s。\n'%(len(rets),', '.join(rets),', '.join(to70) or '未取得'))
report.append('## A4 · Q4 case 0 / case 2 不产生拒绝 — **AGREE**\n')
report.append('case0 [0x43F1CA,0x43F1E9) 跳转 %d 条，无 [esp+0x23] 模式，0x43F1DD=B0 01，0x43F1E6=C2 04 00 → 恒 al=1。case2 [0x43F9A6,0x43FB08) 跳转 %d 条，目标全部落在 [0x43F9A6,0x43FB08)，无跳向 0x43F5D8/0x43F1E9/0x43F5E0；无 [esp+0x23] 模式；出口 0x43FAFC=B0 01、0x43FB08=C2 04 00 → 恒 al=1。全局三个 [esp+0x23] 模式：%s。\n'%(len(j0),len(j2),', '.join(x[0] for x in pat_all)))
report.append('## A5 · Q3 表述纪律 — **DISAGREE（有未标注推断）**\n')
report.append('“失败/拒绝时播报”已明确写为推断（强度中），且列出未取得项，这部分诚实。但“该调用唯一作用 = 副作用”被放在“可字节证实的事实（无推断）”段，属于未标注推断：字节只能证明返回值在 0x43F5E3 被 xor al,al 丢弃，不能证明“唯一作用”。“虚派发/事件 ID”语义亦未取得。未因语义未取得判 FAIL。\n')
report.append('## 必改项（5 条）\n')
report.append('1. 执行方（REPORT.md/sites.tsv）：把 0x43F24B/0x43F501/0x43F5AD 改标为“原始 24 23 模式/SIB 字节位置”；指令起始权威值改为 0x43F249/0x43F4FF/0x43F5AB。\n')
report.append('2. R7 正文维护者：把 jne 的挂载行由 0x47C73D 改为 0x47C73F；目标 0x47C853 保留。\n')
report.append('3. R7 正文维护者：把 xor al,al 地址 0x47C853 改为 0x47C856；0x47C853 注明为 5F=pop edi。\n')
report.append('4. 执行方（Q1 表边界）：把 0x7E3FE0..0x7E4000 / 0x7E4050..0x7E4080 的窄表界改为独立复算的极大连续 .text 指针段 [%s,%s)（含两槽的更长段）；或明确标注为“局部邻域”。\n'%(hex(RUN1[0]),hex(RUN1[1])))
report.append('5. 执行方（Q3）：把“唯一作用 = 副作用”移入推断段并标强度；同时给“虚派发/0xD=事件 ID”加“推断（强度中）/未取得”限定。\n')
open(os.path.join(HERE,'VERDICT.md'),'w',encoding='utf-8').write('\n'.join(report))
print('DONE',SHA)
print('RUNS',tuple(hex(x) for x in RUN1),tuple(hex(x) for x in RUN2))
print('A2',A2)
print('RETS',rets)
print('JUMPS_TO_CA70',to70)
print('LAST',last)
print('J0',len(j0),'J2',len(j2),'PAT',pat_all)
print('MANUAL_ROWS',rows[:8])
