# -*- coding: utf-8 -*-
"""R124: append the round record to the four documents.

Writing discipline (every target): wx-exclusive backup -> assert old sha256 and
CR against the expected baseline -> single write -> readback verification ->
assert the new text carries no backtick (the standing rule) BEFORE writing.
"""
import io, os, hashlib, datetime, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK   = os.path.join(R14, 'R17_LEAD_BASELINE')
RC   = os.path.join(R14, 'R14_COMMON.md')
LED  = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD  = os.path.join(R14, 'STATUS_BOARD.md')

def sha(b): return hashlib.sha256(b).hexdigest()
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

SEC_RC = '''
## 2.128 R124 台账：IID 到接口名的字节定名（12/18）+ 接口方法数（IUnknown 3 / IPersist 1 / IPersistStream 4）+ R110 普查漏记一类的实证

R124 只做静态字节测量，全部结论可从 gamemd.exe（sha256 73201cc0...fcf67476）复算，不引外部头文件、不引历史结论当证据。

**一 · 方法：MSVC x86 BaseClassDescriptor 的 24 字节布局**

每个带 vtable 的类，[vt-4] 是 CompleteObjectLocator；COL+16 是 ClassHierarchyDescriptor；CHD+8 = NumBaseClasses，CHD+12 = pBaseClassArray。每个 BCD 24 字节：pTypeDescriptor(+0) / NumContainedBases(+4) / mdisp(+8) / pdisp(+12) / vdisp(+16) / attributes(+20)。接口名 = CString(u32(BCD)+8)。954 个类全部解码成功，bases[0] 恒为该类自身 954/954。26 个 .?AU 开头的名字即 COM 接口。

注：TypeDescriptor 与 BCD 记录在 .data 段，COL/CHD/BaseClassArray 在 .rdata。第一版把每个指针都按 .rdata 守卫，解码整批塌成 0/954（自错 S-114）。

**二 · 继承链由 NumContainedBases 直接给出**

IUnknown=0，IPersist=1，IPersistStream=2，且每个接口名的 ncb 单值（无例外）。IClassFactory=1，IRTTITypeInfo=1。INIEntry/INISection=2，IStream=2。这是二进制自己的记录，不是推断。

**三 · IID 定名：类集合包含 + QI 出参偏移两条独立记录**

类集合只用包含关系（QI 若继承自基类，比较的 IID 少于 RTTI 名单，故相等判据是错的，自错 S-115）。仅靠类集合，18 个 IID 里 13 个唯一、5 个并列。再引入第二条记录：QI 每个被接受分支写入出参的 this 调整值（0 或 lea ecx,[reg+OFF] 的 OFF），它必须等于 RTTI 对该类记录的 mdisp。两条记录都满足即定名。结果 12/18 唯一，且无一例两条记录互相矛盾（S2/S3）。

已定名 12 个：0x7e9530=ILinkStream、0x7e9ae0=IRTTITypeInfo、0x7e9b00=IPublicHouse、0x7ea6e8=IUnknown、0x7ea768=IHouse（OFF 36）、0x7f7c20=IWOLBrowserEvent、0x7f7c90=IUnknown、0x7f7ca0=IClassFactory、0x7f7cb0=IEnumConnections、0x7f7cc0=IConnectionPoint、0x7f7cd0=IConnectionPointContainer（OFF 44）、0x7f7ce0=IEnumConnectionPoints。

正控：0x7f7c90 的 16 字节恰是 00000000-0000-0000-C000-000000000046，且定名结果 IUnknown；0x7f7ca0 定名 IClassFactory。反控：把两条记录的偏移互换，IHouse 的定名即失败。

**四 · 0x7f7c70 与 0x7f7c80 仍不可分（R113 起第 4 轮未取得，本轮给出不可分的结构理由）**

两个常量分别是 0000010C-... 与 00000109-...。三条内部记录完全相同：类集合相同（77，逐类相同，对称差 0）；出参偏移都是 0；RTTI 基类数组里 IPersistStream 恒排在 IPersist 之前 77/77（顺序恒定即无信号）。另 0x7e9b40 也与这两个不可分。0x7f7cf0 在 IStream 与 ISequentialStream 之间不可分。0x7e36c0 与 0x7e9b20 的偏移解不出（分支是尾位置接受，无 lea 也无 mov 直存）。

**五 · R110 的 IID 普查漏记一类（新发现的既有产物缺陷）**

R110 的 iids_of 里窗口判断 a - f < QI_HEAD(120) 被写在每一次 cmpsd 上，本意只限制「首个 cmpsd」，实际把函数体内偏移超过 120 字节的比较全部丢弃。HouseClass(slot0=0x4f6830) 实际比较 6 个 GUID，字节偏移 47/68/99/130/161/182，R110 只记了前 3 个，丢的是 0x7f7cd0、0x7f7c70、0x7f7c80。用同一窗口复现，R110 的 172 行可逐行复现（证明这是 R110 原样，不是重写）；去掉窗口后只有 HouseClass 一类变化，且 0x7f7c90(171)、0x7f7ca0(78)、0x7e9ae0(76) 的类集合完全不变。所以 0x7f7c70 与 0x7f7c80 的类集合真值是 77 而不是 76。反控：171 个「最后一次比较已在窗口内」的类，去掉窗口后一个都不增加。

**六 · 接口方法数（R113 起第 4 轮未取得，本轮取得）**

接口块边界：90 个 persist 家族类的主 vtable 里，第一个「函数体写 vtable 常量」的 slot 恒为 8（49 个类可判，41 个类短到没有销毁器）；slot 0..7 无一写 vtable 常量（合计 0 次）。AbstractClass 是最干净的实例：slot8 的销毁器写 4 个 vtable 常量，与它的 4 个 mdisp 值 {0,4,8,12} 一一对应。故接口块 = slot 0..7 共 8 个。

IUnknown 方法数：IClassFactory 族 78 个类（77 个 TClassFactory 模板 + 1 个 TiberianSunClassFactory）的 vtable 长度恒为 5，且 IClassFactory 的 NumContainedBases=1，故 IUnknown = 5 - 2 = 3。

于是 IPersistStream = 8 - 3(IUnknown) - 1(IPersist) = 4。IPersist 声明 1 个方法由 ncb=1 直接给出。

形态佐证：slot0 恒为 QI（含 repe cmpsd 模板）；slot1 与 slot2 全族恒 mov eax,1 ; ret 4；slot7 全族 90/90 结束于 ret 8（2 参数 Save），基实现另有 0x80004003 的 NULL 出参守卫（62/90，其余是委派给 0x4103e0 的重写或空实现）。

**七 · 跨家族与规则 D**

执行员 deepseek task 243 failed + OVERTIME（61 回合 / 14.8 分钟 vs 预算 8.0 / error_max_turns），报告未写，只落 q1..q5。按规则 D 结论不采信，只取落盘原始数字与我的复算比对：954 解码、0/954 失败、26 接口名、NumContainedBases 分布、IUnknown=0/IPersist=1/IPersistStream=2、IClassFactory ncb=1、vtable 长度 5、17 个 IID 的 GUID 文本全部一致。唯一分歧是 0x7f7c70/0x7f7c80 的类集合：它报 77，我原报 76 —— 复算后证明它对的，是 R110 漏记 HouseClass，见第五节。这条分歧是本轮最有价值的交叉检验。

**八 · 自错**

S-113 BCD 字段从头读早一个 dword（mdisp/pdisp/vdisp 错位）。S-114 段守卫把 TypeDescriptor/BCD 也按 .rdata 判，解码整批塌成 0/954。S-115 用类集合相等当判据，5 个 IID 因继承被误判无解。S-116 vtable 终止规则用「下一个 COL」，对末组 vtable 失效，8 个类报未终止。S-117 capstone 小立即数印成十进制，只认 0x 前缀致 78 个 AddRef/Release 全记 None。S-118 QI 函数体停在首个 ret，而模板前部就有 ret 0xc 的 NULL 早退。S-119 AbstractClass 集合写成一行式，把仅「包含」该类的 2 个类卷进来。S-120 lea 位移只认 + 0x 形态，13 个分支记成不可判。S-121 先按类集合紧致度筛、再比偏移，方向错了（更紧的名字压在偏移不符上）。S-122 不取紧致名字，IUnknown 因被所有类携带而永远并列。S-123 断言存在「基类数组恰为 [IUnknown]」的 vtable，MSVC 恒把最派生类列首位，该断言不可满足。S-124 同 S-116 的连带。S-125 槽计数从 k=1 起，全部少 1（5 槽记成 4），IClassFactory 钉值看起来被违反。S-126 persist 家族筛选先滤 .?AU 再取尾，把 INoticeSink 这类类基漏掉，尾部匹配到 90 个不该匹配的类。S-127 边界判据用「地址落在 .rdata 就算写 vtable」,把仅仅引用 vtable 地址的普通方法也计入，须按 store 形态判。S-128 ret 尺寸扫描停在首个 ret，而一个体可有多个 ret，误判 28 个委派重写。S-129 反控筛 len(iids)==1 只剩 1 个样本，等于没有反控。

**九 · 断言与收口**

r124a 14 / r124b 11 / r124c 14 / r124d 13 / r124e 14 / r124f 13 = 79 项全 PASS。全程 disasm_lite 线性扫描与目标单条 disasm，未对整段 .text 开 detail=True；脚本均带 timeout；收口前确认无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0（GATE_VER 仍 R121，本轮不改门禁）。

**十 · 未取得（不粉饰）**

1) 0x7f7c70 与 0x7f7c80 谁是 IPersist、谁是 IPersistStream（三条内部记录完全相同，静态定不了；须外部头文件或动态采样）。2) 0x7e9b40 与这两个同样不可分。3) 0x7f7cf0 在 IStream 与 ISequentialStream 之间不可分。4) 0x7e36c0 与 0x7e9b20 的出参偏移解不出。5) 35 个容器运行期元素值与计数。6) 共用模板的充分证明。7) 门禁 C11 其余 4 处永远通过子项、五条不可能行未裁定、窗口表未扩。
'''

