# -*- coding: utf-8 -*-
"""R176 沙箱：ast 取 facts_floors 的常量与 canon 五函数，先复算旧 MASTER 命中作硬闸，
再算新 MASTER（F24 floor 与新 CUR_SHA256/TOTAL_BYTES）。不写任何文件。"""
import ast,hashlib,sys
SRC='/home/t628/projects/ra2-campaign-forge/_r160/facts_floors.py'
src=open(SRC,encoding='utf-8').read()
tree=ast.parse(src)
ns={}
# 取 canon_* 函数源码
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.name.startswith('canon_'):
        exec(compile(ast.Module(body=[node],type_ignores=[]),SRC,'exec'),ns)
# 取常量
want={'GRADES','FLOORS','EVID','EVIDB','LOST','ITEMS','UNIQ','LOST_ITEMS','LOST_UNIQ','MASTER_SHA256','CUR_SHA256','TOTAL_BYTES'}
got={}
for node in tree.body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
        n=node.targets[0].id
        if n in want:
            got[n]=ast.literal_eval(node.value)
print('constants found:',sorted(got))
assert set(got)==want, set(want)-set(got)
def master(cur_sha,total,floors):
    return hashlib.sha256(('\n'.join([cur_sha,str(total),ns['canon_g'](got['GRADES']),ns['canon_f'](floors),
        ns['canon_e'](got['EVID']),ns['canon_eb'](got['EVIDB']),ns['canon_l'](got['LOST']),
        str(got['ITEMS']),str(got['UNIQ']),str(got['LOST_ITEMS']),str(got['LOST_UNIQ'])])).encode()).hexdigest()
old=master(got['CUR_SHA256'],got['TOTAL_BYTES'],got['FLOORS'])
print('old recomputed',old[:16],'pinned',got['MASTER_SHA256'][:16])
assert old==got['MASTER_SHA256'],'HARD GATE: old constants must reproduce old MASTER'
newfl=dict(got['FLOORS']); newfl['F24']=(11238,36117)
print('F24 floor',got['FLOORS']['F24'],'->',newfl['F24'])
# 反控 1：只换 sha
a=master('X'*64,got['TOTAL_BYTES'],got['FLOORS']); assert a!=old
# 反控 2：只换 total
b=master(got['CUR_SHA256'],got['TOTAL_BYTES']+1,got['FLOORS']); assert b!=old
# 反控 3：只换 F24 floor（两个分量各试一次）
for idx in (0,1):
    f=dict(got['FLOORS']); f['F24']=tuple(newfl['F24'][i]+(1 if i==idx else 0) for i in range(2))
    assert master(got['CUR_SHA256'],got['TOTAL_BYTES'],f)!=old
print('3 negative controls ok (sha / total / each F24 component changes MASTER)')
newsha='PLACEHOLDER'
# 用真实新 sha 计算（稍后由写盘脚本注入）；此处先打印用 V559 内容的真值
raw=open('/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/R17_R128_FACTINDEX_V558/FACT_INDEX.tsv','rb').read()
print('V558 sha',hashlib.sha256(raw).hexdigest()[:16],'bytes',len(raw))
print('V558 master (should equal pinned):',master(hashlib.sha256(raw).hexdigest(),len(raw),got['FLOORS'])[:16])
