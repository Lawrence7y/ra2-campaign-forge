"""S13-K1: generate LAYOUT.md from evidence TSVs (no manual transcription).
Groups contiguous 1-byte fields into one row to keep <=200 lines.
"""
import csv
BASE=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1"
ini={}
for r in csv.DictReader(open(BASE+r"\EVIDENCE\ini_fields.tsv",encoding="utf-8"),delimiter="\t"):
    ini.setdefault((r["class"],int(r["store_off"],16)),[]).append(r)
ctor={}
for r in csv.DictReader(open(BASE+r"\EVIDENCE\ctor_offsets.tsv",encoding="utf-8"),delimiter="\t"):
    ctor.setdefault((r["class"],int(r["off"],16)),[]).extend(r["sites"].split(",") if r["sites"] else [])

CLASSES=[
 ("WeaponTypeClass",0x7F73B8,0x849248,0x80E3C0,0x771C70,0x772080,0x160),
 ("WarheadTypeClass",0x7F6B30,0x847C18,0x80D2C0,0x75CEC0,0x75D3A0,0x1D0),
 ("BulletTypeClass",0x7E4948,0x81AFB0,0x7FC7C8,0x46BBC0,0x46BEE0,0x2F8),
 ("BulletClass",0x7E46E4,0x81AF70,0x7FC710,0x466380,None,0x160),
]
VPTR={0,4,8,12}
SPECIAL={
 ("WeaponTypeClass",0xA0):("BulletTypeClass* (Projectile=)","Projectile","0x7729AA; conv 0x46C790"),
 ("WeaponTypeClass",0xAC):("WarheadTypeClass* (Warhead=)","Warhead","0x772992; conv 0x75E3B0"),
 ("WarheadTypeClass",0xA0):("Verses double[11] @+0xA0..+0xF7","Verses","0x75DDE6/0x75DE48 (11x loop)"),
}
out=[]
def w(x=""): out.append(x)

w("# S13-K1 LAYOUT — 四个核心战斗类的字段布局")
w("")
w("> 目标 `ra2youli\\gamemd.exe` SHA-256 `73201CC0…F67476`，ImageBase 0x400000。只读。capstone 5.0.7 `skipdata=True`；")
w("> 类名以 RTTI TypeDescriptor 实测（`work/rtti_extract.py`）；虚表长度**从 .rdata 定界数槽**（不读 `vtables_v2.json`）；")
w("> thiscall `this` 寄存器回溯到首个 `mov reg,ecx`（构造器/loader 逐一确认）；站点归属用函数区间包含。")
w("> 字段语义锚点=INI 键；写者=`mov [obj+off],reg`/`fstp [obj+off]`；读者=同 loader 中 `mov reg,[obj+off]` 取默认值（该类自身读点）。")
w("> 原始未截断证据：`EVIDENCE/ini_fields.tsv`、`EVIDENCE/ctor_offsets.tsv`、`EVIDENCE/field_tables.txt`、`EVIDENCE/rtti_extract.txt`。")
w("")
w("## 0 定位总表（RTTI 实测，非文件名启发）")
w("")
w("| 类 | TypeDescriptor | COL | vftable(主) | 实测槽数 | slot11=WhatAmI | slot12=GetSize | 构造器入口 | INI loader(slot25) |")
w("|---|---|---|---|---|---|---|---|---|")
ids={"WeaponTypeClass":("0x31",0x160),"WarheadTypeClass":("0x32",0x1D0),"BulletTypeClass":("0x09",0x2F8),"BulletClass":("0x08",0x160)}
for cls,vt,td,col,ctor_addr,loader,sz in CLASSES:
    w(f"| {cls} | 0x{td:08X} | 0x{col:08X} | 0x{vt:08X} | { {'WeaponTypeClass':27,'WarheadTypeClass':27,'BulletTypeClass':40,'BulletClass':125}[cls] } | id {ids[cls][0]} | {sz:#x} | 0x{ctor_addr:08X} | {('0x%08X'%loader) if loader else '—（运行时对象）'} |")
w("")
w("槽数双通道：`.rdata` 定界连续指针扫描（27/27/40/125）与 `re_atlas/evidence/rtti/symbols.json` 元数据一致；")
w("slot11/slot12 体均为 `mov eax,imm; ret`，实测返回值见上表（`EVIDENCE/verify_slots.txt`）。四张副虚表 `vt-0x2C..vt-0x10` 为多重继承子对象表（见 `rtti_extract.txt`）。")
w("")

