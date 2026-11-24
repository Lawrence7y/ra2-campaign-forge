# -*- coding: utf-8 -*-
"""生成 8 行 EVIDENCE/ROW_*.txt + ROW_SUMMARY.json（组合自动 holders/sites + 人工核 ③b 明细）。"""
import json,os,ax_lib

ROOT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED4"
H=json.load(open(os.path.join(ROOT,'work','holders.json'),encoding='utf-8'))
S=json.load(open(os.path.join(ROOT,'work','sites.json'),encoding='utf-8'))
pe=ax_lib.load()
hmap={r['entry']:r for r in H['rows']}

# 人工逐条打完入口到 ret 得到的可信 extent（绝对 end, 相对 size）——自动化 stop 启发式会把
# 紧邻函数吞进来（如 00703860），此处用 dump 逐条核过的边界覆盖。
EXTENT={
 "00704350":(0x7049BC,0x66D),   # slot187: ret @+0x066C, +0x0670 起下一函数
 "006FFBE0":(0x6FFDFA,0x21A),   # ret 0x10 @+0x0217
 "00703860":(0x703B0B,0x2AB),   # slot26: ret 8 @+0x02A4, +0x02B0 起下一函数
 "005F9950":(0x5F996D,0x1D),    # ret 0xc @+0x001A(3B), +0x0020 起下一函数
 "006F3F40":(0x6F42F9,0x3B9),   # ret @+0x03B8
 "006F6CA0":(0x6F6F33,0x293),   # ret 8 @+0x0290
 "005F9720":(0x5F994B,0x22B),   # ret 8 @+0x0228
 "007171A0":(0x7177B2,0x612),   # ret 4
}

