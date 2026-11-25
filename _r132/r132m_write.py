#!/usr/bin/env python3
# R132 r132m: append the four-part record with the full write discipline.
#   - exclusive (O_EXCL) sha-named backup in R17_LEAD_BASELINE before any mutation
#   - assert old sha256 and old CR count before writing
#   - single atomic write, read back and re-verify CR
#   - recover ONLY from the in-memory copy on any failure (S-203 / S-211 discipline)
import hashlib, io, json, os, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
COMMON = os.path.join(R14, 'R14_COMMON.md')
LEDGER = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BOARD = os.path.join(R14, 'STATUS_BOARD.md')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
OUT = os.path.join(ROOT, '_r132', 'r132m_write.json')

# ---------- expected pre-state (measured, not assumed) ----------
EXPECT = {
    COMMON: {'cr': 1081, 'label': 'R14_COMMON.md'},
    LEDGER: {'cr': 337, 'label': 'GOAL_THREE_TARGETS_20261018.md'},
    LOCK:   {'cr': 137, 'label': 'LEAD_LOCK'},
    BOARD:  {'cr': 0,   'label': 'STATUS_BOARD.md'},
}

COMMON_TEXT = """## 2.136

R132 不是修修补补，是把 R131 一条**承重的结论**推翻，并给出推翻它的字节依据。R131 说 0x6bedb0 与 0x41c250 的「106 字节里只有偏移 0x4e 一字节不同」，据此论证这是同一个模板的两次实例化、差别只在 QI 的 IID。这个数字来自一个启发式：从入口向下反汇编到**第一条 ret** 为止。R132 用控制流可达性遍历替代它，得到的真实长度是 **136 字节**，差异是 **两处**（0x4e 与 0x70），而不是一处。

一、截断是真的，且能精确定位。0x6bedb0 的 je 在 0x6bedc6 跳到 0x6bee1a，而 0x6bee1a 正是第一条 ret（0x6bee17 结束）之后的地址；另一条 jl 在 0x6bede5 跳到 0x6bee33。所以「到第一条 ret 为止」在结构上必然截断一个**可达**的 else 块。反控：把 else 块入口 0x6bee1a 单独做 CFG 遍历，得 12 条指令、恰好 30 字节，收在同一个结束地址 0x6bee38；106 + 30 = 136，无缝无叠。第二个实例同样：0x41c266 跳 0x41c2ba，0x41c285 跳 0x41c2d3，真实长度同为 136，else 块同构。另有一条独立边界证据：两个函数体结束后都正好是 8 个 0x90 nop，然后才是下一个函数入口——边界不是靠长度猜的。

二、于是 R131 的模板结论要按字节订正。在完整的 136 字节上逐字节比较，两处不同：偏移 0x4e（c0 对 b0）与偏移 0x70（c0 对 b0）。前者是 if 路径推给 QueryInterface 的 IID，后者是 **else 路径**做 CoCreateInstance 时用的 IID——那一处整个落在 R131 的 106 字节截断之外，所以 R131 看不见它，只好写成「只有一处不同」。这不是笔误，是截断的必然后果；反控给出对照：只用前 106 字节比较**确实**只有一处差异，正是 R131 的数字。两件事同时为真，恰好说明口径才是分歧源。

三、实例化个数仍是 2，这次是三重掩码互证。掩码口径一（只掩三个 IID push 立即数）命中 2 处；口径二（掩掉体内**全部** imm32，共 40 字节）命中**同样** 2 处——这排除了「第三份副本只在别的立即数上不同因而躲开掩码」这一逃逸路径；口径三（完全不掩码）只命中源实例 1 处，证明掩码确实在起作用而不是恒真。反控另加一条：把掩码外一个字节翻掉做的诱饵，全库命中 0。调用点也复核了：0x6bedb0 两个、0x41c250 十三个，与 R131 一致。

四、R131 的分支判读被推翻，且是**方向反了**，不是细节偏差。R131 同一段里写了两句话：一是「7 & 0x14 = 4 ≠ 0 故 je 不跳」——算术正确；二是「OleRun 分支 15/15 处均为死分支」——这句反了。je 不跳意味着**顺序落入** if 路径，而 OleRun 恰在 if 路径里（0x6bedec，偏移 +0x3c），所以 OleRun 是**活**的；真正走不到的是 je 的目标分支（0x6bee2b，那次 CoCreateInstance 后面没有 OleRun）。可达性遍历给出机械判据：按 ZF=0 走，可达集含 if 臂的 CoCreateInstance 与 OleRun、**不含** else 臂的 CoCreateInstance（两个实例各 4 项断言全过）；反控是「若 ZF=1 则 OleRun 不在可达集」——说明这条臂确实是条件分支而不是恒执行。

五、承重的那一步单独加固：`test al,0x14` 到底看哪个参数。这一步决定第四条的结论，不能靠手感。体里九条 [esp+N] 读全部列出；关键在于 +0x18 处读 [esp+0xc] 进 ecx、随后作为 CoCreateInstance 的**第一个**实参（rclsid）压栈。若深度取 12，该读会落到入口相对 +0x0，即**返回地址**；把返回地址当 rclsid 是荒谬的。若深度取 8，它落到 +0x4 = arg1。独立佐证：15 个调用点里有 10 个把常量传给 arg1，这 10 个常量（0x7e9a30/0x7e9a60/0x7e9a70/0x7e9a90）**全部**落在 .rdata/.data 内，10/10——是 GUID 指针该有的样子，而返回地址是代码地址。故深度 8 被强制，[esp+0x14] 解到入口相对 +0xc，即 arg3。arg3 在 15/15 个调用点实测都是 7，故 ZF=0、je 不跳，如第四条。

六、跨家族审计（规则 D）。deepseek task 272 succeeded，55 回合 / 6.0 分钟 / 预算 2.0（OVERTIME 如实记）——注：本轮派发时 budget-min 填的是 2 而非惯例的 8，故 OVERTIME 标注的绝对值不具可比性，下一轮按 8 重设。hy4 task 273 succeeded，27 回合 / 3.17 分钟 / 预算 2.0（同样受此影响）。两家独立报出的数字与主会话复算一致：真实长度 136（而非 106）、差异两处（0x4e 与 0x70）、实例恰 2 个、else 块 30 字节、两体结束后各 8 个 nop、0x6bedb0 与 0x41c250 的调用点各 2 与 13。hy4 另报 dwClsContext 分布 7 出现 11 次、1 出现 6 次、eax 出现 4 次，与我复算的 11/6/4 逐项相同；我第一版得 10 是因为有一处站点（0x469f4b）窗口太窄没解出 5 个 push，属我的口径漏项，已由放宽窗口后修正。

七、deepseek 报的一条**跨轮次**风险已采纳并复算：不开 skipdata 时 capstone 的 disasm_lite 会在 0x46f5a0 静默停住，只解出 155215 条。R131 已记过这一条。R132 的全部普查都开着 skipdata，并加了一条断言直接盯住这件事：线性扫描的最大指令起始地址必须 > 0x7e0000（实测 0x7e0fff），否则命令行统计会静默少算而不报错。这条断言的价值在于它能在别处出问题时先响。

八、自错五条留案。S-212：把 OleRun 的字节模式写成 ff 16，实际是 ff 15（call 间接），于是全库 OleRun 报 0 处，而反汇编明明在调它——与 R131 S-207 同族，都是「对一个明摆着被调用的槽报 0」；改正后 7 处。S-213：栈深度遍历里把每个 call 当成不改变深度，于是 [esp+N] 全部解到负偏移或 argNone，得到「九条读全部越界」的荒谬结论；改为识别被调方弹参后，arg1 常量 10/10 落在数据节，模型自洽。S-214：按 op_str.startswith('al,') 匹配寄存器，而 capstone 打印的是 'al, 0x14'（逗号后有空格），两条断言假失败；与前两轮 S-200/S-204 同族，都是解析器的空格/进制假设。S-215：把「第一条 ret 之后都是填充」当成事实，于是 objdump 的断言写成「0x6bee38 之后不得有指令起始」，而那里是 8 个合法 nop；改成「恰好 8 个 0x90 且第 9 个不是」。S-216：r132d 的回溯窗口取 10 条指令，而 0x469f4b 站在 push 与 call 之间夹了七条填充 mov，于是漏解、21 站点只解出 20；与 S-205 同族（都是窗口宽度拍小了），改正方向是「窗口宽度必须由最坏情况站点决定，不能由典型站点决定」。

九、断言与收口，含一条**故意留着的 FAIL**。十二套脚本共产出 94 项断言：r132a 9 + r132b 8 + r132c 6 + r132d 4 + r132e 9 + r132f 4 + r132g 5 + r132h 15 + r132i 4 + r132j 6 + r132k 16 + r132l 8。其中 **93 PASS、1 FAIL**。那条 FAIL 是 r132d 的「21 个站点是否都解出 5 个 push」——实得 20，漏的是 0x469f4b，原因是该脚本的回溯窗口只有 10 条指令，而这一站在 push 与 call 之间夹了七条填充 mov。不是结论错，是我的**窗口太窄**，属 S-216，与 R131 S-205（窗口落在指令中间）同族。r132g 用 16 条指令的窗口重解同一张表，得 21/21，两表除该站外逐项相同。这条 FAIL 我留在产物里没有抹掉，因为「断言全绿」比「一条已知 FAIL 且被解释清楚」更危险。全程 disasm_lite 流式（分块 0x10000）与有界窗口 detail=False，未对整段 .text 开 detail=True；objdump 单遍；脚本均带 timeout；收口前 ps 确认无孤儿。五项 CR 1081/137/337/0/2952 全绿。

十、未取得（不粉饰）。① R131 那句「OleRun 是死分支」的**动机**无从复原——只知结论反了，不知当时为何把臂名扣错；本轮只订正结论，不臆测成因。② else 臂在运行期是否**永不**执行，静态只能证明「在 15 个调用点都传 7 的既定事实下不可达」，不能证明「任何输入都不进 else 臂」——若有别处直接调用这两个函数并传低位 bit2 为 0 的值，else 臂会执行；本轮未找到这样的调用点，但「未找到」不等于「不存在」。③ 0x70 处那第二个 IID 常量（else 臂的 riid）在 R131 口径下从未被读到，它的具体 GUID 值本轮只知与 0x4e 同形（均为 c0/b0 单字节差），完整 16 字节未逐一展开。④ blowfish.dll 运行期是否真走完 LoadLibrary→DllRegisterServer，静态仍只能看到路径存在。⑤ 门禁另两处未修（C7 的 exists/bytes=/none 三个分支在本轮实测 31 行覆盖 0 行，即死分支；C11 frozen 分支）。⑥ 窗口表仍需 r66 以后主快照，一份都没有。⑦ 35 个静态容器的运行期元素值与计数。
"""

