# -*- coding: utf-8 -*-
"""R209 p1：FACT_INDEX 升版 V590 -> V591，把「律 T 订正（thunk 不只 slot0，而是 IUnknown 三方法三连）」
写入 F29。约束同 R208 p3：行数 57 / F01..F56 / 5 列 / grade 与第 4 列逐字不变 / 只增长 / LF-only。
顺序：先写版本目录 -> 后改指针（p2 做）。
"""
import os,io,csv,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
OLD=TIER+'/R17_R131_FACTINDEX_V590/FACT_INDEX.tsv'
NEWD=TIER+'/R17_R131_FACTINDEX_V591'
NEW=NEWD+'/FACT_INDEX.tsv'
raw=open(OLD,'rb').read()
assert raw.count(b'\r')==0
sha_old=hashlib.sha256(raw).hexdigest()
assert sha_old=='e49a3eddc47d7cc5183d6aa9f103a2a0f7e1ee679379763b5aa6ef5866c6ec33', sha_old
print('V590 sha OK', sha_old[:16], len(raw), 'B')
rows=list(csv.reader(io.StringIO(raw.decode('utf-8')),delimiter='\t'))
hdr,data=rows[0],rows[1:]
assert len(data)==56 and data[0][0]=='F01'
i29=[i for i,r in enumerate(data) if r[0]=='F29'][0]
b_stmt=len(data[i29][1].encode()); b_lim=len(data[i29][4].encode())
print('F29 before: stmt %d B lim %d B'%(b_stmt,b_lim))
ADD=('；**R209 律 T 订正（口径过窄，R208 结论需扩展而非推翻）**：R208 说「101 条额外视图的 slot0 是 this 调整 thunk」'
 '——数字对，但**口径过窄**。用全槽扫描（不是只取 slot0）实测：.text 段 this 调整 thunk 共 **70** 个'
 '（83 6C 24 04 锚点 67 + 81 6C 24 04 锚点 3）；这 70 个**全部**被 vftable 槽引用（孤儿 thunk 0 个）。'
 '被引用的 **101** 张额外视图表的 slot0、slot1、slot2 **三槽连排都是 thunk**（303 槽），另有 2 处越界槽'
 '（HouseClass mdisp=40 表 slot3/slot4），合计 **305** 槽。三槽的 thunk 立即数都等于该表 mdisp **303/303**。'
 '三槽 thunk 的 E9 落点分别满足「ret 0xc」**101/101**、「ret 4」**101/101**、「ret 4」**101/101** '
 '（而主视图 954 表的同三槽 ret 分布是 slot0 {4:709,12:187,8:1,0:3}、slot1 9 种、slot2 7 种，异构）'
 '⇒ 三槽语义 = **QueryInterface / AddRef / Release**，即额外视图数组的前三槽是把 IUnknown 三方法'
 '按 this 偏移 m 调整后转发给本类主视图同槽。又：三槽 E9 落点 == 本类主视图（mdisp==0 那张）同槽号，'
 'k=0/1/2 各 **101/101**。去重后 (slot0,slot1,slot2) 三元组 **23** 个，23 个三元组内 mdisp 唯一，'
 '但只落 **13** 个 jmp 三元组 ⇒ 同一套 QI/AddRef/Release 目标被多个 mdisp 复用（22 个 slot0 thunk ↔ 12 个 QI 目标）。'
 '越界 2 槽（HouseClass）：slot3 thunk 0x510ab0 imm=4 jmp 0x4f6e60（体 = mov eax,[esp+4] ; mov eax,[eax+0xc] ; ret 4，'
 'getter 形态）、slot4 thunk 0x510ac0 imm=4 jmp 0x4f6950（体首 mov ecx,[esp+4] ; sub esp,0x40 ; ... ; push 0x20，'
 '取缓冲形态）；两槽 imm=4 而表 mdisp=40 ⇒ **越界槽不遵循 thunk-imm==mdisp**，其 imm 是接口自身的 this 偏移而非基类偏移。'
 'T/S/I 三形态互斥性同步加固：T 承载 101 表 / S 承载 156 表（0x410590 78 / 0x410580 75 / 0x6d1770 3，全为单槽）/ '
 'I 承载 3 表（0x41bc30 / 0x522a60 / 0x746100），三集合两两不交且合计 260 = 额外视图总数。')
ADD_LIM=('；R209 追加边界：① 本项只覆盖「额外视图数组前三槽 + HouseClass 越界两槽」，不覆盖主视图 954 表 slot>=3 的槽语义；'
 '② 70 个 thunk 中 22 个作 slot0、其余 48 个只作 slot1/slot2（按 slot0 口径计数会漏 48 个，R208 报「21 个」是把 B81 那条漏了，实为 22）；'
 '③ 305 槽的数字口径是「槽」不是「表」也不是「COL」，与 R208 的「101 条 COL」不同分母；'
 '④ S 表 0x6d1770 三张承载表为 MouseClass / TabClass / ScrollClass（mdisp 全 21784、均单槽），'
 '其体内比较的 0x11c7 / 0x11c8 不是类 pTD 地址（pTD 全落 .data），且该函数被直接 call/jmp 各 0 次，语义未取得；'
 '⑤ HouseClass slot4 的 jmp 目标 0x4f6950 只读出前 6 条指令，完整语义未取得。')
data[i29][1]=data[i29][1]+ADD
data[i29][4]=data[i29][4]+ADD_LIM
assert len(data[i29][1].encode())>b_stmt and len(data[i29][4].encode())>b_lim
for i in range(56):
    if i==i29: continue
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
print('V591 written: %d B (V590 %d B, +%d) sha=%s'%(len(out),len(raw),len(out)-len(raw),sha_new))
chk=list(csv.reader(io.StringIO(open(NEW,'rb').read().decode('utf-8')),delimiter='\t'))
assert len(chk)==57 and [r[0] for r in chk[1:]]==['F%02d'%i for i in range(1,57)]
assert all(len(r)==5 for r in chk)
assert not [i for i in range(1,57) if chk[i][2]!=rows[i][2]]
assert not [i for i in range(1,57) if chk[i][3]!=rows[i][3]]
print('结构校验：57 行 / F01..F56 / 5 列 / grade 全同 / 第4列全同 ⇒ OK')
print('F29 after: stmt %d B lim %d B'%(len(chk[i29+1][1].encode()),len(chk[i29+1][4].encode())))
