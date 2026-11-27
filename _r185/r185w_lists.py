import sys,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
dw=P.dw;where=P.where;cstr=P.cstr;r2o=P.r2o
def colrec(a):
    if a is None or where(a)!='.rdata': return None
    d=[dw(a+4*i) for i in range(5)]
    if None in d or d[0] not in (0,1) or d[2]!=0: return None
    if where(d[3])!='.data' or where(d[4])!='.rdata': return None
    nm=cstr(d[3]+8)
    if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): return None
    return {'va':a,'sig':d[0],'mdisp':d[1],'ptd':d[3],'pchd':d[4],'name':nm.decode('latin1')}
def dem(n):
    b=n[4:] if n.startswith('.?A') else n
    return b[:-2] if b.endswith('@@') else b
S=json.load(open('/home/t628/projects/ra2-campaign-forge/out/reverse/symbols.json'))['classes']
m4=[]; d88=[]
for k,c in S.items():
    if c['vtable_va'] is None: continue
    vt=int(c['vtable_va'],16); r=colrec(dw(vt-4))
    if r['mdisp']!=0: m4.append((k,hex(vt),hex(r['va']),r['mdisp']))
    cv=int(c['col_va'],16)
    if cv!=r['va']:
        r2=colrec(cv)
        d88.append((k,hex(vt),hex(r['va']),r['mdisp'],hex(cv),r2['mdisp']))
print('mdisp!=0 primary COL count',len(m4))
for x in m4: print('  ',x)
print('dual COL 88, 前 10:'); 
for x in d88[:10]: print('  ',x)
json.dump({'m4':m4,'d88':d88},open('/home/t628/projects/ra2-campaign-forge/_r185/r185w.json','w'),indent=1)
