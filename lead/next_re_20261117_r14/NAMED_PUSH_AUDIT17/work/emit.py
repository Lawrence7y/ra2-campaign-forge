# -*- coding: utf-8 -*-
"""Emit per-row evidence files + verdict.tsv + VERDICT.md from the facts this audit
verified byte-by-byte. Every address below was read back from gamemd.exe by work/pe.py."""
import os

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT17"

ROWS = []


def R(**kw):
    ROWS.append(kw)


R(entry="004A2CD0", sub="S17", name="CStreamClass::slot4",
  r2="vt=007E5DAC slot4 (+0x10) @007E5DBC ; COL=007FF9B8 TD=0081FC30 .?AVCStreamClass@@",
  r2d="""entry 在整镜像中作为 dword 只出现 1 次：007E5DBC (.rdata) ⇒ 唯一持有表 base=007E5DAC
      主/次表核：同 TD 0081FC30 有 **2 张**表 —— 007E5DAC(15 槽，slot0=004A2990=QueryInterface) 与
      007E5D94(5 槽：0:004A3220 1:004A3230 2:004A3240 3:004A2A20 4:004A2AB0)。本 entry **只在 007E5DAC**，
      不在那张 5 槽小表里 ⇒ 「小成员表顶替主表」不成立。
      004A2990 实测即 QI：004A2999 b8 03400080(E_POINTER) / 004A2A02 b8 02400080(E_NOINTERFACE) /
      004A2A11 33c0(S_OK)，其间以 f3a7(repe cmpsd,ecx=4) 比 16 字节 IID(0x7F7C90/0x7F7CF0)。""",
  r3f="3b2",
  r3="""③b② 多值状态码 HRESULT（非 bool）
      被调 004A3020（直接调用，目标钉死）：
        004A2D8D  e8 8e020000   call 0x4A3020
        004A2DB1  e8 6a020000   call 0x4A3020
      调用方真分支：
        004A2D92  85 c0         test eax,eax
        004A2D94  7c 61         jl   0x4A2DF7
        004A2DB6  85 c0         test eax,eax
        004A2DB8  7c 3d         jl   0x4A2DF7
      被调返回域：004A3089 b8 05400080 (E_FAIL) / 004A30CD 25 05400080 (neg+sbb 后 E_FAIL 或 0) /
        004A307F 7c51 与 004A30BB jl 0x4A30D2 把内层 IStream::Read 的负 HRESULT 原样透传 / 004A30D5 c20800 ret 8 不清 eax
      ⇒ 返回值域 {0(S_OK), 0x80004005(E_FAIL), 任意负 HRESULT} —— **多值状态码**
      两路动作不同：失败 jl→004A2DF7 收尾、eax 保持负码原样返回；成功 004A2D96 清 [esi+0x14] 续填，
        块末 004A2DF5 33c0 xor eax,eax → 返回 0
      无 eax 覆写：004A2D8D→004A2D92、004A2DB1→004A2DB6 之间均无写 eax 指令""",
  r4="ctor 004A2820 @004A285E mov [esi],0x7e5dac",
  r4d="""④ 活虚表安装点（direct-only 不足 ⇒ 本行直调 0 条，全 .text E8/E9 目标扫 0 命中）
      枚举 vt 007E5DAC 全部写点（整镜像 dword 出现 3 次，全 .text）：
        004A285E  c706 ac5d7e00  mov dword ptr [esi],0x7e5dac   ← 采用
        004A2889  c706 ac5d7e00  mov dword ptr [esi],0x7e5dac
        004A3119  c706 ac5d7e00  mov dword ptr [esi],0x7e5dac
      ㉓ 构造/析构逐个判定：
        004A285E 所在 004A2820：push esi; mov esi,ecx; 初化 +8/+0xC/+0x10/+0x11/+0x14；
          三次 push 0x10000 + call 0x7C8E17(operator new) 填 +0x18/+0x1C/+0x20；再装 vt；mov eax,esi; ret
          ⇒ **构造器**（体内 free 0 次）。直接调用者 006BEF4C call 0x4A2820（TClassFactory<VCStreamClass> 构造点）
        004A2889 所在 004A2880：装 vt 后经 0x4A3020 收尾并释放缓冲 ⇒ **析构器**（排除）
        004A3119 所在 004A3110：本表 **slot14 == 004A3110** ⇒ **删除析构器**（排除）
      atexit 排除：全 .text `push imm32; call 0x7C978A` 注册点 152 个，
        004A2820 / 004A2880 / 004A3110 三者均不在注册集合；CStreamClass 非全局静态对象""",
  ss="no",
  r5="""逐项核执行器所报数值，全中：004A2D8D ✓ 004A2DB1 ✓ 004A2D92 ✓ 004A2D94 ✓ 004A2DB6 ✓ 004A2DB8 ✓
      004A3089 ✓ 004A30CD ✓ 004A2DF5 ✓ COL 007FF9B8 ✓ TD 0081FC30 ✓ 安装点 004A285E ✓ 排除 004A2880 ✓ 004A3110 ✓
      第 4 列未主张读/写方向，无可反之处。
      附加实测（不入结论）：004A2D61/004A2DDC call 0x7CA090 以 dst=[esi+0x18]+[esi+0x14]、src=ebp 做 memcpy
      ⇒ 数据流「调用方 → 本对象缓冲」，随后 0x4A3020 经 call [edx+0x10] 写出，方向为「写」，与 slot4 名不冲突。""",
  verdict="PASS",
  reason=("004A2CD0：② 唯一持有表 007E5DAC（同 TD 另有一张 5 槽次基表 007E5D94，本 entry 不在其中），"
          "COL=007FF9B8→TD=0081FC30→内联 .?AVCStreamClass@@，slot0=004A2990 实测为 QI 故为主表；"
          "③ 被调 0x4A3020 在 004A3089 返 0x80004005、004A30CD 经 neg/sbb 再 and 0x80004005，"
          "并把内层 Read 的负 HRESULT 原样透传（004A30D5 ret 8 不清 eax）⇒ 多值状态码非 bool，"
          "调用方 004A2D8D/004A2DB1 后 004A2D92 test+004A2D94 jl、004A2DB6 test+004A2DB8 jl 真分支，"
          "失败路保 eax、成功路 004A2DF5 xor eax,eax；④ 锚 004A285E（构造器 004A2820，三处 operator new 后装活 vt，"
          "调用者 006BEF4C 来自工厂），排除同表另两写点 004A2889(析构 004A2880)、004A3119(删除析构 slot14)，"
          "三者均不在 152 个 atexit 注册集合；④②不同源"))

