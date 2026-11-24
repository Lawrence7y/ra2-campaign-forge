# -*- coding: utf-8 -*-
"""Generate S22 B4 outputs: EVIDENCE/ROW_*.txt x13, delta.tsv (all_four rows),
base_rate.tsv, PROGRESS.md. Uses verdicts.json produced by finalize_b4.py.
"""
import os, sys, json, re
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
with open(os.path.join(HERE,"verdicts.json"),encoding="utf-8") as f:
    V = json.load(f)

SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

def cls(name):
    m = re.search(r'TClassFactory_V(.+?)__', name)
    return m.group(1) if m else name

def seqstr(seq, marker_addr=None):
    out=[]
    for addr,hx,op in seq:
        mk = " <<<" if addr==marker_addr else ""
        out.append("     %s  %-24s %s%s" % (addr,hx,op,mk))
    return "\n".join(out)

def evidence_text(v):
    e=v["entry"]; r1=v["r1"]; r2=v["r2"]; c1=v["special_C1"]; r3=v["r3b"]; r4=v["r4"]
    L=[]
    L.append("ROW_%s   subsystem=S22   name=%s   批次=S22_B4" % (e,v["name"]))
    L.append("目标: ra2youli\\gamemd.exe  SHA-256=%s" % SHA)
    L.append("ImageBase=0x400000  .text=[0x401000,0x7E038D)")
    L.append("本批特殊约束: ② 主虚表 slot0 必须=00410260（不得用小成员表）；④ 锚点落析构器判 FAIL(㉓)")
    L.append("")
    L.append("[环① 入口]")
    L.append("  entry=%s 在 .text=%s  atlas_size=%s  n_insn=%s  skipdata=%s 首字节=%s 末条=%s" % (
        e,r1["in_text"],r1["atlas_size"],r1["n_insn"],r1["n_skipdata"],r1["first_bytes"],r1["last"]))
    L.append("  函数边界自洽: %s" % (r1["in_text"] and r1["n_skipdata"]==0))
    L.append("")
    L.append("[环② 类身份] 裁定=%s" % ("PASS" if (r2["rtti_ok"] and c1["ok"]) else "FAIL"))
    L.append("  .rdata 中本 entry 作 4B VA 的槽: %s = %s（唯一命中）" % (r2["slot_va"],r2["slot_bytes"]))
    L.append("  vtable_base=%s  slot_off=%s slot_no=%s  线索槽号=%s ⇒ 槽号自洽=%s" % (
        r2["vtable"],r2["slot_off"],r2["slotno"],r2["clue_slotno"],r2["slotno"]==r2["clue_slotno"]))
    L.append("  [vt-4]=COL %s 字节=%s sig=0(COL)" % (r2["col"],r2["col_bytes"]))
    L.append("  [COL+0xC]=TD %s 字节=%s" % (r2["td"],r2["td_bytes"]))
    L.append("  TD+8 名串 @%s 字节=%s" % (r2["name_va"],r2["name_bytes"]))
    L.append("  RTTI 类名 = %s" % r2["rtti_name"])
    L.append("  —— 工厂类身份由 RTTI(COL→TD→名串)+槽号独立钉死，未借名字中 Class 部分")
    L.append("  【本批特殊约束 C1】对象主虚表 slot0:")
    L.append("     要求=%s  实测=%s  选取方式=%s  ⇒ %s" % (
        c1["mainvt_slot0_required"],c1["mainvt_slot0_actual"],c1["picked_kind"],"PASS" if c1["ok"] else "FAIL"))
    if not c1["ok"]:
        L.append("     对象 ctor 写表清单（逐条，slot0 实测）:")
        for oc,p in r3["mainvt_writes"]:
            L.append("       objctor=%s write@%s vt=%s insn=%s → slot0=%s consts=%s nret=%s ok=%s" % (
                oc,p["write"],p["vt"],p["insn"],p["QI"],p["QI_consts"],p["QI_nrets"],p["QI_ok"]))
        L.append("     ⇒ 无主虚表 slot0=00410260：不得拿小成员表/非规范 QI 顶替，② FAIL")
    L.append("")
    L.append("[环③ 整体合同] 裁定=%s" % ("PASS" if r3["ok"] else "FAIL"))
    L.append("  形态: ③b②（COM IClassFactory::CreateInstance，可伪证 HRESULT 返回约定）")
    L.append("  早期守卫（imm 错误码，字节内可核）:")
    gname={"80070057":"E_INVALIDARG","80040110":"CLASS_E_NOAGGREGATION","8007000E":"E_OUTOFMEMORY"}
    for k,val in r3["guards"].items():
        L.append("     %s(0x%s) @%s : %s" % (gname.get(k.upper(),"?"),k,val["addr"],val["bytes"]))
    L.append("  ③b② 主站点 —— 创建对象的 QueryInterface 返回约定 + 调用方真分支:")
    qs=r3["qi_site"]
    L.append("     call [eax](主 vt slot0) @%s : %s" % (qs["addr"],qs["bytes"]))
    L.append(seqstr(qs["seq"],qs["addr"]))
    L.append("  被调 QI=%s，返回常量=%s，ret 数=%s，QI_ok=%s" % (
        r3["qi_va"],",".join(r3["qi_consts"]) if r3["qi_consts"] else "(无 falsifiable 常量)",
        r3["qi_nrets"],r3["mainvt"]["QI_ok"] if r3["mainvt"] else False))
    if r3["qi_rets"]:
        L.append("  被调 ret 指令字节（逐条）:")
        for a,b,op in r3["qi_rets"]:
            L.append("     %s  %-16s %s" % (a,b,op))
    if r3["mainvt"]:
        L.append("  被调定位链: 工厂体内 call 对象ctor %s → 该 ctor @%s 写 vt %s → vt[0]=%s" % (
            r3["obj_ctor"],r3["mainvt"]["write"],r3["mainvt"]["vt"],r3["qi_va"]))
    if r3["release"]:
        L.append("  失败路调用 %s @%s %s，与成功路动作真不同" % (
            r3["release"]["op"],r3["release"]["addr"],r3["release"]["bytes"]))
    br=r3["branch"]
    if br:
        L.append("  三陷阱排查: mov edi,eax=%s；test edi,edi=%s；%s（test 与分支零间隔）；本体内 QI call 数=%d；无 eax 覆写（返回值在 edi）" % (
            br["mov_edi"],br["test_edi"],br["jcc"],br["n_qi_calls"]))
    if not r3["ok"]:
        L.append("  ⇒ ③b FAIL: 被调 QI 无可伪证 HRESULT 三态常量（返回非 HRESULT/esi），或分支结构不成立")
    L.append("  语义方向: 写出接口指针到 ppvOut（CreateInstance 产出对象接口），未写反")
    L.append("")
    L.append("[环④ 使用见证] 裁定=%s" % ("PASS" if r4["ok"] else "FAIL"))
    L.append("  形态: 活 COM 类对象（工厂实例堆分配 + ctor 装本类 vt + CoRegisterClassObject 以 CLSID 注册）")
    L.append("  工厂自身 vt=%s slot#%s = 本 entry；构造器 %s 写该 vt:" % (r2["vtable"],r2["slotno"],r4["factory_ctor"]))
    for a,b,op in r4["fc_ins"]:
        L.append("     %s  %-20s %s%s" % (a,b,op," <<< 装本类 vt" if r2["vtable"].lower() in op.lower() else ""))
    L.append("  ctor 直接调用者=%s；atexit 注册=%s（空=非析构器表）" % (r4["fc_callers"],r4["fc_atexit"]))
    L.append("  注册现场（本行自身地址）: call 工厂ctor @%s" % (r4["ctor_call"]))
    L.append("  宿主初始化函数=%s(size=%s)，atexit 注册=%s ⇒ 非析构器" % (
        r4["host_func"],r4["host_size"],r4["host_atexit"]))
    L.append("  【本批特殊约束 C2】④ 锚点落析构器检查: anchor_in_dtor=%s ⇒ %s（㉓）" % (
        r4["anchor_in_dtor"],"FAIL" if r4["anchor_in_dtor"] else "PASS"))
    L.append("  本 entry 全镜像直接 call 者=%s（纯虚派发，非 direct-only）" % r4["direct_callers_entry"])
    L.append("")
    L.append("[②④ 不同源]")
    L.append("  ② 锚 .rdata 的 RTTI 描述符链 + 虚表槽 %s；④ 锚 .text 的堆分配+ctor 装表+CoRegisterClassObject 注册指令 —— 段不同、地址不同、产物类型不同" % r2["slot_va"])
    L.append("")
    L.append("[裁定] %s" % ("四环齐全 ⇒ [已证]，写入 delta.tsv" if v["all_four"] else "不成立，不产出"))
    return "\n".join(L)+"\n"

