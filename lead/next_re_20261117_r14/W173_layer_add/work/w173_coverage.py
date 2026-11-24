# -*- coding: utf-8 -*-
"""W173 生成 coverage_delta.tsv：本卡涉及的每个函数一行。
来源：chB 层数组引用函数、chA 层候选(0)、w94 对象字段写函数、Add 直接调用者、GetLayer 实现。
"""
from __future__ import annotations
import os
import sys
import bisect

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w173_common as C

E = C.EVID
OUT = C.OUT
LO, HI = C.LAYER_BASE, C.LAYER_END

# 人工核对过的语义（证据见 EVIDENCE/w173_probe_funcs.txt / w173_verify.txt / w173_getlayer_detail.txt 等）
CUR = {
    0x4A88C0: ("S07", "MapClass::ClearLayers", "遍历[5]LayerClass(mov esi,0x8A0360)逐层调虚槽+0x0C清空", "[已证]", "EVIDENCE/w173_probe_funcs.txt"),
    0x4A9720: ("S07", "ObjectClass::SetLayer", "取[vptr+0x78]层号→lea ecx,[idx*8+0x8A0360]直接call 0x5519B0加入层→写[obj+0x94]=层号", "[已证]", "EVIDENCE/w173_probe_funcs.txt"),
    0x4A9770: ("S07", "ObjectClass::RemoveFromLayer", "按[obj+0x94]取层→虚槽+0x10定位→数组左移→[+0x94]=-1（两处:0x4A97D2/0x4A982C）", "[已证]", "EVIDENCE/w173_probe_funcs.txt"),
    0x4A835D: ("S07", "LayerArrayCtor", "构造[5]LayerClass：0x4A8630 mov eax,0x8A0368;步长0x18;最终vft=0x7E6060", "[已证]", "EVIDENCE/w173_chB_detail.txt"),
    0x4AA2B0: ("S07", "Layer_items_count_reader", "按层对象基访问Items(0x8A0364)/Count(0x8A0370)", "[已证]", "EVIDENCE/w173_chB_detail.txt"),
    0x4AA380: ("S07", "Layer_items_scaled_reader", "用[eax*8+0x8A0370]/[ecx*8+0x8A0364]读层项", "[已证]", "EVIDENCE/w173_chB_detail.txt"),
    0x4ADFF0: ("S07", "Layer2_count_reader", "读层[2] Count(0x8A03A0)/Items(0x8A0394)", "[已证]", "EVIDENCE/w173_chB_detail.txt"),
    0x4AE0B0: ("S07", "Layer2_count_reader_2", "读层[2] Count/Items", "[已证]", "EVIDENCE/w173_chB_detail.txt"),
    0x4AE6F0: ("S07", "ForEachLayer_call_551B90", "遍历5层(0x8A0360..0x8A03D8)对每层ecx=layer调0x551B90", "[已证]", "EVIDENCE/w173_probe_funcs.txt"),
    0x4AE720: ("S07", "ForEachLayer_call_551B20", "遍历5层对每层ecx=layer调0x551B20直到返回>=0", "[已证]", "EVIDENCE/w173_probe_funcs.txt"),
    0x55BAA0: ("S07", "LayerAddOnlyIfNotPresent", "[obj+0x98]!=0直接返回;否则push(obj,flag)直接call 0x5519B0加入层", "[已证]", "EVIDENCE/w173_probe_funcs.txt"),
    0x55D360: ("S07", "SortLayer2", "对层[2](0x8A0390)按元素[vptr+0xB8]排序(mov ecx,0x8A0390@0x55DBC3)", "[已证]", "EVIDENCE/w173_chB_detail.txt"),
    0x4824D4: ("S07", "Layer2_draw_prep_atlas_hole", "atlas空洞函数（全.text扫call目标发现）；读层[2] Items/Count(0x8A0394/0x8A03A0)", "[静态推断]", "EVIDENCE/w173_chB_detail.txt"),
    0x6D8DB0: ("S07", "DrawListTraverse", "遍历层数组渲染：以层对象基0x8A0360/Count0x8A03A0取元素后调绘制", "[已证]", "EVIDENCE/w173_chB_detail.txt"),
    0x6D97D0: ("S07", "DrawLayerReverse", "倒序消费层[2]元素(mov eax,[0x8A03A0];mov ecx,[0x8A0394])", "[已证]", "EVIDENCE/w173_chB_detail.txt"),
    0x6D9920: ("S07", "DrawLayerForward", "正序消费层[2]元素", "[已证]", "EVIDENCE/w173_chB_detail.txt"),
    0x6D9A50: ("S07", "DrawLayerSlice", "切片消费层[2]元素", "[已证]", "EVIDENCE/w173_chB_detail.txt"),
    0x5519B0: ("S07", "VectorClass<T>::Add", "thiscall(ecx=vector);栈参(item,only_check);ret 8;容量不足扩容后写Items[Count++]", "[已证]", "EVIDENCE/w173_conv_detail.txt"),
    0x5F4260: ("S07", "ObjectClass::GetLayer(default)", "call[vptr+0x54]判可见→否则mov eax,2 ret（默认层2）", "[已证]", "EVIDENCE/w173_getlayer_detail.txt"),
    0x4369F0: ("S20", "BuildingLightClass::GetLayer", "mov eax,3;ret（层3）", "[已证]", "EVIDENCE/w173_getlayer_detail.txt"),
    0x62D770: ("S20", "ParticleClass::GetLayer", "mov eax,3;ret（层3）", "[已证]", "EVIDENCE/w173_getlayer_detail.txt"),
    0x74A960: ("S20", "VoxelAnimClass::GetLayer", "mov eax,3;ret（层3）", "[已证]", "EVIDENCE/w173_getlayer_detail.txt"),
    0x75F890: ("S20", "WaveClass::GetLayer", "mov eax,3;ret（层3）", "[已证]", "EVIDENCE/w173_getlayer_detail.txt"),
    0x65C320: ("S07", "RadSiteClass::GetLayer", "mov al,1;ret 4（层1）", "[静态推断]", "EVIDENCE/w173_getlayer_detail.txt"),
    0x54B750: ("S05", "ObjectCtor_layer0_7ECE34", "call 0x55AAC0后写[esi+0x94]=0并置vft=0x7ECE34（层0对象构造）", "[已证]", "EVIDENCE/w173_fn54B750.txt"),
    0x636B50: ("S07", "ClearLayerField_636B50", "mov [edi+0x94],-1 清空对象层字段", "[已证]", "EVIDENCE/w173_w94_precise.txt"),
    0x4A88C0: ("S07", "MapClass::ClearLayers", "遍历[5]LayerClass逐层调虚槽+0x0C清空", "[已证]", "EVIDENCE/w173_probe_funcs.txt"),
}