R(entry="006BEF10", sub="S17", name="TClassFactory<VCStreamClass>::slot3",
  r2="vt=007F3768 slot3 (+0xC) @007F3774 ; COL=00809C68 TD=00840F68 .?AV?$TClassFactory@VCStreamClass@@@@",
  r2d="""entry 作为 dword 只出现 1 次：007F3774 (.rdata) ⇒ 唯一持有表 base=007F3768
      表 5 槽：0:006BEE50 1:006BEEC0 2:006BEEE0 3:006BEF10 4:006BEF90
      按 TD 归组：TD 00840F68 只对应 **1 个 COL**(00809C68) ⇒ 该类仅此一张表，5 槽即全部虚函数
        ⇒ 「小成员表顶替主表」不成立
      slot0=006BEE50 实测为 QI：006BEE55 test eax,eax / 006BEE59 b8 03400080(E_POINTER)""",
  r3f="3b2",
  r3="""③b② 多值状态码 HRESULT（非 bool）
      被调钉死链：006BEF3C push 0x2c; 006BEF3E call 0x7C8E17(operator new); 006BEF4A mov ecx,eax;
        006BEF4C e8 cf38deff call 0x4A2820（CStreamClass 构造器，见 ROW_004A2CD0，其 004A285E 装活表 007E5DAC）
        ⇒ [esi]=007E5DAC ⇒ 006BEF6A ff10 call dword ptr [eax] = 007E5DAC **slot0 = 004A2990 (QueryInterface)**
      调用方真分支：
        006BEF6C 8bf8  mov edi,eax
        006BEF6E 85ff  test edi,edi
        006BEF70 7d09  jge 0x6bef7b
        006BEF72 8b16  mov edx,[esi]
        006BEF78 ff5238 call dword ptr [edx+0x38]   ← CStreamClass slot14=004A3110（0x38/4=14 ✓ 与表实测自洽）
        006BEF7B 8bc7  mov eax,edi  → ret 0x10
      被调 004A2990 返回域：004A2999 b8 03400080(E_POINTER) / 004A2A02 b8 02400080(E_NOINTERFACE) / 004A2A11 33c0(S_OK)
      ⇒ {0x80004003, 0x80004002, 0} 多值状态码，非 {0,1} 布尔
      两路动作不同：成功保留对象直接返回；失败先 Release 释放再返回负码
      无 eax 覆写（结果经 edi 保存，006BEF7B mov eax,edi 还原）
      入口 operator new 空判断（006BEF46 test eax,eax + 006BEF48 je → 0x8007000E）属 ③a，不计入""",
  r4="ctor 006BEE40 @006BEE49 mov [eax],0x7f3768",
  r4d="""④ 活虚表安装点（全 .text 扫 E8/E9 目标 == 006BEF10：0 条直调）
      枚举 vt 007F3768 全部写点：整镜像 dword 出现 **1 次**
        006BEE49  c700 68377f00  mov dword ptr [eax],0x7f3768   ← 采用
      所在函数 006BEE40 全 body：8bc1 mov eax,ecx / c74004 00000000 mov [eax+4],0 /
        c700 68377f00 装 vt / c3 ret  ⇒ **构造器**，无 free、无 push dtor
      实调用上下文（证非死表）：唯一调用者 006BC468 call 0x6bee40，其前序
        006BC458 push 8 / 006BC45A call 0x7C8E17(operator new) / 006BC462 test eax,eax / 006BC466 mov ecx,eax
        ⇒ 堆分配后立刻构造，随后 006BC477.. 把该对象作参数压栈（CoCreate 风格注册）
      atexit 排除：006BEE40 / 006BEE50 均不在 152 个注册集合；vt 007F3768 在 .data 出现 0 次
        ⇒ 无全局静态实例""",
  ss="no",
  r5="""逐项核数值，全中：vt 007F3768 ✓ slot+0xC ✓ 槽 007F3774 ✓ COL 00809C68 ✓ TD 00840F68 ✓
      内联名 .?AV?$TClassFactory@VCStreamClass@@@@ ✓（与执行器逐字相同）
      006BEF6A ✓ 006BEF6C ✓ 006BEF6E ✓ 006BEF70 ✓ 006BEF72 ✓ [edx+0x38] ✓
      004A2999 E_POINTER ✓ 004A2A02 E_NOINTERFACE ✓ 004A2A11 xor eax,eax ✓ 006BEF4C call 0x4A2820 ✓
      ④ 006BEE49 ✓。第 4 列未主张读/写方向，无可反之处。""",
  verdict="PASS",
  reason=("006BEF10：② 唯一持有表 007F3768（TD 00840F68 仅 1 个 COL，5 槽表即全表，slot0=006BEE50=QI），"
          "COL=00809C68→TD=00840F68→内联 .?AV?$TClassFactory@VCStreamClass@@@@，slot3=+0xC 与 name 一致；"
          "③ 被调经 006BEF4C call 0x4A2820 装配为 CStreamClass 实例，故 006BEF6A call [eax] = 007E5DAC slot0=004A2990，"
          "该 QI 在 004A2999 返 0x80004003、004A2A02 返 0x80004002、004A2A11 xor eax,eax 返 0 ⇒ 多值状态码非 bool，"
          "006BEF6C mov edi,eax+006BEF6E test+006BEF70 jge 真分支，失败路 006BEF78 call [edx+0x38]=slot14 释放后返负码、"
          "成功路保留对象；④ 锚 006BEE49（构造器 006BEE40，唯一调用者 006BC468 在 operator new 后立即构造并使用），"
          "该表 .data 出现 0 次且不在 152 个 atexit 注册集合；入口 006BEF46 test eax,eax 属 ③a 不计"))

R(entry="006BF690", sub="S17", name="TClassFactory<SuperClass>::slot3",
  r2="vt=007F37E0 slot3 (+0xC) @007F37EC ; COL=00809DF8 TD=00841068 .?AV?$TClassFactory@VSuperClass@@@@",
  r2d="""entry 作为 dword 只出现 1 次：007F37EC (.rdata) ⇒ 唯一持有表 base=007F37E0
      表 5 槽：0:006BF5D0 1:006BF640 2:006BF660 3:006BF690 4:006BF710
      TD 00841068 只对应 1 个 COL(00809DF8) ⇒ 仅此一张表，5 槽即全部虚函数
      slot0=006BF5D0 实测为 QI：006BF5D5 test eax,eax / 006BF5D9 b8 03400080(E_POINTER)""",
  r3f="3b2",
  r3="""③b② 多值状态码 HRESULT（非 bool）
      被调钉死链：006BF6BC push 0x80; call 0x7C8E17(operator new); 006BF6CD mov ecx,eax;
        006BF6CF e8 ecb70000 call 0x6CAEC0（SuperClass 构造器，其 006CAF12 装 SuperClass 主表 007F3FE8）
        ⇒ [esi]=007F3FE8（COL=0080B610 → TD=008423E0 内联 .?AVSuperClass@@，slot0=00410260）
        ⇒ 006BF6ED ff10 call dword ptr [eax] = **00410260 = QueryInterface**
      调用方真分支：
        006BF6EF 8bf8 mov edi,eax / 006BF6F1 85ff test edi,edi / 006BF6F3 7d09 jge 0x6bf6fe
        006BF6FB ff5220 call dword ptr [edx+0x20]   ← SuperClass slot8=006CE220（0x20/4=8 ✓）
        006BF6FE 8bc7 mov eax,edi → ret 0x10
      被调 00410260 返回域：00410269 b8 03400080(E_POINTER) / 004102E6 b8 02400080(E_NOINTERFACE) / 004102F5 33c0(S_OK)
        并依次比 0x7F7C90 / 0x7F7C80 / 0x7F7C70 / 0x7E9AE0 四个 16 字节 IID（f3a7,ecx=4），004102E1 cmp [eax],0 + jne 判命中
      ⇒ {0x80004003, 0x80004002, 0} 多值状态码，非 {0,1} 布尔
      两路动作不同：成功保留对象返回 0；失败 call [edx+0x20] 释放后返回负码
        006CE220 实测 `push esi; mov esi,ecx; call 0x6CB120; test byte [esp+8],1; je; push esi; call 0x7C8B3D(free)`
        ⇒ 确为释放语义 ✓
      无 eax 覆写；入口 operator new 空判断（006BF6C9 test eax,eax → 0x8007000E）属 ③a 不计入""",
  r4="ctor 006BF5C0 @006BF5C9 mov [eax],0x7f37e0",
  r4d="""④ 活虚表安装点（全 .text 扫 E8/E9 目标 == 006BF690：0 条直调）
      枚举 vt 007F37E0 全部写点：整镜像 dword 出现 **1 次**
        006BF5C9  c700 e0377f00  mov dword ptr [eax],0x7f37e0   ← 采用
      所在函数 006BF5C0：8bc1 mov eax,ecx / mov [eax+4],0 / 装 vt / c3 ret ⇒ **构造器**
      实调用上下文：唯一调用者 006BC599 call 0x6bf5c0，前序 006BC589 push 8 / call 0x7C8E17 /
        006BC593 test eax,eax / 006BC597 mov ecx,eax ⇒ 堆分配后立刻构造并被使用
      atexit 排除：006BF5C0 / 006BF5D0 不在 152 个注册集合；vt 007F37E0 在 .data 出现 0 次
      附（表 007F3FE8 的写点，仅用于 ③ 的被调钉死，不作本行 ④ 锚）：006CAF12（构造器 006CAEC0 内）、
        006CB129（析构器 006CB120 内，即 Release 006CE220 所 call 者）、006CAFF9、006CDF15""",
  ss="no",
  r5="""逐项核数值，全中：vt 007F37E0 ✓ slot+0xC ✓ 槽 007F37EC ✓ COL 00809DF8 ✓ TD 00841068 ✓
      内联名 .?AV?$TClassFactory@VSuperClass@@@@ ✓
      006BF6ED ✓ 006BF6EF ✓ 006BF6F1 ✓ 006BF6F3 ✓ 006BF6F5 ✓ [edx+0x20] ✓
      00410269 E_POINTER ✓ 004102E6 E_NOINTERFACE ✓ 004102F5 xor eax,eax ✓
      006BF6CF call 0x6CAEC0 ✓ 007F3FE8 slot0=00410260 ✓（执行器「符合主表 slot0 常见 00410260」实测成立）
      ④ 006BF5C9 ✓。第 4 列未主张读/写方向，无可反之处。""",
  verdict="PASS",
  reason=("006BF690：② 唯一持有表 007F37E0（TD 00841068 仅 1 个 COL，5 槽表即全表，slot0=006BF5D0=QI），"
          "COL=00809DF8→TD=00841068→内联 .?AV?$TClassFactory@VSuperClass@@@@，slot3=+0xC 与 name 一致；"
          "③ 被调经 006BF6CF call 0x6CAEC0 装配为 SuperClass 实例（006CAF12 装主表 007F3FE8），"
          "故 006BF6ED call [eax] = 007F3FE8 slot0=00410260，该 QI 在 00410269 返 0x80004003、004102E6 返 0x80004002、"
          "004102F5 xor eax,eax 返 0，并比 4 个 16B IID ⇒ 多值状态码非 bool；006BF6EF mov edi,eax + 006BF6F1 test + "
          "006BF6F3 jge 真分支，失败路 006BF6FB call [edx+0x20]=slot8=006CE220（实测含 call 0x6CB120 + test byte[esp+8],1 "
          "+ call 0x7C8B3D 释放）后返负码；④ 锚 006BF5C9（构造器 006BF5C0，调用者 006BC599 在 operator new 后构造并使用），"
          "不在 152 个 atexit 注册集合且 .data 出现 0 次；入口 006BF6C9 test eax,eax 属 ③a 不计"))