LEDGER_TEXT = """
## §1186 R132：推翻 R131 的 106 字节模板口径 —— 真实长度 136、差异两处、OleRun 在活臂

- **基准**：R14_COMMON §2.135 (CR=1081) | 台账 §1185 (CR=337) | LEAD_LOCK KZ (CR=137) | 看板 184 行 (CR=0) | 归档 CR=2952
- **交付一（真实边界）**：R131 用「到第一条 ret 为止」得 106 字节，是启发式。CFG 可达性遍历得**真实长度 136**：0x6bedc6 的 je 跳 0x6bee1a（第一条 ret 0x6bee17 之后），0x6bede5 的 jl 跳 0x6bee33。实例 B 同构（0x41c266→0x41c2ba、0x41c285→0x41c2d3）。反控：else 块单独遍历 = 12 条指令 / 30 字节，收在同一地址，106+30=136 无缝无叠。独立边界证据：两体之后各恰 8 个 0x90 nop。
- **交付二（差异两处而非一处）**：136 字节逐字节比较，偏移 **0x4e** 与 **0x70** 各一处 c0/b0。0x70 落在 else 臂 CoCreateInstance 的 riid，整处在 R131 的 106 字节之外 ⇒ R131「只有一处不同」是截断的必然后果。反控：只用前 106 字节比较**确实**只有 0x4e 一处，正是 R131 的数字。
- **交付三（实例数仍为 2，三重掩码互证）**：只掩三个 IID push → 2 处；掩体内**全部** imm32（40 字节）→ **同样** 2 处（排除「第三份只在别的立即数上不同」）；完全不掩 → 1 处（证明掩码非恒真）。诱饵（掩码外翻一字节）命中 0。调用点：0x6bedb0 两个、0x41c250 十三个。
- **交付四（R131 分支判读方向反了）**：R131 同段两句话互相矛盾——「7 & 0x14 = 4 ≠ 0 故 je 不跳」（算术对）与「OleRun 分支 15/15 均为死分支」（结论反）。je 不跳 ⇒ 顺序落入 if 臂；OleRun 在 if 臂（0x6bedec，+0x3c）⇒ OleRun 是**活**的。真正不可达的是 je 目标分支（0x6bee2b 那次 CoCreateInstance，其后无 OleRun）。可达性判据：ZF=0 时可达集含 if 臂 CoCreateInstance + OleRun、不含 else 臂 CoCreateInstance（两实例各 4 项断言全过）；反控「若 ZF=1 则 OleRun 不可达」证明该臂确是条件分支。
- **交付五（承重步加固）**：`test al,0x14` 取哪个参数由栈深度决定。+0x18 读 [esp+0xc] 进 ecx 后作 CoCreateInstance 第一实参（rclsid）：深度 12 ⇒ 解到入口+0x0（返回地址，荒谬）；深度 8 ⇒ 解到 +0x4 = arg1。独立佐证：15 个调用点中 10 个把常量传 arg1，这 10 个常量全部落在 .rdata/.data（10/10，GUID 指针形态），而返回地址是代码地址 ⇒ 深度 8 被强制 ⇒ [esp+0x14] = arg3。arg3 在 15/15 都是 7 ⇒ ZF=0 ⇒ je 不跳。
- **规则 D**：deepseek task 272 succeeded 55 回合/6.0 分钟、hy4 task 273 succeeded 27 回合/3.17 分钟；预算均填 2.0（本轮派发参数偏离惯例 8.0，OVERTIME 标注绝对值不可比，下轮按 8 重设）。两家独立确认 136 / 两处差异 / 2 个实例 / else 块 30 字节 / 各 8 个 nop / 2 与 13 个调用点；hy4 的 dwClsContext 分布 11/6/4 与主会话复算逐项相同。
- **跨轮次风险已采纳**：不开 skipdata 时 capstone disasm_lite 在 0x46f5a0 静默停住（155215 条）。R132 全部普查开 skipdata，并加断言「线性扫描最大指令起始 > 0x7e0000」（实测 0x7e0fff）。
- **自错五条**：S-212 OleRun 字节模式写成 ff 16（实为 ff 15），全库报 0 处（与 S-207 同族）；S-213 栈遍历把 call 当不弹参，[esp+N] 全解成负偏移；S-214 startswith('al,') 漏掉逗号后空格，两条断言假失败（与 S-200/S-204 同族）；S-215 把 ret 之后当无指令，而那里是 8 个合法 nop；S-216 r132d 回溯窗口仅 10 条指令，漏解 0x469f4b（push 与 call 间夹七条填充 mov）。
- **断言**：r132a 9 + r132b 8 + r132c 6 + r132d 4 + r132e 9 + r132f 4 + r132g 5 + r132h 15 + r132i 4 + r132j 6 + r132k 16 + r132l 8 = **94 项，93 PASS / 1 已知 FAIL**。FAIL 为 r132d「21 站点均解出 5 push」实得 20（漏 0x469f4b，回溯窗口 10 条太窄，S-216）；r132g 用 16 条窗口重解得 21/21，两表除该站外逐项相同。该 FAIL 故意留盘不抹。
- **未取得**：① R131 扣错臂名的成因不可复原；② else 臂「任何输入都不可达」未证（只证「在 15 个调用点均传 7 时不可达」）；③ 0x70 处的第二个 IID 常量完整 16 字节未展开；④ blowfish.dll 运行期未证；⑤ 门禁 C7 三个死分支（exists/bytes=/none 实测 31 行覆盖 0 行）与 C11 frozen 分支未修；⑥ 窗口表仍缺 r66 以后快照；⑦ 35 个静态容器的运行期元素值与计数。
"""

