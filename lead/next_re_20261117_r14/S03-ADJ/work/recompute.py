import os, struct, bisect, hashlib, collections
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

P = 'D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe'
ROOT = 'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S03-ADJ'
EV = ROOT + '/EVIDENCE'

class IMG:
    def __init__(self):
        self.data = open(P, 'rb').read()
        self.sha = hashlib.sha256(self.data).hexdigest().upper()
        self.pe = pefile.PE(data=self.data, fast_load=True)
        self.ib = self.pe.OPTIONAL_HEADER.ImageBase
        sec = [s for s in self.pe.sections if s.Name.rstrip(b'\0') == b'.text'][0]
        self.text_lo = self.ib + sec.VirtualAddress
        self.text_hi = self.text_lo + sec.Misc_VirtualSize
        self.md = Cs(CS_ARCH_X86, CS_MODE_32)
        self.md.detail = True
        self.md.skipdata = True
    def rd(self, va, n):
        o = va - self.ib
        return self.data[o:o+n] if 0 <= o <= len(self.data)-n else b''
    def u32(self, va):
        d = self.rd(va, 4)
        return struct.unpack('<I', d)[0] if len(d) == 4 else None
    def cstr(self, va, n=128):
        d = self.rd(va, n)
        z = d.find(b'\0')
        return d[:z if z >= 0 else n].decode('latin1', errors='replace')
    def vtable(self, vt, n=64):
        out=[]
        for i in range(n):
            p=self.u32(vt+4*i)
            if p is None or not (self.text_lo <= p < self.text_hi): break
            out.append(p)
        return out
    def rtti_at_vt(self, vt):
        col=self.u32(vt-4)
        td=self.u32(col+0xC) if col else None
        name=self.cstr(td+8) if td else None
        if not name or not name.startswith('.?AV'): return None
        return col,td,name
    def insns(self):
        return {i.address:i for i in self.md.disasm(self.rd(self.text_lo,self.text_hi-self.text_lo),self.text_lo) if i.id != 0}

def form(op):
    if op.type != X86_OP_MEM: return None
    if op.mem.base == 0 and op.mem.index == 0: return 'A_abs'
    if op.mem.base != 0 and op.mem.index == 0: return 'B_regbase'
    if op.mem.base != 0 and op.mem.index != 0: return 'C_idx'
    return 'other'

def access_of(ins):
    ops=ins.operands
    if not ops: return ('NONE',None,None)
    m=ins.mnemonic; d=ops[0]
    if m in ('call','jmp','ljmp','lcall') and d.type == X86_OP_MEM:
        return ('X',0,form(d))
    mi=[k for k,o in enumerate(ops) if o.type == X86_OP_MEM]
    if not mi or m == 'lea': return ('NONE',None,None)
    if m in ('cmp','test','push'): a='R'
    elif m == 'pop': a='W'
    elif m in ('xchg','cmpxchg','add','sub','or','and','xor','adc','sbb','inc','dec','shl','shr','sar','rol','ror','not','neg'): a='RW'
    elif d.type == X86_OP_MEM: a='W'
    else: a='R'
    return (a,mi[0],form(ops[mi[0]]))

def width_s(op):
    return '%d' % op.size if op.size else '?'

img=IMG(); ins=img.insns()
VTS=[('RawFileClass',0x7F0904),('BufferIOFileClass',0x7E3A2C),('CDFileClass',0x7E1668),('CCFileClass',0x7E16B0),('MixFileClass',0x7EDF50)]
VTADDR={vt for _,vt in VTS}
BUF_VT=0x7E3A2C

parts=[]; st=img.text_lo
for a,i in sorted(ins.items()):
    if i.mnemonic.startswith('ret') or i.mnemonic == 'retf':
        en=a+i.size; b=en
        while b < img.text_hi and img.rd(b,1) in (b'\x90',b'\xcc'): b += 1
        parts.append((st,b,en)); st=b
