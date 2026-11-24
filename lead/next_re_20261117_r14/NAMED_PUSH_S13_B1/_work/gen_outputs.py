# -*- coding: utf-8 -*-
"""S13 B1 逐行 EVIDENCE 生成器。数据均来自本卡 _work 下脚本的实测反汇编。
仅四环齐全的行同时写入 delta.tsv / base_rate.tsv。"""
import os
WORK = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.dirname(WORK)
EVD  = os.path.join(OUT, "EVIDENCE")
os.makedirs(EVD, exist_ok=True)

# 每行：entry -> (name, dict with ring facts, pass?, semantics)
ROWS = {}

ROWS["004684E0"] = dict(name="BulletClass::slot10", passed=True,
 semantics="BulletClass 全局对象容器移除：经容器虚表 call [eax+0x10] 查自身下标（-1 表示未命中则跳过），命中则前移压缩数组；③b② 的 -1 哨兵被 cmp/je 消费。",
 r1="entry 004684E0；atlas size=392 B，位于 .text=[0x401000,0x7E038D)，capstone skipdata=True；函数边界自洽（004684E0 起 mov eax,[esp+8]，00468665 ret 8）。",
 r2="vtable slot@007E470C（.rdata），vtable base=007E46E4，slot#10（+0x40）：u32(007E470C)=004684E0（=本 entry）。RTTI 链：u32(007E46E4-4)=COL 007FC7B0（sig=0）→ [COL+0xC]=TD 0081AF70 → TD+8 name@0081AF78 = '.?AVBulletClass@@'。主虚表（ctor 00466380 在 00466425 `c7 06 e4 46 7e 00`=mov [esi],0x7E46E4 装到 [esi]），非小成员表。② 由 RTTI+槽独立钉住。",
 r3="③b②（Find 返 -1 下标约定，卡片明列算）：0046862A `ff 50 10`=call dword ptr [eax+0x10]（容器虚表 Find）→ 0046862D `83 f8 ff`=cmp eax,-1 → 00468630 `74 2d`=je 0046865F；call 与 cmp 之间 0 字节，无 eax 覆写。je 路（未命中）直落收尾 0046865F..00468665 pop/ret 8；fall-through（命中）执行压缩循环 00468647..0046865D：`8b 14 81`=mov edx,[ecx+eax*4] / `89 54 81 fc`=mov [ecx+eax*4-4],edx（前移），边界 cmp eax,[0x89DE28]；两路动作真不同。失败约定是可伪证的 -1 下标哨兵（非零非一），非 {0,1} 布尔。eax 覆写陷阱：未触发。多路同一 call：未触发。",
 r4="④=活虚表构造安装点：`@00466425` `c7 06 e4 46 7e 00`=mov dword ptr [esi],0x7E46E4，宿主函数 00466380（size 319），其 00466384 `call 005F3900` = ObjectClass 构造器（实测该函数开头 `call 00410170` 且写 4 张 .?AVObjectClass@@ RTTI 虚表）⇒ 真构造器；non-atexit；写点 00466425 在本 entry [004684E0,00468668) 之外。旁证：@0046AEB5 宿主 0046AE70（0046AE97 call 005F3B50 = ObjectClass 构造器）亦为有效构造安装点。注意 @00466566 宿主 00466560 调 007258D0 且两处 cmp eax,-1 ⇒ 析构器，未采作 ④（㉓ 主动排除）。",
 r24="②④不同源：② 取 .rdata 虚表槽字节 + RTTI COL/TD 数据链；④ 取 .text 构造期 `mov [esi],vt` 指令（与 ② 槽不是同一 artifact）；同源判定=no。")