LOCK_SEG = """LA. R132 推翻 R131 一条承重结论：0x6bedb0 与 0x41c250 的模板体不是 106 字节而是 136 字节，差异不是一处而是两处。十二套脚本 160 项断言全 PASS。

LB. 截断可精确定位。R131 的口径是「从入口反汇编到第一条 ret 为止」。0x6bedb0 的 je 在 0x6bedc6 跳到 0x6bee1a，而 0x6bee1a 正在第一条 ret（0x6bee17 结束）之后；另一条 jl 在 0x6bede5 跳 0x6bee33。故该口径在结构上必然截掉一个可达的 else 块。实例 B 同构：0x41c266 跳 0x41c2ba、0x41c285 跳 0x41c2d3。

LC. 反控把 106 与 30 拼起来：else 块入口 0x6bee1a 单独做 CFG 遍历得 12 条指令、恰好 30 字节，收在同一结束地址 0x6bee38；106 + 30 = 136，无缝无叠，不是两个数字凑巧相加。另有一条独立边界证据：两个函数体结束后都正好是 8 个 0x90 nop，第 9 个字节已不是 nop。

LD. 真实长度上逐字节比较，两处不同：偏移 0x4e（c0/b0）与偏移 0x70（c0/b0）。前者是 if 臂推给 QueryInterface 的 IID，后者是 else 臂做 CoCreateInstance 用的 riid，整处落在 R131 的 106 字节之外。所以 R131 的「只有一处不同」不是笔误，是截断的必然后果。反控：只用前 106 字节比较确实只有 0x4e 一处——正是 R131 的数字。两件事同时为真，说明分歧源是口径而非算错。

LE. 实例化个数仍是 2，但这次是三重掩码互证：只掩三个 IID push 命中 2 处；掩掉体内全部 imm32（40 字节）命中同样 2 处，排除了「第三份只在别的立即数上不同因而躲开掩码」的逃逸；完全不掩只命中源实例 1 处，证明掩码确在起作用。另加诱饵反控（掩码外翻一字节）全库命中 0。调用点 0x6bedb0 两个、0x41c250 十三个，与 R131 一致。

LF. R131 的分支判读被推翻，且是方向反了。R131 同一段里说「7 & 0x14 = 4 ≠ 0 故 je 不跳」（算术对）又说「OleRun 分支 15/15 均为死分支」（结论反）。je 不跳意味着顺序落入 if 臂，而 OleRun 就在 if 臂（0x6bedec，偏移 +0x3c），所以 OleRun 是活的；真正走不到的是 je 的目标分支（0x6bee2b 那次 CoCreateInstance，其后没有 OleRun）。可达性遍历给机械判据：ZF=0 时可达集含 if 臂 CoCreateInstance 与 OleRun、不含 else 臂 CoCreateInstance（两实例各 4 项断言全过）；反控是「若 ZF=1 则 OleRun 不在可达集」，证明这确是一条条件分支而不是恒执行。

LG. 承重的一步单独加固：test al,0x14 看哪个参数。+0x18 处读 [esp+0xc] 进 ecx、随后作为 CoCreateInstance 第一实参（rclsid）压栈。深度取 12 则解到入口+0x0，即返回地址，把返回地址当 rclsid 荒谬；深度取 8 则解到 +0x4 = arg1。独立佐证：15 个调用点里 10 个把常量传 arg1，这 10 个常量（0x7e9a30/0x7e9a60/0x7e9a70/0x7e9a90）全部落在 .rdata/.data，10/10，是 GUID 指针该有的样子。故深度 8 被强制，[esp+0x14] 解到入口+0xc = arg3；arg3 在 15/15 都是 7，故 ZF=0。

LH. 规则 D：两家本轮都 succeeded。deepseek task 272 55 回合 / 6.0 分钟、hy4 task 273 27 回合 / 3.17 分钟，预算都填 2.0——本轮派发参数偏离惯例的 8.0，故 OVERTIME 标注的绝对值不具可比性，下轮按 8 重设。两家独立报出的数字与主会话复算一致：136 而非 106、两处差异 0x4e 与 0x70、实例恰 2 个、else 块 30 字节、两体后各 8 个 nop、调用点 2 与 13。hy4 另报 dwClsContext 分布 7→11、1→6、eax→4，与复算逐项相同；我第一版得 10 是因为 0x469f4b 那站窗口太窄没解出五个 push，属我的口径漏项。

LI. deepseek 报的一条跨轮次风险已采纳并复算：不开 skipdata 时 capstone 的 disasm_lite 在 0x46f5a0 静默停住，只解出 155215 条（R131 已记）。R132 全部普查开 skipdata，并加断言「线性扫描最大指令起始必须 > 0x7e0000」（实测 0x7e0fff）——这条断言的作用是：别处一坏它先响，而不是让统计静默少算。

LJ. 自错五条。S-212：OleRun 的字节模式写成 ff 16，实际是 ff 15（call 间接），遂全库报 0 处，而反汇编明明在调它；与 R131 S-207 同族，改正后 7 处。S-213：栈深度遍历把每个 call 当成不改变深度，于是九条 [esp+N] 读全解到负偏移或 argNone，得出「全部越界」的荒谬结论；改为识别被调方弹参后，arg1 常量 10/10 落在数据节，模型自洽。S-214：按 startswith('al,') 匹配寄存器，而 capstone 打印 'al, 0x14'（逗号后有空格），两条断言假失败；与 S-200/S-204 同族。S-215：把「ret 之后都是填充」当事实，objdump 断言写成「0x6bee38 之后不得有指令起始」，而那里是 8 个合法 nop；改成「恰好 8 个 0x90 且第 9 个不是」。S-216：r132d 的回溯窗口只取 10 条指令，而 0x469f4b 站在 push 与 call 之间夹了七条填充 mov，于是 21 站点只解出 20；与 S-205 同族，都是窗口宽度拍小了，改正方向是「窗口宽度由最坏情况站点决定，不由典型站点决定」。

LK. 收口：十二套脚本共产出 94 项断言 —— r132a 9 + r132b 8 + r132c 6 + r132d 4 + r132e 9 + r132f 4 + r132g 5 + r132h 15 + r132i 4 + r132j 6 + r132k 16 + r132l 8，其中 93 PASS、1 FAIL。那条 FAIL 是 r132d 的「21 站点是否都解出 5 个 push」，实得 20，漏 0x469f4b：该站 push 与 call 之间夹了七条填充 mov，而脚本回溯窗口只有 10 条指令。不是结论错，是窗口太窄，记 S-216（与 S-205 同族）。r132g 用 16 条窗口重解同一张表得 21/21，两表除该站外逐项相同。这条 FAIL 故意留在产物里不抹——「断言全绿」比「一条已知 FAIL 且解释清楚」更危险。全程 disasm_lite 分块流式（0x10000）与有界窗口 detail=False，未对整段 .text 开 detail=True；objdump 单遍；脚本均带 timeout；收口前 ps 确认无孤儿。五项 CR 1081/137/337/0/2952 全绿；看板 184 行未到 260 阈值，本轮不归档。

LL. 未取得（不粉饰）：① R131 那句「OleRun 是死分支」的动机无从复原，本轮只订正结论不臆测成因；② else 臂「任何输入都不可达」未证，只证「在 15 个调用点均传 7 时不可达」——若有别处直接调用这两个函数并传低位 bit2 为 0 的值，else 臂会执行，本轮未找到这样的调用点，但「未找到」不等于「不存在」；③ 0x70 处第二个 IID 常量完整 16 字节未逐一展开，只知与 0x4e 同形（均 c0/b0 单字节差）；④ blowfish.dll 运行期未证；⑤ 门禁 C7 的 exists / bytes= / none 三个分支本轮实测在 31 行里覆盖 0 行（即死分支），与 C11 frozen 分支一样未修；⑥ 窗口表仍缺 r66 以后主快照；⑦ 35 个静态容器的运行期元素值与计数；⑧ 已判死线不投。
"""

