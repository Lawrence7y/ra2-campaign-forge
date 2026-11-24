# -*- coding: utf-8 -*-
import io

rows = [
    ("0046D000", "S21", "PASS",
     "vt=007E4A28 slot5@007E4A3C=entry(bytes 00 d0 46 00);COL=007FC920 pTD=0081B170 .?AVCampaignClass@@;vt[0]=00410260",
     "3b2",
     "ctor install 0046CB70 mov[esi],7E4A28 in_func=0046CB60 (base ctor call 00410800; caller 006C02D1 preceded by push 0x3a0@006C02BC + call 7C8E17@006C02C1 operator new)",
     "no",
     "0046D000 69B:call 00410380@0046D00B(50/56 压 stream+this)/test eax,eax@0046D010(85c0)/jl 0x46D041@0046D012(7c2d) 越过 xor 保留负码;成功路 call 00410960@0046D01F(基类构造内含装 7E2000/7E1FE4/7E1FDC/7E1FD4)+装主表 7E4A28@0046D024+0x7E4A0C/0x7E4A04/0x7E49FC,收尾 xor eax,eax@0046D03F 返0;00410380 90B 空流 E_POINTER 80004003@00410389 正路 call[eax+0xc]=IStream::Read 读方向;㉓全枚举5写点:0046CB70(构造器→④锚)/0046CC16(非删除析构器0046CC10)/0046CEC6(工厂内 operator new 后装表)/0046D024(本行体内不可自证)/0046D096(删除析构器0046D090: test byte[esp+c],1@0046D106+call 7C8B3D@0046D10E+ret4@0046D11A 已排除),atexit写点0"),
    ("0046D090", "S21", "PASS",
     "vt=007E4A28 slot8@007E4A48=entry(bytes 90 d0 46 00);COL=007FC920 pTD=0081B170 .?AVCampaignClass@@;vt[0]=00410260",
     "3b2",
     "ctor install 0046CB70 in_func=0046CB60 (outside row;caller 006C02D1 preceded by push 0x3a0+call 7C8E17 operator new);row's own dtor write 0046D096 excluded per ㉓",
     "no",
     "0046D090 删除析构器:0046D096装4表/call 7258D0@0046D0B1/mov edx,[0xA83CF8]@0046D0B6/call[edx+0x10]@0046D0CA FindItemIndex/cmp eax,-1@0046D0CD(83f8ff)/je 0x46D0FF@0046D0D0(742d) 哨兵真被检查并分支;命中路 mov[0xA83D08],ecx@0046D0DF(Count-1)+mov[ecx+eax*4-4],edx@0046D0F1(非栈写)+jl回边@0046D0FD,未命中路直接跳/基类析构 004109C0@0046D101/delete标志 test byte[esp+c],1@0046D106+call 7C8B3D@0046D10E+ret4@0046D11A;容器0xA83CF8 vptr仅2写点:004E6EFD装7E9FE4(DynamicVectorClass活表,宿主004E6EE0 atexit=False)与004E6F28装7EA004(基类死表,宿主004E6F20 而004E6EE2 push 0x4e6f20+004E6F16 call 7C978A=atexit 已排除);活表slot4(+0x10)=004EC530 未命中 or eax,-1@004EC54F;④锚0046CB70行外构造器"),
    ("0071B1B0", "S16", "PASS",
     "vt=007F5180 slot8@007F51A0=entry(bytes b0 b1 71 00);COL=0080C328 pTD=008445C8 .?AVTemporalClass@@;vt[0]=00410260",
     "3b2",
     "ctor install 0071A467 mov[esi],7F5180 in_func=0071A450 (base init call 00410170; sole caller 006C074C preceded by push 0x50@006C073C + call 7C8E17@006C073E operator new)",
     "no",
     "0071B1B0 删除析构器:0071B1BD装4表/call[edx+0x10]@0071B1E3(edx=[0xB0EC60]活vptr,取自0071B1D8)/cmp eax,-1@0071B1E6(83f8ff)/je 0x71B218@0071B1E9(742d) 哨兵真被分支;命中路 mov[0xB0EC70],ecx@0071B1F8+mov[ecx+eax*4-4],edx@0071B20A非栈写+jl回边@0071B216,未命中路跳过;基类析构 004101F0@0071B21A/delete标志 test byte[esp+c],1@0071B21F+call 7C8B3D@0071B227+ret4@0071B233;容器0xB0EC60 vptr仅2写点:0071A3ED装7F5114(DynamicVectorClass活表,宿主0071A3D0 atexit=False)与0071A418装7F5134(VectorClass死表,宿主0071A410 而0071A3D2 push 0x71a410+0071A406 call 7C978A=atexit 已排除);活表slot4(+0x10)=0071B4D0 未命中 or eax,-1@0071B4EF;㉓全枚举6写点中仅0071B1BD在本行体内、atexit 0;④锚0071A467行外构造器;缺陷:第4列把槽址写成0071B1A0(实为007F51A0)属数字转置笔误,vt/slot#/槽值字节三项全对故不影响结论"),
]

with io.open("verdict.tsv", "a", encoding="utf-8", newline="\n") as f:
    for r in rows:
        f.write("\t".join(r) + "\n")
print("appended", len(rows))

# sanity: columns + counts
lines = io.open("verdict.tsv", encoding="utf-8").read().rstrip("\n").split("\n")
print("total lines", len(lines))
for l in lines:
    p = l.split("\t")
    assert len(p) == 8, (len(p), p[0])
    print(p[0], p[1], p[2], p[4], p[6])