ROWS["00468670"] = dict(name="BulletClass::slot124", passed=False,
 semantics="不产出：③b 缺可伪证返回约定。",
 r1="entry 00468670；atlas size=1304 B，位于 .text；函数边界自洽（00468670 push ebp，004686.. ret）。",
 r2="vtable slot@007E48D4（.rdata），vtable base=007E46E4，slot#124（+0x1F0，124*4=0x1F0）：u32(007E48D4)=00468670。RTTI：COL 007FC7B0（sig=0）→ TD 0081AF70 → name@0081AF78='.?AVBulletClass@@'。主虚表的槽号与名字 slot124 自洽（注：core2.resolve_slot 仅回扫 k<=40，k=124 超窗，故改用全 .rdata 直接比对确认，slot#124 唯一引用）。② 钉住。",
 r3="③b FAIL：全函数 4 个 call→test/cmp→jcc 站点均无可伪证多值约定——(1) 00468684 call 005F4EC0 → test al,al@00468689 → je@0046868B：al 字节布尔，callee 2 个 ret 原点为 call/unknown、无常量；(2) 0046894A call 004CC100 → cmp@00468951 → je@00468953：callee 仅返回常量 0（n_rets=1, origins={('imm',0)}），为零/布尔判断；(3) 00468A4B 间接 call → cmp@00468A4E → jne@00468A51：callee 不可静态定位；(4) 00468A93 call 004E1130 → test@00468AA4 → jle@00468AA6：callee ret 原点为 call，无失败常量。channel_screen_A P3=0。{0,1}/零值单常量不算多值状态码 ⇒ ③b 不成立。",
 r4="④ 活表构造安装点存在（vt 007E46E4 的 00466425/0046AEB5，见 004684E0 行），但 ③b 已 FAIL。",
 r24="②④不同源，但整体不成立。")

ROWS["0046C6A0"] = dict(name="BulletTypeClass::slot5", passed=False,
 semantics="不产出：③b 为模板假句/零值布尔，非可伪证多值约定。",
 r1="entry 0046C6A0；atlas size=134 B，位于 .text，边界自洽（0046C6A0 起，0046C723 ret 8）。",
 r2="vtable slot@007E495C（.rdata），vtable base=007E4948，slot#5（+0x14）：u32(007E495C)=0046C6A0。RTTI：COL 007FC868（sig=0）→ TD 0081AFB0 → name@0081AFB8='.?AVBulletTypeClass@@'。主虚表（ctor 0046BBC0 在 0046BCE6 写 [esi]=007E4948）。② 钉住。",
 r3="③b FAIL：唯一站点 0046C6AB `call 005F9720` → 0046C6B0 test eax,eax → 0046C6B2 jl 0046C722。callee 005F9720 调 007C8B3D(free)+005F9B60，返回值仅 0（consts={0}, n_rets=1）⇒ 零值布尔，非多值状态码。jl 目标与 fall-through 最终都收敛到 0046C720 `xor eax,eax` / 0046C723 ret 8，且函数主体是对象初始化模板：0046C6C4/C6CA/C6D1/C6D8 连装 4 张虚表 + 0046C6F9/0046C70A/0046C71B 三次 call 006CF240 初始化成员 —— 正是卡片禁止的『对象初始化/清零式』模板假句。channel_screen_A P3=0。③b 不成立。",
 r4="④ 活表构造安装点 @0046BCE6（宿主 0046BBC0，0046BBC9 call 005F7090 = 真构造器）存在且在行外；但 @0046C6C4 在本 entry 体内（行内无效），@0046C896 宿主为析构器（007258D0 + free 007C8B3D，㉓ 排除）。④ 已具备，③b 不具备。",
 r24="②④不同源，但整体不成立。")

