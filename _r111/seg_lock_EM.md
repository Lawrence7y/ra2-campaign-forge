
EM. R111（2026-11-24）· 补 R110 三处漏抽：120 B 窗口截断 + slot0 adjustor thunk 盲区 + ATL 内联比较盲区；COL.offset==4 拿到第三条独立链

EM1. 📊 **本轮定位**：R110 §EL11 把「每个 IID 的接口方法表未查」列为未取得。
本轮开工先做最小侦察，撞到的不是「方法表难查」，而是**我上一轮的抽取判据本身有三个洞**。
三处彼此独立、全部机械可核，且都不是「判据放松」—— 每处都补了新的正向形态判据。

EM2. ✅ **洞 A：120 B 窗口截断多接口类的后半段**（R110 自错 L-02 的补丁带来的副作用）
    R110 为压反控基线，把 `repe cmpsd` 的接受窗口限成**函数头 120 B**。
    HouseClass 的 QI 体 `0x4f6830` 实测有 **6** 个 `mov edi,imm32`，R110 只取到前 **3** 个。
    换成 **HB 定界**后（其余判据一字不改）：有 QI 的类**仍 172**，被截断仅 **1 类**，
    distinct IID **17 → 18**，补上的正是 `0x7f7cd0 = B196B284-…`（**IConnectionPointContainer**）——
    R110 报的 4 个标准 OLE 对应里就缺它。分布 `1→1/2→92/3→3/4→76` 变 `1→1/2→92/3→2/4→76/6→1`。
    反控 20000 起点同判据同终点命中 **116（0.580%）** ⇒ 富集 **31.1 倍**
    （R110 的 105/0.525% 是 120 B 窗口下的数，不可直接比）。

EM3. ✅ **洞 B：12 类的 slot0 是 adjustor thunk，N 全为 4**，且与 COL.offset **同一个集合**
    判据 `sub dword ptr [esp+4], N ; jmp <imm32>`（3 条内不得改写 N）⇒ 命中 **12** 类，**N 分布 {4:12}**。
    这 12 类恰是 R110 §EL5 列出的那 12 张 Locomotion 族 offset==4 的表
    （Drive/DropPod/Fly/Hover/Jumpjet/Locomotion/Mech/Rocket/Ship/Teleport/Tunnel/Walk）。
    - **集合等式**（逐类比，不只比个数）：{slot0 是 thunk 的类} == {COL.offset != 0 的类}，对称差 **[]**。
    - **逐类 N == COL.offset，12/12**。两链不共用数据：N 读 `.text` 立即数，offset 读 `.rdata` 的 COL+4。
    - 反控：随机 20000 起点里 thunk 形态 **2（0.010%）**；slot0 里 12/954 = 1.26% ⇒ 富集 **125.8 倍**。
    - 穿透 12/12 全抽得到 IID；**7 个 thunk 目标从未作为任何类的 slot0 出现**（只经 thunk 可达）；
      并新增 **2 个 cmpsd 链从未见过的 distinct IID**：`0x7e9b10`(92FEA800-…)、`0x7ed358`(070F3290-…)。
    **意义**：§EL5 是「.rdata 侧 offset 预测 .text 侧装配点」，本轮是「.text 侧 thunk 立即数预测 .rdata 侧 offset」，
    方向相反、集合相等、逐类数值相等 ⇒ **COL.offset 语义至此三条独立证据**。

EM4. ✅ **洞 C：3 个 ATL sink 用内联 dword 比较**，反解出 IUnknown（此链有硬盲区）
    形态：`cmp [edi],0` → `mov eax,[edi+4]`+`test eax,eax` → `cmp [edi+8],0xc0` → `cmp [edi+0xc],0x46000000`。
    四段 ⇒ 16 字节 `00000000-…-C000000000000046`，与 IUnknown **逐字节相等**。
    命中 3 类（`?$CComObject@…ChatEventSink/DownloadEventSink/NetUtilEventSink@@@ATL`）。
    **盲区**：只有「后 8 字节为 `C000000000000046`」的 IID 族才能这样编（16 字节拆成 4 个可立即数 dword，
    中间两个必须为 0）⇒ **「未抽到 = 没有接口」不成立**，本轮不据此下任何「某类无接口」结论。