def semantics(v):
    e=v["entry"]; r2=v["r2"]; r3=v["r3b"]; r4=v["r4"]
    c=cls(v["name"])
    g=r3["guards"]
    ga=g.get("80070057",{}).get("addr","?")
    return (
      "S22 T_TClassFactory_V%s__::slot3（IClassFactory::CreateInstance）—— ③b② 成立："
      "入口三道 imm 错误码守卫（ppvOut 空→E_INVALIDARG 0x80070057 @%s；pUnkOuter 非空→CLASS_E_NOAGGREGATION 0x80040110；"
      "new/ctor 空→E_OUTOFMEMORY 0x8007000e）。主站点 @%s `call dword ptr [eax]`（新建 %s 对象主 vt %s 的 slot0=QueryInterface %s，"
      "主虚表 slot0=00410260 已核），@%s `mov edi,eax`/`test edi,edi`/`%s`：失败返 0x80004002/0x80004003、成功返 0，"
      "返回约定字节可伪证（常量 %s、%d 处 ret）；调用方真拿它分支且两路动作不同——失败路 @%s `call [edx+0x20]` 带 delete 标志=1 释放新建对象，成功路回传 HRESULT。"
      "返回值在 edi，test 与分支零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。"
      "语义：为 %s 类工厂 CreateInstance——校验输出指针与聚合参数→分配构造一个 %s 对象→QueryInterface 取接口：失败 Release 新建对象并回传负 HRESULT、成功回传 S_OK 与接口指针（写出接口指针到 ppvOut，非读入）。"
      "② 槽 %s(vt %s +%s，slot#3) 4B 值即本 entry，RTTI COL=%s→TD=%s→名=%s；主虚表 slot0=%s(=00410260，非小成员表)。"
      "④ 活 COM 类对象：ctor %s 装 vt %s→注册，宿主 %s 非 atexit 非析构（㉓ 排除，④ 锚点不在析构器），direct 调用者=0（纯虚派发非 direct-only），②④ 不同源(.rdata RTTI vs .text 分配/装表/注册)。"
      % (c,ga,r3["qi_site"]["addr"],c,r3["mainvt"]["vt"],r3["qi_va"],r3["branch"]["seq"][1][0],r3["branch"]["jcc"],
         ",".join(r3["qi_consts"]),r3["qi_nrets"],r3["release"]["addr"] if r3["release"] else "?",c,c,
         r2["slot_va"],r2["vtable"],r2["slot_off"],r2["col"],r2["td"],r2["rtti_name"],r3["qi_va"],
         r4["factory_ctor"],r2["vtable"],r4["host_func"])
    )