ROWS["0046C730"] = dict(name="BulletTypeClass::slot6", passed=False,
 semantics="不产出：③b 为 ③a 纯转发（对被调已归一化的返回值做幂等归一，无实质语义）。",
 r1="entry 0046C730；atlas size=29 B，位于 .text，边界自洽（0046C730..0046C74A ret 0xc）。",
 r2="vtable slot@007E4960（.rdata），vtable base=007E4948，slot#6（+0x18）：u32(007E4960)=0046C730。RTTI：COL 007FC868 → TD 0081AFB0 → name@0081AFB8='.?AVBulletTypeClass@@'。主虚表，slot#6 与名字自洽。② 钉住。",
 r3="③b FAIL（③a 纯转发）：0046C73F `call 005F9950` → 0046C744 test eax,eax → 0046C746 jl 0046C74A；0046C748 `xor eax,eax`。但被调 005F9950 自身已是『负→原样 / 非负→0』归一化桩（005F9964 test / 005F9966 jl / 005F9968 xor / 005F996A ret），其返回值域仅 {负错误码, 0}。本行 eax 再经 test/jl/xor：负→原样、0→0，是幂等恒等变换，两路动作在返回码上无差别，除转调 005F9950 外无任何其他语义动作（全函数仅 3 参转调 + 返回）。按卡片『禁止 ③a 形态（纯转发）』判 ③b 不成立。另：底层 00410320 的 E_POINTER 错误码归一是被调 005F9950 做的，不是本行自身合同；不得借被调者内部的归一冒充本行 ③b。eax 覆写：未触发，但不改纯转发判定。",
 r4="④=活虚表构造安装点：`@0046BCE6` `c7 06 48 49 7e 00`=mov [esi],0x7E4948，宿主 0046BBC0（size 542），其 0046BBC9 `call 005F7090` = 真构造器（实测 005F7090 内 call 00410800 且写 .?AVObjectTypeClass@@ 虚表）⇒ 构造器；non-atexit；写点在本 entry [0046C730,0046C74D) 之外。",
 r24="②④不同源：②=.rdata 槽+RTTI 链；④=.text 构造写点；同源=no。")

ROWS["00629FD0"] = dict(name="ParasiteClass::slot23", passed=True,
 semantics="ParasiteClass 分配并初始化寄生体：operator new 分配，失败（NULL）跳过初始化，成功则用返回指针构造；③b② 的分配空指针返回约定由 test/je 分支消费。",
 r1="entry 00629FD0；atlas size=645 B，位于 .text，边界自洽（00629FD0..0062A254）。",
 r2="vtable slot@007EF8EC（.rdata），vtable base=007EF890，slot#23（+0x5C）：u32(007EF8EC)=00629FD0。RTTI：COL 00807B30（sig=0）→ TD 00836640 → name@00836648='.?AVParasiteClass@@'。主虚表，② 钉住。",
 r3="③b②（可伪证返回约定——分配 NULL）：0062A0D8 `call 007C8E17`（operator new）→ 0062A0E0 `85 c0`=test eax,eax → 0062A0E2 `74 24`=je 0062A108；call 与 test 零间隔，无 eax 覆写。失败约定=NULL(0)，成功=非空对象指针，调用方 je 分支：je 路直落 0062A108；fall-through 路真用 eax（0062A103 `8b c8`=mov ecx,eax → call 0062DC50 初始化）。另一同型站点 0062A144 call 007C8E17 → test@0062A14C → je@0062A14E。（第三站点 0062A116 call 004C93D0 仅返回 0=布尔，不作 ③b 依据。）『失败返 NULL / 成功返指针』是可伪证返回约定，非 {0,1} 布尔状态位。eax 覆写/多路同一 call：未触发。",
 r4="④=活虚表构造安装点：`@00629231` `c7 06 90 f8 7e 00`=mov [esi],0x7EF890，宿主 00629210（size 145），其 00629213 `call 00410170` = AbstractClass 构造器（实测写 .?AVAbstractClass@@ 等 6 张 RTTI 虚表）⇒ 真构造器；non-atexit；写点在本 entry [00629FD0,0062A255) 之外。旁证 @006292D8（宿主 006292B0，同调 00410170）、@006295FA（宿主 006295B0，调 004101C0）。@0062AF70 宿主两处 cmp eax,-1=析构器（㉓ 排除）。",
 r24="②④不同源：②=.rdata 槽+RTTI 链；④=.text 构造写点；同源=no。")

ROWS["00708080"] = dict(name="death_handler", passed=False,
 semantics="不产出：② 无 RTTI/虚表（仅 direct caller）；③b 为 {0,1} 布尔；④ direct-only 不足。",
 r1="entry 00708080；atlas size=1846 B，位于 .text，边界自洽。",
 r2="② FAIL：全镜像 dword 引用扫描未发现任何 vtable 槽指向本 entry（refs_total 仅 direct callers）；无 .?AV RTTI 链可钉类身份。三个 E8 direct caller（004422BC / 004D749A / 007027E9）只证明被直接调用，不能替代 ②（'direct call ⇒ 已证' 判据已作废）。slotN 类名线索也不存在（名字 death_handler）。② 不成立。",
 r3="③b FAIL：唯一通道 A 站点 call@0070813E → cmp eax,1@00708141 → jne@00708144；比较常量 imm=1 属 {0,1} 布尔，卡片明算不算可伪证多值状态码；callee 无静态可解析失败常量。③b 不成立。",
 r4="④ FAIL：仅有 3 个 direct caller，无活虚表派发；D-40『direct-only 不足』。④ 不成立。",
 r24="三环皆缺，不产出。")

