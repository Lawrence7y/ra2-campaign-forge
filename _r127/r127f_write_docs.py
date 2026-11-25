# -*- coding: utf-8 -*-
"""R127: 追加 R14_COMMON §2.131、台账 §1181、LEAD_LOCK 的 GN 段、看板第 127 轮段。

纪律（与 R125/R126 一致）：wx 独占备份 -> 断言旧 sha256 与旧 CR -> 断言新文本零反引号
-> 单次写入 -> 回读校验（sha、CR、字节数、新段存在）。

看板当前 107 行，未到 260 行阈值，本轮不归档。
"""
import io, os, sys, hashlib, datetime

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
RC = os.path.join(R14, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD = os.path.join(R14, 'STATUS_BOARD.md')

EXPECT = {
    RC:  ('ba7a0bbdae204ff1', 1081),
    LED: ('2dadd25687cdbbba', 337),
    LOCK: ('dbb74bdf60fff030', 137),
    BRD: ('18a9ea180c36695b', 0),
}
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def do(path, tag, new_text, want_cr, marker=None):
    assert '`' not in new_text, '%s 新文本含反引号' % tag
    old = io.open(path, 'rb').read()
    dst = os.path.join(BK, 'r127_%s.%s.bak' % (tag, TS))
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try:
        os.write(fd, old)
    finally:
        os.close(fd)
    want_sha, expect_cr = EXPECT[path]
    assert sha16(old) == want_sha, '%s 旧 sha %s != %s' % (tag, sha16(old), want_sha)
    assert old.count(b'\r') == expect_cr, '%s 旧 CR %d != %d' % (
        tag, old.count(b'\r'), expect_cr)

    new = old.decode('utf-8').rstrip('\n') + '\n' + new_text
    nb = new.encode('utf-8')
    with io.open(path, 'wb') as f:
        f.write(nb)
    rb = io.open(path, 'rb').read()
    assert rb == nb, '%s 回读不一致' % tag
    assert rb.count(b'\r') == want_cr, '%s 新 CR %d != %d' % (
        tag, rb.count(b'\r'), want_cr)
    if marker:
        assert marker.encode('utf-8') in rb, '%s 回读未见新段标记' % tag
    print('  WROTE %-11s sha %s -> %s  CR=%d  bytes %d -> %d  LF %d -> %d'
          % (tag, sha16(old), sha16(rb), rb.count(b'\r'),
             len(old), len(rb), old.count(b'\n'), rb.count(b'\n')))


SEC_RC = '''
## 2.131 R127 台账：0x7f7c70/0x7f7c80 由 OleSaveToStream 的参数角色定名完毕；0x7e36c0 = IApplication、0x7e9b20 = ISwizzle

R127 全部为静态字节测量，可从 gamemd.exe（sha256 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476）逐条复算。六套脚本 60 项断言全 PASS。本轮不引外部头文件，上限在末节写清。

**一 · 0x7f7c80 / 0x820270 = IPersistStream，0x7f7c70 / 0x818858 = IPersist（R125 起记「不由字节给出」，本轮由参数角色定位）**

R125 已把两个常量的使用侧分开了一半：0x7f7c70 的 push 站点是空集，一切结论只能由 .data 拷贝 0x818858 的 16 个观测点承担；0x7f7c80 的 .rdata 拷贝有 60 处 push、.data 拷贝 0x820270 有 8 处。但「谁是 IPersist、谁是 IPersistStream」仍缺一条能把名字钉死的内部记录。

本轮的判据换到**实参契约**上，与「跟哪些 OLE 调用共现」无关。导入表实测 ole32!OleSaveToStream 恰 1 槽 0x7e15f4、ole32!OleLoadFromStream 恰 1 槽 0x7e15f8（名字与 DLL 都取自本映像导入表字节）。OleSaveToStream 的第 2 实参契约是 IPersistStream，第 1 实参是 IStream。实测：

- 0x820270（0109 的 .data 拷贝）作为 riid 的 8 个 QI 站点，从 push 之后**正向反汇编到 ret 为止**（不是固定字节窗口，避免窗口太短漏计）全部命中 call [0x7e15f4]：0x4af856 到 0x4af8a5、0x4b6313 到 0x4b6364、0x4db76a 到 0x4db7be、0x50469e 到 0x5046c9、0x54b83c 到 0x54b88b、0x69ef66 到 0x69efb5、0x719d96 到 0x719de5、0x75c756 到 0x75c7a5，共 8/8。
- 0x7f7c80（同一 GUID 的 .rdata 拷贝）的 60 处 push 中，35 处在此后 40 字节内直接出现 ff 15 f4 15 7e 00（push 之后直接 call）。
- 反向：0x818858 / 0x7f7c70 的全部 16 个站点，正向扫到 ret 为止**没有一处**命中 call [0x7e15f4]。

所以 0109 对 = IPersistStream 由「被当作 OleSaveToStream 的第 2 实参」这条契约证据承担。

**二 · 010C 那一侧由方法数上限承担**

0x818858 / 0x7f7c70 的 16 个站点上，QI 结果上出现的虚槽只有 +0xc 一处（R125 已记：0x42cab5 的 ff 50 0c）。三个 GetClassID 站点 0x4d5892、0x73e7b7、0x742815 都是「call [reg+0xc] 带一个 4 字节出参，紧接着 lea esi,[esp+K] 与 mov edi,<类自己的 CLSID> 后 repe cmpsd」，三个被比常量互不相同：92612C46-F71F-11D1-AC9F-006008055BB5、4A582747-9839-11D1-B709-00A024DDAFD1、4A582743-9839-11D1-B709-00A024DDAFD1。这与 IPersist 只有一个 GetClassID 相符，与 IPersistStream 的 4 个方法不符。

两对必须在 L1 的两个候选（.?AUIPersistStream@@ 与 .?AUIPersist@@）里二选一，且方向单向可失败（010C 从不触 +0x10 以上，0109 从不喂 OleSaveToStream），故这不是「挑一个像的」而是唯一解。**上限**：字节仍读不出 IPersist 三个字的拼写，方向由外部 GUID 约定补上（109 = IPersistStream、10C = IPersist）。这一点不粉饰。

**三 · 0x7e36c0 与 0x7e9b20 是 IID 常量，不是 QI 体（撤回 R124-R126 的表述）**

这两个地址都在 .rdata、各 16 字节，是 IID：0x7e36c0 = {96F02EC3-6FE8-11D1-B6FD-00A024DDAFD1}，0x7e9b20 = {5FF0CA70-8B12-11D1-B708-00A024DDAFD1}。R124 到 R126 台账里把它们称作「QI 体」是错的表述，本轮撤回。

它们的**接受点**（体内把 riid 与该 IID 做 repe cmpsd 的 QI 体）实测三处：0x429360 在 vtable 0x7e36d4 的 slot0（.?AVApplicationClass@@）、0x429270 在 vtable 0x7ea564 的 slot3(+0xc)（.?AVTiberianSunClassFactory@@）、0x6cf430 在 vtable 0x7f4108 的 slot0（.?AVSwizzleManagerClass@@）。

**四 · 完整性核验（这一条是本轮补的洞）**

r127b 的接受点走「vtable 槽 -> 函数入口 -> 体内比较」这条路，结构性盲点是「入口没被任何 vtable 槽直接指向的 QI 体看不见」。r127d 专门补这个洞，用的是不看 vtable 的两条独立路径：

- 整份映像全字节枚举 bf <IID32> 与 68 <IID32> 两种锚点：0x7e36c0 的 bf 站点 0x4292ab 与 0x42937f、68 站点 0x429409 / 0x429489 / 0x4f6936；0x7e9b20 的 bf 站点 0x6cf44e、68 站点 0x429555。全部落在 .text。
- 全 .rdata 里 u32 == 三个 QI 体入口的位置逐个判定：0x429360 恰被 0x7e36d4 slot0 指向、0x429270 恰被 0x7ea564 slot3 指向（该 4 字节在 0x7ea570）、0x6cf430 恰被 0x7f4108 slot0 指向，各 1 处，无多余宿主。
- 三个 QI 体入口被当作立即数（bf/68 imm32）引用的次数**全为 0**，即除 vtable 槽之外没有第二条引用路径，所以宿主集合就是完整集合。
- 反控：同一套「扫 .rdata 里 u32 == X」判据对 0x429580 与 0x6cf400 给出 0 命中（相邻区的函数未被 vtable 引用），对 0x429210 给出 1 命中（.?AVTiberianSunClassFactory@@ 的 slot0），对 0x40f000 给出 1 命中但解不出类名 —— 判据不是恒真。

**五 · 定名**

- 0x7e36c0 = .?AUIApplication@@：接受点宿主是 ApplicationClass 与 TiberianSunClassFactory。前者 RTTI 在 mdisp 0 处的非 IUnknown 接口名唯一是 IApplication；后者唯一是 IClassFactory（该处是 IClassFactory::CreateInstance 的形状，ret 0x10 = 4 实参，把 0x89a29c 处的对象——0x429200 处被写成 0x7e36d4 即 ApplicationClass 的 mdisp0 虚表——拿来做 riid 比对）。两个宿主交集里只剩 IApplication 一个非 IUnknown 接口名。
- 0x7e9b20 = .?AUISwizzle@@：宿主 SwizzleManagerClass 的 RTTI 恰 3 条基类 .?AVSwizzleManagerClass@@ / .?AUISwizzle@@ / .?AUIUnknown@@，ncb 2/1/0，mdisp 全 0，非 IUnknown 的接口名唯一。
- 两个 QI 体（0x429360、0x6cf430）都同时显式比较 0x7f7c90（IID_IUnknown），故它们对应的 IID 不是 IUnknown。
- 0x429360 的 QI 体还有第三分支接受 0x7ea6e8 = {96F02EC7-6FE8-11D1-B6FD-00A024DDAFD1}，出参写成 .data 单例 0x87f7e8 而不是 this。**本轮不给它定名**：接受值不是本对象，mdisp 判据对它无效。

**六 · 本轮自己的判据错误（S-167 到 S-176，全部留案）**

- S-167：自审卡把 repe cmpsd 写成 F3 A5（那是 repe movsd），实际字节 F3 A7。改后重扫。
- S-168：接受点判据用 rd(f, 300) 读固定 300 字节窗口，跨过函数边界，把 0x429210 / 0x6cf410 也算成接受点。
- S-169：改用「向前找 0xC2/0xC3 后接连续 >=2 个 90/CC」求函数入口，但 0xC2/0xC3 会以立即数字节形式出现，仍算错。
- S-170：改用 disasm_lite 指令对齐求入口 —— .text 里嵌着数据（.byte 伪指令 65 处），线性反汇编在数据上错位，求出的入口与末端都不可靠。最终改为不自己求函数边界，只做纯字节枚举并与 r127b 的站点集合做双向差集。
- S-171：r127d 第一版把段基址存成 RVA 而非 VA，D1 报出的锚点整体少 0x400000。
- S-172：r127e 的 E4 第一版把「站点之后窗口内所有 call [reg+off]」都算进来，把 0x742899 的 call [edx+0x1c8]（ebp 另一个对象的虚调用）当成 QI 结果的虚槽调用。
- S-173（最重的一条）：我派给审计员的卡 R127-AUDIT-IPERSIST.md 第 5 条写「复算 0x7ea564 与 0x7e36d4 两个 vtable 的 +0xc 槽值是否等于 0x429270 与 0x429360」。实测 0x7e36d4 的 slot0 = 0x429360、slot3(+0xc) = 0x429420。卡面是我写错的；r127b 的产物写 slot_index 0 与 3，它对。审计员若照卡面核 +0xc 会得到 0x429420 并对不上，这不是它的错。
- S-174：r127e 的 E6 第一版取 bcd+16 当 ncb，那是 vdisp（全 0），于是三条基类 ncb 全报 0。MSVC x86 BC 布局是 +0 sig / +4 numContainedBases / +8 mdisp / +12 pdisp / +16 vdisp。
- S-175：r127e 的 E4 第二版改成的简单寄存器跟踪在 16 个站点上追到 0 处 —— 真实代码先把 ppv 槽值与 setl/dec/and 合成再解引用（0x42ca82 mov edx,[esp+0x4c] -> 0x42ca8c and ebx,edx -> 0x42caad mov eax,[ebx] -> 0x42cab5 call [eax+0xc]）。故 E4 不构成对 r127a「槽只到 +0xc」的独立复核，如实记方法无解。
- S-176：r127e 的 E7 第一版同样被 S-172 的口径污染，把 +0x1c8 当反例；改为「窗口内 off >= 0x10 的虚调用是否以 ppv 槽装出的寄存器为基址」，实测每一条都不是。
- S-177：r127h 的 H6 第一版用「COL 的 +20 处 pSelf 必须等于 COL 自身地址」当校验，但该构建所有 COL 的 +20 全为 0，判据恒假。改用 signature + pTypeDescriptor + pClassDescriptor 三个字段定位。
- S-178：我把审计员中途落盘的 7215 字节版本当成最终报告，据此写了「裁决分歧」的 H6/H7 两条；回收最终版（273 行）后它自己已改对，两条分歧都不存在。教训：等 wait_subagents 返回再读报告。

**七 · 跨家族（规则 D，两次派发，一失败一成功）**

第一次派 deepseek（task 256）：status failed，error = error_max_turns，61 回合 / 15.17 分钟，派发预算 5.0 分钟，**OVERTIME** 如实记，result 为空、未落任何报告。所以那一次的外部复核输入为零，不能写「已审计」。

第二次派 hy4（task 257）：succeeded，39 回合 / 3.15 分钟，预算 4.0 分钟，无 OVERTIME。报告 273 行 / 11111 字节、零反引号，收进 _r127/audit/r127_audit_hy4.md。它四条主张全判 PASS，未发现推翻性证据。

规则 D 的复算由 r127h（14 项）承担，逐条按审计卡口径重算：IAT 两个槽、四组 IID 字节与 GUID 文本、0x820270 的 8 个站点与 8 对命中地址、0x818858 的 16 个站点与 0 命中、三个 vtable 槽值、0x7f4108 的 COL 五个字段与三条基类四列、三处宿主槽位、两个 IID 的 5 处与 2 处出现位置。全部与它逐个相同，无一条分歧。

过程中有一条要如实说：我第一次读到的是它**中途**写下的 7215 字节版本，那一版第 6 条报 ValueError 并把宿主全判 unknown，我据此写了「裁决分歧」。随后回收最终版（273 行），它自己已改对，结论与我一致 —— 所以「分歧」这个前提是我读早了造成的，不虚构分歧。

它给的一条证据我原来漏了，采纳并复算（H10）：存在两个「固定参数包装器」直接 call QI 体 —— 0x4f6930 是 push ecx / lea eax,[esp] / push eax / push 0x7e36c0 / push 0x89a29c / call 0x429360 / ret 4；0x429550 是 mov eax,[esp+8] / push eax / push 0x7e9b20 / push 0xb0c110 / call 0x6cf430 / ret 8。这两处比 vtable 槽更硬：IID 与对象都写死，只留出参，直接证「这个 IID 就是交给这个 QI 体比的」。反控：同一判据对 0x429480（IClassFactory::CreateInstance 的包装器）给否。

**八 · 断言与收口**

r127a 15 + r127b 9 + r127c 9 + r127d 5 + r127e 8 + r127h 14 = 60 项全 PASS。全程 disasm_lite 流式扫描与单点窗口 disasm，未对整段 .text 开 detail=True；脚本带 timeout；收口前 ps 确认无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0（GATE_VER 仍 R126，本轮不改门禁）。看板 107 行未到 260 行阈值，本轮不归档。

**九 · 未取得（不粉饰）**

1) 010C = IPersist 的方向仍由外部 GUID 约定补上，字节只给出「更窄那个多一个 slot 3」。2) 0x7ea6e8 未定名（接受值不是 this，mdisp 判据无效）。3) 0x429270 是转交型（把 pUnkOuter 交给内层对象的 QI，不写自己的 ppv），本卡如实分两类记，不把它当失败。4) 010C 站点的 ppv 槽值经 setl/dec/and 合成后解引用，简单寄存器跟踪追不到，故「槽只到 +0xc」仍只由 r127a 的符号执行承担。5) 若 QI 结果被存进堆结构体后再取用，本轮所有判据都看不见。6) 35 个静态容器的运行期元素值与计数。7) 共用模板展开的充分证明。8) 门禁 C11 其余四处永远通过子项、五条不可能行未裁定、窗口表未扩。
'''


SEC_LED = '''
## §1181 R127 台账：IPersist / IPersistStream 由 OleSaveToStream 参数角色定名完毕；0x7e36c0 = IApplication、0x7e9b20 = ISwizzle

R127 全部为静态字节测量，可从 gamemd.exe（sha256 73201cc0...fcf67476）复算。六套脚本 60 项断言全 PASS。

**一 · 0x7f7c80 / 0x820270 = IPersistStream，0x7f7c70 / 0x818858 = IPersist**

判据是实参契约，不是共现频率。导入表实测 ole32!OleSaveToStream 恰 1 槽 0x7e15f4。0x820270 作为 riid 的 8 个 QI 站点，从 push 之后正向反汇编到 ret 为止全部命中 call [0x7e15f4]（8/8，逐个给地址对：0x4af856->0x4af8a5、0x4b6313->0x4b6364、0x4db76a->0x4db7be、0x50469e->0x5046c9、0x54b83c->0x54b88b、0x69ef66->0x69efb5、0x719d96->0x719de5、0x75c756->0x75c7a5）；0x7f7c80 的 60 处 push 中 35 处此后紧接 ff 15 f4 15 7e 00。反向：0x818858 / 0x7f7c70 的 16 个站点无一命中该 call。OleSaveToStream 第 2 实参契约是 IPersistStream，故 0109 对 = IPersistStream。

010C 那侧由方法数上限承担：16 个站点上 QI 结果只在 +0xc 出现（0x42cab5 的 ff 50 0c），三个 GetClassID 站点 0x4d5892 / 0x73e7b7 / 0x742815 都是 call [reg+0xc] 带 4 字节出参后接 mov edi,<类自己的 CLSID> 与 repe cmpsd，三个 CLSID 互不相同（92612C46-F71F-11D1-AC9F-006008055BB5、4A582747-9839-11D1-B709-00A024DDAFD1、4A582743-9839-11D1-B709-00A024DDAFD1），与 IPersist 只有一个 GetClassID 相符、与 IPersistStream 的 4 方法不符。两对在 L1 的两个候选里二选一，方向单向可失败。上限：IPersist 的拼写仍不由字节给出，方向靠外部 GUID 约定。

**二 · 0x7e36c0 与 0x7e9b20 是 IID 常量，不是 QI 体（撤回 R124-R126 表述）**

0x7e36c0 = {96F02EC3-6FE8-11D1-B6FD-00A024DDAFD1}，0x7e9b20 = {5FF0CA70-8B12-11D1-B708-00A024DDAFD1}，都在 .rdata、各 16 字节。接受点（做 repe cmpsd 的 QI 体）三处：0x429360 @ vtable 0x7e36d4 slot0（.?AVApplicationClass@@）、0x429270 @ vtable 0x7ea564 slot3(+0xc)（.?AVTiberianSunClassFactory@@）、0x6cf430 @ vtable 0x7f4108 slot0（.?AVSwizzleManagerClass@@）。

**三 · 完整性（r127d 补的洞）**

r127b 走 vtable 槽反查，盲点是「入口未被任何 vtable 槽指向的 QI 体看不见」。r127d 用不看 vtable 的两条路补：全映像 bf/68 锚点枚举（0x7e36c0：bf 0x4292ab、0x42937f；68 0x429409、0x429489、0x4f6936。0x7e9b20：bf 0x6cf44e；68 0x429555），以及全 .rdata 里 u32 == 入口的位置逐个判槽 —— 三个入口各恰 1 处宿主且与 r127b 完全一致。三个入口被 bf/68 立即数引用的次数全为 0，故除 vtable 槽外无第二条引用路径，宿主集合完整。反控：0x429580 与 0x6cf400 给 0 命中、0x429210 给 1 命中、0x40f000 给 1 命中但解不出类名，判据非恒真。

**四 · 定名**

0x7e36c0 = .?AUIApplication@@（ApplicationClass 与 TiberianSunClassFactory 两个宿主的 mdisp0 非 IUnknown 接口名交集唯一）；后者那处是 IClassFactory::CreateInstance 形状（ret 0x10，把 0x89a29c 对象拿来做比对，该对象 0x429200 处被写成 0x7e36d4）。0x7e9b20 = .?AUISwizzle@@（SwizzleManagerClass 的 3 条基类 mdisp 全 0、ncb 2/1/0，非 IUnknown 唯一）。两个 QI 体都同时比较 0x7f7c90，故两者都不是 IUnknown。0x429360 的第三分支接受 0x7ea6e8 = {96F02EC7-...}，出参写成 .data 单例 0x87f7e8 而非 this，**不定名**（接受值不是本对象，mdisp 判据无效）。

**五 · 自错 S-167 到 S-176**

S-167 把 repe cmpsd 写成 F3 A5（实为 F3 A7）；S-168 用固定 300 字节窗口跨过函数边界；S-169 用 C2/C3 字节找 ret 被立即数误导；S-170 用线性反汇编求函数边界，但 .text 内嵌数据（.byte 65 处）导致错位，最终改为不求函数边界、只做纯字节枚举加双向差集；S-171 段基址存 RVA 而非 VA，锚点整体少 0x400000；S-172 把别的寄存器的虚调用算成 QI 结果的虚槽；S-173 派给审计员的卡第 5 条把 0x429360 说成在 +0xc（实为 slot0，+0xc 是 0x429420），卡面写错、r127b 产物对；S-174 取 bcd+16 当 ncb（那是 vdisp），ncb 在 +4；S-175 简单寄存器跟踪在 16 个站点追到 0 处（ppv 槽经 setl/dec/and 合成），故 E4 不构成独立复核；S-176 E7 第一版同样被 S-172 口径污染。

**六 · 规则 D 与收口**

两次派发。deepseek task 256 failed 加 error_max_turns（61 回合 / 15.17 分钟 vs 预算 5.0，OVERTIME），result 为空、零报告，那次外部输入为零。hy4 task 257 succeeded（39 回合 / 3.15 分钟 / 预算 4.0 / 无 OVERTIME），报告 273 行零反引号，四条主张全 PASS。r127h 14 项按审计卡口径逐条复算，与它逐个相同，无分歧。它还给了两个我漏掉的固定参数包装器（0x4f6930 与 0x429550），直接 call QI 体、IID 与对象都写死，采纳并复算通过。

另记三条自错：S-177 用 pSelf 自指当 COL 校验判据（该构建全 0，恒定失败）；S-178 把审计员中途落盘版当最终报告，据此虚构了两条「分歧」。

断言：r127a 15 + r127b 9 + r127c 9 + r127d 5 + r127e 8 + r127h 14 = 60 项全 PASS。disasm_lite 流式扫描与单点窗口，未对整段 .text 开 detail=True；脚本带 timeout；收口前 ps 确认无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0（GATE_VER 仍 R126，本轮不改门禁）。看板 107 行未到 260 行阈值，本轮不归档。

**七 · 未取得（不粉饰）**

1) IPersist 拼写仍靠外部约定；2) 0x7ea6e8 未定名；3) 0x429270 是转交型（不写自己的 ppv），不参与 mdisp 判据；4) 010C 的 ppv 槽经 setl/dec/and 合成，简单跟踪追不到，「槽只到 +0xc」仍只由 r127a 符号执行承担；5) QI 结果存进堆结构体后再取用的路径看不见；6) 35 个静态容器运行期元素值与计数；7) 共用模板展开的充分证明；8) 门禁 C11 其余四处永远通过子项、五条不可能行未裁定、窗口表未扩。
'''


SEC_LOCK = '''
GN. R127 主攻 R125/R126 台账 GK 里的前两条未取得项，两条都取得，另撤回 R124 起的一处错误表述。六套脚本 60 项断言全 PASS。

GO. 0x7f7c80/0x820270 = IPersistStream，0x7f7c70/0x818858 = IPersist。判据换成实参契约：ole32!OleSaveToStream 恰 1 槽 0x7e15f4（名字取自本映像导入表字节）。0x820270 作 riid 的 8 个 QI 站点，从 push 之后正向反汇编到 ret 为止 8/8 全部命中 call [0x7e15f4]（0x4af856->0x4af8a5、0x4b6313->0x4b6364、0x4db76a->0x4db7be、0x50469e->0x5046c9、0x54b83c->0x54b88b、0x69ef66->0x69efb5、0x719d96->0x719de5、0x75c756->0x75c7a5）；0x7f7c80 的 60 处 push 中 35 处紧接 ff 15 f4 15 7e 00。反向：0x818858/0x7f7c70 的 16 站点无一命中。OleSaveToStream 第 2 实参契约是 IPersistStream。

GP. 010C 侧由方法数上限承担：16 站点上 QI 结果只在 +0xc 出现（0x42cab5 的 ff 50 0c），三个 GetClassID 站点 0x4d5892、0x73e7b7、0x742815 都是 call [reg+0xc] 带 4 字节出参后接 mov edi,<类自己的 CLSID> 与 repe cmpsd，三个 CLSID 互不相同。这与 IPersist 只有一个 GetClassID 相符、与 IPersistStream 的 4 方法不符。两对在 L1 的两个候选（.?AUIPersistStream@@ / .?AUIPersist@@）里二选一，方向单向可失败。上限：IPersist 三个字的拼写仍不由字节给出，方向靠外部 GUID 约定（109 = IPersistStream、10C = IPersist）补上，不粉饰。

GQ. 撤回一处错表述：0x7e36c0 与 0x7e9b20 都在 .rdata、各 16 字节，是 IID 常量，不是 QI 体 —— R124 到 R126「QI 体」的说法本轮撤回。0x7e36c0 = {96F02EC3-6FE8-11D1-B6FD-00A024DDAFD1}，0x7e9b20 = {5FF0CA70-8B12-11D1-B708-00A024DDAFD1}。它们的接受点（体内做 repe cmpsd 的 QI 体）三处：0x429360 @ vtable 0x7e36d4 slot0（.?AVApplicationClass@@）、0x429270 @ vtable 0x7ea564 slot3(+0xc)（.?AVTiberianSunClassFactory@@）、0x6cf430 @ vtable 0x7f4108 slot0（.?AVSwizzleManagerClass@@）。

GR. 补 r127b 的结构性盲点：它走 vtable 槽反查，看不见「入口未被任何 vtable 槽指向的 QI 体」。r127d 用不看 vtable 的两条路补：全映像 bf/68 锚点枚举（0x7e36c0 bf 0x4292ab、0x42937f，68 0x429409、0x429489、0x4f6936；0x7e9b20 bf 0x6cf44e，68 0x429555），以及全 .rdata 里 u32 == 入口的位置逐个判槽 —— 三个入口各恰 1 处宿主、与 r127b 完全一致。三个入口被 bf/68 立即数引用次数全为 0，故除 vtable 槽外无第二条引用路径，宿主集合完整。反控：0x429580 与 0x6cf400 给 0 命中、0x429210 给 1 命中（.?AVTiberianSunClassFactory@@ slot0）、0x40f000 给 1 命中但解不出类名。

GS. 定名：0x7e36c0 = .?AUIApplication@@（ApplicationClass 与 TiberianSunClassFactory 两个宿主 mdisp0 非 IUnknown 接口名交集唯一；后者那处是 IClassFactory::CreateInstance 形状，ret 0x10，把 0x89a29c 对象拿来做比对，该对象 0x429200 处被写成 0x7e36d4）。0x7e9b20 = .?AUISwizzle@@（SwizzleManagerClass 三条基类 mdisp 全 0、ncb 2/1/0，非 IUnknown 唯一）。两个 QI 体都同时比较 0x7f7c90，故都不是 IUnknown。0x429360 的第三分支接受 0x7ea6e8 = {96F02EC7-6FE8-11D1-B6FD-00A024DDAFD1}，出参写成 .data 单例 0x87f7e8 而非 this，本轮不定名 —— 接受值不是本对象，mdisp 判据对它无效。

GT. 本轮自错 S-167 到 S-176 全部留案，其中三条值得单独记。S-170：我三次尝试自己算函数边界（固定 300 字节窗口跨边界、C2/C3 字节被立即数误导、线性反汇编在 .text 内嵌数据上错位），最后放弃自算，改为纯字节枚举加与 r127b 站点集合的双向差集 —— 承认「不自己求边界」比强行求更可靠。S-173：我派给审计员的卡第 5 条写「复算 0x7ea564 与 0x7e36d4 的 +0xc 槽值是否等于 0x429270 与 0x429360」，实测 0x7e36d4 的 slot0 = 0x429360、slot3(+0xc) = 0x429420，卡面是我写错的，r127b 产物写 slot_index 0 与 3 是对的；审计员若照卡面核会得到 0x429420 并对不上，这不是它的错。S-175：E4 改用的简单寄存器跟踪在 16 个站点追到 0 处 —— 真实代码先把 ppv 槽值经 setl/dec/and 合成再解引用（0x42ca82 mov edx,[esp+0x4c] -> 0x42ca8c and ebx,edx -> 0x42caad mov eax,[ebx] -> 0x42cab5 call [eax+0xc]），故 E4 不构成对 r127a「槽只到 +0xc」的独立复核，如实记方法无解。

GU. 规则 D 两次派发，一失败一成功，如实记。deepseek task 256 failed 加 error_max_turns（61 回合 / 15.17 分钟 vs 预算 5.0 ⇒ OVERTIME），result 为空、零报告，那次外部输入为零、不能写「已审计」。hy4 task 257 succeeded（39 回合 / 3.15 分钟 / 预算 4.0 / 无 OVERTIME），报告 273 行 / 11111 字节零反引号，收进 _r127/audit/r127_audit_hy4.md，四条主张全 PASS。复算由 r127h 14 项承担：IAT 两槽、四组 IID 字节与 GUID 文本、8 对 (push, 命中) 地址、16 站点 0 命中、三个 vtable 槽值、COL 五字段与三条基类四列、三处宿主槽位、两个 IID 的 5 处与 2 处出现位置 —— 全部逐个相同，无一条分歧。

GV. 断言与收口：r127a 15 + r127b 9 + r127c 9 + r127d 5 + r127e 8 + r127h 14 = 60 项全 PASS。全程 disasm_lite 流式扫描与单点窗口 disasm，未对整段 .text 开 detail=True；脚本带 timeout；收口前 ps 确认无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0（GATE_VER 仍 R126，本轮不改门禁）。看板 107 行未到 260 行阈值，本轮不归档。

GY. 未取得（不粉饰）：① IPersist 的拼写仍靠外部 GUID 约定，字节只给出「更窄那个多一个 slot 3」；② 0x7ea6e8 未定名（接受值不是 this，mdisp 判据无效）；③ 0x429270 是转交型（把 pUnkOuter 交给内层对象的 QI、不写自己的 ppv），如实分两类记，不当失败；④ 010C 站点的 ppv 槽值经 setl/dec/and 合成后解引用，简单寄存器跟踪追不到，「槽只到 +0xc」仍只由 r127a 的符号执行承担；⑤ 若 QI 结果被存进堆结构体后再取用，本轮所有判据都看不见；⑥ 35 个静态容器运行期元素值与计数；⑦ 共用模板展开的充分证明；⑧ 门禁 C11 其余四处永远通过子项、五条不可能行未裁定、窗口表未扩。
'''


if __name__ == '__main__':
    do(RC, 'R14_COMMON', SEC_RC, 1081, marker='## 2.131 R127')
    do(LED, 'LEDGER', SEC_LED, 337, marker='## §1181 R127')
    do(LOCK, 'LEAD_LOCK', SEC_LOCK, 137, marker='GN. R127')
    print('DONE')
