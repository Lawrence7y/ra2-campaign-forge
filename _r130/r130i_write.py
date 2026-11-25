#!/usr/bin/env python3
# R130 r130i: append this round's text to the four artifacts, LF-only, preserving each
# file's CR count. Preconditions asserted against the post-archival state. Idempotent
# guard: refuses if this round's marker is already present.
import hashlib
import io
import os
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BOARD = os.path.join(R14, 'STATUS_BOARD.md')
COMMON = os.path.join(R14, 'R14_COMMON.md')
LOCK = os.path.join(ROOT, 'lead/LEAD_LOCK')
LEDGER = os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md')

MARK = 'R130'

BOARD_TXT = u'''
## \U0001f7e2 R17 第 130 轮（2026-11-25 06:0x–06:3x）· 0x7f3710 那张表为何只有 1 项已结案：全库只有 1 张类工厂表，包装器只有 2 个调用点且全在同一个循环里；另发现 C17 实际处于空转状态

### 一 · 起点：R129 台账 HZ 的第一条未取得项

R129 留下的问题是“0x7e9500 那席 CLSID 对应的类工厂表为何只有 1 项，是否还有第二张同类表”。本轮把它拆成两个可机械核验的子问：（a）包装器 0x6bedb0 全库有几个调用点；（b）全库有几张按“表头 + 步长 + 上界 + 回边”形态遍历的表。两个子问都以字节结果回答，不靠形态猜。

### 二 · 包装器 0x6bedb0 全库只有 2 个调用点，且都在同一个循环里

实测（r130c，三种独立方式）：capstone 线性扫描得 2 处 0x6bc364 与 0x6bc3aa；objdump 第二译码器同样得 2 处；原始字节 E8 rel32 扫描也得同样 2 处。三路交集完全一致。且这 2 处均落在 0x6bc34d 到回边 0x6bc412 的循环体内（0/2 在循环外）。
反控一条，且是本轮最有价值的一条：对 0x6bedb0 做「纳粥 imm32 扫描」得 **0 处**（实测）。因为 call 是相对跳转，字节里存的是目标减去（调用点+5）的位移，不是目标本身。若只用 imm32 扫描会得出「包装器根本没人调用」的错结论。反向检验：表头常量 0x7f3710 作为数据 imm32 全库恰 1 处，与层序自洽。

### 三 · 全库 117 个表遍历循环，只有 1 个喂给这个包装器

一遍前向对齐扫描（r130b，1394186 条指令）得 117 个符合四要素的循环（表头 mov 可被提到循环之前，这是本库的常态：0x6bc342 的 mov esi,0x7f3710 正在循环头 0x6bc34d 之前 11 字节）。其中表头在 .rdata 的 9 个，在 .data 的 108 个。只有 1 个循环的体内含 0x6bedb0 的调用，它就是 0x6bc34d。
表内容逐项读出：恰 1 项，+0 = 0x7e9500（CLSID 指针），+4 = 0x840a78（ASCII 字符串指针）。字符串实读为 blowfish.dll。CLSID 十六字节与 R129 逐字相同：10 ad 40 14 a8 6a d1 11 b6 f9 00 a0 24 dd af d1。

### 四 · 一个造假判据被自己的反控杀掉

我第一版想的结论是「0x7f3710 是全库唯一步长大于等于 8 的 .rdata 表」。反控直接给了反例：还有 0x7e1b78（步长 112，6 项）与 0x7e1b88（步长 112，2 项）。若我不写反控就把那句写进台账，就是一条很容易被推翻的假判据。
查字节后实情：那两张根本不是指针表。0x7e1b78 的字节是 54 45 4d 50 45 52 41 54 45 00 —— ASCII 7034 594d 4552 4154 45，就是 TEMPERATE；后面跟 SNOW / URBAN / DESERT / NEWURBAN / LUNAR。0x7e1b88 是 4e61 6d65 3a54 656d —— Name:Temp。它们是地形名字符串序列，循环（0x48dbec 与 0x5970b6，步长 0x70）确实在每 0x70 字节取一个字符串指针。
所以修正后的命题只在「结构上是（CLSID 指针, DLL 字符串指针）对」这个范围内成立，不能写成「全库唯一的大步长 .rdata 表」。这是两个不同的命题，后者是假的。

### 五 · 它们不是“第二张类工厂表”，但“只有 1 项”的因果仍未完全落定

R129 问的是「为何只有 1 项」。本轮能确定的是：全库没有第二张同序列表，包装器也没有第二个调用点，所以「只装一个类工厂」是**字节事实**，不是我漏扫。
但「为何只需要一个」的因果还没有字节证据。我不把「没有第二个」写成「所以设计上只需要一个」，后者需要 blowfish.dll 在运行期的使用路径证据，属于动态范围。

### 六 · 第二件事：C17 实际处于空转状态（本轮发现，未修）

看门禁输出 C17 这一行写着 checked=0。R129 将 C17_PIN 清空后，impossible=0 是预期的；但 checked=0 是另一件事，R129 没解释。
实测（r130f）：第 7 列声称「有」的 12 行，它们的产物文件全部存在（0 个缺失），但这 12 份产物里 DISC_RECHECK 自述行合计 **0 条**，12/12 行各自为 0。
反控三条证明扫描器没坏：同一扫描器在 R14 目录下的 26 个 _r94 测试产物里读到了合法自述行；临时写一条合法行能被计数为 1（NC1）；用错的纪律号查得 0（NC2）。
结论：C17 的两道判据（C17a 时间不可能性、C17b 跨轮复用）目前对**任何真实产物**都不执行，它们只能对测试产物生效。这是一射空枪，不是一道门。
本轮**不修**它：修法要么把 12 行的第 7 列降为「无」（那是对别人行的裁定，需单独走流程），要么为它们补真产物（需要真回跑，本轮做不到），两条都不是本轮能单方落定的。只把发现与证据落盘。

### 七 · 窗口表扩展被硬阻断，不是不做

R129 说「窗口表只覆盖 r36..r65 共 28 轮，r66 以后全部不可验证”。我查了能否扩：窗口端点的唯一来源是 R17_LEAD_BASELINE 下的 STATUS_BOARD.before_rN_HHMMSS.md 主快照。实测：r66 以后的主快照**一份都没有**（r66..r129 都无）。
没有快照就没有真实时刻，没有真实时刻就不能造窗口，否则就是编造时刻（R129 裁定五条不可能行时用的是同一条理由）。故本轮不扩窗口表，也不把它写成待办。

### 八 · 规则 D：一次派发，失败，如实记

deepseek task 267 failed 加 error_max_turns：61 回合 / 10.33 分钟 / 预算 8.0 分钟 ⇒ OVERTIME，report 为空。按 §2.12 规则 D，本轮**不写「已过跨家族审计」**。
它在超时前落了一份 audit_a_repro.json。按规则，审计员结论必须由主会话复算；我复算并逐条比对：
它报 295 个表循环，我得 117。不是分歧：295 是它的 raw 候选数，经它自己的复验后尸体列恰 117；用（表头,上界,步长）三元组比对，两份集合 117/117 完全相等，两边的差集均为空。
它的 T4 比我多报了 0x7e1b78 与 0x7e1b88，这一点是它对、我错（我先前的「唯一大步长表」命题是假的），已在第四节如实更正。
它的 T1/T2/T3 与我一致（2 个调用点、两个都在循环内、正控命中）。这些数字由 r130g 第 A/B 组 15 项断言重算。

### 九 · 自错三条留案

S-200：imm() 只接受 0x 前缀，但 capstone 小立即数打印为**十进制**（add esi, 8 / push 7），大的才打 0x。导致已知循环 0x6bc34d 被判为不匹配，全库得 0 个循环。和 R129 S-192「reciprocity对象只接受一种数值形式」是同一族。临界信号是正控：若不写“必须找到已知循环”这条正控，我会把 0 当成“确实没有”写进台账。
S-201：objdump 行匹配时我先后写了两版正则（要求操作数后跟空白，以及要求操作数后不是非空白），两版都得 0。真因是字符类只吃掉 0x 前缀里的那个 0 就在 x 处停下，后随的断言永远不满足。与二进制无关。改成显式吃掉 (?:0x)? 后才对。我当时两次都在猜正则，而不是去看一行原始输出。
S-202：r130f 把 _r94 测试产物从 ROOT 解析，得到「固定测试产物 0 份带行」，于是 PC1 反控报 False。实际路径是 R14/_r94/...。若不用反控，这会被写成「扫描器坏了」。

### 十 · 收口

r130a 9 + r130b 6 + r130c 7 + r130d 8 + r130e 5 + r130f 8 + r130g 41 = 84 项断言，全 PASS（r130g 包含对前六套的逐项重算）。
全程 disasm_lite 流式扫描与 objdump 单遍，未对整段 .text 开 detail=True；脚本均带 timeout；收口前 ps 确认无孤儿进程。
本轮未改任何门禁文件（check_disc.py / DISC_RECHECK.tsv / recheck_verify.py 字节未动），故 GATE_VER 仍为 R129。
五项 CR 全绿 1081/137/337/0/2952；看板写入前 255 行已越 260 阈值，已按规则将最早两轮（186 行 / 21528 字节）搬进 BOARD_ARCHIVE，搬前归档 CR=2952、搬后仍 2952；看板 255 降到 69。

### 十一 · 未取得（不粉饰）

①「为何只需要 1 个类工厂」的因果未得，只得到了「确实只有 1 个」的字节事实；② blowfish.dll 运行期是否真被 LoadLibraryA 装入并成功 CoCreateInstance，静态只能看到两个调用邻接；③ C17 空转本轮只证实不修；④ 窗口表扩展需 r66 以后的主快照，目前一份都没有；⑤ 35 个静态容器的运行期元素值与计数；⑥ 共用模板展开的充分证明；⑦ 门禁另两处未修（C7 bytes=N 死分支、C11 frozen 分支）；⑧ 已判死线不投。
'''