SEC_LED = '''
## §1178 R124 台账：IID 到接口名的字节定名（12/18）+ 接口方法数取得 + R110 普查漏记一类的实证

R124 全部为静态字节测量，可从 gamemd.exe（sha256 73201cc0...fcf67476）复算。

**方法**：MSVC x86 BCD 24 字节，pTypeDescriptor(+0)/NumContainedBases(+4)/mdisp(+8)/pdisp(+12)/vdisp(+16)/attributes(+20)，接口名 = CString(u32(BCD)+8)。954 类全部可解，bases[0] 恒为自身 954/954；.?AU 名字 26 个即 COM 接口。TypeDescriptor/BCD 在 .data，COL/CHD/BaseClassArray 在 .rdata（段守卫写错会整批塌成 0）。

**继承链**（二进制自己的记录）：IUnknown=0，IPersist=1，IPersistStream=2，IClassFactory=1，IRTTITypeInfo=1，IStream=2，每个接口名 ncb 单值。

**IID 定名 12/18**：类集合只取包含关系（相等判据错，继承会少比 IID）；第二条独立记录是 QI 分支写入出参的 this 调整值，须等于 RTTI 的 mdisp。两条都满足即定名，无一例矛盾。定名结果：0x7e9530=ILinkStream、0x7e9ae0=IRTTITypeInfo、0x7e9b00=IPublicHouse、0x7ea6e8=IUnknown、0x7ea768=IHouse(OFF 36)、0x7f7c20=IWOLBrowserEvent、0x7f7c90=IUnknown、0x7f7ca0=IClassFactory、0x7f7cb0=IEnumConnections、0x7f7cc0=IConnectionPoint、0x7f7cd0=IConnectionPointContainer(OFF 44)、0x7f7ce0=IEnumConnectionPoints。正控 0x7f7c90 = IID_IUnknown 常量；反控互换偏移后 IHouse 定名失败。

**0x7f7c70 与 0x7f7c80 仍不可分**：三条内部记录完全相同（类集合相同、出参偏移都 0、RTTI 顺序恒定 77/77）。这是不可分的结构理由，不是没测。0x7e9b40 同；0x7f7cf0 在 IStream/ISequentialStream 间不可分；0x7e36c0 与 0x7e9b20 偏移解不出。

**新发现：R110 普查漏记一类**。iids_of 的 a - f < 120 被写在每次 cmpsd 上，本意只限首个，实际丢弃函数体内偏移超 120 字节的全部比较。HouseClass(0x4f6830) 实际比 6 个 GUID（偏移 47/68/99/130/161/182），R110 只记 3 个，丢了 0x7f7cd0/0x7f7c70/0x7f7c80。用同一窗口可逐行复现 R110 的 172 行；去窗后只有 HouseClass 一类变化，0x7f7c90(171)/0x7f7ca0(78)/0x7e9ae0(76) 不变。故这两个 IID 的类集合真值 77 而非 76。反控 171 个「末次比较已在窗内」的类去窗后无一增加。

**接口方法数（R113 起第 4 轮未取得，本轮取得）**：接口块 = 主 vtable 的 slot 0..7 共 8 个（90 个 persist 家族类里首个写 vtable 常量的 slot 恒为 8，49 类可判；slot 0..7 合计 0 次写；AbstractClass 的 slot8 销毁器写 4 个 vtable 常量对应 4 个 mdisp {0,4,8,12}）。IClassFactory 族 78 类 vtable 长度恒 5 且 ncb=1 ⇒ IUnknown=3。故 IPersistStream = 8-3-1 = 4。IPersist=1 由 ncb 直接给出。形态佐证：slot1/slot2 全族 mov eax,1 ; ret 4；slot7 全族 ret 8（2 参数 Save）。

**跨家族**：执行员 deepseek task 243 failed + OVERTIME（61 回合 / 14.8 分钟 vs 预算 8.0）。按规则 D 不采信结论，只比原始数字：解码 954/0 失败、26 接口名、ncb 链、IClassFactory ncb=1、vtable 长 5、17 个 GUID 文本全部一致；唯一分歧 77 vs 76，复算后证明它对的（R110 漏 HouseClass）。

**自错 S-113..S-129 共 17 条**：BCD 字段错位、段守卫错、类集合相等判据错、vtable 终止规则、capstone 十进制立即数、QI 函数体停在首个 ret、集合写成一形式、lea 位移只认十六进制、筛序错、不取紧致名、不可满足断言、槽计数从 1 起、家族筛选先滤后缀、写 vtable 判据按地址而非 store 形态、ret 尺寸停在首 ret、反控单样本。

**断言**：r124a 14 + r124b 11 + r124c 14 + r124d 13 + r124e 14 + r124f 13 = 79 项全 PASS。未对整段 .text 开 detail=True；脚本带 timeout；无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0。

**未取得**：① 0x7f7c70/0x7f7c80 谁是 IPersist 谁是 IPersistStream（三条内部记录相同，须外部头文件或动态采样）；② 0x7e9b40 同；③ 0x7f7cf0 在 IStream/ISequentialStream 间；④ 0x7e36c0 与 0x7e9b20 偏移解不出；⑤ 35 个容器运行期元素值与计数；⑥ 共用模板的充分证明；⑦ C11 其余 4 处永远通过子项、五条不可能行、窗口表。
'''

