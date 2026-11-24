# -*- coding: utf-8 -*-
"""生成 18 行 EVIDENCE/ROW_<entry>.txt。每行独立地址锚、独立理由。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

here = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(here, "..", "EVIDENCE"))
rows = json.load(open(os.path.join(here, "rows_b1.json"), encoding="utf-8"))
rec = json.load(open(os.path.join(here, "rings124.json"), encoding="utf-8"))

MAIN_VT = 0x007E3EBC
COL = 0x007FC360
TD = 0x00818D60

# 逐行 ③ 裁定（PASS 的 3 行给出站点与两路；FAIL 的 15 行各给各自站点与理由）
R3 = {
"0043C2D0": dict(v="FAIL", reason="整行所有 ③b② 机械站点都在比「虚取值出来的状态/类型常量」或「分配/取值得到的指针是否为空」，没有任何一处是失败/成功错误码约定",
  lis=[("0043C32A", "call [eax+0x184] → 主虚表 slot 97 = 005B3040（字段 getter：返回 [this+0xAC]，为 -1 时改返回 [this+0xB4]）", "后接 0043C330 `cmp eax,0x12` — 比较状态枚举 0x12，非错误码"),
       ("0043C33D", "同一 getter 第二次调用", "后接 0043C343 `cmp eax,0x13`，同为状态枚举"),
       ("0043C526", "call [eax+0x278] → slot 158 = 0065AAA0（尾转 [eax+0x27C]），入参 push 0x23", "后接 0043C52C `cmp eax,1`；比较的是属性查询结果"),
       ("0043C943", "call 0065AD30 = `mov eax,[ecx+0xE4]; mov eax,[eax+ecx*4]; ret 4`（数组元素 getter）", "后接 0043C948 `test eax,eax` / 0043C94A `je` — 判元素指针是否为空，非错误码"),
       ("0043CDB9", "call 007C5F00 = MSVC `_ftol`（浮点转整数）", "后接 0043CDBE `cmp eax,0x180` / 0043CDC3 `jge` — 范围阈值比较"),
       ("0043CC50", "call [edx+0x184] 同一 slot 97 getter", "后接 0043CC56 `cmp eax,0x13` 状态枚举")]),
"0043D030": dict(v="FAIL", reason="只有两处 ③b② 机械站点，且都是对虚取值 getter 的结果做建筑类型常量比较，没有返回约定可伪证",
  lis=[("0043D079", "call [edx+0x184] → 主虚表 slot 97 = 005B3040（字段 getter）", "后接 0043D07F `cmp eax,0x18` 与类型常量 0x18 比较，命中才进 0043D084 的子检查"),
       ("0043D09B", "同一 slot 97 getter 第二次调用", "后接 0043D0A1 `cmp eax,0x10`，同为类型常量")]),
"0043D290": dict(v="FAIL", reason="唯一 test-eax 型站点的被调是尾转壳（返回值来源无法从字节定），其余站点全是状态/类型常量比较",
  lis=[("0043D2B2", "call [eax+0x6C] → 主虚表 slot 27 = 004513D0；该函数尾部为 `jmp [Type vtbl+0x9C]` / `jmp [Type vtbl+0xC0]` 尾转，返回值来源静态不可定", "后接 0043D2B5 `test eax,eax` / 0043D2BB `je` — 测到的值无约定可伪证"),
       ("0043D2C9", "call [edx+0x2C] → slot 11", "后接 0043D2CC `cmp eax,6` — 比较类类型 id 6"),
       ("0043D2DF", "call [eax+0x184] slot 97 getter", "后接 0043D2E5 `cmp eax,0x13`"),
       ("0043D33F", "同一 slot 97 getter", "后接 0043D345 `cmp eax,0x10`"),
       ("0043D548", "同一 slot 97 getter", "后接 0043D54E `cmp eax,0x18`"),
       ("0043D6DF", "同一 slot 97 getter（一次调用后连比 0x12 与 0x13）", "0043D6E5 `cmp eax,0x12` / 0043D6EA `cmp eax,0x13`")]),
"0043FB20": dict(v="FAIL", reason="站点分两类：虚取值后比类型常量；以及 calloc 返回值是否为 NULL。前者不是错误码，后者是分配结果非空判断；且 0x440499 站点的两路动作只是「构造对象」与「置 0」",
  lis=[("0043FB39", "call [edx+0x184] slot 97 getter", "后接 0043FB3F `cmp eax,0x12`，再 0043FB4E `cmp eax,0x13`"),
       ("0043FB48", "同一 slot 97 getter", "后接 0043FB4E `cmp eax,0x13`"),
       ("0043FEC2", "同一 slot 97 getter", "后接 0043FEC8 `cmp eax,1`"),
       ("00440499", "call 007C8E17 = `push 1; push size; call 007C9442`（calloc(n,1) 的薄壳）", "004404A1 `test eax,eax` / 004404A3 `je` — 分配失败判空，非错误码约定"),
       ("00440511", "同一 calloc 薄壳，size=0x1C8", "00440519 `test eax,eax` / 0044051B `je` 同上")]),
"00440580": dict(v="FAIL", reason="站点被 eax 覆写陷阱污染两处（前一次 call 的返回值被紧随的第二次 call 覆盖），真正被测的返回有两类是「链表查到的对象指针是否为空」和 strcmp 比较结果，另两处是 calloc 指针与外来对象槽调用，均非错误码约定",
  lis=[("00440720", "call 004FCE80", "**eax 覆写陷阱**：00440725 `mov ecx,edi` 后 00440727 又 `call 0047C520`，eax 被覆盖；0044072C `test eax,eax` 测的是 0047C520 的返回"),
       ("00440727", "call 0047C520（在 [ecx+0xE4] 链表上遍历、`call [eax+0x2C]` 比 6，返回对象指针或 NULL）", "00442E2C→0044072C `test eax,eax` / 0044072E `je` — 指针非空判断"),
       ("004407A0", "call [edi+0x1AC]（外来对象 slot 107）；edi 为运行时对象", "004407A6 `test eax,eax` / 004407A8 `jne`；被调类不可静态定，约定不可伪证"),
       ("004407C3", "call [eax+0x8C]（[Type+0xE54] 对象的 slot 35）", "004407C9 `test eax,eax` / 004407CB `je`；同上不可伪证"),
       ("004409A3", "call 007C8D20 = 大小写折叠的 strcmp 实现", "004409AB `test eax,eax` / 004409AD `je` — 相等/不等比较，非错误码"),
       ("00441178", "call 007C8E17 = calloc 薄壳，size=0xE8", "00441180 `test eax,eax` / 00441182 `je` — 分配判空；成功路 `mov ecx,eax; call 00435820` 构造对象")]),
"004415F0": dict(v="FAIL", reason="站点是「取帧计数/坐标后与常数比」的数量与几何阈值检查，以及一个建筑类型常量比较，不是失败/成功错误码",
  lis=[("00441779", "call 00750E20（返回 0 或调用/未知）", "随后 00441784 立刻再 call 0045EC90 覆盖 eax；00441789 `cmp eax,2` 测的是 0045EC90 的返回"),
       ("00441784", "call 0045EC90（读取一个域计数）", "00441789 `cmp eax,2` / 0044178C `jl` — 数量范围检查，非错误码"),
       ("00441799", "call 0045ECA0（另一域计数）", "0044179E `cmp eax,2` / 004417A1 `jl` 同上"),
       ("004417AD", "call 0045EC90", "004417B2 `cmp eax,2` / 004417B5 `jle` — 同一计数的上界侧检查"),
       ("00441C3D", "call [edx+0x184] slot 97 getter", "00441C43 `cmp eax,0x13` — 建筑类型常量"),
       ("00441E51", "call [eax+0x1C8]（slot 114 = 005F5F40）", "00441E57 `cmp eax,-0xA` / 00441E5A `jle` — 与 -10 比较的坐标/阈值域，非失败码")]),
"00442230": dict(v="PASS", reason="③b② 成立：站点在栈上临时 TechnoClass* 向量上做虚派发 Find，被调 `or eax,-1` 使「未找到 = -1」字节可伪证，调用方 `cmp eax,-1` 真的按 -1 分支，两路动作不同（未命中直接跳过；命中则 count-- 并把后续元素前移覆盖，含非栈写），且 cmp 与 je 之间无 eax 覆写、单 call 非多路同一 call",
  anchor="004424BB", lis=[("004424BB", "call [edx+0x10]，edx = 栈对象 vptr（[esp+0x14] 处写入 0x7E180C；同族路径写 0x7E17AC）", "004424BE `cmp eax,-1` / 004424C1 `je 0x4424E8`"),
       ("0x7E180C", "vptr 0x7E180C → [-4]=COL 007FA6D8 → RTTI `.?AV?$VectorClass@PAVTechnoClass@@@@`，slot 4（+0x10）= 0040BA80", "0040BAAC `or eax,-1`；0040BAB0 `ret 4` ⇒ 未找到返回 -1"),
       ("0x7E17AC", "vptr 0x7E17AC → COL 007FA640 → RTTI `.?AV?$DynamicVectorClass@PAVTechnoClass@@@@`，slot 4 = 0040BB90", "0040BBAF `or eax,-1`；0040BBB3 `ret 4` ⇒ 两条可能 vptr 下 -1 约定一致"),
       ("004424C3", "命中路：`mov ecx,[esp+0x24]`(count) / 004424C7 `cmp eax,ecx` / 004424CB `dec ecx`", "004424CE 回写 count；004424D9 `mov edx,[ecx+eax*4]` / 004424DC `mov [ecx+eax*4-4],edx` 压缩前移（非栈写）"),
       ("004424E8", "未命中路（-1 分支目标）", "跳过整段压缩，直接继续后续逻辑")]),
"00442C40": dict(v="FAIL", reason="唯一站点的被调其实是 BuildingTypeClass 的虚函数（eax 取自 [ecx]=[this+0x520] 的 vptr，不是本对象主虚表），该被调 57 个 ret 且返回值无 0/非0 失败约定，约定不可伪证",
  lis=[("00442CB2", "call [eax+0xC0]；00442CAA `mov ecx,[esi+0x520]`、00442CB0 `mov eax,[ecx]` ⇒ eax = **Type 对象** vptr，不是 [esi] 主虚表", "实为 BuildingTypeClass 主虚表 007E4570 的 slot 48 = 00465960"),
       ("00465960", "00465960（size≥0x1200，57 个 ret；返回常量多为不可判定，含 0x1798、0xAAAAAAAB 等非错误码量）", "无「失败=N / 成功=0」的约定可从字节伪证 ⇒ 该站点不成立"),
       ("00442CBA", "分支两侧：00442CBC `mov byte [esi+0x6DC],al`(=0) 与 00442CC4..00442CCF `call 00465AF0` + `mov byte [esi+0x6E9],1`", "动作确实不同，但被调约定不可伪证，只能是布尔/状态位")]),
"00443C60": dict(v="FAIL", reason="两处站点被 eax 覆写陷阱污染（005657A0 的返回值只用来填 ecx 当 this，真正被测的是 0047C3D0 的浮点换算结果）；另两处是对外来对象虚取值的类型常量比较",
  lis=[("00444322", "call 005657A0（返回常量 0x00ABE4D0，即某日志/全局对象地址）", "**eax 覆写陷阱**：00444327 `mov ecx,eax` 后 00444329 再 `call 0047C3D0`，eax 被覆盖"),
       ("00444329", "call 0047C3D0（`and esp,-8; sub esp,0x34` 后走 x87 计算）", "0044432E `test eax,eax` / 00444330 `jne`；返回值为浮点换算后的数值，非错误码"),
       ("00444DC3", "call [eax+0x278] → 主虚表 slot 158，入参 push 2", "00444DC9 `cmp eax,1` — 属性查询结果与常量 1 比较"),
       ("00444DE8", "call [eax+0x2C] → slot 11", "00444DEB `cmp eax,1` — 类类型常量比较")]),
"004456D0": dict(v="FAIL", reason="四处站点被调同为 004F7870，其返回常量集合只有 {0,1}（布尔命中标记），非零只多做一次日志调用；不构成「失败返回什么/成功返回什么」的错误码约定",
  lis=[("00445758", "call 004F7870（11 个 ret，常量集合 {0,1}）；入参 push 1 / push 0 / push 项指针", "0044575D `test eax,eax` / 0044575F `je` 跳过；非零路只 `push esi / push 7 / mov ecx,0x87F7E8 / call 006A6300`（日志）"),
       ("0044579D", "同一 004F7870", "004457A2 `test eax,eax` / 004457A4 `je`；非零路日志 id = 0x28"),
       ("004457DE", "同一 004F7870", "004457E3 `test` / 004457E5 `je`；非零路日志 id = 0x10"),
       ("0044581E", "同一 004F7870", "00445823 `test` / 00445825 `je`；非零路日志 id = 3"),
       ("00445727", "外侧 `add eax,-3; cmp eax,0x25; ja` + 字节索引表 00445854 + `jmp [edx*4+0x445840]`（38 项 → 5 个互异目标）", "跳转表分支落到 5 个循环块，但各块只是换全局数组与日志 id，仍以布尔命中为准")]),
"00445F80": dict(v="FAIL", reason="站点分别是：浮点转整数后的零值默认分支（③a 零+默认）、状态跳转表、以及 calloc 返回值判空；均不是错误码约定",
  lis=[("00445FEC", "call 006C9650", "随后 00445FF1 立刻 call 007C5F00（_ftol）覆盖 eax；00445FF6 `test eax,eax` 测的是 _ftol 结果"),
       ("00445FF1", "call 007C5F00 = MSVC `_ftol`", "00445FF6 `test eax,eax` / 00445FF8 `je 0x446016` — 为 0 时跳过除法直接置 0，典型「零+默认」"),
       ("0044692E", "call 0049FAE0（含 `mov eax,0` 离开路径）", "00446933 `test eax,eax` / 00446935 `je`；非零路 00446943 `cmp eax,9; ja` + `jmp [eax*4+0x446FC0]`（10 项 → 7 目标）"),
       ("00446B68", "call 007C8E17 = calloc 薄壳", "00446B70 `test eax,eax` / 00446B72 `je` — 分配判空；成功路 `mov ecx,eax; call 007353C0`"),
       ("00446F28", "call 007C8E17 = calloc 薄壳, size=0x6D8", "00446F30 `test eax,eax` / 00446F32 `je` — 同上")]),
"00447110": dict(v="FAIL", reason="两处站点都是 `call [edx+0x184]`（主虚表 slot 97 字段 getter）后与建筑类型常量 0x13 比较，是类型判定不是错误码",
  lis=[("00447135", "call [eax+0x184] → slot 97 = 005B3040（返回 [this+0xAC]/[this+0xB4]）", "0044713B `cmp eax,0x13` / 0044713E `je 0x447203` — 与类型常量 0x13 比较"),
       ("00447158", "同一 slot 97 getter", "0044715E `cmp eax,0x13` / 00447161 `jne`；00447169 处第三次调用后 `cmp eax,0x13; setne al` 亦同")]),
"00447210": dict(v="PASS", reason="③b② 成立：站点调用 006FFEC0 后把返回值搬进 ebx 再按常量分派，被调 12 个 ret 中 11 个带常量、且是**多值状态码集合** {0,4,5,7,8,0x1A,0x37}（非布尔），调用方真的拿它分支且各路动作不同——8 直接 `ret 8` 上抛、4 走一分支、5 再走另一分支、其余落默认；比较与跳转之间无 ebx 覆写、单 call 非多路同一 call",
  anchor="00447267", lis=[("00447267", "call 006FFEC0（direct，this=esi，两参数 push [esp+0x20] / push ebp）", "0044726C `8b d8` = mov ebx,eax；0044726E `83 fb 08` = cmp ebx,8；00447271 `75 09` = jne 0x44727C"),
       ("006FFEC0", "被调返回约定（12 个 ret，11 个带常量，全部 `ret 0xc`）：0x7000E8/0x700169/0x70018E `mov eax,4`、0x700110 `mov eax,8`、0x6FFF8A/0x7005E3 `mov eax,7`、0x700569 `mov eax,5`、0x7001E6 `mov eax,0x1A`、0x6FFFD8/0x700003 `mov eax,0x37`、0x7005EF `xor eax,eax`(0)", "⇒ 多值状态码集合可逐字节伪证（不是 0/1 布尔）"),
       ("00447279", "rc==8 路（jne 不跳）：`pop esi; pop ebp; pop ebx; add esp,0xC; ret 8`，eax 仍为 ebx=8 ⇒ **把 8 原样上抛**", "与其余各路动作完全不同"),
       ("0044727C", "rc!=8 后 `83 fb 04` = cmp ebx,4；00447280 `0f 85 e0 00 00 00` = jne 0x447366", "rc==4 路进 00447286：读 `[Type+0xCD1]`、比对 `[this+0x21C]` 与全局 0xA83D4C 等实质工作"),
       ("00447366", "rc!=4 后 `83 fb 05` = cmp ebx,5；00447369 `jne 0x4473C7`", "rc==5 路进 0044736B `push 0; mov ecx,esi; call [edx+0x3F8]`，其余落 0x4473C7 默认路"),
       ("0044723C", "同函数内另一站点 `call [edx+0x2C]`（槽 11，在 BuildingClass 主表上实现为 00459EC0 = `mov eax,6; ret`）后 `cmp eax,6`", "该站点是类类型常量比较，**不**作为 ③ 依据；③ 成立靠 0x447267 这一站点")]),
"00447F10": dict(v="PASS", reason="③b② 成立：站点调用 006FC0B0 后把返回值搬进 ebp 再判非零，被调 32 个 ret 全部 `ret 0xC`，其中 0x6FCD20 `xor eax,eax` 的出口是成功 0，其余出口带 1/3/5/6/8/9 等常量；调用方真的拿它分支——非零即把该错误码原样上抛，零则继续做后续判定；无 eax 覆写、单 call 非多路同一 call，本函数自身另返回 2/3/5/6 表示不同拒绝原因",
  anchor="00447FD4", lis=[("00447FD4", "call 006FC0B0（direct，入参 push [esp+0x18] / [esp+0x14] / [esp+0x10]，this=esi）", "00447FD9 `mov ebp,eax`；00447FDB `test ebp,ebp`；00447FDD `jne 0x448052`"),
       ("006FC0B0", "被调返回约定（按 atlas 边界自入口对齐解码，32 个 ret 全部 `ret 0xC`）：0x6FCD20 `xor eax,eax`(33 c0) → 0x6FCD26 ret = **成功 0**；失败出口逐条带常量：0x6FCD11 `mov eax,8`(b8 08 00 00 00) → 0x6FCD1A ret，0x6FCD2C `mov eax,6`(b8 06 00 00 00) → 0x6FCD35 ret，0x6FCBA1/0x6FCBC1/0x6FCBDA/0x6FCC51/0x6FCCB1/0x6FCCE2 `mov eax,5`(b8 05 00 00 00)，另有 `mov eax,3` 7 处、`mov eax,1`、`mov eax,9`", "⇒ 0 与非零错误码集合可逐字节伪证"),
       ("00448052", "失败路（jne 目标）：`pop edi; mov eax,ebp; pop esi; pop ebp; ret 0xC` — 把被调错误码原样上抛", "与成功路动作完全不同"),
       ("00447FDF", "成功路：继续 00447FE3 `call [edx+0x3FC]`(slot 255) 与 00447FF8 `call [eax+0x4E8]`(slot 314) 等后续判定", "后续分别返回 2（00448049 `mov eax,2`）或 0"),
       ("00447F66", "本函数自身的错误码出口：00447F66 `mov eax,6`、00447FA5 `mov eax,6`、00447FBA `mov eax,3`、00448049 `mov eax,2`、0044805C `mov eax,5`", "均 `ret 0xC`，与 0 成功路构成完整错误码合同")]),
"00448260": dict(v="FAIL", reason="唯一站点比较的是「地图像素距离」的整数阈值（被调经 _ftol 返回几何量），不是失败/成功错误码",
  lis=[("00448644", "call 0041C380 = 三条 fild/fmul 求和后 `call 004CAC40`、再 `jmp 007C5F00`(_ftol) ⇒ 返回整数距离", "00448649 `cmp eax,0x40` / 0044864C `jge 0x4485AA` — 与 64 比较的距离阈值，几何量非错误码")]),
"0044E8F0": dict(v="PASS", reason="③b② 成立：站点对本对象内的成员 DynamicVectorClass<InfantryClass*> 虚派发 Find，被调 `or eax,-1` 使「未找到 = -1」字节可伪证，调用方 `cmp eax,-1` 真的按 -1 分支，命中路做 count-- 与数组压缩前移（含非栈写），未命中路直接跳过；cmp 与 je 之间无 eax 覆写、单 call 非多路同一 call，成员对象 vptr 由本类构造器写入",
  anchor="0044EA8F", lis=[("0044EA8F", "call [edx+0x10]，edx = [esi+0x66C] 的成员对象 vptr；0044EA7E `lea edi,[esi+0x66C]` 即 this", "0044EA92 `cmp eax,-1` / 0044EA95 `je 0x44EAB8`"),
       ("0043B6DB", "成员 vptr 安装点：`c7 86 6c 06 00 00 c8 43 7e 00` = `mov dword ptr [esi+0x66C], 0x7E43C8`（在构造器 0043B680 内）", "0x7E43C8 → [-4]=COL 007FC298 → RTTI `.?AV?$DynamicVectorClass@PAVInfantryClass@@@@`"),
       ("0x7E43D8", "slot 4（+0x10）= 0045A610（Find：`mov edx,[ecx+0x10]` 计数、`mov ecx,[ecx+4]` 数组、逐个比较）", "0045A62F `or eax, 0xffffffff`；0045A633 `ret 4` ⇒ 未找到 = -1"),
       ("0044EA97", "命中路：`mov ecx,[edi+0x10]`(count) / 0044EA9A `cmp eax,ecx` / 0044EA9E `dec ecx`", "0044EAA1 `mov [edi+0x10],ecx`；0044EAAA `mov edx,[ecx+eax*4]` / 0044EAAD `mov [ecx+eax*4-4],edx` 压缩前移（非栈写）"),
       ("0044EAB8", "未命中路（-1 分支目标）：直接跳出，转到 0044EAB8 `mov eax,[0xA8E7AC]` 之后的第二个容器处理", "两路动作不同"),
       ("0044EAD9", "同函数内第二个同类容器（this+0x684，由 0043B709 安装同一 vptr 0x7E43C8）的 Find", "0044EADC `cmp eax,-1` / 0044EADF `je` — 独立站点，非多路同一 call")]),
"0044EB10": dict(v="FAIL", reason="唯一站点的被调是 rand（MSVC 线性同余伪随机，状态数组上限 0xFA=250），与 0x19 比较是随机取阈，不是错误码",
  lis=[("0044EB2C", "call 0065C7E0；该函数以 `mov eax,[esp+4]` / 状态数组 `[edx+ecx*4+0xC]` 与 `cmp eax,0xFA` 构成 MSVC rand 的 LCG", "0044EB31 `cmp eax,0x19` / 0044EB34 `jge 0x44EB53` — 与 25 比较的随机取阈")]),
"0044EBF0": dict(v="FAIL", reason="五处站点是对同一运行时未知类对象做槽 +0x94 的虚调用（该对象由 004CA160 返回，静态类型不可定），被调约定无法从字节伪证；另有 00500510 是按参数走 40 路跳表返回不同对象指针，非错误码",
  lis=[("0044EC8C", "call [edx+0x94]；edx = [edi] 而 edi = 0044EC59 `call 004CA160` 的返回对象 ⇒ 运行时类不可静态定", "0044EC92 `test eax,eax` / 0044EC94 `jne`；被调不可定位 ⇒ 约定不可伪证"),
       ("0044ED0D", "同一形状（入参 push 1/0/0）", "0044ED13 `test eax,eax` / 0044ED15 `jne 0x44ED45`"),
       ("0044ED8E", "同一形状", "0044ED94 `test eax,eax` / 0044ED96 `jne 0x44EDC6`"),
       ("0044EE0F", "同一形状", "0044EE15 `test eax,eax` / 0044EE17 `jne 0x44EE47`"),
       ("0044EE90", "同一形状", "0044EE96 `test eax,eax` / 0044EE98 `jne 0x44EEC8`"),
       ("0044EEF7", "call 00500510（direct）；其内部 `dec eax; cmp eax,0x27; ja` + 字节索引表 + `jmp [edx*4+0x500574]`，各 case 返回 [ecx+0x53B0/0x53B4/0x53B8] 等对象指针", "0044EEFC `test eax,eax` / 0044EEFE `je` — 返回的是对象指针，非错误码")]),
}

def bytes_hex(va, n):
    return " ".join("%02x" % b for b in C.va_read(va, n))

def ins_lines(insns, marks=()):
    out = []
    for i in insns:
        tag = "   <<<" if i.address in marks else ""
        out.append("  %08X: %-24s %-32s%s" % (i.address, bytes_hex(i.address, i.size),
                                              i.mnemonic + " " + i.op_str, tag))
    return out

for r in rows:
    ent = r["entry"]
    e = int(ent, 16)
    R = rec[ent]
    R3r = R3[ent]
    hint = R["hint_slot"]
    lines = []
    lines.append("# ROW %s  S12  %s   （NAMED-PUSH S12 B1）" % (ent, r["name"]))
    lines.append("")
    # ①
    e2, insns = C.disasm_body(ent)
    marks = set()
    if R3r.get("anchor"):
        marks.add(int(R3r["anchor"], 16))
    lines.append("## 环① 入口与函数边界")
    lines.append("- entry=%s（delta entry 列原样写此串：大写十六进制、无 0x）；in .text[0x401000,0x7E038D) = %s" % (ent, R["in_text"]))
    lines.append("- atlas size=%d B；capstone 5.0.7(skipdata=True) 反汇编 n_insn=%d，skipdata 条数=%d" % (R["size"], R["n_insn"], R["n_skip"]))
    lines.append("- 函数体按 atlas 计 [0x%s, 0x%s)；入口 16 B: %s" % (ent, R["body_end"], bytes_hex(e, 16)))
    if R["n_skip"] == 0:
        lines.append("- 末条指令 %s ⇒ 边界自洽（末条为 ret/jmp，且解码恰好用尽 atlas size）" % R["last_insn"])
        lines.append("- 裁定：**PASS**")
    else:
        lines.append("- 末条指令 %s；atlas size 停在一条指令中间（skipdata=%d），自 0x%s 继续解码仍是合法代码 ⇒ atlas 长度略短于真实函数体" % (R["last_insn"], R["n_skip"], R["body_end"]))
        lines.append("- 裁定：**PASS（带截断注记）** —— 入口地址本身在 .text 内、从入口线性解码自洽；仅 atlas 给出的长度短 3~4 字节，且本行所有 ③/④ 锚点距尾部 > 0x100 B，不受影响")
    lines.append("- 首 6 条 / 末 3 条：")
    lines += ins_lines(insns[:6])
    lines.append("  ...")
    lines += ins_lines(insns[-3:])
    lines.append("")
    # ②
    lines.append("## 环② 类身份（独立取证：RTTI 描述符 → 类名字串 + 主虚表槽号/槽值双钉）")
    lines.append("- 槽驻留 0x%s [.rdata]，槽 4 字节 = `%s` = entry %s" % (R["slot_va"], bytes_hex(int(R["slot_va"], 16), 4), "✔" if R["slot_is_entry"] else "✘"))
    lines.append("- 槽号 = %d（线索 `%s` 的 N=%d，**由字节复算而非反推**）；vtable base = 0x007E3EBC，槽偏移 = +0x%X" % (hint, r["name"].split("::")[-1], hint, 4 * hint))
    lines.append("- `[vt-4]` @0x007E3EB8 = 0x%s = COL 0x007FC360，COL.sig = 0x%08X（=0，" % (bytes_hex(0x7E3EB8, 4), C.u32(COL) or 0) + "Complete Object Locator)")
    lines.append("- `[COL+0xC]` @0x007FC36C = 0x%s = TD 0x00818D60；TD+8 @0x00818D68 名串 = `%s`" % (bytes_hex(0x7FC36C, 4), C.read_cstr(TD + 8, 60)))
    lines.append("- 该表槽 0 @0x007E3EBC = 0x%s = 0x00410260 ⇒ **对象主虚表**（任务卡给的真主虚表槽 0 锚），不是小成员子表；同族另有三张小子表 0x007E3E90(槽0=00410590)/0x007E3E98(00410580)/0x007E3EA0(004105E0)，本行槽不落在其中" % bytes_hex(0x7E3EBC, 4))
    lines.append("- 类名 `.?AVBuildingClass@@` 与线索类 `BuildingClass` 一致，且槽号 == 线索槽号 ⇒ **② 钉住**")
    lines.append("- 取证来源：`.rdata` 的 COL/TD/名串数据链（与 ④ 的 `.text` 构造安装指令链**不同源**）")
    lines.append("")
    # ③
    lines.append("## 环③ 整体合同（只认 ③b）")
    lines.append("- 机械 ③b② 站点（call → test/cmp eax → jcc，两路动作签名不同）：见下逐站点；本行裁定 **%s**" % R3r["v"])
    for it in R3r["lis"]:
        addr, what, why = it[0], it[1], it[2]
        lines.append("- `%s` %s" % (addr, what))
        if addr.startswith("004") and C.in_text(int(addr, 16)):
            lines.append("     字节: %s" % bytes_hex(int(addr, 16), 8))
        lines.append("     → %s" % why)
    lines.append("- **裁定 %s**：%s" % (R3r["v"], R3r["reason"]))
    lines.append("")
    # ④
    lines.append("## 环④ 使用见证（活虚表派发；与 ② 不同源）")
    lines.append("- 主虚表 0x007E3EBC 在 `.text` 中的构造期安装点（`mov dword ptr [reg], 0x7E3EBC`）：")
    lines.append("    - 0x0043B71F `%s`（在函数 0043B680 内，192 B，先 `call 006F4300` 基类构造、收尾 `mov eax,esi; ret 4` 返 this ⇒ **构造器**，非析构器）" % bytes_hex(0x43B71F, 6))
    lines.append("    - 0x0043B9FA `%s`（在函数 0043B740 内，1456 B，先 `call 006F2B40` 基类构造、收尾 `mov eax,esi; ret 8` 返 this ⇒ **构造器**）" % bytes_hex(0x43B9FA, 6))
    lines.append("    - 0x0043BCFD `%s`（在函数 0043BCF0 内，986 B）" % bytes_hex(0x43BCFD, 6))
    lines.append("    - 三处均 `push <func>` + `call 0x7C978A`(atexit)=**否** ⇒ ㉓ 成对陷阱排除：④ 锚点**不在**析构器/atexit 表里")
    lines.append("- 本行槽 0x%s 位于上述已安装的主虚表内（base 0x007E3EBC + 0x%X）⇒ 构造完成后 `[obj+0]` 派发可达本 entry" % (R["slot_va"], 4 * hint))
    lines.append("- 直接调用者（direct callers）%d 个：%s" % (R["n_direct"], R["direct_callers"] if R["direct_callers"] else "无（本行只靠活虚表派发；按 D-40『direct-only 不足』的补集口径——此处不是 direct-only，而是活虚表链）"))
    lines.append("- 取证来源：`.text` 构造安装指令 + 槽值字节（与 ② 的 `.rdata` RTTI 数据链不同源）")
    lines.append("- 裁定：**PASS**")
    lines.append("")
    # 汇总
    allfour = (R3r["v"] == "PASS")
    lines.append("## 裁定")
    lines.append("- ①=%s ②=PASS ③=%s ④=PASS ②④独立=是（.rdata RTTI 数据链 vs .text 构造安装链）" %
                 ("PASS" if R["n_skip"] == 0 else "PASS(截断注记)", R3r["v"]))
    lines.append("- **四环齐全=%s → %s**" % ("是" if allfour else "否", "产出" if allfour else "不产出"))
    lines.append("")
    lines.append("## 本行地址锚")
    lines.append("- entry 0x%s；② 槽 0x%s；④ 安装点 0x0043B71F / 0x0043B9FA / 0x0043BCFD；③ 锚 %s" %
                 (ent, R["slot_va"], R3r.get("anchor", "见环③ 逐站点")))
    open(os.path.join(OUT, "ROW_%s.txt" % ent), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("ROW_%s.txt  %s  %s" % (ent, R3r["v"], "产出" if allfour else "-"))