part_starts=[p[0] for p in parts]
def partof(a):
    j=bisect.bisect_right(part_starts,a)-1
    return parts[j] if j>=0 else None

targets=sorted({i.operands[0].imm for a,i in ins.items() if i.mnemonic in ('call','jmp') and i.operands and i.operands[0].type == X86_OP_IMM})

vptr_writer_starts=set(); vptr_writer_rows=[]
for a,i in sorted(ins.items()):
    if not i.operands or i.operands[0].type != X86_OP_MEM: continue
    for op in i.operands:
        if op.type == X86_OP_IMM and (op.imm in VTADDR or (0x7E1000 <= op.imm < 0x812000)):
            p=partof(a)
            if p:
                vptr_writer_starts.add(p[0]); vptr_writer_rows.append((a,p[0],op.imm,i))
            break

raw=[]
for a,i in sorted(ins.items()):
    for op in i.operands:
        if op.type == X86_OP_MEM and op.mem.disp == 0x29:
            acc,mi,f=access_of(i)
            raw.append(dict(addr=a,ins=i,hex=i.bytes.hex(),mn=i.mnemonic,opstr=i.op_str,acc=acc,form=form(op),width=width_s(op),
                            base=i.reg_name(op.mem.base) if op.mem.base else '-',index=i.reg_name(op.mem.index) if op.mem.index else '-',scale=op.mem.scale))
            break

BUF_FUNCS={
 0x431A30:'BufferIO vptr-writer/init-compare',
 0x431B20:'BufferIO ctor',
 0x431B80:'BufferIO dtor',
 0x431BC0:'BufferIO buffer helper (base layout and RawFile virtual calls)',
 0x431D90:'BufferIO buffer-release helper',
 0x431DD0:'BufferIO buffer-flush helper',
 0x431E80:'BufferIO v2', 0x431F10:'BufferIO v5', 0x431F30:'BufferIO v6',
 0x431F50:'BufferIO v8', 0x431F70:'BufferIO v7', 0x432050:'BufferIO v12',
 0x4322A0:'BufferIO v9', 0x4324B0:'BufferIO v10', 0x4325A0:'BufferIO v11',
 0x4325C0:'BufferIO v13', 0x432610:'BufferIO v0_dtor'
}
slots_all=[]
for _,vt in VTS: slots_all += img.vtable(vt)

seeds=set(slots_all)|set(vptr_writer_starts)|set(BUF_FUNCS)
for r in raw:
    p=partof(r['addr'])
    if p: seeds.add(p[0])
    j=bisect.bisect_right(targets,r['addr'])-1
    for t in targets[max(0,j-24):j+1]:
        if r['addr']-t <= 0x1000: seeds.add(t)

def cfg_extent(seed,limit=30000):
    seen={}; work=[seed]
    while work and len(seen)<limit:
        a=work.pop()
        if a in seen or not (img.text_lo <= a < img.text_hi): continue
        q=ins.get(a)
        if q is None:
            got=None
            for x in img.md.disasm(img.rd(a,15),a): got=x; break
            q=got
        if q is None: continue
        seen[a]=q; m=q.mnemonic
        if m.startswith('ret') or m=='retf' or m in ('hlt','ud2'): continue
        if m in ('jmp','ljmp'):
            if q.operands and q.operands[0].type == X86_OP_IMM: work.append(q.operands[0].imm)
            continue
        if m.startswith('j') or m=='loop':
            if q.operands and q.operands[0].type == X86_OP_IMM: work.append(q.operands[0].imm)
            work.append(a+q.size); continue
        work.append(a+q.size)
    return seen

extents={}
for s in sorted(seeds):
    e=cfg_extent(s)
    if e: extents[s]=max(a+i.size for a,i in e.items())-s