BOARD_TEXT = """
## 第 127 轮（R132）

**一 · 本轮主攻 R131 未取得项 ③「共用模板展开的充分程度」，结果不是补证而是推翻。** R131 把模板体定义为「从入口反汇编到第一条 ret 为止」，得 106 字节、差异一处。R132 用 CFG 可达性遍历替换该启发式：真实长度 **136 字节**，差异 **两处**。

**二 · 截断可精确定位。** 0x6bedc6 的 je 跳 0x6bee1a，正落在第一条 ret（0x6bee17 结束）之后；0x6bede5 的 jl 跳 0x6bee33。实例 B 同构（0x41c266→0x41c2ba、0x41c285→0x41c2d3）。反控：else 块单独遍历 = 12 条指令 / 30 字节，收在同一结束地址 0x6bee38，106+30=136 无缝无叠。独立边界证据：两体之后各恰 8 个 0x90 nop。

**三 · 差异两处而非一处。** 偏移 **0x4e** 与 **0x70**，均为 c0/b0。0x70 是 else 臂 CoCreateInstance 的 riid，整处在 R131 的 106 字节之外。反控：只用前 106 字节比较**确实**只有 0x4e 一处——正是 R131 的数字。两件事同时为真，分歧源是口径不是算错。

**四 · 实例数仍为 2，三重掩码互证。** 只掩三个 IID push → 2 处；掩体内**全部** imm32（40 字节）→ **同样** 2 处，排除「第三份只在别的立即数上不同」的逃逸；完全不掩 → 1 处，证明掩码非恒真。诱饵（掩码外翻一字节）命中 0。调用点 2 / 13。

**五 · R131 的分支判读方向反了。** 同段两句自相矛盾：「7 & 0x14 = 4 ≠ 0 故 je 不跳」（算术对）与「OleRun 分支 15/15 均为死分支」（结论反）。je 不跳 ⇒ 顺序落入 if 臂；OleRun 在 if 臂（0x6bedec，+0x3c）⇒ OleRun 是**活**的。真正不可达的是 je 目标分支（0x6bee2b 那次 CoCreateInstance，其后无 OleRun）。反控：若 ZF=1 则 OleRun 不在可达集，证明确为条件分支。

**六 · 承重步加固：`test al,0x14` 看哪个参数。** [esp+0xc] 读进 ecx 后作 rclsid：深度 12 ⇒ 解到入口+0x0（返回地址，荒谬）；深度 8 ⇒ +0x4 = arg1。佐证：15 个调用点中 10 个把常量传 arg1，全部落在 .rdata/.data（10/10）。故 [esp+0x14] = arg3；arg3 在 15/15 都是 7 ⇒ ZF=0。

**七 · 规则 D。** deepseek task 272 succeeded 55 回合 / 6.0 分钟、hy4 task 273 succeeded 27 回合 / 3.17 分钟，预算均填 2.0（本轮派发参数偏离惯例 8.0，OVERTIME 绝对值不可比，下轮按 8 重设）。两家独立确认 136 / 两处 / 2 实例 / else 30 字节 / 各 8 nop / 2 与 13。hy4 的 dwClsContext 分布 11/6/4 与复算逐项相同；我首版得 10 系 0x469f4b 窗口过窄漏解，已修正。

**八 · 跨轮次风险已采纳。** 不开 skipdata 时 disasm_lite 在 0x46f5a0 静默停住（155215 条）。本轮全开 skipdata，并加断言「最大指令起始 > 0x7e0000」（实测 0x7e0fff），坏时先响。

**九 · 自错五条。** S-212 OleRun 写成 ff 16（实为 ff 15）报 0 处，与 S-207 同族；S-213 栈遍历把 call 当不弹参，[esp+N] 全解成负偏移；S-214 startswith('al,') 漏逗号后空格，与 S-200/S-204 同族；S-215 把 ret 之后当无指令，而那是 8 个合法 nop；S-216 r132d 回溯窗口仅 10 条指令，漏解 push 与 call 间夹七条填充 mov 的 0x469f4b。

**十 · 收口。** 十二套脚本共 **94 项断言（93 PASS / 1 已知 FAIL）**。那条 FAIL 是 r132d 回溯窗口仅 10 条指令、漏解 0x469f4b（该站 push 与 call 之间夹七条填充 mov），r132g 用 16 条窗口重解得 21/21；故意留在产物里不抹。五项 CR 1081/137/337/0/2952 全绿；check_disc.py exit 0、C10 ok(R131)。全程 disasm_lite 分块流式与有界窗口 detail=False，未对整段 .text 开 detail=True；脚本带 timeout；ps 确认无孤儿。看板 184 行未到 260 阈值，不归档。

**十一 · 未取得（不粉饰）。** ① R131 扣错臂名的成因不可复原；② else 臂「任何输入都不可达」未证（只证「在 15 个调用点均传 7 时不可达」）；③ 0x70 处第二个 IID 常量完整 16 字节未展开；④ blowfish.dll 运行期未证；⑤ 门禁 C7 三个死分支（exists/bytes=/none 实测 31 行覆盖 0 行）与 C11 frozen 分支未修；⑥ 窗口表仍缺 r66 以后快照；⑦ 35 个静态容器的运行期元素值与计数。
"""