COMMON_TXT = u'''
## 2.134

R130 。本节记一个可复现的字节结论与两个方法坑。

一、gamemd.exe 中，包装器 0x6bedb0（0x6beddd call CoCreateInstance、0x6bedec call OleRun、0x6bee05 call [ecx]、0x6bee10 call [edx+8]）在全库**只有 2 个调用点**：0x6bc364 与 0x6bc3aa。三种独立方式给出同一结果：capstone disasm_lite 线性扫描（1394186 条）、objdump 第二译码器（1401544 条）、原始字节 E8 rel32 扫描。两个调用点均落在 0x6bc34d 循环体内（回边 0x6bc412）。

二、全库「表头 mov + add 步长 + cmp 上界 + 条件回边」形态的循环共 117 个（表头在 .rdata 9 个、在 .data 108 个）。只有 1 个循环喂给上述包装器，它走的表头 0x7f3710 、上界 0x7f3718、步长 8，故表内恰 1 项：+0 = 0x7e9500（CLSID {1440AD10-6AA8-11D1-B6F9-00A024DDAFD1}），+4 = 0x840a78（ASCII blowfish.dll）。

三、方法坑 S-200：capstone 对**小立即数打印十进制**（add esi, 8），对大的才打 0x（cmp esi, 0x7f3718）。若立即数解析器只接受 0x 前缀，已知循环会被判为不匹配、全库得 0 个。必须同时接受两种形式，且必须写「必须找到已知循环」这条正控。

四、方法坑 S-201：匹配 objdump 的 call 行时，[0-9a-f]+ 会先吃掉 '0x' 的 '0' 并在 'x' 处停下，后随的空白类或否定 lookahead 永远不满足，于是一条也匹不上。必须显式写 (?:0x)?。两版错正则都会让人以为「objdump 找不到调用」。

五、结论的边界：「全库没有第二张类工厂表」是字节事实；「所以设计上只需要一个」不是，后者需要运行期路径证据。另：0x7e1b78 与 0x7e1b88 这两张 .rdata 「步长 112」的表是地形名字符串序列（TEMPERATE / SNOW / URBAN / DESERT / NEWURBAN / LUNAR），不是指针表，不能用它们反驳上述结论。
'''

