# SEMFIX-REST · 给 **48 行 `[已证]`** 补写语义栏（**只改语义，不动 grade**）

> ⚠️ **本卡不升不降任何 grade。** 这 48 行的 grade **已经过 `AUDIT-SEM-SELF` 判为 P1（③b 成立）**，
> 但它们盘上的语义栏仍是旧模板语（「槽语义未证」/「线索/弱信号」）⇒ **行内自相矛盾**。本卡的任务是把语义写对。

## 依据
`AUDIT-SEM-SELF`（DeepSeek v4.1-flash high，只读测量）对全表 95 行「`[已证]` 但语义自陈未证」逐行独立反汇编，判 **P1=73 / P2=22**。
它在 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\ROW_VERDICTS.tsv` 的 **`criterion` 列**里为每个 P1 行写了**具体字节证据**（跳表地址 / 回边 / 哨兵写点 / vt 写点）。
⇒ **本卡就是把这些 `criterion` 转写成人类可读的 ③ 合同。**

## 工作面（48 行，**全部已给 P1 判据**）
- `0040F0A0`（S20）：`完整复制循环 0x40F0EE..0x40F0FC（读 [edx+eax*4-4]→写 [edi+eax*4-4]→inc eax→cmp/jl 回边），伴 0x7C8E17 分配、0x7C8B3D 释放、字段 +4/+`
- `0040F150`（S20）：`查找循环 0x40F163..0x40F16D（cmp [ecx],esi → inc eax/add ecx,4/cmp/jl）+ 未命中 or eax,-1(0x40F16F) 可证伪返回约定；§8.4 slot4=`
- `00417FE0`（S05）：`跳表：0x417FF9 cmp eax,0xa + 0x417FFC ja 0x418D1D(越界守卫) + 0x417FFF jmp dword[eax*4+0x418D58]，表 10 槽目标全落 .text`
- `0041A5C0`（S05）：`多路守卫链 + 15 次调用 + RNG 尾；[+0x6C4]虚调与 vt[+0x1c8] 比较决定分支，结局互斥`
- `0041FB10`（S14）：`[+0xA0] 三路分派(dec/je/dec/jne，值 1/2/其它)选 owner 指针；[+0xA8] 带 cmp -1 索引 0xA83C9C`
- `0044ACF0`（S12）：`跳表 0x44B728 共 11 槽、cmp bound=0xA，各目标落 .text 可逐路核`
- `00473BA0`（S03）：`三路原点分派：sub eax,0/je(origin=0)、sub eax,2/jne(origin=2) 选基址 [+0x5C] 或 0；随后溢出钳位 sets dl/dec edx/and 与 cmp/jle 封顶 `
- `00473C50`（S03）：`Open 四级尝试阶梯(vt[+0x18]→vt[+4]+0x5B4430→0x431F10)，状态 enum [+0x68] 记 0/1/2，返回 al=1 当且仅当某级成功 ⇒ 可证伪`
- `00473D10`（S03）：`123 指令、7 jcc、9 调用；test byte[esp+0x20],2 标志分流 + 初始化阶梯 + 多 vt 派发，结局互斥`
- `0047EFE0`（S08）：`4 个严格循环(首 head=0x47F1B1 span=17，读5/写2/cmp)，S08`
- `0047F250`（S08）：`4 个严格循环(首 head=0x47F403 span=29，读7/写2/cmp)，S08`
- `0047FF80`（S06）：`无效哨兵 0xFFFF 闸：cmp eax,0xFFFF/jne(0x480022) → 直接写 4 dword 矩形返回；否则 test eax,eax/jl 与 cmp [0xA8ED38]/jge 双重越界闸后索引`
- `004801F0`（S07）：`状态码映射：call 0x6D8700 结果 → cmp -2 则取 0xF(0x480215)、cmp -1 则取 0(0x480221)，否则原值 ⇒ -2/-1/其它 三态可证伪；结果存 [+0x120]/[+0x`
- `004A9890`（S07）：`3 个严格循环(首 head=0x4A9A3C span=30，读11/写4/cmp)；DisplayClass slot36`
- `004AFD40`（S11）：`四个虚谓词闸(vt+0x37C/+0x380/+0x1D4/+0x1D8 @0x4AFD4B/0x4AFD5E/0x4AFD71/0x4AFD80)全同早退，随后目标向量 [+0x30..0x38] 写入并与 0x8A0`
- `004B0500`（S11）：`5 个严格循环(如 head=0x4B078C span=116，读 47/写 4/cmp)，DriveLocomotionClass slot16`
- `004F4410`（S09）：`三路：vt[+0x2C] 为真→返 0；全局 0xA8EF54 非空→vt[+0x10] 并返 1；否则写全局=esi 返 1(单例登记)`
- `004F54A0`（S14）：`严格循环 head=0x4F5C0D span=7 + 24 处 vt 写 + 66 调用 + err -1 x3；1023 指令`
- `00508F60`（S06）：`计数循环 [+0x78]/数组 [+0x6C]，每元素 6 个互斥过滤闸(byte[+0x16A5]/[+0x81]/[+0x74]/0xA8B238/[+0x1EC]/[+0x1ED])`
- `005113F0`（S04）：`构造器显式布局 ~30 字段：+0xB4/+0xB8/+0xBC 置 -1(0x511401 or eax,-1)、+0x98/+0xC0.. 置 0、成组 1.0 double 高字 0x3FF00000、1.0f 0`
- `00517A50`（S18）：`严格循环 head=0x517C36 span=10 + 4 张 vt 写 + err -1`
- `0052CB90`（S21）：`严格循环 head=0x52CBBF span=71(读15/写15/cmp)`
- `0052CD70`（S04）：`严格循环 head=0x52CDBD span=109(读30/写10/cmp)；443 指令 49 调用`
- `0053C6A0`（S20）：`复制循环 head=0x53C6EE span=6；DV<AnimClass*> slot2 SetCapacity`
- `005514B0`（S20）：`复制循环 head=0x5514FE span=6；DV<LaserDrawClass*> slot2 SetCapacity`
- `00551560`（S20）：`查找循环 + 未命中 or eax,-1；DV<LaserDrawClass*> slot4 FindItemIndex`
- `00555DA0`（S07）：`哨兵映射：cmp edi,-1 → 三字段同置 0x3E8(0x555F14)，否则写 edi/ebp/ebx 三元组；另有 3 个谓词调用与除法常量序列`
- `00557090`（S20）：`复制循环 head=0x5570DE span=6；DV<LineTrail*> slot2 SetCapacity`
- `00557140`（S20）：`查找循环 + 未命中 or eax,-1；DV<LineTrail*> slot4 FindItemIndex`
- `005656D0`（S09）：`越界哨兵链：idx=(Y<<9)+X 后 js(0x5656EF) 与 cmp 0x40000/jge(0x5656F1) 双越界闸 → 回落 0xABDC50 并写 0xABDC74(与 §8.2⑤ 同族)；返回 (c`
- `00565800`（S06）：`3 个严格循环(head=0x56588B span=10 等)；MapClass slot5`
- `005B3C20`（S03）：`构造器显式布局：14+ 字段清零(+4..+0x24)、vt 0x7EDF50@0x5B3C52、标志字节 +0x10/+0x11/+0x12，随后 [0x7E4C30] 指针调用与 0x6BEC60/0x6BEC50 `
- `005B4630`（S03）：`析构器所有权形状：vt 0x7EDF50 写、[+0xC] 无条件 free(0x7C93E8/0x7C8B3D)、[+0x24] 仅当 byte[+0x12] 才 free 并清标志、[+0x20] free 并清 0`
- `005F3900`（S05）：`构造器显式布局 ~25 字段：成组 0、0xFF(255)、1、-1 默认值，含 +0x6C/+0x70=0xFF、+0x64=-1、多字节标志位 ⇒ 内存形状断言`
- `005FC380`（S06）：`多继承 vt 形状：0x7EF3D4@[esi]、0x7EF3B0@[esi+4]、0x7EF3CC@[esi+8]、0x7EF3A8@[esi+0xC] + 全局初始化块(0xA8EC58/60/5D/64)`
- `0062B5E0`（S06）：`多路：RNG 0x65C780 + 依 [+0x314]==1/==4 三条互斥分支(0x62B7E5/0x62B834/0x62B865)，含 idiv 10 取模与浮点累加 [+0xE4]`
- `0062DC50`（S12）：`双 vt 构造：基类 0x5F3900 + 嵌入子对象 vt 0x7E9D64 写于 [esi+0xBC](0x62DC95)，字段 +0xAC/+0xB0..+0xB8 与三元组(0xAC4A58/5C/60)初始化`
- `0064DAB0`（S18）：`6 个严格循环(首 head=0x64DACE span=41，读12/写2/cmp)；帧 CRC 六集合累加`
- `00653100`（S09）：`跳表 0x653734 共 4 槽 bound=3 + 41 jcc + 15 调用；RadarClass slot16`
- `00655C50`（S06）：`严格循环 head=0x655DC0 span=53(读22/写1/cmp)；380 指令 38 jcc`
- `00656EC0`（S06）：`4 个严格循环(首 head=0x657228 span=32，读13/写4/cmp)；784 指令 65 jcc`
- `0065CBF0`（S03）：`多出口可证伪：+0x18==0 → 早退 al=0；vt[+0x18] 为真 → 走 0x65CC94；arg 非零则 0x65CB50(1) 后重查 vt[+0x18] 再经 [0x7E11E0] ⇒ 成功/失败路径互`
- `006A4550`（S04）：`多继承 vt 形状：0x7F2EC0@[esi]、0x7F2EA4@[esi+4]、0x7F2E9C@[esi+8]、0x7F2E94@[esi+0xC]、0x7E4DD8@[esi+0x98]，伴 7 字段初始化(0x`
- `006BB9A0`（S01）：`3 个严格循环(首 head=0x6BBEEF span=47，读9/写4/cmp)；1742 指令 261 调用(注:触及 6000B extent 上限，见 UNKNOWNS)`
- `006F0AB0`（S14）：`3 个严格循环(首 head=0x6F0B34 span=11) + 9 处 vt 写 + 66 jcc`
- `006F9E50`（S05）：`2 个严格循环(head=0x6FA353 span=15)；1348 指令 207 jcc 73 调用；TechnoClass slot23`
- `0075ACB0`（S11）：`三虚谓词闸(vt+0x37C/+0x1D4/+0x1D8)+目标向量 [+0x18..0x20] 写入并与 0xB45BE8/EC/F0 比较；WalkLocomotionClass slot17`
- `007DCFC4`（S02）：`2 个严格循环(head=0x7DCFE6 span=10，读2/写1/cmp) + 3 处 push imm(分配)`

## 每行的新语义栏必须包含（缺一不可）
1. **一句话总述**：这个函数整体做什么（不是「某类虚表槽 N」这种占位描述）。
2. **关键判据**：D-42 ③b 的四个充分条件它占哪一条，并给**指令偏移**（如 `0x417FF9 cmp eax,0xa` / `0x64DACE 回边 head`）。
3. **D-42 的四个充分条件**（`R14_COMMON §8.6`）：
   ① 跳表/switch 多路分支且每路可核；② 可证伪的错误码/返回约定；③ 内存形状断言（成员 ctor 数 + vt + 对象大小）；④ 完整循环 I/O（读→判→写→推进）。

## ⛔ 严禁
- **禁止改 grade**（既不升也不降）；**禁止改名**；**禁止改 subsystem**。本卡**只改第 4 列（one_line_semantics）**。
- **禁止把 `criterion` 原样抄进语义栏** —— 要转写成「人能读懂的功能描述 + 关键偏移」，不是贴证据流水。
- **禁止**让新语义再出现「槽语义未证」「弱信号」「线索」「未定」等字样。

## 强制自证
- **⑨ 停机核验**：这 48 行在盘上都应是 `[已证]`；自己核对（不符即停下报告）。
- **⑮ 体内出现**：你在语义里引用的每个地址/偏移，**必须在体内真出现**（不能只抄 `criterion`）。抽样复核 ≥5 行。
- **⑲**：capstone 5.0.7 无 `op.index`（`op.mem.index`，无 index 返 **0 非 None**）。

## 交付
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_REST\`
`PROGRESS.md`（≤40 行，第一行写「补写几行」）/ `EVIDENCE\` / `work\`
`coverage_delta.tsv`：8 列 `entry, subsystem, name, one_line_semantics, grade, evidence_path, name_kind, 旧grade→新grade`
  （⚠️ **grade 列必须与盘上完全相同**，即 `[已证]`→`[已证]`；name 也必须与盘上逐字相同）
**开工 10 分钟内先落骨架；每完成 5 行增量落盘。严禁建 venv / pip install。**

## 核心数字
① 补写行数（目标 48）② 每行新语义的字符数（应 ≥80）③ 抽样复核的 ⑤ 体内命中率 ④ grade/name 零变更自证