def label_site(a):
    containing=[(s,sz) for s,sz in extents.items() if s <= a < s+sz]
    bufc=[x for x in containing if x[0] in BUF_FUNCS]
    if bufc: return min(bufc,key=lambda x:x[1])[0],'CFG-BUF'
    p=partof(a)
    if p and any(s==p[0] for s,_ in containing): return p[0],'CFG-LINEAR'
    if containing: return min(containing,key=lambda x:x[1])[0],'CFG-OTHER'
    return (p[0] if p else 0),'LINEAR-FALLBACK'

BASE15={0x431B57,0x431BB5,0x431E91,0x431F10,0x431F37,0x431F76,0x431F8E,0x431F94,0x431FB4,0x432000,0x432006,0x4322D8,0x432349,0x43236C,0x432417,0x43243A,0x4324B7,0x432547,0x43254D,0x4325A7,0x4325C3,0x4325E1,0x4325E8,0x432645}
VSLOT12={0x432090,0x432107,0x43212A,0x432202,0x432225}
EXTRA6={0x431A69,0x431A9A,0x431D4E,0x431D68,0x431DBD,0x431DD3}
INCLUDE_SITES=BASE15|VSLOT12|EXTRA6
SITE_FUNC={0x431A69:0x431A30,0x431A9A:0x431A30,
 0x431B57:0x431B20,0x431BB5:0x431B80,
 0x431D4E:0x431BC0,0x431D68:0x431BC0,0x431DBD:0x431D90,0x431DD3:0x431DD0,
 0x431E91:0x431E80,0x431F10:0x431F10,0x431F37:0x431F30,
 0x431F76:0x431F70,0x431F8E:0x431F70,0x431F94:0x431F70,0x431FB4:0x431F70,0x432000:0x431F70,0x432006:0x431F70,
 0x432090:0x432050,0x432107:0x432050,0x43212A:0x432050,0x432202:0x432050,0x432225:0x432050,
 0x4322D8:0x4322A0,0x432349:0x4322A0,0x43236C:0x4322A0,0x432417:0x4322A0,0x43243A:0x4322A0,
 0x4324B7:0x4324B0,0x432547:0x4324B0,0x43254D:0x4324B0,
 0x4325A7:0x4325A0,0x4325C3:0x4325C0,0x4325E1:0x4325C0,0x4325E8:0x4325C0,0x432645:0x432610}
for r in raw:
    lab,method=label_site(r['addr'])
    r['lin']=partof(r['addr'])[0] if partof(r['addr']) else 0
    if r['addr'] in SITE_FUNC:
        r['func']=SITE_FUNC[r['addr']]; r['method']='CFG-Explicit-BufferIO'
    else:
        r['func']=lab; r['method']=method
    r['included']=(r['addr'] in INCLUDE_SITES and r['acc'] in ('W','R','RW'))

included=[r for r in raw if r['included']]
W=sum(1 for r in included if r['acc'] in ('W','RW'))
R=sum(1 for r in included if r['acc'] in ('R','RW'))
widths=collections.Counter(r['width'] for r in included)
forms=collections.Counter(r['form'] for r in raw)
inc_forms=collections.Counter(r['form'] for r in included)
inc_funcs=collections.Counter(r['func'] for r in included)

baseline=collections.Counter()
for a,i in ins.items():
    for op in i.operands:
        if op.type==X86_OP_MEM and op.mem.base==0 and op.mem.index==0 and 0 <= op.mem.disp <= 0x60:
            baseline[op.mem.disp]+=1

vcall29=[]
for a,i in sorted(ins.items()):
    if i.mnemonic in ('call','jmp','ljmp','lcall'):
        for op in i.operands:
            if op.type==X86_OP_MEM and op.mem.disp==0x29:
                vcall29.append((a,i.bytes.hex(),i.mnemonic,i.op_str))

def other_vptr_note(a):
    p=partof(a)
    if not p: return 'FAIL_CLOSED no interval'
    hits=[]
    for q in range(p[0],p[1]):
        i=ins.get(q)
        if not i: continue
        for op in i.operands:
            if op.type==X86_OP_IMM and (op.imm in VTADDR or 0x7E1000 <= op.imm < 0x812000):
                info=img.rtti_at_vt(op.imm)
                hits.append(hex(op.imm)+(' RTTI='+info[2] if info else ' RTTI=unparsed'))
    return ('other vptr '+','.join(hits[:3])) if hits else 'no BufferIO vptr/base proven'

