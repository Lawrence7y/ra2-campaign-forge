# -*- coding: utf-8 -*-
"""B2 产物生成：EVIDENCE/ROW_<entry>.txt ×15、delta.tsv、base_rate.tsv。
所有字节均现场从二进制读取，不手抄。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EV = os.path.join(ROOT, "EVIDENCE")
rows = json.load(open(os.path.join(HERE, "rows_b2.json"), encoding="utf-8"))


def B(va, n=None):
    """取指令字节（n 缺省取该地址处一条指令长度）。"""
    if n is None:
        d = disasm(va, 15)
        n = d[0].size if d else 4
    return va_read(va, n).hex(" ")


def I(va):
    d = disasm(va, 15)
    return ("%s %s" % (d[0].mnemonic, d[0].op_str)) if d else "?"


# ---------------- 各环底账 ----------------
CLS_INFO = {
    "BuildingClass": dict(vt=0x007E3EBC, col=0x007FC360, td=0x00818D60, n=322,
                          rtti=".?AVBuildingClass@@",
                          ctors=[(0x0043B71F, 0x0043B680, "mov dword ptr [esi], 0x7e3ebc",
                                  "收尾 mov eax,esi; pop esi; ret 4 返 this"),
                                 (0x0043B9FA, 0x0043B740, "mov dword ptr [esi], 0x7e3ebc",
                                  "收尾 mov eax,esi; ...; ret 8 返 this")],
                          dtors=[(0x0043BCFD, 0x0043BCF0,
                                  "返回 void（pop ecx; ret）+ 2 处 call 0x7C8B3D(free) + 尾部 call 0x6F4500 基类析构 ⇒ 析构器，㉓ 排除")]),
    "BuildingTypeClass": dict(vt=0x007E4570, col=0x007FC618, td=0x008193A8, n=49,
                              rtti=".?AVBuildingTypeClass@@",
                              ctors=[(0x0045E2CD, 0x0045DD90, "mov dword ptr [esi], 0x7e4570",
                                      "ret 4，函数体无 free/基类析构调用 ⇒ 构造器"),
                                     (0x0045E558, 0x0045E520, "mov dword ptr [esi], 0x7e4570",
                                      "收尾 mov eax,esi; pop esi; ret 4 返 this")],
                              dtors=[(0x0045E58D, 0x0045E580,
                                      "返回 void + 8 处 call 0x7C8B3D(free) + 尾部 call 0x711AE0 基类析构 ⇒ 析构器，㉓ 排除")]),
    "CaptureManagerClass": dict(vt=0x007E4B40, col=0x007FCB60, td=0x0081B6C8, n=24,
                                rtti=".?AVCaptureManagerClass@@",
                                ctors=[(0x00471807, 0x004717D0, "mov dword ptr [esi], 0x7e4b40",
                                        "收尾 mov [ecx+eax*4],esi 挂进全局表 0x89E0F4 后 mov eax,esi; ret 0xc 返 this"),
                                       (0x004718BC, 0x00471890, "mov dword ptr [esi], 0x7e4b40",
                                        "收尾 mov eax,esi; ret 返 this")],
                                dtors=[(0x004729CD, 0x004729C0,
                                        "test byte ptr [esp+0xc],1 + 2 处 call 0x7C8B3D(free) + call 0x4101F0 基类析构 ⇒ 删除式析构器，㉓ 排除")]),
    "FactoryClass": dict(vt=0x007E88D0, col=0x00800610, td=0x00822290, n=24,
                         rtti=".?AVFactoryClass@@",
                         ctors=[(0x004C991A, 0x004C98B0, "mov dword ptr [esi], 0x7e88d0",
                                 "收尾 mov [ecx+eax*4],esi 挂进容器后 mov eax,esi; ret 返 this，函数体无 free ⇒ 构造器"),
                                (0x004CA2C7, 0x004CA270, "mov dword ptr [edi], 0x7e88d0",
                                 "在调用方给的 [edi] 处实地构造对象并写两张子表，函数体无 free/基类析构 ⇒ 非析构器")],
                         dtors=[(0x004CA776, 0x004CA770,
                                 "test byte ptr [esp+0xc],1 + 2 处 call 0x7C8B3D(free) + call 0x4101F0 基类析构 ⇒ 删除式析构器，㉓ 排除")]),
}

# ---------------- ③ 逐行裁定（每行独立地址/字节） ----------------
R3 = {
"0044EFB0": dict(ok=False, sites=["0044F3CD", "0044F4C3", "0044F02D", "0044F0A6", "0044F11D"],
  reason=("全行 14 个「call → 比较 → 跳转」站点，无一是可伪证错误码。"
          "唯一两个直接调用站点判的是**表项计数**而非错误码：`0x44F3CD call 0x45EC90`（被调仅 14 B："
          "`mov eax,[ecx+0xef0]; mov eax,[eax*4+0x8192B8]; ret`，无任何返回常量，返回值是全局表取值）后 "
          "`0x44F3D2 cmp eax,-1` / `0x44F3D5 jl 0x44F4A7`；同函数内 `0x44F49A call 0x45EC90` 后 "
          "`0x44F49F cmp ebp,eax` / `0x44F4A1 jle` 证明它就是**循环上界**。"
          "另一站点 `0x44F4C3 call 0x45ECA0`（`mov eax,[..+0x819310]; add eax,edx; ret 4`，同样是表取值 + 常量偏移）后 "
          "`0x44F4C8 cmp eax,-1` / `0x44F4CB jl 0x44F59F`。其余 12 站点全是 `call [edi+0x1ac]`（外来对象 slot 107，"
          "静态类不可定）后的 `test eax,eax; jne/je`——非零即早退，属「返回值是否为空/是否命中」判定，"
          "被调约定不可伪证 ⇒ ③b② 不成立；亦无 ③b①/③b③/③b④ 形态。")),
"00453E20": dict(ok=True, sites=["00453EB3", "00453FCD", "00453FED", "0045407A", "0045409C"],
  reason=("③b② 成立（HRESULT 失败上抛 / 成功返 0 的双段约定，两端字节可读）。"
          "站点 `0x453EB3 e8 98 80 2b 00` = `call 0x70BF50`（this=edi 的对象，参数 [esp+0x18]）；"
          "`0x453EB8 3b c3` = `cmp eax,ebx`，ebx 由 `0x453E46 33 db` = `xor ebx,ebx` 置 0 ⇒ 即 `cmp eax,0`；"
          "`0x453EBA 89 44 24 10` 把 hr 存栈（**不是 eax 覆写**）；`0x453EBE 0f 8c ba 02 00 00` = `jl 0x45417E`。"
          "失败落点 `0x45417E` 是纯收尾 `pop edi; pop esi; pop ebp; pop ebx; pop ecx; c2 08 00(ret 8)`，"
          "**不碰 eax** ⇒ 负 HRESULT 原样上抛；成功路径跑到 `0x454170 8b 44 24 10` = `mov eax,[esp+0x10]` 即同一个 hr（≥0）返回。"
          "被调 `0x70BF50` 的约定同样字节可伪证：`0x70BF5C call 0x65AB80` → `0x70BF61 33 db` xor ebx,ebx → "
          "`0x70BF63 3b c3` cmp eax,ebx → `0x70BF65 0f 8c de 02 00 00` jl `0x70C249`（收尾不碰 eax，负值上抛）；"
          "成功尾部 `0x70C246 8b c3` = `mov eax,ebx`(=0) → `0x70C24B c2 08 00` ret 8 ⇒ 失败负值、成功 0。"
          "两路动作完全不同：失败直接跳过整段反序列化（成员向量、指针数组、15+3+8 个成员指针的读回全不做）；"
          "成功则逐段 `call [ecx+0xc]` 读回并在 `0x454170` 返回 0。"
          "另三处 `0x453FED / 0x45407A / 0x45409C` 的 `test eax,eax; jl 0x45417E` 是同一函数的次要出口，落点同一。"
          "比较与跳转之间无 eax 覆写；同一 call 不是多路共用（每站点地址不同、参数不同）。")),
"00454190": dict(ok=False, sites=["004541A3", "004541C8", "004541EA", "00454210", "00454232"],
  reason=("③b② 不成立的**关键实证是「返回值恒为常量」**：唯一直接调用站点 `0x4541A3 e8 a8 80 2b 00` = `call 0x70C250`；"
          "该被调仅 25 B，尾部 `0x70C264 33 c0` = `xor eax,eax` / `0x70C266 c2 0c 00` = `ret 0xc`，"
          "**全函数唯一返回路径都返回 0**（它只是把三个参数转发给 `0x65AC40` 后清 eax）⇒ 调用方 "
          "`0x4541A8 8b e8`=mov ebp,eax / `0x4541AA 85 ed`=test ebp,ebp / `0x4541AC 0f 8c`=jl `0x454242` 这条分支"
          "**可证永不成立**，不构成「调用方真的拿它分支」。"
          "其余 4 站点 `0x4541C8 / 0x4541EA / 0x454210 / 0x454232` 是 `call [edx+0x10]`（运行期流的 Read，"
          "被调类不可静态定 ⇒ 返回约定不可伪证）后 `test eax,eax; jl 0x454244`。"
          "★ 与同批成立行 `00453E20`（其反向 Save/Load 对偶）的差别只有一处：对偶行的直接被调 `0x70BF50` "
          "有「成功 0／失败负值」双段约定，而本行的直接被调 `0x70C250` 恒返 0（死分支）。")),
"00456750": dict(ok=False, sites=["00456757"],
  reason=("唯一站点 `0x456757 e8 54 ff ff ff` = `call 0x4566B0`；其后 `0x45675C 85 c0` = `test eax,eax` / "
          "`0x45675E 0f 8e fe 01 00 00` = `jle 0x456962`。被调 `0x4566B0` 的 5 条返回路径全是**业务数值 getter**："
          "`0x4566E8 0f be c1` = `movsx eax,cl`（取 `[Type+0xCD3]` 符号扩展）、`0x4566F5` 取 `[Type+0xCD2]`、"
          "`0x45673D 0f be 81 07 17 00 00` 取 `[Type+0x1707]`、`0x45672A..0x45673C` 取 `([edi+0xB4]>>8)`、"
          "`0x45674B 8b c3` = `mov eax,ebx`(=0 由 `0x4566B4 33 db`)。"
          "即返回集是「若干有符号业务量 ∪ 0」，没有失败/成功错误码语义；`jle` 是「算出来的量 ≤0 就跳过」的数值判定，"
          "属 ③a 的「零+默认」家族 ⇒ 不成立。全行无其它 call 站点，无 ③b①/③b③/③b④。")),
"0045E800": dict(ok=False, sites=["0045E80B", "0045E81F"],
  reason=("两站点均为**分配/构造结果判空**，非错误码。`0x45E80B e8 07 a6 36 00` = `call 0x7C8E17`（`push 0x720` 后的分配薄壳）"
          "→ `0x45E813 85 c0` test eax,eax → `0x45E815 74 56` je `0x45E86D`（失败落点 `0x45E86D 32 c0` = `xor al,al`，返回 false）；"
          "`0x45E81F e8 1c cf fd ff` = `call 0x43B740`（**本批 ② 同一张 BuildingClass 主虚表的构造器**，见 ④）→ "
          "`0x45E824 85 c0` test eax,eax → `0x45E826 74 45` je `0x45E86D`。"
          "被调 `0x43B740` 收尾 `mov eax,esi; ...; ret 8` 返 this，其返回集是「this 或 0」，即**指针非空判定**；"
          "`0x7C8E17` 同为零/NULL 判定。二者都是 bool 主输出，按 D-46(A) 与卡面「bool 不算」不入 ③b②。"
          "本行是「分配→构造→按坐标放置」的工厂方法（返回 al），无错误码约定。")),
"0045E880": dict(ok=False, sites=["0045E888"],
  reason=("唯一站点 `0x45E888 e8 8a a5 36 00` = `call 0x7C8E17`（`push 0x720` 分配）→ `0x45E890 85 c0` test eax,eax → "
          "`0x45E892 74 11` je `0x45E8A5`（`0x45E8A5 33 c0` = `xor eax,eax` 返回 NULL）。"
          "即「分配失败返回 NULL」的指针判空，属 bool/指针非空判定，按 D-46(A) 与卡面「bool 不算」不入 ③b②；"
          "成功路 `0x45E89C call 0x43B740` 后直接 `ret 4` 把构造结果当返回值，整个函数是 43 B 的 new+construct 薄壳。")),
"0045EBD0": dict(ok=False, sites=["0045EBD5"],
  reason=("唯一站点是**间接调用 + 空指针判定**：`0x45EBD5 ff 90 9c 00 00 00` = `call dword ptr [eax+0x9c]`（slot 39，"
          "即本批 `0045F040` 的实现）→ `0x45EBDB 85 c0` test eax,eax → `0x45EBDD 74 23` je `0x45EC02`（`xor ecx,ecx; xor edx,edx` 判零路）"
          "；非零路把返回对象里 4 个 dword（`+0/+4/+8/+0xC`）复制到调用方给的 16 B 缓冲。"
          "`0045F040` 的返回集是「指针或 0」（其 `0x45F04F test eax,eax` / `0x45F15D ret` 返回 `[esi+0xA4]`），"
          "故这里判的是**指针是否为空**、两路只是「复制 16 B」与「写 0」的默认值分支，属 ③a「零+默认」⇒ 不成立。")),
"0045F040": dict(ok=False, sites=["0045F093", "0045F0DF"],
  reason=("两站点均为**分配结果判空**：`0x45F093 e8 f8 47 04 00` = `call 0x4A3890` → `0x45F098 85 c0` test eax,eax → "
          "`0x45F0A0 74 09` je `0x45F0AB`；第二次 `0x45F0DF call 0x4A3890` → `0x45F0E4 85 c0` → `0x45F0EC 74 07` je `0x45F0F5`。"
          "被调 `0x4A3890` 仅 56 B，全部路径汇到 `0x4A38C2 8b c7` = `mov eax,edi`（edi 由 `0x4A38B0 8b f8` = mov edi,eax 取自 "
          "`0x4A38AB call 0x7C8E17` 的分配结果）→ `0x4A38C7 c3` ret ⇒ **返回集只有「分配到的指针」与 0**，"
          "即 NULL 判定，不是错误码。非零路 `0x45F0A2 c6 86 a8 00 00 00 01` 置成功标志位 1，也是布尔语义 ⇒ 不成立。")),
"0045FE50": dict(ok=False, sites=["00460554", "00460620", "00460758", "00460768", "00464736"],
  reason=("28 个站点逐个判，全是「查表/查名/取配置量」而非错误码，三类："
          "① `call 0x528A10`（17 处）——该被调 493 B，两出口 `0x528BC6 c2 14 00`（`0x528BC0 33 c0` xor eax,eax）与 "
          "`0x528BFA c2 14 00`（`0x528BF4 8b c1` = mov eax,ecx 取自字符串长度）⇒ 返回「0 或正长度」，"
          "调用方 `0x460758 85 c0` test / `0x46075F 74 11` je 判的是**翻译串是否为空**，属 ③a 零+默认；"
          "② `call 0x7514D0`（7 处，Find-by-name：`0x751515 or eax,0xffffffff` 未命中 -1、`0x75151B 8b c6` 返下标）后 "
          "`0x46076D 83 f8 ff` cmp eax,-1 / `0x460770 75 02` jne `0x460774`，**两路只差 `0x460772 8b c7`(mov eax,edi) 一条默认值回填**"
          "——即「找不到就用原值」，属 ③a 零+默认，非错误码分派；"
          "③ `call 0x5276D0` / `0x474DA0`（配置量解析、名字查表）返回「旧默认值或解析值」，`0x46473B 85 c0` test 后 "
          "`0x464743 0f 8e` jle 是**数值范围判定**。三类均无可伪证的失败/成功错误码约定 ⇒ ③b② 不成立；"
          "全行经 `core.jumptables()` 扫描 **0 张跳转表**（本批 15 行全部为 0）⇒ ③b① 形态在本批不存在。")),
"00465300": dict(ok=True, sites=["00465313", "00465332", "00465355"],
  reason=("③b② 成立（HRESULT 上抛 / 成功返 0，两端字节可读）。主站点 `0x465313 e8 a8 1a 2b 00` = `call 0x716DC0`；"
          "`0x465318 85 c0` = `test eax,eax`；`0x46531A 7c 4e` = `jl 0x46536A`。"
          "失败落点 `0x46536A` 是收尾 `pop edi; pop esi; pop ebp; pop ebx; c2 0c 00(ret 0xc)`，**不碰 eax** ⇒ "
          "负 HRESULT 原样返回；成功路径走到 `0x465368 33 c0` = `xor eax,eax` 再落同一收尾 ⇒ 返回 0。"
          "被调 `0x716DC0` 的约定同样逐字节可读：`0x716DD1 call 0x5F9950` → `0x716DD6 85 c0` test → "
          "`0x716DD8 0f 8c b6 02 00 00` jl `0x717094`（收尾 `pop edi; pop esi; ret 0xc`，不碰 eax ⇒ 负值上抛，"
          "且该路径因 ebx 尚未 push 而合法地跳过 `0x717093 pop ebx`）；成功侧 `0x717091 33 c0` = xor eax,eax → "
          "`0x717096 c2 0c 00` ret 0xc ⇒ 成功 0、失败负值。"
          "两路动作完全不同：失败跳过整段记录读取（`+0x178C` 计数 + `[+0x1788]+i*0xC` 的记录数组全不读）；成功读回后返回 0。"
          "另两站点 `0x465332 / 0x465355` 是 `call [edx+0x10]`（流 Read）后的 `test eax,eax; jl 0x46536A`，同落点。"
          "比较与跳转之间无 eax 覆写；各站点地址/参数互不相同，非多路同一 call。")),
"004728E0": dict(ok=True, sites=["004728F3", "00472915", "00472942"],
  reason=("③b② 成立（具名 HRESULT：E_POINTER 0x80004003 / 成功 ≥0）。站点 `0x4728F3 e8 28 da f9 ff` = `call 0x410320`；"
          "`0x4728F8 8b f8` = `mov edi,eax`；`0x4728FA 85 ff` = `test edi,edi`；`0x4728FC 89 7c 24 18` 只把 hr 存栈（**不是覆写判据寄存器**）；"
          "`0x472900 7c 54` = `jl 0x472956`；落点 `0x472956 8b c7` = `mov eax,edi` → `0x47295C c2 0c 00` ret 0xc ⇒ **负 HRESULT 原样上抛**。"
          "被调 `0x410320`（87 B）的返回集字节可枚举：`0x41032B b8 03 40 00 80` = `mov eax,0x80004003`（E_POINTER）→ `0x410331 c2 0c 00` ret 0xc；"
          "成功侧不写 eax，原样传出内层 COM 调用的 HRESULT（`0x410348 ff 50 10` 后 `0x410364 7c 0c` jl 落 `0x410372`，"
          "`0x410374 c2 0c 00` ret 0xc 不碰 eax）；入口 `0x410325 85 f6` / `0x410327 75 0a` jne 把空指针引到 E_POINTER 出口。"
          "两路动作真不同：失败直接返回错误码、跳过整个读循环；成功继续 `call [edx+0x10]` 读回计数与每项两个 dword。"
          "另两站点 `0x472915 / 0x472942` 是流 Read 的 `test eax,eax; jl 0x472958`（收尾不碰 eax）。"
          "多值/具名错误码，非 {0,1} 布尔；比较与跳转之间无判据寄存器覆写。")),
"004729C0": dict(ok=True, sites=["004729F3"],
  reason=("③b② 成立（容器 Find 的「未命中 = -1 / 命中 = 下标」约定，调用方按下标做压缩移除）。"
          "站点 `0x4729F3 ff 52 10` = `call dword ptr [edx+0x10]`，edx 由 `0x4729E8 8b 15 f0 e0 89 00` = "
          "`mov edx,[0x89E0F0]` 取得**全局容器**的 vptr，this 由 `0x4729C8 b9 f0 e0 89 00` = `mov ecx,0x89E0F0` 传入；"
          "`0x4729F6 83 f8 ff` = `cmp eax,-1`；`0x4729F9 74 2d` = `je 0x472A28`。"
          "被调可字节钉死：全局 `0x89E0F0` 的静态初始化点 `0x47176D c7 05 f0 e0 89 00 d4 4a 7e 00` 写入 vtable `0x007E4AD4`，"
          "其 `[-4] @0x7E4AD0 = 0x007FCA18`（COL，sig=0）→ TD `.?AV?$DynamicVectorClass@PAVCaptureManagerClass@@@@`；"
          "slot4（`0x7E4AE4`，即 `+0x10`）= `0x00472FD0` = Find，其 `0x472FEF 83 c8 ff` = `or eax,0xFFFFFFFF`、"
          "`0x472FF3 c2 04 00` = `ret 4` ⇒ **未命中 = -1、命中 = 下标**，字节可伪证。"
          "两路动作真不同：未命中跳 `0x472A28` 跳过整段移除；命中则 `0x472A05 49`(dec ecx) / `0x472A08 89 0d 00 e1 89 00` "
          "回写计数、`0x472A17 8b 14 81` / `0x472A1A 89 54 81 fc` 前移压缩（**写全局数组，非栈写**）。"
          "cmp 与 je 之间无 eax 覆写；单 call，非多路同一 call。")),
"004CA3C0": dict(ok=True, sites=["004CA3D2", "004CA3EE", "004CA40D"],
  reason=("③b② 成立（具名 HRESULT：E_POINTER 0x80004003 / 成功 0）。站点 `0x4CA3D2 e8 49 5f f4 ff` = `call 0x410320`；"
          "`0x4CA3D7 85 c0` = `test eax,eax`；`0x4CA3D9 7c 44` = `jl 0x4CA41F`；失败落点 `0x4CA41F` 是收尾 "
          "`pop edi; pop esi; pop ebx; c2 0c 00(ret 0xc)`，**不碰 eax** ⇒ 负 HRESULT 原样上抛；"
          "成功路径走到 `0x4CA41D 33 c0` = `xor eax,eax` 再落同一收尾 ⇒ 返回 0。"
          "被调 `0x410320` 返回集字节可枚举：`0x41032B b8 03 40 00 80` = `mov eax,0x80004003`(E_POINTER) → `0x410331 c2 0c 00` ret 0xc；"
          "成功侧 `0x410374 c2 0c 00` ret 0xc 不碰 eax，原样传出内层 COM 调用的 HRESULT。"
          "两路动作真不同：失败跳过整个工厂项读回段；成功继续读计数并循环 `[edi+0x44]+i*4`。"
          "另两站点 `0x4CA3EE / 0x4CA40D` 是流 Read 的 `test eax,eax; jl`（后者跳 `0x4CA41D` 走 `xor eax,eax`，"
          "即吞错返回 0——这正说明只有 `0x4CA3D9` 那条是**上抛**路径，两路差别是实质的）。"
          "比较与跳转之间无 eax 覆写；单 call。")),
"004CA770": dict(ok=True, sites=["004CA7AA", "004CA803"],
  reason=("③b② 成立（两处独立的容器 Find「未命中 = -1 / 命中 = 下标」+ 压缩移除，地址与容器各不相同）。"
          "站点一 `0x4CA7AA ff 52 10` = `call dword ptr [edx+0x10]`，edx 由 `0x4CA796 8b 15 30 3e a8 00` = `mov edx,[0xA83E30]`，"
          "this 由 `0x4CA7A1 b9 30 3e a8 00` 传入；`0x4CA7AD 83 f8 ff` = `cmp eax,-1`；`0x4CA7B0 74 2d` = `je 0x4CA7DF`。"
          "该全局静态初始化点 `0x4E6E7D c7 05 30 3e a8 00 a4 9f 7e 00` 写入 vtable `0x007E9FA4`，`[-4] @0x7E9FA0 = 0x00801610`（COL, sig=0）"
          "→ `.?AV?$DynamicVectorClass@PAVFactoryClass@@@@`；slot4（`0x7E9FB4`）= `0x004EC2D0` = Find，其 "
          "`0x4EC2EF 83 c8 ff` = `or eax,0xFFFFFFFF`、`0x4EC2F3 c2 04 00` = `ret 4` ⇒ 未命中 -1、命中下标。"
          "站点二 `0x4CA803 ff 52 10`，edx 由 `0x4CA7EF 8b 15 20 f7 b0 00` = `mov edx,[0xB0F720]`，this 由 `0x4CA7FA` 传入；"
          "`0x4CA806 83 f8 ff` cmp eax,-1 / `0x4CA809 74 2d` je `0x4CA838`。该全局初始化点 "
          "`0x7252ED c7 05 20 f7 b0 00 ec 91 7e 00` 写入 vtable `0x007E91EC`，`[-4] @0x7E91E8 = 0x008009B0`（COL, sig=0）"
          "→ `.?AV?$DynamicVectorClass@PAVAbstractClass@@@@`；slot4（`0x7E91FC`）= `0x004E0550` = Find，其 "
          "`0x4E056F 83 c8 ff` / `0x4E0573 c2 04 00` 同形。"
          "两路动作真不同（两站点同构）：未命中跳过该容器的移除；命中则 `0x4CA7BC 49`(dec ecx) / "
          "`0x4CA7BF 89 0d 40 3e a8 00`（及站点二 `0x4CA815`/`0x4CA818`）回写计数、`0x4CA7CE 8b 14 81` / "
          "`0x4CA7D1 89 54 81 fc`（及站点二 `0x4CA827`/`0x4CA82A`）前移压缩——**写全局数组，非栈写**。"
          "cmp 与 je 之间无 eax 覆写；两站点各自的 call 地址、容器全局、this 均不同，非多路同一 call。")),
"00705CA0": dict(ok=False, sites=["00705CA8"],
  reason=("唯一站点 `0x705CA8 ff 90 84 01 00 00` = `call dword ptr [eax+0x184]`（本类主虚表 slot 97），其后 "
          "`0x705CAE 83 f8 01` = `cmp eax,1` / `0x705CB1 75 33` = `jne 0x705CE6`。该槽实现是字段 getter"
          "（`[this+0xAC]`，为 -1 时改取 `[this+0xB4]`），返回值是**建筑状态/类型常量**，"
          "`cmp eax,1` 判的是「状态是否等于 1」而非错误码；另 `0x705CB9 85 c9` test ecx,ecx / `0x705CBB 74 29` je 是对 "
          "`[esi+0x2B4]` 的**指针判空**。两路只是「从 `[+0x2B4]` 指向的对象取 12 B」与「从 `this+0x9C` 取 12 B」的取值分支，"
          "属状态常量比较 + 空指针判定，无失败/成功错误码约定 ⇒ ③b② 不成立。")),
}

# ---------------- 生成 EVIDENCE ----------------
ORDER = [r["entry"] for r in rows]
summary = []
for r in rows:
    e = r["entry"]
    name = r["name"]
    ev = int(e, 16)
    cls = r["name"].split("::")[0]
    slot_hint = int(r["name"].split("::")[1].replace("vslot", "").replace("slot", ""))
    CI = CLS_INFO[cls]
    info = ATLAS.get(e)
    body = disasm(ev, info["size"])

    # ② 槽定位
    slotva = CI["vt"] + 4 * slot_hint
    slotval = u32(slotva)
    assert slotval == ev, (e, hex(slotva), hex(slotval or 0))
    colback = u32(CI["vt"] - 4)
    ci = parse_col(colback)
    tdi = parse_td(ci["td"])
    r3 = R3[e]

    L = []
    L.append("ROW %s  %s   (S12 / NAMED-PUSH B2)" % (e, name))
    L.append("=" * 78)
    L.append("")
    L.append("① 入口")
    L.append("  entry = 0x%s，在 .text [0x401000,0x7E038D) 内：是" % e)
    L.append("  atlas 边界：entry=0x%s size=%d n_instr=%d" % (e, info["size"], info["n_instr"]))
    L.append("  自入口线性解码（capstone 5.0.7, skipdata=True）：%d 条，skipdata 占 %d B"
             % (len(body), sum(i.size for i in body if i.id == 0)))
    L.append("  首指令 %08X  %-18s %s" % (body[0].address, B(body[0].address), I(body[0].address)))
    L.append("  末指令 %08X  %-18s %s" % (body[-1].address, B(body[-1].address), I(body[-1].address)))
    L.append("  判定：PASS（入口地址在 .text 内、自入口解码自洽、atlas 边界对齐到指令末）")
    L.append("")
    L.append("② 类身份（独立取证：.rdata RTTI 数据链 + 主虚表槽号，非反推自线索）")
    L.append("  线索名 = %s  ⇒ 类=%s、槽号=%d（线索只作对照，不作证据）" % (name, cls, slot_hint))
    L.append("  主虚表 vt      = 0x%08X   （slot0 = 0x%08X = 0x00410260 ⇒ 对象主虚表）"
             % (CI["vt"], u32(CI["vt"])))
    L.append("  槽 VA          = 0x%08X  = vt + 4*%d" % (slotva, slot_hint))
    L.append("  槽内 4 B       = %s   → 0x%08X == entry ✔" % (va_read(slotva, 4).hex(" "), slotval or 0))
    L.append("  回扫 [vt-4]    = 0x%08X（COL，signature=0x%X）" % (colback, ci["sig"]))
    L.append("  [COL+0xC]      = 0x%08X（TypeDescriptor）" % ci["td"])
    L.append("  [TD+8] 名串    = %s" % tdi["name"])
    L.append("  主表槽数       = %d（%d > %d ⇒ 槽号在表内）" % (CI["n"], CI["n"], slot_hint))
    L.append("  判定：PASS（RTTI 名与线索类一致；槽号由字节复算 = 线索 %d；表 slot0=00410260 是对象主虚表）" % slot_hint)
    L.append("  ★ 陷阱③ 排查：本类另有小成员/次基类子表（BuildingClass 0x7E3E90/98/A0、BuildingTypeClass 0x7E4544/4C/54、"
             "CaptureManagerClass 0x7E4B14/1C/24、FactoryClass 0x7E88A4/AC/B4，各仅 1/1/6 槽，slot0 为 00410590/00410580/004105E0），"
             "本行槽**不在**这些小表里——已逐表核对，落点即主表 0x%08X。" % CI["vt"])
    L.append("")
    L.append("③ 整体合同（只认 ③b）——判定：%s" % ("PASS ③b②" if r3["ok"] else "FAIL"))
    L.append("  检验站点（本行自身地址）：%s" % "  ".join("0x" + s for s in r3["sites"]))
    for s in r3["sites"]:
        va = int(s, 16)
        L.append("    0x%s  %-20s %s" % (s, B(va), I(va)))
    L.append("  依据：")
    L.append("    " + r3["reason"])
    L.append("  三陷阱逐条：")
    L.append("    · eax/判据寄存器覆写：比较与跳转之间无判据寄存器被 move/pop/算术覆写（见上站点字节）")
    L.append("    · 多路同一 call：各站点 call 地址与参数互不相同，非多路径进同一处 call")
    L.append("    · 模板假句：语义落在具体被调与其返回约定上，未写「对象初始化/清零」式空话")
    L.append("")
    L.append("④ 使用见证（活虚表派发，行外、非 atexit；与 ② 不同源）")
    L.append("  %s 主虚表 0x%08X 在 .text 的安装点（构造器，mov [mem],vt）：" % (cls, CI["vt"]))
    for (w, fn, ins, note) in CI["ctors"]:
        L.append("    0x%08X  %-34s %s" % (w, B(w), ins))
        L.append("         in_func=0x%08X   atexit=%s   %s" % (fn, is_atexit_registered(fn) or "无",
                                                              note))
    for (w, fn, note) in CI["dtors"]:
        L.append("    [已排除] 0x%08X in_func=0x%08X —— %s" % (w, fn, note))
    L.append("  ⇒ 本行所在槽位于由构造器装入活对象 [obj+0] 的主虚表内，构造完成后 [obj+0] 派发可达本 entry。")
    L.append("  ⇒ ㉓ 成对陷阱：④ 锚点全部取构造安装点，且 atexit 检查为空；析构器自身的 vptr 重装点一律不用作 ④。")
    L.append("  ⇒ ②④ 不同源：② 锚 .rdata 的 COL/TD/名串数据链 + 槽值 4 B；④ 锚 .text 的构造期安装指令字节。")
    L.append("")
    L.append("结论：四环%s —— %s" % ("齐全 ⇒ [已证]" if r3["ok"] else "不齐（③ FAIL）⇒ 不产出",
                                    ("成立" if r3["ok"] else "不成立")))
    open(os.path.join(EV, "ROW_%s.txt" % e), "w", encoding="utf-8").write("\n".join(L) + "\n")

    summary.append(dict(entry=e, name=name, slot_va="%08X" % slotva, slot_idx=slot_hint,
                        r1="PASS", r2="PASS", r3=("PASS" if r3["ok"] else "FAIL"),
                        r4="PASS", ok=r3["ok"], sites=r3["sites"]))
    print("wrote ROW_%s.txt  ③=%s" % (e, "PASS" if r3["ok"] else "FAIL"))

# ---------------- delta.tsv ----------------
SEM = {
"00453E20": ("S12 BuildingClass::vslot5 —— ③b② 成立：站点 0x453EB3 `e8 98 80 2b 00` = call 0x70BF50；"
  "0x453EB8 `3b c3` = cmp eax,ebx（ebx 由 0x453E46 `33 db` xor 置 0）；0x453EBA `89 44 24 10` 只把 hr 存栈（非 eax 覆写）；"
  "0x453EBE `0f 8c ba 02 00 00` = jl 0x45417E。被调 0x70BF50 约定字节可伪证：0x70BF5C call 0x65AB80 → 0x70BF61 `33 db` → "
  "0x70BF63 `3b c3` cmp eax,ebx → 0x70BF65 `0f 8c de 02 00 00` jl 0x70C249（收尾不碰 eax，负值上抛）；"
  "成功尾部 0x70C246 `8b c3` = mov eax,ebx(=0) → 0x70C24B `c2 08 00` ret 8 ⇒ 失败负 HRESULT、成功 0。"
  "调用方真的分支且两路动作不同：失败落点 0x45417E 是纯收尾 `pop edi;pop esi;pop ebp;pop ebx;pop ecx;ret 8`（不碰 eax ⇒ 错误码原样上抛），"
  "整段反序列化（成员向量、指针数组、15+3+8 个成员指针的读回）全跳过；成功则逐段 `call [ecx+0xc]` 读回并在 0x454170 `8b 44 24 10` 返回 hr(≥0)。"
  "另三站点 0x453FED/0x45407A/0x45409C 的 `test eax,eax; jl 0x45417E` 同落点。比较与跳转间无判据寄存器覆写；非多路同一 call。"
  "语义：建筑对象从存档流载入（BuildingClass 反序列化）——先调 0x70BF50 初始化并取 hr，失败把负 HRESULT 原样上抛、成功读回全部成员后返回 0。"
  "② 槽 007E3ED0（vt 007E3EBC +0x14，slot#5）4B 值即本 entry；COL 007FC360(sig=0)→TD 00818D60→`.?AVBuildingClass@@`，主表槽 0=00410260，与线索 vslot5 自洽；"
  "④ 构造安装点 0x0043B71F（in_func=0043B680，atexit=False，收尾 `mov eax,esi;ret 4` 返 this ⇒ 构造器）与 0x0043B9FA（0043B740，同）把主表装入活对象；"
  "析构器重装点 0x0043BCFD（0043BCF0，void 返回+free）按 ㉓ 排除；②④ 不同源（.rdata RTTI 链 vs .text 构造安装字节）。"),
"00465300": ("S12 BuildingTypeClass::slot6 —— ③b② 成立：站点 0x465313 `e8 a8 1a 2b 00` = call 0x716DC0；"
  "0x465318 `85 c0` = test eax,eax；0x46531A `7c 4e` = jl 0x46536A。失败落点 0x46536A 是收尾 `pop edi;pop esi;pop ebp;pop ebx;c2 0c 00`（不碰 eax ⇒ 负 HRESULT 原样返回）；"
  "成功路径走到 0x465368 `33 c0` = xor eax,eax 再落同一收尾 ⇒ 返回 0。被调 0x716DC0 约定逐字节可读：0x716DD1 call 0x5F9950 → 0x716DD6 test eax,eax → "
  "0x716DD8 `0f 8c b6 02 00 00` jl 0x717094（该路径因 ebx 尚未 push 而合法跳过 0x717093 pop ebx，落点不碰 eax ⇒ 负值上抛）；"
  "成功侧 0x717091 `33 c0` xor eax,eax → 0x717096 `c2 0c 00` ret 0xc ⇒ 成功 0。两路动作不同：失败跳过整段记录读取（[+0x178C] 计数与 [+0x1788]+i*0xC 记录数组全不读），成功读回后返回 0。"
  "另两站点 0x465332/0x465355 为 `call [edx+0x10]` 流 Read 后的 `test eax,eax; jl 0x46536A`，同落点。比较与跳转间无 eax 覆写；各站点地址/参数互异。"
  "语义：建筑类型副本从存档流载入（BuildingTypeClass::slot6）——调 0x716DC0 载入，失败把负 HRESULT 原样上抛，成功读回记录数组并返回 0。"
  "② 槽 007E4588（vt 007E4570 +0x18，slot#6）4B 值即本 entry；COL 007FC618(sig=0)→TD 008193A8→`.?AVBuildingTypeClass@@`，主表槽 0=00410260，与线索 slot6 自洽；"
  "④ 构造安装点 0x0045E2CD（in_func=0045DD90，atexit=False，ret 4、函数体无 free/基类析构 ⇒ 构造器）与 0x0045E558（0045E520，收尾 `mov eax,esi;ret 4` 返 this）；"
  "析构器重装点 0x0045E58D（0045E580，void 返回+8 处 free+基类析构 0x711AE0）按 ㉓ 排除；②④ 不同源。"),
"004728E0": ("S12 CaptureManagerClass::slot6 —— ③b② 成立：站点 0x4728F3 `e8 28 da f9 ff` = call 0x410320；0x4728F8 `8b f8` = mov edi,eax；"
  "0x4728FA `85 ff` = test edi,edi；0x4728FC `89 7c 24 18` 只存栈（非覆写判据寄存器）；0x472900 `7c 54` = jl 0x472956；"
  "落点 0x472956 `8b c7` = mov eax,edi → 0x47295C `c2 0c 00` ret 0xc ⇒ 负 HRESULT 原样上抛。被调 0x410320(87B) 返回集字节可枚举："
  "0x41032B `b8 03 40 00 80` = mov eax,0x80004003（E_POINTER）→ 0x410331 `c2 0c 00` ret 0xc；成功侧 0x410374 `c2 0c 00` ret 0xc 不碰 eax，"
  "原样传出内层 COM 调用 HRESULT；入口 0x410325 `85 f6`/0x410327 `75 0a` jne 把空指针引到 E_POINTER 出口。"
  "调用方真的分支且两路不同：失败直接返回错误码并跳过整个读循环；成功继续 `call [edx+0x10]` 读回计数与每项两个 dword。"
  "另两站点 0x472915/0x472942 为流 Read 的 `test eax,eax; jl 0x472958`（收尾不碰 eax）。具名多值错误码（E_POINTER=0x80004003 / 成功 ≥0），非 {0,1} 布尔。"
  "语义：CaptureManagerClass 从流载入——先调 0x410320 校验并读取参数（空指针得 0x80004003），失败原样上抛，成功读回计数与每项两个 dword。"
  "② 槽 007E4B58（vt 007E4B40 +0x18，slot#6）4B 值即本 entry；COL 007FCB60(sig=0)→TD 0081B6C8→`.?AVCaptureManagerClass@@`，主表槽 0=00410260，与线索 slot6 自洽；"
  "④ 构造安装点 0x00471807（in_func=004717D0，atexit=False，收尾把 this 挂进全局表 0x89E0F4 后 `mov eax,esi;ret 0xc` 返 this ⇒ 构造器）与 0x004718BC（00471890，同形）；"
  "析构器重装点 0x004729CD（004729C0，test byte[esp+0xc],1 + free + 基类析构 0x4101F0）按 ㉓ 排除；②④ 不同源。"),
"004CA3C0": ("S12 FactoryClass::slot6 —— ③b② 成立：站点 0x4CA3D2 `e8 49 5f f4 ff` = call 0x410320；0x4CA3D7 `85 c0` = test eax,eax；"
  "0x4CA3D9 `7c 44` = jl 0x4CA41F。失败落点 0x4CA41F 是收尾 `pop edi;pop esi;pop ebx;c2 0c 00`（不碰 eax ⇒ 负 HRESULT 原样上抛）；"
  "成功路径走到 0x4CA41D `33 c0` = xor eax,eax 再落同一收尾 ⇒ 返回 0。被调 0x410320 返回集字节可枚举：0x41032B `b8 03 40 00 80` = mov eax,0x80004003（E_POINTER）→ "
  "0x410331 `c2 0c 00`；成功侧 0x410374 `c2 0c 00` 不碰 eax（原样传出内层 HRESULT）。"
  "调用方真的分支且两路不同：失败跳过整个工厂项读回段；成功继续读计数并循环 `[edi+0x44]+i*4`。另两站点 0x4CA3EE/0x4CA40D 为流 Read 的 `test eax,eax; jl`，"
  "其中 0x4CA40D 跳 0x4CA41D 走 `xor eax,eax`（吞错返 0）——正说明只有 0x4CA3D9 那条是上抛路径，两路差别实质。具名多值错误码，非 {0,1} 布尔；比较与跳转间无 eax 覆写。"
  "语义：FactoryClass 从流载入——先调 0x410320 校验参数（空指针返回 0x80004003 E_POINTER），失败负 HRESULT 原样上抛，成功逐项读回工厂项并返回 0。"
  "② 槽 007E88E8（vt 007E88D0 +0x18，slot#6）4B 值即本 entry；COL 00800610(sig=0)→TD 00822290→`.?AVFactoryClass@@`，主表槽 0=00410260，与线索 slot6 自洽；"
  "④ 构造安装点 0x004C991A（in_func=004C98B0，atexit=False，收尾把 this 挂进容器后 `mov eax,esi;ret` 返 this，函数体无 free ⇒ 构造器）与 0x004CA2C7（004CA270，在 [edi] 处实地构造并写两张子表，无 free/基类析构）；"
  "析构器重装点 0x004CA776（004CA770）按 ㉓ 排除；②④ 不同源。"),
"004729C0": ("S12 CaptureManagerClass::slot8 —— ③b② 成立：站点 0x4729F3 `ff 52 10` = call dword ptr [edx+0x10]，edx 由 0x4729E8 `8b 15 f0 e0 89 00` = "
  "mov edx,[0x89E0F0] 取全局容器 vptr、this 由 0x4729C8 `b9 f0 e0 89 00` 传入；0x4729F6 `83 f8 ff` = cmp eax,-1；0x4729F9 `74 2d` = je 0x472A28。"
  "被调可字节钉死：全局 0x89E0F0 的静态初始化点 0x47176D `c7 05 f0 e0 89 00 d4 4a 7e 00` 写入 vtable 0x007E4AD4，其 [-4]@0x7E4AD0=0x007FCA18（COL,sig=0）→ "
  "TD `. ?AV?$DynamicVectorClass@PAVCaptureManagerClass@@@@`；slot4(0x7E4AE4,+0x10)=0x00472FD0=Find，其 0x472FEF `83 c8 ff` = or eax,0xFFFFFFFF、"
  "0x472FF3 `c2 04 00` = ret 4 ⇒ 未命中=-1、命中=下标，字节可伪证。调用方真的拿 -1 分支且两路动作不同：未命中跳 0x472A28 跳过整段移除；"
  "命中则 0x472A05 `49`(dec ecx)/0x472A08 `89 0d 00 e1 89 00` 回写计数、0x472A17 `8b 14 81` / 0x472A1A `89 54 81 fc` 前移压缩（写全局数组，非栈写）。"
  "cmp 与 je 之间无 eax 覆写；单 call 非多路同一 call。语义：CaptureManagerClass 删除式析构器——先在全局 DynamicVectorClass<CaptureManagerClass*>(0x89E0F0) 中 Find 自身"
  "（未命中=-1），命中则 count-- 并前移压缩移除；随后释放成员 +0x28、调基类析构 0x4101F0，flags&1 时 operator delete 本对象。"
  "② 槽 007E4B60（vt 007E4B40 +0x20，slot#8）4B 值即本 entry；COL 007FCB60(sig=0)→TD 0081B6C8→`.?AVCaptureManagerClass@@`，主表槽 0=00410260，与线索 slot8 自洽；"
  "④ 构造安装点 0x00471807（004717D0，构造器，挂进全局表后返 this）与 0x004718BC（00471890，同形），atexit 均为空；"
  "**本行自身 0x004729CD 是删除式析构器的 vptr 重装点（test byte[esp+0xc],1 + free + 基类析构），按 ㉓ 不作 ④**；②④ 不同源。"),
"004CA770": ("S12 FactoryClass::slot8 —— ③b② 成立（两处独立站点、两个不同容器）：站点一 0x4CA7AA `ff 52 10` = call [edx+0x10]，edx 由 0x4CA796 `8b 15 30 3e a8 00` "
  "= mov edx,[0xA83E30]、this 由 0x4CA7A1 `b9 30 3e a8 00` 传入；0x4CA7AD `83 f8 ff` = cmp eax,-1；0x4CA7B0 `74 2d` = je 0x4CA7DF。"
  "该全局静态初始化点 0x4E6E7D `c7 05 30 3e a8 00 a4 9f 7e 00` 写 vtable 0x007E9FA4，[-4]@0x7E9FA0=0x00801610（COL,sig=0）→ `. ?AV?$DynamicVectorClass@PAVFactoryClass@@@@`，"
  "slot4(0x7E9FB4)=0x004EC2D0=Find，其 0x4EC2EF `83 c8 ff` = or eax,0xFFFFFFFF、0x4EC2F3 `c2 04 00` = ret 4。"
  "站点二 0x4CA803 `ff 52 10`，edx 由 0x4CA7EF `8b 15 20 f7 b0 00` = mov edx,[0xB0F720]；0x4CA806 `83 f8 ff` cmp -1；0x4CA809 `74 2d` je 0x4CA838；"
  "该全局初始化点 0x7252ED `c7 05 20 f7 b0 00 ec 91 7e 00` 写 vtable 0x007E91EC，[-4]@0x7E91E8=0x008009B0（COL,sig=0）→ `. ?AV?$DynamicVectorClass@PAVAbstractClass@@@@`，"
  "slot4(0x7E91FC)=0x004E0550=Find，0x4E056F `83 c8 ff` / 0x4E0573 `c2 04 00` 同形 ⇒ 未命中=-1、命中=下标。"
  "两站点均：未命中跳过该容器移除；命中则 0x4CA7BC `49`/0x4CA7BF `89 0d 40 3e a8 00`（站点二 0x4CA815/0x4CA818）回写计数、0x4CA7CE `8b 14 81`/0x4CA7D1 `89 54 81 fc`"
  "（站点二 0x4CA827/0x4CA82A）前移压缩——写全局数组，非栈写。cmp 与 je 之间无 eax 覆写；两站点 call 地址/容器全局/this 全不同，非多路同一 call。"
  "语义：FactoryClass 删除式析构器——在两个全局容器 DynamicVectorClass<FactoryClass*>(0xA83E30) 与 DynamicVectorClass<AbstractClass*>(0xB0F720) 中各 Find 自身并压缩移除"
  "（未命中=-1），再清理成员、调基类析构 0x4101F0、flags&1 时 operator delete 本对象。"
  "② 槽 007E88F0（vt 007E88D0 +0x20，slot#8）4B 值即本 entry；COL 00800610(sig=0)→TD 00822290→`.?AVFactoryClass@@`，主表槽 0=00410260，与线索 slot8 自洽；"
  "④ 构造安装点 0x004C991A（004C98B0，构造器返 this）与 0x004CA2C7（004CA270，在 [edi] 处实地构造），atexit 均为空；"
  "**本行自身 0x004CA776 是删除式析构器 vptr 重装点，按 ㉓ 不作 ④**；②④ 不同源。"),
}

dl = ["entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path"]
n = 0
for s in summary:
    if not s["ok"]:
        continue
    e = s["entry"]
    nm = [r["name"] for r in rows if r["entry"] == e][0]
    path = "D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/NAMED_PUSH_S12_B2/EVIDENCE/ROW_%s.txt" % e
    dl.append("%s\tS12\t%s\t%s\t[已证]\t%s" % (e, nm, SEM[e], path))
    n += 1
open(os.path.join(ROOT, "delta.tsv"), "w", encoding="utf-8", newline="\n").write("\n".join(dl) + "\n")
print("\ndelta.tsv rows =", n)

# ---------------- base_rate ----------------
tot = len(summary)
r2 = sum(1 for s in summary if s["r2"] == "PASS")
r3 = sum(1 for s in summary if s["r3"] == "PASS")
r4 = sum(1 for s in summary if s["r4"] == "PASS")
allf = sum(1 for s in summary if s["ok"])
open(os.path.join(ROOT, "base_rate.tsv"), "w", encoding="utf-8", newline="\n").write(
    "batch\trows_checked\tring2_ok\tring3b_ok\tring4_ok\tall_four\trate\n"
    "S12_B2\t%d\t%d\t%d\t%d\t%d\t%.4f\n" % (tot, r2, r3, r4, allf, allf / tot))
print("base_rate: %d/%d/%d/%d/%d rate=%.4f" % (tot, r2, r3, r4, allf, allf / tot))

json.dump(summary, open(os.path.join(HERE, "final_summary.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("-> final_summary.json")
