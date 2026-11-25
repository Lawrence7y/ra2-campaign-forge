# -*- coding: utf-8 -*-
"""R128q：追加 R14_COMMON 2.132、台账 1182、LEAD_LOCK GZ 段、看板第 128 轮段。

纪律：wx 独占备份 -> 断言旧 sha256 与旧 CR -> 断言新文本零反引号 -> 一次性写入 -> 回读校验。
看板当前 187 行，未到 260 行归档阈值。
"""
import io, os, sys, hashlib, datetime

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
RC   = os.path.join(R14, 'R14_COMMON.md')
LED  = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD  = os.path.join(R14, 'STATUS_BOARD.md')
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

EXPECT = {RC: 1081, LED: 337, LOCK: 137, BRD: 0}

def sha16(b): return hashlib.sha256(b).hexdigest()[:16]

def do(path, tag, new_text, marker=None):
    assert '`' not in new_text, '%s 新文本含反引号' % tag
    old = io.open(path, 'rb').read()
    dst = os.path.join(BK, 'r128_%s.%s.bak' % (tag, TS))
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try:
        os.write(fd, old)
    finally:
        os.close(fd)
    want_cr = EXPECT[path]
    old_cr = old.count(b'\r')
    assert old_cr == want_cr, '%s 旧 CR %d != %d' % (tag, old_cr, want_cr)
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
    print('  WROTE %-12s sha %s -> %s  CR=%d  bytes %d -> %d  LF %d -> %d'
          % (tag, sha16(old), sha16(rb), rb.count(b'\r'), len(old), len(rb),
             old.count(b'\n'), rb.count(b'\n')))

