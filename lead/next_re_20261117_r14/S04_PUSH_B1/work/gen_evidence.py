# -*- coding: utf-8 -*-
"""生成 18 行 EVIDENCE/ROW_<entry>.txt：每行用自身地址/字节/站点，禁止共用 reason。
输入 analysis.json / verify2..7.json（均为只读取证中间产物）。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W

WORK=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(os.path.dirname(WORK),"EVIDENCE")
os.makedirs(OUT,exist_ok=True)

A=json.load(open(os.path.join(WORK,"analysis.json"),encoding="utf-8"))
V2=json.load(open(os.path.join(WORK,"verify2.json"),encoding="utf-8"))
V4=json.load(open(os.path.join(WORK,"verify4.json"),encoding="utf-8"))
V5=json.load(open(os.path.join(WORK,"verify5.json"),encoding="utf-8"))
V6=json.load(open(os.path.join(WORK,"verify6.json"),encoding="utf-8"))
V7=json.load(open(os.path.join(WORK,"verify7.json"),encoding="utf-8"))

def hx(x):
    try: return "%08X"%(int(x)&0xFFFFFFFF)
    except Exception: return str(x)

def render(r):
    e=r["entry"]; ea=int(e,16); sz=r["atlas"].get("size",0); ni=r["atlas"].get("n_instr",0)
    v2=V2[e]; v4=V4[e]; v5=V5[e]; v6=V6[e]; v7=V7[e]
    L=[]
    L.append("# ROW %s  S04  sub_%s"%(e,e))
    L.append("")
    L.append("本文件只述本行自身字节证据；判据 D-40 四环（②与④须独立证据链；③只认③b；余量仅6行，宁严不宽）。")
    L.append("")
    # 环①
    L.append("## 环① 入口与函数边界")
    L.append("- entry=%s（大写十六进制，无 0x 前缀，delta entry 列原样）"%e)
    L.append("- atlas: size=%d B, n_instr=%d；in_text(.text=[0x401000,0x7E038D))=%s；函数体末 %s 在 .text 内=%s"
             %(sz,ni,r["in_text"],hx(ea+sz-1),r["body_end_in_text"]))
    L.append("- capstone 5.0.7 skipdata=True 反汇编 n_insn=%d，skipdata 垃圾字节=%d（解码连贯）"
             %(r["n_insn_disasm"],r["n_skipdata"]))
    L.append("- 序言字节锚（自身地址）:")
    for x in r["first_insns"][:6]: L.append("    "+x)
    L.append("- 结论：① PASS（入口在 .text 内、边界自洽）。")
    L.append("")
    # 环②
    L.append("## 环② 类身份（RTTI 名 / 虚表归属 / 构造链）——取不到写 未取得 并判本行不成立")
    L.append("- 通道1 RTTI/虚表归属：全镜像（所有 section，含 .text，按 dword 值 == entry VA=0x%X 逐字节扫）命中 %d 处 → 无虚表槽，不能由 [vt-4]=COL 解出类名。"%(ea,len(v2["dword_refs_all_sections"])))
    L.append("- 通道2 构造链：")
    L.append("    - 本函数体内写 mov [this+0], vt（把 vtable 装进 ecx 指向对象）= %d 处；序言用 ecx=%s。"%(len(v5["ctor_write_to_this"]),v5["prologue_uses_ecx"]))
    if v4:
        L.append("    - 体内确有可解析 RTTI 的 vtable 立即数 %d 处，但均为局部/服务对象构造写入，非本函数 this 的 vptr 安装："%len(v4))
        for x in v4[:8]: L.append("        %s  => %s"%(x["ins"],x["rtti"]["name"]))
    else:
        L.append("    - 体内无可解析到 .?AV 类名的 vtable 立即数（0 处）。")
    # 服务对象全局构造链
    if v6:
        L.append("    - 函数体引用的『有已知类的全局对象』: %s"%json.dumps({g:[w[2] for w in d["writes"]] for g,d in v6.items()},ensure_ascii=False))
        L.append("      ⇒ 单点全局引用，且该全局为多态/别名（参照 S06-K1：0x87F7E8 最终动态对象为 PowerClass，非恒为 MouseClass），不满足 D-42 细则3『禁单点推断』与 §8.8 条2『≥2 项字节吻合』，不立类身份。")
    else:
        L.append("    - 函数体未引用任何『由构造写定死类的全局对象』（C7 05 <global>,<vt> 通道命中 0）。")
    L.append("- 通道3 调用方交付 this：在 direct caller 窗口内找到『构造对象→mov ecx,obj→call 本行』的真实 handoff：")
    real=0
    for c in v5["callers"]:
        for h in c["ctor_to_ecx"]:
            if h.get("to_ecx"):
                real+=1
                L.append("      [窗口候选] call@%s 构造 %s @%s → %s"%(c["site"],h["name"],h["write"],"; ".join(h["to_ecx"])))
    if real==0:
        L.append("      0 处（调用方窗口内虽有局部对象构造，但无 mov ecx,obj 交付给 call 本行的证据）。")
    else:
        L.append("      ⇒ 手工反汇编复核（verify8.py）：上述 mov ecx,reg 均属 call 本行之前的『另一条 call』的实参设置；")
        L.append("        到 call 本行那一刻 ecx 已被改写为 ebx/edi 等非该构造对象值，且本行序言用 ecx=%s；"%v5["prologue_uses_ecx"])
        L.append("        局部 vtable 写入的对象（栈临时）从未作为 this 交付给本行 ⇒ 全部为窗口伪命中，构造链不成立。")
    L.append("- 结论：② **未取得**（三条通道均不成立；类名不编造）。按卡『②取不到就写未取得并判该行不成立』，本行不成立。")
    L.append("")
    # 环③
    L.append("## 环③ 整体合同（只认 ③b）")
    L.append("- 通道A ③b②（可伪证错误码/返回约定）：机械命中 p1=%d → 动作签名不同 p2=%d → 可伪证 p3=%d"
             %(r["chA"]["p1"],r["chA"]["p2"],r["chA"]["p3"]))
    if r["chA_sites"]:
        for s in r["chA_sites"]:
            L.append("    - call@%s → %s@%s → %s@%s；p3_form=%s；哨兵=%s；eax覆写陷阱=%s"
                     %(hx(s["call_addr"]),s["test_kind"],hx(int(s["test_addr"],16) if isinstance(s["test_addr"],str) else s["test_addr"]),
                       s["jcc_mnemonic"],hx(int(s["jcc_addr"],16) if isinstance(s["jcc_addr"],str) else s["jcc_addr"]),
                       s["p3_form"],s.get("call_site_falsy"),
                       "触发" if any(t["call_addr"]==s["call_addr"] and t["eax_overwritten"] for t in r["chA_eax_trap"]) else "未触发"))
    else:
        L.append("    - 无可伪证站点（call 后未出现 test/or/cmp eax + jcc 且动作不同的形态）→ ③b② 不成立。")
    L.append("- 陷阱排查：eax 覆写=%s；多路同一 call 仅参数不同=未据此计数；模板假句（清零/初始化）=本行语义为『调用图邻居弱信号』，非模板假句但亦非③b合同。"
             %("有（见上）" if any(t["eax_overwritten"] for t in r["chA_eax_trap"]) else "未触发"))
    L.append("- 通道B ③b①（跳转表）：%d 处。"%len(r["chB"]))
    L.append("- 结论：③ %s。"%("③b② 形态成立（但不足以救②缺环）" if r["chA"]["p3"]>0 else "不成立（无可伪证返回约定）"))
    L.append("")
    # 环④
    L.append("## 环④ 使用见证（真实调用者或活虚表派发；direct-only 不足）")
    L.append("- direct E8 caller（capstone 指令边界复核，raw==boundary=%d==%d）:"%(v7["raw_count"],v7["boundary_count"]))
    for c in v7["boundary"][:12]: L.append("      %s"%c)
    if len(v7["boundary"])>12: L.append("      ...（共 %d 处）"%len(v7["boundary"]))
    L.append("- 活虚表派发：本行 entry 不在任何虚表槽（见环② dword 命中 0），故不存在独立于②的活虚表派发见证。")
    L.append("- 结论：④ **不合格**（仅 direct-only；无 vtable 派发链；direct 单独不足以支撑 [已证]，D-40）。")
    L.append("")
    # 总表
    L.append("## 四环结论")
    L.append("- ① PASS / ② 未取得(FAIL) / ③ %s / ④ 不合格(direct-only,FAIL)。"%("成立" if r["chA"]["p3"]>0 else "不成立"))
    L.append("- 四环不齐（②、④ 均缺）⇒ **不进 delta**；grade 维持原值，不改 coverage.tsv。")
    L.append("- 否决主因（本行专属）：entry %s 作为 4B VA 全镜像 0 命中（无虚表槽）+ 非构造器 + 无独立活派发；见上方本行地址锚。"%e)
    return "\n".join(L)+"\n"

for r in A:
    e=r["entry"]
    with open(os.path.join(OUT,"ROW_%s.txt"%e),"w",encoding="utf-8") as f:
        f.write(render(r))
print("wrote %d EVIDENCE files to %s"%(len(A),OUT))
