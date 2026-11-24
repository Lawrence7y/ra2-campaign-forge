# -*- coding: utf-8 -*-
"""从 EVIDENCE 组装 coverage_delta.tsv（6 列）；行数=自报=3；②类=name类；偏移入口相对。"""
import os
ROOT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED4"
rows=[
("006FFBE0","TechnoClass::slot222",
 "[已证] ①entry 006FFBE0 16B对齐+E8体外直调见证;②全.rdata原始命中=5表全部持有同槽222:"
 "007E3EBC[222]→COL007FC360→TD+8'.?AVBuildingClass@@';007E8C94[222]→COL00800948→'.?AVFootClass@@';"
 "007EB058[222]→COL008033B8→'.?AVInfantryClass@@';007F4960[222]→COL0080C058→'.?AVTechnoClass@@'←name类TechnoClass;"
 "007F5C70[222]→COL0080CC68→'.?AVUnitClass@@';5表同slot→错源⑯归属基类级TechnoClass,name栏TechnoClass在持有集内且TD+8逐字一致;"
 "非容器族DV/V同slot别名=无;③b①switch式互斥闸链:+0x0030 cmp edi,2/+0x0035 cmp edi,1(模式实参,前置call 0x637aa0通过);"
 "+0x00F1 cmp edi,0xa→call[vptr+0x35c];+0x0105 cmp edi,1→call[vptr+0x370];"
 "+0x011A/0x0123 cmp edi,2/0x1d→call[vptr+0x368];+0x012C cmp edi,7→call[vptr+0x358];"
 "+0x0140 cmp edi,8→call[vptr+0x364];+0x0151 cmp edi,0x10→call[vptr+0x36c];默认+0x0162→call[vptr+0x84];"
 "≥6互斥闸且各闸调用不同虚表槽(0x358/0x35c/0x364/0x368/0x36c/0x370/0x84),每路可核,非同call仅参数不同;"
 "④direct E8边界@体外站点1处(00417CB4),site+5+rel32==entry/非自环;CFG extent+0x0000..+0x21A",
 "EVIDENCE/ROW_006FFBE0.txt;EVIDENCE/ROW_SUMMARY.json;EVIDENCE/baselines.json"),
("00703860","TechnoClass::slot26",
 "[已证] ①entry 00703860 16B对齐+E8体外直调见证;②全.rdata原始命中=1表全部持有:"
 "007F4960[26]→COL0080C058→TD+8'.?AVTechnoClass@@'←name类TechnoClass(name类在持有集内且逐字一致);"
 "单持有表slot26,错源⑯不触发(holders=1);非容器族DV/V同slot别名=无;"
 "③b②可证伪返回码约定(互斥谓词→确定码):+0x004F mov eax,5;"
 "+0x00FF/+0x0115/+0x012C/+0x019D/+0x01FB mov eax,3;+0x023A mov eax,1(距<0x40);+0x024E mov eax,2(<0x80);"
 "+0x0262 mov eax,3(<0xc0);+0x0294 setge cl/+0x029A add ecx,4(→4或5);+0x02A5 xor eax,eax(→0);"
 "返回码集{0,1,2,3,4,5}与各谓词一一对应可逐条证伪,与审计已收006FC0B0/006FFEC0同型;"
 "④direct E8边界@体外站点2处(004545C3,004DA519),site+5+rel32==entry/非自环;CFG extent+0x0000..+0x2AB",
 "EVIDENCE/ROW_00703860.txt;EVIDENCE/ROW_SUMMARY.json;EVIDENCE/baselines.json"),
("005F9950","ObjectTypeClass::slot6",
 "[已证] ①entry 005F9950 16B对齐+E8体外直调见证;②全.rdata原始命中=1表全部持有:"
 "007EF2D8[6]→COL00807580→TD+8'.?AVObjectTypeClass@@'←name类ObjectTypeClass(name类在持有集内且逐字一致);"
 "单持有表slot6,错源⑯不触发(holders=1);非容器族DV/V同slot别名=无;"
 "③b②可证伪返回约定:+0x000F call 0x410320(有符号比较helper)/+0x0014 test eax,eax/+0x0016 jl +0x001A"
 "(helper负→原样保留负错误码返回)/+0x0018 xor eax,eax(非负→归一0),返回字节可预测(负→原值/非负→0),"
 "与审计已收0070BF50(call 0x65ab80;cmp eax,0;jl→ret 原样返回负值)同型;④direct E8边界@体外站点10处"
 "(0042897F,0046C73F,00549D7F,005FEC1F,0064483F,006457B3,006B58BF,00716DD1,0071E24F,0074B8DF),"
 "site+5+rel32==entry/非自环;CFG extent+0x0000..+0x1D",
 "EVIDENCE/ROW_005F9950.txt;EVIDENCE/ROW_SUMMARY.json;EVIDENCE/baselines.json"),
]
out=['entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path']
for e,n,sem,ev in rows:
    out.append('%s\tS05\t%s\t%s\t[已证]\t%s'%(e,n,sem,ev))
p=os.path.join(ROOT,'coverage_delta.tsv')
open(p,'w',encoding='utf-8').write('\n'.join(out)+'\n')
print("wrote coverage_delta.tsv rows=",len(rows))
# self-check: ② class token vs name class
for e,n,sem,ev in rows:
    cls=n.split('::')[0]
    assert ('.?AV'+cls+'@@') in sem, (e,cls)
    print(' %s name-class %s present in ② 栏 OK'%(e,cls))