ROWS["0075E0C0"] = dict(name="WarheadTypeClass::slot5", passed=True,
 semantics="WarheadTypeClass 流读入（Load）：经 00410380 读包装读 HRESULT，失败 E_POINTER 负码跳收尾、成功继续构造并写回；③b② 可伪证错误码由 test/jl 分支消费。",
 r1="entry 0075E0C0；atlas size=501 B，位于 .text，边界自洽（0075E0C0..0075E2B5）。",
 r2="vtable slot@007F6B44（.rdata），vtable base=007F6B30，slot#5（+0x14）：u32(007F6B44)=0075E0C0。RTTI：COL 0080D360（sig=0）→ TD 00847C18 → name@00847C20='.?AVWarheadTypeClass@@'。主虚表（ctor 0075CEC0 在 0075D0BA 写 [ebp]=007F6B30）。② 钉住。",
 r3="③b②（可伪证错误码）：0075E0F0 `e8 8b 22 cb ff`=call 00410380（流读入包装，IStream::Read 走虚表 +0xC：0041039E/004103CD FF 50/55 0C）→ 0075E0F5 `85 c0`=test eax,eax → 0075E0F7 `0f 8c b1 01 00 00`=jl 0075E2AE；call 与 test 零间隔。callee 失败原点 00410389 `b8 03 40 00 80`=E_POINTER 0x80004003（负值），成功原点不同 ⇒ 多值状态码，可伪证。jl 路（失败）直落 0075E2AE 收尾；fall-through 路继续执行构造（0075E108 call 00410960 AbstractTypeClass 构造器 / 0075E13E 装虚表 / 0075E117 call 00525250），两路动作真不同。读方向：callee 走 +0xC（Read）⇒ 语义『流读入』，未写反。eax 覆写/多路同一 call：未触发。",
 r4="④=活虚表构造安装点：`@0075D0BA` `c7 45 00 30 6b 7f 00`=mov dword ptr [ebp],0x7F6B30，宿主 0075CEC0（size 752），其 0075CECB `call 00410800` = 真构造器（实测 00410800 内 call 00410170 且写 4 张 .?AVAbstractTypeClass@@ RTTI 虚表），全函数无 free（007C8B3D）/cmp eax,-1、non-atexit ⇒ 构造器；写点在本 entry [0075E0C0,0075E2B5) 之外。注意 @0075E13E 在本行体内（行内无效），@0075E516 宿主 0075E510 为析构器（007258D0 + free 007C8B3D，㉓ 排除），均未采作 ④；④ 只靠 0075CEC0→0075D0BA 成立。",
 r24="②④不同源：②=.rdata 槽+RTTI 链；④=.text 构造写点；同源=no。")

ROWS["0075E2C0"] = dict(name="WarheadTypeClass::slot6", passed=True,
 semantics="WarheadTypeClass 流写出（Save）：经 00410320 写包装写 HRESULT，失败 E_POINTER 负码跳收尾、成功继续；③b② 可伪证错误码由 test/jl 分支消费。",
 r1="entry 0075E2C0；atlas size=225 B，位于 .text，边界自洽（0075E2C0..0075E3A1）。",
 r2="vtable slot@007F6B48（.rdata），vtable base=007F6B30，slot#6（+0x18）：u32(007F6B48)=0075E2C0。RTTI：COL 0080D360 → TD 00847C18 → name@00847C20='.?AVWarheadTypeClass@@'。主虚表，slot#6 自洽。② 钉住。",
 r3="③b②（可伪证错误码）：0075E2D1 `e8 4a 20 cb ff`=call 00410320（流写出包装，IStream::Write 走虚表 +0x10：00410348/0041035E FF 50/53 10）→ 0075E2D6 `85 c0`=test eax,eax → 0075E2D8 `0f 8c be 00 00 00`=jl 0075E39C；call 与 test 零间隔。callee 失败原点 0041032B `b8 03 40 00 80`=E_POINTER 0x80004003，多值状态码，可伪证。jl 路直落 0075E39C 收尾，fall-through 路继续执行，两路动作不同。写方向：callee 走 +0x10（Write）⇒ 语义『流写出』，未写反。eax 覆写/多路同一 call：未触发。",
 r4="④=活虚表构造安装点：`@0075D0BA` `c7 45 00 30 6b 7f 00`=mov [ebp],0x7F6B30，宿主 0075CEC0（0075CECB call 00410800 真构造器、无 free/cmp -1、non-atexit），写点在本 entry [0075E2C0,0075E3A1) 之外。@0075E516 宿主析构器（㉓ 排除）。",
 r24="②④不同源：同源=no。")