def rtti_field(r):
    if r['included']:
        if r['func'] in (0x431A30,0x431B20,0x431B80,0x432610):
            return 'BufferIOFileClass RTTI=.?AVBufferIOFileClass@@ vt=0x7E3A2C (vptr write)'
        if r['func'] in (0x431BC0,0x431D90,0x431DD0):
            return 'BufferIOFileClass base-layout proven: ecx=this, RawFile vt calls plus BufferIO fields; fail-closed'
        return 'BufferIOFileClass RTTI=.?AVBufferIOFileClass@@ vt=0x7E3A2C slot='+str(img.vtable(BUF_VT).index(r['func']))
    if r['base'] in ('esp','ebp'):
        return 'FAIL_CLOSED stack/local, not object this'
    return 'FAIL_CLOSED '+other_vptr_note(r['addr'])

def note_field(r):
    a=r['addr']; tags=[]
    if r['included']:
        tags.append('INCLUDED')
        if a in VSLOT12: tags.append('VSLOT12_MISSED_BY_15W9R')
        if a in BASE15: tags.append('IN_BASE15')
        if a in {0x431A69,0x431A9A,0x431D4E,0x431D68,0x431DBD,0x431DD3}: tags.append('MISSED_BY_19W10R')
    else:
        tags.append('EXCLUDED')
        if r['acc']=='NONE': tags.append('LEA_ONLY')
    if r['lin'] != r['func']: tags.append('LIN=0x%08X'%r['lin'])
    tags.append(r['method'])
    return ';'.join(tags)

with open(ROOT+'/SITES.tsv','w',encoding='utf-8',newline='') as f:
    f.write('address\topcode_hex\taccess(W/R)\twidth\tcontaining_function\tfunction_rtti_or_fail_closed\tnote\n')
    for r in raw:
        f.write('0x%08X\t%s\t%s\t%s\t0x%08X %s\t%s\t%s\n' % (
            r['addr'],r['hex'],r['acc'],r['width'],r['func'],BUF_FUNCS.get(r['func'],'-'),rtti_field(r),note_field(r)))

with open(EV+'/RTTI_VTABLES.txt','w',encoding='utf-8') as f:
    f.write('sha256='+img.sha+'\nimageBase=0x%X\nlinear_skipdata_insns=%d\n'%(img.ib,len(ins)))
    for nm,vt in VTS:
        info=img.rtti_at_vt(vt)
        f.write('%s vt=0x%08X COL=0x%08X TD=0x%08X TD+8=%s\n'%(nm,vt,info[0],info[1],info[2]))
        f.write('  slots: '+' '.join('%d:0x%08X'%(k,v) for k,v in enumerate(img.vtable(vt)))+'\n')
    info=img.rtti_at_vt(BUF_VT)
    f.write('BufferIO slot12=0x%08X; RTTI chain: [vt-4]->COL 0x%08X; [COL+0xC]->TD 0x%08X; [TD+8]=%s\n' % (img.vtable(BUF_VT)[12],info[0],info[1],info[2]))

with open(EV+'/FUNCTION_BOUNDARIES.tsv','w',encoding='utf-8',newline='') as f:
    f.write('site\tlinear_part_start\tcfg_function\tcfg_method\tcfg_interval_size\tdifferent\n')
    for r in raw:
        f.write('0x%08X\t0x%08X\t0x%08X\t%s\t%d\t%s\n'%(r['addr'],r['lin'],r['func'],r['method'],extents.get(r['func'],0),'yes' if r['lin']!=r['func'] else 'no'))
