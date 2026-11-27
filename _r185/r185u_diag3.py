import sys,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
dw=P.dw; where=P.where; cstr=P.cstr
def colrec(a):
    if a is None or where(a)!='.rdata': return None
    d=[dw(a+4*i) for i in range(5)]
    if None in d or d[0] not in (0,1) or d[2]!=0: return None
    if where(d[3])!='.data' or where(d[4])!='.rdata': return None
    nm=cstr(d[3]+8)
    if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): return None
    return {'va':a,'sig':d[0],'off':d[1],'cd':d[2],'ptd':d[3],'pchd':d[4],'name':nm.decode('latin1')}
def dem(n):
    if not (n.startswith('.?AV') or n.startswith('.?AU')): return n
    b=n[4:]
    return b[:-2] if b.endswith('@@') else b
S=json.load(open('/home/t628/projects/ra2-campaign-forge/out/reverse/symbols.json'))
CL=S['classes']
eq=0; ne=[]; badpre=[]; badcv=[]; offmap=collections.Counter(); offmap2=collections.Counter()
for k,c in CL.items():
    if c['vtable_va'] is None: continue
    vt=int(c['vtable_va'],16); cv=int(c['col_va'],16)
    pre=dw(vt-4)
    a=colrec(pre); b=colrec(cv)
    if not a: badpre.append((k,hex(pre) if pre is not None else None,where(pre)))
    else: offmap[a['off']]+=1
    if not b: badcv.append((k,hex(cv),where(cv)))
    else: offmap2[b['off']]+=1
    if pre==cv: eq+=1
    else: ne.append((k,a and dem(a['name']),a and a['off'],b and dem(b['name']),b and b['off'],a and b and a['ptd']==b['ptd']))
print('pre==col_va:',eq,'diff:',len(ne))
print('pre-COL off hist',dict(offmap))
print('col_va-COL off hist',dict(offmap2))
print('badpre',len(badpre),badpre[:5])
print('badcv',len(badcv),badcv[:8])
print('diff samples',ne[:6])
print('diff中 名字相同数:',sum(1 for x in ne if x[1]==x[3]),' ptd相同数:',sum(1 for x in ne if x[5]))
print('diff 中 a 缺失:',sum(1 for x in ne if x[1] is None))
