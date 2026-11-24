from pathlib import Path
import hashlib, struct

MIRROR=Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
INDEX=Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R15_SLOT73\class_index.tsv")
COVERAGE=Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
OUT=Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R17_SLOT73_MAP")
BASE=0x400000
TARGETS=[0x43F180,0x449440,0x4D3780,0x6F4A70]
FOUR=[".?AVAircraftClass@@",".?AVFootClass@@",".?AVInfantryClass@@",".?AVUnitClass@@"]
EXTERNAL=[(0x7E22A4,0x7E23C8),(0x7E8C94,0x7E8DB8),(0x7EB058,0x7EB17C),(0x7F5C70,0x7F5D94)]
BT=chr(96); FENCE=BT*3

data=MIRROR.read_bytes(); sha=hashlib.sha256(data).hexdigest().upper()
if not sha.startswith("73201CC0"): raise SystemExit("sha mismatch: "+sha)
pe=struct.unpack_from("<I",data,0x3C)[0]
nsec=struct.unpack_from("<H",data,pe+6)[0]; optsz=struct.unpack_from("<H",data,pe+20)[0]
secs=[]
for i in range(nsec):
 o=pe+24+optsz+i*40; name=data[o:o+8].rstrip(b"\0").decode("ascii")
 vs,rva,rs,raw=struct.unpack_from("<IIII",data,o+8); secs.append((name,rva,rs,raw))
name,RR,RS,RAW=next(s for s in secs if s[0]==".rdata")
def u32(va):
 r=va-BASE
 if not (RR<=r and r+4<=RR+RS): raise ValueError("outside .rdata: "+hex(va))
 return struct.unpack_from("<I",data,RAW+r-RR)[0]
def H(v): return "0x%08X"%v
def Q(v): return BT+str(v)+BT

rows=[]
with INDEX.open(encoding="utf-8") as f:
 next(f)
 for line in f:
  if not line.strip(): continue
  c,v,n,m=line.rstrip("\n").split("\t"); rows.append((c,int(v,16),int(n),m))
sel=sorted([r for r in rows if r[2]>=108],key=lambda r:(r[1],r[0]))
rec=[]
for c,v,n,m in sel:
 rec += [(u32(v+73*4),c,v,73),(u32(v+107*4),c,v,107)]
rec.sort(key=lambda r:(r[0],r[3],r[2],r[1]))
groups={}
for val,c,v,s in rec: groups.setdefault(val,[]).append((c,v,s))

with (OUT/"reverse_map.tsv").open("w",encoding="utf-8",newline="\n") as f:
 f.write("function_value\tclass_name\tvtable_va\tslot\n")
 for val,c,v,s in rec: f.write("%s\t%s\t%s\t%d\n"%(H(val),c,H(v),s))

four=[]
for c in FOUR:
 ms=[r for r in sel if r[0]==c and r[3]=="yes"]
 if len(ms)!=1: raise SystemExit("main not unique: "+c)
 _,v,n,_=ms[0]; four.append((c,v,n,u32(v+73*4),u32(v+107*4),v+0x124))
with (OUT/"four_classes.tsv").open("w",encoding="utf-8",newline="\n") as f:
 f.write("class_name\tmain_vtable\tslot_count\tslot_73\tslot_107\tmain_plus_0x124\n")
 for c,v,n,a,b,p in four: f.write("%s\t%s\t%d\t%s\t%s\t%s\n"%(c,H(v),n,H(a),H(b),H(p)))

cov="未取得"
for line in COVERAGE.read_text(encoding="utf-8",errors="replace").splitlines():
 if line.split("\t",1)[0].upper()=="004D3780": cov=line; break

def hits(val):
 hs=groups.get(val,[])
 return "无命中" if not hs else "<br>".join("%s @ %s 槽%d"%(c,H(v),s) for c,v,s in hs)
def groupblock(val):
 hs=groups.get(val,[]); return "### "+Q(H(val))+"（"+str(len(hs))+" 项）\n"+"\n".join("- "+Q(c)+" @ "+Q(H(v))+" 槽 "+str(s) for c,v,s in hs)

q1=["| 函数值 | 命中数 | 完整反向清单（类名来自索引） |","|---|---:|---|"]
for t in TARGETS: q1.append("| "+Q(H(t))+" | "+str(len(groups.get(t,[])))+" | "+hits(t)+" |")
allgroups=[]
for val in sorted(groups): allgroups += [groupblock(val),""]
q2=["| 类名 | 主 vtable | 槽数 | #73 | #107 | 主vtable+0x124 |","|---|---:|---:|---:|---:|---:|"]
for c,v,n,a,b,p in four: q2.append("| "+Q(c)+" | "+Q(H(v))+" | "+str(n)+" | "+Q(H(a))+" | "+Q(H(b))+" | "+Q(H(p))+" |")
q3=["| 类名 | 算式 | 外部地址 | 是否相等 |","|---|---|---:|---|"]
all_eq=True
for (c,v,n,a,b,p),(vb,ext) in zip(four,EXTERNAL):
 if v!=vb: raise SystemExit("base mismatch")
 ok=(p==ext); all_eq=all_eq and ok
 q3.append("| "+Q(c)+" | "+Q(H(v))+" + 0x124 = "+Q(H(p))+" | "+Q(H(ext))+" | "+("相等" if ok else "不相等")+" |")