# 收集所有 w94 对象字段写所在函数
ins = C.text_insns()
w94_funcs = set()
for j, r in enumerate(ins):
    if r["mn"] != "mov" or len(r["ops"]) < 2:
        continue
    d, s = r["ops"][0], r["ops"][1]
    if d["kind"] != "mem" or d["base"] in (None, "esp", "ebp") or d["disp"] != C.W94_OFF or d["size"] != 4:
        continue
    o = C.owner(r["va"], "atlas")
    if o:
        w94_funcs.add(o[0])

# 收集 chB 函数（精确+范围都算层数组引用）
chb_funcs = set()
for j, r in enumerate(ins):
    for op in r["ops"]:
        if (op["kind"] == "imm" and LO <= (op["val"] & 0xFFFFFFFF) < HI) or \
           (op["kind"] == "mem" and LO <= (op["disp"] & 0xFFFFFFFF) < HI):
            o = C.owner(r["va"], "atlas")
            if o:
                chb_funcs.add(o[0])
            break

all_funcs = sorted(set(CUR) | w94_funcs | chb_funcs)
rows = ["entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path"]
for f in all_funcs:
    if f in CUR:
        sub, name, sem, grade, ev = CUR[f]
    else:
        sub = "S05"
        name = "sub_%08X" % f
        src = "imm/reg"
        for j, r in enumerate(ins):
            if r["mn"] == "mov" and len(r["ops"]) >= 2:
                d, s = r["ops"][0], r["ops"][1]
                if (d["kind"] == "mem" and d["base"] not in (None, "esp", "ebp")
                        and d["disp"] == C.W94_OFF and d["size"] == 4
                        and C.owner(r["va"], "atlas") and C.owner(r["va"], "atlas")[0] == f):
                    src = ("imm 0x%X" % (s["val"] & 0xFFFFFFFF)) if s["kind"] == "imm" else \
                          ("reg " + s["name"]) if s["kind"] == "reg" else "mem"
                    break
        sem = "写 ObjectClass+0x94 层字段 = %s（该写点已证；整体语义未定）" % src
        grade = "[已证]" if f in w94_funcs else "[静态推断]"
        ev = "EVIDENCE/w173_w94_precise.txt"
    rows.append("%08X\t%s\t%s\t%s\t%s\t%s" % (f, sub, name, sem, grade, ev))

with open(os.path.join(OUT, "coverage_delta.tsv"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(rows) + "\n")
print("coverage_delta rows=%d (curated=%d w94=%d chB=%d)" % (
    len(rows) - 1, len(CUR), len(w94_funcs), len(chb_funcs)))