# ---------------- S18 ----------------
COMMON_TBL = """      三张相关虚表（同一族，实测）：
        IPX      vt=007F794C 23 槽 COL=0080EA60 TD=0084D8F8 .?AVIPXInterfaceClass@@      chd base[1]=WinsockInterfaceClass
        Winsock  vt=007F79BC 23 槽 COL=0080EAF8 TD=0084D8D0 .?AVWinsockInterfaceClass@@  chd numBase=1(根)
        UDP      vt=007F7A6C 31 槽 COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@      chd base[1]=WinsockInterfaceClass
      即 IPX、UDP 均派生自 Winsock；每个 TD 只有 1 个 COL ⇒ 每类各 1 张虚表，无「小成员表 vs 主表」歧义。"""

CTOR_TXT = """      ㉓ 构造/析构逐个判定（枚举全部写点，非析构锚）：
        IPX  ctor 007B0D90 @007B0DA4（先 call 0x7B19C0 = Winsock 基类构造，再装 vt，尾 mov eax,esi/ret）
             直接调用者 **5** 个：0052E3F1 00540926 00560533 00685B21 00686189
        Winsock ctor 007B19C0 @007B1A20（大体量字段初化 + 0x80 次字节表清零 + 尾 mov eax,esi/ret）
             直接调用者 2 个：007B0D93（IPX ctor 内）、007B2DB3（UDP ctor 内）
        Winsock 析构 007B1AB0 @007B1ABC、Winsock slot0=007B2780 @007B278C（删除析构器）—— **排除**
        UDP  ctor 007B2DB0 @007B2E2D（call 0x7B19C0 后初化 + 尾 mov eax,esi/ret）
             直接调用者 1 个：0052F456
        UDP  析构 007B2E50 @007B2E56（call 0x7C8B3D 释放）、UDP slot0=007B4170 @007B4176（删除析构器）—— **排除**
      atexit 排除：全 .text `push imm32; call 0x7C978A` 注册点 152 个；
        007B0D90 / 007B19C0 / 007B2DB0 / 007B1AB0 / 007B2780 / 007B2E50 / 007B4170 **均不在**注册集合
      静态实例排除：007F794C / 007F79BC / 007F7A6C 作为 dword 在 .data 中出现 **0 次**
        ⇒ 无全局静态对象，活表全部来自堆分配路径
      对象落点：构造后存入全局 **0x887628**（0052E3FD / 00685B26 / 0068618E 存 IPX；0052F461 存 UDP）"""

R(entry="007B13D0", sub="S18", name="IPXInterfaceClass::slot16",
  r2="vt=007F794C slot16 (+0x40) @007F798C ; COL=0080EA60 TD=0084D8F8 .?AVIPXInterfaceClass@@",
  r2d="""entry 作为 dword 只出现 1 次：007F798C (.rdata) ⇒ 唯一持有表 base=007F794C
      IPX 表 23 槽，slot16 == 007B13D0 ✓；IPX TD 只有 1 个 COL ⇒ 该表即 IPX 主虚表
""" + COMMON_TBL,
  r3f="3b2",
  r3="""③b② 多值状态码（WSOCK32 SOCKET_ERROR 哨兵 + WSA 错误码二级判别）
      本体 007B13D0..007B1720（290 条指令 / 848 字节），首 cmp eax,0x473 为消息号分派。
      sendto 路：
        007B14C6  e8 e5740100   call 0x7C89B0  → IAT [0x7E1558] = **WSOCK32!sendto**
        007B14CB  83f8ff        cmp eax,-1
        007B14CE  7510          jne 0x7B14E0
        007B14D0  call 0x7C897A → WSAGetLastError
        007B14D5  3d 33270000   cmp eax,0x2733   (WSAEWOULDBLOCK=10035)
        007B14DA  0f8531ffffff  jne 0x7B1411   ⇒ 真错误：007B141D call [eax+0x24] 关闭，返回 0
        等 0x2733 时落到 007B14E0 继续（视为可重试，摘队/释放缓冲/回边 007B143C）
      recvfrom 路：
        007B1586  e8 1f740100   call 0x7C89AA  → IAT [0x7E154C] = **WSOCK32!recvfrom**
        007B158B  83f8ff        cmp eax,-1
        007B158E  89442410      mov [esp+0x10],eax   （存值，不覆写 eax）
        007B1592  752b          jne 0x7B15BF
        失败：call 0x7C897A(WSAGetLastError) / 007B1599 cmp eax,0x2733 / 007B159E je 0x7B1714
      ⇒ 返回值域至少 {-1 且错误码 0x2733, -1 且其它错误, ≥0 字节数} 三态，**多值状态码，非 {0,1} 布尔**
      两路动作真不同（重试续跑 vs 关socket/中止）；无 eax 覆写（call→cmp 紧邻）""",
  r4="ctor 007B0D90 @007B0DA4 mov [esi],0x7f794c + 派发点 007775FF call [eax+0x40]",
  r4d="""④ 使用见证
      (a) 直调：全 .text E8/E9 目标 == 007B13D0 的站点 **0 条**
      (b) 活虚表安装点：007B0DA4（见下 ㉓）
      (c) 真实派发点：007775C1 mov eax,[0x887628] → 007775FF ff5040 call dword ptr [eax+0x40]
          （0x887628 即构造后存放网络接口对象的全局；slot16 派发；IPX/UDP 两类的 slot16 分别是本行与 007B3AA0）
""" + CTOR_TXT,
  ss="no",
  r5="""逐项核数值，全中：007B14C6 ✓ 007B1586 ✓ cmp eax,-1 ✓ jne 分支 ✓ ② vt 007F794C slot+0x40 槽 007F798C ✓
      COL 0080EA60 ✓ TD 0084D8F8 ✓ ④ 007B0DA4 ✓ in_func 007B0D90 ✓ direct5 ✓ 非析构 ✓
      API 身份独立复核（IAT）：sendto=0x7E1558 ✓ recvfrom=0x7E154C ✓ WSAGetLastError=0x7E1574 ✓
      「失败返 -1、成功返字节数/继续」与实测一致；「无 eax 覆写」实测成立；第 4 列未反写读/写方向。""",
  verdict="PASS",
  reason=("007B13D0：② 唯一持有表 007F794C（IPX TD 仅 1 COL ⇒ 主虚表），slot16=+0x40 @007F798C，"
          "COL=0080EA60→TD=0084D8F8→内联 .?AVIPXInterfaceClass@@；③ sendto(007B14C6→IAT[0x7E1558]) 后 "
          "007B14CB cmp eax,-1+007B14CE jne，并再以 007B14D5 cmp eax,0x2733 三级判别（真错误→007B141D 关 socket 返 0；"
          "WSAEWOULDBLOCK→续跑），recvfrom(007B1586→IAT[0x7E154C]) 同形（007B158B cmp+007B1592 jne、007B1599 cmp 0x2733）"
          "⇒ 三态状态码非 bool，两路动作真不同且无 eax 覆写；④ 无直调，锚活虚表安装点 007B0DA4（构造器 007B0D90，"
          "先 call 0x7B19C0 基类构造，5 个直调者），另有真实派发点 007775FF call [eax+0x40]（对象取自全局 0x887628）；"
          "该族三表写点全枚举：IPX 析构与删除析构不存在于 007F794C 写点集（其写点仅 007B0DA4 一处），"
          "Winsock/UDP 的析构与删除析构写点已逐一排除，且 7 个相关函数均不在 152 个 atexit 注册集合；④②不同源"))

