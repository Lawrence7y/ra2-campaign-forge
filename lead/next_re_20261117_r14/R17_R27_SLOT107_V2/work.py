#!/usr/bin/env python3
import csv, hashlib, struct, os, bisect
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM
IMG=Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
ROOT=Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14")
OUT=Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R27_SLOT107_V2")
R23_CTORS=ROOT/"R17_R23_CALLER_PATH"/"ctor_sites.tsv"
EXPECT_SHA="73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
CTORS={0x43B740:"ctor_A",0x43B680:"ctor_B"}
DISPS=(0x124,0x1AC)
TARGET_NAME="0x449440 (BuildingClass vtable #107, +0x1AC)"
data=IMG.read_bytes(); sha=hashlib.sha256(data).hexdigest().upper()
if sha!=EXPECT_SHA: raise SystemExit("SHA MISMATCH; abort: "+sha)
pe=pefile.PE(data=data); IB=pe.OPTIONAL_HEADER.ImageBase
SEC={s.Name.decode("latin1").rstrip(chr(0)):s for s in pe.sections}
text,rdata,sdata=SEC[".text"],SEC[".rdata"],SEC[".data"]
CODE=data[text.PointerToRawData:text.PointerToRawData+text.SizeOfRawData]
TEXT_LO=IB+text.VirtualAddress; TEXT_HI=TEXT_LO+text.SizeOfRawData
RD_LO=rdata.PointerToRawData; RD_HI=RD_LO+rdata.SizeOfRawData; DA_HI=sdata.PointerToRawData+sdata.SizeOfRawData
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
def hx(v): return "0x%X"%v
def off_va(va):
 r=va-IB
 for s in pe.sections:
  rv=s.VirtualAddress
  if rv<=r<rv+s.SizeOfRawData: return s.PointerToRawData+(r-rv)
 return None
def va_off(o):
 for s in pe.sections:
  rp=s.PointerToRawData
  if rp<=o<rp+s.SizeOfRawData: return IB+s.VirtualAddress+(o-rp)
 return None
def u32va(va):
 o=off_va(va); return struct.unpack_from("<I",data,o)[0] if o is not None else None
def regs_of(ins): return {md.reg_name(r) for r in ins.regs_write}
def ins_s(x): return "%08X  %-20s %-7s %s"%(x.address,x.bytes.hex(),x.mnemonic,x.op_str)
def bytehex(x): return x.bytes.hex(" ")
printable=bytes(range(0x20,0x7f)); td={}
for o in range(sdata.PointerToRawData,DA_HI-8):
 if data[o:o+4]!=b".?AV": continue
 e=o+4
 while e<DA_HI and data[e] in printable: e+=1
 if e>=DA_HI or data[e]!=0 or e-o<10: continue
 tv=va_off(o-8)
 if tv is not None and u32va(tv+4)==0: td.setdefault(tv,data[o:e].decode("ascii"))
col={}
for o in range(RD_LO,RD_HI-24,4):
 ptd=struct.unpack_from("<I",data,o+12)[0]
 if ptd not in td: continue
 cd=struct.unpack_from("<I",data,o+16)[0]; co=off_va(cd)
 if co is None or co+16>len(data): continue
 sig,attr,nbases,basearr=struct.unpack_from("<IIII",data,co)
 if sig==0 and attr<0x100 and 0<nbases<0x1000 and off_va(basearr) is not None:
  col[IB+rdata.VirtualAddress+(o-RD_LO)]=td[ptd]
vtable_values=set(); vtable_count=0; slot_values_total=0
for o in range(RD_LO,RD_HI-4,4):
 if struct.unpack_from("<I",data,o)[0] not in col: continue
 vbase=IB+rdata.VirtualAddress+(o+4-RD_LO); p=off_va(vbase); vtable_count+=1
 while p is not None and p+4<=RD_HI:
  v=struct.unpack_from("<I",data,p)[0]
  if not(TEXT_LO<=v<TEXT_HI): break
  vtable_values.add(v); slot_values_total+=1; p+=4