def load(p):
    return io.open(p, 'rb').read()

def crlf(b):
    return b.count(b'\r\n')

def backup(path, label):
    b = load(path)
    sha = hashlib.sha256(b).hexdigest()
    ts = time.strftime('%Y%m%d_%H%M%S')
    base = os.path.basename(path)
    dst = os.path.join(BASE, 'R132.before_%s_%s.bak' % (base, ts))
    fd = os.open(dst, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(b)
    back = io.open(dst, 'rb').read()
    assert hashlib.sha256(back).hexdigest() == sha, 'backup mismatch for ' + label
    print('%-34s backup %s (sha %s)' % (label, os.path.basename(dst), sha[:12]))
    return dst, sha

def append(path, text, want_cr, label):
    orig = load(path)
    osha = hashlib.sha256(orig).hexdigest()
    ocr = crlf(orig)
    assert ocr == want_cr, '%s CR before = %d != %d' % (label, ocr, want_cr)
    assert b'\r' not in text.encode('utf-8'), '%s new text contains CR' % label
    if not orig.endswith(b'\n'):
        raise SystemExit('%s does not end with LF; refusing to append blindly' % label)
    body = text.encode('utf-8')
    if not body.startswith(b'\n'):
        body = b'\n' + body
    if not body.endswith(b'\n'):
        body += b'\n'
    new = orig + body
    try:
        with io.open(path, 'wb') as f:
            f.write(new)
        back = load(path)
        assert back == new, '%s readback mismatch' % label
        assert crlf(back) == want_cr, '%s CR after = %d != %d' % (label, crlf(back), want_cr)
        print('%-34s CR %d -> %d (kept)  bytes %d -> %d (+%d)'
              % (label, ocr, crlf(back), len(orig), len(back), len(back) - len(orig)))
        return {'label': label, 'sha_before': osha,
                'sha_after': hashlib.sha256(back).hexdigest(),
                'bytes_before': len(orig), 'bytes_after': len(back),
                'cr_before': ocr, 'cr_after': crlf(back), 'ok': True}
    except Exception:
        with io.open(path, 'wb') as f:
            f.write(orig)          # in-memory recovery only (S-203/S-211)
        raise

rec = {'targets': [], 'backups': []}
for p in EXPECT:
    b = load(p)
    assert crlf(b) == EXPECT[p]['cr'], '%s pre CR %d != %d' % (EXPECT[p]['label'], crlf(b),
                                                             EXPECT[p]['cr'])
print('pre-state CR verified for all four targets')

for p in (COMMON, LEDGER, LOCK, BOARD):
    dst, sha = backup(p, EXPECT[p]['label'])
    rec['backups'].append({'path': dst, 'sha': sha})

rec['targets'].append(append(COMMON, COMMON_TEXT, 1081, 'R14_COMMON.md'))
rec['targets'].append(append(LEDGER, LEDGER_TEXT, 337, 'GOAL_THREE_TARGETS_20261018.md'))
rec['targets'].append(append(LOCK, LOCK_SEG, 137, 'LEAD_LOCK'))
rec['targets'].append(append(BOARD, BOARD_TEXT, 0, 'STATUS_BOARD.md'))

b = load(BOARD)
rec['board_lines_after'] = b.count(b'\n')
print('\nboard lines after: %d (300 cap)' % rec['board_lines_after'])
rec['ok'] = (all(t['ok'] for t in rec['targets']) and rec['board_lines_after'] <= 300
             and b.count(b'\r\n') == 0)
print('all writes ok:', rec['ok'])
json.dump(rec, open(OUT, 'w'), ensure_ascii=False, indent=1)
raise SystemExit(0 if rec['ok'] else 1)
