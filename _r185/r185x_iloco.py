import sys,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
dw=P.dw;where=P.where;cstr=P.cstr
def colrec(a):
    if a is None or where(a)!='.rdata': return None
    d=[dw(a+4*i) for i in range(5)]
    if None in d or d[0] not in (0,1) or d[2]!=0: return None
    if where(d[3])!='.data' or where(d[4])!='.rdata': return None
    nm=cstr(d[3]+8)
    if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): return None
    return {'va':a,'mdisp':d[1],'ptd':d[3],'pchd':d[4],'name':nm.decode('latin1')}
def dem(n):
    b=n[4:] if n.startswith('.?A') else n
    return b[:-2] if b.endswith('@@') else b
def bcd(a):
    d=[dw(a+4*i) for i in range(6)]
    if None in d or where(d[0])!='.data': return None
    return {'ptd':d[0],'ncbase':d[1],'mdisp':d[2],'pdisp':d[3]}
S=json.load(open('/home/t628/projects/ra2-campaign-forge/out/reverse/symbols.json'))['classes']
twelve=[]
for k,c in S.items():
    if c['vtable_va'] is None: continue
    r=colrec(dw(int(c['vtable_va'],16)-4))
    if r['mdisp']==4: twelve.append(k)
print('mdisp==4 主 COL 类数',len(twelve),twelve)
# 对每个，检查 BCD 里 ILocomotion 的 mdisp
for k in twelve:
    c=S[k]; vt=int(c['vtable_va'],16); r=colrec(dw(vt-4))
    ch=r['pchd']; nb=dw(ch+8); arr=dw(ch+12)
    ent=[]
    for i in range(nb):
        b=bcd(dw(arr+4*i))
        nm=dem(cstr(b['ptd']+8).decode('latin1'))
        ent.append((nm,b['mdisp'],b['ncbase']))
    iloco=[e for e in ent if e[0]=='ILocomotion']
    print(k,'nbase',nb,'ILocomotion',iloco,'bases==symbols?',[e[0] for e in ent]==c['bases'])
