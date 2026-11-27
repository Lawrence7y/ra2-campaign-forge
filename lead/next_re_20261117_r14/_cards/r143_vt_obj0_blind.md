# R143 执行卡：独立复算「对象偏移 0 处的 dword 是 vptr」这条对象模型判读的字节证据（盲测）

## 背景
仓库 /home/t628/projects/ra2-campaign-forge。目标二进制 ra2bench/gamemd.exe（4,825,360 B，sha256 73201cc0…）。
历史上有一条判读写着 vt == [esi]（对象偏移 0 处的 dword 就是虚表指针），一直标为「未独立证、只证到 edx==[esi]」。
本卡要你自写脚本，用字节把这条判读拆成三条可失败判据并各自复算。**禁止**读取或运行 _r143/r143a_metric.py、_r143/r143b_model.py、_r143/r143c_model.py（被审计对象）。

## 判定口径（必须照此实现，不许改）
### 0. 地址换算
用 pefile 读节表（fast_load=True），ImageBase=0x400000。文件偏移 = PointerToRawData + (VA - ImageBase - 节.VirtualAddress)，只在该节 SizeOfRawData 内有效；越界返回 None（视为不落盘）。

### 1. 虚表地址集合 VTS
1a 在 .data 与 .rdata 两节内用正则 \.\?A[VU][!-~]{1,200}?@@ 找装饰名串，记串起点 S。
1b 一个 TD 合法当：dword[S-8] 非 None 且 dword[S-4]==0 且 dword[S-8] 落在 .data 或 .rdata 内。TD 集合的元素是 S-8。
1c 在 .data/.rdata 内逐个 4 字节对齐扫描，若 dword 值 v 属于 TD 集合，则候选 COL = 该 dword 地址 - 12，要求 dword[COL]==0 且 dword[COL+12]==v 且 dword[COL+16]!=0。
1d 在 .data/.rdata 内逐个 4 字节对齐扫描，若 dword 值 v 属于 COL 集合，则 vt = 该 dword 地址 + 4，要求 dword[vt-4]==v。所有这样的 vt 去重即 VTS。
报出：TD 个数、COL 个数、VTS 的 distinct 个数。

### 2. .text 线性扫描
用 capstone 5.x CS_ARCH_X86/CS_MODE_32 的 disasm_lite（不要用 detail=True 扫全段，会 OOM），按 64KB 分块，块基址 = ImageBase + 节.VirtualAddress + (块文件偏移 - PointerToRawData)。跨块的尾指令不消费，下一块从它的地址重新开始。把 op_str 里的空白归一化：把逗号/加号/星号两侧空白全部删掉。报出全段解出的指令条数。

### 3. C1 写入侧判据
匹配 op_str 形如  dword ptr [X]  或  dword ptr [X+0xN]  或  dword ptr [X-0xN]  再跟 ,立即数 的 mov（立即数为 0x… 或十进制）。
按 X 是否属于 {eax,ebx,ecx,edx,esi,edi} 分成两类：
  (a) 寄存器基址（对象字段写），记 (站点VA, 基址寄存器, 位移, 立即数)；
  (b) 绝对地址基址（形如 dword ptr [0x87f5d8]，全局写），单独计数，不进 (a)。
对 (a) 里立即数属于 VTS 的：报站点数、位移==0 的站点数、位移!=0 的站点数、位移==0 覆盖的 distinct vt 个数、该覆盖数除以 VTS 总数、（位移!=0）覆盖的 distinct vt 个数、位移直方图前 8 项。

### 4. C2 读取侧判据
匹配 op_str 形如 dword ptr [X] / [X+0xN] / [X-0xN] 的 call 或 jmp，且 X 属于 {eax,ebx,ecx,edx,esi,edi}：这是虚派发点。总数据此计数。
对每个派发点，回溯该基址寄存器在本函数内的「最近一次定义」，用一遍流式扫描维护状态机：
  - 遇到 mov 目的为通用寄存器且源形如 dword ptr [Y+d] → 记 (kind=load, 装载基址 Y, 位移 d, 装载VA)
  - 遇到 mov 目的为通用寄存器且源不是内存 → kind=other
  - 遇到 lea 目的为通用寄存器 → kind=other
  - 遇到 pop 到通用寄存器 → kind=other
  - 遇到 add/sub/adc/sbb/and/or/xor/inc/dec/neg/not/shl/shr/sar/sal/rol/ror/imul/xchg/bswap/mul/div/idiv 且第一操作数是通用寄存器 → kind=other
  - 遇到 call 之后把 eax/ecx/edx 记为 kind=clobber（被调用者破坏）
  - 未见过任何定义 → kind=unknown
报出派发点总数与 kind 直方图。
再对 kind==load 的那些，把装载的基址 Y 分成两类：
  - 栈类：Y 是 esp 或 ebp
  - 对象类：Y 属于 {eax,ebx,ecx,edx,esi,edi}
分别在两类内部报「装载位移==0」的计数与占比，以及这两类的各自总数。

### 5. C3 控制判据
5a 全部内存装载（mov 目的为通用寄存器、源为 dword ptr [Y+d]，Y 任意）的总条数与其中位移==0 的条数与占比，作为无条件下限基线。
5b 富集倍数 = C2 里对象类装载位移==0 的占比 除以 5a 的占比。
5c 把「位移==0」换成位移==4、==8、==0xc、==0x10，各报对象类计数（应当显著低于 0 位）。
5d 伪虚表集合反控：用 random.seed(143) 在 .data/.rdata 的全部 4 字节对齐 dword 值里抽样，样本量等于 VTS 的 distinct 个数，用这个伪集合重算 C1 的「位移==0 的站点数」与「distinct 覆盖数」（应当显著塌下来）。
5e 独立解码器反控：读 _r140/obj_starts.txt（每行一个十六进制地址，是 objdump 线性扫描得到的 .text 指令起点集），报派发点里落在该集合的比例；并报基线 = 集合大小 / .text 的 SizeOfRawData。两者对比要有量级差。

### 6. 定点字节旁证（必须原样抄出，不许只用反汇编器）
用 i686-w64-mingw32-objdump 对 0x47C420..0x47C450 这 0x30 字节单独解码（先按文件偏移切出字节写成临时 .bin，用 -D -b binary -m i386 --adjust-vma 指定基址），逐条抄出 0x47C437 与 0x47C440 两条指令的助记符与机器码字节。再报这两条在 capstone 下的解码结果，两者必须一致。

## 输出
- 一条命令跑完（脚本自己写，放 _r143/sub/ 下，文件名 sub_verify.py），把结果打成 JSON 同时写 _r143/sub/sub_result.json。
- 结尾附 SELF-CHECK 一节，逐项列出你算出的每个数字。
- 不修改任何既有文件；不读上述三个被审计脚本。
- 卡面与产出里都不要出现反引号字符。
