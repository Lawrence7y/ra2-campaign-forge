# -*- coding: utf-8 -*-
"""R210 c1: 12 个 QI 目标的 (IID, 返回 this 偏移) 完整分解 + 与额外视图 mdisp 的对应。
IID -> 标准名只取 OLE 公开 IID 值（外部知识，非代码字节推论），标注清楚。
"""
import sys,struct,json,collections,re
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]

d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
TH={int(k,16):v for k,v in d3['thunk'].items()}
VT={int(k,16):[int(x,16) for x in v] for k,v in d3['vt'].items()}
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
HIT={int(k,16):[(i,int(x,16)) for i,x in v] for k,v in d3['hit'].items()}
QI=collections.defaultdict(list)
for c in HIT:
    for i,v in HIT[c]:
        if i==0: QI[TH[v]['jmp']].append(c)
ck('C0 12 个 slot0 QI 目标', len(QI)==12, len(QI))

def guid(va):
    o=P.r2o(va); b=P.RAW[o:o+16]
    d1,d2,d3_=struct.unpack_from('<IHH',b,0)
    return '%08X-%04X-%04X-%s-%s'%(d1,d2,d3_,b[8:10].hex().upper(),b[10:16].hex().upper())

def body(a,cap=800):
    o=P.r2o(a); out=[]
    for i in md.disasm(P.RAW[o:o+cap],a):
        out.append(i)
        if i.mnemonic=='ret' and i.address>a+0x20: break
    return out

def parse(a):
    ins=body(a)
    thisreg=None
    # 找 this 寄存器：mov <reg>, dword ptr [esp + X] 且随后被 lea [reg+K] 使用
    for i in ins:
        if i.mnemonic=='lea' and '+' in i.op_str:
            try: thisreg=i.op_str.split('[')[1].split(' ')[0].strip()
            except Exception: pass
    rows=[]   # (iid, off, kind)
    cur=None
    for k,i in enumerate(ins):
        if i.mnemonic=='mov' and i.op_str.startswith('edi, 0x'):
            cur=dict(iid=int(i.op_str.split(', ')[1],16), off=None, at=i.address, form='?')
        if cur is None: continue
        if i.mnemonic=='repe':
            cur['cmp']=i.address
        if i.mnemonic=='mov' and i.op_str.count(',')==1 and i.op_str.startswith('dword ptr [') and cur.get('off') is None:
            src=i.op_str.split(', ')[1]
            cur['off']=0; cur['form']='mov_this'; cur['src']=src
            rows.append(cur); cur=None
        if i.mnemonic=='lea' and cur.get('off') is None:
            m=re.search(r'\+ (0x[0-9a-f]+)\]', i.op_str)
            if not m: continue
            off=int(m.group(1),16)
            cur['off']=off; cur['form']='lea'; rows.append(cur); cur=None
        if i.mnemonic=='call':
            d0=[]
            for j in ins[k:k+4]:
                if j.mnemonic=='cmp' and 'ptr [' in j.op_str: d0.append(('cmp',j.op_str))
                if j.mnemonic=='mov' and j.op_str.startswith('dword ptr ['): d0.append(('mov',j.op_str))
            cur['off']=0; cur['form']='delegate'; cur['after']=d0; rows.append(cur); cur=None
    # 去重（同一 IID 若多次出现保留首个带 off 的）
    out=[]
    seen=set()
    for r in rows:
        key=(r['iid'],r['off'])
        if key in seen: continue
        seen.add(key); out.append(r)
    return ins,out,thisreg

TAB={}
for t in sorted(QI):
    ins,rows,tr=parse(t)
    TAB[t]=dict(ninsn=len(ins),iids=[(r['iid'],r['off'],r['form']) for r in rows],thisreg=tr,
                ntab=len(QI[t]),mdisp=sorted({MD[c] for c in QI[t]}))
    print('==== %08x ntab=%-3d mdisp=%-24s this=%s'%(t,len(QI[t]),sorted({MD[c] for c in QI[t]}),tr))
    for r in rows:
        print('     IID %08x %-38s -> this+%-6s form=%s'%(r['iid'],guid(r['iid']),('0x%x'%r['off']) if r['off'] is not None else None,r['form']))

# 反控：IID 地址必须全落 .rdata 且是 16 字节对齐的 4 处 cmpsd
alliid=sorted({x[0] for v in TAB.values() for x in v['iids']})
ck('C1 被比较 IID 地址数 = %d，全落 .rdata'%len(alliid), all(P.where(a)=='.rdata' for a in alliid), [hex(a) for a in alliid])
# 关键断言：每张 T 表的 mdisp 必须出现在其 QI 的返回偏移集合里，或为 0
ok=0; bad=[]
for t,v in TAB.items():
    offs={x[1] for x in v['iids']}
    for c in QI[t]:
        if MD[c]==0: continue
        if MD[c] in offs: ok+=1
        else: bad.append((hex(c),NM[c],MD[c],sorted(offs)))
ck('C2 每张额外视图表的 mdisp 都在其 QI 返回偏移集合中', len(bad)==0, 'ok=%d bad=%d %s'%(ok,len(bad),bad[:4]))
ck('C3 101 张表全部覆盖（非 0 mdisp）', ok+len(bad)==101, ok+len(bad))
json.dump(dict(tab={hex(k):v for k,v in TAB.items()},
               qi={hex(k):v for k,v in QI.items()},
               guid={hex(a):guid(a) for a in alliid}),
          open('/home/t628/projects/ra2-campaign-forge/_r210/c1.json','w'),indent=0)
print('FAILS',fails)
