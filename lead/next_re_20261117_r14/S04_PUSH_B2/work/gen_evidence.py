# -*- coding: utf-8 -*-
"""生成 18 份 EVIDENCE/ROW_<entry>.txt（每行自身地址锚 + 四环 + 裁定），并写 S04_delta.tsv。
所有 reason 逐行不同且含本行地址。只读输入为 work/ 下的 dump、facts、ctor 分析。
"""
import os, csv, re, json
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S04_PUSH_B2"
W = os.path.join(OUT, "work")
EVID = os.path.join(OUT, "EVIDENCE")

# 逐行专属裁定（含本行地址锚，禁止整批共用）
VERDICT = {
"00523C90": ("③不成立+②未取得", "本体 call@0x523C9A(0x7c8d20=stricmp 0x817474)→test@0x523CA2→je@0x523CA4，"
  "检查的是字符串比较返回值而非本函数的可伪证错误码契约；+0x28 mov eax,[0xa8e358] 后又 test@0x523CA2 类链条测成员，"
  "属 ③a 分支控制流。②：全数据段 dword_refs=0，entry 0x523C90 从无 RTTI vt 槽；构造链：函数体 0 处写已知 vt。"
  "④ direct-only(7 站点)。任一环 FAIL ⇒ 否决。"),
"00523D00": ("②未取得", "entry 0x523D00 全数据段 dword_refs=0、RTTI vt 槽 0；函数体 0 处写已知 vt，"
  "ecx=this(esi) 访问 [esi+0xe3c]/[esi+0x1f8] 但无 RTTI/虚表/构造链可定类名。③b② 站点 call@0x523D26→test@0x523D2B→jle@0x523D2D "
  "为返回值分支，但 ② 环取不到直接判不成立；④ 仅 1 direct(0x52473A)。否决。"),
"00525430": ("③不成立（②经构造链成立但③缺）", "②：本体 +0xEE mov [esi],0x7E4DD8 / +0x16B mov [esi],0x7E4DD8（esi=ecx=this），"
  "VT 0x7E4DD8 RTTI=.?AV?$TypeList@H@@ ⇒ 构造链可定类 TypeList<int>，构造链通道成立。"
  "③：① ③b② 无（call@0x52545C→test@0x525461→je@0x525463 是 stricmp 分支且调用方 br=0/16，构造器无返回契约被分支）；"
  "② ③b③ 仅 1 张 distinct vt（写 3 次同值）+6 个 this 字段(<10、<2vt)，D-42 门槛不达；"
  "③ ③b④ 回边 jne@0x52550B→0x5254A0 循环体内 +0xC8 mov [ecx+eax*4],edi 有非栈写，"
  "但 +0xA2 cmp ecx,ebx/jle 测的是 [esp+0x20] 而非写索引上界，无 per-iteration 边界检查 ⇒ ③b④ 不成立。否决。"),
"00525A60": ("②未取得+③模板假句", "entry 0x525A60 dword_refs=0、RTTI vt 槽 0；函数体写 vt 均在栈/局部对象"
  "（+? mov [esp+0x40],0x7E61F0 Straw / [ebx+0],0x7EB74C Node / [esi+0],0x7EB744 List）非 this(ecx)，"
  "构造链不能定本函数类名。③b② 6 站点多为 INI 解析分支（如 call@0x525AC? 后 test→je），语义属对象初始化/清零模板句；"
  "br=0/3。④ direct-only(3)。否决。"),
"00526B10": ("②未取得（③b②强但不救②）", "③b② 确为真形态：call@0x526C50(0x52b620=FindItem)→test@0x526C55→je@0x526C57→0x526C8E，"
  "失败 ret 原点 +0x17E xor eax,eax / ret 8，成功返回非 NULL，sig_t=([],[0],True,0)≠sig_f，调用方 br=15/16。"
  "但 ②：entry 0x526B10 dword_refs=0、RTTI vt 槽 0；ebp=ecx=this 是调用方传入的栈局部"
  "（如 site 0x65F5D2 前 lea ecx,[esp+0x18]），本函数既不自写 vt 也不虚派发 ebp，构造链无法定 this 类名 ⇒ ②未取得直接判不成立。否决。"),
"00533D20": ("②未取得", "entry 0x533D20 dword_refs=0、RTTI vt 槽 0；函数体 5 处 vt 写全在栈临时"
  "（[esp+0x10],0x7E1AF4 CCINIClass / [esp+0x68],0x7E16B0 CCFileClass / 0x7E1668 CDFileClass），this+字段写=0，"
  "构造链不能定本函数类名。③b② 站点 call@0x533E?→test→jle 为文件/INI 读取分支，br=0/3。④ direct-only(3)。否决。"),
"005E6520": ("②未取得", "entry 0x5E6520 dword_refs=0、RTTI vt 槽 0；序言 cmp ecx,ebx/jl 用 ecx 作整数索引非 this；"
  "7 处 vt 写全在栈局部（[esp+0x1C],0x7E1B04 GenericList/[esp+0x14],0x7EA5F4 INIClass/[esp+0x4C],CCFileClass/CDFileClass），"
  "this+字段写=0，构造链不能定类名。③b② call@→test→je 为 INI 解析分支，br=1/22。否决。"),
"005FA620": ("②未取得", "entry 0x5FA620 dword_refs=0、RTTI vt 槽 0；函数体 0 处写已知 vt，构造链无。"
  "③b② 5 站点为内部返回分支但 ④ 仅 1 direct(0x52C630)、br=0。②取不到直接判不成立。否决。"),
"006418B0": ("②未取得", "entry 0x6418B0 dword_refs=0、RTTI vt 槽 0；2 处 vt 写在栈局部"
  "（[esp+0x34],0x7E6218 Pipe / 0x7E6200 BufferPipe），this+字段写=0，构造链不能定本函数类名。"
  "③b② 2 站点为管道读写分支，br=0/2。否决。"),
"00641B00": ("②未取得", "entry 0x641B00 dword_refs=0、RTTI vt 槽 0；2 处 vt 写在栈局部"
  "（[esp+0x30],0x7E61F0 Straw / 0x7E61E0 BufferStraw），this+字段写=0，构造链不能定类名。"
  "③b② 3 站点 br=0/1。否决。"),
"00641EE0": ("②未取得", "entry 0x641EE0 dword_refs=0、RTTI vt 槽 0；8 处 vt 写全在栈局部"
  "（[esp+0xAC]/[esp+0x100],0x7E1AF4 CCINIClass / [esp+0x20],0x7E61F0 Straw 等），this+字段写=0，构造链不能定类名。"
  "③b② 1 站点 br=0/3。否决。"),
"00644890": ("②未取得", "entry 0x644890 dword_refs=0、RTTI vt 槽 0；函数体 0 处写已知 vt；"
  "ecx=this 为拷贝赋值壳（复制字段），构造链无类名。③b② 4 站点 br=2/17 但属返回约定弱分支；"
  "②取不到直接判不成立。否决。"),
"00645820": ("②未取得", "entry 0x645820 dword_refs=0、RTTI vt 槽 0；函数体 0 处写已知 vt，构造链无；"
  "③b② 4 站点 br=0/1，④ 仅 1 direct。否决。"),
"0067A090": ("②未取得+③模板假句", "entry 0x67A090 dword_refs=0、RTTI vt 槽 0；函数体 0 处写已知 vt；"
  "本体 +0x02 mov edi,[esp+0xc]/+0x06 mov esi,ecx 为拷贝赋值（复制 [esi+4]/[esi+8] 数组 + 标量），"
  "42 个 direct 调用方均为构造器但 ecx=this 无 vt 归属，构造链不能定本函数类名。"
  "③b② 唯一站点 call@0x67A0B3(0x7c8e17=new)→test@0x67A0BE→je@0x67A0C0 为分配失败分支，语义属对象初始化模板句，br=0/42。否决。"),
"0067A110": ("②未取得+③模板假句", "entry 0x67A110 dword_refs=0、RTTI vt 槽 0；函数体 0 处写已知 vt；"
  "同 0x67A090 族拷贝赋值壳，构造链不能定类名。③b② 唯一站点为 new 分配失败→je 分支，语义模板句，br=0/5。否决。"),
"0067A190": ("②未取得+③模板假句", "entry 0x67A190 dword_refs=0、RTTI vt 槽 0；函数体 0 处写已知 vt；"
  "拷贝赋值壳，构造链不能定类名。③b② 唯一站点为分配失败分支，br=0/1。否决。"),
"0067A210": ("②未取得+③模板假句", "entry 0x67A210 dword_refs=0、RTTI vt 槽 0；函数体 0 处写已知 vt；"
  "拷贝赋值壳，构造链不能定类名。③b② 唯一站点为分配失败分支，br=0/1。否决。"),
"0067A290": ("②未取得+③模板假句", "entry 0x67A290 dword_refs=0、RTTI vt 槽 0；函数体 0 处写已知 vt；"
  "拷贝赋值壳，构造链不能定类名。③b② 唯一站点为分配失败分支，br=0/6。否决。"),
}

