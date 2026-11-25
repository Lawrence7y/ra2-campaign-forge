# -*- coding: utf-8 -*-
"""R125: append the round record to the four documents.

Discipline for every target: wx-exclusive backup -> assert old sha256 and CR
against the recorded baseline -> assert the new text carries no backtick ->
single write -> readback verification.
"""
import io, os, hashlib, datetime, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
RC = os.path.join(R14, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD = os.path.join(R14, 'STATUS_BOARD.md')

EXPECT = {
    RC:  ('0525aef0f6f8780d', 1081),
    LED: ('a87bf73f369bac20', 337),
    LOCK: ('c7259b4fd9c7d674', 137),
    BRD: ('066f29dc8113fb68', 0),
}

TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

SEC_RC = '''
## 2.129 R125 台账：0x7f7c70 与 0x7f7c80 由「使用侧参数角色」分开，并把 0x7f7c70 从排除法升级为正向证据

R125 只做静态字节测量，全部结论可从 gamemd.exe（sha256 73201cc0...fcf67476）复算。本轮不引外部头文件当证据，最后一段专门说明哪些结论必须靠外部约定才能定死。

**一 · 起点与两处常数**

四条地址的 16 字节实测：0x7f7c70 与 0x818858 都是 0000010C-0000-0000-C000-000000000046，0x7f7c80 与 0x820270 都是 00000109-0000-0000-C000-000000000046，两两成对相同。相邻的 0x817bc0 是 00000000-0000-0000-C000-000000000046，即 IID_IUnknown 的一份数据拷贝；它前面是两张 RTTI 类名字符串 .?AVFootClass@@ 与 .?AVAircraftClass@@，所以这一片是 GUID 池而不是结构体。

形式普查（mov edi 立即数落在 QI 模板内 / push 立即数）：0x7f7c70 是 4 与 0，0x7f7c80 是 4 与 60，0x818858 是 0 与 16，0x820270 是 0 与 8。独立用字节锚点 BF imm32 与 68 imm32 复算，四组数字逐个相同。0x7f7c70 的形式 B 是空集，这一条很重要：对它的任何结论都只能由 .data 那份拷贝 0x818858 的 16 个观测点承担，不能假装 rdata 有调用点。

**二 · 本轮换的判据：不是「与 OLE 共现」，是「QI 结果占第几个参数」**

R125 起初（r125a/r125b）用的判据是「push 该 IID 的函数体里是否出现对 0x7e15f4 / 0x7e15f8 的调用」。这只是人群关联，它无法说明 QI 出的那个指针是否就是交给 OLE 的参数——一个函数体可以 push 好几个对象，只有一个来自 QI。

本轮改测更强的局部关系：在每次 push 该 IID 处找到 QueryInterface 调用，取它的出参栈槽 K；QueryInterface 是 stdcall，调用后 ESP 与调用前相同，所以在调用后读 [esp + K] 与调用前 lea 命名的是同一个槽，不需要任何栈帧模型（这正好避开 R125a 六次自伤里的栈槽基准错）。

结果：35 处 0x7f7c80 站点里，QI 结果被作为 OleSaveToStream 的第 0 个参数传入，且从读到 push 之间该寄存器没有任何重写（35/35，零覆写）。0x820270 的 8 个站点经栈槽中转（CComPtr 惯用法）后全部到达 OleSaveToStream，其中 7 处可证明是第 0 个参数，1 处（0x4b6313）只证到「到达同一调用」，未能归位，如实留缺。0x818858 的 16 个站点一处都不到达 OleSaveToStream。

**三 · 把 0x7f7c70 从排除法升级为正向证据**

R124 只能说这两个常量「三条内部记录完全相同，分不开」。本轮给出可证伪的正向预测并实测：

若 0000010C 是 IPersist，则由 R124 已证的 NumContainedBases 链（IUnknown 0 小于 IPersist 1 小于 IPersistStream 2）与 IUnknown 方法数 3，IPersist 只加一个方法 GetClassID，它必然落在虚表字节偏移 0xc（slot 3），且 IPersist 句柄不应被调过 0xc。

实测：0x818858 的句柄在 0x42cab5 处被 call dword ptr [eax + 0xc] 调用（字节 ff 50 0c），且从不越过 0xc（另有 0x42cabf 的 [edx + 8]，即 slot 2 Release）。反方向：0x7f7c80 的 60 个句柄使用点只出现 offset 8（Release），一次都没有出现 0xc。

也就是说，两个常量在「使用侧的可调用槽位集合」上不可互换：只有 10C 那个被当作带 slot 3 的接口调用，109 那个从未。这条比 R124 的三条记录强，因为它是单向的、可失败的预测，而 R124 那三条在构造上对称。

必须同时说清上限：这条记录确定的是「哪个常量是更窄的那个接口（多一个 slot 3）」，它并不从字节里读出 IPersist 这三个字的拼写。方向仍由外部 GUID 约定补上（00000109 是 IPersistStream、0000010C 是 IPersist），这一点与异族审计员的判断一致，本轮不粉饰。

**四 · 一处必须排除的伪证据（自错 S-150）**

0x42cac6 处有 call dword ptr [eax + 0x84]，粗看像「10C 句柄被调过 slot 0x21」。实测 0x42cac2 是 mov eax, dword ptr [esi]，eax 已被换成另一个对象的虚表，esi 不是 10C 的出参对象。若把这条算进 10C，会得出「10C 是高槽位接口」的反向结论。本级同族伪证据另有三处，全部按来源追踪排除。

**五 · 跨家族（规则 D）**

审计员 hy4 task 249 succeeded，28 回合 / 3.32 分钟，预算 8.0，无 OVERTIME。报告落盘 _r125/audit/r125_audit_hy4.md（111 行，零反引号）。其数字我逐条用独立脚本复算（r125h 11 项）：形式 A 4/4/0/0 一致、形式 B 0/60/16/8 一致、OLE 调用总量 43 与 8 一致、四个双 IID 分派器的零调整字节 89 18 / 89 02 / 89 18 / 89 10 一致、0x42cab5 的 ff 50 0c 与 0x42cac6 的 ff 90 84 00 00 00 及 0x42cac2 的 8b 06 一致、反控 0x7f7cd0 为 9、0x7f7c90 为 56 一致。全部一致，无一条分歧。

审计员有一处判断比我的原稿更严格且我采纳：它指出「与 OLE 共现」不能单独定身份，方向靠外部 GUID 约定。本轮第二节的参数角色分析是对这一批评的正面回应——它把关联升级成了参数位置关系，但仍然不能读出字符串，所以结论上限的表述按它的口径写。

审计员另指出若有人声称「0x820270 从不进 OLE」那是错的，实测 8/8 全进。我复核后确认它对的：这正是本轮 G5 与 G3b 两条断言的来源，同时把「到达」与「可证明在第 0 参数」分开记，不再混为一谈。

**六 · 本轮修掉的既有产物缺陷（两处，都在我自己的半成品里）**

其一，r125c 的 S3 断言写反了：它要求「每个查 0000010C 的函数体也必须查 00000109」，而实测是单向的相反方向（16/16 个 10C 体都不查 109）。这是我写断言时把蕴含方向搞反（S-145），不是二进制事实。已改为正向表述并给出精确恒等式。

其二，r125c 的 S2b 与 N2 用了凭感觉的阈值（多数过半、大于 100），已分别改成精确恒等式 n_alone == n109 与「两个人群大小不相等」，不再有自由参数。

**七 · 断言与收口**

r125a 24 + r125b 9 + r125c 10 + r125d 16 + r125e 9 + r125f 9 + r125g 9 + r125h 11 = 97 项全 PASS。全程用 disasm_lite 流式线性扫描，未对整段 .text 开 detail=True；单点目标用窗口反汇编。脚本均带 timeout；收口前确认无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0（GATE_VER 仍 R124，本轮不改门禁）。

**八 · 未取得（不粉饰）**

1) 两个常量的接口名字符串仍不由字节给出，须外部头文件或动态采样（win-main 本次 OFFLINE，未做）。2) 0x4b6313 一处 0x820270 站点只证到「到达 OleSaveToStream」，未能证明是第 0 参数，留缺一格。3) 0x7f7c70 的 rdata 常量形式 B 为空集，其结论全部压在 .data 拷贝上，两份拷贝对齐是额外假设。4) 0x7e9b40 仍与这对不可分。5) 0x7f7cf0 在 IStream 与 ISequentialStream 之间仍不可分。6) 0x7e36c0 与 0x7e9b20 的出参偏移仍解不出。7) 35 个静态容器的运行期元素值与计数。8) 共用模板展开的充分证明。9) 门禁 C11 其余四处永远通过子项、五条不可能行未裁定、窗口表未扩。
'''

SEC_LED = '''
## §1179 R125 台账：0x7f7c70 与 0x7f7c80 由使用侧参数角色分开，并把 0x7f7c70 升级为正向证据

R125 全部为静态字节测量，可从 gamemd.exe（sha256 73201cc0...fcf67476）复算。

**常数与普查**：0x7f7c70 与 0x818858 同为 0000010C-0000-0000-C000-000000000046，0x7f7c80 与 0x820270 同为 00000109-0000-0000-C000-000000000046，两两成对相同；相邻 0x817bc0 是 IID_IUnknown 的拷贝，前接两张 RTTI 类名，这一片是 GUID 池。形式 A（QI 模板内 mov edi）与形式 B（push）分别为 4/0、4/60、0/16、0/8，用 BF imm32 与 68 imm32 字节锚点独立复算逐个相同。0x7f7c70 的 push 是空集，其对结论只能靠 .data 拷贝的 16 个观测点。

**判据升级**：R125 起初用「函数体内是否与 OLE 共现」，那只是人群关联。本轮改测局部参数角色：取 QueryInterface 的出参栈槽 K；stdcall 返回后 ESP 与调用前相同，故调用后读 [esp+K] 与调用前 lea 命名同一槽，无需栈帧模型。结果 35 处 0x7f7c80 站点的 QI 结果作为 OleSaveToStream 第 0 参数传入，且读与 push 之间零寄存器重写（35/35）。0x820270 的 8 站经 CComPtr 栈槽中转全部到达 OleSaveToStream，其中 7 站可证为第 0 参数，1 站（0x4b6313）未归位，留缺。0x818858 的 16 站零到达。

**正向证据**：按 R124 已证的 ncb 链（IUnknown 0 小于 IPersist 1 小于 IPersistStream 2）与 IUnknown 方法数 3，IPersist 只加 GetClassID，必落偏移 0xc。实测 0x818858 句柄在 0x42cab5 被 call [eax+0xc]（字节 ff 50 0c）调用且从不越过 0xc；反向 0x7f7c80 的 60 个使用点只有 offset 8，一次没有 0xc。故两个常量在使用侧槽位集合上不可互换，只有 10C 被当作带 slot 3 的接口调用。这比 R124 三条对称记录强，因为它是单向可失败预测。上限：它确定的是「哪个更窄、多一个 slot 3」，不读出字符串拼写；方向仍由外部 GUID 约定补上。

**必须排除的伪证据**：0x42cac6 的 call [eax+0x84] 粗看像 10C 被调过 slot 0x21，实测 0x42cac2 是 mov eax,[esi]，eax 已换成另一对象虚表，esi 不是 10C 出参对象；算进去会得出反向结论。

**跨家族**：审计员 hy4 task 249 succeeded，28 回合 / 3.32 分钟 / 无 OVERTIME，报告 111 行零反引号。数字逐条复算（r125h 11 项）全部一致：形式 A 4/4/0/0、形式 B 0/60/16/8、OLE 总量 43 与 8、四个双 IID 分派器零调整字节、0x42cab5 ff 50 0c、0x42cac6 ff 90 84 00 00 00、0x42cac2 8b 06、反控 9 与 56。审计员指出「共现」不能单独定身份，本轮第二节的参数角色分析即对此的正面回应；它另指出「0x820270 从不进 OLE」若有人这么说那是错的（实测 8/8 全进），复核确认它对的。

**修掉两处自有半成品缺陷**：r125c 的 S3 断言把蕴含方向写反（要求 10C 体也查 109，实测 16/16 相反），已改为正向；S2b 与 N2 的凭感觉阈值改成精确恒等式与人群不等判据。

**断言**：r125a 24 + r125b 9 + r125c 10 + r125d 16 + r125e 9 + r125f 9 + r125g 9 + r125h 11 = 97 项全 PASS。未对整段 .text 开 detail=True；脚本带 timeout；无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0。

**未取得**：① 接口名字符串不由字节给出（win-main OFFLINE，未做动态采样）；② 0x4b6313 未归位；③ 0x7f7c70 结论全压 .data 拷贝；④ 0x7e9b40 仍不可分；⑤ 0x7f7cf0 在 IStream 与 ISequentialStream 间；⑥ 0x7e36c0 与 0x7e9b20 偏移解不出；⑦ 35 个容器运行期值；⑧ 共用模板充分证明；⑨ 门禁 C11 剩余子项与不可能行。
'''

SEC_LOCK = '''
FZ. R125 主攻 R124 台账未取得项①：0x7f7c70 与 0x7f7c80 的定名。八套脚本 97 项断言全 PASS，全部可从字节复算。

GA. 起点实测：0x7f7c70 与 0x818858 同为 0000010C-0000-0000-C000-000000000046，0x7f7c80 与 0x820270 同为 00000109-0000-0000-C000-000000000046。相邻 0x817bc0 是 IID_IUnknown 的拷贝，前接 .?AVFootClass@@ 与 .?AVAircraftClass@@ 两张 RTTI 类名，故这一片是 GUID 池。形式 A / 形式 B 为 4/0、4/60、0/16、0/8，用 BF imm32 与 68 imm32 字节锚点独立复算逐个相同。0x7f7c70 的 push 是空集 —— 这条很硬：对它的一切结论只能由 .data 拷贝的 16 个观测点承担。

GB. 判据换代。R125 起初（r125a/b）用「push 该 IID 的函数体里是否出现 OLE 调用」，那只是人群关联，无法说明 QI 出的指针是否就是交给 OLE 的那个参数。本轮改测局部参数角色：在 push 处取 QueryInterface 的出参栈槽 K；stdcall 返回后 ESP 与调用前相同，故调用后读 [esp + K] 与调用前 lea 命名同一槽，不需要栈帧模型（正好避开 R125a 栈槽基准错那类自伤）。

GC. 结果：0x7f7c80 的 35 处站点，QI 结果作为 OleSaveToStream 第 0 个参数传入，且读到 push 之间该寄存器零重写（35/35）。0x820270 的 8 站经 CComPtr 栈槽中转全部到达 OleSaveToStream，其中 7 站可证为第 0 参数，1 站（0x4b6313）只证到到达、未归位，如实留缺。0x818858 的 16 站零到达。

GD. 把 0x7f7c70 从排除法升级为正向证据。可证伪预测：若 0000010C 是 IPersist，由 R124 已证 ncb 链（IUnknown 0 小于 IPersist 1 小于 IPersistStream 2）与 IUnknown 方法数 3，IPersist 只加 GetClassID，必落虚表偏移 0xc，且不应被调过 0xc。实测 0x818858 句柄在 0x42cab5 被 call dword ptr [eax + 0xc] 调用（字节 ff 50 0c），从不越过 0xc；反向 0x7f7c80 的 60 个使用点只出现 offset 8（Release），一次都没有 0xc。两个常量在使用侧槽位集合上不可互换 —— 这比 R124 那三条对称记录强，因为它单向且可失败。

GE. 上限必须写清：这条记录确定的是「哪个常量是更窄的那个、多一个 slot 3」，它并不从字节里读出 IPersist 三个字的拼写。方向仍由外部 GUID 约定补上（109 是 IPersistStream、10C 是 IPersist）。这一点与异族审计员一致，不粉饰。

GF. 排除一处会翻转方向的伪证据（S-150）：0x42cac6 有 call dword ptr [eax + 0x84]，粗看像「10C 被调过 slot 0x21」。实测 0x42cac2 是 mov eax, dword ptr [esi]，eax 已被换成另一对象的虚表，esi 不是 10C 的出参对象。算进去就会得出「10C 是高槽位接口」的反向结论。同族伪证据本轮另排除三处，全部按来源追踪而非按窗口距离。

GG. 规则 D：审计员 hy4 task 249 succeeded，28 回合 / 3.32 分钟 / 预算 8.0 / 无 OVERTIME，报告 _r125/audit/r125_audit_hy4.md 共 111 行、零反引号。数字逐条独立复算（r125h 11 项）全部一致：形式 A 4/4/0/0、形式 B 0/60/16/8、OLE 调用总量 43 与 8、四个双 IID 分派器的零调整字节 89 18 / 89 02 / 89 18 / 89 10、0x42cab5 的 ff 50 0c、0x42cac6 的 ff 90 84 00 00 00、0x42cac2 的 8b 06、反控 0x7f7cd0 为 9 与 0x7f7c90 为 56。无一条分歧。

GH. 审计员有两条批评我采纳。其一，「与 OLE 共现」不能单独定身份，方向靠外部约定 —— 本轮 GC 的参数角色分析正是对此的正面回应，它把关联升级为参数位置关系，但仍读不出字符串，故上限按它的口径写。其二，若有人声称「0x820270 从不进 OLE」那是错的，实测 8/8 全进；我复核后确认它对的，并把「到达」与「可证明在第 0 参数」分开记（G3 与 G3b 两条断言），不再混为一谈。

GI. 修掉两处自有半成品缺陷。其一，r125c 的 S3 断言把蕴含方向写反：它要求「每个查 0000010C 的函数体也必须查 00000109」，而实测是相反方向的单向结构（16/16 个 10C 体都不查 109）。这是写断言时方向搞反（S-145），不是二进制事实；已改为正向并给出精确恒等式。其二，r125c 的 S2b 与 N2 用了凭感觉的阈值（过半、大于 100），已改为精确恒等式 n_alone == n109 与「两个人群大小不相等」，不再有自由参数。

GJ. 断言与收口：r125a 24 + r125b 9 + r125c 10 + r125d 16 + r125e 9 + r125f 9 + r125g 9 + r125h 11 = 97 项全 PASS。全程 disasm_lite 流式扫描，未对整段 .text 开 detail=True，单点目标用窗口反汇编；脚本带 timeout；收口前确认无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0（GATE_VER 仍 R124，本轮不改门禁）。

GK. 未取得（不粉饰）：① 两个常量的接口名字符串仍不由字节给出，须外部头文件或动态采样（win-main 本次 OFFLINE，未做）；② 0x4b6313 一处 0x820270 站点只证到到达 OleSaveToStream，未证第 0 参数，留缺一格；③ 0x7f7c70 的 rdata 形式 B 为空集，结论全压在 .data 拷贝上，两份拷贝对齐是额外假设；④ 0x7e9b40 仍与这对不可分；⑤ 0x7f7cf0 在 IStream 与 ISequentialStream 间仍不可分；⑥ 0x7e36c0 与 0x7e9b20 的出参偏移仍解不出；⑦ 35 个静态容器的运行期元素值与计数；⑧ 共用模板展开的充分证明；⑨ 门禁 C11 其余四处永远通过子项、五条不可能行未裁定、窗口表未扩。
'''

SEC_BRD = '''
## 🟢 R17 第 125 轮（2026-11-25 01:0x–02:0x）· 0x7f7c70 与 0x7f7c80 用「QI 结果占第几个参数」分开，并把 0x7f7c70 从排除法升级为单向可失败的正向证据

### 一 · 起点

R124 留下的悬案是 0x7f7c70 与 0x7f7c80 定不了名，理由很硬：类集合相同、QI 出参偏移都 0、RTTI 顺序恒定。本轮先复测常数本身：0x7f7c70 与 0x818858 同为 0000010C-0000-0000-C000-000000000046，0x7f7c80 与 0x820270 同为 00000109-0000-0000-C000-000000000046，两两成对相同。相邻 0x817bc0 是 IID_IUnknown 的拷贝，前接 .?AVFootClass@@ 与 .?AVAircraftClass@@ 两张 RTTI 类名，所以这一片是 GUID 池。

形式普查 4/0、4/60、0/16、0/8（QI 模板内 mov edi 与 push 立即数），用 BF imm32 与 68 imm32 字节锚点独立复算逐个相同。其中一条很硬：0x7f7c70 的 push 是空集，对它的一切结论只能由 .data 拷贝 0x818858 的 16 个观测点承担。

### 二 · 判据为什么必须换

本轮前半段（r125a/r125b）沿用的判据是「push 该 IID 的函数体里是否出现对 OleSaveToStream / OleLoadFromStream 的调用」。这只是人群关联：一个函数体可以 push 好几个对象，只有一个来自 QueryInterface，共现并不能说明交出去的就是 QI 那个指针。

改测更强的局部关系：在 push 处取 QueryInterface 的出参栈槽 K；QueryInterface 是 stdcall，返回后 ESP 与调用前相同，所以在调用后读 [esp + K] 与调用前 lea 命名的是同一个槽 —— 不需要任何栈帧模型，正好避开 R125a 那六次自伤里的栈槽基准错。

结果按站点数给：0x7f7c80 的 35 处，QI 结果作为 OleSaveToStream 的第 0 个参数传入，且从读到 push 之间该寄存器零重写（35/35）。0x820270 的 8 站经 CComPtr 栈槽中转全部到达 OleSaveToStream，其中 7 站可证为第 0 参数，1 站（0x4b6313）只证到到达、未归位。0x818858 的 16 站零到达。

### 三 · 把 0x7f7c70 从排除法变成正向证据

R124 那三条记录在构造上就是对称的，所以永远分不开。本轮换单向预测：若 0000010C 是 IPersist，由 R124 已证的 ncb 链（IUnknown 0 小于 IPersist 1 小于 IPersistStream 2）加 IUnknown 方法数 3，IPersist 只加 GetClassID，必落虚表偏移 0xc，且不应被调过 0xc。

实测站在 0x818858 一边成立：句柄在 0x42cab5 被 call dword ptr [eax + 0xc] 调用（字节 ff 50 0c），从不越过 0xc。反向也成立：0x7f7c80 的 60 个使用点只出现 offset 8（Release），一次都没有 0xc。于是两个常量在「使用侧可调用槽位集合」上不可互换 —— 这是单向且可失败的，比对称记录强。

上限写清：它确定的是哪个常量更窄、多一个 slot 3，并不从字节里读出 IPersist 三个字的拼写。方向仍由外部 GUID 约定补上（109 是 IPersistStream、10C 是 IPersist）。

### 四 · 排除一处会翻转方向的伪证据

0x42cac6 有 call dword ptr [eax + 0x84]，粗看像「10C 被调过 slot 0x21」。实测 0x42cac2 是 mov eax, dword ptr [esi]，eax 已换成另一对象的虚表，esi 不是 10C 的出参对象。算进去就会得出「10C 是高槽位接口」的反向结论。同族伪证据本轮另排除三处，全部按来源追踪而不是按窗口距离。

### 五 · 跨家族与规则 D

审计员 hy4 task 249 succeeded，28 回合 / 3.32 分钟 / 预算 8.0 / 无 OVERTIME，报告 111 行、零反引号。它的数字我逐条独立复算（r125h 11 项）全部一致：形式 A 4/4/0/0、形式 B 0/60/16/8、OLE 调用总量 43 与 8、四个双 IID 分派器的零调整字节、0x42cab5 的 ff 50 0c、0x42cac6 的 ff 90 84 00 00 00、0x42cac2 的 8b 06、反控 9 与 56。无一条分歧。

它的两条批评我采纳。一，「共现」不能单独定身份，方向靠外部约定 —— 本轮第二节就是对此的正面回应。二，若有人声称「0x820270 从不进 OLE」那是错的，实测 8/8 全进；我复核后确认它对的，并把「到达」与「可证明在第 0 参数」分开记（G3 与 G3b），不再混为一谈。

### 六 · 修掉两处自有半成品缺陷

r125c 的 S3 断言把蕴含方向写反了：它要求「每个查 0000010C 的函数体也必须查 00000109」，而实测是相反方向的单向结构（16/16 个 10C 体都不查 109）。这是写断言时方向搞反（S-145），不是二进制事实；已改为正向并给出精确恒等式。同一脚本的 S2b 与 N2 用了凭感觉的阈值（过半、大于 100），已改成精确恒等式 n_alone == n109 与「两个人群大小不相等」，不再留自由参数。

### 七 · 收口

r125a 24 + r125b 9 + r125c 10 + r125d 16 + r125e 9 + r125f 9 + r125g 9 + r125h 11 = 97 项断言全 PASS。全程 disasm_lite 流式扫描，未对整段 .text 开 detail=True；单点目标用窗口反汇编；脚本带 timeout；收口前确认无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0（GATE_VER 仍 R124，本轮不改门禁）。

### 八 · 未取得（不粉饰）

① 两个常量的接口名字符串仍不由字节给出，须外部头文件或动态采样（win-main 本次 OFFLINE，未做）。② 0x4b6313 一处 0x820270 站点只证到到达 OleSaveToStream，未证第 0 参数，留缺一格。③ 0x7f7c70 的 rdata 形式 B 为空集，结论全压在 .data 拷贝上，两份拷贝对齐是额外假设。④ 0x7e9b40 仍与这对不可分。⑤ 0x7f7cf0 在 IStream 与 ISequentialStream 间仍不可分。⑥ 0x7e36c0 与 0x7e9b20 的出参偏移仍解不出。⑦ 35 个静态容器的运行期元素值与计数。⑧ 共用模板展开的充分证明。⑨ 门禁 C11 其余四处永远通过子项、五条不可能行未裁定、窗口表未扩。
'''


def sha(b):
    return hashlib.sha256(b).hexdigest()


def append(path, text, new_cr_expected):
    old = open(path, 'rb').read()
    exp_sha, exp_cr = EXPECT[path]
    assert sha(old).startswith(exp_sha), '%s sha drift: %s' % (path, sha(old))
    assert old.count(b'\r') == exp_cr, '%s CR drift: %d' % (path, old.count(b'\r'))
    assert '`' not in text, '%s new text carries a backtick' % path
    bk = os.path.join(BK, 'r125_%s.%s.bak' % (os.path.basename(path), TS))
    fd = os.open(bk, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(old)
    assert sha(open(bk, 'rb').read()) == sha(old), 'backup mismatch'
    new = old + text.encode('utf-8')
    with open(path, 'wb') as f:
        f.write(new)
    after = open(path, 'rb').read()
    assert sha(after) == sha(new), 'readback mismatch'
    assert after.count(b'\r') == new_cr_expected, \
        '%s CR after write %d != %d' % (path, after.count(b'\r'), new_cr_expected)
    return bk, len(old), len(after)


def main():
    rows = []
    rows.append(('R14_COMMON',) + append(RC, SEC_RC, 1081))
    rows.append(('LEDGER',) + append(LED, SEC_LED, 337))
    rows.append(('LEAD_LOCK',) + append(LOCK, SEC_LOCK, 137))
    rows.append(('STATUS_BOARD',) + append(BRD, SEC_BRD, 0))
    for r in rows:
        print('%-14s backup=%s %d -> %d bytes' % (r[0], os.path.basename(r[1]), r[2], r[3]))


if __name__ == '__main__':
    main()