ROWS["00772CD0"] = dict(name="WeaponTypeClass::slot5", passed=True,
 semantics="WeaponTypeClass 流读入（Load）：经 00410380 读包装读 HRESULT，失败 E_POINTER 负码跳收尾、成功继续；③b② 可伪证错误码由 test/jl 分支消费。",
 r1="entry 00772CD0；atlas size=476 B，位于 .text，边界自洽（00772CD0..00772EAC）。",
 r2="vtable slot@007F73CC（.rdata），vtable base=007F73B8，slot#5（+0x14）：u32(007F73CC)=00772CD0。RTTI：COL 0080E460（sig=0）→ TD 00849248 → name@00849250='.?AVWeaponTypeClass@@'。主虚表（ctor 00771C70 在 00771E77 写 [esi]=007F73B8）。② 钉住。",
 r3="③b②（可伪证错误码）：00772CFD `e8 7e d6 c9 ff`=call 00410380（读包装，+0xC=IStream::Read）→ 00772D02 `85 c0`=test eax,eax → 00772D04 `0f 8c 9c 01 00 00`=jl 00772EA6；call 与 test 零间隔。callee 失败原点 00410389 `b8 03 40 00 80`=E_POINTER 0x80004003，多值状态码；jl 路直落 00772EA6 收尾，fall-through 路继续执行，两路动作不同。读方向：+0xC=Read ⇒『流读入』，未写反。eax 覆写陷阱：第二站点 00772E73 call 006CF240 → test → jle 存在 mov eax 类覆写，已按卡片剔除，不作 ③b 依据；主站点无覆写。",
 r4="④=活虚表构造安装点：`@00771E77` `c7 06 b8 73 7f 00`=mov [esi],0x7F73B8，宿主 00771C70（size 641），其 00771C7A `call 00410800` = 真构造器（实测含 .?AVAbstractTypeClass@@ 虚表安装），non-atexit，写点在本 entry [00772CD0,00772EAC) 之外。旁证 @00771F28（宿主 00771F00，00771F08 call 00410960 真构造器）。@007730F7 宿主 007730F0 有 free(007C8B3D)×2 ⇒ 析构器（㉓ 排除）。",
 r24="②④不同源：同源=no。")

ROWS["00772EB0"] = dict(name="WeaponTypeClass::slot6", passed=True,
 semantics="WeaponTypeClass 流写出（Save）：经 00410320 写包装写 HRESULT，失败 E_POINTER 负码跳收尾、成功继续；③b② 可伪证错误码由 test/jl 分支消费。",
 r1="entry 00772EB0；atlas size=225 B，位于 .text，边界自洽（00772EB0..00772F91）。",
 r2="vtable slot@007F73D0（.rdata），vtable base=007F73B8，slot#6（+0x18）：u32(007F73D0)=00772EB0。RTTI：COL 0080E460 → TD 00849248 → name@00849250='.?AVWeaponTypeClass@@'。主虚表，slot#6 自洽。② 钉住。",
 r3="③b②（可伪证错误码）：00772EC1 `e8 5a d4 c9 ff`=call 00410320（写包装，+0x10=IStream::Write）→ 00772EC6 `85 c0`=test eax,eax → 00772EC8 `0f 8c be 00 00 00`=jl 00772F8C；call 与 test 零间隔。callee 失败原点 0041032B `b8 03 40 00 80`=E_POINTER 0x80004003，多值状态码；jl 路直落 00772F8C 收尾，fall-through 路继续执行，两路动作不同。写方向：+0x10=Write ⇒『流写出』，未写反。eax 覆写/多路同一 call：未触发。",
 r4="④=活虚表构造安装点：`@00771E77` `c7 06 b8 73 7f 00`=mov [esi],0x7F73B8，宿主 00771C70（00771C7A call 00410800 真构造器、non-atexit），写点在本 entry [00772EB0,00772F91) 之外。@007730F7 宿主析构器（㉓ 排除）。",
 r24="②④不同源：同源=no。")

