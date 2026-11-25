# -*- coding: utf-8 -*-
"""R126: 追加 R14_COMMON §2.130、台账 §1180、LEAD_LOCK 的下一字母段。

纪律与 r126g 相同：wx 独占备份 -> 断言旧 sha256 与 CR -> 断言新文本零反引号
-> 单次写入 -> 回读校验。
"""
import io, os, sys, hashlib, datetime

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
RC = os.path.join(R14, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')

EXPECT = {
    RC:  ('c3c3b4c245b16d19', 1081),
    LED: ('03c773e13f40fc08', 337),
    LOCK: ('d3d70987e35dca18', 137),
}
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def do(path, tag, new_text, want_cr):
    assert '`' not in new_text, '%s 新文本含反引号' % tag
    old = io.open(path, 'rb').read()
    dst = os.path.join(BK, 'r126_%s.%s.bak' % (tag, TS))
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try:
        os.write(fd, old)
    finally:
        os.close(fd)
    want_sha, want_cr = EXPECT[path]
    assert sha16(old) == want_sha, '%s 旧 sha %s != %s' % (tag, sha16(old), want_sha)
    assert old.count(b'\r') == want_cr, '%s 旧 CR %d != %d' % (tag, old.count(b'\r'), want_cr)

    new = old.decode('utf-8').rstrip('\n') + '\n' + new_text
    nb = new.encode('utf-8')
    with io.open(path, 'wb') as f:
        f.write(nb)
    rb = io.open(path, 'rb').read()
    assert rb == nb, '%s 回读不一致' % tag
    assert rb.count(b'\r') == want_cr, '%s 新 CR %d != %d' % (tag, rb.count(b'\r'), want_cr)
    print('  WROTE %-10s sha %s -> %s  CR=%d  bytes %d -> %d  LF %d -> %d'
          % (tag, sha16(old), sha16(rb), rb.count(b'\r'),
             len(old), len(rb), old.count(b'\n'), rb.count(b'\n')))


SEC_RC = '''
## 2.130 R126 台账：推翻两条「不可分」，0x7e9b40 取得为 IFlyControl；并纠正本轮自己的两处误定名

R126 全部为静态字节测量，可从 gamemd.exe（sha256 73201cc0...fcf67476）逐条复算。本轮不引外部头文件，上限在最后一节写清。

**一 · 0x7e9b40 = IFlyControl（R124 起记「与 0x7f7c70/0x7f7c80 不可分」，本轮推翻）**

AircraftClass 的 QueryInterface 体在 0x414290：先 call 0x410260 委派给基类（AbstractClass 那一层），基类失败才比自己的 IID。0x4142b1 是 mov edi, 0x7e9b40；比对成功后的分支 0x4142c1 是 lea eax, [ebx + 0x6c0]，0x4142c8 是 mov dword ptr [ebp], eax，即把出参写成 this + 0x6c0；失败分支 0x4142da 写 0。

AircraftClass 的 RTTI 共 18 条基类。mdisp 恰为 0x6c0 的有两条：.?AUIFlyControl@@ 与一个 .?AUIUnknown@@，这是多继承子对象的标准配对（每个接口子对象各自带 IUnknown）。剔除 IUnknown 后唯一，即 IFlyControl。全量 954 个类里 mdisp 0x6c0 只出现这一处（反控：换成 0x6c4 命中 0 条）。

独立旁证：0x4177c0 处 lea eax, [esi + 0x6c0] 后紧接 push eax 与 call dword ptr [ecx + 0xc]，即该子对象被按虚表槽 offset 0xc 调用，与 R125 在 0x7f7c70 侧得到的「更窄那个多一个 slot 3」在使用侧一致。全映像 this+0x6c0 共 10 处：1 处是 QI 体写出参，9 处是取子对象地址。

**二 · R124 为什么把它与 IPersist 家族混在一起（结构性原因，不是疏忽）**

同一个类的 RTTI 在 mdisp 0 处并排有 .?AUIPersistStream@@ 与 .?AUIPersist@@。这两个接口自己没有次对象偏移，于是在任何类里都恒占 mdisp 0 —— R124 用的「出参 this 调整值 == RTTI mdisp」这条判据在这两个名字上永远有两条候选，结构上无法分开。R124 把它们记成「三条记录完全对称」是对的；错在把 0x7e9b40 也归进这一组，它走的是 0x6c0。

**三 · 0x7f7cf0 那条「不可分」的表述本身无字节依据**

0x7f7cf0 的 16 字节是 0000000C-0000-0000-C000-000000000046，即标准 IID_IStream。IID_ISequentialStream 是 0C733A30-2A1C-11CE-ADE5-00AA0044773D，它在整份映像里出现 0 次，连 Data1 0x0C733A30 也是 0 次；正控 IStream 的 Data1 0x0000000C 出现 539 次。所以「在 IStream 与 ISequentialStream 之间不可分」不是测不出，而是那个候选根本不在映像里。

**四 · GUID 池与孪生的全量普查（R125 只做了两个 IID）**

窗口起点要按 Data4 模式长度分别算：OLE 系 d4 全 8 字节是模式（C000-0000-0000-0046），MIDL 系只有后 6 字节是模式（前 2 字节是变体号）。统一按 k-8 起算会整体偏移两字节；反控：错口径下 0x7e36c0 与 0x7e9b20 都解不出来。

结果：65 个 GUID 窗口（.rdata 55、.data 10）。整份映像里 16 字节完全相同的孪生共 9 对，每对都是一个 .rdata 配一个 .data，无 .rdata 内自孪生。标准 OLE 前缀（Data1 <= 0x1FF 且 Data2/Data3 全零）恰 10 处、6 个不同 Data1：0x0、0x1、0xC、0x109、0x10C、0x13A；其中 0x0/0xC/0x109/0x10C 各有 .rdata 与 .data 两处，0x1 与 0x13A 只有 .rdata 一处。

**五 · 孪生形态分离的上限（对抗性自审的结论）**

形式 R = mov edi 立即数且前后 8 条内同时有 mov ecx, 4 与 repe cmpsd；形式 C = push 立即数。四对实测（.rdata 侧 R/C，.data 侧 R/C）：0x7f7c90 与 0x817bc0 是 91/56 与 0/9；0x7f7cf0 与 0x81fc50 是 1/0 与 0/2；0x7f7c80 与 0x820270 是 4/60 与 0/8；0x7f7c70 与 0x818858 是 4/0 与 0/16。

分离不纯净：0x7f7c90 与 0x7f7c80 的 .rdata 侧都有形式 C。反向的规律成立：四对的 .data 侧形式 R 全为 0。故能说的只有「.data 那份只被 push 引用，.rdata 那份两种都有」，这不是「谁是 IPersist」的证据。

我原本预期「.data 站点集中在少数函数」也不成立：0x818858 的 16 站点落在 15 或 16 个函数（口径差 1）、0x820270 的 8 站点落在 8 个函数。

**六 · 本轮自己的两处误定名（S-154 与 S-158，已改并留案）**

其一，第一版机制把「mov ecx, 4 + mov edi, IID + repe cmpsd」一律当 QI 体，但调用方也这么写：0x501805 与 0x44dedd 的 esi 来自 lea esi, [esp + 0x24]，是调用方把 GUID 副本放栈上再比。据此我先把 0x7e9550 定成 INoticeSource、0x7e9a50 定成 ReferenceCounted。补上「esi 不得由 lea 取地址」这条必要条件后两个名字同时消失。修正后剩下的三个名字全为 .?AU 前缀（接口），无 .?AV（类）混入，与 R124「.?AU 名字 26 个即 COM 接口」一致。

其二，我在 r126f 断言里写「this+0x6c0 全映像应只有 2 处」，那是估计值不是实测值：实测 10 处。断言已改为实测值。同理 r126f 的「该 QI 体应解出至少 2 个 (IID, 调整值) 对」也是凭直觉设的下限，实测该 QI 体只自己处理 1 个 IID（其余委派给基类），已改为等号。

**七 · 跨家族（规则 D）**

审计员 hy4 task 251 succeeded，50 回合 / 11.28 分钟 vs 派发预算 8.0 分钟，**OVERTIME**，如实记。报告 _r126/audit/r126_audit_hy4.md，151 行，零反引号。数字逐条独立复算（r126d 10 项）：OLE 前缀 10 处 6 个 Data1 一致；形式 R/C 八个数 4/0、0/16、4/60、0/8、91/56、0/9、1/0、0/2 逐个一致；0x7f7cd0 的 Data1 = 0xB196B284 一致；0x7f7c70 末字节翻转后命中 0 次一致。

采纳与不采纳各一处。不采纳它的总结「5 对加 1 个单点」：它自己的表格是 10 处，而 10 处只能蕴含 4 对加 2 单（0x7f7ca0 与 0x7f7d00 各只有 .rdata 一处），我按表格数字复算为 4 对 2 单。采纳它的 0x818858 分散度结论：两支口径给 15 与 16，差 1，两个数都支持「高度分散」，故我把断言写在分散度上而非精确值。

另记一条自错：我在 r126d 初稿把 D5 写成「审计员的 0xB196B284 我复算不出来」，实测审计员对，是我把断言方向写反（S-160），已改。

**八 · 断言与收口**

r126a 11 + r126b 12 + r126c 10 + r126d 10 + r126e 8 + r126f 10 = 61 项全 PASS。全程 disasm_lite 流式扫描，未对整段 .text 开 detail=True；脚本带 timeout；收口前 ps 确认无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0（本轮不改门禁，GATE_VER 仍 R124）。

看板先按 260 行阈值归档最早两段（第 120 轮与第 124 轮整段搬进 BOARD_ARCHIVE.md），归档后看板 CR 仍 0、归档 CR 仍 2952、看板 97 行。

**九 · 未取得（不粉饰）**

1) 0x7f7c70 与 0x7f7c80 谁是 IPersist、谁是 IPersistStream 仍不由字节给出：这两个接口在所有类里恒占 mdisp 0，本轮没找到第三条内部记录能把它们分开。2) 0x7e36c0 与 0x7e9b20 的 QI 体不被任何类的 slot0 引用，本方法对它们只能给出「查了哪些 IID」（两者都查 0x7f7c90），给不出接口名。3) 0x7e9b20 的 QI 体在 0x6cf478 把出参写成 QI 返回值本身、不做 this 调整，其 this 偏移仍是 0。4) 大量 .rdata IID 的站点不落在任何类的 slot0 上，本方法对它们无解，不为此放宽判据。5) 35 个静态容器的运行期元素值与计数。6) 共用模板展开的充分证明。7) 门禁 C11 其余四处永远通过子项、五条不可能行未裁定、窗口表未扩。
'''


SEC_LED = '''
## §1180 R126 台账：推翻两条「不可分」，0x7e9b40 取得为 IFlyControl

R126 全部为静态字节测量，可从 gamemd.exe（sha256 73201cc0...fcf67476）复算。

**0x7e9b40 = IFlyControl**：AircraftClass 的 QI 体在 0x414290，先 call 0x410260 委派基类，失败才比自己的 IID；0x4142b1 是 mov edi, 0x7e9b40，成功分支 0x4142c1 是 lea eax,[ebx+0x6c0]，0x4142c8 是 mov [ebp],eax，即出参 = this+0x6c0；失败分支 0x4142da 写 0。该类 RTTI 18 条基类，mdisp=0x6c0 的有两条：.?AUIFlyControl@@ 与一个 .?AUIUnknown@@（多继承子对象的标准配对），剔除 IUnknown 后唯一。全量 954 类里 mdisp 0x6c0 仅此一处（反控 0x6c4 命中 0）。独立旁证 0x4177c0：lea eax,[esi+0x6c0] 后接 push 与 call [ecx+0xc]，按 slot 3 调用。

**R124 混淆的结构原因**：同类 RTTI 在 mdisp 0 处并排有 .?AUIPersistStream@@ 与 .?AUIPersist@@；这两个接口自身无次对象偏移，在任何类里恒占 mdisp 0，故「出参调整值 == mdisp」这条判据对它们永远有两条候选，结构上分不开。R124 记它们对称是对的；把 0x7e9b40 归进这一组是错的。

**0x7f7cf0 的「不可分」无依据**：0x7f7cf0 的 16 字节即标准 IID_IStream（0000000C-...）。IID_ISequentialStream 是 0C733A30-2A1C-11CE-ADE5-00AA0044773D，整份映像出现 0 次，连 Data1 也 0 次（正控 IStream 的 Data1 0x0000000C 出现 539 次）。

**池与孪生全量普查**：窗口起点按 Data4 模式长度分别算（OLE 系 d4 全 8 字节是模式，MIDL 系只有后 6 字节是模式）；统一按 k-8 会偏移两字节，反控下 0x7e36c0 与 0x7e9b20 都解不出。得 65 个窗口（.rdata 55、.data 10），整映像 16 字节孪生 9 对，每对一个 .rdata 配一个 .data。标准 OLE 前缀恰 10 处 6 个 Data1（0x0/0x1/0xC/0x109/0x10C/0x13A），其中 4 个有双份、0x1 与 0x13A 只有 .rdata。

**形态分离的上限**：四对实测 .rdata 侧 R/C 与 .data 侧 R/C 为 91/56 与 0/9、1/0 与 0/2、4/60 与 0/8、4/0 与 0/16。分离不纯净（0x7f7c90、0x7f7c80 的 .rdata 侧都有形式 C），但反向规律成立：四对 .data 侧形式 R 全为 0。故只能说「.data 那份只被 push 引用、.rdata 那份两种都有」，不是身份证据。我原预期的「.data 站点集中少数函数」不成立：0x818858 的 16 站点落在 15 或 16 个函数、0x820270 的 8 站点落在 8 个函数。

**本轮自错两处**：一，第一版把「mov ecx,4 + mov edi,IID + repe cmpsd」一律当 QI 体，但 0x501805 与 0x44dedd 的 esi 来自 lea esi,[esp+0x24]，是调用方比 GUID 副本；据此误把 0x7e9550 定成 INoticeSource、0x7e9a50 定成 ReferenceCounted，补上「esi 不得由 lea 取地址」后两名字消失，剩余三个全为 .?AU 接口前缀。二，r126f 里「this+0x6c0 应只有 2 处」是估计值，实测 10 处，已改。

**跨家族**：审计员 hy4 task 251 succeeded，50 回合 / 11.28 分钟 vs 预算 8.0 分钟，OVERTIME。报告 151 行零反引号。数字逐条复算（r126d 10 项）全部一致：OLE 前缀 10 处 6 个 Data1、形式 R/C 八个数、0x7f7cd0 的 Data1=0xB196B284、翻转末字节命中 0。不采纳其总结「5 对加 1 单」（其表格 10 处只能蕴含 4 对加 2 单）；采纳其 0x818858 分散度结论（两支口径 15 与 16 差 1，都支持高度分散）。

**断言**：r126a 11 + r126b 12 + r126c 10 + r126d 10 + r126e 8 + r126f 10 = 61 项全 PASS。未对整段 .text 开 detail=True；脚本带 timeout；无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0。看板按 260 行阈值先归档最早两段，归档后看板 97 行、CR 0，归档 CR 2952。

**未取得**：① IPersist 与 IPersistStream 谁是 0x7f7c70 谁是 0x7f7c80 仍不由字节给出（两者恒占 mdisp 0）；② 0x7e36c0 与 0x7e9b20 的 QI 体不被任何类 slot0 引用，只知都查 0x7f7c90；③ 0x7e9b20 出参写成 QI 返回值本身、this 偏移为 0；④ 大量 .rdata IID 站点不落在任何类 slot0；⑤ 35 个容器运行期值；⑥ 共用模板充分证明；⑦ 门禁 C11 剩余子项与不可能行。
'''


SEC_LOCK = '''
FY. R126 主攻 R125 台账 GK 里那两条「不可分」。六套脚本 61 项断言全 PASS，全部可从字节复算。两条都被推翻，另纠正本轮自己的两处误定名。

GA. 0x7e9b40 = IFlyControl。AircraftClass 的 QI 体在 0x414290：先 call 0x410260 委派基类，基类失败才比自己的 IID。0x4142b1 是 mov edi, 0x7e9b40；成功分支 0x4142c1 是 lea eax, [ebx + 0x6c0]，0x4142c8 是 mov dword ptr [ebp], eax，即出参 = this + 0x6c0；失败分支 0x4142da 写 0。该类 RTTI 18 条基类，mdisp = 0x6c0 的是 .?AUIFlyControl@@ 与一个 .?AUIUnknown@@ 两条（多继承子对象的标准配对），剔除 IUnknown 后唯一。全量 954 类里 mdisp 0x6c0 仅此一处，反控换成 0x6c4 命中 0 条。

GB. 独立旁证：0x4177c0 是 lea eax, [esi + 0x6c0]，紧接 push eax 与 call dword ptr [ecx + 0xc]，即该子对象被按虚表槽 offset 0xc 调用。这与 R125 在 0x7f7c70 侧得到的「更窄那个多一个 slot 3」在使用侧一致。全映像 this+0x6c0 共 10 处：1 处 QI 体写出参、9 处取子对象地址。

GC. R124 为什么会把它与 IPersist 家族混在一起，原因在结构不在疏忽：同一个类的 RTTI 在 mdisp 0 处并排有 .?AUIPersistStream@@ 与 .?AUIPersist@@。这两个接口自身没有次对象偏移，于是在任何类里恒占 mdisp 0 —— R124 的判据「出参调整值 == RTTI mdisp」对它们永远有两条候选，结构上永远分不开。R124 记这两个对称是对的；错在把 0x7e9b40 也归进这一组。

GD. 0x7f7cf0 那条「在 IStream 与 ISequentialStream 之间不可分」的表述本身无字节依据：该地址 16 字节即标准 IID_IStream（0000000C-0000-0000-C000-000000000046）。IID_ISequentialStream 是 0C733A30-2A1C-11CE-ADE5-00AA0044773D，整份映像出现 0 次，连 Data1 0x0C733A30 也是 0 次；正控 IStream 的 Data1 0x0000000C 出现 539 次。所以不是测不出，是那个候选不在映像里。

GE. GUID 池与孪生的全量普查（R125 只做了两个 IID）：窗口起点必须按 Data4 模式长度分别算 —— OLE 系 d4 全 8 字节是模式，MIDL 系只有后 6 字节是模式、前 2 字节是变体号；统一按 k-8 会整体偏移两字节，反控下 0x7e36c0 与 0x7e9b20 都解不出来。结果 65 个窗口（.rdata 55、.data 10），整映像 16 字节孪生 9 对，每对一个 .rdata 配一个 .data，无 .rdata 内自孪生。标准 OLE 前缀恰 10 处、6 个 Data1：0x0、0x1、0xC、0x109、0x10C、0x13A；其中四个有双份，0x1 与 0x13A 只有 .rdata 一处。

GF. 形态分离的上限（对抗性自审）：四对实测（.rdata 侧 R/C，.data 侧 R/C）为 91/56 与 0/9、1/0 与 0/2、4/60 与 0/8、4/0 与 0/16。分离不纯净：0x7f7c90 与 0x7f7c80 的 .rdata 侧都有形式 C。反向规律成立：四对的 .data 侧形式 R 全为 0。故只能说「.data 那份只被 push 引用、.rdata 那份两种都有」，这不是身份证据。我原本预期「.data 站点集中在少数函数」也不成立：0x818858 的 16 站点落在 15 或 16 个函数、0x820270 的 8 站点落在 8 个函数。

GG. 本轮自错两处，都记在案。S-154：第一版机制把「mov ecx, 4 + mov edi, IID + repe cmpsd」一律当 QI 体，但调用方也这么写 —— 0x501805 与 0x44dedd 的 esi 来自 lea esi, [esp + 0x24]，是调用方把 GUID 副本放栈上再比。据此我先把 0x7e9550 定成 INoticeSource、0x7e9a50 定成 ReferenceCounted。补上「esi 不得由 lea 取地址」这条必要条件后两个名字同时消失；修正后剩的三个名字全为 .?AU 接口前缀，无 .?AV 类名混入。S-158：r126f 里「this+0x6c0 应只有 2 处」是估计值不是实测，实测 10 处，断言已改。另 S-160：r126d 初稿把 D5 写成「审计员的 0xB196B284 我复算不出来」，实测审计员对，是我把方向写反，已改。

GH. 规则 D：审计员 hy4 task 251 succeeded，50 回合 / 11.28 分钟，派发预算 8.0 分钟 ⇒ OVERTIME 如实记。报告 _r126/audit/r126_audit_hy4.md，151 行，零反引号。数字逐条独立复算（r126d 10 项）全部一致：OLE 前缀 10 处 6 个 Data1、形式 R/C 八个数 4/0、0/16、4/60、0/8、91/56、0/9、1/0、0/2、0x7f7cd0 的 Data1 = 0xB196B284、0x7f7c70 末字节翻转后命中 0 次。

GI. 采纳与不采纳各一处。不采纳它的总结「5 对加 1 个单点」：它自己的表格是 10 处，而 10 处只能蕴含 4 对加 2 单（0x7f7ca0 与 0x7f7d00 各只有 .rdata 一处），我按表格数字复算为 4 对 2 单，采纳表格不采纳总结。采纳它的 0x818858 分散度结论：两支口径给 15 与 16，差 1，两个数都支持高度分散，故把断言写在分散度上而非精确值。

GJ. 断言与收口：r126a 11 + r126b 12 + r126c 10 + r126d 10 + r126e 8 + r126f 10 = 61 项全 PASS。全程 disasm_lite 流式扫描，未对整段 .text 开 detail=True；脚本带 timeout；收口前 ps 确认无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0（GATE_VER 仍 R124，本轮不改门禁）。看板按 260 行阈值先归档最早两段（第 120 轮与第 124 轮整段搬进 BOARD_ARCHIVE.md），归档后看板 97 行、CR 仍 0，归档 CR 仍 2952。

GK. 未取得（不粉饰）：① 0x7f7c70 与 0x7f7c80 谁是 IPersist、谁是 IPersistStream 仍不由字节给出 —— 这两个接口在所有类里恒占 mdisp 0，本轮没找到第三条内部记录能把它们分开；② 0x7e36c0 与 0x7e9b20 的 QI 体不被任何类的 slot0 引用，本方法只能给出「查了哪些 IID」（两者都查 0x7f7c90），给不出接口名；③ 0x7e9b20 的 QI 体在 0x6cf478 把出参写成 QI 返回值本身、不做 this 调整，this 偏移仍是 0；④ 大量 .rdata IID 的站点不落在任何类 slot0 上，本方法对它们无解，不为此放宽判据；⑤ 35 个静态容器运行期元素值与计数；⑥ 共用模板展开的充分证明；⑦ 门禁 C11 其余四处永远通过子项、五条不可能行未裁定、窗口表未扩。
'''


do(RC, 'R14_COMMON', SEC_RC, 1081)
do(LED, 'LEDGER', SEC_LED, 337)
do(LOCK, 'LEAD_LOCK', SEC_LOCK, 137)
print('DONE')
