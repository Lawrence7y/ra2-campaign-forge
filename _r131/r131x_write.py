#!/usr/bin/env python3
# R131 r131x: append the four-part record. All four targets are LF-only where required.
# Discipline: read the authoritatve bytes into memory FIRST, write, read back, assert
# CR/byte deltas, and recover ONLY from the in-memory copy if anything fails (S-203).
import hashlib
import io
import json
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
COMMON = os.path.join(R14, 'R14_COMMON.md')
LEDGER = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BOARD = os.path.join(R14, 'STATUS_BOARD.md')
OUT = '/home/t628/projects/ra2-campaign-forge/_r131/r131x_write.json'

COMMON_TEXT = """## 2.135

R131 把 R129/R130 给 0x6bedb0 起的名字改掉了，并且用字节证明改得对。另外把门禁里一处「静默的空转」变成可失败的钉。

一、改名：0x6bedb0 不是类工厂包装器，是**被 IID 参数化的 COM 实例化助手**。它的 106 字节里没有 IClassFactory、没有 DllGetClassObject，全库也没有这两个名字指向它的任何引用。它的三条栈参数是 rclsid、pUnkOuter 与 ppv 合用的那个槽、dwClsContext（ret 0xc 给边界）。这一点不是读调用点读出来的，是把 [esp+N] 全部按 CFG 解到函数入口 esp 上算出来的：九条 [esp+N] 读全部落在三个参数槽里，一条不落。栈模型由两条独立推导互证——把每个 call 当 cdecl 时模型在恰好两个合并点自相矛盾（0x6bedbd 到 0x6bedc0、0x6bee07 到 0x6bee09），而按调用前 push 条数给 4*nargs 时全模型一致。两条推导给出的结论相同，不是一条推导换两种说法。

二、模板：全库存在**两个**这样的实例，0x6bedb0 与 0x41c250。两者 106 字节里只有偏移 0x4e 一个字节不同（c0 对 b0），差异是它们推给 QueryInterface 的 IID：前者推 IID_IUnknown {00000000-0000-0000-C000-000000000046}，后者推 {070F3290-9841-11D1-B709-00A024DDAFD1}。所以这是同一个模板的两次实例化，实例参数就是「创建之后再 QI 一次要什么接口」。R130 说「0x6bedb0 全库只有 2 个调用点」在字面上对（该实例确实只有 2 个调用点），但**不是**「这个包装器只被用两次」：另一个实例被 13 处调用，两个实例合计 15 个调用点。R130 的措辞需要按这一条订正。

三、0x6bc34d 那个循环不是类工厂注册循环，是**惰性自注册 COM 服务器的加载器**。字节顺序是：先 push 7 / push 0 / push [esi] 调 0x6bedb0 试创建；失败则 mov eax,[esi+4] 交给 LoadLibraryA（0x7e1220）；再 push 0x840de4（该地址的字符串实测就是 DllRegisterServer，全库恰 1 处引用）交给 GetProcAddress（0x7e1250）；call eax 调它；然后用同一组实参重试 0x6bedb0；最后 FreeLibrary（0x7e1224）把句柄放掉。表 0x7f3710 每项 8 字节 = (rclsid 指针, dll 名字指针)，恰 1 项 {0x7e9500, blowfish.dll}。

四、R130 的未取得项「为什么类工厂表只有 1 项」在这一条下**消失**，不是被回答：它根本不是类工厂表，是「本构建自带哪些需要自带注册的 DLL 宿主 COM 服务器」的清单，而本构建只带一个（blowfish.dll）。把它当类工厂表追问「为何不是 8 项」是问错了对象。

五、dwClsContext 实测在全部 15 个调用点都是 7（INPROC_SERVER|INPROC_HANDLER|LOCAL_SERVER）。包装器里 test al,0x14 的 0x14 是 LOCAL_SERVER|REMOTE_SERVER；7 与 0x14 相与得 4，非零，所以 je 不跳、CoCreateInstance 确实被调用。我第一次把这一位算反了（写成「7 不碰 0x14」），是被 7 & 0x14 = 4 这个算术纠正的，记作 S-206。另一个实例 13 个调用点也全部传 7，故 OleRun 那条分支在这个二进制里**从未被走到**，是模板层面的死分支——这是实测 15/15，不是推断。

六、门禁真修：新增 C18，把 C17 的空转从「静默的 0」变成「必须显式登记、一变就 FAIL」。因果链实测：C17 只扫第 7 列以「有」开头的行；这 12 行恰好等于 DISC_UNVERIFIABLE.tsv 的 12 行；而冻结档的语义就是「结构上不可能自产出凭证行」。于是 C17 的输入集按定义不可能含自述行，checked 恒 0；C11 同理，19 个 claims-none 加 12 个 frozen 等于 31，没有一行能到 ok=1。这不是「恰好没有」，是构造上不可能有，与 R68 CW8 ③、R102 C11b 是同一形状的永久免检票。故 C18 钉住五个实测值（c17_checked=0 / c11_ok=0 / claims_有=12 / frozen=12 / claims_none=19）并另钉一条因果（claims-有 集合必须仍等于 frozen 集合）。修法不是「要求 checked>0」——那要真回跑，做不到也不该伪造。

七、C18 的反控 9/9（r131v）：正控 exit 0 且打 C18 note；把 c17_checked 改成 1、c11_ok 改成 5、frozen_rows 改成 13，三次各自 exit 1 并命中 C18；只关掉因果那一条而计数不动时仍然 exit 0（证明它是独立的第二个条件，不是把同一个判断写两遍）；六次改盘后门禁字节与改前逐字节相同。恢复只从内存，不读任何回退文件（S-203 的修法沿用）。

八、方法坑两条。S-204：capstone 对**小立即数打十进制**（push 7 / push 0），我的立即数解析器只吃 0x 前缀，于是把 7 和 0 判成「寄存器或内存」，四条断言假失败；与 R130 S-200 同族，正控是「这条必须是立即数 7」。S-207：按 ff 15 形式找 IAT 引用时，我把 data[i-2] 当成操作码字节，但 ff 15 <imm32> 里 0xff 在 i-2、0x15 在 i-1，于是两个槽都报 0 处引用；而反汇编明明白白在调它们——「对一个明摆着被调用的槽报 0」就是窗口错位的信号，改成同时校验 i-2==0xff 与 i-1∈{15,25,35,05} 后得 22 处与 8 处。

九、第二译码器：0x6bedb0 的 2 个调用点用 capstone（skipdata）与 objdump 各自得出，站点集相同；原始 E8 rel32 字节扫描给出同一集合。反控最有价值的一条：**不开 skipdata 时 capstone 的 disasm_lite 会在 0x46f5a0 静默停住**，只解出 155215 条指令，0x6bedb0 的两个调用点直接消失——那一版会得出「无人调用」的错结论。R130 的普查脚本是开着 skipdata 的，所以 R130 的 117 个循环数没有踩这个坑；本条由跨家族审计员独立发现，主会话复算确认。

十、结论的边界（不粉饰）：本节给出的都是字节事实与从字节算出的算术。「为何本构建只带一个自注册 DLL」仍未得——那是构建配置问题，静态字节里没有答案。blowfish.dll 的运行期是否真的走完 LoadLibrary→DllRegisterServer→重试成功，静态只能看到这条路径存在，看不到它被执行。
"""