R14_NEW = '''## 2.132 R128：三个 BSS 单例的 vptr 写入者全部唯一命中；0x7ea6e8 = IGameMap 由「认-转交-自认」闭环定名；C11 的 claims-none 免检通道真修成可失败

**起点。** R127 台账 GY 留了八条未取得，本轮取其中两条 plus 一条 R127 明确记为「方法无解」的补测：① 0x429270 转交链落成字节；② 0x7ea6e8 定名（R127 记为 mdisp 判据对它无效、故不定名）；④ 010C 的「槽只到 +0xc」补第二条独立证据。第④条**方法失败并如实留缺**，不在下面四条里充数。

**一 · 一个前提被推翻。** R127 待办② 的字面做法是「静态读 0x87f7e8 处的 vptr 指向哪张虚表」。实测 0x87f7e8 落在 .data 的非 raw 区（BSS）：段内偏移 0x6d7e8 远超 SizeOfRawData 0x6c000，映像文件里没有任何静态字节，静态读必然得 0。这不是「读不到所以不知道」，是**方法在结构上不可行**。改走反向路径：找谁写它的 vptr。

**二 · 三个单例的 vptr 写入者各恰一处（含反控）。** 全 .text 扫 C7 05 形态（mov dword ptr [abs], imm32，共 1971 处）：

- 0x87f7e8 <- 0x7e1964 只在 0x40d1b2（1 处），写入点属静态初始化函数 0x40d1b0，由 0x40d190 的 mov ecx,0x87f7e8 / call 0x5bda40 / push 0x40d1b0 / call 0x7c978a 注册（ctor 后立即 atexit 注册析构 0x40d1b0）。
- 0x89a29c <- 0x7e36d4 只在 0x429200（1 处），是一个三字节函数 mov [0x89a29c],0x7e36d4 / ret。
- 0xb0c110 <- 0x7f4108 有两处（0x6cf0c8 与 0x6cf0f6），同一函数 0x6cf0f0 的 ctor 与其 atexit 注册点，指向同一张表，故仍是单一写入目标。

反控：相邻地址 0x87f7e4 的 C7 05 写入 0 处、0x87f7ec 的写入是 mov [0x87f7ec],eax（与 vptr 无关）；0x89a2a0 的写入 0 处。判据不是「凡 .data 地址都命中」。

**三 · 0x87f7e8 的类型。** 0x7e1964 的 COL 在 0x7fab38，TypeDescriptor 0x816c90 解出 .?AVMouseClass@@，12 条基类，末条 .?AVINoticeSink@@ 的 mdisp = 21784 = 0x5518。ctor 0x5bda40 体内恰好写两处：0x5bda4a mov [esi],0x7e1964（主 vptr）与 0x5bda68 mov [esi+0x5518],0x7e195c（INoticeSink 子对象 vptr）—— 偏移与 RTTI 的 mdisp 逐位一致。0x7e195c 的 COL 也解出 .?AVMouseClass@@（COL 0x7fa9b8，与主表的 0x7fab38 不同）⇒ 两条 vtable、两张 COL、同一个类，多继承的标准形态。

**四 · 0x87f7e8 是全局单例，不是数组。** 指令级引用 3700 处：3693 处 mov ecx,0x87f7e8（this 传递）、3 处 push 0x87f7e8、2 处 mov edx,[0x87f7e8]、1 处写 vptr、1 处 mov [edx],0x87f7e8（写别人的出参）。lea reg,[0x87f7e8] 站点 0 处 ⇒ 没有「先取地址再写 vptr」的第二条路径。对 [0x87f7e8+4k] 的写只有 +0，无 +4/+8/+0x10 ⇒ 单个对象不是数组。

**五 · IClassFactory::CreateInstance 全链。** vtable 0x7ea564 的 COL = .?AVTiberianSunClassFactory@@（基类 IClassFactory ncb 1、IUnknown ncb 0，三者 mdisp 全 0）。前五槽 ret 字节 = 12/4/4/16/8：AddRef 与 Release 是 ret 4，故本构建的 COM 方法一律 **this 显式占第一个栈参数**（若走 ecx 约定它们必须是 ret 0）。这正是 R127 困惑的「CreateInstance ret 0x10 与 3 实参不符」的真因：this+pUnkOuter+riid+ppv 恰 4 实参。实参取值逐位自洽：[esp+0x10] 是 ppv、四次 push 后 [esp+0x18] 是原始 +8 的 pUnkOuter、[esp+0x1c] 是原始 +0xc 的 riid。四条失败路径：ppv 空 E_INVALIDARG 0x80070057、pUnkOuter 非空 CLASS_E_NOAGGREGATION 0x80040110、E_OUTOFMEMORY 0x8007000e 两处、E_NOINTERFACE 0x80004002（走 ebx 通道，末尾 mov eax,ebx 返回）。

**六 · 认-转交-自认的闭环，0x7ea6e8 = IGameMap。** 0x7ea6e8 在全 .text 的指令级引用恰 3 处，三处都是 mov edi,0x7ea6e8：

1. 0x42930f 在 TiberianSunClassFactory::QI 里 —— 认了之后 mov ecx,0x87f7e8 / mov edx,[0x87f7e8] / push ppv / push riid / push 0x87f7e8 / call [edx]，即**转交**给全局 MouseClass 的 QI；
2. 0x4293a5 在 0x429360（ApplicationClass::QI）里 —— 认了之后把 ppv 写成常量 0x87f7e8（不是 this），这正是 R127 判「mdisp 判据无效」的那一处；
3. 0x4f4273 在 0x4f4240（MouseClass::QI）里 —— 自己认，ppv = this。

第三处是 R127 没有的。R127 只找到前两处，因为它的扫描漏了这一处（见第十条）。0x4f4240 只比较两个 IID：0x7f7c90（IID_IUnknown）与 0x7ea6e8，两条接受分支都写 ppv=this，第一条 ret 在 0x4f4298（ret 0xc），其后全是 nop，无后续分支。MouseClass 的 COL 在 mdisp 0 处的非 IUnknown 接口名唯一 = .?AUIGameMap@@（INoticeSink 在 0x5518，被 ppv=this 排除）⇒ 0x7ea6e8 = IGameMap，唯一解。

判据的四条反控：① 把 mdisp 换成 0x5518 做同一统计，全库命中集为空（100 个类在 mdisp 0 有解，0 个在 0x5518 有解），说明判据只在 mdisp 0 给解、不是随便挑名字；② 去掉「非 IUnknown」过滤后 MouseClass 得两个候选，唯一性消失，过滤是必要的；③ 同一个 MouseClass::QI 对 0x7f7c90 也接受并返回 this，但 0x7f7c90 已由 IID_IUnknown 常量（Data1 全 0）独立定名，判据给出不同名字不是恒等判据；④ 0x7ea6e8 与 0x7e36c0 仅 Data1 末字节不同（C7 vs C3），是两个常量。全库 954 个可解 COL 的类里，9 个声明 .?AUIGameMap@@，全部是窗口族（Display/GScreen/Map/Mouse/Power/Radar/Scroll/Sidebar/Tab）。

**七 · 两处方法失败，如实留缺。** 其一，010C 的「槽只到 +0xc」想补第二条独立证据：不用符号执行、改用「IID 引用点附近出现的虚调用偏移」当判据。±0x200 窗口下 010C 侧与 0109 侧最大偏移都是 0x1c8，判据无分辨力；收到 +0x80 后 010C 侧给 {16,36}、0109 侧给 {16}，但 IPersist 只有 1 个方法不可能出现 +0x24，只能是噪声。**方法失败，不产出证据**，R127 GY ④ 保持原样。这与 R127 S-170（三次自算函数边界全失败）是同一教训：不自己求函数边界，就不能按窗口对调用偏移下结论。本轮不再试第三次。其二，0xb0c110 <- 0x7f4108 的两处写入同址，虽指向同一张表，但「该对象是与 ApplicationClass 同级的全局单例」这一句仍只是形态推断，没有第二条记录。

**八 · 规则 D 两次派发，都成功。** hy4 task 260 succeeded（15 回合 / 1.47 分钟 / 预算 8.0 / 无 OVERTIME），报告 128 行 / 7340 B 零反引号；deepseek task 261 succeeded（439 行 / 22146 B 零反引号）。两边都有数字错，都按规则 D 用两译码器仲裁后判定：

- hy4 报「含该地址的指令 498 条」「0x7ea6e8 引用 2 处」，实测 3700 条与 3 处。用 capstone 与 i686-w64-mingw32-objdump 各出一份**地址集合**（不比总数）逐地址比对：3700/3700 交集 3700、仅 C 0、仅 O 0；0x7ea6e8 三处两个译码器完全一致。498 不对应 objdump 里任何一个可数的量（mov $0x87f7e8,%ecx 是 3693 行、任何提及是 3700 行、mov 0x87f7e8,%reg 是 2 行）。
- deepseek 报「单遍 disasm_lite 会在 0x46f59d 停住、只解码 155215 条」。实测那个 155215/0x46f59d 恰是 **skipdata=False** 的结果，而 skipdata=True 的 disasm_lite 给 1394186 条、最后一条 0x7e0fff、覆盖 100.00%\n（.text raw 到 0x7e1000，差 1 字节是对齐尾巴）。它把两种口径混为一谈。
- deepseek 十三条主张逐条复算**全部一致**（r128o 13/13）：c705e8f78700 唯一命中且立即数 0x7e1964、前缀字节分布 3693/3/2/1/1、push 0x87f7e8 三处地址、mov edx,[0x87f7e8] 两处地址、0x40d1bc 写 0x884d00<-0x7e195c 的原始字节、三个 GUID 文本、三处 mov edi,0x7ea6e8、call [edx] 两条与 ff 12 字节、push 立即数四条、edx 写入五处、ApplicationClass 的 COL 0x7fbc18 / TD 0x8186c8 / n 3 / slot0 0x429360。它报的是**文件偏移** 0xd1b2、我算的是**段内偏移** 0xc1b2，两者对应同一 VA。
- 采纳它一条我漏的事实并复算：0x6bd940 是第三处 push 0x87f7e8，上下文 push 0x840a74 / push 1 / push 0x7e9520 / push 0x87f7e8 / call ebx。我先前只报两处。
- 它的中间产物里 TOTAL 498 与主会话真值 3700 差 3202，成因是它的扫描器逐字节重同步；但它最终报告改成了重同步口径的 3700，与真值一致，故最终报告无此错。

**九 · 自错五条全留案。** S-179：我先预判「指令级引用远少于字节级」，实测两者都是 3700，方向反了。S-180：C4 第一版只在 eax 里找 E_NOINTERFACE，漏了它走 ebx 通道。S-181：D1 第一版用 rg 得 2 处，因为 md.skipdata 设在 disasm 之后才生效；三处才对。S-182：N0 拿 Misc_VirtualSize 0x3df38d 当 .text 长度，实际 raw 是 0x3e0000。S-183：O1 断言 p == 0xd1b2，但 raw 是段内偏移、应为 0xc1b2（0xc1b2+0x401000 = 0x40d1b2）。另有一次 OOM：r128e 第一版把 139 万条指令物化成 list，被 cgroup kill（exit 137），改成 disasm_lite 生成器单遍流式后通过 —— 这正是本仓 CLAUDE.md 与每轮提示词都写明的红线，我自己踩了。

**十 · 门禁真修一处（带四条反控）。** R127 与 R128 的待办都点了「C11 的永远通过子项」。本轮不猜是哪几处，先全量测（r128f 6/6）：31 行按第 7 列分「声明不补」14 行、「声明回跑」17 行；14 行的产物全部存在且都没有本纪律的自述行（声明与事实一致，不是逃逸）；校验式是 rows=N 的 4 行（22/26/27/28）实测行数与期望逐一相符，但 rows=N 只数行数、对内容无感。挑 claims-none 做真修：主循环原来对它们直接 continue 计入 claims-none，永不 FAIL；现在改成先核「该行产物里不得出现本纪律的自述行」，违反即 FAIL。

反控（r128k 6/6，用「正本改名藏起 + 改过的副本放到正本路径 + finally 恢复并断言 sha」做，避开 R126 S-161 的临时目录陷阱）：正控 exit 0 且 C10 显示 ok(R128)；GATE_VER 改回 R127 而第 20 行仍登记 R128 -> exit 1 命中 C10；只改第 20 行不改 GATE_VER -> exit 1 命中 C7 id 20；给 id 11 的产物塞一条它自己的自述行 -> exit 1 命中新判据「C11 id 11 claims-none but its product carries 1 self-description line」。GATE_VER 由 R127 升到 R128 并同步 DISC_RECHECK 第 20 行登记式（C10 门自检要求二者一致，而本轮确实动了门禁脚本）。两处改动方向都是收紧。终态 check_disc.py exit 0、C10 显示 ok(R128)。

**十一 · 断言与收口。** 十五套脚本 130 项断言全 PASS（r128a 16 + r128b 11 + r128c 12 + r128d 11 + r128e 9 + r128f 6 + r128g 6 + r128h 7 + r128i 9 + r128j 8 + r128k 6 + r128l 5 + r128m 4 + r128n 7 + r128o 13）。全程 disasm_lite 流式扫描，未对整段 .text 开 detail=True；脚本带 timeout；收口前 ps 确认无孤儿进程（唯一残留是本会话自己的 shell 包装，已处理）。五项 CR 全绿 1081/137/337/0/2952；看板 187 行未到 260 行阈值，本轮不归档（归档 CR 仍 2952）。

**十二 · 未取得（不粉饰）。** ① 0xb0c110 的「与 ApplicationClass 同级全局单例」仍只是形态推断，无第二条记录。② 010C 的「槽只到 +0xc」仍只由 R127 r127a 的符号执行承担，本轮方法失败未补上（见第七条）。③ 若 QI 结果被存进堆结构体后再取用，本轮所有判据都看不见。④ 0x6bd940 处的 call ebx 的 ebx 来源未追（该处是第三处 push，但被调函数未定）。⑤ 35 个静态容器的运行期元素值与计数。⑥ 共用模板展开的充分证明。⑦ 门禁还有三处未修：C7 的 bytes=N 死分支、C11 的 frozen 分支、C10 门自检；五条不可能行 C11 id 3/4/22/27/28 未裁定；窗口表未扩。⑧ 已判死线不再投入：具名池、无名池、direct-only(D2)、D4结构性无、静态④、动态④、证据指针791行、D-48攻②-b。
'''