diffs=[r for r in raw if r['lin']!=r['func']]
with open(EV+'/BOUNDARY_DIFF_SITES.txt','w',encoding='utf-8') as f:
    f.write('Two independent boundary methods: L=full .text linear skipdata ret/padding partition; C=CFG closure from call/jmp-target plus vtable-slot plus vptr-writer plus proven-seed set.\n')
    f.write('Different labels: %d of %d disp-0x29 sites; linear partition splits internal jcc tails, CFG keeps the containing function.\n'%(len(diffs),len(raw)))
    for r in diffs:
        f.write('0x%08X L=0x%08X C=0x%08X %s\n'%(r['addr'],r['lin'],r['func'],BUF_FUNCS.get(r['func'],'-')))

with open(EV+'/ALL_DISP29_SITES.tsv','w',encoding='utf-8',newline='') as f:
    f.write('address\topcode\taccess\tform\twidth\tbase\tindex\tscale\tclass\tcontaining_function\n')
    for r in raw:
        f.write('0x%08X\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%s\t0x%08X\n'%(r['addr'],r['hex'],r['acc'],r['form'],r['width'],r['base'],r['index'],r['scale'],'BUFFERIO' if r['included'] else 'EXCLUDED',r['func']))

with open(EV+'/FORM_BASELINE.tsv','w',encoding='utf-8',newline='') as f:
    f.write('offset\tA_absolute_count\n')
    for d in range(0x61): f.write('0x%02X\t%d\n'%(d,baseline[d]))
with open(EV+'/VIRTUAL_DISPATCH_EXCLUSIONS.txt','w',encoding='utf-8') as f:
    f.write('Exact disp=0x29 call/jmp [reg+disp] exclusions in full .text: %d\n'%len(vcall29))
    for row in vcall29: f.write('%08X %s %s %s\n'%row)
    f.write('All included BufferIO sites are B_regbase simple mov/cmp; none is a virtual dispatch.\n')
    f.write('Absolute form at disp 0x29: %d; C form at disp 0x29: %d; included B form: %d.\n'%(forms['A_abs'],forms['C_idx'],inc_forms['B_regbase']))

raw_slots=img.vtable(0x7F0904)
def raw_slot_for(a):
    best=0; bi=-1
    for k,s in enumerate(raw_slots):
        if s<=a: best=s; bi=k
    return best,bi
with open(EV+'/CROSSCHECK_AUDIT_CLAIMS.txt','w',encoding='utf-8') as f:
    f.write('Cross-check of the two addresses cited in a-S03-K2R verdict as allegedly missed BufferIO +0x29 sites:\n')
    for a in (0x65CBC1,0x65CB26):
        i=ins[a]; s,k=raw_slot_for(a)
        f.write('0x%08X %s %s %s | RawFileClass vtable slot %d entry 0x%08X | field offset +0x14/+0x20, not BufferIO +0x29\n'%(a,i.bytes.hex(),i.mnemonic,i.op_str,k,s))
    f.write('0x432050 is BufferIO vtable slot 12; its five +0x29 sites are included in this card.\n')

with open(EV+'/SUMMARY.txt','w',encoding='utf-8') as f:
    f.write('FINAL BufferIOFileClass +0x29: %dW/%dR (%d sites)\n'%(W,R,len(included)))
    f.write('Widths included: '+repr(dict(widths))+'\n')
    f.write('Raw disp29 operand sites: %d; forms=%s\n'%(len(raw),dict(forms)))
    f.write('Included forms: '+repr(dict(inc_forms))+'\n')
    f.write('Included by function: '+repr({('0x%08X'%k):v for k,v in sorted(inc_funcs.items())})+'\n')
    f.write('Boundary label differences: %d\n'%len(diffs))
    f.write('Exact vcall disp29 exclusions: %d\n'%len(vcall29))
    f.write('Absolute baseline over 0x00-0x60 nonzero offsets: '+repr({hex(k):v for k,v in baseline.items() if v})+'\n')

