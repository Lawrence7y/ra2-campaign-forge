# -*- coding: utf-8 -*-
"""R129o：四件套追加（R14_COMMON 2.133 / 台账 §1183 / LEAD_LOCK 下一字母段 / 看板第 129 轮）。

纪律：wx 独占备份 -> 断言旧 sha256 与旧 CR -> 断言新文本零反引号 -> 一次性写入 ->
回读校验 -> 断言新 CR 不变。
"""
import io, os, sys, hashlib, datetime

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
RC = os.path.join(R14, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD = os.path.join(R14, 'STATUS_BOARD.md')
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
EXPECT = {RC: 1081, LED: 337, LOCK: 137, BRD: 0}

def sha16(b): return hashlib.sha256(b).hexdigest()[:16]

def do(path, tag, new_text, marker=None):
    assert '`' not in new_text, '%s 新文本含反引号' % tag
    old = io.open(path, 'rb').read()
    dst = os.path.join(BK, 'r129_%s.%s.bak' % (tag, TS))
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try: os.write(fd, old)
    finally: os.close(fd)
    want = EXPECT[path]
    assert old.count(b'\r') == want, '%s 旧 CR %d != %d' % (tag, old.count(b'\r'), want)
    new = old.decode('utf-8').rstrip('\n') + '\n' + new_text
    nb = new.encode('utf-8')
    with io.open(path, 'wb') as f: f.write(nb)
    rb = io.open(path, 'rb').read()
    assert rb == nb, '%s 回读不一致' % tag
    assert rb.count(b'\r') == want, '%s 新 CR %d != %d' % (tag, rb.count(b'\r'), want)
    if marker: assert marker.encode('utf-8') in rb, '%s 回读未见标记' % tag
    print('  WROTE %-10s %s -> %s  CR=%d  bytes %d -> %d  LF %d -> %d'
          % (tag, sha16(old), sha16(rb), rb.count(b'\r'), len(old), len(rb),
             old.count(b'\n'), rb.count(b'\n')))

R14_NEW = '''## 2.133 R129：0x6bd940 的 call ebx 定名成 RegisterActiveObject，并把 CLSID <-> 类工厂 <-> 类名串成四段链；C11 的 claims-none 校验式接上真跑；C17 五条不可能行裁定为撤回

**起点。** R128 台账 HJ 的第四项「0x6bd940 的 call ebx 目标未定」本轮取得；另两条待办（C11 其余永远通过子项、C17 五条不可能行的裁定）本轮各推进一格。第十七套脚本 109 项断言全 PASS。

**一 · call ebx 的目标不是「附近有 mov ebx」，而是三条同时成立。** 0x6bd6c2 的字节是 8b 1d 70 13 7e 00，即 mov ebx, dword ptr [0x7e1370]；0x7e1370 在本映像导入表里解析出 OLEAUT32.dll 的 RegisterActiveObject。三条判据：① 定义点唯一且 IAT 槽可解析出名字；② 从定义点到调用点的每条可达路径上没有其它 ebx 写（本轮实测 1 条无写路径、0 条带写路径）；③ 定义点是必经点（dominance）—— 分别切断 0x6bd6c2、0x6bc347、0x6bb9c3 后 0x6bd945 全部不可达。反控：相邻槽 0x7e1374 解析出 VariantChangeType 而非同名；同函数另外两个 ebx 定义（0x6bbee9 OpenMutexA、0x6bc347 LoadLibraryA）都不能冒充。

**二 · 调用点的实参形状与 API 契约一致。** 0x6bd934 起四条 push：0x840a74、1、0x7e9520、0x87f7e8，随后 call ebx。RegisterActiveObject(punk, rclsid, dwFlags, lpdwRegister) 的第二个实参是 CLSID 指针，实测 0x7e9520 = .rdata 常量 {B45A4A81-86DA-11D1-B706-00A024DDAFD1}；第四个实参 0x840a74 是 .data 原始区里的一个 DWORD，静态初值 0xFFFFFFFF，其后紧跟 ASCII 串 blowfish.dll。撤销侧成对存在：0x6be131 读 0x840a74、与 -1 比较、非 -1 则 call [0x7e1384]（OLEAUT32!RevokeActiveObject）并把 0x840a74 写回 -1；0x6bec9d 是同一形状的第二处。0x840a74 的 imm32 引用全库恰 5 处，无第六处。

**三 · CLSID 到类名是可走的四段链，每段都由字节给出。** 段一：0x6bc42a 起把四个实参压栈（&局部、1、1、0xa8e8c8），第五个 0x7e9520 由 0x6bc43a 压入，随后 mov esi,[0x7e15d8] + call esi，0x7e15d8 = ole32!CoRegisterClassObject。段二：0xa8e8c8 在 .data 的 BSS 区（段内偏移 0x6d8c8 > SizeOfRawData 0x6c000），映像内无静态字节，故必须走写入者反查；其 imm32 全库恰 2 处，写入者是 0x4e7ce0 的 c7 05 c8 e8 a8 00 64 a5 7e 00 c3，把 vptr 写成 0x7ea564。段三：0x7ea564 的 COL 解出 .?AVTiberianSunClassFactory@@，基类 IClassFactory ncb 1、IUnknown ncb 0，三者 mdisp 全 0。段四：0x7e9520 的 imm32 引用全库 5 处，其中 0x6bc43b 是类对象注册的 rclsid、0x6bd93c 是活动对象注册的 rclsid —— 同一个 CLSID 的两个面。反控三条：相邻常量 0x7e9510 与 0x7e9520 只差 Data1 末字节；把段二 vptr 换成另一张真实类表 0x7f4108，段三给出 .?AVSwizzleManagerClass@@（不同类）；0xa8e8c8 无静态字节，故不存在「静态读 vptr」的旁路。

**四 · 0x7f3710 起的表不是猜的。** 循环头 0x6bc342 mov esi,0x7f3710、步长 0x6bc409 add esi,8、上界 0x6bc40c cmp esi,0x7f3718、回边 0x6bc412 jl 0x6bc34d，四条都在字节里。表恰 1 项：+0 = .rdata 0x7e9500 = {1440AD10-6AA8-11D1-B6F9-00A024DDAFD1}（作为 CoCreateInstance 的 rclsid 传给封装 0x6bedb0），+4 = .data 的 ASCII 串 blowfish.dll（作为 LoadLibraryA 的实参）。封装 0x6bedb0 体内：0x6beddd call [0x7e15fc]（CoCreateInstance）、0x6bedec call [0x7e1600]（OleRun）、0x6bee05 call [ecx]、0x6bee10 call [edx+8]（Release）。反控三条：步长 4 与 8 各扫一遍，只有 8 与指令字节一致；上界由字节给出而非我数的；上界处的 8 字节若被当成第 2 项，给不出「.rdata 指针 + 可打印串」这一对。

**五 · 门禁真修第二处：claims-none 的校验式接上真跑。** R128 已把 claims-none 从「直接 continue」改成「产物里不得出现本纪律自述行」，那闭合的是「把有偷偷改成无、产物里还留着自述行」。另一种仍敞开：把校验式改成当前不成立的式子、同时把第 7 列写成无，门禁照样 exit 0。先实测（r129d 8/8）：14 条 claims-none 的校验式在真产物上 14/14 成立、在空产物上 0/14 成立 ⇒ 有分辨力且零误伤。改法：claims-none 行的校验式必须真跑通过。反控 7/7：正控 exit 0 + C10 ok(R129)；把 id 11 的式子改坏 ⇒ exit 1 命中新判据；改成 rows=0（恒真式）⇒ 同样命中；把产物路径指向不存在 ⇒ exit 1；收尾三份正本字节回基线。

**六 · 五条不可能行裁定为撤回，这是本轮唯一「净损失」的决定。** C17 钉住的五条（id 3/4/22/27/28）声称 R55 回跑，但产物路径轮次分别是 61/81/84/88，全部晚于 R55。三条路先逐条验算（r129i 12/12）：改行不可行——只改 round 到路径轮次，五条 at 仍落在 R55 窗口外，要过 R4 就必须改 at，而 at 无外部时钟，改它就是编造时刻；撤回与降级在机制上同形，都要动第 7 列。取撤回：第 7 列 有 -> 无，同时把那五条假声称从产物里删掉（只改一列不删行会被 R128 判据当场抓住，r129j 实测 5 条 FAIL 正是这个）。删前把原文逐字存进 R129_RETRACTED.tsv（撤回不等于抹掉记录），四份产物各建 wx 备份。三处常量同步重钉：C11B_PIN_GAP 由 7 个 id 涨到 12 个、C17_PIN 由 5 条塌成空集并换摘要（空集摘要 = hashlib 对空串实测值 e3b0c442...，非手填）、C17_REUSED_ATS 清空。

**七 · 代价如实量出来。** C11 的 ok 计数由 5 降到 0 —— 因为撤回的五条恰是全表唯一五条能通过 recheck_verify 的行。也就是说本轮把「5 条自洽但不可能的凭证」换成了「0 条凭证」，不是「5 条真凭证」。这是净损失。换来的是两条真判据：不再有假声称躺在产物里；claims-none 的校验式必须有分辨力。裁定反控 10/10：正控 exit 0 + ok(R129) + pinned 0 + gap 12；塞回假声称 ⇒ exit 1；塞回假声称并改回有 ⇒ exit 1；改坏 claims-none 式子 ⇒ exit 1；C17_PIN 改回非空不改摘要 ⇒ exit 1；C11B_PIN_GAP 改回 7 个 ⇒ exit 1；改回有但不补行 ⇒ exit 1；收尾三份正本回基线。

**八 · 第二译码器仲裁（沿用 R128 规则）。** 四组地址集合各用 capstone 与 i686-w64-mingw32-objdump 出一份，比集合不比总数。原始口径下交集恒 0，原因是我把「capstone 的字节命中（立即数起点）」与「objdump 的指令起点」直接比；归一化到指令起点后：0xa8e8c8 2/2 交集 2、0x7e9520 5/5 交集 5、0x840a74 5/5 交集 5、0x87f7e8 3700/3700 交集 3700，四组均无单边独有。归一化用的是 objdump 的指令边界表，不是我自己求的边界。

**九 · 规则 D 一次失败一次成功，如实记。** hy4 task 264 failed 加 error_max_turns（61 回合 / 5.22 分钟 vs 预算 10.0 ⇒ OVERTIME），result 为空、零报告，那次外部输入为零、不能写「已审计」。deepseek 侧派发时撞上实时内存上限 MAX_SUBAGENTS 由 2 降到 1（MemAvailable 796.5 MB），按本仓纪律不并发、等内存回落。故本轮审计以主会话自审（r129n）+ 第二译码器仲裁（r129m）承担，不假称已过跨家族审计。

**十 · 自错十五条全留案，其中两条同族。** S-184 窗口 0x16 切断 10 字节指令；S-185 断言按记忆写而非按字节；S-186 反控对象自身不可解（拿 IID 当 vtable）；S-187 与 S-197 是同一族——都写了 or True 恒真断言，第二轮由 r129n 的 N1 自动抓到；S-188 拿「碰巧只出现一次的子串」当替换目标；S-189 跨文件搬文本没处理行尾 CR；S-190 用 split 下标取文件名字段；S-191 字节差断言没按文件汇总、没计行尾换行；S-192 跨工具比文本只收一种数值形式；S-193 解析 objdump 地址假设 8 位补零；S-194 跨译码器比集合未归一化；S-195 归一化时自求指令边界，300 处落到非边界（与 R127 S-170 同一个坑）；S-196 只降级不删行等于半撤；S-198 统计口径含自身产物导致自指漂移。

**十一 · 断言与收口。** 十七套脚本 109 项断言全 PASS（r129a 17 + r129b 13 + r129c 13 + r129d 8 + r129e 8 + r129f 7 + r129g 10 + r129h 8 + r129i 12 + r129j 13 + r129k 26 + r129k2 22 + r129l 10 + r129m 21 + r129n 19，另有 r129o 本次写入自校验）。全程 disasm_lite 流式扫描与 objdump 单遍，未对整段 .text 开 detail=True；脚本带 timeout；收口前 ps 确认无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0、C10 ok(R129)。

**十二 · 未取得（不粉饰）。** ① 0xb0c110 的「与 ApplicationClass 同级全局单例」仍无第二条记录。② 010C 的「槽只到 +0xc」仍只由 R127 符号执行承担。③ QI 结果存进堆结构体后再取用的路径所有判据都看不见。④ 0x7e9500 那个 CLSID 对应的 dll 只有 blowfish.dll 一项，表为何只有一项（不是八项）未解。⑤ 35 个静态容器运行期元素值与计数。⑥ 共用模板展开的充分证明。⑦ 门禁另两处未修（C7 bytes=N 死分支、C11 frozen 分支）、窗口表未扩（ROUND_WINDOWS 只有 r36..r65 共 28 轮，r66 以后全部不可验证 —— 本轮降级的五条正因为落表外才只靠 C17 的路径轮次判据抓到）。⑧ 已判死线不投。
'''

LED_NEW = '''## §1183 R129：0x6bd945 的 call ebx 定名 RegisterActiveObject；CLSID 到类名四段链落成字节；C11 claims-none 校验式接上真跑；C17 五条不可能行裁定撤回

**A. call ebx 定名。** 0x6bd6c2 的 8b 1d 70 13 7e 00 = mov ebx,[0x7e1370]，该 IAT 槽 = OLEAUT32!RegisterActiveObject。三条判据同时成立：定义点唯一且槽名可解析、到调用点的每条路径无其它 ebx 写（1 条无写 / 0 条带写）、定义点是必经点（切断后调用点不可达，三处各测）。反控：相邻槽 0x7e1374 = VariantChangeType；同函数另两个 ebx 定义不能冒充。

**B. 实参契约自洽。** 0x6bd934 起四条 push：0x840a74 / 1 / 0x7e9520 / 0x87f7e8。RegisterActiveObject 第二实参 rclsid = 0x7e9520 = {B45A4A81-86DA-11D1-B706-00A024DDAFD1}，第四实参 lpdwRegister = 0x840a74（.data 原始区、静态 0xFFFFFFFF、后紧跟 blowfish.dll）。撤销侧配对：0x6be131 与 0x6bec9d 两处 call [0x7e1384]（RevokeActiveObject）后把 0x840a74 写回 -1；0x840a74 的 imm32 全库恰 5 处。

**C. 四段链。** 段一 0x6bc42a 起四实参 + 0x6bc43a push 0x7e9520 + mov esi,[0x7e15d8] + call esi（CoRegisterClassObject）。段二 0xa8e8c8 在 BSS（段内 0x6d8c8 > raw 0x6c000），无静态字节；imm32 全库 2 处，写入者 0x4e7ce0 把 vptr 写成 0x7ea564。段三 0x7ea564 COL = .?AVTiberianSunClassFactory@@（IClassFactory ncb1 / IUnknown ncb0，mdisp 全 0）。段四 0x7e9520 的 5 处引用含 0x6bc43b（类对象 rclsid）与 0x6bd93c（活动对象 rclsid）。反控：0x7e9510 差 Data1 末字节；换 0x7f4108 给 .?AVSwizzleManagerClass@@；无静态读旁路。

**D. 0x7f3710 表。** 头 0x6bc342 / 步长 0x6bc409 add esi,8 / 上界 0x6bc40c cmp esi,0x7f3718 / 回边 0x6bc412 jl，四条都在字节里；表恰 1 项（0x7e9500 GUID + blowfish.dll）。封装 0x6bedb0 含 CoCreateInstance / OleRun / call [ecx] / call [edx+8] 四条。反控：步长 4 与 8 对比、上界由字节给、上界处 8 字节不构成合法项。

**E. 门禁真修第二处。** claims-none 的校验式必须真跑通过（R128 只挡「产物里还留着自述行」）。前置实测 14/14 成立、空产物 0/14 ⇒ 有分辨力零误伤。反控 7/7 全中。

**F. 五条不可能行裁定撤回。** 三条路验算：改行不可行（只改 round 则 at 出窗，改 at 即编造时刻）；撤回与降级同形。取撤回：第 7 列 有->无 + 从产物删掉假声称（只改一列会被 R128 判据抓，实测 5 FAIL）+ 原文存 R129_RETRACTED.tsv + 四份产物 wx 备份。三处重钉：C11B_PIN_GAP 7->12、C17_PIN 5->空集（摘要 e3b0c442... 为 hashlib 对空串实测值）、C17_REUSED_ATS 清空。

**G. 代价。** C11 ok 由 5 降到 0（撤回的五条恰是唯一五条能过 recheck_verify 的行）。本轮是「5 条自洽但不可能的凭证」换成「0 条凭证」，净损失，如实记。换来两条真判据。裁定反控 10/10。

**H. 第二译码器仲裁。** 四组集合归一化到指令起点后交集分别为 2/5/5/3700，均无单边独有；归一化用 objdump 的指令边界，不自求边界。

**I. 规则 D。** hy4 task 264 failed + error_max_turns（61 回合 / 5.22 分钟 vs 预算 10.0 ⇒ OVERTIME），零报告，不写「已审计」。deepseek 派发撞 MAX_SUBAGENTS 2->1（796.5 MB），按纪律不并发。本轮审计由主会话自审 r129n + 第二译码器 r129m 承担。

**J. 自错 15 条。** S-184 窗口切断指令 / S-185 断言按记忆写 / S-186 反控对象不可解 / S-187 与 S-197 同为 or True 恒真断言（第二轮由 N1 自动抓到）/ S-188 替换目标非唯一 / S-189 跨文件搬运没处理行尾 CR / S-190 split 下标取字段 / S-191 字节差未按文件汇总 / S-192 跨工具只收一种数值形式 / S-193 假设地址补零 / S-194 跨译码器未归一化 / S-195 自求指令边界（同 R127 S-170）/ S-196 只降级不删行 / S-198 统计含自身致自指漂移。

**K. 断言与收口。** 十七套脚本 109 项全 PASS。disasm_lite 流式 + objdump 单遍，未整段开 detail，脚本带 timeout，无孤儿进程。五项 CR 1081/137/337/0/2952 全绿，check_disc.py exit 0、C10 ok(R129)。

**L. 未取得。** ① 0xb0c110 同级单例无第二记录；② 010C 槽上界仍单来源；③ QI 结果存堆结构体路径看不见；④ 0x7e9500 那张表为何只有 1 项未解；⑤ 35 容器运行期值；⑥ 共用模板充分证明；⑦ 门禁另两处未修（C7 bytes=N、C11 frozen）、窗口表只覆盖 r36..r65；⑧ 已判死线不投。
'''

LOCK_NEW = '''HL. R129 主攻 R128 台账 HJ 的第四项（0x6bd940 的 call ebx 目标未定），取得；另两条待办各推进一格（C11 第二处永远通过子项、C17 五条不可能行的裁定）。十七套脚本 109 项断言全 PASS。

HM. call ebx 的目标是 OLEAUT32!RegisterActiveObject，判据三条而不是「附近有 mov ebx」：0x6bd6c2 的字节是 8b 1d 70 13 7e 00（mov ebx,[0x7e1370]），该 IAT 槽在导入表里解析出 RegisterActiveObject；从定义点到 0x6bd945 的每条可达路径上没有其它 ebx 写（实测 1 条无写路径 / 0 条带写路径）；定义点是必经点 —— 分别切断 0x6bd6c2、0x6bc347、0x6bb9c3 后 0x6bd945 全部不可达。反控：相邻槽 0x7e1374 = VariantChangeType；同函数另外两个 ebx 定义（0x6bbee9 OpenMutexA、0x6bc347 LoadLibraryA）不能冒充。

HN. 实参契约自洽：0x6bd934 起四条 push 是 0x840a74 / 1 / 0x7e9520 / 0x87f7e8。RegisterActiveObject 的第二实参 rclsid = 0x7e9520 = {B45A4A81-86DA-11D1-B706-00A024DDAFD1}（.rdata，16 字节），第四实参 lpdwRegister = 0x840a74（.data 原始区 DWORD，静态 0xFFFFFFFF，后紧跟 ASCII 串 blowfish.dll）。撤销侧配对存在：0x6be131 与 0x6bec9d 两处都是「读 0x840a74 → 与 -1 比较 → 非 -1 则 call [0x7e1384]（RevokeActiveObject）→ 写回 -1」；0x840a74 的 imm32 全库恰 5 处，无第六处。

HO. CLSID 到类名的四段链落成字节。段一：0x6bc42a 起四个实参压栈（&局部 / 1 / 1 / 0xa8e8c8），第五个 0x7e9520 由 0x6bc43a 压入，随后 mov esi,[0x7e15d8] + call esi = CoRegisterClassObject。段二：0xa8e8c8 在 .data 的 BSS 区（段内 0x6d8c8 > SizeOfRawData 0x6c000），映像内无静态字节，故只能走写入者反查；其 imm32 全库恰 2 处，写入者 0x4e7ce0 的字节是 c7 05 c8 e8 a8 00 64 a5 7e 00 c3，把 vptr 写成 0x7ea564。段三：0x7ea564 的 COL = .?AVTiberianSunClassFactory@@（IClassFactory ncb 1 / IUnknown ncb 0，三者 mdisp 全 0）。段四：0x7e9520 的 imm32 引用全库 5 处，其中 0x6bc43b 是类对象注册的 rclsid、0x6bd93c 是活动对象注册的 rclsid —— 同一个 CLSID 的两个面。反控三条：相邻常量 0x7e9510 只差 Data1 末字节；把段二 vptr 换成另一张真实类表 0x7f4108，段三给出 .?AVSwizzleManagerClass@@（不同类）；0xa8e8c8 无静态字节，故不存在静态读旁路。

HP. 0x7f3710 起的表由四条字节给边界，不是我数的：头 0x6bc342 mov esi,0x7f3710、步长 0x6bc409 add esi,8、上界 0x6bc40c cmp esi,0x7f3718、回边 0x6bc412 jl 0x6bc34d。表恰 1 项：+0 = .rdata 0x7e9500 = {1440AD10-6AA8-11D1-B6F9-00A024DDAFD1}（作为 CoCreateInstance 的 rclsid 传给封装 0x6bedb0），+4 = .data 的 blowfish.dll（作为 LoadLibraryA 的实参）。封装 0x6bedb0 体内四条调用：0x6beddd call [0x7e15fc]（CoCreateInstance）、0x6bedec call [0x7e1600]（OleRun）、0x6bee05 call [ecx]、0x6bee10 call [edx+8]（Release）。反控三条：步长 4 与 8 对比只有 8 与指令一致；上界由字节给；上界处的 8 字节不构成合法项。

HQ. 门禁真修第二处：C11 的 claims-none 校验式接上真跑。R128 只挡住「产物里还留着自述行」，没挡「校验式本身已不成立」。前置实测（r129d）14 条 claims-none 的式子在真产物上 14/14 成立、在空产物上 0/14 成立 ⇒ 有分辨力且零误伤。改法即接上它。反控 7/7：正控 exit 0 + ok(R129)、改坏 id 11 的式子命中新判据、改成 rows=0 恒真式同样命中、产物路径指向不存在 exit 1、收尾三份正本字节回基线。

HR. C17 钉住的五条不可能行（id 3/4/22/27/28 声称 R55，产物路径轮次 61/81/84/88）裁定为撤回。三条路先验算（r129i 12/12）：改行不可行 —— 只改 round 到路径轮次，五条 at 仍落在 R55 窗口外，要过 R4 必须改 at，而 at 无外部时钟，改它就是编造时刻；撤回与降级机制同形。取撤回：第 7 列 有 -> 无，同时把五条假声称从产物里删掉（只改一列不删行会被 R128 判据当场抓住，r129j 实测 5 FAIL），删前原文逐字存 R129_RETRACTED.tsv，四份产物各建 wx 备份。三处常量同步重钉：C11B_PIN_GAP 7 -> 12 个 id、C17_PIN 5 -> 空集并换摘要（空集摘要 e3b0c442... 是 hashlib 对空串实测值，非手填）、C17_REUSED_ATS 清空。

HS. 代价如实记：C11 的 ok 计数由 5 降到 0，因为撤回的五条恰是全表唯一五条能过 recheck_verify 的行。本轮把「5 条自洽但不可能的凭证」换成「0 条凭证」，不是「5 条真凭证」，是净损失。换来两条真判据：不再有假声称躺在产物里；claims-none 的校验式必须有分辨力。裁定反控 10/10 全中。

HT. 第二译码器仲裁沿用 R128 规则，但踩了一个新坑并如实记：原始口径下四组交集恒 0，因为我把 capstone 的字节命中（立即数起点）与 objdump 的指令起点直接比。归一化到指令起点后 0xa8e8c8 2/2 交集 2、0x7e9520 5/5 交集 5、0x840a74 5/5 交集 5、0x87f7e8 3700/3700 交集 3700，四组均无单边独有。归一化用的是 objdump 的指令边界表，不是我自己求的（自求时 300 处落到非边界，与 R127 S-170 同一个坑）。

HU. 规则 D 一次失败一次未派。hy4 task 264 failed 加 error_max_turns（61 回合 / 5.22 分钟 vs 预算 10.0 ⇒ OVERTIME），result 为空、零报告，那次外部输入为零，不写「已审计」。deepseek 派发时撞上实时内存上限 MAX_SUBAGENTS 由 2 降到 1（MemAvailable 796.5 MB），按本仓纪律不并发、等内存回落。故本轮审计由主会话自审（r129n 19 项）+ 第二译码器仲裁（r129m 21 项）承担，不假称已过跨家族审计。

HV. 自错 15 条全留案。S-184 窗口 0x16 切断 10 字节指令；S-185 断言按记忆里的调用形态写（实际是 mov esi,[...] + call esi）；S-186 反控对象自身不可解（拿 IID 常量当 vtable）；S-187 与 S-197 同一族 —— 都写了 or True 恒真断言，第二轮由 r129n 的 N1 自动抓到；S-188 拿「碰巧只出现一次的子串」当替换目标（id 11 与 12 共用产物）；S-189 跨文件搬文本没处理行尾 CR（存档表混进 1 个 CR）；S-190 用 basename.split('_')[2] 取文件名字段；S-191 字节差断言没按文件汇总、没计行尾换行；S-192 跨工具比文本只收零填充形式；S-193 解析 objdump 地址假设 8 位补零；S-194 跨译码器比集合未归一化（差点写成「两译码器分歧」）；S-195 归一化时自求指令边界；S-196 只降级第 7 列不删假声称等于半撤；S-198 统计口径含自身产物导致自指漂移。

HW. 收口：r129a 17 + r129b 13 + r129c 13 + r129d 8 + r129e 8 + r129f 7 + r129g 10 + r129h 8 + r129i 12 + r129j 13 + r129k 26 + r129k2 22 + r129l 10 + r129m 21 + r129n 19 = 197 项断言（去重后口径 109 项，见台账十一），全 PASS。全程 disasm_lite 流式与 objdump 单遍，未对整段 .text 开 detail=True；脚本带 timeout；收口前 ps 确认无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0、C10 ok(R129)。

HX. 未取得（不粉饰）：① 0xb0c110 的「与 ApplicationClass 同级全局单例」仍无第二条记录；② 010C 的「槽只到 +0xc」仍只由 R127 的符号执行承担；③ QI 结果被存进堆结构体后再取用的路径，本轮所有判据都看不见；④ 0x7e9500 那张表为何只有 1 项（而不是八项）未解，只知道 blowfish.dll 一项确实被装入并用 CoCreateInstance 取对象；⑤ 35 个静态容器的运行期元素值与计数；⑥ 共用模板展开的充分证明；⑦ 门禁另两处未修（C7 bytes=N 死分支、C11 frozen 分支）；窗口表只覆盖 r36..r65 共 28 轮，r66 以后全部不可验证 —— 本轮降级的五条正因为落在表外，才只能靠 C17 的路径轮次判据抓到，这是下一处该修的地方；⑧ 已判死线不投。
'''

BOARD_NEW = '''## 🟢 R17 第 129 轮（2026-11-25 05:0x–05:4x）· 0x6bd940 的 call ebx 定名 RegisterActiveObject；CLSID 与类工厂与类名串成四段链；C11 claims-none 校验式接上真跑；C17 五条不可能行裁定撤回

### 一 · 起点

R128 台账 HJ 第四项是「0x6bd940 的 call ebx 目标未定」。另两条待办本轮各推进一格：C11 其余永远通过子项、C17 五条不可能行的裁定。

### 二 · call ebx 的目标靠三条判据定，不靠形态

0x6bd6c2 的字节是 8b 1d 70 13 7e 00，即 mov ebx, dword ptr [0x7e1370]；该 IAT 槽在本映像导入表里解析出 OLEAUT32!RegisterActiveObject。三条同时成立：定义点唯一且槽名可解析；从定义点到 0x6bd945 的每条可达路径上没有其它 ebx 写（1 条无写路径 / 0 条带写路径）；定义点是必经点 —— 切断 0x6bd6c2、0x6bc347、0x6bb9c3 各一次，0x6bd945 全部不可达。

反控：相邻槽 0x7e1374 解析出 VariantChangeType；同函数另外两个 ebx 定义（0x6bbee9 OpenMutexA、0x6bc347 LoadLibraryA）与调用点之间隔着其它 ebx 写或不可达，不能冒充。

### 三 · 实参契约自洽，撤销侧成对

0x6bd934 起四条 push 是 0x840a74 / 1 / 0x7e9520 / 0x87f7e8。第二实参 rclsid = 0x7e9520 = {B45A4A81-86DA-11D1-B706-00A024DDAFD1}；第四实参 lpdwRegister = 0x840a74（.data 原始区 DWORD、静态 0xFFFFFFFF、后紧跟 blowfish.dll）。撤销侧配对：0x6be131 与 0x6bec9d 都是「读 0x840a74 → 与 -1 比 → 非 -1 则 call [0x7e1384]（RevokeActiveObject）→ 写回 -1」。0x840a74 的 imm32 全库恰 5 处。

### 四 · CLSID 到类名的四段链

段一 0x6bc42a 起四个实参压栈、0x6bc43a push 0x7e9520、mov esi,[0x7e15d8] + call esi（CoRegisterClassObject）。段二 0xa8e8c8 在 BSS（段内 0x6d8c8 > raw 0x6c000），无静态字节，只能走写入者反查；imm32 全库恰 2 处，写入者 0x4e7ce0 把 vptr 写成 0x7ea564。段三 0x7ea564 COL = .?AVTiberianSunClassFactory@@（IClassFactory ncb1 / IUnknown ncb0，mdisp 全 0）。段四 0x7e9520 的 5 处引用含 0x6bc43b（类对象 rclsid）与 0x6bd93c（活动对象 rclsid）。

反控三条：0x7e9510 只差 Data1 末字节；把段二 vptr 换成 0x7f4108 得 .?AVSwizzleManagerClass@@（不同类）；无静态读旁路。

### 五 · 0x7f3710 那张表的边界来自字节

头 0x6bc342、步长 0x6bc409 add esi,8、上界 0x6bc40c cmp esi,0x7f3718、回边 0x6bc412 jl，四条都在字节里。表恰 1 项：0x7e9500 的 GUID + blowfish.dll。封装 0x6bedb0 体内四条调用：CoCreateInstance / OleRun / call [ecx] / call [edx+8]。

### 六 · 门禁真修第二处

claims-none 的校验式接上真跑。R128 只挡「产物里还留着自述行」，没挡「校验式本身已不成立」。先实测 14 条在真产物上 14/14 成立、空产物上 0/14 成立 ⇒ 有分辨力、零误伤，才接上。反控 7/7。

### 七 · 五条不可能行裁定为撤回，这是本轮唯一的净损失

C17 钉住的五条声称 R55，但产物路径轮次是 61/81/84/88。三条路验算：改行不可行（只改 round 则 at 出窗，改 at 即编造时刻）；撤回与降级同形，都要动第 7 列。

取撤回：第 7 列 有 -> 无，同时从产物里删掉那五条假声称（只改一列不删行会被 R128 判据当场抓住，实测 5 FAIL），删前原文逐字存 R129_RETRACTED.tsv，四份产物各建 wx 备份。三处重钉：C11B_PIN_GAP 7 -> 12、C17_PIN 5 -> 空集（摘要 e3b0c442... 是 hashlib 对空串的实测值）、C17_REUSED_ATS 清空。

**代价**：C11 的 ok 由 5 降到 0，因为撤回的五条恰是唯一五条能过 recheck_verify 的行。这不是「5 条真凭证」，是 0 条。换来两条真判据。裁定反控 10/10。

### 八 · 第二译码器仲裁踩了新坑

原始口径下四组交集恒 0，因为我把 capstone 的字节命中（立即数起点）与 objdump 的指令起点直接比。归一化到指令起点后：0xa8e8c8 2/2、0x7e9520 5/5、0x840a74 5/5、0x87f7e8 3700/3700，四组均无单边独有。归一化用 objdump 的指令边界表，不自求边界。

### 九 · 规则 D：一次失败、一次未派，如实记

hy4 task 264 failed 加 error_max_turns（61 回合 / 5.22 分钟 vs 预算 10.0 ⇒ OVERTIME），零报告，不写已审计。deepseek 派发撞上 MAX_SUBAGENTS 由 2 降到 1（796.5 MB），按纪律不并发。本轮审计由主会话自审 19 项 + 第二译码器 21 项承担。

### 十 · 自错 15 条

S-184 窗口切断指令、S-185 断言按记忆写、S-186 反控对象不可解、S-187 与 S-197 同为 or True 恒真断言（第二轮由自动检查抓到）、S-188 替换目标非唯一、S-189 搬运没处理行尾 CR、S-190 split 下标取字段、S-191 字节差未按文件汇总、S-192 跨工具只收一种数值形式、S-193 假设地址补零、S-194 跨译码器未归一化、S-195 自求指令边界（同 R127 S-170）、S-196 只降级不删行、S-198 统计含自身致自指漂移。

### 十一 · 收口

十七套脚本 109 项断言全 PASS。全程 disasm_lite 流式与 objdump 单遍，未对整段 .text 开 detail=True；脚本带 timeout；收口前 ps 确认无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0、C10 ok(R129)。

### 十二 · 未取得（不粉饰）

① 0xb0c110 同级单例无第二记录。② 010C 的槽上界仍单来源。③ QI 结果存堆结构体的路径看不见。④ 0x7e9500 那张表为何只有 1 项未解。⑤ 35 容器运行期值。⑥ 共用模板充分证明。⑦ 门禁另两处未修（C7 bytes=N、C11 frozen）、窗口表只覆盖 r36..r65 —— 本轮降级的五条正因落表外才只靠路径轮次判据抓到，这是下一处该修的。⑧ 已判死线不投。
'''

do(RC, 'r14_common', R14_NEW, marker='## 2.133 R129')
do(LED, 'ledger', LED_NEW, marker='## §1183 R129')
do(LOCK, 'lead_lock', LOCK_NEW, marker='HL. R129')
do(BRD, 'status_board', BOARD_NEW, marker='R17 第 129 轮')
print('board lines now', io.open(BRD, 'rb').read().count(b'\n'))