LEDGER_TEXT = """
## §1185 R131：0x6bedb0 由「类工厂包装器」改名为 IID 参数化实例化助手；0x6bc34d 是惰性自注册加载器；门禁新增 C18 钉住 C17 空转

- **基准**：R14_COMMON §2.134 (CR=1081) | 台账 §1184 (CR=337) | LEAD_LOCK KK (CR=137) | 看板 148 行 (CR=0) | 归档 CR=2952
- **交付一（改名，含字节依据）**：0x6bedb0 的 106 字节里没有 IClassFactory / DllGetClassObject。三条栈参数由 CFG 栈模型解出：九条 [esp+N] 读全部落在 rclsid / ppv-pUnkOuter 共用槽 / dwClsContext 三个槽内。栈模型两路互证：全 cdecl 假设下恰两处合并点自相矛盾，按 push 条数 4*nargs 假设下全一致。
- **交付二（模板有两次实例化）**：0x6bedb0 与 0x41c250 的 106 字节仅偏移 0x4e 一字节不同（c0/b0），差异是推给 QueryInterface 的 IID（IUnknown 对 070F3290-...）。故 R130「只有 2 个调用点」是**该实例**的 2 个，全族 15 个（2 + 13）。
- **交付三（循环语义）**：0x6bc34d 顺序实测为 试创建 → LoadLibraryA → GetProcAddress(DllRegisterServer) → call → 重试 → FreeLibrary。DllRegisterServer 字符串在 0x840de4、全库恰 1 处引用。表 0x7f3710 每项 8 字节 (rclsid, dll)，1 项 = {0x7e9500, blowfish.dll}。
- **交付四（R130 未取得项消失）**：「为何类工厂表只有 1 项」问错对象：它不是类工厂表，是本构建自带的自注册 DLL 清单，本构建带 1 个。
- **交付五（dwClsContext 实测）**：15/15 个调用点都传 7；7 & 0x14 = 4 ≠ 0 ⇒ je 不跳，CoCreateInstance 确实被调；OleRun 分支在全部 15 处均为死分支。
- **交付六（门禁 C18 真修）**：C17 空转的根因是 claims-有 集合（12）恰等于 frozen 集合（12），而冻结档语义就是「不可能自产出凭证行」⇒ checked 与 C11 ok 均构造上恒 0。C18 钉五个实测值 + 一条因果（两个集合必须仍相等）。反控 9/9。
- **方法坑**：S-204 小立即数打十进制致 7/0 被判成非立即数（与 R130 S-200 同族）；S-207 找 ff 15 引用时把 data[i-2] 当操作码，两个槽都假报 0 处；真因是 0xff 在 i-2、0x15 在 i-1。S-206 把 7 & 0x14 算反。
- **第二译码器 + 一条硬反控**：不开 skipdata 时 capstone disasm_lite 在 0x46f5a0 静默停住（155215 条），调用点消失；开 skipdata 后 capstone / objdump / 裸 E8 三法站点集一致。R130 的普查开着 skipdata，故其 117 不受影响。
"""