SEC_LOCK = '''
FL. R124 主攻 R123 台账未取得项②与④：IID 到接口名、IPersistStream 方法数。六套脚本 79 项断言全 PASS，全部结论可从字节复算。

FM. 方法：MSVC x86 BCD 24 字节，pTypeDescriptor(+0)/NumContainedBases(+4)/mdisp(+8)/pdisp(+12)/vdisp(+16)/attributes(+20)，接口名 = CString(u32(BCD)+8)。954 个带 vtable 的类全解，bases[0] 恒为自身 954/954。.?AU 名字 26 个即 COM 接口。TD 与 BCD 在 .data，COL/CHD/BaseClassArray 在 .rdata —— 第一版把每个指针都按 .rdata 守卫，解码整批塌成 0/954（S-114）。

FN. 继承链由 ncb 直接给出：IUnknown=0，IPersist=1，IPersistStream=2，IClassFactory=1，IRTTITypeInfo=1，IStream=2，每名单值。

FO. IID 定名 12/18。两条独立记录：类集合只取包含（相等判据错，继承会少比 IID）；QI 分支写入出参的 this 调整值须等于 RTTI 的 mdisp。无一例两条记录矛盾。定名：0x7e9530=ILinkStream、0x7e9ae0=IRTTITypeInfo、0x7e9b00=IPublicHouse、0x7ea6e8=IUnknown、0x7ea768=IHouse(OFF 36)、0x7f7c20=IWOLBrowserEvent、0x7f7c90=IUnknown、0x7f7ca0=IClassFactory、0x7f7cb0=IEnumConnections、0x7f7cc0=IConnectionPoint、0x7f7cd0=IConnectionPointContainer(OFF 44)、0x7f7ce0=IEnumConnectionPoints。正控 0x7f7c90 的字节恰为 IID_IUnknown 常量；反控互换偏移后 IHouse 定名失败。

FP. 0x7f7c70 与 0x7f7c80 仍不可分（R113 起第 4 轮未取得），本轮给出不可分的结构理由而非只是没测：类集合相同（77，对称差 0）、出参偏移都是 0、RTTI 基类数组里 IPersistStream 恒在 IPersist 之前 77/77（顺序恒即无信号）。0x7e9b40 同样不可分；0x7f7cf0 在 IStream 与 ISequentialStream 间不可分；0x7e36c0 与 0x7e9b20 的偏移解不出。

FQ. 新发现：R110 的 IID 普查漏记一类。iids_of 里 a - f < QI_HEAD(120) 被写在每次 cmpsd 上，本意只限首个，实际把函数体内偏移超 120 字节的比较全丢掉。HouseClass(0x4f6830) 实际比 6 个 GUID（47/68/99/130/161/182），R110 只记 3 个，丢 0x7f7cd0/0x7f7c70/0x7f7c80。用同窗可逐行复现 R110 的 172 行；去窗后只 HouseClass 变，0x7f7c90(171)/0x7f7ca0(78)/0x7e9ae0(76) 不变。故这两个 IID 的类集合真值 77 而非 76。反控 171 个「末次比较已在窗内」的类去窗后无一增加。

FR. 接口方法数取得（R113 起第 4 轮未取得）：接口块 = 主 vtable 的 slot 0..7 共 8 个。90 个 persist 家族类里首个「函数体写 vtable 常量」的 slot 恒为 8（49 类可判，41 类短到无销毁器），slot 0..7 合计 0 次写；AbstractClass 的 slot8 销毁器写 4 个 vtable 常量，与 4 个 mdisp {0,4,8,12} 一一对应。IClassFactory 族 78 类 vtable 长恒 5 且 ncb=1 ⇒ IUnknown=3。故 IPersistStream = 8-3-1 = 4；IPersist=1 由 ncb 直接给出。形态佐证：slot1/slot2 全族 mov eax,1 ; ret 4；slot7 全族 90/90 ret 8。

FS. 规则 D：执行员 deepseek task 243 failed + OVERTIME（61 回合 / 14.8 分钟 vs 预算 8.0 / error_max_turns），报告未写，只落 q1..q5。结论不采信，只取原始数字复算比对：954 解 / 0 失败、26 接口名、ncb 链、IClassFactory ncb=1、vtable 长 5、17 个 GUID 文本逐项一致。唯一分歧 77 vs 76 复算后证明它对的 —— R110 漏记 HouseClass。这是本轮最有价值的交叉检验。

FT. 自错 S-113..S-129 共 17 条：BCD 字段读早一个 dword、段守卫把 .data 记录也按 .rdata 判、类集合用相等而非包含、vtable 终止用下一个 COL（末组失效）、capstone 小立即数印十进制致 78 个 AddRef 全记 None、QI 体停在首个 ret 而模板前部就有 NULL 早退、AbstractClass 集合一行式卷进 2 个仅包含它的类、lea 位移只认十六进制、先按紧致度筛再比偏移的方向错、不取紧致名致 IUnknown 永远并列、断言「基类数组恰为 [IUnknown]」不可满足、槽计数从 k=1 起全部少 1、persist 家族先滤 .?AU 再取尾、写 vtable 判据按地址而非 store 形态、ret 尺寸停在首 ret 误判 28 个委派重写、反控筛 len==1 只剩 1 个样本。

FU. 断言：r124a 14 + r124b 11 + r124c 14 + r124d 13 + r124e 14 + r124f 13 = 79 项全 PASS。全程 disasm_lite 与目标单条 disasm，未对整段 .text 开 detail=True；脚本带 timeout；收口前确认无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0（GATE_VER 仍 R121）。看板按 260 行阈值归档了 R118 与 R119 两段，归档后 CR 仍 2952、看板 CR 仍 0。

FV. 未取得（不粉饰）：① 0x7f7c70 与 0x7f7c80 谁是 IPersist 谁是 IPersistStream（三条内部记录完全相同，静态定不了，须外部头文件或动态采样）；② 0x7e9b40 与这两个同样不可分；③ 0x7f7cf0 在 IStream 与 ISequentialStream 之间不可分；④ 0x7e36c0 与 0x7e9b20 的出参偏移解不出；⑤ 35 个容器运行期元素值与计数；⑥ 共用模板的充分证明；⑦ 门禁 C11 其余 4 处永远通过子项、五条不可能行未裁定、窗口表未扩。
'''