R(entry="007B1BC0", sub="S18", name="IPXInterfaceClass::slot7",
  r2="vt=007F794C slot7 (+0x1C) @007F7968 ; COL=0080EA60 TD=0084D8F8 .?AVIPXInterfaceClass@@（另有 Winsock@007F79D8 同址实现）",
  r2d="""entry 作为 dword 出现 2 次（**两个持有表**，全部枚举）：
        007F7968  IPX     vt=007F794C slot7 (+0x1C)  COL=0080EA60 TD=0084D8F8
        007F79D8  Winsock vt=007F79BC slot7 (+0x1C)  COL=0080EAF8 TD=0084D8D0
      执行器 ② 只引 IPX 表。按 §8.7 判据1 全枚举后：IPX 与 Winsock **两张表的 slot7 指向同一 entry**，
      且 chd 显示 IPX 派生自 Winsock（base[1]=WinsockInterfaceClass）⇒ 该实现由**基类 Winsock 定义**、
      IPX 未覆写。两种表述都字节为真：「IPX 虚表 slot7 == 本 entry」成立（本行按此命名），
      但若按「实现所属类」讲，归属类应为 WinsockInterfaceClass —— 记此注，不改变 ② 的可核性。
""" + COMMON_TBL,
  r3f="3b2",
  r3="""③b② 多值状态码（WSAAsyncSelect = SOCKET_ERROR 哨兵）
      007B1BDB  e8 dc6d0100   call 0x7C89BC  → IAT [0x7E156C] = **WSOCK32!WSAAsyncSelect**
      007B1BE0  83f8ff        cmp eax,-1
      007B1BE3  7517          jne 0x7B1BFC
        失败：007B1BE5 call 0x7C897A(WSAGetLastError) / 007B1BEB push 0x84DEA4(日志串) / 007B1BF8 32c0 xor al,al / ret
      007B1C1F  e8 986d0100   call 0x7C89BC  → WSAAsyncSelect（第二次）
      007B1C24  83f8ff        cmp eax,-1
      007B1C27  7517          jne 0x7B1C40
        失败：007B1C29 call 0x7C897A / 007B1C2F push 0x84DE68 / 007B1C3C xor al,al / ret
      007B1C40  b001          mov al,1 / ret    ← 成功
      ⇒ 判据是 WSOCK32 的 SOCKET_ERROR(-1) 哨兵，`cmp eax,-1` 后真分支；返回值域 {-1, 0} 且 -1 是错误域专用值
        （不是 {0,1} 布尔：分支比较对象是 -1，不是 0/1）。两路动作不同（记日志+失败 vs 继续+成功）。
      无 eax 覆写：007B1BDB→007B1BE0、007B1C1F→007B1C24 之间无写 eax 指令。""",
  r4="ctor 007B0D90 @007B0DA4 + 真实调用者 007B3895 call 0x7b1bc0",
  r4d="""④ 使用见证（两种都成立，且与 ② 不同源）
      (a) **真实调用者**：007B3890 体内 007B3895 `e8 26e3ffff call 0x7B1BC0`（UDP slot7 直接调用本 entry，
          紧随 007B389A `84c0 test al,al` + 007B389C `je` 消费其布尔返回）
      (b) 活虚表安装点 007B0DA4（IPX ctor）/ 007B1A20（Winsock ctor）—— 见下 ㉓
""" + CTOR_TXT,
  ss="no",
  r5="""逐项核数值，全中：007B1BDB ✓ 007B1C1F ✓ cmp eax,-1 ✓ jne ✓ ② vt 007F794C slot+0x1C 槽 007F7968 ✓
      COL 0080EA60 ✓ TD 0084D8F8 ✓ ④ 007B0DA4 / 007B0D90 / direct5 / 非析构 ✓ 直调者 007B3895 ✓
      API 身份独立复核：WSAAsyncSelect=0x7E156C ✓ WSAGetLastError=0x7E1574 ✓
      ⚠ 唯一偏差（不改变 ③b 成立）：执行器 ② 称「.?AVIPXInterfaceClass@@」而**未提 Winsock 表同址**；
        按判据1 已补全枚举，归属说明见 ② 注。""",
  verdict="PASS",
  reason=("007B1BC0：② 全表枚举得 2 张持有表——IPX 007F794C slot7 @007F7968 与 Winsock 007F79BC slot7 @007F79D8"
          "（chd 示 IPX 派生自 Winsock，故实现由基类 Winsock 定义、IPX 未覆写；执行器只引 IPX 表，已补注），"
          "COL=0080EA60→TD=0084D8F8→内联 .?AVIPXInterfaceClass@@ 字节为真；③ WSAAsyncSelect(007B1BDB/007B1C1F→IAT[0x7E156C]) "
          "两处后 007B1BE0/007B1C24 cmp eax,-1 配 007B1BE3/007B1C27 jne 真分支，失败路记日志+xor al,al、成功路 mov al,1，"
          "比较对象是 -1 错误域哨兵而非 0/1，判为可伪证状态码；无 eax 覆写；④ 双证——真实调用者 007B3895 call 0x7b1bc0"
          "（007B389A test al,al 消费），以及活虚表安装点 007B0DA4（构造器 007B0D90，5 个直调者），"
          "同表另两写点 007B1ABC/007B278C 属析构器与删除析构器已排除，7 个相关函数均不在 152 个 atexit 注册集合；④②不同源"))