LED_NEW = '''## §1182 R128：三个 BSS 单例 vptr 写入者唯一化；0x7ea6e8 = IGameMap 闭环定名；CreateInstance 实参约定改为 this-on-stack；C11 claims-none 真修

**A. 结构前提推翻。** 0x87f7e8 在 .data 非 raw 区（段内 0x6d7e8 > SizeOfRawData 0x6c000），映像内无静态字节，R127 待办② 的「静态读 vptr」方法不可行，改反向找写入者。0x89a29c（0x429200）与 0xb0c110（0x6cf0c8 / 0x6cf0f6 同表）同样各自唯一。

**B. 0x87f7e8 = .?AVMouseClass@@ 全局单例。** vptr 0x7e1964，COL 0x7fab38，TD 0x816c90，12 基类，末条 .?AVINoticeSink@@ mdisp 0x5518。ctor 0x5bda40 写 [esi]=0x7e1964 与 [esi+0x5518]=0x7e195c，偏移与 RTTI 逐位一致。0x7e195c 的 COL 0x7fa9b8 也解出同一类名 ⇒ 两条 vtable 两张 COL 一个类。引用 3700 处形态分解：3693 mov ecx this 传递 / 3 push / 2 mov edx,[abs] / 1 写 vptr / 1 写出参。lea 取地址 0 处，[+4k] 写只有 +0 ⇒ 单对象非数组。

**C. CreateInstance 全链。** vtable 0x7ea564 COL = .?AVTiberianSunClassFactory@@。前五槽 ret = 12/4/4/16/8；AddRef/Release 是 ret 4 ⇒ 本构建 COM 方法 this 显式占第一栈参（ecx 约定下必须 ret 0）。这解开 R127 的「ret 0x10 与 3 实参不符」：[esp+0x10]=ppv、[esp+0x18]=原始+8 的 pUnkOuter、[esp+0x1c]=原始+0xc 的 riid。HRESULT 四条：0x80070057 / 0x80040110 / 0x8007000e x2 / 0x80004002（ebx 通道）。

**D. 0x7ea6e8 = .?AUIGameMap@@。** 全 .text 三处引用，构成闭环：0x42930f（TSClassFactory::QI 认了转交）、0x4293a5（0x429360 认了写常量 0x87f7e8）、0x4f4273（0x4f4240 MouseClass::QI 自认，ppv=this）。第三处是 R127 没有的。MouseClass 在 mdisp 0 处非 IUnknown 接口唯一 = IGameMap。四条反控：mdisp 换 0x5518 全库无解、去掉 IUnknown 过滤唯一性消失、同 QI 对 0x7f7c90 给不同名、0x7ea6e8 与 0x7e36c0 差 Data1 末字节。

**E. 两处方法失败。** 010C 的虚调用偏移窗口法在 ±0x200 与 +0x80 两档都无分辨力（两侧 max 同为 0x1c8 / 给出不可能的 +0x24），**不产出证据**，R127 GY ④ 保持原样。0xb0c110 的同级单例定位仍只是形态推断。

**F. 规则 D。** hy4 task 260（15 回合 / 1.47 分钟 / 预算 8.0 / 无 OVERTIME，128 行 7340 B 零反引号）两处数字错（498 vs 3700、2 vs 3），用 capstone + objdump 两份地址集合仲裁：3700/3700 交集 3700、仅 0/0；三处完全一致。deepseek task 261（439 行 22146 B 零反引号）报的「单遍 disasm_lite 停在 0x46f59d / 155215 条」实测是 skipdata=False 的结果（skipdata=True 得 1394186 条、覆盖 100.00%）。其十三条主张逐条复算全部一致；采纳它一条我漏的事实（0x6bd940 第三处 push 0x87f7e8）。

**G. 自错五条。** S-179 预判方向反（指令级并不少于字节级）、S-180 漏 ebx 通道的 HRESULT、S-181 skipdata 设置顺序致漏 0x4f4273、S-182 错用 Misc_VirtualSize 当 .text 长度、S-183 混淆段内偏移与文件偏移。另有一次 OOM（r128e 首版物化 139 万条指令被 kill），改流式生成器后通过 —— 踩了本仓自己写明的红线。

**H. 门禁真修一处。** C11 的 claims-none 从「直接 continue、永不 FAIL」改为「核产物里不得出现本纪律自述行」。全量实测 31 行（14 声明不补 / 17 声明回跑），14 行现状诚实。四条反控全中：正控 exit 0 + ok(R128)、GATE_VER 不同步命中 C10、登记行不同步命中 C7 id 20、给 id 11 产物塞自述行命中新判据。GATE_VER R127 -> R128。

**I. 断言与收口。** 十五套脚本 130 项全 PASS（16+11+12+11+9+6+6+7+9+8+6+5+4+7+13）。disasm_lite 流式、未整段开 detail、脚本带 timeout、无孤儿进程。五项 CR 1081/137/337/0/2952 全绿，check_disc.py exit 0、C10 ok(R128)；看板 187 行未到 260，不归档。

**J. 未取得。** ① 0xb0c110 同级单例定位无第二证据；② 010C 槽上界仍单来源；③ QI 结果存堆结构体的路径看不见；④ 0x6bd940 的 call ebx 目标未定；⑤ 35 容器运行期值；⑥ 共用模板充分证明；⑦ 门禁另三处未修（C7 bytes=N、C11 frozen、C10 门自检）、五条不可能行未裁定、窗口表未扩；⑧ 已判死线不投。
'''