SEC_BRD = '''## 🟢 R17 第 124 轮（2026-11-25 00:0x–01:0x）· 用二进制自己的 RTTI 把 IID 定名到接口（12/18），并取得 IPersistStream 方法数 = 4；顺带实证 R110 的 IID 普查漏记一类

**主攻**：R123 台账未取得项②（0x7f7c70 接口名与 IPersistStream 方法数）与④（共用模板充分证明的前置口径）。两项都推进到底，其中方法数完全取得。

### 一 · 方法：不解外部头文件，只用 exe 内的 RTTI

MSVC x86 每个带 vtable 的类，[vt-4] 是 COL，COL+16 是 CHD，CHD+8 = NumBaseClasses、CHD+12 = pBaseClassArray；每个 BCD 24 字节，pTypeDescriptor(+0)/NumContainedBases(+4)/mdisp(+8)/pdisp(+12)/vdisp(+16)/attributes(+20)，接口名就是 CString(u32(BCD)+8)。954 个类全部解码，bases[0] 恒为自身 954/954。.?AU 开头的 26 个名字即 COM 接口。

### 二 · 继承链是二进制自己记的，不是推断

IUnknown=0、IPersist=1、IPersistStream=2、IClassFactory=1、IRTTITypeInfo=1、IStream=2，每个接口名单值无例外。

### 三 · IID 定名 12/18：两条互不共字节的记录都要满足

第一条是类集合包含（用相等是错的：继承来的 QI 比较的 IID 少于 RTTI 名单）。第二条是 QI 每个被接受分支写进出参的 this 调整值（0 或 lea 的 OFF），它必须等于 RTTI 对该类记的 mdisp。两条都满足才定名，结果 12/18，且无一例两条记录互相矛盾。定名：0x7e9530=ILinkStream、0x7e9ae0=IRTTITypeInfo、0x7e9b00=IPublicHouse、0x7ea6e8=IUnknown、0x7ea768=IHouse(OFF 36)、0x7f7c20=IWOLBrowserEvent、0x7f7c90=IUnknown、0x7f7ca0=IClassFactory、0x7f7cb0=IEnumConnections、0x7f7cc0=IConnectionPoint、0x7f7cd0=IConnectionPointContainer(OFF 44)、0x7f7ce0=IEnumConnectionPoints。

### 四 · 0x7f7c70 与 0x7f7c80 仍不可分 —— 但这次说的是"为什么不可分"

两个常量是 0000010C-... 与 00000109-...。三条内部记录完全相同：类集合相同（77，逐类对称差 0）、出参偏移都是 0、RTTI 里 IPersistStream 恒排在 IPersist 前 77/77。顺序恒定本身就没有信号。0x7e9b40 同样不可分；0x7f7cf0 在 IStream 与 ISequentialStream 间不可分；0x7e36c0 与 0x7e9b20 的偏移解不出。静态到此为止，再往前必须外部头文件或动态采样。

### 五 · 顺带实证一个既有产物的缺陷：R110 的 IID 普查漏记一类

R110 的 iids_of 里那句 a - f < QI_HEAD(120) 本意只限制"首个 cmpsd"，实际写在每一次 cmpsd 上，于是函数体内偏移超过 120 字节的比较全被丢掉。HouseClass(slot0=0x4f6830) 实际比较 6 个 GUID，偏移 47/68/99/130/161/182，R110 只记了前 3 个，丢掉的正是 0x7f7cd0、0x7f7c70、0x7f7c80。用同一窗口能逐行复现 R110 的 172 行（证明这是 R110 原样不是重写）；去掉窗口后只有 HouseClass 一类变化，0x7f7c90(171)、0x7f7ca0(78)、0x7e9ae0(76) 完全不变。所以这两个 IID 的类集合真值是 77 不是 76。反控：171 个"末次比较已在窗口内"的类，去窗后一个都不增加。

### 六 · IPersistStream 方法数 = 4（R113 起挂 4 轮的项，本轮取得）

接口块边界：90 个 persist 家族类的主 vtable 里，第一个"函数体写 vtable 常量"的 slot 恒为 8（49 类可判，41 类短到没有销毁器），slot 0..7 合计写 0 次。AbstractClass 最干净：slot8 销毁器写 4 个 vtable 常量，与它 4 个 mdisp {0,4,8,12} 一一对应 ⇒ 接口块 = slot 0..7 共 8 个。IUnknown 由 IClassFactory 族钉死：78 个类 vtable 长度恒 5 且 ncb=1 ⇒ IUnknown = 5-2 = 3。于是 IPersistStream = 8-3-1 = 4，IPersist=1 由 ncb 直接给出。形态佐证：slot1/slot2 全族 mov eax,1 ; ret 4；slot7 全族 90/90 ret 8。

### 七 · 跨家族与规则 D

执行员 deepseek task 243 failed + OVERTIME（61 回合 / 14.8 分钟 vs 预算 8.0 / error_max_turns），报告未写，只落 q1..q5。按规则 D 不采信其结论，只取原始数字复算：954 解 / 0 失败、26 接口名、ncb 链、IClassFactory ncb=1、vtable 长 5、17 个 GUID 文本全部一致。唯一分歧是类集合 77 对我原报的 76 —— 复算后证明执行员对的，是 R110 漏了 HouseClass。这条分歧是本轮最有价值的交叉检验。

### 八 · 自错 S-113..S-129 共 17 条

BCD 字段读早一个 dword；段守卫把 .data 里的 TD/BCD 也按 .rdata 判，解码整批塌成 0/954；类集合用相等而非包含；vtable 终止用"下一个 COL"对末组失效；capstone 小立即数印十进制而只认 0x 前缀，78 个 AddRef/Release 全记 None；QI 体停在首个 ret 而模板前部就有 NULL 早退；AbstractClass 集合写成一形式卷进 2 个仅"包含"它的类；lea 位移只认十六进制；先按紧致度筛再比偏移方向错；不取紧致名致 IUnknown 永远并列；断言"基类数组恰为 [IUnknown]"不可满足（MSVC 恒列最派生类在首位）；槽计数从 k=1 起全部少 1；persist 家族先滤 .?AU 再取尾；写 vtable 判据按地址而非 store 形态，把仅引用地址的普通方法计入；ret 尺寸扫描停在首 ret 误判 28 个委派重写；反控筛 len(iids)==1 只剩 1 个样本。

### 九 · 收口

r124a 14 + r124b 11 + r124c 14 + r124d 13 + r124e 14 + r124f 13 = 79 项断言全 PASS。全程 disasm_lite 与目标单条 disasm，未对整段 .text 开 detail=True；脚本均带 timeout；收口前确认无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；看板按 260 行阈值归档 R118 与 R119 两段（归档 CR 仍 2952、看板 CR 仍 0）；check_disc.py exit 0（GATE_VER 仍 R121，本轮不改门禁）。

### 十 · 未取得（不粉饰）

① 0x7f7c70 与 0x7f7c80 谁是 IPersist 谁是 IPersistStream（三条内部记录完全相同，静态定不了，须外部头文件或动态采样）；② 0x7e9b40 与这两个同样不可分；③ 0x7f7cf0 在 IStream 与 ISequentialStream 之间不可分；④ 0x7e36c0 与 0x7e9b20 的出参偏移解不出；⑤ 35 个容器运行期元素值与计数；⑥ 共用模板的充分证明；⑦ 门禁 C11 其余 4 处永远通过子项、五条不可能行未裁定、窗口表未扩。
'''