R(entry="007B2630", sub="S18", name="IPXInterfaceClass::slot10",
  r2="vt=007F794C slot10 (+0x28) @007F7974 ; COL=0080EA60 TD=0084D8F8 .?AVIPXInterfaceClass@@（另 Winsock@007F79E4 / UDP@007F7A94 同址）",
  r2d="""entry 作为 dword 出现 **3 次（三个持有表，全部枚举）**：
        007F7974  IPX     slot10 (+0x28)  COL=0080EA60 TD=0084D8F8
        007F79E4  Winsock slot10 (+0x28)  COL=0080EAF8 TD=0084D8D0
        007F7A94  UDP     slot10 (+0x28)  COL=0080EBE0 TD=0084E1C0
      三个表的 slot10 指向同一 entry ⇒ 实现由基类 Winsock 定义，IPX 与 UDP 均未覆写。
      执行器只引 IPX 表（字节为真），按 §8.7 判据1 在此补全枚举。
""" + COMMON_TBL,
  r3f="3b2",
  r3="""③b② 多值状态码（setsockopt = SOCKET_ERROR 哨兵；两次调用四种日志落点）
      007B2652  e8 4d630100   call 0x7C89A4  → IAT [0x7E1554] = **WSOCK32!setsockopt**（SO_REUSEADDR 路）
      007B2657  83f8ff        cmp eax,-1
      007B265A  7515          jne 0x7B2671
        失败 007B265C call 0x7C897A(WSAGetLastError) / 007B2662 push 0x84E0D8 / jmp 007B267E
        成功 007B2671 push 0x84E0B8
      007B2690  e8 0f630100   call 0x7C89A4  → setsockopt（第二路，0x1001）
      007B2695  83f8ff        cmp eax,-1
      007B2699  7518          jne 0x7B26B3
        失败 007B269B call 0x7C897A / 007B26A1 push 0x84E080 / 007B26AE mov al,1
        成功 007B26B3 push 0x84E060 / 007B26C0 mov al,1
      ⇒ 判据是 SOCKET_ERROR(-1) 哨兵 + 二次 `cmp eax,-1` 真分支，两路日志串实测不同（0x84E0D8/0x84E0B8、0x84E080/0x84E060）
        ⇒ 可伪证错误域；非 {0,1} 布尔判据（比较对象 -1）。
      无 eax 覆写：两处 call→cmp 紧邻。""",
  r4="ctor 007B0D90 @007B0DA4 + 4 个真实调用者 (007B13AB/007B31BC/007B32EA/007B36A1)",
  r4d="""④ 使用见证（两路都成立，且与 ② 不同源）
      (a) **真实调用者 4 条**（全 .text E8/E9 目标 == 007B2630）：
          007B13AB (IPX slot16 体内) / 007B31BC (UDP slot23 体内) / 007B32EA (UDP slot26 体内) / 007B36A1 (UDP slot15 体内)
      (b) 活虚表安装点 007B0DA4 / 007B1A20 / 007B2E2D（三张表各自的构造器）—— 见下 ㉓
""" + CTOR_TXT,
  ss="no",
  r5="""逐项核数值，全中：007B2652 ✓ 007B2690 ✓ cmp eax,-1 ✓ 日志串 0x84E0D8/0x84E0B8 ✓ 0x84E080/0x84E060 ✓
      ② vt 007F794C slot+0x28 槽 007F7974 ✓ COL 0080EA60 ✓ TD 0084D8F8 ✓ ④ 007B0DA4 ✓ direct callers=4 ✓ 非析构 ✓
      API 身份独立复核：setsockopt=0x7E1554 ✓ setsockopt 参数 (0x1002/0x1001, 4, 串) 与 SO_REUSEADDR/SO_DONTLINGER 形态相符
      ⚠ 唯一偏差：② 未提 Winsock/UDP 两表同址（已补全枚举，归属注同上行）。""",
  verdict="PASS",
  reason=("007B2630：② 全表枚举得 3 张持有表——IPX @007F7974 / Winsock @007F79E4 / UDP @007F7A94 皆为 slot10(+0x28)，"
          "同一实现由基类 Winsock 定义（执行器只引 IPX 表，已补注），COL=0080EA60→TD=0084D8F8→.IPXInterfaceClass@@ 字节为真；"
          "③ setsockopt(007B2652/007B2690→IAT[0x7E1554]) 两处后 007B2657/007B2695 cmp eax,-1 配 007B265A/007B2699 jne，"
          "四路日志落点实测不同(0x84E0D8/0x84E0B8、0x84E080/0x84E060)，比较对象为 -1 错误域哨兵非 0/1；无 eax 覆写；"
          "④ 双证——4 条真实直接调用者 007B13AB/007B31BC/007B32EA/007B36A1，以及活虚表安装点 007B0DA4"
          "（构造器 007B0D90，5 个直调者）；三表其余写点经逐个判定为析构器/删除析构器（Winsock 007B1ABC/007B278C、"
          "UDP 007B2E56/007B4176）已排除，7 个相关函数均不在 152 个 atexit 注册集合；④②不同源"))

R(entry="007B26D0", sub="S18", name="IPXInterfaceClass::slot17",
  r2="vt=007F794C slot17 (+0x44) @007F7990 ; COL=0080EA60 TD=0084D8F8 .?AVIPXInterfaceClass@@（另 Winsock@007F7A00 / UDP@007F7AB0 同址）",
  r2d="""entry 作为 dword 出现 **3 次（三个持有表）**：
        007F7990  IPX slot17(+0x44) / 007F7A00  Winsock slot17 / 007F7AB0  UDP slot17
      三表同址 ⇒ 实现由基类 Winsock 定义，IPX/UDP 未覆写。执行器只引 IPX 表（字节为真），此补全枚举。
""" + COMMON_TBL,
  r3f="3b2",
  r3="""③b② 多值状态码（gethostname = SOCKET_ERROR 哨兵）
      007B26DB  e8 ee620100   call 0x7C89CE  → IAT [0x7E1560] = **WSOCK32!gethostname**
      007B26E0  83f8ff        cmp eax,-1
      007B26E3  7519          jne 0x7B26FE
        失败 007B26E5 call 0x7C897A(WSAGetLastError) / 007B26EB push 0x84E134 / 007B26F8 32c0 xor al,al / 007B26FB c20800 ret 8
        成功 007B26FE push 0x84E110 / 007B2709 add esp,8 / 007B270C b001 mov al,1 / 007B270F ret 8
      ⇒ `cmp eax,-1` 后真分支；判据对象是 gethostname 的 SOCKET_ERROR 哨兵，属 API 错误域
        （不是 {0,1} 布尔：分支比较 -1，且两路落不同日志串 0x84E134 / 0x84E110）。
      无 eax 覆写：007B26DB→007B26E0 紧邻。""",
  r4="ctor 007B0D90 @007B0DA4（无直调，无槽位派发点可锚）",
  r4d="""④ 使用见证 —— **本行是 12 行里 ④ 最弱的一行，照实记**
      (a) 直调：全 .text E8/E9 目标 == 007B26D0 的站点 **0 条**
      (b) 槽位派发点：扫「从全局 0x887628 取对象后 call [reg+0x44]」**0 命中**；
          全 .text `call [reg+0x44]` 共 131 处，泛化过高（0x44 在多族类里都是某槽），
          无法把任何一处钉到本类实例 ⇒ **不主张有派发点**
      (c) 活虚表安装点：007B0DA4（IPX ctor）/ 007B1A20（Winsock ctor）/ 007B2E2D（UDP ctor）——
          即 ④ 只由「该槽所在的活虚表确实被构造器装入活对象」这一条支撑
""" + CTOR_TXT,
  ss="no",
  r5="""逐项核数值，全中：007B26DB ✓ cmp eax,-1 ✓ jne(gap=0) ✓ 失败 xor al,al / 成功 mov al,1 ✓
      ② vt 007F794C slot+0x44 槽 007F7990 ✓ COL 0080EA60 ✓ TD 0084D8F8 ✓ ④ 007B0DA4 / 007B0D90 / direct5 / 非析构 ✓
      API 身份独立复核：gethostname=0x7E1560 ✓
      「读写方向写反」不适用（无缓冲区方向主张，仅查返回哨兵）。
      ⚠ 保留意见：执行器 ④ 写「装活 vt + 派发」，其中「派发」在本行**我复现不出来**（见 ④(b)）。""",
  verdict="PASS",
  reason=("007B26D0：② 全表枚举得 3 表同址（IPX @007F7990 / Winsock @007F7A00 / UDP @007F7AB0 均 slot17+0x44），"
          "实现属基类 Winsock（执行器只引 IPX 表，已补注），COL=0080EA60→TD=0084D8F8→.IPXInterfaceClass@@ 字节为真；"
          "③ gethostname(007B26DB→IAT[0x7E1560]) 后 007B26E0 cmp eax,-1 配 007B26E3 jne 真分支，失败记日志+xor al,al "
          "ret 8、成功记 0x84E110+mov al,1，比较对象为 -1 错误域哨兵非 0/1；无 eax 覆写；④ 仅活虚表安装点 007B0DA4"
          "（构造器 007B0D90，5 个直调者）——直调 0 条、槽位派发点扫 0 命中，是 12 行中 ④ 最弱的一行，已记入 VERDICT.md §4；"
          "该表写点仅 007B0DA4 一处（无析构写点），相关函数均不在 152 个 atexit 注册集合；④②不同源"))