def section_from_dump(d, header, next_header):
    if next_header:
        m = re.search(re.escape(header)+r"(.*?)(?="+re.escape(next_header)+r"|\Z)", d, re.S)
    else:
        m = re.search(re.escape(header)+r"(.*)\Z", d, re.S)
    return m.group(1).strip() if m else ""

def main():
    rows=[]
    with open(os.path.join(W,"b2_entries.tsv"),encoding="utf-8") as fh:
        for r in csv.DictReader(fh,delimiter="\t"): rows.append(r)
    made=[]
    for r in rows:
        e=r["entry"]; ea=int(e,16)
        d=open(os.path.join(W,"dump_%s.txt"%e),encoding="utf-8").read()
        verdict, reason = VERDICT[e]
        lines=[]
        lines.append("# EVIDENCE entry %s  name=%s  subsystem=%s  grade=%s  (S04_PUSH_B2)" %(e,r["name"],r["subsystem"],r["grade"]))
        lines.append("")
        lines.append("## ① 入口")
        m=re.search(r"entry=0x([0-9A-F]+) in_text=(\w+).*?atlas_size=(\d+)",d)
        lines.append("  entry=0x%s in_text=%s atlas_size=%s .text=[0x401000,0x7E038D)" % (m.group(1),m.group(2),m.group(3)))
        bm=re.search(r"bytes@entry = ([0-9a-f ]+)",d)
        lines.append("  bytes@entry = %s" % (bm.group(1) if bm else ""))
        dm=re.search(r"disasm insns=(\d+) last_ret_end=(\S+)",d)
        lines.append("  disasm insns=%s last_ret_end=%s (函数边界自洽)" % (dm.group(1),dm.group(2)))
        lines.append("")
        lines.append("## ② 类身份（RTTI 名 / 虚表归属 / 构造链）")
        lines.append("  全数据段 dword_refs=0；RTTI vt 槽 n_named_slots=0（两套实现独立复算一致：build_index.py + B1 witness_core.resolve_slot）")
        lines.append("  ⇒ RTTI 名/虚表归属 = 未取得。构造链通道逐行核查见裁定。")
        lines.append("")
        lines.append("## ③ 整体合同（只认 ③b）")
        seg=section_from_dump(d,"## ③ 整体合同（③b 形态检测）","## full disassembly")
        for ln in seg.splitlines():
            if ln.strip() and ("③b② 候选站点" in ln or "call@" in ln or "jump-table" in ln or "backward-branch" in ln or "back)" in ln):
                lines.append("  "+ln.strip())
        lines.append("")
        lines.append("## ④ 使用见证（真实调用者 / 活虚表派发，direct-only 不足）")
        seg4=section_from_dump(d,"## ④ 使用见证（direct call 站点 / 活虚表派发）","## ③ 整体合同")
        for ln in seg4.splitlines():
            if ln.strip() and ("direct E8" in ln or "livevt" in ln):
                lines.append("  "+ln.strip())
        lines.append("")
        lines.append("## 裁定：%s —— 不成立（不进 delta）" % verdict)
        lines.append("  "+reason)
        lines.append("")
        lines.append("## 关键反汇编锚点（本行入口 +0xNN）")
        segd=section_from_dump(d,"## full disassembly (entry-relative, atlas size)","")
        keep=[]
        for ln in segd.splitlines():
            s=ln.strip()
            if not s: continue
            if any(k in s for k in ("call","test","ret","mov dword ptr [esi],","mov [esi],","mov dword ptr [esp","lea ecx","mov esi, ecx","mov ebp, ecx","mov edi, ecx","cmp ecx")):
                keep.append("  "+s)
        lines.extend(keep[:26])
        open(os.path.join(EVID,"ROW_%s.txt"%e),"w",encoding="utf-8").write("\n".join(lines)+"\n")
        made.append(e)
    # delta: header only (no four-ring-complete rows)
    with open(os.path.join(OUT,"S04_delta.tsv"),"w",encoding="utf-8",newline="") as fh:
        fh.write("entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\n")
    print("wrote %d EVIDENCE files + empty S04_delta.tsv" % len(made))
    for e in made: print("  ROW_%s.txt"%e)

if __name__=="__main__": main()