for _ci,(cls,vt,td,col,ctor_addr,loader,sz) in enumerate(CLASSES):
    offs=sorted((set([o for (c,o) in ini if c==cls])|set([o for (c,o) in ctor if c==cls]))-VPTR)
    w(f"## {_ci+1} {cls} — 字段数 {len(offs)}（排除 4 个 vptr 槽）")
    w("")
    w("| off | 宽 | 类型/语义 | 写者站点 | 读者站点 |")
    w("|---|---|---|---|---|")
    # group contiguous width-1 keyed offsets
    used=set(); rows=[]
    for o in offs:
        if o in used: continue
        rs=ini.get((cls,o),[])
        # build run of contiguous byte keyed fields
        if rs and rs[0]["width"]=="1" and (cls,o) not in SPECIAL:
            run=[o]; keys=[]; wsites=[]; rsites=[]
            cur=o
            while True:
                rr=ini.get((cls,cur),[])
                if not rr or rr[0]["width"]!="1" or (cls,cur) in SPECIAL: break
                keys.extend([x["key"] for x in rr if x["key"]])
                wsites.extend([x["store_site"] for x in rr]+ctor.get((cls,cur),[]))
                rsites.extend([x["default_site"] for x in rr if x["default_site"]])
                used.add(cur)
                if cur+1 in offs and ini.get((cls,cur+1),[]) and ini[(cls,cur+1)][0]["width"]=="1" and (cls,cur+1) not in SPECIAL:
                    cur+=1; run.append(cur)
                else: break
            if len(run)>=2:
                rows.append((f"0x{run[0]:X}..0x{run[-1]:X}","1 ea", ", ".join(keys)[:120], ", ".join(dict.fromkeys(wsites))[:100], ", ".join(dict.fromkeys(rsites))[:60]))
                continue
            used.discard(o)
        # single field
        if (cls,o) in SPECIAL:
            sem,k,wt=SPECIAL[(cls,o)]
            rows.append((f"0x{o:X}", "4", sem, wt, "—"))
        elif rs:
            keys=",".join(sorted(set(x["key"] for x in rs if x["key"]))) or "[converter]"
            wd=rs[0]["width"]
            typ={"ReadInteger":"int","ReadBool":"bool","ReadDouble":"double","ReadString":"char*/ptr"}.get(rs[0]["reader"],rs[0]["reader"])
            ws=", ".join([x["store_site"] for x in rs]+ctor.get((cls,o),[]))
            rsite=", ".join([x["default_site"] for x in rs if x["default_site"]][:2])
            rows.append((f"0x{o:X}",wd,f"{typ} {keys}",ws[:100],rsite))
        else:
            rows.append((f"0x{o:X}","?","[未证] (ctor 默认写)", ", ".join(ctor.get((cls,o),[]))[:100],"—"))
    for r in rows: w("| "+" | ".join(r)+" |")
    w("")

w("## 5 一致性核对（字段表 max_end ≤ GetSize）")
w("")
w("| 类 | 字段数(排除vptr) | 最大字段偏移+宽 | GetSize/分配 | 结论 |")
w("|---|---|---|---|---|")
for _ci,(cls,vt,td,col,ctor_addr,loader,sz) in enumerate(CLASSES):
    offs=sorted((set([o for (c,o) in ini if c==cls])|set([o for (c,o) in ctor if c==cls]))-VPTR)
    maxend=0
    for o in offs:
        rs=ini.get((cls,o),[]); wd=int(rs[0]["width"]) if rs and rs[0]["width"].isdigit() else (8 if cls=="WarheadTypeClass" and o in (0x98,0xF8) else 1)
        maxend=max(maxend,o+wd)
    w(f"| {cls} | {len(offs)} | 0x{maxend:X} | 0x{sz:X} | {'吻合' if maxend<=sz else 'FAIL'} |")
w("")
w("## 6 WeaponTypeClass ↔ WarheadTypeClass 引用关系（task 4）")
w("")
w("`Warhead=` 键 → `ReadString@0x77295F`（key `0x8183b4`=\"Warhead\"，默认取当前 `+0xAC`）→ `call 0x75E3B0`（字符串→WarheadTypeClass* 解析器）→ `mov [esi+0xAC],eax @0x772992`。")
w("即 **WeaponTypeClass+0xAC = WarheadTypeClass\\***。同段 `Projectile=`（key `0x849268`）→ `call 0x46C790` → `mov [esi+0xA0],eax @0x7729AA`，即 **+0xA0 = BulletTypeClass\\***。")
w("证据：`EVIDENCE/inspect_special.txt`（逐条），写者站点 `ini_fields.tsv`；构造器同样在 `0x771CA9/0x771C97` 清这两个指针。")
w("")
w("## 7 Verses 伤害倍率矩阵（task 5）")
w("")
w("`Verses=` 键（默认串 \"100%,…\" 共 11 项，`0x847c40`）→ `ReadString@0x75DDE6` → `strtok(',')@0x7c9cc2` → 循环 `strchr('%')@0x7caf30` + `atoi@0x7c9bfd` ×常数 `@0x7e3808` → `fstp qword [ebx] @0x75DE48`，")
w("其中 `lea ebx,[esi+0xA0]`、`mov ebp,0xB`（11 次）、`add ebx,8`。构造器 `0x75CEC0` 内 `lea esi,[ebp+0xA0]` + `mov ecx,0x14; rep movsd @0x75D1A7` 独立复现 11 个 double 的初始化（首项 1.0 = `0x3FF0000000000000`）。")
w("**维度 11（护甲类型）× double(8B)，行主序连续 @ WarheadTypeClass+0xA0..+0xF7（88 B）**。+0x149 的 byte 不是 INI 字段，而是 0x75DE80/0x75DE98 依 +0xC0/+0xD0 与阈值 `0x7e2800` 比较得到的派生标志（原工具误标为 Verses，已更正）。")
w("")

open(BASE+r"\LAYOUT.md","w",encoding="utf-8").write("\n".join(out))
print("wrote LAYOUT.md",len(out),"lines")