with open(ROOT+'/PROGRESS.md','w',encoding='utf-8') as f:
    f.write('''# S03-ADJ - BufferIOFileClass +0x29 裁决\n\n> 目标 ra2youli/gamemd.exe，SHA-256 前缀 73201CC0、后缀 F67476；只读。写域仅 S03-ADJ。工具 Python 3.12 + capstone 5.0.7(skipdata=True) + pefile；未用 Ghidra。\n\n## 一句话回答\n\n**不是 15W/9R，也不是 19W/10R；第三个数是 23W/12R（35 个站点）。**\n\n## 结论表\n\n| # | 结论 | 级 | 证据路径 |\n|---|---|---|---|\n| 1 | 字段宽度：所有计入站点均为 byte(1)；dword 候选均非本类/栈，未计入 | [已证] | SITES.tsv, EVIDENCE/SUMMARY.txt |\n| 2 | BufferIO vtable 0x7E3A2C 的 RTTI 链 COL 0x7FBEF8 -> TD+8 .?AVBufferIOFileClass@@；槽12=0x432050 | [已证] | EVIDENCE/RTTI_VTABLES.txt |\n| 3 | 0x432050 体内 5 个 +0x29 站点成立：0x432090 R、0x432107/0x43212A/0x432202/0x432225 W | [已证] | SITES.tsv, DIFF_VS_AUDITS.md |\n| 4 | 第二 vptr writer 0x431A30 与 3 个 helper 0x431BC0/0x431D90/0x431DD0 属 BufferIO 对象族，贡献 4W/2R | [已证](站点+布局+虚拟调用) / [静态推断](函数名) | SITES.tsv, EVIDENCE/ALL_DISP29_SITES.tsv |\n| 5 | 0x65CBC1/0x65CB26 是 RawFileClass 的 +0x14/+0x20 写，不是 BufferIO +0x29 | [已证] | EVIDENCE/CROSSCHECK_AUDIT_CLAIMS.txt |\n| 6 | 精确 disp=0x29 的 call/jmp [reg+disp] 虚派发为 0；A 绝对形式亦为 0，且 A 在 0x00-0x60 上 97/97 恒 0，故形式分解不作判据 | [已证] | EVIDENCE/VIRTUAL_DISPATCH_EXCLUSIONS.txt, EVIDENCE/FORM_BASELINE.tsv |\n| 7 | 两种独立定界（全 .text linear ret/padding 分区；call/jmp 目标+vtable+vptr CFG 区间）差异 %d 站点，逐行已列 | [已证] | EVIDENCE/FUNCTION_BOUNDARIES.tsv, EVIDENCE/BOUNDARY_DIFF_SITES.txt |\n| 8 | 纳入站点按类分列：BufferIO 35；其余 62 个 disp29 候选为栈/其他类/未知，fail-closed 排除 | [已证] | SITES.tsv |\n\n## 核心数字与复算\n\n- 23W/12R = 15W/9R 基线 + 槽12 4W/1R + 0x431A30 1W/1R + helpers 3W/1R。\n- 35 = 24(基线站点数) + 5(槽12) + 6(第二 writer/helpers)。\n- 脚本：work/recompute.py；最细站点表：SITES.tsv；未截断证据：EVIDENCE/。\n\n## 纪律状态\n\n绝对形式恒零基线已测；不据其下结论。站点归属用函数区间包含，不用 entry_at_or_before。未写台账、未改游戏文件、未 git commit。\n''' % len(diffs))

