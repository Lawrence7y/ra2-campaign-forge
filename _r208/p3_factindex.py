# -*- coding: utf-8 -*-
"""R208 p3：FACT_INDEX 升版 V588 -> V589，把 0x7f9594 结案写入 F01。
约束（facts_floors 的 D2..D8）：
  - 行数仍 56 + 表头、fact_id 仍 F01..F56、grade 不变、第 4 列证据清单逐字不变（D7）
  - 只允许「增长」：statement 与 limitations 追加文字（D6 下界不动）
  - LF-only（D1）
步骤：先写版本目录（顺序不能反）-> 再改指针 -> 再改 facts_floors 常量与 D9 主指纹 -> 再改 gate_runner 的 LEDGER
"""
import os,io,csv,hashlib,json,re,sys,shutil
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
OLD=TIER+'/R17_R131_FACTINDEX_V588/FACT_INDEX.tsv'
NEWD=TIER+'/R17_R131_FACTINDEX_V589'
NEW=NEWD+'/FACT_INDEX.tsv'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'

raw=open(OLD,'rb').read()
assert raw.count(b'\r')==0
sha_old=hashlib.sha256(raw).hexdigest()
rows=list(csv.reader(io.StringIO(raw.decode('utf-8')),delimiter='\t'))
hdr,data=rows[0],rows[1:]
assert len(data)==56 and data[0][0]=='F01'
b0_stmt=len(data[0][1].encode()); b0_lim=len(data[0][4].encode())
print('F01 before: stmt %d B lim %d B'%(b0_stmt,b0_lim))

ADD_STMT=('；**R208 结案**：链末 TD 的 `+0` 字段不是「类 ID」，而是 MSVC type_info 类的**共享 vftable 指针** 0x7f9594'
          '（988/988 个 TD 全等；该址 1 槽 0x7c8ab7 = scalar deleting destructor；vftable[-1]=0x7f9590 装 0x80ee30 即 .?AVtype_info@@ 的 COL；'
          '+4 起为 Access violation - no RTTI data! 且被 .text 非对齐 imm32 引用 3 处 0x7ca957/0x7caab1/0x7cabe1；'
          '.data 值落 .rdata 的引用榜 988 vs 8 领先 123 倍）⇒ TD 布局 = {+0 vfptr, +4 spare 恒 0, +8 内联 mangled 名}，R202 的「+0=类 ID」读法作废')
ADD_LIM=('；R208 追加：TD 头 +0 == 0x7f9594（988/988，取值分布仅 1 项）、+4 == 0（988/988）、+8 起为内联 C 串（988/988，非指针）——'
         '三者均为全量实测而非抽样。反控：0x7f9590 / 0x7f9598 作 +0 目标各命中 0 次。'
         '边界：本结论只覆盖「TD+0 的语义」，不覆盖 attributes 位义（attrs&1 的 4 条 pdisp=-1 与 MSVC 标准位义矛盾，静态不可判定，须动态采样）。')
data[0][1]=data[0][1]+ADD_STMT
data[0][4]=data[0][4]+ADD_LIM
assert len(data[0][1].encode())>b0_stmt and len(data[0][4].encode())>b0_lim
# 其余 55 行逐字节不变
for i in range(1,56):
    assert rows[i+1][1:]==data[i][1:], 'row %d mutated'%i
buf=io.StringIO()
w=csv.writer(buf,delimiter='\t',lineterminator='\n',quoting=csv.QUOTE_MINIMAL)
w.writerow(hdr)
for r in data: w.writerow(r)
txt=buf.getvalue()
if not txt.endswith('\n'): txt+='\n'
out=txt.encode('utf-8')
assert out.count(b'\r')==0
os.makedirs(NEWD,exist_ok=True)
assert not os.path.exists(NEW)
open(NEW,'wb').write(out)
sha_new=hashlib.sha256(out).hexdigest()
print('V589 written: %d B (V588 %d B, +%d) sha=%s'%(len(out),len(raw),len(out)-len(raw),sha_new[:16]))
# 回读校验：结构不变
chk=list(csv.reader(io.StringIO(open(NEW,'rb').read().decode('utf-8')),delimiter='\t'))
assert len(chk)==57 and [r[0] for r in chk[1:]]==['F%02d'%i for i in range(1,57)]
assert all(len(r)==5 for r in chk)
diffcols=[i for i in range(1,57) if chk[i][2]!=rows[i][2]]
assert not diffcols, diffcols
diffev=[i for i in range(1,57) if chk[i][3]!=rows[i][3]]
assert not diffev, diffev
print('结构校验：57 行 / F01..F56 / 5 列 / grade 全同 / 第4列全同 ⇒ OK')
json.dump(dict(old=sha_old,new=sha_new,obytes=len(raw),nbytes=len(out),dir=os.path.basename(NEWD)),
          open(ROOT+'/_r208/p3_fi.json','w'),ensure_ascii=False,indent=1)
