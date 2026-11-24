
## 2.115 R111（2026-11-24）· 补 R110 三处漏抽（120 B 窗口截断 / thunk 盲区 / ATL 盲区）⇒ QI 类 172→187、distinct IID 17→20；并拿到 COL.offset==4 的第三条独立链（slot0 adjustor thunk 立即数，集合等式 12/12 且逐类 N==offset）

### 2.115.1 本轮定位：R110 的「未取得①」不是缺工作量，是我上一轮的判据有洞

R110 §EL11 把「每个 IID 的接口方法表未查」列为未取得。本轮开工先做最小侦察（探针脚本已在收口前删除），
撞到的不是「方法表难查」，而是我上一轮的抽取判据本身漏抽。三处洞、三个独立发现：

- 洞 A（窗口截断）：R110 为压反控基线，把 repe cmpsd 的接受窗口限成函数头 120 B（自错 L-02 的补丁）。
  这同时截断了多接口类后半段的 IID：HouseClass 的 QI 体（0x4f6830）实测有 6 个 mov edi,imm32，
  R110 只取到前 3 个。
- 洞 B（thunk 盲区）：12 个类的 slot0 不是 QI 本体，而是 MSVC this-adjustor thunk
  （sub dword ptr [esp + 4], N ; jmp <真实 QI>），槽 0 体内自然没有 cmpsd 形态。
- 洞 C（ATL 盲区）：3 个 ATL sink 的 QI 用内联 dword 立即数比较判 IID，根本不是 mov edi,<IID ptr> + repe cmpsd。

三处全部机械可核，且都不是「判据放松」—— 每处都给了新的正向形态判据。

### 2.115.2 洞 A 修正：按 HB 函数终点抽 ⇒ QI 类 172→172（不变）、distinct IID 17→18

把窗口换成 HB 边界（R109 §EK9 已证 HB 是唯一可靠边界；本轮全脚本唯一定界来源），其余判据一字不改：

- 有 QI 的类仍为 172（窗口不是「多个类漏掉」，是「一个类少了 IID」）。
- 被截断的类 1 个：HouseClass，6 个 IID 被截成 3 个（差 3 个实例）。
- distinct IID 17 → 18，新增的正是漏掉的那个：
  0x7f7cd0 = B196B284-BAB4-101A-B69C-00AA00341D07（IConnectionPointContainer）。
  R110 报的 4 个标准 OLE 对应里缺了它，本轮补上。
- 每类认 IID 个数分布：R110 的 1→1 / 2→92 / 3→3 / 4→76 变为 1→1 / 2→92 / 3→2 / 4→76 / 6→1。
  差别全在 HouseClass 从 3 变 6；原本 3 的那 3 个类里有 1 个是 HouseClass。
- 反控：随机 20000 个指令起点同判据同终点命中 116（0.580%）⇒ 富集 31.1 倍
  （R110 的 105/0.525% 是 120 B 窗口下的数，不可直接比）。
- 正向子集断言：R110 逐类 IID 集合 ⊆ 本轮集合，违例 0；指针去重与 16 字节内容去重仍双射；
  18 个 IID 全落 .rdata，0 个在 .text。

### 2.115.3 洞 B：12 个类的 slot0 是 adjustor thunk，N 全为 4 —— 与 COL.offset 是同一集合

判据：sub dword ptr [esp + 4], N ; jmp <imm32>（3 条指令内不得改写 N）。

- 命中 12 个类，N 取值分布 {4: 12} —— 全为 4。
- 这 12 个类：Drive / DropPod / Fly / Hover / Jumpjet / Locomotion / Mech / Rocket / Ship / Teleport / Tunnel / Walk
  （恰是 R110 §EL5 列出的那 12 张 Locomotion 族 offset==4 的表）。
- 集合等式（逐类比，不只比个数）：{slot0 是 thunk 的类} == {COL.offset != 0 的类}，对称差 []。
- 逐类 N == COL.offset，12/12。两条链不共用任何数据：N 读 .text 的 thunk 立即数，
  offset 读 .rdata 的 COL+4 且另由 §EL5 的装配点 disp 佐证。
- 反控：随机 20000 个指令起点里 thunk 形态 2（0.010%）；slot0 里 12/954 = 1.26% ⇒ 富集 125.8 倍。
- 穿透 thunk 到真实 QI 后重抽 IID：12/12 全部抽得到（共享本体 0x55a9b0 等 7 个目标，
  其中 7/7 从未作为任何类的 slot0 出现，即只经 thunk 可达）。
- 副作用：穿透后新增 2 个 distinct IID（cmpsd 链从未见过）：
  0x7e9b10 = 92FEA800-A184-11D1-B70A-00A024DDAFD1、0x7ed358 = 070F3290-9841-11D1-B709-00A024DDAFD1。