LOCK_TXT = u'''
KA. R130 主攻 R129 台账 HZ 的第一条未取得项（0x7e9500 那张类工厂表为何只有 1 项、是否还有第二张）。取得：只有 1 张，且包装器只有 2 个调用点全在同一循环。另发现 C17 实际空转。八套脚本 84 项断言全 PASS。

KB. 包装器 0x6bedb0 全库只有 2 个调用点（0x6bc364、0x6bc3aa），三种独立方式一致：capstone 1394186 条、objdump 1401544 条、原始 E8 rel32 字节扫描。两处均在 0x6bc34d..0x6bc412 循环体内，0 处在外。反控最有价值的一条：对 0x6bedb0 做纳粥 imm32 扫描得 0 处（call 存的是目标减（调用点+5）的位移），只用 imm32 会得出「无人调用」的错结论；表头常量 0x7f3710 作数据 imm32 全库恰 1 处。

KC. 全库表遍历循环 117 个（.rdata 头 9 / .data 头 108），只 1 个喂给 0x6bedb0。表 0x7f3710 恰 1 项：+0 = 0x7e9500，+4 = 0x840a78 -> blowfish.dll。CLSID 十六字节 10 ad 40 14 a8 6a d1 11 b6 f9 00 a0 24 dd af d1 与 R129 逐字相同。循环头 0x6bc34d 的表头 mov 在 0x6bc342、步长 add 在 0x6bc409、上界 cmp 在 0x6bc40c、回边 jl 在 0x6bc412 ——与 R129 一致。

KD. 一个假命题被自己的反控杀掉，如实记。我起初写下「0x7f3710 是全库唯一步长大于等于 8 的 .rdata 表」，反控给出反例 0x7e1b78（步长 112，6 项）与 0x7e1b88（步长 112，2 项）。查字节：那是地形名字符串序列（TEMPERATE / SNOW / URBAN / DESERT / NEWURBAN / LUNAR；另一张开头是 Name:Temperate），循环 0x48dbec 与 0x5970b6 每 0x70 字节取一个字符串指针，不是（CLSID, DLL）对。修正后的命题只在「结构为（CLSID 指针, DLL 字符串指针）对」范围内成立。

KE. 第二件事（本轮发现，未修）：C17 实际处于空转状态。门禁自己打印 checked=0。实测：第 7 列声称「有」的 12 行，产物文件全存在但 DISC_RECHECK 自述行合计 0 条（12/12 各为 0）。反控三条：同扫描器在 R14/_r94 的 26 份测试产物里读到合法行（证明扫描器没坏）、临时行可计数为 1、错纪律号得 0。故 C17a/C17b 目前对任何真实产物都不执行，只能对测试产物生效。本轮不修：降列是裁定、补真产物需真回跑，两条都需单独流程。

KF. 窗口表扩展被硬阻断：窗口端点的唯一来源是 R17_LEAD_BASELINE 下的 before_rN_HHMMSS 主快照，r66 以后一份都没有。无快照即无真实时刻，造窗口即编造时刻，与 R129 裁定五条不可能行时同一理由。故不扩，也不写成待办。

KG. 规则 D 一次派发失败，如实记。deepseek task 267 failed 加 error_max_turns（61 回合 / 10.33 分钟 / 预算 8.0 ⇒ OVERTIME），report 为空。故本轮不写「已过跨家族审计」。它超时前落了 audit_a_repro.json，主会话逐条复算：它报 295 个循环、我得 117，295 是 raw 候选数而非分歧，按（表头,上界,步长）三元组比对两家 117/117 完全相等、双边差集为空；它的 T4 比我多报了 KD 那两张序列，那一点是它对、我错。

KH. 自错三条留案。S-200：imm() 只接受 0x 前缀，而 capstone 小立即数打十进制（add esi, 8），导致已知循环被判为不匹配、全库 0 个；与 R129 S-192 同族；信号来自正控。S-201：匹配 objdump call 行时 [0-9a-f]+ 只吃掉 '0x' 的 '0'、在 'x' 处停下，两版正则都得 0，与二进制无关；须显式 (?:0x)?。S-202：r130f 把 _r94 测试产物从 ROOT 解析，PC1 反控报 False；实际路径在 R14 下。三条都是「先信自己的解析代码，后查原始字节」。

KI. 收口：r130a 9 + r130b 6 + r130c 7 + r130d 8 + r130e 5 + r130f 8 + r130g 41 = 84 项全 PASS。未改任何门禁文件（check_disc.py / DISC_RECHECK.tsv / recheck_verify.py 字节未动），GATE_VER 仍 R129。五项 CR 全绿 1081/137/337/0/2952；看板写入前 255 行越阈，已将最早两轮（186 行）搬进归档，搬前后归档 CR 均 2952，看板 255 降 69。全程 disasm_lite 流式与 objdump 单遍，未对整段 .text 开 detail=True。

KJ. 未取得（不粉饰）：①「为何只需要 1 个类工厂」的因果未得，只得到「确实只有 1 个」的字节事实；② blowfish.dll 运行期是否真被装入并成功取对象，静态只能看到两个调用邻接；③ C17 空转本轮只证实不修（降列是裁定、补真产物需真回跑）；④ 窗口表扩展需 r66 以后主快照，目前一份也没有；⑤ 35 个静态容器的运行期元素值与计数；⑥ 共用模板展开的充分证明；⑦ 门禁另两处未修（C7 bytes=N 死分支、C11 frozen 分支）；⑧ 已判死线不投。
'''