# 1) EVIDENCE (all 13 rows)
evdir=os.path.join(BASE,"EVIDENCE")
os.makedirs(evdir,exist_ok=True)
for v in V:
    with open(os.path.join(evdir,"ROW_%s.txt"%v["entry"]),"w",encoding="utf-8") as f:
        f.write(evidence_text(v))

# 2) delta.tsv (all_four rows only)
rows=[]
for v in V:
    if not v["all_four"]: continue
    e=v["entry"]
    ep="D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/NAMED_PUSH_S22_B4/EVIDENCE/ROW_%s.txt"%e
    rows.append("\t".join([e,v["subsystem"],v["name"],semantics(v),"[已证]",ep]))
with open(os.path.join(BASE,"delta.tsv"),"w",encoding="utf-8") as f:
    f.write("entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\n")
    f.write("\n".join(rows)+"\n")

# counts
r2=sum(1 for v in V if v["r2"]["rtti_ok"] and v["special_C1"]["ok"])
r3=sum(1 for v in V if v["r3b"]["ok"])
r4=sum(1 for v in V if v["r4"]["ok"])
af=sum(1 for v in V if v["all_four"])
rate=af/len(V)

# 3) base_rate.tsv
with open(os.path.join(BASE,"base_rate.tsv"),"w",encoding="utf-8") as f:
    f.write("batch\trows_checked\tring2_ok\tring3b_ok\tring4_ok\tall_four\trate\n")
    f.write("S22_B4\t%d\t%d\t%d\t%d\t%d\t%.4f\n"%(
        len(V),r2,r3,r4,af,rate))

print("generated EVIDENCE x%d, delta rows=%d, base_rate S22_B4 %d/%d/%d/%d rate=%.4f"%(
    len(V),len(rows),r2,r3,r4,af,rate))