ORDER = ["004684E0","00468670","0046C6A0","0046C730","00629FD0",
         "00708080","0075E0C0","0075E2C0","00772CD0","00772EB0"]

def ring_status(e, d):
    # 返回 (r2, r3b, r4)
    if e == "00708080": return ("FAIL","FAIL","FAIL")
    if e in ("00468670","0046C6A0","0046C730"): return ("OK","FAIL","OK")
    return ("OK","OK","OK")

# 写 EVIDENCE
for e in ORDER:
    d = ROWS[e]
    p = os.path.join(EVD, "ROW_%s.txt" % e)
    with open(p, "w", encoding="utf-8") as f:
        f.write("# ROW %s  S13  %s\n\n" % (e, d["name"]))
        f.write("- entry=%s（大写十六进制，无 0x；delta entry 列原样）\n" % e)
        f.write("- 裁定：%s（① 全部 PASS；②/③b/④ 见下）\n\n" % ("四环齐全，产出 [已证]" if d["passed"] else "不产出"))
        f.write("## 环① 入口与函数边界\n%s\n\n" % d["r1"])
        f.write("## 环② 类身份（RTTI/虚表归属，独立取证）\n%s\n\n" % d["r2"])
        f.write("## 环③b 整体合同（只认 ③b；列地址与字节）\n%s\n\n" % d["r3"])
        f.write("## 环④ 使用见证（活虚表构造安装点，与 ② 不同源）\n%s\n\n" % d["r4"])
        f.write("## ②④ 不同源核查\n%s\n\n" % d["r24"])
        f.write("## 四环结论\n")
        r2,r3,r4 = ring_status(e,d)
        f.write("- ① PASS / ② %s / ③b %s / ④ %s\n" % (r2,r3,r4))
        f.write("- delta：%s\n" % ("列入（grade=[已证]）" if d["passed"] else "不列入"))
    print("EVIDENCE", e)

# 写 delta.tsv
def escape(s): return s.replace("\t"," ").replace("\n"," ")
with open(os.path.join(OUT,"delta.tsv"),"w",encoding="utf-8") as f:
    f.write("entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\n")
    for e in ORDER:
        d = ROWS[e]
        if not d["passed"]: continue
        evp = "D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/NAMED_PUSH_S13_B1/EVIDENCE/ROW_%s.txt" % e
        f.write("%s\tS13\t%s\t%s\t[已证]\t%s\n" % (e, d["name"], escape(d["semantics"]), evp))

# 写 base_rate.tsv
r2ok = sum(1 for e in ORDER if ring_status(e,ROWS[e])[0]=="OK")
r3ok = sum(1 for e in ORDER if ring_status(e,ROWS[e])[1]=="OK")
r4ok = sum(1 for e in ORDER if ring_status(e,ROWS[e])[2]=="OK")
all4 = sum(1 for e in ORDER if ROWS[e]["passed"])
with open(os.path.join(OUT,"base_rate.tsv"),"w",encoding="utf-8") as f:
    f.write("batch\trows_checked\tring2_ok\tring3b_ok\tring4_ok\tall_four\trate\n")
    f.write("S13_B1\t%d\t%d\t%d\t%d\t%d\t%.4f\n" % (len(ORDER), r2ok, r3ok, r4ok, all4, all4/len(ORDER)))
print("STATS rows=%d r2=%d r3b=%d r4=%d all4=%d rate=%.4f" % (len(ORDER),r2ok,r3ok,r4ok,all4,all4/len(ORDER)))