only=groups.get(0x43F180,[]); shared=groups.get(0x4D3780,[])
if len(only)!=1 or only[0][0]!=".?AVBuildingClass@@" or only[0][2]!=73: raise SystemExit("43F180 check failed")
if sorted((c,s) for c,v,s in shared)!=sorted((c,73) for c in FOUR): raise SystemExit("4D3780 check failed")
quote=("在本次索引覆盖且槽数≥108的21个主vtable中，槽73上："+Q(".?AVBuildingClass@@")+" 使用 "+Q("0x0043F180")+"，"+Q(".?AVTechnoClass@@")+" 使用 "+Q("0x006F4A70")+"，"+Q(".?AVAircraftClass@@")+"、"+Q(".?AVFootClass@@")+"、"+Q(".?AVInfantryClass@@")+"、"+Q(".?AVUnitClass@@")+" 共用 "+Q("0x004D3780")+"。")
R=[]
R += [str(MIRROR)+" | sha256 "+sha,"","# R17-R17-SLOT73-MAP · 报告","","## 范围与读取",""]
R += ["- SHA256 前缀 "+Q(sha[:8])+" 与期望 "+Q("73201CC0")+" 一致。"]
R += ["- 类名只读沿用 "+Q("R17_R15_SLOT73\\class_index.tsv")+"；本次未修改该目录。"]
R += ["- 索引中槽数≥108的vtable共 "+Q(str(len(sel)))+" 个；槽#73/#107共 "+Q(str(len(rec)))+" 个4字节值 = "+Q(str(len(rec)*4))+" bytes。"]
R += ["- 槽值数据读取限于 "+Q(".rdata")+"：RVA "+Q(H(RR))+"，raw字节数 "+Q(str(RS))+"；所有槽地址均落在该节。整文件sha256只用于身份校验。"]
R += ["- 不建进程、不调试、不启动gamemd；未做大范围反汇编。",""]
R += ["## Q1 · 全量反向映射",""]
R += [str(len(rec))+"/"+str(len(rec))+" 个槽读取均有值；按值分成 "+str(len(groups))+" 组。四个指定函数完整清单：",""]
R += q1 + ["","### 全部值分组",""] + allgroups
R += ["## Q2 · FootClass 补齐与四类并排",""]
R += [Q(".?AVFootClass@@")+" 主vtable "+Q("0x007E8C94")+"（341槽）：**#73 = "+Q("0x004D3780")+"；#107 = "+Q("0x004D9C10")+"**。",""]
R += q2 + ["","## Q3 · 与外部线索对账",""]
R += ["外部线索 "+str(COVERAGE)+"：",FENCE+"text",cov,FENCE,""]
R += q3 + ["", "结论：**外部线索与本次独立字节分析一致**。" if all_eq else "结论：存在差异，见上表。",""]
R += ["## Q4 · 结论措辞",""]
R += ["1. "+Q("0x0043F180")+" 仅命中 "+Q(".?AVBuildingClass@@")+" 主表#73；"+Q("0x00449440")+" 命中该主表#107。"]
R += ["2. "+Q("0x004D3780")+" 仅命中 "+Q(".?AVAircraftClass@@")+"、"+Q(".?AVFootClass@@")+"、"+Q(".?AVInfantryClass@@")+"、"+Q(".?AVUnitClass@@")+" 主表#73，各1项；其余类没有命中。"]
R += ["3. 可直接引用：**"+quote+"**",""]
R += ["> 类名逐字取自索引；索引未给出则写“未取得”。适用范围限于本次索引覆盖且槽数≥108的vtable。",""]
R += ["## 产物","", "- "+Q("REPORT.md"),"- "+Q("reverse_map.tsv"),"- "+Q("four_classes.tsv"),"- "+Q("work.py")]
with (OUT/"REPORT.md").open("w",encoding="utf-8",newline="\n") as f: f.write("\n".join(R))
print("sha="+sha); print("selected=%d slots=%d groups=%d"%(len(sel),len(rec),len(groups)))
for t in TARGETS: print("%s=%d"%(H(t),len(groups.get(t,[]))))
for row in four: print("four "+row[0]+" "+H(row[1])+" "+str(row[2])+" "+H(row[3])+" "+H(row[4])+" "+H(row[5]))
print("all_equal="+str(all_eq))