R(entry="007B30B0", sub="S18", name="UDPInterfaceClass::slot23",
  r2="vt=007F7A6C slot23 (+0x5C) @007F7AC8 ; COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@",
  r2d="""entry 作为 dword 只出现 1 次：007F7AC8 (.rdata) ⇒ 唯一持有表 base=007F7A6C
      UDP 表 31 槽（0:007B4170 … 23:007B30B0 … 30:007B3920），slot23 == 本 entry ✓
      UDP TD 只有 1 个 COL ⇒ 该 31 槽表即 UDP 主虚表（非「小成员表」）
""" + COMMON_TBL,
  r3f="3b2",
  r3="""③b② 多值状态码（socket / bind = SOCKET_ERROR 哨兵）
      007B30E4  e8 b5580100   call 0x7C899E  → IAT [0x7E157C] = **WSOCK32!socket**
      007B30E9  83f8ff        cmp eax,-1
      007B30EC  89866cf00300  mov dword ptr [esi+0x3f06c],eax   （存 socket 句柄，不覆写 eax）
      007B30F2  7509          jne 0x7B30FD
        失败 007B30F4 32c0 xor al,al / 007B30FA c20400 ret 4
      007B315F  e8 34580100   call 0x7C8998  → IAT [0x7E1580] = **WSOCK32!bind**
      007B3164  83f8ff        cmp eax,-1
      007B3168  7523          jne 0x7B318D
        失败 007B316A call 0x7C897A(WSAGetLastError) / 007B3170 push 0x84E204 / 007B317C..007B3181 call [eax+4]（关 socket）
             / 007B3184 xor al,al / ret 4
        成功 007B318D.. 组包 + 007B31B3 call 0x7C89A4(setsockopt) + 007B31BC call 0x7B2630 + 007B31CE mov al,1
      ⇒ 判据是 SOCKET_ERROR(-1) 哨兵（socket 与 bind 各一次），两路动作真不同（关 socket / 继续组包入列）
      无 eax 覆写：两处 call→cmp 紧邻（007B30EC 是存值不是覆写比较对象）""",
  r4="ctor 007B2DB0 @007B2E2D mov [esi],0x7f7a6c + 派发点 0069C457 call [edx+0x5c]",
  r4d="""④ 使用见证
      (a) 直调 0 条
      (b) 活虚表安装点 007B2E2D（UDP ctor）
      (c) 真实派发点：0069C436 mov ecx,[0x887628] → 0069C457 ff525c call dword ptr [edx+0x5c]（slot23）
""" + CTOR_TXT,
  ss="no",
  r5="""逐项核数值，全中：007B30E4(socket) ✓ 007B315F(bind) ✓ cmp eax,-1 ✓ jne ✓
      ② vt 007F7A6C slot+0x5C 槽 007F7AC8 ✓ COL 0080EBE0 ✓ TD 0084E1C0 ✓（主虚表）✓
      ④ 007B2E2D ✓ in_func 007B2DB0 ✓ direct1 ✓ 非析构 ✓；排除 007B2E56(析构 007B2E50) ✓
        007B4176(删除析构 007B4170 = **本表 slot0**，实测装 vt 后 call 0x7C8B3D 释放) ✓
      API 身份独立复核：socket=0x7E157C ✓ bind=0x7E1580 ✓ closesocket=0x7E1584 ✓ setsockopt=0x7E1554 ✓""",
  verdict="PASS",
  reason=("007B30B0：② 唯一持有表 007F7A6C（UDP TD 仅 1 COL ⇒ 31 槽主虚表），slot23=+0x5C @007F7AC8，"
          "COL=0080EBE0→TD=0084E1C0→内联 .?AVUDPInterfaceClass@@；③ socket(007B30E4→IAT[0x7E157C]) 后 007B30E9 "
          "cmp eax,-1+007B30F2 jne（失败 xor al,al ret 4），bind(007B315F→IAT[0x7E1580]) 后 007B3164 cmp eax,-1+"
          "007B3168 jne（失败 WSAGetLastError+call [eax+4] 关 socket，成功 007B318D 组包+setsockopt+call 007B2630+mov al,1）"
          "⇒ SOCKET_ERROR 哨兵多值状态码非 bool，两路动作真不同；④ 锚活虚表安装点 007B2E2D（构造器 007B2DB0，direct1=0052F456），"
          "另有派发点 0069C457 call [edx+0x5c]（对象取自 0x887628）；同表另两写点 007B2E56（析构 007B2E50）、"
          "007B4176（删除析构 = slot0 = 007B4170）已排除，三函数均不在 152 个 atexit 注册集合；④②不同源"))

R(entry="007B31E0", sub="S18", name="UDPInterfaceClass::slot26",
  r2="vt=007F7A6C slot26 (+0x68) @007F7AD4 ; COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@",
  r2d="""entry 作为 dword 只出现 1 次：007F7AD4 (.rdata) ⇒ 唯一持有表 base=007F7A6C
      UDP 表 slot26 == 007B31E0 ✓；UDP TD 只有 1 个 COL ⇒ 主虚表
""" + COMMON_TBL,
  r3f="3b2",
  r3="""③b② 多值状态码（bind = SOCKET_ERROR 哨兵；另 socket 一处同形）
      007B3234  e8 65570100   call 0x7C899E  → **WSOCK32!socket**；007B323B 83feff cmp esi,-1；007B323E 750c jne
        失败 007B3240.. 32c0 xor al,al / ret 4
      007B3295  e8 fe560100   call 0x7C8998  → **WSOCK32!bind**
      007B329A  83f8ff        cmp eax,-1
      007B329D  7520          jne 0x7B32BF
        失败 007B329F 56 push esi / 007B32A0 call 0x7C8992(**closesocket**) / 007B32A6 push 0x84E294 / 007B32B6 xor al,al / ret 4
        成功 007B32BF..: 007B32C6 写组播地址表 [ebx+ecx*2+0x3f320]=bp、007B32D6 写 [ebx+edx*4+0x3f300]=esi、
             007B32E4 计数 +1、007B32EA call 0x7B2630(setsockopt 路)、007B32F4 push 0x84E274、007B32FC mov al,1
      ⇒ SOCKET_ERROR(-1) 哨兵 cmp+jne 真分支；两路动作真不同（closesocket 放弃 vs 写表+调 007B2630+成功）
      无 eax 覆写：两处 call→cmp 紧邻""",
  r4="ctor 007B2DB0 @007B2E2D + 派发点 005D90A9 call [eax+0x68]",
  r4d="""④ 使用见证
      (a) 直调 0 条
      (b) 活虚表安装点 007B2E2D（UDP ctor）
      (c) 真实派发点：005D9093 mov eax,[0x887628] → 005D90A9 ff5068 call dword ptr [eax+0x68]（slot26）
          同类另有 005D96B5/005D96DA/005D9876/005D98A8/005D9ABA 等 20 处同槽派发（均自 0x887628）
""" + CTOR_TXT,
  ss="no",
  r5="""逐项核数值，全中：007B3295 ✓ cmp eax,-1 ✓ jne(gap=0) ✓ 失败 closesocket+日志+xor al,al ✓
      成功「写组播地址表 + call 007B2630 + mov al,1」✓（007B32C6/007B32D6/007B32EA/007B32FC）
      ② vt 007F7A6C slot+0x68 槽 007F7AD4 ✓ COL 0080EBE0 ✓ TD 0084E1C0 ✓
      ④ 007B2E2D ✓ 007B2DB0 ✓ 排除两处析构写点 007B2E56 / 007B4176 ✓
      API 身份独立复核：bind=0x7E1580 ✓ socket=0x7E157C ✓ closesocket=0x7E1584 ✓""",
  verdict="PASS",
  reason=("007B31E0：② 唯一持有表 007F7A6C（UDP TD 仅 1 COL ⇒ 主虚表），slot26=+0x68 @007F7AD4，"
          "COL=0080EBE0→TD=0084E1C0→内联 .?AVUDPInterfaceClass@@；③ bind(007B3295→IAT[0x7E1580]) 后 007B329A cmp eax,-1+"
          "007B329D jne（失败 007B329F 起 call 0x7C8992=closesocket+日志+xor al,al；成功 007B32C6 写组播地址表、"
          "007B32EA call 0x7B2630、007B32FC mov al,1），另 socket(007B3234) 同形 ⇒ SOCKET_ERROR 哨兵非 bool、两路动作真不同；"
          "无 eax 覆写；④ 锚活虚表安装点 007B2E2D（构造器 007B2DB0，direct1），另有派发点 005D90A9 call [eax+0x68]"
          "（对象取自 0x887628，同槽共 20 处）；同表另两写点 007B2E56(析构)/007B4176(删除析构 slot0) 已排除，"
          "均不在 152 个 atexit 注册集合；④②不同源"))