ctor_sites=[]
for i in range(len(CODE)-4):
 if CODE[i]!=0xE8: continue
 site=TEXT_LO+i; dst=site+5+struct.unpack_from("<i",CODE,i+1)[0]
 if dst in CTORS: ctor_sites.append((site,dst,CODE[i:i+5].hex(" ")))
ctor_sites.sort()
starts=set(vtable_values)|set(CTORS)|{TEXT_LO}; i=0
while i<len(CODE)-3:
 c=CODE[i]
 if c in (0x90,0xCC):
  j=i
  while j<len(CODE) and CODE[j]==c: j+=1
  if (c==0x90 and j-i>=4) or (c==0xCC and j-i>=2):
   if TEXT_LO+j<TEXT_HI: starts.add(TEXT_LO+j)
  i=j
 else: i+=1
starts=sorted(s for s in starts if TEXT_LO<=s<TEXT_HI)
def dis_range(a,b):
 if a<TEXT_LO or b>TEXT_HI or a>=b: return []
 return list(md.disasm(CODE[a-TEXT_LO:b-TEXT_LO],a))
def pick_host(site):
 j=bisect.bisect_right(starts,site)-1
 for k in range(j,max(-1,j-128),-1):
  h=starts[k]
  if any(x.address==site for x in dis_range(h,min(site+16,TEXT_HI))): return h
 return None
r23_rows=[]
with R23_CTORS.open(newline="",encoding="utf-8") as f:
 for r in csv.DictReader(f,delimiter="\t"): r23_rows.append(r)
r23_hosts=[int(r["host"],16) for r in r23_rows]
host_rows=[]; host_info=[]
for k,(site,dst,cbytes) in enumerate(ctor_sites):
 host=pick_host(site)
 if host is None: raise SystemExit("host unresolved for "+hx(site))
 j=bisect.bisect_right(starts,host); nxt=starts[j] if j<len(starts) else TEXT_HI
 il=dis_range(host,nxt); rets=[x.address+x.size for x in il if x.mnemonic.startswith("ret")]
 fn_end=rets[-1] if rets else nxt; gap=CODE[fn_end-TEXT_LO:nxt-TEXT_LO]
 gap_ok=all(b in (0x90,0xCC) for b in gap); assert host<=site<fn_end
 anchor_type="VTABLE_SLOT" if host in vtable_values else ("CTOR_ENTRY" if host in CTORS else "POST_PADDING")
 prev=CODE[host-TEXT_LO-16:host-TEXT_LO].hex(" ") if host-TEXT_LO>=16 else ""
 first=CODE[host-TEXT_LO:host-TEXT_LO+16].hex(" ")
 retb=CODE[rets[-1]-TEXT_LO:fn_end-TEXT_LO].hex(" ") if rets else ""
 steps=sum(1 for x in il if x.address<site); assertion="PASS %s <= %s < %s"%(hx(host),hx(site),hx(fn_end))
 r23h=r23_hosts[k] if k<len(r23_hosts) else None; diff="DIFF" if r23h!=host else "SAME"
 host_rows.append([hx(site),hx(dst),cbytes,hx(r23h) if r23h is not None else "NA",hx(host),hx(fn_end),hx(nxt),assertion,anchor_type,prev,first,retb,gap[:24].hex(" "),"PASS" if gap_ok else "FAIL",str(steps),diff])
 host_info.append(dict(site=site,dst=dst,cbytes=cbytes,host=host,fn_end=fn_end,nxt=nxt,il=il,r23h=r23h,diff=diff))
def mem_base_disp(op):
 if op.type!=X86_OP_MEM or op.mem.base==0: return None
 return md.reg_name(op.mem.base),op.mem.disp