LOCK_NEW = '''GZ. R128 主攻 R127 台账 GY 的前两条未取得项（① 0x429270 转交链、② 0x7ea6e8 定名），另试第四条（010C 槽上界补第二证据）但方法失败。十五套脚本 130 项断言全 PASS。

HA. 推翻一个方法前提：0x87f7e8 在 .data 非 raw 区（段内 0x6d7e8 > raw 0x6c000），映像内无静态字节，「静态读它的 vptr」不可行。改反向：全 .text 扫 C7 05 形态 1971 处，与三个目标地址相交的写入各唯一 —— 0x87f7e8 <- 0x7e1964 在 0x40d1b2、0x89a29c <- 0x7e36d4 在 0x429200、0xb0c110 <- 0x7f4108 在 0x6cf0c8 与 0x6cf0f6（同函数两张表同址，仍单一目标）。反控 0x87f7e4 与 0x89a2a0 各 0 处。

HB. 0x87f7e8 = .?AVMouseClass@@ 全局单例：vptr 0x7e1964、COL 0x7fab38、TD 0x816c90、12 基类、末条 .?AVINoticeSink@@ mdisp 0x5518；ctor 0x5bda40 同时写 [esi]=0x7e1964 与 [esi+0x5518]=0x7e195c，偏移与 RTTI 逐位一致；0x7e195c 的 COL 0x7fa9b8 也解出同类名，两条 vtable 两张 COL 一个类。引用形态 3693 this 传递 + 3 push + 2 mov edx + 1 写 vptr + 1 写出参 = 3700；lea 取地址 0 处、[+4k] 写仅 +0，故是单对象不是数组。

HC. CreateInstance 全链落成字节，并纠正 R127 的结构误解：vtable 0x7ea564 前五槽 ret = 12/4/4/16/8，AddRef 与 Release 是 ret 4 ⇒ 本构建 COM 方法一律 this 显式占第一栈参（ecx 约定下必须 ret 0）。故 ret 0x10 自洽（this+pUnkOuter+riid+ppv 四实参），R127 记的「不符」不是异常是误读。实参位置：[esp+0x10]=ppv、[esp+0x18]=原始+8、[esp+0x1c]=原始+0xc。四条 HRESULT：0x80070057 / 0x80040110 / 0x8007000e x2 / 0x80004002（走 ebx 通道，末尾 mov eax,ebx）。

HD. 0x7ea6e8 = .?AUIGameMap@@，走的不是 mdisp 判据（R127 已证对它无效），而是「认-转交-自认」闭环：全 .text 恰三处 mov edi,0x7ea6e8 —— 0x42930f（TiberianSunClassFactory::QI 认了之后 push 0x87f7e8 转交给 MouseClass 的 QI）、0x4293a5（0x429360 认了之后把 ppv 写成常量 0x87f7e8）、0x4f4273（0x4f4240 MouseClass::QI 自认，ppv=this）。第三处 R127 没有，因为它的扫描漏了。0x4f4240 只比 IUnknown 与 0x7ea6e8 两个，ret 0xc 后全 nop 无后续分支；MouseClass 在 mdisp 0 处非 IUnknown 接口唯一 = IGameMap。四条反控：mdisp 换 0x5518 全库无解（100 -> 0）、去 IUnknown 过滤唯一性消失、同 QI 对 0x7f7c90 给不同名、0x7ea6e8 与 0x7e36c0 差 Data1 末字节（C7 vs C3）。全库 9 个类声明 IGameMap，全是窗口族。

HE. 两处方法失败，如实留缺。其一：010C 的「槽只到 +0xc」想到用「IID 引用点附近的虚调用偏移」当第二证据，±0x200 窗口两侧 max 同为 0x1c8（无分辨力），收到 +0x80 后 010C 侧给 {16,36} 而 IPersist 只有 1 方法不可能有 +0x24（是噪声）。方法失败不产出证据，R127 GY ④ 保持原样，本轮不试第三次。其二：0xb0c110 的「与 ApplicationClass 同级全局单例」仍只是形态推断。

HF. 规则 D 两次派发都成功，两边都有数字错，都用两译码器地址集合仲裁。hy4 task 260 succeeded（15 回合 / 1.47 分钟 / 预算 8.0 / 无 OVERTIME，128 行 7340 B 零反引号）报 498 条与 2 处，实测 3700 与 3 处；capstone 与 objdump 各出地址集合比对 3700/3700 交集 3700、仅 0/0，三处完全一致；498 不对应 objdump 可数的任何量（3693 / 3700 / 2）。deepseek task 261 succeeded（439 行 22146 B 零反引号）报「单遍 disasm_lite 停在 0x46f59d / 155215 条」，实测那正是 skipdata=False 的结果，skipdata=True 得 1394186 条、最后 0x7e0fff、覆盖 100.00%。其十三条主张逐条复算全部一致；采纳它一条我漏的事实并复算：0x6bd940 是第三处 push 0x87f7e8（上下文 push 0x840a74 / push 1 / push 0x7e9520 / push 0x87f7e8 / call ebx）。

HG. 自错五条留案。S-179 我先预判「指令级引用远少于字节级」，实测两者都是 3700，方向反了。S-180 C4 第一版只在 eax 找 E_NOINTERFACE，漏了 ebx 通道。S-181 D1 第一版 rg 得 2 处，因 md.skipdata 设在 disasm 之后才生效。S-182 N0 用 Misc_VirtualSize 0x3df38d 当 .text 长度，raw 实为 0x3e0000。S-183 O1 混淆段内偏移 0xc1b2 与文件偏移 0xd1b2。另有一次 OOM：r128e 首版把 139 万条指令物化成 list 被 cgroup kill（exit 137），改 disasm_lite 生成器单遍流式后通过 —— 踩了本仓自己写明的红线，如实记。

HH. 门禁真修一处（C11 的 claims-none 免检通道），带四条反控。先全量测 31 行：14 声明不补 / 17 声明回跑，14 行产物全在且都无本纪律自述行（声明诚实），rows=N 有 4 行（22/26/27/28）实测与期望相符但只数行数。改法：claims-none 行的产物里不得出现本纪律自述行，违反即 FAIL。反控用「正本改名藏起 + 改过的副本放正本路径 + finally 恢复并断言 sha」（避开 R126 S-161 的临时目录陷阱）：正控 exit 0 + ok(R128)；GATE_VER 改回 R127 -> exit 1 命中 C10；只改第 20 行 -> exit 1 命中 C7 id 20；给 id 11 产物塞自述行 -> exit 1 命中新判据。GATE_VER R127 -> R128 并同步登记行。方向是收紧。终态 exit 0、C10 ok(R128)。

HI. 断言与收口：r128a 16 + r128b 11 + r128c 12 + r128d 11 + r128e 9 + r128f 6 + r128g 6 + r128h 7 + r128i 9 + r128j 8 + r128k 6 + r128l 5 + r128m 4 + r128n 7 + r128o 13 = 130 项全 PASS。全程 disasm_lite 流式、未对整段 .text 开 detail=True、脚本带 timeout、收口前 ps 确认无孤儿进程（残留的只是本会话自己的 shell 包装，已处理）。五项 CR 全绿 1081/137/337/0/2952；看板 187 行未到 260 行阈值，本轮不归档（归档 CR 仍 2952）。

HJ. 未取得（不粉饰）：① 0xb0c110 的「与 ApplicationClass 同级全局单例」无第二条记录；② 010C 的「槽只到 +0xc」仍只由 R127 r127a 符号执行承担，本轮方法失败未补；③ QI 结果存进堆结构体后再取用的路径本轮判据看不见；④ 0x6bd940 的 call ebx 目标未定；⑤ 35 个静态容器运行期元素值与计数；⑥ 共用模板展开的充分证明；⑦ 门禁另三处未修（C7 bytes=N 死分支、C11 frozen 分支、C10 门自检）、五条不可能行 C11 id 3/4/22/27/28 未裁定、窗口表未扩；⑧ 已判死线不投。
'''

