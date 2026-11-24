# -*- coding: utf-8 -*-
"""生成 delta.tsv 与 base_rate.tsv（每条语义独立，不共用整批 reason）。"""
import os

D = r"D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/NAMED_PUSH_S12_B1"

ROWS = [
 ("00442230", "BuildingClass::vslot91",
  "S12 BuildingClass::vslot91 —— ③b② 成立：站点 0x4424BB 字节 `ff 52 10` = call dword ptr [edx+0x10]"
  "（edx 为栈上临时向量的 vptr，[esp+0x14] 处写入 0x7E180C；同族路径写 0x7E17AC）；0x4424BE `83 f8 ff` = cmp eax,-1；"
  "0x4424C1 `74 25` = je 0x4424E8。被调是该容器 slot 4（+0x10）：vptr 0x7E180C → [-4]=COL 007FA6D8 → RTTI "
  "`DynamicVectorClass/VectorClass<PAVTechnoClass>` → slot4 = 0x40BA80，其 0x40BAAC `or eax,0xFFFFFFFF`、"
  "0x40BAB0 `ret 4`；另一可能 vptr 0x7E17AC → COL 007FA640 → `DynamicVectorClass<PAVTechnoClass>` → slot4 = 0x40BB90，"
  "其 0x40BBAF `or eax,0xFFFFFFFF`、0x40BBB3 `ret 4` ⇒ 两条可能 vptr 下「未找到 = -1、命中 = 下标」均可字节伪证。"
  "调用方真的拿 -1 分支，两路动作不同：未命中跳 0x4424E8 跳过整段；命中则 0x4424CE 回写 count-1、"
  "0x4424D9 `mov edx,[ecx+eax*4]` / 0x4424DC `mov [ecx+eax*4-4],edx` 前移压缩（非栈写）。"
  "cmp 与 je 之间无 eax 覆写；单 call 非多路同一 call。"
  "语义：在栈上临时 TechnoClass* 向量中 Find 目标（-1 = 未命中），命中则按下标做压缩移除，未命中跳过。"
  "② 槽 007E4028（vt 007E3EBC +0x16C，slot#91）的 4B 值即本 entry，RTTI COL=007FC360(sig=0) → TD=00818D60 → "
  "name=.?AVBuildingClass@@，主表槽 0 = 00410260，槽号与线索 vslot91 自洽；"
  "④ 活 vt 构造安装点 0x0043B71F（in_func=0043B680，`mov dword ptr [esi],0x7E3EBC`，atexit=False，"
  "收尾 `mov eax,esi; ret 4` 返 this ⇒ 构造器非析构器）把主表装入活对象 [obj+0]；"
  "②④ 不同源（.rdata RTTI 数据链 vs .text 构造安装指令）。"),
 ("00447210", "BuildingClass::vslot29",
  "S12 BuildingClass::vslot29 —— ③b② 成立：站点 0x447267 `e8 54 8c 2b 00` 字节 = call 0x6FFEC0（direct，this=esi，"
  "两参数 push [esp+0x20] / push ebp）；0x44726C `8b d8` = mov ebx,eax；0x44726E `83 fb 08` = cmp ebx,8；"
  "0x447271 `75 09` = jne 0x44727C。被调 0x6FFEC0 的返回约定字节可伪证：12 个 ret 中 11 个带常量且一律 `ret 0xc` —— "
  "0x7000E8 / 0x700169 / 0x70018E `mov eax,4`、0x700110 `mov eax,8`、0x6FFF8A / 0x7005E3 `mov eax,7`、"
  "0x700569 `mov eax,5`、0x7001E6 `mov eax,0x1A`、0x6FFFD8 / 0x700003 `mov eax,0x37`、0x7005EF `xor eax,eax`(0)，"
  "是**多值状态码集合** {0,4,5,7,8,0x1A,0x37}（不是 0/1 布尔）。调用方真的拿它分派且各路动作不同："
  "rc==8 → 0x447279 `pop esi; pop ebp; pop ebx; add esp,0xC; ret 8` 把 8 原样上抛、不再做事；"
  "rc!=8 → 0x44727C `83 fb 04` = cmp ebx,4、0x447280 `0f 85 e0 00 00 00` = jne 0x447366，rc==4 路进 0x447286 读 "
  "`[Type+0xCD1]`、比对 `[this+0x21C]` 与全局 0xA83D4C 等实质工作；rc!=4 → 0x447366 `83 fb 05` = cmp ebx,5、"
  "0x447369 `jne 0x4473C7`，rc==5 路进 0x44736B `push 0; mov ecx,esi; call [edx+0x3F8]`，其余落默认路 0x4473C7。"
  "比较与跳转之间无 ebx 覆写；单 call 非多路同一 call。"
  "语义：建筑动作分派——先调 0x6FFEC0 取动作/状态码（0/4/5/7/8/0x1A/0x37），按码分支：8 直接上抛返回，"
  "4 与 5 各走一条实质处理分支，其余落默认。"
  "② 槽 007E3F30（vt 007E3EBC +0x74，slot#29）的 4B 值即本 entry，RTTI COL=007FC360(sig=0) → TD=00818D60 → "
  "name=.?AVBuildingClass@@，主表槽 0 = 00410260，槽号与线索 vslot29 自洽；"
  "④ 活 vt 构造安装点 0x0043B71F（in_func=0043B680，atexit=False，构造器）把主表装入活对象 [obj+0]；"
  "②④ 不同源（.rdata RTTI 数据链 vs .text 构造安装指令）。"),
 ("00447F10", "BuildingClass::vslot240",  "S12 BuildingClass::vslot240 —— ③b② 成立：站点 0x447FD4 `e8 ...` = call 0x6FC0B0（direct，this=esi，"
  "三参数 push [esp+0x18]/[esp+0x14]/[esp+0x10]）；0x447FD9 `8b e8` = mov ebp,eax；0x447FDB `85 ed` = test ebp,ebp；"
  "0x447FDD `75 73` = jne 0x448052。被调 0x6FC0B0 的返回约定字节可伪证（按其 atlas 边界自入口对齐解码，"
  "32 个 ret 一律 `ret 0xC`）：0x6FCD20 `xor eax,eax`（`33 c0`）→ 0x6FCD26 ret = **成功 0**；失败出口逐条带常量，"
  "如 0x6FCD11 `mov eax,8`（`b8 08 00 00 00`）→ 0x6FCD1A ret、0x6FCD2C `mov eax,6`（`b8 06 00 00 00`）→ 0x6FCD35 ret、"
  "0x6FCBA1/0x6FCBC1/0x6FCBDA/0x6FCC51/0x6FCCB1/0x6FCCE2 `mov eax,5`（`b8 05 00 00 00`），"
  "另有 `mov eax,3` 7 处、`mov eax,1`、`mov eax,9`。"
  "调用方真的拿它分支且两路动作不同：非零路 0x448052 `pop edi; mov eax,ebp; pop esi; pop ebp; ret 0xC` "
  "把被调错误码原样上抛；零路继续 0x447FE3 `call [edx+0x3FC]`(slot 255)、0x447FF8 `call [eax+0x4E8]`(slot 314) 等后续判定。"
  "判的是 ebp，eax 未被覆写；单 call 非多路同一 call。"
  "语义：建造/放置合法性判定——先查占位与类型状态，再调 0x6FC0B0 做放置判定并把其错误码原样上抛"
  "（0=成功，1/3/5/6/8/9=各类失败），自身另返回 2/3/5/6 表示不同拒绝原因"
  "（0x448049 `mov eax,2`、0x447FBA `mov eax,3`、0x44805C `mov eax,5`、0x447F66 与 0x447FA5 `mov eax,6`）。"
  "② 槽 007E427C（vt 007E3EBC +0x3C0，slot#240）的 4B 值即本 entry，RTTI COL=007FC360(sig=0) → TD=00818D60 → "
  "name=.?AVBuildingClass@@，主表槽 0 = 00410260，槽号与线索 vslot240 自洽；"
  "④ 活 vt 构造安装点 0x0043B71F（in_func=0043B680，atexit=False，构造器）把主表装入活对象 [obj+0]；"
  "②④ 不同源（.rdata RTTI 数据链 vs .text 构造安装指令）。"),
 ("0044E8F0", "BuildingClass::vslot10",
  "S12 BuildingClass::vslot10 —— ③b② 成立：站点 0x44EA8F 字节 `ff 52 10` = call dword ptr [edx+0x10]"
  "（edx = 本对象成员向量的 vptr，存于 [esi+0x66C]；0x44EA7E `lea edi,[esi+0x66C]` 即 this）；"
  "0x44EA92 `83 f8 ff` = cmp eax,-1；0x44EA95 `74 21` = je 0x44EAB8。"
  "该成员 vptr 由本类构造器 0x43B6DB `c7 86 6c 06 00 00 c8 43 7e 00`（mov dword ptr [esi+0x66C],0x7E43C8）安装；"
  "0x7E43C8 → [-4]=COL 007FC298 → RTTI `.?AV?$DynamicVectorClass@PAVInfantryClass@@@@` → "
  "slot4（0x7E43D8）= 0x45A610 = Find，其 0x45A62F `or eax,0xFFFFFFFF`、0x45A633 `ret 4` ⇒ 未找到 = -1 可字节伪证、命中 = 下标。"
  "调用方真的拿 -1 分支且两路动作不同：未命中跳 0x44EAB8 跳过；命中则 0x44EA9E `dec ecx`、"
  "0x44EAA1 `mov [edi+0x10],ecx` 回写计数、0x44EAAA / 0x44EAAD `mov edx,[ecx+eax*4]; mov [ecx+eax*4-4],edx` "
  "前移压缩（非栈写）。cmp 与 je 之间无 eax 覆写；单 call 非多路同一 call"
  "（同函数内 0x44EAD9 是对另一成员容器 this+0x684 的独立 Find，vptr 由 0x43B709 安装同一 0x7E43C8）。"
  "语义：对本对象内成员 DynamicVectorClass<InfantryClass*>（this+0x66C 与 +0x684）虚派发 Find 目标"
  "（-1 = 未命中），命中则 count-- 并把后续元素前移一格压缩移除，未命中直接跳过。"
  "② 槽 007E3EE4（vt 007E3EBC +0x28，slot#10）的 4B 值即本 entry，RTTI COL=007FC360(sig=0) → TD=00818D60 → "
  "name=.?AVBuildingClass@@，主表槽 0 = 00410260，槽号与线索 vslot10 自洽；"
  "④ 活 vt 构造安装点 0x0043B71F（in_func=0043B680，atexit=False，构造器）把主表装入活对象 [obj+0]；"
  "②④ 不同源（.rdata RTTI 数据链 vs .text 构造安装指令）。"),
]

lines = ["entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path"]
for e, nm, sem in ROWS:
    lines.append("%s\tS12\t%s\t%s\t[已证]\t%s/EVIDENCE/ROW_%s.txt" % (e, nm, sem, D, e))
with open(os.path.join(D, "delta.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines) + "\n")

with open(os.path.join(D, "base_rate.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("batch\trows_checked\tring2_ok\tring3b_ok\tring4_ok\tall_four\trate\n")
    f.write("S12_B1\t18\t18\t4\t18\t4\t%.4f\n" % (4 / 18.0))

print("delta.tsv 行数 =", len(ROWS), " rate =", round(4 / 18.0, 4))
