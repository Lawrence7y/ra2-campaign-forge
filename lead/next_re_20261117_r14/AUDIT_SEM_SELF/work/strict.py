
import json, importlib.util
spec = importlib.util.spec_from_file_location('eng', r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\work\engine2.py')
# 直接重用 engine2 里的函数
src = open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\work\engine2.py',encoding='utf-8').read()
src = src.split('import sys')[0]
g = {}
exec(compile(src, 'eng2', 'exec'), g)
extent = g['extent']; md = g['md']
import capstone

def strict_loops(entry):
    body = extent(entry)
    addr2i = {i.address:i for i in body}
    keys = sorted(addr2i)
    out=[]
    for i in body:
        m=i.mnemonic
        if m.startswith('j') and m!='jmp':
            t = g['dtgt'](i)
            if t is None or t > i.address: continue
            seg=[addr2i[a] for a in keys if t<=a<=i.address]
            inc=read=write=cmp_=0
            for ii in seg:
                if ii.mnemonic in ('inc','dec','add','sub','lea'):
                    if ii.mnemonic!='lea' or '0x1' in ii.op_str or '*' in ii.op_str:
                        inc+=1
                try:
                    for op in ii.operands:
                        if op.type==capstone.x86.X86_OP_MEM:
                            if op.access & capstone.CS_AC_WRITE: write+=1
                            elif op.access & capstone.CS_AC_READ: read+=1
                except Exception: pass
                if ii.mnemonic.startswith('cmp') or ii.mnemonic=='test': cmp_+=1
            out.append({'head':hex(t),'back':hex(i.address),'n':len(seg),'inc':inc,'read':read,'write':write,'cmp':cmp_,
                        'ok': inc>0 and read>0 and write>0 and cmp_>0 and len(seg)>=4})
    return [o for o in out if True], out

rows=[]
for line in open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\work\weak105.tsv',encoding='utf-8'):
    f=line.rstrip('\n').split('\t')
    if len(f)<5 or f[0]=='entry' or f[1]=='S22': continue
    rows.append((f[0],f[3]))
res={}
for e,c in rows:
    try:
        _,loops = strict_loops(int(e,16))
    except Exception as ex:
        loops=[]
    ok=[l for l in loops if l['ok']]
    res[e]={'cls':c,'n_loops':len(loops),'n_ok':len(ok),'loops':loops}
json.dump(res, open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\work\strict_loops.json','w'), indent=1)
keep=[]
for e,c in rows:
    r=res[e]
    if r['n_ok']>0: keep.append((e,c,r['n_ok'],r['n_loops'],r['loops'][0]['head'],r['loops'][0]['n']))
print('rows with >=1 strict loop:', len(keep))
for k in keep: print(' ',k[0],k[1],'ok=%d/%d head=%s span=%d'%(k[2],k[3],k[4],k[5]))
