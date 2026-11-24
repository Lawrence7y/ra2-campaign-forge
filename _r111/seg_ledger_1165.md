
## §1165 R111（2026-11-24）· 补 R110 三处漏抽：120 B 窗口截断（HouseClass 6 个 IID 截成 3）+ slot0 adjustor thunk 盲区（12 类）+ ATL 内联比较盲区（3 类）⇒ QI 类 172→187、distinct IID 17→20；COL.offset==4 得第三条独立链（thunk 立即数 N，集合等式 + 逐类 N==offset 12/12，反控富集 125.8 倍）；双向集合等式 8 精确 + 5 歧义 + 5 归因，反控 0.495%

**本轮不是「查方法表」，是先发现上一轮判据有三个洞。** R110 §EL11 把「接口方法表未查」列为未取得，
本轮开工侦察时发现真正的问题是我自己的抽取判据漏抽——三处，彼此独立，全部机械可核。

### 判据扩成三种编码（互斥，合计 187 类 = 19.6% of 954）

| 编码 | 类数 | 判据 | 抽出物 |
|---|---|---|---|
| CMPSD | 172 | mov ecx,4 → mov edi,IID ptr → repe cmpsd，**HB 定界** | .rdata 指针 |
| TH | 12 | sub dword [esp+4],N ; jmp T（穿透 T 后同 CMPSD 判据） | .rdata 指针 |
| ATL | 3 | cmp [edi],0 / mov+test [edi+4] / cmp [edi+8],0xc0 / cmp [edi+0xc],0x46000000 | 16 字节内容 |

三支两两不相交（172+12+3=187，互斥断言 PASS）。**ptr 支 20 个 distinct IID**（cmpsd 18 → 加 TH 20，
R110 的 17 全是子集，新增 0x7f7cd0 / 0x7e9b10 / 0x7ed358）；**content 支 1 个** = IUnknown，不并入 ptr 支计数。

### 洞 A：HB 定界取代 120 B 窗口 ⇒ 类数不变、IID 17→18

- R110 为压反控把 cmpsd 窗口限成函数头 120 B（自错 L-02 的补丁），同时截断多接口类后半段。
- 按 HB 终点重抽：有 QI 的类仍 172（不是「漏了好几个类」，是「一个类少了 IID」）。
- 被截断仅 **1 类**：HouseClass，**6 个 IID 截成 3 个**（0x4f6830 实测 6 个 mov edi,imm32）。
- distinct IID **17→18**，补上的正是 **0x7f7cd0 = B196B284-BAB4-101A-B69C-00AA00341D07 (IConnectionPointContainer)**
  —— R110 报的 4 个标准 OLE 对应里就缺它。
- 分布 1→1 / 2→92 / 3→3 / 4→76 变为 1→1 / 2→92 / 3→2 / 4→76 / **6→1**。
- 反控 20000 起点同判据同终点命中 116（0.580%）⇒ 富集 **31.1 倍**（R110 的 105/0.525% 是 120 B 窗口下的数，不可比）。
- 正向：R110 逐类 IID 集合 ⊆ 本轮，**违例 0**；指针去重与 16 字节内容去重仍**双射**；18 个全在 .rdata、0 个在 .text。

### 洞 B：12 类 slot0 是 adjustor thunk，N 全为 4 —— 与 COL.offset 同一个集合

- 判据 sub dword [esp+4],N ; jmp <imm32>（3 条内不得改写 N）⇒ 命中 **12** 类，**N 分布 {4:12}**。
- 12 类 = Drive/DropPod/Fly/Hover/Jumpjet/Locomotion/Mech/Rocket/Ship/Teleport/Tunnel/Walk，
  **恰是 R110 §EL5 那 12 张 Locomotion 族 offset==4 的表**。
- **集合等式**：{slot0 是 thunk 的类} == {COL.offset != 0 的类}，对称差 **[]**；**逐类 N == COL.offset，12/12**。
  两链不共用数据：N 读 .text 立即数，offset 读 .rdata 的 COL+4（另由 §EL5 装配点 disp 佐证）。
- 反控：随机 20000 起点里 thunk 形态 **2（0.010%）**；slot0 里 12/954 = 1.26% ⇒ 富集 **125.8 倍**。
- 穿透 thunk 后 12/12 都抽得到 IID；7 个 thunk 目标**从未作为任何类的 slot0 出现**（只经 thunk 可达）；
  并新增 **2 个 cmpsd 链从未见过的 distinct IID**：0x7e9b10 = 92FEA800-A184-11D1-B70A-00A024DDAFD1、
  0x7ed358 = 070F3290-9841-11D1-B709-00A024DDAFD1。
- 意义：§EL5 是「.rdata 侧 offset 预测 .text 侧装配点」，本轮是「.text 侧 thunk 立即数预测 .rdata 侧 offset」，
  方向相反、集合相等、逐类数值相等 ⇒ **COL.offset 语义至此三条独立证据**。

### 洞 C：3 个 ATL sink 用内联 dword 比较，反解出 IUnknown（且此链有硬盲区）

四段齐全 ⇒ 16 字节 00000000-0000-0000-C000-000000000046，与 IUnknown **逐字节相等**。
命中 3 类：?$CComObject@VCChatEventSink@@@ATL / ...DownloadEventSink@@@ATL / ...NetUtilEventSink@@@ATL。
**盲区**：只有「后 8 字节为 C000000000000046」的 IID 族才能这样编（16 字节拆成 4 个可立即数 dword，
中间两个必须为 0）。对一般 IID 无法这样编，故 **「未抽到 = 没有接口」不成立**，本轮不据此下任何「某类无接口」结论。