R(entry="007B3450", sub="S18", name="UDPInterfaceClass::slot15",
  r2="vt=007F7A6C slot15 (+0x3C) @007F7AA8 ; COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@",
  r2d="""entry 作为 dword 只出现 1 次：007F7AA8 (.rdata) ⇒ 唯一持有表 base=007F7A6C
      UDP 表 slot15 == 007B3450 ✓；UDP TD 只有 1 个 COL ⇒ 主虚表
""" + COMMON_TBL,
  r3f="3b2",
  r3="""③b② 多值状态码（socket / bind = SOCKET_ERROR 哨兵）
      007B35F8  e8 a1530100   call 0x7C899E  → **WSOCK32!socket**
      007B35FD  83f8ff        cmp eax,-1
      007B3600  898770f00300  mov dword ptr [edi+0x3f070],eax  （存句柄）
      007B3606  750d          jne 0x7B3615
        失败 007B3608 5f / 007B3609 32c0 xor al,al / ret 4
      007B3653  e8 40530100   call 0x7C8998  → **WSOCK32!bind**
      007B3658  83f8ff        cmp eax,-1
      007B365B  7514          jne 0x7B3671
        失败 007B365D 8b17 mov edx,[edi] / 007B3661 ff5204 call dword ptr [edx+4]（关 socket）/ 007B3665 xor al,al / ret 4
        成功 007B3671.. 组包 + 后续 gethostname/setsockopt
      ⇒ SOCKET_ERROR(-1) 哨兵 cmp+jne 真分支，两路动作真不同
      另：入口 007B3464 ff5064 call [eax+0x64]（slot25）后 007B3469 84c0 test al,al + 007B346B jne 是**布尔返回检查**
        ⇒ 按 ③a 处理，本审计**不计入** ③b（与执行器自述一致）
      无 eax 覆写：007B35FD→007B3606（中间 007B3600 是存值，不动 eax）、007B3658→007B365B""",
  r4="ctor 007B2DB0 @007B2E2D + 派发点 0052F474 call [edx+0x3c]",
  r4d="""④ 使用见证（本行 ④ 最硬：派发点与构造点同处一个函数）
      0052F439 mov ecx,[0x887628] / 0052F43F cmp ecx,ebx / 0052F441 jne → 若为空则 0052F456 call 0x7B2DB0 新建 UDP 对象
      0052F461 mov [0x887628],ecx
      0052F471 8b11 mov edx,[ecx]
      0052F474 ff523c **call dword ptr [edx+0x3c]**  ← slot15 = 本 entry 007B3450
      ⇒ 该派发点的对象正是 0x7B2DB0 构造的 UDP 实例，槽号 +0x3C/4=15 与 ② 完全一致
      (a) 直调 0 条
      (b) 活虚表安装点 007B2E2D（UDP ctor）
""" + CTOR_TXT,
  ss="no",
  r5="""逐项核数值，全中：007B35F8(socket) ✓ 007B3653(bind) ✓ cmp eax,-1 ✓ jne ✓ 两路动作不同 ✓
      ② vt 007F7A6C slot+0x3C 槽 007F7AA8 ✓ COL 0080EBE0 ✓ TD 0084E1C0 ✓
      ④ 007B2E2D ✓ 007B2DB0 ✓ direct1 ✓ 排除析构写点 ✓
      「call 0x4068E0 空 stub→test→je 属布尔不计」：0x4068E0 实测**单字节 c3 ret**（确为空 stub ✓）
      API 身份独立复核：socket=0x7E157C ✓ bind=0x7E1580 ✓ closesocket=0x7E1584 ✓ gethostname=0x7E1560 ✓""",
  verdict="PASS",
  reason=("007B3450：② 唯一持有表 007F7A6C（UDP TD 仅 1 COL ⇒ 主虚表），slot15=+0x3C @007F7AA8，"
          "COL=0080EBE0→TD=0084E1C0→内联 .?AVUDPInterfaceClass@@；③ socket(007B35F8→IAT[0x7E157C]) 后 007B35FD "
          "cmp eax,-1+007B3606 jne（失败 xor al,al ret 4），bind(007B3653→IAT[0x7E1580]) 后 007B3658 cmp eax,-1+"
          "007B365B jne（失败 007B3661 call [edx+4] 关 socket），两路动作真不同；入口 007B3469 test al,al 属 ③a 不计；"
          "④ 最硬的一行——派发点 0052F474 call [edx+0x3c] 与构造点 0052F456 同在 0x887628 取用函数内，槽号 15 与 ② 一致，"
          "另锚活虚表安装点 007B2E2D（构造器 007B2DB0，direct1）；同表另两写点 007B2E56(析构)/007B4176(删除析构 slot0) 已排除，"
          "不在 152 个 atexit 注册集合；0x4068E0 实测确为单字节 ret；④②不同源"))

R(entry="007B3890", sub="S18", name="UDPInterfaceClass::slot7",
  r2="vt=007F7A6C slot7 (+0x1C) @007F7A88 ; COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@",
  r2d="""entry 作为 dword 只出现 1 次：007F7A88 (.rdata) ⇒ 唯一持有表 base=007F7A6C
      UDP 表 slot7 == 007B3890 ✓（注意：基类 Winsock 的 slot7 是 007B1BC0，UDP 在此**确实覆写**，
      因此本行与 007B1BC0 是两条不同实现，非同一 entry 的两个名字）
      UDP TD 只有 1 个 COL ⇒ 主虚表
""" + COMMON_TBL,
  r3f="3b2",
  r3="""③b② 多值状态码（WSAAsyncSelect = SOCKET_ERROR 哨兵）
      007B38C6  e8 f1500100   call 0x7C89BC  → IAT [0x7E156C] = **WSOCK32!WSAAsyncSelect**
      007B38CB  83f8ff        cmp eax,-1
      007B38CE  7419          je 0x7B38E9
        失败 007B38E9 push 0x84E3D0 / call 0x4068E0 / 007B38F6 32c0 xor al,al / ret
        成功 007B38D0 8b8630f30300 mov eax,[esi+0x3f330] / inc ebx / add edi,4 / cmp / 007B38DC jl 回边（遍历地址表）
             → 007B38DE e86d14e2ff call 0x5D4D50 / 007B38E5 b001 mov al,1 / ret
      ⇒ SOCKET_ERROR(-1) 哨兵 cmp+je 真分支；两路动作真不同（记日志失败 vs 遍历地址表后 call 0x5D4D50 成功）
      入口 007B3895 e8 26e3ffff call 0x7B1BC0（**直调** 另一行 entry）+ 007B389A test al,al + 007B389C je
        是布尔检查 ⇒ 属 ③a，不计入 ③b
      无 eax 覆写：007B38C6→007B38CB 紧邻""",
  r4="ctor 007B2DB0 @007B2E2D + 派发点 0052F4AC call [eax+0x1c]",
  r4d="""④ 使用见证
      0052F4A0 8b0d28768800  mov ecx,[0x887628]
      0052F4AA 8b01          mov eax,[ecx]
      0052F4AC ff501c        **call dword ptr [eax+0x1c]**   ← slot7 = 本 entry 007B3890
      ⇒ 与 007B3450 同一函数 0052F4xx，对象同为 0x887628（UDP 实例），槽号 +0x1C/4=7 与 ② 一致
      (a) 直调 0 条（本 entry 无直接调用者）
      (b) 活虚表安装点 007B2E2D（UDP ctor）
""" + CTOR_TXT,
  ss="no",
  r5="""逐项核数值，全中：007B38C6 ✓ cmp eax,-1 ✓ je(gap=0) ✓ 失败日志+xor al,al ✓
      成功「遍历地址表 + call 0x5D4D50 + mov al,1」✓（007B38DC 回边、007B38DE call 0x5D4D50、007B38E5 mov al,1）
      ② vt 007F7A6C slot+0x1C 槽 007F7A88 ✓ COL 0080EBE0 ✓ TD 0084E1C0 ✓
      ④ 007B2E2D ✓ 007B2DB0 ✓ 排除析构写点 ✓
      API 身份独立复核：WSAAsyncSelect=0x7E156C ✓""",
  verdict="PASS",
  reason=("007B3890：② 唯一持有表 007F7A6C（UDP TD 仅 1 COL ⇒ 主虚表），slot7=+0x1C @007F7A88，"
          "COL=0080EBE0→TD=0084E1C0→内联 .?AVUDPInterfaceClass@@；本行与 007B1BC0 是两条不同实现"
          "（UDP 覆写了基类 Winsock 的 slot7），非同一 entry 的两个名字；③ WSAAsyncSelect(007B38C6→IAT[0x7E156C]) 后 "
          "007B38CB cmp eax,-1+007B38CE je（失败记日志+xor al,al；成功 007B38DC 回边遍历地址表、007B38DE call 0x5D4D50、"
          "007B38E5 mov al,1）⇒ SOCKET_ERROR 哨兵非 bool；入口 007B389A test al,al 属 ③a 不计；"
          "④ 派发点 0052F4AC call [eax+0x1c]（对象取自 0x887628，槽 7 与 ② 一致），另锚活虚表安装点 007B2E2D"
          "（构造器 007B2DB0，direct1）；同表另两写点 007B2E56(析构)/007B4176(删除析构 slot0) 已排除；④②不同源"))