# 人工核：③b 档位 / 入口相对偏移明细 / 归属类 / name / 是否入 delta / 理由
NOTE={
"00704350":dict(name="TechnoClass::slot187",cls="TechnoClass",tier="未成立",delta=False,
  detail="维持[静态推断]。三闸 +0x01A8 cmp edi,-1/je +0x01D2、+0x01D5 cmp ebx,-1/je +0x01FE、+0x0201 cmp eax,-1/je +0x022B："
         "实为取三个候选 cell 的 [cell+0x44]（House 索引），为 -1 则换下一个候选对象；"
         "三闸成功路全部汇入同一表达式 lea eax,[ecx+ebp-1]（ecx=[0x843124]），仅源寄存器 edi/ebx/eax 不同；"
         "既非错误码/返回约定(③b②不成立)，又命中 §8.7判据6「只有参数不同」(细则#1排除)。"
         "③b④候选 +0x05B7..+0x05C8 为纯读循环(mov esi,[ecx]/test [esi+0x140]/inc eax/add ecx,4/cmp eax,3/jl，无写)；"
         "+0x05D5..+0x0639 循环体无显式对象写，写发生在被调 0x547150 内经指针的间接缓冲写，弱于已证口径。"
         "全函数 jmp dword ptr 计算跳表=0、B8 imm32 C3=0、cmp reg,-1 仅此 3 处 → 无可交的互异 ③b。",
  matter="①入口形态成立;②单持有表 TechnoClass slot187(COL 0080C058→TD+8 '.?AVTechnoClass@@')成立;④direct 站点 004DB08C 成立;唯③b不成立"),
"006FFBE0":dict(name="TechnoClass::slot222",cls="TechnoClass",tier="③b①",delta=True,
  detail="switch 式互斥闸链(入口相对)：+0x0030 cmp edi,2 / +0x0035 cmp edi,1(edi=[esp+0x9c] 的模式实参,前置 call 0x637aa0 通过才进入);"
         "+0x00F1 cmp edi,0xa→call [vptr+0x35c]; +0x0105 cmp edi,1→call [vptr+0x370];"
         "+0x011A cmp edi,2 / +0x0123 cmp edi,0x1d→call [vptr+0x368]; +0x012C cmp edi,7→call [vptr+0x358];"
         "+0x0140 cmp edi,8→call [vptr+0x364]; +0x0151 cmp edi,0x10→call [vptr+0x36c]; 默认 +0x0162→call [vptr+0x84] 续处理。"
         "≥6 道互斥闸，各闸调用【不同的】虚表槽(0x358/0x35c/0x364/0x368/0x36c/0x370/0x84)，每路可核 → ③b① 成立；"
         "各闸动作与被调目标各异，不满足 §8.7判据6「汇入同一 call 仅参数不同」的排除条件。",
  matter="①成立;②5 表同槽222(Building/Foot/Infantry/Techno/Unit)→⑯归属基类级 TechnoClass;④direct 站点 00417CB4 成立"),
"00703860":dict(name="TechnoClass::slot26",cls="TechnoClass",tier="③b②",delta=True,
  detail="可证伪返回码约定(入口相对)：多个互斥谓词各返回确定码 —— +0x004F mov eax,5;"
         "+0x00FF/+0x0115/+0x012C/+0x019D/+0x01FB mov eax,3; +0x023A mov eax,1(距离<0x40);"
         "+0x024E mov eax,2(<0x80); +0x0262 mov eax,3(<0xc0); +0x0294 setge cl / +0x029A add ecx,4(→4 或 5);"
         "+0x02A5 xor eax,eax(→0)。返回码集 {0,1,2,3,4,5} 与各自谓词(占位/距离带/标志)一一对应、可逐条证伪，"
         "与审计已收 006FC0B0{1,3,5,6,8,9}/006FFEC0{4,5,7,8,0x1A,0x37} 同类。",
  matter="①成立;②单持有表 TechnoClass slot26;④direct 站点 004545C3,004DA519 成立"),
"005F9950":dict(name="ObjectTypeClass::slot6",cls="ObjectTypeClass",tier="③b②",delta=True,
  detail="可证伪返回约定(入口相对，函数体 +0x0000..+0x001A)：+0x000F call 0x410320(有符号比较 helper);"
         "+0x0014 test eax,eax / +0x0016 jl +0x001A → helper 返回负值时原样保留该负错误码并返回;"
         "+0x0018 xor eax,eax → 非负时归一为 0。返回字节可预测(负→原值/非负→0)，"
         "与审计在 a-S05-KPROVED3 已收的 0070BF50(call 0x65ab80;cmp eax,0;jl→ret 原样返回负值) 同型。",
  matter="①成立;②单持有表 ObjectTypeClass slot6(COL 00807580);④direct 站点 10 处成立"),
"006F3F40":dict(name="TechnoClass::slot9",cls="TechnoClass",tier="③a",delta=False,
  detail="6 个顺序独立的惰性构造块(+0x005D push 0x74/call 0x7c8e17→call 0x6b6c90; +0x00D7 0x64→0x6af1a0; "
         "+0x016C 0x50→0x4717d0; +0x01F4 0x58→0x6292b0; +0x0243 0x50→0x71a4e0; +0x0294 0x60→0x41d380)，"
         "各块是『字段非空则构造子对象并存到不同偏移』的独立 if，不是单一选择子上的 switch/跳表(③b①不成立);"
         "无 -1 哨兵/错误码、无 B8 imm32 C3、无回边循环。整体为机械初始化流(③a)。",
  matter="①成立;②2 表同槽9(FootClass/TechnoClass)→⑯归属基类级 TechnoClass;④5 站点成立;唯③b仅③a"),
"005F9720":dict(name="ObjectTypeClass::slot5",cls="ObjectTypeClass",tier="③a",delta=False,
  detail="析构/清零函数：+0x001E..+0x00EE 逐字段判空→调 dtor/free 再写 0; "
         "+0x01C4..+0x01E4 有界清零循环(ecx=0x12,4 处显式写/add eax,8/dec ecx/jne)——"
         "D-42 ③a 明列『清零+置默认值』为机械可述；循环虽带显式写+界+推进，但语义整体是清零而非有信息 I/O。"
         "③b③内存形状要求『成员 ctor 数+vt+对象大小』三件，此处仅 dtor/free，无 ctor/vt 装配，不达。",
  matter="①成立;②单持有表 ObjectTypeClass slot5;④10 站点成立;唯③b仅③a"),
"007171A0":dict(name="TechnoTypeClass::slot13",cls="TechnoTypeClass",tier="③a",delta=False,
  detail="线性序列化函数(448 指令/104 call)：把 [esi+各偏移] 逐项 push 后调 0x4a1d90/0x4a1d50/0x4a1de0/0x4a1ca0 写出;"
         "无回边(jmptbl=0/back=0)、无 -1 哨兵、无返回码集合、无 switch。纯机械字段转储(③a)。",
  matter="①成立;②单持有表 TechnoTypeClass slot13;④4 站点成立;唯③b仅③a"),
"006F6CA0":dict(name="TechnoClass::slot54",cls="TechnoClass",tier="③a",delta=False,
  detail="线性初始化函数：+0x0011 call 0x5f4ec0 判 al 否则返回 0; 其后顺序 write 字段 + 若干 call; "
         "仅 +0x0175 cmp eax,0xf 一处常量比较(单一分支，非多路); 无 -1 哨兵/返回码集/回边/switch。③a。",
  matter="①成立;②单持有表 TechnoClass slot54;④2 站点成立;唯③b仅③a"),
}