EM5. 📊 **合并口径：三种编码、两栏数字，不混算**
    CMPSD 172（HB 定界）+ TH 12（穿透后同判据）+ ATL 3（内联比较）= **187 类**（19.6% of 954），
    三支**两两不相交**（互斥断言 PASS）。**ptr 支 20 个 distinct IID**（cmpsd 18 → 加 TH 20，
    R110 的 17 个全是子集，新增 `0x7f7cd0`/`0x7e9b10`/`0x7ed358`）；
    **content 支 1 个** = IUnknown，**不并入 ptr 支计数**（一是指针一是内容，混算是同一语义重复计数）。
    反控：「任一形态」随机 20000 起点命中 **116（0.580%）**=CMPSD 112+ATL 2+TH 2；19.60% ⇒ 富集 **33.8 倍**。

EM6. ✅ **双向集合等式：把「4 个 IID 与类名逐字对应」升级成集合检验**
    对每个 IID 取认领类集合 Q(iid)，每个接口名 b 取声明集合 C(b)，Q==C 称精确对应。
    **精确相等 8 个**：IClassFactory(78)/IApplication/ISwizzle/IFlyControl/IWOLBrowserEvent/
    IEnumConnections/IConnectionPoint/IEnumConnectionPoints。
    **歧义 5 个**（多个接口名集合完全相同 ⇒ **照报全部候选、不挑一个当定论**）：
    `0x7e9530`、`0x7f7cf0` → {IStream, ISequentialStream, ILinkStream}；
    `0x7e9b00`、`0x7ea768`、`0x7f7cd0` → {IHouse, IPublicHouse, IConnectionPointContainer}。
    **无精确相等 5 个**，逐个机械归因（T=thunk/S=空桩/D=委托/A=ATL）：
    IUnknown(171 认领) 残差 **18 类 = T:12 + A:3 + S:2 + D:1**，四类形态全解释得掉、无语义不符类。
    **一个真反常**：`0x7ea6e8` 被 **10** 类认领但 IGameMap 只声明 **9** 个 —— 是**多认**
    （ApplicationClass 认它但没声明 IGameMap），不是少认；GUID `96F02EC7-…` 与 IApplication 的
    `96F02EC3-…` 只差最后一位数字。
    反控：随机同规模类集合 20000 次撞上任一 Q(iid) 的 **99 次（0.495%）** ⇒ 等式不是松判据。

EM7. 📌 **子代理：hy4 #190 + deepseek #191，两支都 succeeded，8/8 一致**
    跨家族配对，各 8 条只读核对，用时 15 s / 14 s，回合 4 / 5，**无 [OVERTIME]**。
    派 2 支（开局 mem 1192 MB / MAX_SUBAGENTS=3，留 1 支余量）。
    按 §2.12 规则 D 主会话**独立实现**复算其全部 8 条（`r111e`），另加 4 条**只读原始字节、不碰 JSON**的
    独立复算（X1–X4），合计 **12/12 PASS**：
    X1 原始字节扫 `0x4f6830` 内 `mov edi,imm32` 得 **6** 个（直证洞 A）；
    X2 12 类 slot0 前 6 字节均 `83 6c 24 04 04 e9`（直证洞 B）；X3 12 类 COL.offset 独立读全为 4；
    X4 `0x7f7c90` 16 字节 == IUnknown。
    deepseek 指出我该改的口径：`r111b` 键名是 `trials` 而 `r111a`/`r111c` 是 `n`（值都 20000）—— 它对，我的疏漏。