这条链的意义：§EL5 是「从 .rdata 侧的 offset 预测 .text 侧装配点」，本轮是「从 .text 侧的 thunk 立即数
预测 .rdata 侧的 offset」，方向相反、集合相等、逐类数值相等。COL.offset 的语义至此有三条独立证据。

### 2.115.4 洞 C：3 个 ATL sink 用内联 dword 比较，反解出 IUnknown

形态（0x7ac700 为例，同一基址上四段齐全）：
cmp dword [edi], 0 → mov eax,[edi+4] + test eax,eax → cmp dword [edi+8], 0xc0 → cmp dword [edi+0xc], 0x46000000。
四段 ⇒ 16 字节 00000000-0000-0000-C000-000000000046，与 IUnknown 逐字节相等。

- 命中 3 个类：?$CComObject@VCChatEventSink@@@ATL / ...DownloadEventSink@@@ATL / ...NetUtilEventSink@@@ATL。
- 这条链有硬盲区：只有「后 8 字节为 C000000000000046」的 IID 族才能这样编（编译器得把 16 字节拆成
  可立即数的 4 个 dword，且中间两个必须为 0）。对一般 IID 无法这样编，
  故「未抽到 = 没有接口」这个推论不成立，本轮不据此下任何「某类无接口」的结论。

### 2.115.5 合并口径：三种编码、两栏数字，不混算

| 编码 | 类数 | 判据 | 抽出物 |
|---|---|---|---|
| CMPSD | 172 | mov ecx,4 → mov edi,IID ptr → repe cmpsd，HB 定界 | .rdata 指针 |
| TH | 12 | sub [esp+4],N ; jmp T，穿透 T 后同 CMPSD 判据 | .rdata 指针 |
| ATL | 3 | 四段内联 dword 比较 | 16 字节内容 |

合计 187 个类（19.6% of 954），三支两两不相交（172+12+3=187，互斥断言 PASS）。

- ptr 支（CMPSD+TH）：cmpsd 链 18 → 合并 20 个 distinct IID；R110 的 17 个全为子集，
  本轮新增 3 个：0x7f7cd0（洞 A）、0x7e9b10 / 0x7ed358（洞 B）。
- content 支（ATL）：1 个，等于 IUnknown。不并入 ptr 支计数（一个是 .rdata 指针、一个是 16 字节内容，
  混算会是同一语义的重复计数）。
- 反控：随机 20000 起点「任一形态」命中 116（0.580%）= CMPSD 112 + ATL 2 + TH 2；
  slot0 里 187/954 = 19.60% ⇒ 富集 33.8 倍。

### 2.115.6 双向集合等式：把「4 个 IID 与类名逐字对应」升级成集合检验

R110 §EL3 只做到「17 个里 4 个与 RTTI 类名逐字对应」——那是举例。本轮做集合等式：
对每个 IID 取认领类集合 Q(iid)，对每个接口名 b（bases 里 I 开头第 2 字母大写的驼峰）取声明集合 C(b)，
Q == C 称精确对应。两条链来源独立（GUID 在 .rdata 的 16 字节 / 接口名在 RTTI TD 的装饰名里）。

- 精确相等 8 个：IClassFactory(78)、IApplication、ISwizzle、IFlyControl、IWOLBrowserEvent、
  IEnumConnections、IConnectionPoint、IEnumConnectionPoints。
- 歧义 5 个（多个接口名集合完全相同，故照报全部候选、不挑一个当定论）：
  0x7e9530 / 0x7f7cf0 → {IStream, ISequentialStream, ILinkStream}；
  0x7e9b00 / 0x7ea768 / 0x7f7cd0 → {IHouse, IPublicHouse, IConnectionPointContainer}。
- 无精确相等 5 个，逐个机械归因（判据：T=thunk / S=空桩 xor eax,eax;ret / D=委托 / A=ATL）：
  IUnknown(171 认领) 残差 18 类 = T:12 + A:3 + S:2 + D:1。四类形态全部解释得掉，无语义不符类。
- 一个真反常：0x7ea6e8 被 10 个类认领，但 IGameMap 只声明 9 个 —— 是多认
  （ApplicationClass 认它但没声明 IGameMap），不是少认。GUID 96F02EC7-… 与 IApplication 的 96F02EC3-…
  只差最后一位数字，判为同一族接口的相邻成员。
- 反控：随机同规模类集合 20000 次，撞上任一 Q(iid) 的 99 次（0.495%）⇒ 集合等式不是松判据。

### 2.115.7 子代理（hy4 #190 + deepseek #191，两支都 succeeded，8/8 一致）

派 2 支（开局 mem 1192 MB / MAX_SUBAGENTS=3，留 1 支余量），跨家族 hy4 ↔ deepseek 配对，各 8 条只读核对。
两支都 succeeded、8/8 一致，用时 15 s / 14 s，回合 4 / 5，无 [OVERTIME]。