### 双向集合等式（把「4 个逐字对应」升级成集合检验）

对每个 IID 取认领类集合 Q(iid)，每个接口名 b 取声明集合 C(b)，Q==C 称精确对应。
两条链来源独立（GUID 在 .rdata 16 字节 / 接口名在 RTTI TD 装饰名里）。

- **精确相等 8 个**：IClassFactory(78) / IApplication / ISwizzle / IFlyControl / IWOLBrowserEvent /
  IEnumConnections / IConnectionPoint / IEnumConnectionPoints。
- **歧义 5 个**（多个接口名集合完全相同 ⇒ **照报全部候选、不挑一个当定论**）：
  0x7e9530、0x7f7cf0 → {IStream, ISequentialStream, ILinkStream}；
  0x7e9b00、0x7ea768、0x7f7cd0 → {IHouse, IPublicHouse, IConnectionPointContainer}。
- **无精确相等 5 个**，逐个机械归因（T=thunk / S=空桩 xor eax,eax;ret / D=委托 / A=ATL）：
  IUnknown(171 认领) 残差 **18 类 = T:12 + A:3 + S:2 + D:1**，四类形态全解释得掉，无语义不符类。
- **一个真反常**：0x7ea6e8 被 **10** 类认领但 IGameMap 只声明 **9** 个 —— 是**多认**（ApplicationClass 认它但
  没声明 IGameMap），不是少认。GUID 96F02EC7-… 与 IApplication 的 96F02EC3-… 只差最后一位数字。
- 反控：随机同规模类集合 20000 次撞上任一 Q(iid) 的 **99 次（0.495%）** ⇒ 集合等式不是松判据。

### 子代理与复算

hy4 **#190** + deepseek **#191**，跨家族配对，各 8 条只读核对，**两支 succeeded、8/8 一致**，
15 s / 14 s，回合 4 / 5，**无 [OVERTIME]**；派 2 支（开局 mem 1192 MB / MAX=3，留 1 支余量）。
按 §2.12 规则 D 主会话**独立实现**复算其全部 8 条（r111e），另加 4 条**只读原始字节、不碰 JSON**的
独立复算（X1–X4），合计 **12/12 PASS**：X1 原始字节扫 0x4f6830 内 mov edi,imm32 得 **6** 个（直证洞 A）；
X2 12 类 slot0 前 6 字节均 83 6c 24 04 04 e9（直证洞 B）；X3 12 类 COL.offset 独立读全为 4；X4 IUnknown 16 字节。
deepseek 指出我该改的口径：r111b 键名 trials 而 r111a/r111c 是 n（值都 20000）—— 它对，我的疏漏。

### 自错 9 处（全由断言当场抓住）

L-01 把 Σn=613 当实测写进断言（实为 **501**）；L-02 把「限 172 类里的接口名 21 个」当全库（实为 **33**）；
L-03 用 IClassFactory/IPersist 做 0x7f7c70 残差判据，但 IPersist 也是 IClassFactory 的基类，残差混进 78 个
TClassFactory 类 ⇒ 该条不可解释，改按 slot0 形态逐类归因；
**L-04 r111d 上一稿把 HB 定界换成 700 B 裸窗口 ⇒ 溢出到下一函数，?$VectorCursor@IV?$DynamicVectorClass@I@@
的析构函数 0x4f3fd0 被误判成第 173 个 QI 类，F1b 集合相等断言当场抓住 —— r111a 是对的，是我丢边界纪律**；
L-05 ATL 第 2 段实为 mov+test 不是 cmp ⇒ ATL 恒 0；L-06 ATL 累加器每条指令后清空 ⇒ 永远攒不到 4 段；
L-07 cmp 的值是十进制 0，正则只认 0x ⇒ 第 1 段抽不到；L-08 基址宽匹配 ⇒ 绝对地址 [0x7f76a0] 被当基址；
L-09 ATL 内容与 ptr 支混进同一 Counter ⇒ hex(bytes) TypeError 崩，已分两栏不混算。
（附：fn() 初版逐指令调 capstone，反控 20000×3 形态要 6 分钟以上；改一次 64 KB 窗口 + 1536 B 上界后 100 s。性能自错，不改结论。）

### 收口

五个带断言脚本合计 **60 项 / PASS 60 / FAIL 0**（a14 b12 c8 d14 e12）；check_disc.py **exit 0**；
五项 CR 全绿 1081 / 137 / 337 / 0 / 2952；看板开局 **216 行 < 260 ⇒ 不归档**；
收口前 ps 无 r111* 孤儿；全段 disasm_lite + 64 KB 分块，从未整段 detail=True；
函数体一律 HB 定界 + 1536 B 上界；探针脚本收口前全部删除。

**未取得**：① 20 个 ptr 支 IID 的接口方法表仍未查（本轮探针试抽「QI 成功分支写回哪个指针」，
绝大多数是 mov [ppv],<reg> 即原样返回 this；该探针未落 JSON、未带断言，故不报数字；thunk 那 12 类的偏移
已由 §2.115.3 的 N 直接给出）；② 0x7e9ae0(76 类) 与 0x7f7c70/0x7f7c80(77 类) 三者语义区分未定
（认领集合只差 1 类，接口名候选多重歧义）。
