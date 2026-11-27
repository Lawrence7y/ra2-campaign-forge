import sys,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
dw=P.dw; where=P.where; cstr=P.cstr
def colrec(a):
    if a is None or where(a)!='.rdata': return None
    d=[dw(a+4*i) for i in range(5)]
    if None in d or d[0] not in (0,1): return None
    if where(d[3])!='.data' or where(d[4])!='.rdata': return None
    nm=cstr(d[3]+8)
    if not (nm and nm.startswith(b'.?A')): return None
    return {'va':a,'sig':d[0],'off':d[1],'cd':d[2],'ptd':d[3],'pchd':d[4],'name':nm.decode('latin1')}
S=json.load(open('/home/t628/projects/ra2-campaign-forge/out/reverse/symbols.json'))
CL=S['classes']
def demangle(n):
    if n.startswith('.?AV'): b=n[4:]
    elif n.startswith('.?AU'): b=n[4:]
    else: return n
    return b[:-2] if b.endswith('@@') else b
for k in ('AbstractClass','UnitClass','AITriggerTypeClass','FlyLocomotionClass'):
    c=CL[k]
    cv=int(c['col_va'],16); vt=int(c['vtable_va'],16)
    a=colrec(cv); b=colrec(vt-4)
    print(k)
    print('  symbols col',hex(cv),a and (a['off'],a['cd'],hex(a['pchd']),demangle(a['name'])))
    print('  vt-4    col',hex(vt-4),b and (b['off'],b['cd'],hex(b['pchd']),demangle(b['name'])))
    print('  same pchd?', a and b and a['pchd']==b['pchd'])