LEDGER_TXT = u'''
## §1184

R130 · gamemd.exe 类工厂表唯一性与 C17 空转发现。下表每一行都有脚本产物可回跑，数字先实测后填。

| 事实 | 值 | 来源 |
| --- | --- | --- |
| 包装器 0x6bedb0 调用点数 | 2（0x6bc364、0x6bc3aa） | r130c、r130e |
| 三种方式一致性 | capstone / objdump / E8 字节扫描 均得同 2 处 | r130e |
| 纳粥 imm32 扫描 0x6bedb0 | 0 处（call 为相对跳转） | r130e |
| 表头 0x7f3710 作数据 imm32 | 1 处 | r130e |
| 全库表遍历循环数 | 117（.rdata 9 / .data 108） | r130b |
| 喂给 0x6bedb0 的循环数 | 1（0x6bc34d） | r130c |
| 表 0x7f3710 项数 | 1 | r130b、r130c |
| 该项内容 | +0 = 0x7e9500，+4 = 0x840a78 -> blowfish.dll | r130c |
| CLSID 十六字节 | 10 ad 40 14 a8 6a d1 11 b6 f9 00 a0 24 dd af d1 | r130c |
| claims-none 校验式有分辨力且有耦合 | 19/19 两项反控全过 | r130d |
| 第 7 列声称「有」的行数 | 12 | r130f |
| 这些产物里的 DISC_RECHECK 自述行 | 0 条（12/12 各为 0） | r130f |
| C17 是否空转 | 是（门禁自己打印 checked=0） | r130f |
| 反控：测试产物中含自述行的件数 | 26 | r130f |
| 本轮断言总数 | 84（全 PASS） | r130g |

边界声明：「只有 1 张类工厂表」是字节事实；「为何只需要 1 个」本轮未得，不将前者升格为后者。
'''