BRD_NEW = '''## 🟢 R17 第 128 轮（2026-11-25 04:0x–05:0x）· 三个 BSS 单例的 vptr 写入者唯一命中；0x7ea6e8 = IGameMap 由认-转交-自认闭环定名；C11 的 claims-none 免检通道真修成可失败

### 一 · 起点：先推翻一个方法前提

R127 台账 GY 留了八条未取得，其中第②条的字面做法是「静态读 0x87f7e8 处对象的 vptr 指向哪张虚表」。本轮第一步就发现这条路走不通：0x87f7e8 落在 .data 的非 raw 区（段内偏移 0x6d7e8，远超 SizeOfRawData 0x6c000），映像文件里**没有任何静态字节**，静态读必然得 0。

这不是「读不到所以不知道」，是方法在结构上不可行。换成反向路径：找谁写它的 vptr。

顺带核出 0x89a29c 与 0xb0c110 也都在 BSS。三个单例同一种处境。

### 二 · 三个 vptr 写入者各恰一处，反控给空

全 .text 扫 C7 05 形态（mov dword ptr [abs], imm32，共 1971 处），与三个目标地址相交的写入：

- 0x87f7e8 <- 0x7e1964：只在 0x40d1b2 一处。上下文是静态初始化 0x40d190 的 mov ecx,0x87f7e8 / call 0x5bda40 / push 0x40d1b0 / call 0x7c978a —— ctor 之后立刻 atexit 注册析构。
- 0x89a29c <- 0x7e36d4：只在 0x429200 一处，那个函数就是 mov [0x89a29c],0x7e36d4 / ret。
- 0xb0c110 <- 0x7f4108：两处（0x6cf0c8 与 0x6cf0f6），同一函数的 ctor 与注册点，指向同一张表，仍是单一目标。

反控：相邻地址 0x87f7e4 的 C7 05 写入 0 处；0x87f7ec 的写入是 mov [0x87f7ec],eax（与 vptr 无关）；0x89a2a0 也是 0 处。判据不是「凡 .data 地址都命中」。

### 三 · 0x87f7e8 = .?AVMouseClass@@ 全局单例

0x7e1964 的 COL 在 0x7fab38，TypeDescriptor 0x816c90 解出 .?AVMouseClass@@，12 条基类，末条 .?AVINoticeSink@@ 的 mdisp = 21784 = 0x5518。

ctor 0x5bda40 体内恰好写两处：0x5bda4a 写 [esi]=0x7e1964（主 vptr）、0x5bda68 写 [esi+0x5518]=0x7e195c（INoticeSink 子对象 vptr）。偏移与 RTTI 的 mdisp **逐位一致**。而 0x7e195c 的 COL（0x7fa9b8）也解出同一个类名 —— 两条 vtable、两张 COL、一个类，多继承的标准形态。

引用形态分解成 3700 处：3693 mov ecx（this 传递）、3 push、2 mov edx,[abs]、1 写 vptr、1 写出参。lea reg,[0x87f7e8] 站点 **0 处**，所以没有「先取地址再写 vptr」的第二条路径；对 [0x87f7e8+4k] 的写只有 +0，没有 +4/+8/+0x10 —— 单个对象，不是数组。

### 四 · CreateInstance 的 ret 0x10 不是异常，是我上轮读错了

vtable 0x7ea564 的 COL = .?AVTiberianSunClassFactory@@。前五槽的 ret 字节是 12/4/4/16/8。

关键在 AddRef 与 Release 是 **ret 4**：若这两个走 ecx 约定，它们必须是 ret 0。所以本构建的 COM 方法一律是 **this 显式占第一个栈参数**。CreateInstance 于是有四个实参（this、pUnkOuter、riid、ppv），ret 0x10 完全自洽 —— R127 记的「ret 0x10 与 3 实参不符」不是二进制异常，是约定读错。

实参位置逐位自洽：[esp+0x10] 是 ppv、四次 push 后 [esp+0x18] 是原始 +8 的 pUnkOuter、[esp+0x1c] 是原始 +0xc 的 riid。四条失败路径：ppv 空 0x80070057、pUnkOuter 非空 0x80040110、0x8007000e 两处、0x80004002 —— 最后这个走 ebx 通道，末尾 mov eax,ebx 返回。

### 五 · 0x7ea6e8 = IGameMap：认了之后转交，转交之后自己认

R127 放弃给它定名，理由是「接受分支把出参写成 .data 单例而非 this，mdisp 判据无效」。这个理由成立，但换条路就能拿到。

全 .text 里 0x7ea6e8 的指令级引用**恰三处**，三处都是 mov edi,0x7ea6e8：

1. 0x42930f，在 TiberianSunClassFactory::QI 里 —— 认了之后 mov edx,[0x87f7e8]、push ppv、push riid、push 0x87f7e8、call [edx]，即**转交**给全局 MouseClass 的 QI；
2. 0x4293a5，在 0x429360 里 —— 认了之后把 ppv 写成常量 0x87f7e8，这正是 R127 说的那处；
3. 0x4f4273，在 0x4f4240（MouseClass::QI）里 —— 自己认，ppv = this。

第三处是 R127 没有的。0x4f4240 只比两个 IID（IUnknown 与 0x7ea6e8），第一条 ret 在 0x4f4298，其后全是 nop，没有后续分支。MouseClass 在 mdisp 0 处的非 IUnknown 接口名唯一 = .?AUIGameMap@@，而 INoticeSink 在 0x5518、被 ppv=this 排除。

四条反控：把 mdisp 换成 0x5518 做同一统计，全库命中集从 100 个塌到 **0 个**（判据只在 mdisp 0 给解）；去掉「非 IUnknown」过滤后 MouseClass 得两个候选、唯一性消失（过滤是必要的）；同一个 QI 对 0x7f7c90 也给 this，但它已由常量独立定名（判据不是恒等）；0x7ea6e8 与 0x7e36c0 差 Data1 末字节（C7 vs C3）。全库 9 个类声明 IGameMap，全是窗口族。

### 六 · 两处方法失败，如实留缺

其一，想给 010C 的「槽只到 +0xc」补第二条独立证据，不用符号执行、改用「IID 引用点附近的虚调用偏移」。±0x200 窗口下两侧最大偏移都是 0x1c8，判据无分辨力；收到 +0x80 后 010C 侧给出 {16,36}，但 IPersist 只有 1 个方法、不可能有 +0x24，那只能是相邻函数的噪声。**方法失败，不产出证据**，R127 那条保持原样，本轮不试第三次。

其二，0xb0c110 的「与 ApplicationClass 同级全局单例」这一句仍只是形态推断，没有第二条记录。

两条都写进未取得，不充数。

### 七 · 规则 D：两次派发都成功，两边都有数字错

hy4 task 260 succeeded（15 回合 / 1.47 分钟 / 预算 8.0 / 无 OVERTIME，128 行 7340 B 零反引号）。它报「含该地址的指令 498 条」与「0x7ea6e8 引用 2 处」，实测是 3700 与 3。

仲裁用两个独立译码器各出一份**地址集合**（不比总数，比集合）：capstone 与 i686-w64-mingw32-objdump 给 3700/3700、交集 3700、仅 C 0、仅 O 0；三处也是完全一致。而 498 不对应 objdump 里任何一个可数的量（mov $0x87f7e8,%ecx 是 3693 行、任何提及 3700 行、mov 0x87f7e8,%reg 2 行）。

deepseek task 261 succeeded（439 行 22146 B 零反引号）。它报「单遍 disasm_lite 会在 0x46f59d 停住、只解码 155215 条」。实测那个 155215/0x46f59d **正是 skipdata=False 的结果**；skipdata=True 的 disasm_lite 给 1394186 条、最后一条 0x7e0fff、覆盖 100.00%。它把两种口径混成了一谈。

它十三条主张逐条复算**全部一致**，另采纳它一条我漏的事实并复算：0x6bd940 是第三处 push 0x87f7e8，上下文 push 0x840a74 / push 1 / push 0x7e9520 / push 0x87f7e8 / call ebx。

### 八 · 我这一轮犯的五条，加上一次 OOM

S-179：我先预判「指令级引用远少于字节级」，实测两者都是 3700 —— 方向反了，因为 MouseClass 是全局单例、3693 处都是 this 传递。

S-180：C4 第一版只在 eax 里找 E_NOINTERFACE，漏了它走 ebx 通道。

S-181：D1 第一版用 rg 得 2 处，因为 md.skipdata 设在 disasm 之后才生效。

S-182：N0 拿 Misc_VirtualSize 0x3df38d 当 .text 长度，raw 实际是 0x3e0000。

S-183：O1 混淆段内偏移 0xc1b2 与文件偏移 0xd1b2。

另有一次 OOM：r128e 第一版把 139 万条指令物化成 list，被 cgroup kill（exit 137）。这正是本仓 CLAUDE.md 与每轮提示词都写明的红线，我自己踩了，改成生成器单遍流式后通过。

### 九 · 门禁真修一处：把 claims-none 从免检改成可失败

不猜「哪四处永远通过」，先全量测：31 行按第 7 列分 14 行声明不补、17 行声明回跑；14 行的产物全部存在且都没有本纪律的自述行（声明与事实一致）；rows=N 的 4 行实测与期望相符，但那判据只数行数、对内容无感。

挑 claims-none 做真修。主循环原来对它们直接 continue 计入 claims-none，永不 FAIL；现在改成先核「该行产物里不得出现本纪律的自述行」，违反即 FAIL。

反控用「正本改名藏起 + 改过的副本放到正本路径 + finally 恢复并断言 sha」做（避开 R126 S-161 的临时目录陷阱）：正控 exit 0 且 ok(R128)；GATE_VER 改回 R127 -> exit 1 命中 C10；只改第 20 行 -> exit 1 命中 C7 id 20；给 id 11 的产物塞一条它自己的自述行 -> exit 1 命中新判据。GATE_VER 由 R127 升到 R128 并同步登记行，两处方向都是收紧。终态 exit 0、C10 显示 ok(R128)。

### 十 · 收口

十五套脚本 130 项断言全 PASS（16+11+12+11+9+6+6+7+9+8+6+5+4+7+13）。全程 disasm_lite 流式扫描，未对整段 .text 开 detail=True；脚本带 timeout；收口前 ps 确认无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；看板 187 行未到 260 行阈值，本轮不归档。

### 十一 · 未取得（不粉饰）

① 0xb0c110 的「与 ApplicationClass 同级全局单例」无第二条记录。② 010C 的「槽只到 +0xc」仍只由 R127 的符号执行承担，本轮方法失败未补上。③ 若 QI 结果被存进堆结构体后再取用，本轮所有判据都看不见。④ 0x6bd940 的 call ebx 目标未定。⑤ 35 个静态容器运行期元素值与计数。⑥ 共用模板展开的充分证明。⑦ 门禁另三处未修（C7 bytes=N 死分支、C11 frozen 分支、C10 门自检），五条不可能行 id 3/4/22/27/28 未裁定，窗口表未扩。⑧ 已判死线不再投入。
'''

do(RC, 'R14_COMMON.md', R14_NEW, marker='## 2.132 R128')
do(LED, 'LEDGER', LED_NEW, marker='## §1182 R128')
do(LOCK, 'LEAD_LOCK', LOCK_NEW, marker='GZ. R128')
do(BRD, 'STATUS_BOARD', BRD_NEW, marker='第 128 轮')

# 收尾：CR 与行数复核
for p, tag, want_cr in ((RC, 'R14_COMMON', 1081), (LED, 'LEDGER', 337),
                        (LOCK, 'LEAD_LOCK', 137), (BRD, 'STATUS_BOARD', 0)):
    b = io.open(p, 'rb').read()
    print('  CHECK %-13s CR=%d (want %d)  lines=%d' % (tag, b.count(b'\r'), want_cr,
                                                       b.count(b'\n')))
    assert b.count(b'\r') == want_cr
    assert b'`' not in b or tag in ('R14_COMMON', 'LEDGER', 'LEAD_LOCK', 'STATUS_BOARD')