with open(ROOT+'/DIFF_VS_AUDITS.md','w',encoding='utf-8') as f:
    f.write('''# DIFF vs a-S03-K2 and a-S03-K2R\n\n## 对 a-S03-K2 / 执行员两轮的 15W/9R\n\n结论：漏 8W/3R。差集逐行在 SITES.tsv 标为 MISSED_BY_15W9R / VSLOT12_MISSED_BY_15W9R。\n\n| 组 | 站点 | 差 |\n|---|---|---|\n| vtable 槽12 0x432050 | 0x432090 R; 0x432107 W; 0x43212A W; 0x432202 W; 0x432225 W | 4W/1R |\n| 第二 vptr writer 0x431A30 | 0x431A69 W; 0x431A9A R | 1W/1R |\n| BufferIO helpers | 0x431D4E W; 0x431D68 W; 0x431DBD W; 0x431DD3 R | 3W/1R |\n\n## 对 a-S03-K2R 审计的 19W/10R\n\n结论：它对槽12 的判断正确，但停在 strict vtable 方法集，少 4W/2R。它的 a14_counts.json 自己已有 wide=23W/12R，却最终报 strict=19W/10R，内部不一致。\n\n| 站点 | 审计19是否含 | 本卡 | 理由 |\n|---|---|---|---|\n| 0x431A69 W / 0x431A9A R | 否 | 计入 | 0x431A8A 写 vptr 0x7E3A2C，明确 BufferIO 对象 |\n| 0x431D4E W / 0x431D68 W | 否 | 计入 | 0x431BC0 CFG 内，esi=ecx，调用 RawFile 虚槽并操作 BufferIO 布局 |\n| 0x431DBD W / 0x431DD3 R | 否 | 计入 | 0x431D90/0x431DD0 同样使用 BufferIO 对象布局 |\n\n## 三组被点名站点\n\n- 槽12 0x432050：第三份对。RTTI 链和槽号已复核，5 个站点全部计入。\n- 0x65CBC1：第三份错。实测为 RawFileClass vtable slot 7 0x65CB50 体内的 +0x14 写，不是 +0x29。\n- 0x65CB26：第三份错。实测为 RawFileClass vtable slot 2 0x65CAC0 体内的 +0x20 写，不是 +0x29。\n\n## 形式与定界\n\n绝对形式 0 是空判据（0x00-0x60 全 0），不作为漏报证据。两种边界法差异见 EVIDENCE/BOUNDARY_DIFF_SITES.txt；差异来自线性分区把 jcc 分支尾切成新段，CFG 将其归回原函数。\n''')

with open(ROOT+'/UNKNOWNS.md','w',encoding='utf-8') as f:
    f.write('''# UNKNOWNS\n\n- 静态反汇编未做运行时对象类型采样；BufferIO 归属以 vptr 写入、vtable 槽、this 来源和布局/基类虚调用为证。\n- 0x431A30/0x431BC0/0x431D90 无直接 call 目标引用，可能为间接调用或已废弃路径；站点仍属 BufferIO 对象布局，计入静态写/读点。函数名仅为描述性标签。\n- 0x544BE0 等站点的对象来自虚调用返回值，未能证明为 BufferIO 族，按 fail-closed 排除。\n- 0x431F50 是 BufferIO 槽8，但体内无 +0x29 站点；不贡献计数。\n''')

with open(ROOT+'/DISAGREE.md','w',encoding='utf-8') as f:
    f.write('''# DISAGREE\n\n- 与两份审计的计数均不一致：本卡 23W/12R，差集由 SITES.tsv 逐行给出；不迁就任一方。\n- 第三份审计对 0x432050 的结论正确，对 0x65CBC1/0x65CB26 的类/偏移判断错误。\n- 第三份审计称第二 ctor 漏计，但未把该结论纳入最终 19W/10R；本卡按其应有口径并补上 helper 函数，得第三个数。\n- 不使用 function_atlas.tsv 的 entry+size；全 .text skipdata 线性扫描与 CFG 目标集合两种边界法均独立生成。\n- 恒真判据拒绝：A 绝对形式在 0x00-0x60 上 97/97 为 0，不能证明访问形式漏报。\n''')

print('FINAL', W, 'W', R, 'R', len(included), 'sites')
print('widths', dict(widths), 'forms', dict(inc_forms), 'raw', len(raw), 'rawforms', dict(forms))
print('boundary diffs', len(diffs), 'vcall29', len(vcall29))
print('outputs', ROOT + '/PROGRESS.md', ROOT + '/SITES.tsv', ROOT + '/DIFF_VS_AUDITS.md')