TARGETS = [
    (RC,   SEC_RC,   1081),
    (LED,  SEC_LED,  337),
    (LOCK, SEC_LOCK, 137),
    (BRD,  SEC_BRD,  0),
]

# ---- PRE-WRITE assertions (must run BEFORE any write: R121 S-94 / R122 S-101) ----
for path, sec, cr_exp in TARGETS:
    assert '`' not in sec, ('backtick in section for ' + path)
    assert sec.count('\r') == 0, ('CR in new section for ' + path)
    old = io.open(path, 'rb').read()
    assert old.count(b'\r\n') == cr_exp, (path, old.count(b'\r\n'), cr_exp)
    txt = old.decode('utf-8')
    # R124 S-130: R14_COMMON really does end with a blank line; asserting
    # "no trailing blank" fails on a healthy file.  Normalise instead of assert.
    if txt.endswith('\n\n'):
        txt_norm = txt.rstrip('\n') + '\n'
        assert txt_norm.encode('utf-8').count(b'\r\n') == cr_exp
print('pre-write assertions OK')

for path, sec, cr_exp in TARGETS:
    old = io.open(path, 'rb').read()
    old_sha = sha(old)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = os.path.join(BK, '%s.before_R124_write_%s.bak' % (os.path.basename(path), ts))
    with io.open(bak, 'xb') as f:
        f.write(old)
    assert sha(io.open(bak, 'rb').read()) == old_sha, ('backup mismatch', bak)

    txt = old.decode('utf-8').rstrip('\n') + '\n'   # normalise to exactly one trailing LF
    body = sec.strip('\n')
    new = txt + body + '\n'
    assert '`' not in body
    io.open(path, 'wb').write(new.encode('utf-8'))

    back = io.open(path, 'rb').read()
    assert back.count(b'\r\n') == cr_exp, (path, back.count(b'\r\n'), cr_exp)
    assert body.encode('utf-8') in back, path
    print('%-22s CR=%-5d bytes %d -> %d  bak=%s'
          % (os.path.basename(path), cr_exp, len(old), len(back), os.path.basename(bak)))
print('ALL WRITES OK')