EM8. 📌 **自错 9 处（全由断言当场抓住，不隐去）**
    L-01 把 Σn=**613** 当实测写进断言（实为 **501**）；L-02 把「限 172 类里的接口名 21 个」当全库（实为 **33**）；
    L-03 用 IClassFactory/IPersist 做 `0x7f7c70` 残差判据，但 IPersist 也是 IClassFactory 的基类，
    残差混进 78 个 TClassFactory 类 ⇒ 该条不可解释，改按 slot0 形态逐类归因；
    **L-04 `r111d` 上一稿把 HB 定界换成 700 B 裸窗口 ⇒ 溢出到下一函数，
    `?$VectorCursor@IV?$DynamicVectorClass@I@@` 的析构函数 `0x4f3fd0` 被误判成第 173 个 QI 类，
    F1b 集合相等断言当场抓住 —— r111a 是对的，是我在合并时把边界纪律丢了**；
    L-05 ATL 第 2 段实为 `mov`+`test` 不是 `cmp` ⇒ ATL 恒 0；L-06 ATL 累加器每条指令后清空 ⇒ 永远攒不到 4 段；
    L-07 `cmp` 的值是十进制 0，正则只认 `0x` ⇒ 第 1 段抽不到；L-08 基址宽匹配 ⇒ 绝对地址 `[0x7f76a0]` 被当基址；
    L-09 ATL 内容与 ptr 支混进同一 `Counter` ⇒ `hex(bytes)` TypeError 崩，已分两栏不混算。
    （附：`fn()` 初版逐指令调 capstone，反控 20000×3 形态要 6 分钟以上；改一次 64 KB 窗口 + 1536 B 上界后 100 s。
    性能自错，不改结论。）

EM9. 📊 **收口数字**：五个带断言脚本合计 **60 项 / PASS 60 / FAIL 0**（a 14 / b 12 / c 8 / d 14 / e 12，
    由各 JSON 的 `checks` 直读累加）。`check_disc.py` **exit 0**（31 条纪律全过）。
    五项 CR 全绿 1081 / 137 / 337 / 0 / 2952。看板开局 **216 行 < 260 ⇒ 本轮不归档**。
    收口前 `ps` 核对无 `r111*` 孤儿进程。
    内存纪律：全段一律 `disasm_lite` + 64 KB 分块，从未对整段 `detail=True`；
    函数体一律 HB 定界 + 1536 B 上界（远大于任何实测 QI 体：最长实测 223 B）；
    探针脚本收口前全部删除（`_r111/` 只留五个带断言脚本与 JSON）。

EM10. 📌 **未取得（如实记，不写成「已完成」）**
    ① 20 个 ptr 支 IID 的**接口方法表**仍未查。本轮用探针试抽「QI 成功分支把哪个指针写回 ppv」，
       绝大多数站点是 `mov [ppv], <reg>`（原样返回 this，即 offset 0），极少数带 `lea` 偏移；
       该探针**未落 JSON、未带断言**，故本节**不报数字**。thunk 那 12 类的偏移已由 §EM3 的 N 直接给出，
       故这条的剩余价值是「11 个自研 IID 的方法表」，工作量仍大于一轮。
    ② `0x7e9ae0`(76 类) 与 `0x7f7c70`/`0x7f7c80`(77 类) 三者语义区分未定 ——
       它们认领集合只差 1 个类，且接口名候选多重歧义。

EM11. 🧭 **方法学（下轮可复用）**：本轮三次洞都不是「找不到」，而是**判据自己把证据挡在外面**——
    缩短窗口压反控、thunk 让槽 0 没有目标形态、ATL 换了一种等价编码。
    可复用的自检句式：**「我这条判据的接受窗口/形态假设，会不会正好排除掉一类真实目标？」**
    另一个反复出现的教训：**凡是把「为了压基线」而加的限制，都必须同时验证它没有改变目标集合**
    （本轮 L-04 就是压基线压过头、把 HB 换成了裸窗口）。