LOCK_SEG = """KL. R131 主攻 R130 台账 KJ 的第一条未取得项（「为何只需要 1 个类工厂」的因果），取得的不是一个因果而是一次改名：0x6bedb0 不是类工厂包装器。八套脚本 24+12+9+15+9+7=76 项断言（另 r131w 自审 12 项）全 PASS。

KM. 0x6bedb0 的 106 字节里没有 IClassFactory、没有 DllGetClassObject，全库也没有指向它的这两个名字。三条栈参数由 CFG 栈模型给：rclsid、ppv 与 pUnkOuter 共用的那个槽、dwClsContext（ret 0xc 给界）。九条 [esp+N] 读全部解到这三个槽内，一条不落。模型两路互证——全 cdecl 时恰两处合并点矛盾（0x6bedbd→0x6bedc0、0x6bee07→0x6bee09），按 push 条数取 4*nargs 时全一致。

KN. 模板有两次实例化：0x6bedb0 与 0x41c250，106 字节里只有偏移 0x4e 一字节不同（c0/b0），差的是推给 QueryInterface 的 IID（IUnknown 对 {070F3290-9841-11D1-B709-00A024DDAFD1}）。故 R130 的「只有 2 个调用点」是该实例的 2 个，不是这个包装器被用两次；全族 15 个（2 + 13）。R130 措辞按本条订正。

KO. 0x6bc34d 实测顺序：push 7/0/[esi] 试创建 → 失败则 [esi+4] 进 LoadLibraryA（0x7e1220）→ push 0x840de4 进 GetProcAddress（0x7e1250）→ call eax → 同参重试 → FreeLibrary（0x7e1224）。0x840de4 处字符串实测为 DllRegisterServer，全库恰 1 处引用。表 0x7f3710 每项 8 字节 (rclsid, dll 名)，恰 1 项 {0x7e9500, blowfish.dll}。

KP. 于是 R130 的未取得项「为何类工厂表只有 1 项」不是被回答而是消失：它不是类工厂表，是本构建自带的自注册 DLL 清单，本构建带 1 个。追问「为何不是 8 项」问错了对象。

KQ. dwClsContext 在全部 15 个调用点都是 7；包装器内 test al,0x14 的 0x14 = LOCAL_SERVER|REMOTE_SERVER，7 & 0x14 = 4 ≠ 0 ⇒ je 不跳、CoCreateInstance 确实被调。我第一次把这位算反（写成 7 不碰 0x14），被算术纠正，记 S-206。另一实例 13 个调用点也全传 7，故 OleRun 分支在 15/15 处都是死分支——实测，非推断。

KR. 门禁真修第四处：新增 C18。因果实测——C17 只扫 col7 为「有」的行，那 12 行恰等于 DISC_UNVERIFIABLE.tsv 的 12 行，而冻结档语义就是「不可能自产出凭证行」，故 C17 checked 与 C11 ok 都是构造上恒 0（19 claims-none + 12 frozen = 31，无一行能到 ok）。这不是「恰好没有」而是「不可能有」，与 R68 CW8 ③、R102 C11b 同形。C18 钉五个实测值与一条因果，反控 9/9（改三个计数各 exit 1；只关因果而计数不动仍 exit 0，证明是两个独立条件；六次改盘后门禁字节逐字节回原）。

KS. 方法坑三条。S-204：capstone 对小立即数打十进制（push 7 / push 0），我的解析器只吃 0x 前缀，把 7 和 0 判成非立即数，四条断言假失败；与 R130 S-200 同族。S-207：按 ff 15 找 IAT 引用时把 data[i-2] 当操作码字节，实际 0xff 在 i-2、0x15 在 i-1，两个槽都假报 0 处；「对一个明摆着被调用的槽报 0」就是错位信号，改正后 22 处 / 8 处。

KT. 规则 D：本轮两次派发均 succeeded，deepseek 53 回合 / 9.07 分钟（预算 8.0，OVERTIME 如实记）、hy4 6 回合 / 0.67 分钟。两家独立报出的数字与主会话复算一致：0x6bedb0 2 个调用点、0x41c250 13 个、106 字节仅 1 处不同（偏移 0x4e）、体 A 精确副本 1 份、0x817bc0 的 imm32 9 处、DllRegisterServer 与两个 GUID 的字符串形式。deepseek 另报一条主会话先前未测的机制并已复算确认：**不开 skipdata 时 capstone disasm_lite 在 0x46f5a0 静默停住**（155215 条），调用点消失。R130 的普查开着 skipdata，故其 117 个循环不受影响。

KU. 收口：断言 r131q 35 + r131r 12 + r131s 9 + r131t 15 + r131v 9 + r131w 12 = 92 项全 PASS（r131p 的 8 项含在其中口径之外，另记）。全程 disasm_lite 流式 + 有界窗口 detail=True（最大 0xc0 字节），未对整段 .text 开 detail=True；脚本带 timeout；收口前 ps 确认无孤儿。五项 CR 1081/137/337/0/2952 全绿；check_disc.py exit 0、C10 ok(R131)。

KV. 未取得（不粉饰）：① 「为何本构建只带一个自注册 DLL」未得，那是构建配置问题，静态字节无答案；② blowfish.dll 运行期是否真走完 LoadLibrary→DllRegisterServer→重试成功，静态只能看到路径存在看不到被执行；③ 门禁另两处未修（C7 bytes=N 死分支、C11 frozen 分支）；④ 窗口表仍需 r66 以后主快照，一份都没有；⑤ 35 个静态容器的运行期元素值与计数；⑥ 共用模板展开的充分证明（本条只证明了两个实例的字节关系，未证明还有第三个被内联展开）；⑦ 已判死线不投。
"""

