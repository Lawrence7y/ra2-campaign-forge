# R203-VDISP-AUDIT 跨家族只读复核（deepseek 家族 / 角色 audit）

被审对象（未修改，仅读）：

| 文件 | sha256 前 16 | 字节 | 行 |
|---|---|---|---|
| _r203/m1_dispatch.py | 097631811f3b0924 | 8697 | 157 |
| _r203/m1_dispatch.json | f6ab7bc3f6214f88 | 2907 | 226 |
| _r203/m2_prologue.py | 7c7db0aa6b51a1b6 | 6101 | 116 |
| _r203/m2_prologue.json | 9224dd8c983d362b | 3830 | 181 |

复核环境：gamemd.exe .text = [0x401000, 0x7e1000) 共 4063232 字节；capstone 5.0.7；COL 记录 1214 条全部落在 .rdata。
全部数值由我在本次会话独立重算（未调用执行员脚本，未写任何托管文件）。

---

## 一、结论表

判定只有 PASS / FAIL 两档。

| 编号 | 判定 | 我的数值 | 依据 |
|---|---|---|---|
| A1 | PASS | 1214 | 我的独立 COL 扫描（sig<=2、cd==0、ptd@.data、pchd@.rdata、名以 .?A 开头且以 @@ 结尾）得 1214，偏差 0 |
| A2 | PASS | VT=1214，COL→VT 是双射 | 1 个 vtable 位置对应 1 个 COL，1214 个 COL 全部被引用，0 未用。注意：断言后半句「每个 vt-4 都是 COL」是 m1_dispatch.py:41 的构造条件，恒真；真正有信息量的是双射 |
| A3 | PASS | 14044 | 偏差 0；且 depth 上限 401 从未触发（max depth = 344），说明截断不是人为造成的 |
| A4 | PASS | 6692 | 偏差 0。附风险：199 个 vtable 恰好只有 1 槽（占 16.4%），其槽位目标仅 12.06% 能通过入口判据 W；但这不改变 6692 这个基数 |
| A5 | **FAIL** | 0（与主张同值，但该判据无任何证据力） | 该断言在结构上永不可能非零，见第二节 2.1；随机期望重叠 = 14044×1214/2^32 = 0.0040 次 |
| A6 | **FAIL** | min depth = 1（与主张同值，构造恒真） | VT 的构造条件 m1_dispatch.py:41 要求 slot0 落 .text，所以每表至少 1 槽必然成立，见 2.2 |
| A7 | PASS | 直方图首位 (7, 412)，次位 (1, 199)、第三 (5, 160) | 复现一致。但该断言把 (7,412) 整体写成常量对（m1_dispatch.py:57），只起回归锁作用，不能自证 |
| A8 | PASS | 94786 / 68253 / 26533 / 68244 | 四项偏差均为 0。点名问题：68244 的分母 68253 混入了 9 条数据区伪解码（见 2.1 分母不同源） |
| A9 | PASS | 26533 = 3832 + 18895 + 3797 + 9（算术复现） | 四个桶值与总和全部复现。但分类不一致，见 2.1：3 条 ptr [ecx] 与 2 条负位移被塞进「其它」 |
| A10 | **FAIL** | 桶数 341（执行员口径）/ 343（含 2 个负位移）；非 4 倍数 = 0；top: **8:1713** > 12:1525 > 16:1325 > 132:1130 > 44:1109 > 72:929 > 0:817 | 数值 341 与非 4 倍数为 0 都对，但「最多的前几位」排序错：首位是 disp=8（1713 次），主张遗漏了它并把 1525 当首位。且 m1_dispatch.py:106 还写着陈旧常量 339，该断言在 json 里已 FAIL |
| A11 | PASS | 6719 / 433 / 6259 / 6286 | 偏差 0。内部自洽：433+6259=6692=A4，433+6286=6719 |
| A12 | PASS | 0x84: 85 vtable / 22 目标；0x48: 137 vtable / 27 目标；Spearman(#vts,#targets)=0.909（n=11） | 四项数值偏差 0，正相关成立。必须订正标签：最窄的是 disp=72（ratio 0.197），132 是 0.259，C7 名字里的「最窄接口」挂错了对象 |
| B1 | PASS | 13 条地址集合与主张完全一致（逐字节比对 True） | 我重算的 {t ∈ TGT, t ∉ ASET} 与主张的 13 条是同一集合 |
| B2 | PASS | 13/13 都以 ret 收束；0x43fb20 = 417 条指令 / 1490 字节 | 主张本身（都能解到 ret）成立。主会话测出的 12/13 是 1400 字节取窗截断造成的假象：0x43fb20 需 1490 字节 |
| B3 | PASS | 13/13 的前置区都是数据 | 解释成立。我给出更强机制：每个地址前面要么是 0x90 对齐填充（pad90 >= 4 的有 6/13），要么是连续 .text dword 游程（跳转表，>=3 的有 9/13），要么是 0x01/0x0a/0x03 重复字节填充。线性扫描在这些数据上失步，把填充连同函数头一起吞掉（覆盖指令恒为 add byte ptr [eax - 0x6f6f6f70], dl 这类吞掉 90 90 90 90 的伪指令） |
| B4 | **FAIL** | 5/13 复现；我认可的判据 W 在 13 条上 13/13，反控 0/39，假阳 0.0180 | 判据过严，见第四节 4.1-4.3 |

汇总：共 16 条主张，PASS 12 / FAIL 4（FAIL = A5、A6、A10、B4）。

执行员 json 的 fails 只记录 m1 的 B4(339) 与 D2 两条，与我判 FAIL 的集合仅 B4 重叠；A5/A6/A10 这三处口径错误全部通过了执行员自己的自检。其中 A5/A6 是因为判据按构造恒真，A10 是因为排序主张从未被断言覆盖（脚本只断言了桶数，没断言排序）。

第七节的四条最小命令我已在本次会话中原样执行，全部 rc=0 且输出与正文数值一致（见 §7 末尾的实测回显）。

---

## 二、反向检查 1：分母不同源（逐条点名）

### 2.1 A8 —— 68244/68253 的分母混入了数据区伪解码

主张「直接 call 里目标落 .text 内 68244」。分母 68253 是全部「op 以 0x 开头」的 call 解码结果，其中有 9 条目标是 .text 之外的垃圾值：

    0x409ff2 -> 0xc0c5a07e   0x52eb58 -> 0x46533e39   0x52ebc1 -> 0xe2e0ec18
    0x5a0074 -> 0xd45a5a67   0x6dfe39 -> 0xe971feab   0x70e915 -> 0xe8d3e98a
    0x783b68 -> 0xfa78b3a7   0x7ca1d8 -> 0xf07d1e7e   0x7dcbc8 -> 0xd87e4995

这 9 个**调用点地址本身**没有一个落在线性扫描的指令起点集合里（我用 [a not in ASET] 逐一验证，返回空），即它们本身就是失步区的伪 call。所以「68244 落 .text 内」的正确分母应当是「位于线性相位指令起点的直接 call」，而不是 68253。名目写的是「直接 call」，分母里却按「任意解码出的 call」计。

### 2.2 A9 —— 「基址+位移」与「纯寄存器」的边界自相矛盾

同一个语义（内存间接 call，基址寄存器 + 位移 0）被分到两个桶：

- [ecx] （capstone 打印为不带前缀的 [ecx]）→ 计入「基址+位移」，disp=0，共 817 条
- ptr [ecx] （0x5a0071 / 0x5a0079 / 0x5a0081，字节 ff 59 00 / ff 59 00 / ff 59 00，实为 call dword ptr [ecx]）→ 因 m1_dispatch.py:73 的正则要求「[」紧跟前缀，'ptr ' 前缀不匹配 → 落入「其它」

另外「基址+位移」桶实际上只收了 [reg + 正数]：m1_dispatch.py:73 的正则不允许负号，2 条 [ebp - 0x3c] 型（负位移）因此被推进「其它」，使「其它」从真实的 4 条 SIB 变体 + 3 条 ptr [ecx] = 7 膨胀到 9，「基址+位移」从 18897 缩到 18895。我用带符号解析器复算：abs 3832 / base 18897（含 2 负）/ reg 3797 / other 7。四分类之和 26533 是**构造上必然**保持的（分区不重不漏），所以「和 == 间接总数」这条断言不含证据。

### 2.3 A10 —— 「位移取值全部是 4 的倍数」的分母是被洗过的

分母 18895 已剔除上述 2 条负位移与 3 条 ptr [ecx]。被剔除的 -0x3c 等恰好也是 4 的倍数，所以结论侥幸没破，但分母与 A9 的「其它 9」不自洽：同一个量在两处名目下统计口径不同。

### 2.4 A11 与 C6 —— 同一个数字 6692 被贴到两个不同集合上（最易误读的一处）

- A4 名目：槽位去重目标 = 6692
- C6 名目：直接调用目标落指令起点 = 6692

两者**基数相同但不是同一集合**。我做了集合差：TGT == (DIRT ∩ ASET) 为 False，TGT−(DIRT∩ASET) = 6260，(DIRT∩ASET)−TGT = 6260。这是 433 交集下的纯巧合。任何后续轮次若把「6692」当作同一个对象引用，都会把两个各 6260 条不相交的目标混为一谈。建议台账里固定写成两个不同符号。

### 2.5 A12 —— ratio 的分母是「碰巧实现该槽的类数」，跨位移不可直接比

targets/vts 这个比值的分母按构造是「拥有该偏移槽位的 vtable 数」，随位移剧烈变化（85 到 1214）。用它给「接口宽窄」排序，等于用「参与者数量多少」去解释「映射到少数目标的集中度」，两件事不同质。可比的量应该是「每目标平均被多少个 vtable 共享」（我算的 vts/targets：72 为 5.1，132 为 3.9，0 为 1.4），这个量才单调对应「窄/宽」。

---

## 三、反向检查 2：恒真判据（逐条点名）

### 3.1 A5 —— 结构上永不可能非零（最严重）

m1_dispatch.py:54 判 (vt+d) in VT。而 VT 的构造条件是 m1_dispatch.py:41：P.dw(vt' - 4) in COL。
若 vt+d ∈ VT，则需 P.dw(vt+d-4) ∈ COL。vt+d-4 本身是槽位位置，其取值是**槽位目标**，必须是 .text 地址（m1_dispatch.py:49 的 in_text 已强制）；而 COL 的 1214 个 key **全部落在 .rdata**（我实测分布 {'.rdata': 1214}）。.text ∩ .rdata = ∅。

所以该表达式恒为 False，A5 的「0 次」不是观测结果，是类型不匹配的必然结果。它不能作为「槽位切分正确」的任何证据，也无法探测真正的风险（本 vtable 尾部与下一张 .text 指针表/跳转表粘连）。真正该做的检验是「vt+4k 是否等于某个**未知**指针表的起始」——这需要独立于 COL 的锚点，A5 没做。

### 3.2 A6 —— 构造恒真

m1_dispatch.py:41 要求 in_text(w[i])，即 slot0 必落 .text，于是 SLOT 循环第一轮必然登记，depth >= 1 必然成立。min=1 不是发现，是定义。这条断言应当删掉或替换为「depth 分布的 left-censoring 检查」。

### 3.3 A7 —— 非恒真，但是写死的常量对

A7 本身有判别力（数据变了会 FAIL），不算恒真；但 m1_dispatch.py:57 把 (7, 412) 整对写进断言，等同回归锁。且该直方图的 199 个单槽 vtable 提示槽模型可能有粘连（一张 vtable 后紧跟指针表时会被并进来），A7 无法区分「真的是 7 槽」与「被并到 7 槽」。

### 3.4 C7 —— 真正的恒真（并且是 A12 唯一支撑证据）

m1_dispatch.py:136：

    ck('C7 ...', HOTB['0x84']['vts'] if '0x84' in HOTB else <比较式>, ...)

132 ∈ HOT（m1_dispatch.py:127），所以 HOTB 必含 '0x84'，于是条件表达式求值为整数 85，而 85 为真 → ck 无条件 PASS。原本应该是 == 85 的比较被三元表达式短路掉了。我实测该表达式求值结果就是 85（int），确认恒真。
A12 的「85」因此不算执行员验证过；好在我独立复算得到 85，A12 结论仍成立，但 C7 这条断言必须重写。

### 3.5 D1（顺带）

m1_dispatch.py:143「VT 删 1 条则槽位目标集改变」：删掉一个 vtable 只会移除它独占的目标；若被删 vtable 全部目标都被别的表共享，集合不变。这是弱判据但非恒真，不计入 FAIL。

---

## 四、反向检查 3：预测值写死（点名行号）

判据：断言右侧是常量，而这个常量来自同一脚本的首测结果，脚本无法证伪自己「当初预测得对不对」。这类断言全部点名。

_r203/m1_dispatch.py：

    42  A1  == 1214
    43  A2  == 1214
    51  A3  == 14044
    52  A4  == 6692
    54  A5  右值期望写死为 0（detail 参数直接写 0）
    56  A6  >= 1
    57  A7  == (7, 412)
    99  B1  == 94786 and == 68253 and == 26533  ← 断言名里自己承认「主会话首测预测值写错，按实测订正」，这是写死的自供状
    101 B1b == 68244
    106 B4  == 339   ← **已失效**：json 的 disps 是 341，该断言在 fails 列表里。这是写死常量会腐烂的实证
    118 C1  == 6679
    120 C2  == 13
    122 C3  == 6719
    123 C4  == 433
    124 C5  == (6259, 6286)
    126 C6  == 6692
    136 C7  == 85（且被三元短路，见 3.4）

_r203/m2_prologue.py：

    59  E0  == 6692 and == 13
    94  E1a == 13
    95  E1b all(brk)
    96  E1c < 600
    97  E1d not any(is_regstart)
    98  E1e not any(is_dirt)   ← **符号反了**：13 条里 0x4d82b0 确实在 DIRT 中（json 第 131 行 is_dirt: true，实测 [0x4d82b0] in DIRT 为 True），断言写「全不是」因此 FAIL；正确的观测是 12/13 不是
    106 E4a rate < 0.20
    113 E4b rate < 0.15

结论：m1 有 17 处、m2 有 8 处常量断言。其中 106 已腐烂、98 符号错。第 99 行的注释是最直接的证据——执行员知道自己在把首测数字当「订正」写回去。

---

## 五、第四节：B4 判据过严的定量判定与替代判据

### 5.1 原判据（m2_prologue.py:75-81）的三个独立缺陷

    P0 = (前 6 条内 sub esp,imm) AND (前 6 条内 push) AND (前 8 条内 mov ...,ecx)

实测 5/13。逐条看被排除的 8 条：

    417c80  前 6 条根本没有 push/sub，直接 mov eax,[esp+0x10] 取参  -> 无栈帧函数，合法
    6eae60  mov eax,[esp+4]; mov edx,[ecx+0x70]                    -> 无栈帧 + 直接读 [esp+4]，合法
    4176f0  push ebx; push ebp; push esi; mov esi,ecx ...          -> 有 push 有 ecx，但没有 sub esp（靠 push 建帧），合法
    417bd0  push ebp; mov ebp,[esp+0x10]; push esi; mov esi,ecx    -> 同上，合法
    41bbd0  push esi; mov esi,ecx ...                              -> 同上，合法
    4c49a0  push ebx; push esi; mov esi,ecx; xor ebx,ebx           -> 同上，合法
    41bb30  mov eax,[ecx+0xac]; push esi; mov esi,[esp+8]          -> 无帧，合法
    729e50  sub esp,0x28; push ebx; push esi; mov esi,[esp+0x34]   -> 有 sub 有 push，但没有 mov reg,ecx（this 不从 ecx 转存），合法

即：**(a) 强制 sub esp,imm 排除了无栈帧/纯 push 建帧函数；(b) 强制 mov ...,ecx 排除了不改存 this 的函数。** 这两条与「是不是函数入口」没有因果关系，只与 MSVC 的某一种代码风格相关。

### 5.2 顺带发现：m1/m2 里的 8 条窗口是死代码

m2_prologue.py:77 m = [x[2] for x in seq[:6]]，第 80 行写 range(min(8, len(m)))——len(m) 已 <= 6，故窗口实为 6。修正为 seq[:8] 后命中数仍是 5/13（我实测 P0 与 P0fix 同为 5/13），说明主因是判据语义，不是这个 bug；但 bug 必须修，否则以后会误判。

### 5.3 我认可的判据 W 与命中数

判据 W（入口自洽性，不依赖编译器风格）：

1. 地址 16 字节对齐（169/169 实测：13 条全部 %16==0；全 .text 里 16 对齐起点 253952 个中的 63.45% 不在线性相位，所以单看对齐没有判别力，必须配合下面几条）
2. 首条指令不是 ret/int3/nop/hlt/ud2/leave/jmp/call/jcc（不能从填充或跳转处起算）
3. 以该地址 detail 解码，8 KB 内必须以 ret/int3 收束
4. 前置区必须是数据：往前 32 字节内存在 >= 4 的重复字节游程（0x90/0x01/0x0a/0x03 填充），或往前 48 字节内存在 >= 3 个连续落 .text 的 dword（dd offset 跳转表）；这条直接编码了「线性扫描是在数据区失步的」
5. 前 8 条内有栈帧动作（push，或 sub/and esp,imm）
6. 前 8 条内有 this/栈参信号（出现 ecx，或 [esp+/-n]，或 ebp）

在 13 条上的命中数：**13/13**。

判别力（同一会话同一实现，随机种子固定）：

| 检验集 | W 命中率 |
|---|---|
| 13 条（主张为真入口） | 13/13 |
| 反控 13×(t+1, t+2, t+3)，n=39 | 0/39 |
| 随机 16 对齐且不在线性相位的地址，n=500 | 0.0180（假阳） |
| 随机线性相位起点，n=500 | 0.0060 |
| 随机 16 对齐且是相位起点，n=500 | 0.0900 |
| 真值集 DIRT∩ASET（已知直接调用落点），n=600 | 0.5383 |

最后一行要如实报告：W 在「已知为真的直接调用落点」上只有 53.8% 命中，说明 W 仍然**偏严**，只是对「13 条」这一批恰好全中。所以 W 的正确用法是「13 条全中 + 反控 0/39 + 假阳 1.8%」这一组对照，不能反过来宣称「W 通过的都是入口」。

补充：我另试过两个候选判据并主动否决，避免主会话复用错误判据。

- Q2（前 3 条均落线性相位 + 栈帧 + this 信号）：13 条 0/13，反控 0/39。线性相位一致性对「非相位」地址是循环论证（要求它在线性相位里），必须否决。
- R（重同步判据：detail 解码中途撞回线性相位）：13 条 5/13，反控 0/39，随机 16 对齐非相位假阳 0.1320。假阳性太高（0.59 的随机非相位地址都能在 2 条内重同步），否决。

---

## 六、独立复算的数字（>= 4 个，含偏差）

| 量 | 主张 | 我的独立值 | 偏差 | 备注 |
|---|---|---|---|---|
| A1 COL 记录 | 1214 | 1214 | 0 | 独立实现，未复用 m1 代码 |
| A3 槽位 | 14044 | 14044 | 0 | max depth 344，未触 401 上限 |
| A4 槽位去重目标 | 6692 | 6692 | 0 | 其中 6685 个 %16==0（99.90%） |
| A8 call 总/直接/间接/直接落 .text | 94786/68253/26533/68244 | 94786/68253/26533/68244 | 0/0/0/0 | 线性扫描共 1394120 条指令，66 次 p+=1 重定位 |
| A9 四分类 | 3832/18895/3797/9 | 3832/18897/3797/7（显式带符号解析） | 0/+2/0/−2 | 差 2 即负位移 [ebp-0x3c] 型 |
| A10 位移桶数 / 非 4 倍数 | 341 / 0 | 341（执行员口径）343（含负位移）/ 0 | 0 或 +2 / 0 | 排序错，首位是 disp=8:1713 |
| A11 直接去重目标/∩/仅虚/仅直接 | 6719/433/6259/6286 | 6719/433/6259/6286 | 0/0/0/0 | |
| A12 disp=132 / 72 | 85/22, 137/27 | 85/22, 137/27 | 0 | Spearman 0.909 |
| B2 到 ret 的条数 | 12/13 | 13/13 | +1 | 43fb20 需 1490 B（>1400） |
| B4 原判据命中 | 5/13 | 5/13 | 0 | 判据本身 FAIL |

---

## 七、可复算的最小命令

以下命令只读，不写任何文件；每条独立跑完即给出上表对应数值。

### 7.1 A1 / A3 / A4 / A5 / A6 / A7 / A8 / A11（一次到位）

cd /home/t628/projects/ra2-campaign-forge && python3 - <<'EOF'
import sys,struct,array,collections
sys.path.insert(0,'_r185'); import pe185 as P, capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
T=P.B['.text'];LO,HI,RP=T['lo'],T['hi_file'],T['rawptr'];RAW=P.RAW
def wv(sn):
    s=P.B[sn];n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,RAW,s['rawptr']),n
COL={}
for sn in ('.rdata','.data'):
    b,w,n=wv(sn)
    for i in range(n-4):
        if w[i]>2 or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'): COL[b+4*i]=1
VT={}
for sn in ('.rdata','.data'):
    b,w,n=wv(sn)
    for i in range(n):
        if LO<=w[i]<HI and P.dw(b+4*i-4) in COL: VT[b+4*i]=1
SLOT={};dep={}
for vt in VT:
    k=0
    while k<=400:
        t=P.dw(vt+4*k)
        if not(t is not None and LO<=t<HI): break
        SLOT[(vt,4*k)]=t;k+=1
    dep[vt]=k
TGT=set(SLOT.values())
print('A1',len(COL),'A2',len(VT),'A3',len(SLOT),'A4',len(TGT))
print('A5',sum(1 for (v,d) in SLOT if d and (v+d) in VT),'A6 min',min(dep.values()))
print('A7',collections.Counter(dep.values()).most_common(3))
BUF=RAW[RP:RP+(HI-LO)];p=0;starts=array.array('I');CALLS=[]
while p<len(BUF):
    g=False
    for o,s,m,op in md.disasm_lite(BUF[p:p+65536],LO+p):
        g=True;starts.append(o)
        if m=='call': CALLS.append((o,op))
        p+=s
    if not g: p+=1
ASET=set(starts);D=[(a,int(o,16)) for a,o in CALLS if o.startswith('0x')]
I=[(a,o) for a,o in CALLS if not o.startswith('0x')]
print('A8',len(CALLS),len(D),len(I),sum(1 for a,t in D if LO<=t<HI))
DIRT=set(t for a,t in D if LO<=t<HI)
print('A11',len(DIRT),len(TGT&DIRT),len(TGT-DIRT),len(DIRT-TGT))
print('C6/TGT 是否同一集合',TGT==(DIRT&ASET),len(DIRT&ASET))
EOF

### 7.2 A9 / A10（带符号的独立分类器，暴露负位移与 ptr [ecx] 问题）

cd /home/t628/projects/ra2-campaign-forge && python3 - <<'EOF'
import sys,re,collections
sys.path.insert(0,'_r185'); import pe185 as P, capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
T=P.B['.text'];LO,HI,RP=T['lo'],T['hi_file'],T['rawptr'];RAW=P.RAW
BUF=RAW[RP:RP+(HI-LO)];p=0;I=[]
while p<len(BUF):
    g=False
    for o,s,m,op in md.disasm_lite(BUF[p:p+65536],LO+p):
        g=True
        if m=='call' and not op.startswith('0x'): I.append((o,op))
        p+=s
    if not g: p+=1
N=r'(?:0x[0-9a-f]+|[0-9]+)';cl=collections.Counter();b=[]
for a,o in I:
    s=re.sub(r'^(dword ptr |word ptr |byte ptr |fword ptr |qword ptr )','',o)
    if re.match(r'^\[%s\]$'%N,s): cl['abs']+=1;continue
    m=re.match(r'^\[([a-z]{3})\]$',s)
    if m: cl['base0']+=1;b.append((a,m.group(1),0));continue
    m=re.match(r'^\[([a-z]{3}) ([+-]) (%s)\]$'%N,s)
    if m:
        d=int(m.group(3),16) if m.group(3).startswith('0x') else int(m.group(3))
        if m.group(2)=='-': d=-d;cl['neg']+=1
        else: cl['pos']+=1
        b.append((a,m.group(1),d));continue
    if re.match(r'^[a-z]{3}$',s): cl['reg']+=1;continue
    cl['other']+=1
print('间接总数',len(I),'分类',dict(cl))
disp=collections.Counter(d for _,_,d in b)
print('位移桶数',len(disp),'非4倍数',sum(1 for d in disp if d%4))
print('top8',disp.most_common(8))
EOF

### 7.3 A12 宽窄比与相关性（含「最窄其实是 72」的反证）

cd /home/t628/projects/ra2-campaign-forge && python3 - <<'EOF'
import sys,struct
sys.path.insert(0,'_r185'); import pe185 as P
T=P.B['.text'];LO,HI=T['lo'],T['hi_file'];RAW=P.RAW
def wv(sn):
    s=P.B[sn];n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,RAW,s['rawptr']),n
COL={}
for sn in ('.rdata','.data'):
    b,w,n=wv(sn)
    for i in range(n-4):
        if w[i]>2 or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'): COL[b+4*i]=1
VT={}
for sn in ('.rdata','.data'):
    b,w,n=wv(sn)
    for i in range(n):
        if LO<=w[i]<HI and P.dw(b+4*i-4) in COL: VT[b+4*i]=1
SLOT={}
for vt in VT:
    k=0
    while k<=400:
        t=P.dw(vt+4*k)
        if not(t is not None and LO<=t<HI): break
        SLOT[(vt,4*k)]=t;k+=1
rows=[]
for d in (0,4,8,0xc,0x10,0x14,0x18,0x20,0x2c,0x48,0x84):
    vs=[vt for vt in VT if (vt,d) in SLOT];tg=set(SLOT[(vt,d)] for vt in vs)
    rows.append((len(tg)/len(vs),d,len(vs),len(tg)))
for r,d,v,t in sorted(rows): print('disp=%-4d vts=%-5d tgts=%-4d ratio=%.3f share=%.1f'%(d,v,t,r,v/t))
EOF

### 7.4 B1 / B2 / B3 / B4（13 条的判定与 W 判据 + 反控）

cd /home/t628/projects/ra2-campaign-forge && python3 - <<'EOF'
import sys,struct,random,array
sys.path.insert(0,'_r185'); import pe185 as P, capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
T=P.B['.text'];LO,HI,RP=T['lo'],T['hi_file'],T['rawptr'];RAW=P.RAW
def by(va,n): o=RP+va-LO; return RAW[o:o+n]
M=[0x4155f0,0x4176f0,0x417bd0,0x417c80,0x41bb30,0x41bbd0,0x43fb20,0x453840,
   0x4c49a0,0x4d82b0,0x51d0d0,0x6eae60,0x729e50]
def dec(va,cap=8192,mx=900):
    out=[]
    for i in md.disasm(by(va,min(cap,HI-va)),va):
        out.append((i.address,i.size,i.mnemonic,i.op_str.replace(' ','')))
        if i.mnemonic.startswith('ret') or i.mnemonic=='int3' or len(out)>=mx: break
    return out
def frun(t,n=32):
    b=by(t-n,n);best=run=1
    for i in range(1,n):
        run=run+1 if b[i]==b[i-1] else 1;best=max(best,run)
    return best
def trun(t,n=48):
    w=struct.unpack_from('<%dI'%(n//4),RAW,RP+t-LO-n);best=run=0
    for x in w:
        run=run+1 if LO<=x<HI else 0;best=max(best,run)
    return best
BAD=('ret','int3','nop','hlt','ud2','leave','jmp','call')
def W(va):
    if va%16 or not(LO<=va<HI-64): return False
    s=dec(va)
    if len(s)<6: return False
    if s[0][2] in BAD or s[0][2].startswith('j') or s[0][2].startswith('ret'): return False
    if not (s[-1][2].startswith('ret') or s[-1][2]=='int3'): return False
    if not (frun(va)>=4 or trun(va)>=3): return False
    h=s[:8]
    if not any(x[2]=='push' or (x[2] in ('sub','and') and x[3].startswith('esp,')) for x in h): return False
    if not any(('ecx' in x[3])or('[esp+' in x[3])or('[esp-' in x[3])or('ebp' in x[3]) for x in h): return False
    return True
for t in M:
    s=dec(t); print('%x len=%-5d ninsn=%-4d brk=%s W=%s W=%s'%(
        t,sum(x[1] for x in s),len(s),s[-1][2].startswith('ret') or s[-1][2]=='int3',W(t),W(t)))
print('W 13 条 = %d/13'%sum(1 for t in M if W(t)))
print('W 反控 t+{1,2,3} = %d/39'%sum(1 for t in M for o in (1,2,3) if W(t+o)))
BUF=RAW[RP:RP+(HI-LO)];p=0;starts=array.array('I')
while p<len(BUF):
    g=False
    for o,s2,m,op in md.disasm_lite(BUF[p:p+65536],LO+p): g=True;starts.append(o);p+=s2
    if not g: p+=1
ASET=set(starts);b16=LO+((16-LO%16)%16);all16=list(range(b16,HI,16))
cand=[a for a in all16 if a not in ASET]
random.seed(9)
print('W 假阳(随机16对齐非相位,n=500) = %.4f'%(sum(1 for a in random.sample(cand,500) if W(a))/500))
print('线性相位起点 13 条是否全在 ASET =',[t in ASET for t in M])
EOF

上述四条命令在本次审计会话中原样执行，回显（rc=0）与正文数值一致：

- 7.1：A1 1214 / A2 1214 / A3 14044 / A4 6692 / A5 0 / A6 min 1 / A7 [(7,412),(1,199),(5,160)] / A8 94786 68253 26533 68244 / A11 6719 433 6259 6286 / TGT==(DIRT∩ASET) False（6692）
- 7.2：间接总数 26533，分类 {pos 18078, abs 3832, reg 3797, base0 817, neg 2, other 7}；位移桶 343，非 4 倍数 0，top8 首位 disp=8:1713
- 7.3：disp=72 ratio 0.197（最窄）、disp=132 ratio 0.259
- 7.4：13 条全部 brk=True、W=True；W 13/13，反控 0/39，假阳 0.0180

---

## 八、给主会话的处置建议（不越权，仅建议）

1. A5、A6 必须从「证据」降级为「构造说明」，并从 asserts 计数里剔除——它们占了 m1 25 条断言中的 2 条却是零信息量。
2. C7 的 if '0x84' in HOTB else 必须改成严格比较；它是 A12 目前唯一的执行侧支撑。
3. A10 的排序表述与 m1_dispatch.py:106 的 339 常量必须改；B4 的名字应让位给 W 判据，否则「339/341」这类腐烂会继续产生。
4. B4 的替代判据建议直接采用 W（13/13，反控 0/39，假阳 1.8%），但不得反向宣称「W 通过即入口」（对已知真入口只有 53.8% 命中）。
5. 「6692」这个数字必须分裂成两个符号（槽位去重目标 / 直接调用落指令起点），二者差 6260 条。
