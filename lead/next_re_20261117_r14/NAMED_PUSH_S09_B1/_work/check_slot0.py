# -*- coding: utf-8 -*-
"""检查各主虚表 slot0 是否为 00410260（主表特征），核对小成员表陷阱。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core2 as C2
vbs = {
 'CCToolTip':0x7F74C4,'CheckListClass':0x7E4F84,'Dial8Class':0x7E5E3C,
 'DropListClass':0x7E7FCC,'EditClass':0x7E81A4,'GaugeClass':0x7E9384,
 'TriColorGaugeClass':0x7E9430,'GraphicMenuImageItem':0x7EA674,
 'MouseClass':0x7E1964,'DisplayClass':0x7E6114,'ColorListClass':0x7E5054,
 'ListClass':0x7ED10C,'ShapeButtonClass':0x7E8088,'GScreenClass':0x7EA6FC,
 'MapClass':0x7ED404,'TabClass':0x7EDFB4,'PowerClass':0x7EFF54,
 'RadarClass':0x7F0344,'ScrollClass':0x7F1094,'SidebarClass':0x7F3058,
}
for name,vb in sorted(vbs.items(), key=lambda kv:kv[1]):
    col=C2.u32(vb-4)
    td=C2.u32(col+0xC) if col else None
    nm=C2.read_cstr(td+8,80) if td else None
    s0=C2.u32(vb)
    s1=C2.u32(vb+4)
    print('%-22s vt=%08X slot0=%08X slot1=%08X col=%08X name=%s' % (name,vb,s0 or 0,s1 or 0,col or 0,nm))
