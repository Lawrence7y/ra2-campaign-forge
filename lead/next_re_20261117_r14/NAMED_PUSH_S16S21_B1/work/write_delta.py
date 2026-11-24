# -*- coding: utf-8 -*-
"""生成 delta.tsv（只放四环齐全的行）与 base_rate.tsv。"""
import os

DIR = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S16S21_B1"
DPATH = "D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/NAMED_PUSH_S16S21_B1/EVIDENCE"

ROWS = [
 ("0046D000", "S21", "CampaignClass::slot5",
  "S21 CampaignClass::slot5 —— ③b② 合同（HRESULT/E_POINTER 判负，流读入后构造）：站点 "
  "call 0x00410380@0x0046D00B(e8 70 33 fa ff)；test eax,eax@0x0046D010(85 c0)；jl 0x0046D041@0x0046D012(7c 2d)。"
  "被调 0x00410380 空参 0x00410389 mov eax,0x80004003(b8 03 40 00 80)=E_POINTER、正路 0x0041039E call [eax+0xc](ff 50 0c)"
  "=IStream::Read 槽，004103A3 jl 原样携负 HRESULT 跳到 0x004103D6，成功路 0x004103CD call [ebp+0xc] 的返回值即 eax ⇒ "
  "失败返负 HRESULT（含 0x80004003）/成功返 0(S_OK)，多值非布尔。失败路 0x0046D041 5e;c2 08 00 原样返回不做构造；"
  "成功路 0x0046D01F e8 3c 39 fa ff call 0x00410960(基类构造，内含装 0x7E2000/0x7E1FE4/0x7E1FDC/0x7E1FD4 四张基表) 后 "
  "0x0046D024 c7 06 28 4a 7e 00 装主表 0x7E4A28，0x0046D02A/0046D031/0046D038 再装 0x7E4A0C/0x7E4A04/0x7E49FC，"
  "0x0046D03F 33 c0 返 0；两路动作真不同、test 与 jl 之间无 eax 覆写、全函数仅此一处被检 call、非模板假句。"
  "语义：CampaignClass 虚槽5（流读入并重建本对象）—— 先以 0x410380 对入参做流读入校验，失败原样携负 HRESULT 早退、不构造，"
  "成功且 this 非空时调基类构造并装入本类四张虚表后返回 S_OK。"
  "② 槽 007E4A3C(vt 007E4A28 +0x14，slot#5，字节 00 d0 46 00) 的 4B 值即本 entry，[vt-4]=007E4A24→COL 007FC920(sig 0)→"
  "pTD 0081B170(绝对 VA)→TD+8 内联串 0081B178='.?AVCampaignClass@@'，vt[0]=00410260 确认主表，槽号自洽。"
  "④ 活 vt 构造器安装点 0x0046CB70(c7 06 28 4a 7e 00，in_func=0046CB60 构造器，mov esi,ecx 取 this、call 0x410800 基类初始化、"
  "插入全局数组 0x00A83CF8、0046CC06 mov eax,esi 返回 this；atexit=False)，其唯一调用者 0x006C02D1 前有 0x006C02BC push 0x3a0 + "
  "0x006C02C1 call 0x7C8E17(operator new) ⇒ 活对象上装活表；该表 5 个 imm 写点中 0x0046D096 在删除析构器 0x0046D090 体内"
  "(0046D106 test byte[esp+0xc],1 + 0046D10E call 0x7C8B3D + ret 4)按㉓排除、0x0046D024 在本行自身体内不可自证；②④ 不同源"
  "（.rdata RTTI 数据链 vs .text 构造安装指令）。",
  "ROW_0046D000.txt"),

 ("0046D090", "S21", "CampaignClass::slot8",
  "S21 CampaignClass::slot8 —— ③b② 合同（容器 FindIndex 的 −1 下标哨兵，析构体内摘链）：站点 "
  "0x0046D0CA ff 52 10 call dword ptr [edx+0x10]，edx 由 0x0046D0B6 8b 15 f8 3c a8 00 取自全局容器 0x00A83CF8 的活 vptr；"
  "0x0046D0CD 83 f8 ff cmp eax,-1；0x0046D0D0 74 2d je 0x0046D0FF。被调静态钉死：0x00A83CF8 的 vptr 写点全镜像仅 2 处——"
  "0x004E6EFD 装 0x7E9FE4(RTTI .?AV?$DynamicVectorClass@PAVCampaignClass@@@@，活表)，0x004E6F28 装 0x7EA004"
  "(RTTI .?AV?$VectorClass@PAVCampaignClass@@@@，位于 004E6F20 体内，而 0x004E6EE2 push 0x4E6F20 + 0x004E6F16 call 0x7C978A "
  "即 atexit 注册的全局析构器 ⇒ 死表，按㉓排除)。活表 0x7E9FE4 的 slot#4(+0x10)=0x004EC530，其体内 0x004EC543 cmp [ecx],esi 逐元素比、"
  "0x004EC545 je 命中返下标、0x004EC54F 83 c8 ff or eax,0xffffffff 未找到返 −1 ⇒ 失败=−1 下标哨兵/成功=元素下标，多值可伪证。"
  "未找到路 0x0046D0FF 跳过搬移直接 8b ce 调基类析构；找到路 0x0046D0DF mov [0xA83D08],ecx 计数减一 + 0x0046D0EE/0x0046D0F1 前移循环"
  "(0x0046D0F1 89 54 81 fc 数组非栈写) + 0x0046D0FD 7c e8 回跳，两路动作真不同、cmp 与 je 间无 eax 覆写、单一 call 站点。"
  "语义：CampaignClass 标量删除析构器（虚槽8）—— 装回本类四张虚表、调 0x7258D0 摘除自身，对全局 CampaignClass 容器做 FindIndex，"
  "命中(≠−1)则后继元素前移并把计数减一、未命中(−1)跳过搬移，再调基类析构 0x4109C0，delete 标志为 1 时 operator delete 释放并返回 this。"
  "② 槽 007E4A48(vt 007E4A28 +0x20，slot#8，字节 90 d0 46 00) 的 4B 值即本 entry，[vt-4]=007E4A24→COL 007FC920→pTD 0081B170→"
  "TD+8='.?AVCampaignClass@@'，vt[0]=00410260 主表。④ 活 vt 构造器安装点 0x0046CB70(in_func=0046CB60 构造器，atexit=False)，"
  "其调用者 0x006C02D1 前有 0x006C02BC push 0x3a0 + 0x006C02C1 call 0x7C8E17(operator new)；该表 5 写点中 0x0046D096 正是本行删除"
  "析构器体内(0046D106 test byte[esp+0xc],1 + 0046D10E call 0x7C8B3D)，按㉓排除后取行外构造器；②④ 不同源。",
  "ROW_0046D090.txt"),

 ("0071B1B0", "S16", "TemporalClass::slot8",
  "S16 TemporalClass::slot8 —— ③b② 合同（容器 FindIndex 的 −1 下标哨兵，析构体内摘链）：站点 "
  "0x0071B1E3 ff 52 10 call dword ptr [edx+0x10]，edx 由 0x0071B1D8 8b 15 60 ec b0 00 取自全局容器 0x00B0EC60 的活 vptr；"
  "0x0071B1E6 83 f8 ff cmp eax,-1；0x0071B1E9 74 2d je 0x0071B218。被调静态钉死：0x00B0EC60 的 vptr 写点全镜像仅 2 处——"
  "0x0071A3ED 装 0x7F5114(RTTI .?AV?$DynamicVectorClass@PAVTemporalClass@@@@，活表)，0x0071A418 装 0x7F5134"
  "(RTTI .?AV?$VectorClass@PAVTemporalClass@@@@，位于 0071A410 体内，而 0x0071A3D2 push 0x71A410 + 0x0071A406 call 0x7C978A "
  "即 atexit 注册的全局析构器 ⇒ 死表，按㉓排除)。活表 0x7F5114 的 slot#4(+0x10)=0x0071B4D0，其体内 0x0071B4E3 cmp [ecx],esi 逐元素比、"
  "0x0071B4E5 je 命中返下标、0x0071B4EF 83 c8 ff or eax,0xffffffff 未找到返 −1 ⇒ 失败=−1 下标哨兵/成功=元素下标，多值可伪证。"
  "未找到路 0x0071B218 跳过搬移直接 8b ce 调基类析构；找到路 0x0071B1F8 mov [0xB0EC70],ecx 计数减一 + 0x0071B207/0x0071B20A 前移循环"
  "(0x0071B20A 89 54 81 fc 数组非栈写) + 0x0071B216 7c e8 回跳；两路动作真不同、cmp 与 je 间无 eax 覆写、单一 call 站点。"
  "语义：TemporalClass 标量删除析构器（虚槽8）—— 装回本类四张虚表，对全局 TemporalClass 容器做 FindIndex，命中(≠−1)则后继元素前移"
  "并把计数减一、未命中(−1)跳过搬移，再调基类析构 0x4101F0，delete 标志为 1 时 operator delete 释放并返回 this。"
  "② 槽 007F51A0(vt 007F5180 +0x20，slot#8，字节 b0 b1 71 00) 的 4B 值即本 entry，[vt-4]=007F517C→COL 0080C328→pTD 008445C8→"
  "TD+8='.?AVTemporalClass@@'，vt[0]=00410260 主表。④ 活 vt 构造器安装点 0x0071A467(c7 06 80 51 7f 00，in_func=0071A450 构造器，"
  "mov esi,ecx 取 this、call 0x410170 基类初始化、插入全局数组 0x00B0EC60、0071A4D6 mov eax,esi 返回 this；atexit=False)，其调用者 "
  "0x006C074C 前有 0x006C073C push 0x50 + 0x006C073E call 0x7C8E17(operator new)；该表 6 写点中 0x0071B1BD 正是本行删除析构器体内"
  "(0071B21F test byte[esp+0xc],1 + 0071B227 call 0x7C8B3D)，按㉓排除后取行外构造器；②④ 不同源。",
  "ROW_0071B1B0.txt"),
]

with open(os.path.join(DIR, "delta.tsv"), "w", encoding="utf-8", newline="") as f:
    f.write("entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\n")
    for e, sub, nm, sem, ev in ROWS:
        assert "\t" not in sem and "\n" not in sem, e
        f.write("%s\t%s\t%s\t%s\t[已证]\t%s/%s\n" % (e, sub, nm, sem, DPATH, ev))

with open(os.path.join(DIR, "base_rate.tsv"), "w", encoding="utf-8", newline="") as f:
    f.write("batch\trows_checked\tring2_ok\tring3b_ok\tring4_ok\tall_four\trate\n")
    f.write("B1\t7\t6\t3\t6\t3\t0.4286\n")

print("delta.tsv 行数（不含表头）=%d" % len(ROWS))
for e, sub, nm, sem, ev in ROWS:
    print("  %s  %s  %s  len(sem)=%d" % (e, sub, nm, len(sem)))
print("base_rate: B1\t7\t6\t3\t6\t3\t0.4286")