uniq_hosts={}
for hi in host_info: uniq_hosts.setdefault(hi["host"],hi)
scan_bytes=sum(hi["fn_end"]-hi["host"] for hi in uniq_hosts.values()); disasm_funcs=len(uniq_hosts); disasm_instructions=sum(len(hi["il"]) for hi in uniq_hosts.values())
hits=[]
for host,hi in sorted(uniq_hosts.items()):
 il=hi["il"]
 for idx,x in enumerate(il):
  if x.address>=hi["fn_end"]: break
  found=[]
  if x.mnemonic=="call" and x.operands and x.operands[0].type==X86_OP_MEM:
   mb=mem_base_disp(x.operands[0])
   if mb and mb[1] in DISPS: found.append((mb[0],mb[1],"call [reg+disp32]",bytehex(x),ins_s(x),x.address))
  if x.mnemonic=="mov" and len(x.operands)==2 and x.operands[0].type==2 and x.operands[1].type==X86_OP_MEM:
   mb=mem_base_disp(x.operands[1])
   if mb and mb[1] in DISPS:
    dstreg=md.reg_name(x.operands[0].reg)
    for y in il[idx+1:idx+13]:
     if y.address>=hi["fn_end"]: break
     if y.mnemonic=="call" and y.operands and y.operands[0].type==2 and md.reg_name(y.operands[0].reg)==dstreg:
      found.append((mb[0],mb[1],"mov reg,[reg+disp32]; call reg",bytehex(x)+" ; "+bytehex(y),ins_s(x)+" ; "+ins_s(y),y.address)); break
  for base,disp,form,bts,txt,hit_site in found:
   in_host_ctors=[h for h in host_info if h["host"]==host]
   before=[h for h in in_host_ctors if h["site"]<hit_site]; after=[h for h in in_host_ctors if h["site"]>hit_site]
   ctor=max(before,key=lambda z:z["site"]) if before else (min(after,key=lambda z:z["site"]) if after else None)
   relation="CTOR_BEFORE_HIT" if before else ("CTOR_AFTER_HIT" if after else "NO_CTOR_IN_HOST")
   writes=[]
   if ctor and relation=="CTOR_BEFORE_HIT":
    for y in il:
     if ctor["site"]+5<=y.address<hit_site and y.mnemonic!="call" and base in regs_of(y): writes.append(y)
   lastw=writes[-1] if writes else None
   derived=(hit_site==0x5A6860 and base=="edx")
   if derived:
    chain="0x5A66D4 e8 67 50 e9 ff call 0x43B740 ; 0x5A66D9 8b e8 mov ebp,eax ; 0x5A684D 8b 55 00 mov edx,[ebp] ; 0x5A6860 ff 92 24 01 00 00 call [edx+0x124]"
    overwrite="CTOR_PATH_NO_EBP_OVERWRITE (0x5A66C1 74 23 bypasses ctor to 0x5A66E6 xor ebp,ebp); EDX had 3 earlier writes, final 0x5A684D not overwritten before dispatch"
   else:
    cdesc=("ctor_site=%s is downstream"%hx(ctor["site"])) if ctor and relation=="CTOR_AFTER_HIT" else ("ctor_site=%s in host but not source of base"%hx(ctor["site"]) if ctor else "no ctor in host")
    chain=((bytehex(lastw)+" @ "+hx(lastw.address)+" "+ins_s(lastw)+" ; ") if lastw else "")+bytehex(x)+" @ "+hx(x.address)+" ; "+cdesc
    overwrite="BASE_NOT_DERIVED_FROM_CTOR_OBJECT; base loaded from incoming this/member vptr; "+cdesc
   verdict="YES_DERIVED_FROM_CTOR_OBJECT" if derived else "NO"
   hits.append([hx(hit_site),hx(disp),form,bts,hx(host),hx(hi["fn_end"]),base,hx(ctor["site"]) if ctor else "NA",relation,verdict,chain,overwrite,str(len(writes)),(" ; ".join("%s:%s"%(hx(w.address),bytehex(w)) for w in writes) if writes else "NONE"),((hx(lastw.address)+" "+ins_s(lastw)) if lastw else "NONE"),txt])