按 §2.12 规则 D，主会话独立实现复算其全部 8 条（r111e），另加 4 条只读原始字节、不碰 JSON
的独立复算（X1–X4），合计 12/12 PASS：

- X1 原始字节扫 0x4f6830 内的 mov edi,imm32 得 6 个 —— 直接证洞 A。
- X2 12 个 Locomotion 类 slot0 前 6 字节均为 83 6c 24 04 04 e9 —— 直接证洞 B。
- X3 12 个类 COL.offset 独立从 .rdata 读，全为 4。
- X4 0x7f7c90 16 字节 == IUnknown。

deepseek #191 指出一处我该改的口径：r111b 的键名是 trials 而 r111a/r111c 是 n，数值都是 20000。
它说得对，同一语义三处不同键名是我的疏漏（不重跑，只在 JSON 里保持原样并在此记明）。

### 2.115.8 自错 9 处（全部由断言当场抓住，不隐去）

- L-01 把 Σn=613 写进断言当「实测」——实为 501。写死未测数字等于没断言。
- L-02 把「限 172 类里出现的接口名 21 个」当全库数——全库实为 33 个。
- L-03 用 IClassFactory/IPersist 作 0x7f7c70 的残差判据，但 IPersist 也是 IClassFactory 的基类，
  残差里混进 78 个 TClassFactory 类 ⇒ 该条断言不可解释，已改为按 slot0 形态逐类归因（§2.115.6）。
- L-04 r111d 上一稿把 cmpsd 抽取的 HB 定界换成 700 B 裸窗口 ⇒ 窗口溢出到下一个函数，
  ?$VectorCursor@IV?$DynamicVectorClass@I@@ 的析构函数（0x4f3fd0）被误判成第 173 个 QI 类。
  F1b 的集合相等断言当场抓住（extra 非空）。r111a 是对的，是我在合并时把边界纪律丢了。
- L-05 ATL 形态写成「4 个 cmp 齐全」，实测第 2 段是 mov+test（判 0）而非 cmp ⇒ ATL 类恒 0。
- L-06 ATL 累加器在每条指令后都清空 ⇒ 永远攒不到 4 段，ATL 类恒 0（与 L-05 叠成同一现象）。
- L-07 cmp dword [edi], 0 的值是十进制 0，原正则只认 0x 前缀 ⇒ 第 1 段永远抽不到。
- L-08 基址用宽匹配 ⇒ 绝对地址 [0x7f76a0] 被当成寄存器基址，污染累加器。
- L-09 ATL 抽到的是 16 字节内容、ptr 支是指针，混进同一张 Counter ⇒ hex(bytes) 直接 TypeError 崩。
  已分两栏（ptr 支 / content 支），不混算。
- 附带：fn() 初版逐指令调 capstone，反控 20000×3 形态要跑 6 分钟以上；改成一次 64 KB 窗口 +
  1536 B 上界（远大于任何实测 QI 体：最长实测 223 B）后才压到 100 s。这是性能自错，不改结论。

### 2.115.9 收口

- 五个带断言脚本合计 60 项断言，PASS 60 / FAIL 0（a 14 / b 12 / c 8 / d 14 / e 12，由各 JSON 的 checks 直读累加）。
- check_disc.py exit 0（31 条纪律全过）。
- 五项 CR 全绿：R14_COMMON 1081 / LEAD_LOCK 137 / 台账 337 / STATUS_BOARD 0 / BOARD_ARCHIVE 2952。
- 看板开局 216 行 < 260 ⇒ 本轮不归档；写入本轮段后实测行数并在 §2.115.10 记明。
- 收口前 ps 核对无 r111* 孤儿进程。
- 内存纪律：全段扫描一律 disasm_lite + 64 KB 分块，从未对整段开 detail=True；
  函数体一律 HB 定界 + 1536 B 上界；探针脚本收口前全部删除（_r111/ 只留五个带断言脚本与 JSON）。
- 未取得（如实记）：① 20 个 ptr 支 IID 的接口方法表（每个 IID 对应哪些虚方法）仍未查 ——
  本轮用探针把「QI 成功分支把哪个指针写回 ppv」试抽了一遍，绝大多数站点是 mov [ppv], <reg>
  （原样返回 this，即 offset 0），仅极少数带 lea 偏移；该探针未作正式统计口径（未落 JSON、未带断言），
  故本节不报数字。thunk 那 12 类的偏移已在 §2.115.3 由 N 直接给出，
  故这条的剩余价值是「11 个自研 IID 的方法表」，工作量仍大于一轮；
  ② 0x7e9ae0（76 类）与 0x7f7c70 / 0x7f7c80（77 类）三者的语义区分未定 ——
  它们认领集合只差 1 个类，且接口名候选多重歧义。
