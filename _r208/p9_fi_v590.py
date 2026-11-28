# -*- coding: utf-8 -*-
"""R208 p9：FACT_INDEX 升版 V589 -> V590，把本轮两条新实测写入 F29（T 形态双编码 + 81 兜底的 thunk 级常量性）。
约束与 p3 相同：57 行 / F01..F56 / 5 列 / grade 与第 4 列逐字不变 / 只允许增长 / LF-only。
"""
import os,io,csv,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
OLD=TIER+'/R17_R131_FACTINDEX_V589/FACT_INDEX.tsv'
NEWD=TIER+'/R17_R131_FACTINDEX_V590'
NEW=NEWD+'/FACT_INDEX.tsv'
raw=open(OLD,'rb').read()
assert raw.count(b'\r')==0
rows=list(csv.reader(io.StringIO(raw.decode('utf-8')),delimiter='\t'))
hdr,data=rows[0],rows[1:]
assert len(data)==56
i29=[r[0] for r in data].index('F29')
b_stmt=len(data[i29][1].encode()); b_lim=len(data[i29][4].encode())
ADD=('；**【R208 补订·T 形态双编码】**本镜像 this 调整 thunk 的**字节形态不是统一一种**：额外视图 vftable 的 slot0 为 this 调整 thunk 者共 **101** 条，'
     '其中 **100** 条编码 `83 6C 24 04 <imm8> E9 <rel32>`（mdisp ∈ {4,24,36,40,44}），**1** 条因 mdisp=**1728**（0x6C0）超出 imm8 范围而编码 '
     '`81 6C 24 04 <imm32> E9 <rel32>`（COL 0x7fb310 / .?AVAircraftClass@@ / vftable 0x7e2250 / slot0 0x41c670 / 字节 81 6C 24 04 C0 06 00 00 E9 13 7C FF FF / jmp 0x414290）'
     '⇒ 正确表述是「83 为主、81 兜底」，不是「统一 83」。**立即数 == COL.mdisp 仍是 101/101**（100/100 + 1/1），且 101/101 的 E9 目标都等于本类主视图 slot0。'
     '**thunk 级常量性（R208 新证）**：100 条 A83 只映射到 **21** 个不同 thunk 地址，每个 thunk 地址的 imm 唯一（21/21）、组内 COL 的 mdisp 也唯一 ⇒ 「立即数 == mdisp」在本镜像是 thunk 级常量的推论，'
     '不是逐 COL 独立决定；若将来出现共享 thunk 而 mdisp 不同的 COL，该等式会失效。'
     '**分母口径警告（本轮实测）**：`.text` 全域字节锚点计数 `83 6C 24 04` = **67** 处、`81 6C 24 04` = **3** 处，与「额外视图 slot0」口径的 100/1 **不可混用**；'
     '81 的另两处 0x41c680 / 0x41c690 不是任何 COL 的 slot0，而是同一 vftable 0x7e2250 的 slot1/slot2（该表前三槽 = 0x41c670 / 0x41c680 / 0x41c690 三连 81 thunk）。'
     '**I 形态（R208 补）**：AircraftClass m=8 视图体内 this 调整是 `add esi,-8`（0x41bc8f，入口 +0x5F），**不是** `lea`；InfantryClass（0x522a8e）/UnitClass（0x74612e）才是 `lea esi,[edi - 8]`（各入口 +0x2E）。'
     '三条函数体互不相同：Aircraft 401 B/135 条指令，Infantry 与 Unit 各 112 B/39 条指令且两者之间也只差 10 处（栈帧 2 / 参数偏移 1 / 字段偏移 1 / 内部跳转 6，无一处落在 this 调整位）。')
data[i29][1]=data[i29][1]+ADD
assert len(data[i29][1].encode())>b_stmt
for k in range(56):
    if k!=i29:
        assert data[k][1:]==rows[k+1][1:], 'row %d mutated'%k
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
sha=hashlib.sha256(out).hexdigest()
chk=list(csv.reader(io.StringIO(open(NEW,'rb').read().decode('utf-8')),delimiter='\t'))
assert len(chk)==57 and [r[0] for r in chk[1:]]==['F%02d'%i for i in range(1,57)] and all(len(r)==5 for r in chk)
assert not [i for i in range(1,57) if chk[i][2]!=rows[i][2]]
assert not [i for i in range(1,57) if chk[i][3]!=rows[i][3]]
print(json.dumps(dict(old=hashlib.sha256(raw).hexdigest(),new=sha,obytes=len(raw),nbytes=len(out),
                      dir=os.path.basename(NEWD),stmt29=b_stmt,stmt29_new=len(data[i29][1].encode()),
                      rows=len(chk)),ensure_ascii=False,indent=1))