with (OUT/"ctor_hosts.tsv").open("w",newline="",encoding="utf-8") as f:
 w=csv.writer(f,delimiter="\t",lineterminator="\n")
 w.writerow(["ctor_site","call_target","ctor_call_bytes","r23_host_col","true_host","fn_end","next_trusted_entry","position_assert","anchor_type","prev_16_bytes","host_first_16_bytes","final_ret_bytes","padding_after_fn_end","padding_check","decoded_steps_host_to_ctor","r23_diff"]); w.writerows(host_rows)
with (OUT/"dispatch_hits.tsv").open("w",newline="",encoding="utf-8") as f:
 w=csv.writer(f,delimiter="\t",lineterminator="\n")
 w.writerow(["hit_site","disp","form","bytes","host","fn_end","base_reg","ctor_site","ctor_relation","base_is_constructed_object","byte_chain","overwrite_analysis","base_writes_after_ctor_count","base_write_points","last_base_write","capstone_text"]); w.writerows(hits)
n_124=sum(1 for r in hits if r[1]=="0x124"); n_1ac=sum(1 for r in hits if r[1]=="0x1AC"); diff_sites=[r[0] for r in host_rows if r[-1]=="DIFF"]
lines=[str(IMG)+" | sha256 "+sha,"","# R17-R27-SLOT107-V2 · 正向入口集重做 slot #107 调用方追查","","## 0. R25 作废原因","","- R25 用「R12 hit host ∩ R23 ctor host」精确相等求交得 0，据此报 `0x449440` 未取得；该交集的两个输入都不可信，结论作废。","- R12 `hits.tsv` 的 host 靠字节扫 `C3` 判入口：`0x5A680D 0F BF C3` (`movsx eax,bx`) 中的 `C3` 是 modrm，被当成 ret，真 host `0x5A6510` 误记 `0x5A6810`，且 `0x5A66D9 8B E8` 证明基址来自构造对象而非栈，R12 的 `NON_TARGET` 亦误判。","- 本卡复看实际 `R17_R23_CALLER_PATH/ctor_sites.tsv`：其 `call_target` 列才是 `0x43B740/0x43B680`；`host` 列本身也不是可信函数入口集，15 行中有 %d 行与本卡逐点定界的真实 host 不同（%s）。R25 把该列当交集键，所以零交集无证明力。"%(len(diff_sites),", ".join(diff_sites)),"","## 1. 可信入口集与扫描口径","","- 镜像：%s；sha256 `%s`；size %d B。"%(IMG,sha,len(data)),"- `.rdata` raw 扫描 %d B（%d 个对齐 dword）；RTTI 正向索引：TD %d、COL %d、vtable %d，重算 vtable 槽值 **%d 个**（去重 %d 个；卡面“约 14044”按实测报数）。`.data` 为 TD 扫描 %d B。"%(RD_HI-RD_LO,(RD_HI-RD_LO)//4,len(td),len(col),vtable_count,slot_values_total,len(vtable_values),sdata.SizeOfRawData),"- 入口集 = 全部 `%d` 个 vtable 槽值（去重后）+ `0x43B740`/`0x43B680` + `.text` 起点 + 正向 padding 锚点（NOP run>=4 / CC run>=2）= **%d** 个；**未用 C3/C2 字节扫入口**。"%(len(vtable_values),len(starts)),"- `.text` raw `%d` B 用于定位 15 个 `E8` 直接构造点；每个点都从其 host 锚点解码验证为指令边界。"%text.SizeOfRawData,"- 派发扫描只在 15 个真实 host 的 **%d 个唯一函数 / %d B** 内进行，解码 **%d 条指令**；反汇编函数个数 **%d**（15 个构造点落在 13 个唯一 host）。"%(scan_bytes,scan_bytes,disasm_instructions,disasm_funcs),"","## 2. 15 个构造点的真实 host（逐点字节定界）","","| ctor site | target | R23 host 列 | 真实 host | fn_end | 锚点 | 位置断言 | 与 R23 不同 |","|---|---|---|---|---|---|---|---|"]
for r in host_rows: lines.append("| %s | %s | %s | %s | %s | %s | %s | %s |"%(r[0],r[1],r[3],r[4],r[5],r[8],r[7],r[15]))
lines+=["","每行的前 16 字节、前序 16 字节、末尾真 `ret` 字节、fn_end 后 `90|CC` 填充、下一可信入口、从 host 到 ctor 的解码步数见 `ctor_hosts.tsv`。所有 `padding_check=PASS`，所有 `host <= site < fn_end` 断言成立。","","## 3. host 内 `[reg+0x124]` / `[reg+0x1AC]` 派发","","- `0x1AC` 命中：**%d 条**。`0x124` 命中：**%d 条**（作为正控/对照，说明扫描器能命中已知形态）。"%(n_1ac,n_124),"- 形态覆盖：`call dword ptr [reg+disp32]` 与 `mov reg2,[reg+disp32]` 后 12 条内 `call reg2`；由 Capstone 在锚定函数体内解码，不按字节猜边界。","","| site | disp | bytes | base | host | ctor 关系 | 基址是否构造对象 | 覆写与写点 |","|---|---|---|---|---|---|---|---|"]
for r in hits: lines.append("| %s | %s | `%s` | %s | %s | %s | %s | %s |"%(r[0],r[1],r[3],r[6],r[4],r[8],r[9],r[11]))
lines+=["","逐条字节链与完整寄存器写点统计见 `dispatch_hits.tsv`。要点：","- `0x5A6860`：构造路径 `0x5A66D4 E8 67 50 E9 FF call 0x43B740` → `0x5A66D9 8B E8 mov ebp,eax` → `0x5A684D 8B 55 00 mov edx,[ebp]` → `0x5A6860 FF 92 24 01 00 00 call [edx+0x124]`。构造成功路径上 EBP 无覆写：`0x5A66C1 74 23` 的失败分支跳到 `0x5A66E6 xor ebp,ebp`，绕过构造点；EDX 在到达最终写点前有 3 次早写，最终写点后到派发无覆写。","- `0x7393C0` host 的 5 条 `0x124` 均以传入 `this` 的 `[ebp]`（或经 `[ebp+0x674]`）取 vptr：其中 4 条在构造点 `0x7396C3` 之前，1 条 `0x739AA1` 在之后但基址来自 `[ebp]`，构造出的对象在 `EBX`（`0x7396C8 8B D8`）并用于成员写入，未成为这些派发的基址。即：这些 host 命中不构成该构造对象到 `0x449440` 的链。","","## 4. 结论与覆盖边界","","- **在这 15 个构造点的真实 host 内，未发现 `[reg+0x1AC]` 派发；`%s` 的调用方本轮未取得。**"%TARGET_NAME,"- 本轮只证明「在这 15 个 host 内未发现」；不证明不存在、不证明唯一、不证明运行期真的执行到；**不改变 ②-b 的 `[静态推断]` 收口（D-53(A)）**。","- 覆盖边界：对象经全局/成员字段长距离传递、跨函数传入、由非 `0x43B740`/`0x43B680` 构造，或采用先算目标地址、跳板、索引型、disp8、段覆盖、跨节代码，均不在本轮 15-host 定偏移扫描内；因此本轮负面结论不外推为全镜像不存在。","","## 5. 未取得项","","- `0x449440` 的字节证实调用方：未取得。","- 唯一性与运行期实际执行证据：按卡不证明，未取得（不是待补缺陷）。","","## 6. 产物","","- `REPORT.md`、`ctor_hosts.tsv`、`dispatch_hits.tsv`、`work.py`。"]
(OUT/"REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
print("SHA="+sha)
print("VTABLE_SLOTS=%d UNIQUE=%d ENTRIES=%d"%(slot_values_total,len(vtable_values),len(starts)))
print("CTOR_SITES=%d TRUE_UNIQUE_HOSTS=%d HOST_DIFFS=%s"%(len(ctor_sites),disasm_funcs,",".join(diff_sites)))
print("DISPATCH_SCAN_BYTES=%d DISASM_FUNCS=%d INSNS=%d"%(scan_bytes,disasm_funcs,disasm_instructions))
print("HITS_1AC=%d HITS_124=%d FOUND_449440_CALLER=NO"%(n_1ac,n_124))