BOARD_TEXT = """
## 第 127 轮

**一 · 本轮把 0x6bedb0 的名字改掉了。** R129 和 R130 都叫它「类工厂包装器」。它的 106 字节里没有 IClassFactory、没有 DllGetClassObject，全库也没有指向它的这两个名字。改名不是口味问题：名字错了，R130 的未取得项就跟着错。

**二 · 它是什么：被 IID 参数化的 COM 实例化助手。** 三条栈参数是 rclsid、ppv 与 pUnkOuter 共用的那个槽、dwClsContext（ret 0xc 给边界）。这不是读调用点读出来的，是把九条 [esp+N] 全按 CFG 解到函数入口 esp 上算出来的——九条全部落在三个参数槽内，一条不落。

**三 · 栈模型两路互证。** 把每个 call 当 cdecl，模型在恰好两个合并点自相矛盾（0x6bedbd→0x6bedc0、0x6bee07→0x6bee09）；按「调用前 push 条数 × 4」给 net delta，全模型一致。两条推导结论相同，不是一条换个说法。第一次做时我把 push 的符号写反了、第二次又把返回地址多算了一次，两次都是「某个 [esp+N] 解到参数之外」这个荒谬结果把我拉回来的。

**四 · 模板有两次实例化。** 0x6bedb0 与 0x41c250 的 106 字节里只有偏移 0x4e 一个字节不同（c0 对 b0）。差的是推给 QueryInterface 的 IID：前者 IUnknown，后者 {070F3290-9841-11D1-B709-00A024DDAFD1}。所以 R130 那句「0x6bedb0 全库只有 2 个调用点」字面对、结论错：那是**该实例**的 2 个；另一个实例被 13 处调用，全族 15 个。

**五 · 那个循环的语义也换了。** 0x6bc34d 实测顺序是：试创建 → 失败则 LoadLibraryA（0x7e1220）→ GetProcAddress（0x7e1250）取 DllRegisterServer → call → 同参重试 → FreeLibrary（0x7e1224）。0x840de4 处字符串实测就是 DllRegisterServer，全库恰 1 处引用。这是惰性自注册 COM 服务器加载器。

**六 · 于是 R130 的一条未取得项消失了，而不是被回答。** 「为何类工厂表只有 1 项」——它不是类工厂表，是本构建自带的自注册 DLL 清单，本构建带 1 个。追问「为何不是 8 项」问错了对象。

**七 · dwClsContext 实测 15/15 都是 7。** 7 & 0x14 = 4 ≠ 0，所以 je 不跳、CoCreateInstance 确实被调。OleRun 那条分支在这个二进制里 15/15 处都没被走到，是模板层面的死分支——这是实测，不是推断。我第一次把这 一位算反了（写成 7 不碰 0x14），被算术纠正。

**八 · 门禁真修：新增 C18。** R130 只证实 C17 空转、没修。本轮找到根因：C17 只扫第 7 列以「有」开头的行，那 12 行恰好等于 DISC_UNVERIFIABLE.tsv 的 12 行，而冻结档的语义就是「结构上不可能自产出凭证行」。于是 C17 的输入集按定义不可能含自述行，checked 恒 0；C11 同理（19 + 12 = 31，无一行能到 ok=1）。这不是「恰好没有」，是构造上不可能有，与 R68 CW8 ③、R102 C11b 同一形状。C18 钉住五个实测值并另钉一条因果（claims-有 集合必须仍等于 frozen 集合）。修法不是「要求 checked>0」——那要真回跑，做不到也不该伪造。反控 9/9。

**九 · 规则 D：这次两家都成了。** deepseek 53 回合 / 9.07 分钟（预算 8.0，OVERTIME 如实记），hy4 6 回合 / 0.67 分钟，均 succeeded。两家独立报的数字与我的复算一致：2 / 13 个调用点、106 字节仅 1 处不同（偏移 0x4e）、精确副本 1 份、0x817bc0 的 imm32 有 9 处。deepseek 另报一条我先没测的机制，已复算确认并写进四件套：**不开 skipdata 时 capstone 的 disasm_lite 会在 0x46f5a0 静默停住**，只解出 155215 条指令，0x6bedb0 的两个调用点直接消失。R130 的普查开着 skipdata，所以它的 117 个循环数没有踩这个坑。

**十 · 自错三条留案。** S-204：capstone 对小立即数打十进制（push 7 / push 0），我的解析器只吃 0x 前缀，把 7 和 0 判成非立即数，四条断言假失败；与 R130 S-200 同族。S-207：按 ff 15 找 IAT 引用时把 data[i-2] 当操作码字节，实际 0xff 在 i-2、0x15 在 i-1，两个槽都假报 0 处；「对一个明摆着被调用的槽报 0」就是窗口错位的信号，改正后得 22 处与 8 处。S-206：7 & 0x14 算反。

**十一 · 收口。** r131q 35 + r131r 12 + r131s 9 + r131t 15 + r131v 9 + r131w 12 = 92 项断言全 PASS。全程 disasm_lite 流式、有界窗口 detail=True（最大 0xc0 字节），未对整段 .text 开 detail=True；脚本带 timeout；收口前 ps 确认无孤儿。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0、C10 ok(R131)；GATE_VER 已由 R130 升到 R131 并同步 DISC_RECHECK 第 20 行登记式。看板写入后 148 行未到 260 阈值，本轮不归档。

**十二 · 未取得（不粉饰）。** ①「为何本构建只带一个自注册 DLL」未得——那是构建配置问题，静态字节里没有答案；② blowfish.dll 运行期是否真走完这条路径，静态只能看到路径存在；③ 门禁另两处未修（C7 bytes=N 死分支、C11 frozen 分支）；④ 窗口表仍需 r66 以后的主快照，一份都没有；⑤ 35 个静态容器的运行期元素值与计数；⑥ 共用模板展开的充分程度（只证了两个实例的字节关系，未证没有第三个被内联展开）；⑦ 已判死线不投。
"""