def precheck():
    exp = {
        BOARD: (0, 69),
        COMMON: (1081, None),
        LOCK: (137, None),
        LEDGER: (337, None),
    }
    ok = True
    for p, (cr, lf) in exp.items():
        b = io.open(p, 'rb').read()
        if b.count(b'\r') != cr:
            print('PRECHECK FAIL CR %s %d != %d'
                  % (os.path.basename(p), b.count(b'\r'), cr))
            ok = False
        if lf is not None and b.count(b'\n') != lf:
            print('PRECHECK FAIL LF %s %d != %d'
                  % (os.path.basename(p), b.count(b'\n'), lf))
            ok = False
        if 'R130' in b.decode('utf-8', 'replace') and p is not LOCK:
            print('PRECHECK FAIL: R130 marker already present in '
                  + os.path.basename(p))
            ok = False
    return ok


def app(p, txt, want_cr):
    before = io.open(p, 'rb').read()
    assert before.count(b'\r') == want_cr
    assert '\r' not in txt, 'text contains CR; refusing'
    with io.open(p, 'ab') as f:
        f.write(txt.encode('utf-8'))
    after = io.open(p, 'rb').read()
    assert after.count(b'\r') == want_cr, 'CR changed on ' + p
    assert after.startswith(before), 'file not appended cleanly'
    return after


def main():
    if not precheck():
        print('ABORT preconditions')
        return 1
    app(BOARD, BOARD_TXT, 0)
    app(COMMON, COMMON_TXT, 1081)
    app(LOCK, LOCK_TXT, 137)
    app(LEDGER, LEDGER_TXT, 337)
    for p in (BOARD, COMMON, LOCK, LEDGER):
        b = io.open(p, 'rb').read()
        print('wrote', os.path.basename(p), 'CR', b.count(b'\r'),
              'LF', b.count(b'\n'), 'bytes', len(b),
              'sha', hashlib.sha256(b).hexdigest()[:16])
    return 0


if __name__ == '__main__':
    sys.exit(main())