R(entry="007B3AA0", sub="S18", name="UDPInterfaceClass::slot16",
  r2="vt=007F7A6C slot16 (+0x40) @007F7AAC ; COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@",
  r2d="""entry 作为 dword 只出现 1 次：007F7AAC (.rdata) ⇒ 唯一持有表 base=007F7A6C
      UDP 表 slot16 == 007B3AA0 ✓（IPX 的 slot16 是 007B13D0，两者是不同实现）
      UDP TD 只有 1 个 COL ⇒ 主虚表
""" + COMMON_TBL,
  r3f="3b2",
  r3="""③b② 多值状态码（sendto = SOCKET_ERROR 哨兵 + WSA 错误码二级判别）
      007B3D75  e8 364c0100   call 0x7C89B0  → IAT [0x7E1558] = **WSOCK32!sendto**
      007B3D7A  83f8ff        cmp eax,-1
      007B3D7D  757c          jne 0x7B3DFB          ← 成功：继续缓冲摘除
      007B3D7F  e8 f64b0100   call 0x7C897A (WSAGetLastError)
      007B3D84  3d 33270000   cmp eax,0x2733         (WSAEWOULDBLOCK)
      007B3D89  7470          je 0x7B3DFB           ← 可重试：与成功同落点
      007B3D8B  call 0x7C897A / 007B3D91 push 0x84E4B4(日志) / 007B3DA4 ff5224 call [edx+0x24] / 007B3DAA xor eax,eax / ret
      ⇒ 返回域三态 {-1∧0x2733, -1∧其它错误, ≥0 字节数}，真错误与可重试分离 ⇒ **多值状态码，非 {0,1} 布尔**
      无 eax 覆写：007B3D75→007B3D7A 紧邻""",
  r4="ctor 007B2DB0 @007B2E2D + 派发点 007775FF call [eax+0x40]",
  r4d="""④ 使用见证
      (a) 直调 0 条
      (b) 活虚表安装点 007B2E2D（UDP ctor）
      (c) 真实派发点：007775C1 mov eax,[0x887628] → 007775FF ff5040 call dword ptr [eax+0x40]（slot16）
          注：0x887628 在 IPX 模式下装 IPX 实例（其 slot16=007B13D0）、UDP 模式下装 UDP 实例（slot16=本行），
          故该派发点覆盖 slot16 这一槽的两个实现，本行是其 UDP 侧
""" + CTOR_TXT,
  ss="no",
  r5="""逐项核数值，全中：007B3D75 ✓ cmp eax,-1 ✓ jne(gap=0) ✓ 失败 WSAGetLastError+cmp 0x2733+日志+ret ✓
      成功「继续缓冲摘除」✓；② vt 007F7A6C slot+0x40 槽 007F7AAC ✓ COL 0080EBE0 ✓ TD 0084E1C0 ✓
      ④ 007B2E2D ✓ 007B2DB0 ✓ 排除析构写点 ✓
      API 身份独立复核：sendto=0x7E1558 ✓ WSAGetLastError=0x7E1574 ✓""",
  verdict="PASS",
  reason=("007B3AA0：② 唯一持有表 007F7A6C（UDP TD 仅 1 COL ⇒ 主虚表），slot16=+0x40 @007F7AAC，"
          "COL=0080EBE0→TD=0084E1C0→内联 .?AVUDPInterfaceClass@@（与 IPX 的 slot16=007B13D0 是不同实现）；"
          "③ sendto(007B3D75→IAT[0x7E1558]) 后 007B3D7A cmp eax,-1+007B3D7D jne，失败再 007B3D84 cmp eax,0x2733 + "
          "007B3D89 je 0x7B3DFB（WSAEWOULDBLOCK 视为可重试）否则 007B3D91 日志+007B3DA4 call [edx+0x24]+xor eax,eax"
          "⇒ 三态状态码非 bool、真错误与可重试分离；④ 锚活虚表安装点 007B2E2D（构造器 007B2DB0，direct1），"
          "另有派发点 007775FF call [eax+0x40]（对象取自 0x887628）；同表另两写点 007B2E56(析构)/007B4176(删除析构 slot0) "
          "已排除，均不在 152 个 atexit 注册集合；④②不同源"))

HEAD = "entry\tsubsystem\tverdict\tring2_at\tring3b_form\tring4_at\tsame_source\treason\n"

# ---- emit verdict.tsv ----
def main():
    lines = [HEAD.rstrip("\n")]
    for r in ROWS:
        lines.append("\t".join([r["entry"], r["sub"], r["verdict"], r["r2"], r["r3f"],
                                r["r4"], r["ss"], r["reason"].replace("\t", " ").replace("\n", " ")]))
    with open(os.path.join(OUT, "verdict.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    # ---- emit evidence files ----
    for r in ROWS:
        body = []
        body.append("ROW %s  (%s)  %s" % (r["entry"], r["sub"], r["name"]))
        body.append("=" * 96)
        body.append("审计：agent-233（异族独立审计）。以下每一行地址/字节均由 work/pe.py 从 gamemd.exe 直接读出。")
        body.append("")
        body.append("[1] ② 类身份（全表枚举）")
        body.append("  " + r["r2"])
        body.append(r["r2d"])
        body.append("")
        body.append("[2] ③b 具体形态：%s" % r["r3f"])
        body.append(r["r3"])
        body.append("")
        body.append("[3] ④ 使用见证")
        body.append("  " + r["r4"])
        body.append(r["r4d"])
        body.append("")
        body.append("[4] ④ 与 ② 不同源：same_source = %s" % r["ss"])
        body.append("""  ② 的证据：.rdata 虚表槽值 == entry + RTTI 链 COL→TD→TD+8 内联名
  ④ 的证据：.text 指令（构造器里的 mov dword ptr [obj],<vt>）或 .text 里的 call [reg+slot]
  两者字面是不同的字节事实。
  ⚠ 残余同源枢轴（照实记）：④ 要落到「本 entry 被用」仍需 vt[slot]==entry 这一槽位事实，
    该槽位事实同时被 ② 使用。按 §12.3 D-40 字面口径这是「同一槽位顶两环」的残余；
    但本行 ④ 的锚点是 .text 写点/派发指令，而非 ② 的 .rdata 槽，与 S13_PUSH 6 行（④ 直接引「槽 +0x 驻本 entry」）不同型。""")
        body.append("")
        body.append("[5] 语义与实测一致")
        body.append(r["r5"])
        body.append("")
        body.append("=" * 96)
        body.append("VERDICT: %s   ring3b_form=%s   same_source=%s" % (r["verdict"], r["r3f"], r["ss"]))
        with open(os.path.join(OUT, "EVIDENCE", "ROW_%s.txt" % r["entry"]), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write("\n".join(body) + "\n")

    print("rows=%d pass=%d fail=%d" % (
        len(ROWS), sum(1 for r in ROWS if r["verdict"] == "PASS"),
        sum(1 for r in ROWS if r["verdict"] == "FAIL")))


if __name__ == "__main__":
    main()