rows=[]
for ent,n in NOTE.items():
    e=int(ent,16); hh=hmap[ent]; ss=S['rows'][ent]
    ex_abs,ex_rel=EXTENT[ent]
    ext='0x%06X'%ex_abs; extrel='+0x%03X'%ex_rel
    first=pe.bytes_at(e,8); prev=pe.bytes_at(e-16,16)
    lines=[]
    lines.append("ROW %s  name=%s  ③b档=%s  delta=%s" % (ent,n['name'],n['tier'],'YES' if n['delta'] else 'NO'))
    lines.append("="*72)
    lines.append("[① 入口形态] 16B对齐=%s; 前驱16B=%s; 入口首指令=%s" % (
        'OK' if e%16==0 else 'BAD',' '.join('%02X'%b for b in (prev or b'')),' '.join('%02X'%b for b in (first or b''))))
    lines.append("[② 全部持有表] 原始命中=%d" % hh['n_raw'])
    for hd in hh['holders']:
        lines.append("   vt=%s slot=%-4d %-36s col=%s td=%s slot_ok=%s" % (
            hd['vt'],hd['slot'],hd['name'],hd['col'],hd['td'],hd['slot_ok']))
    if hh.get('nonvt'): lines.append("   非表命中=%s" % hh['nonvt'])
    # ⑯ 归属
    names=sorted({hd['name'] for hd in hh['holders']})
    lines.append("   持有表数=%d; distinct slot=%s; ⑯归属=%s级(%s)" % (
        len(hh['holders']),hh['slots'],'基类' if len(hh['holders'])>=2 else '单类',n['cls']))
    lines.append("[③b 档位与明细] %s" % n['tier'])
    lines.append("   %s" % n['detail'])
    lines.append("   四环综述: %s" % n['matter'])
    lines.append("[④ 直接调用站点] extent=%s; 指令边界E8命中=%d" % (ext,ss['n_hits']))
    for s in ss['valid_sites']: lines.append("   站点 %s (site+5+rel32==entry, 体外, 非自环)" % s)
    if ss['invalid']: lines.append("   剔除站点=%s" % ss['invalid'])
    lines.append("CFG extent=%s (入口相对 %s)" % (ext,extrel))
    txt="\n".join(lines)
    open(os.path.join(ROOT,'EVIDENCE','ROW_%s.txt'%ent),'w',encoding='utf-8').write(txt)
    rows.append(dict(entry=ent,name=n['name'],tier=n['tier'],delta=n['delta'],
                     holders=len(hh['holders']),slots=hh['slots'],extent=ext,extent_rel=extrel,
                     sites=ss['valid_sites'],cls=n['cls']))
    print("wrote ROW_%s.txt"%ent)

json.dump(dict(rows_processed=len(rows),four_ring_complete=sum(1 for r in rows if r['delta']),
               delta_rows=sum(1 for r in rows if r['delta']),rows=rows),
          open(os.path.join(ROOT,'EVIDENCE','ROW_SUMMARY.json'),'w',encoding='utf-8'),indent=2,ensure_ascii=False)
print("SUMMARY four_ring_complete=",sum(1 for r in rows if r['delta']))