def load(p):
    return io.open(p, 'rb').read()

def crlf(b):
    return b.count(b'\r\n')

rec = {'targets': []}
COMMON_B, LEDGER_B, LOCK_B, BOARD_B = load(COMMON), load(LEDGER), load(LOCK), load(BOARD)
BEFORE = {'R14_COMMON.md': COMMON_B, 'GOAL_THREE_TARGETS_20261018.md': LEDGER_B,
          'LEAD_LOCK': LOCK_B, 'STATUS_BOARD.md': BOARD_B}
print('before: common CR=%d bytes=%d | ledger CR=%d | lock CR=%d | board CR=%d lines=%d'
      % (crlf(COMMON_B), len(COMMON_B), crlf(LEDGER_B), crlf(LOCK_B), crlf(BOARD_B),
         BOARD_B.count(b'\n')))

def append(path, text, want_cr, label):
    """Append `text` (LF-only, must end with exactly one trailing newline) to path."""
    orig = io.open(path, 'rb').read()
    osha = hashlib.sha256(orig).hexdigest()
    ocr = crlf(orig)
    assert ocr == want_cr, '%s CR before = %d != %d' % (label, ocr, want_cr)
    assert b'\r' not in text.encode('utf-8'), '%s new text contains CR' % label
    if not orig.endswith(b'\n'):
        raise SystemExit('%s does not end with LF; refusing to append blindly' % label)
    body = text.encode('utf-8')
    if not body.endswith(b'\n'):
        body += b'\n'
    new = orig + body
    try:
        with io.open(path, 'wb') as f:
            f.write(new)
        back = io.open(path, 'rb').read()
        assert back == new, '%s readback mismatch' % label
        assert crlf(back) == want_cr, '%s CR after = %d != %d' % (label, crlf(back), want_cr)
        print('%-34s CR %d -> %d (kept)  bytes %d -> %d (+%d)'
              % (label, ocr, crlf(back), len(orig), len(back), len(back) - len(orig)))
        return {'label': label, 'sha_before': osha, 'sha_after': hashlib.sha256(back).hexdigest(),
                'bytes_before': len(orig), 'bytes_after': len(back),
                'cr_before': ocr, 'cr_after': crlf(back), 'ok': True}
    except Exception:
        with io.open(path, 'wb') as f:
            f.write(orig)          # in-memory recovery only (S-203)
        raise

rec['targets'].append(append(COMMON, COMMON_TEXT, 1081, 'R14_COMMON.md'))
rec['targets'].append(append(LEDGER, LEDGER_TEXT, 337, 'GOAL_THREE_TARGETS_20261018.md'))
rec['targets'].append(append(LOCK, LOCK_SEG, 137, 'LEAD_LOCK'))
rec['targets'].append(append(BOARD, BOARD_TEXT, 0, 'STATUS_BOARD.md'))

b = io.open(BOARD, 'rb').read()
rec['board_lines_after'] = b.count(b'\n')
print('\nboard lines after: %d (300 cap)' % rec['board_lines_after'])
rec['ok'] = (all(t['ok'] for t in rec['targets']) and rec['board_lines_after'] <= 300
             and b.count(b'\r\n') == 0)
print('all writes ok:', rec['ok'])
json.dump(rec, open(OUT, 'w'), ensure_ascii=False, indent=1)
raise SystemExit(0 if rec['ok'] else 1)
