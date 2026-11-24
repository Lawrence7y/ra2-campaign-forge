# W173 · LayerClass::Add 调用点穷举 + [obj+0x94] 层号写点

> 卡号 W173｜2026-11-17｜目标 gamemd.exe SHA256 73201CC0…F67476（已核对）
> 依据 R13_COMMON §4.2/§6/§7；R14_COMMON.md 不存在。工具 capstone 5.0.7 skipdata=True
> （.text 1,394,120 指令 / 66 skipped bytes），归属用函数区间包含；所有脚本在 work/。

## 结论表

| # | 结论 | 级别 | 证据 |
|---|---|---|---|
| 1 | 全 .text `call dword [reg+0x1C]` 共 **142** 站点 / 85 函数（atlas 区间包含）；其中 141 为真正虚表式（base=对象寄存器）、1 处为 `0x733FBE call [esp+0x1C]`（SIB栈槽 ff54241c，非虚派发） | [已证] | EVIDENCE/w173_chA_detail.txt；w173_verify.txt [4]；w173_selfaudit.txt |
| 2 | **142 站中 this∈[0x8A0360,0x8A03D8)（LayerClass）的站点 = 0**：无任何站前 40 条含层数组常量；vptr 来源全是 `mov reg,[对象]`，对象是普通 ObjectClass 派生（ecx=this，追至各对象 vftable） | [已证] | w173_verify.txt [4]/[5]；w173_chA_detail.txt；w173_chain_check.txt |
| 3 | LayerClass 虚表 0x7E6060（RTTI `.?AVLayerClass@@`）slot+0x1C=0x5519B0 仅此一处；**0x7E6060 作为立即数在 .text 只出现 1 次**（0x4A8660 构造函数写 vptr），故无任何代码能把该 vptr 装入寄存器做 `[reg+0x1C]` 虚派发 | [已证] | w173_verify.txt [1]；w173_chain_check.txt [a]；w173_rtti_probe.txt |
| 4 | 0x5519B0（VectorClass\<T\>::Add，ecx=this、栈参(item,only_check)、ret 8）**直接调用者恰 2**：0x4A9759（fn 0x4A9720）、0x55BABB（fn 0x55BAA0）——与台账 §928-5 一致 | [已证] | w173_verify.txt [2]；w173_conv_detail.txt |
| 5 | 通道 B（不依赖 atlas 发现）：对 `0x8A0360+k*0x18`(k=0..4) 精确基址的立即数/位移引用 **7 站点 / 6 函数**；含字段偏移的范围引用共 56 站点 / 17 函数。站点归属 atlas 与 synth 双判、边界校验全 True（atlas 空洞 0x4824D4 段由 synth 归属） | [已证] | w173_chB_detail.txt；w173_summary.txt；w173_verify.txt [5] |
| 6 | A∩B 交集 = **0**（函数级与站点级均 0）。B 的 17 个层数组函数中 `call[+0x1C]` 数全为 0；A 的 142 站所在函数无一引用层数组常量 | [已证] | w173_summary.txt；w173_verify.txt [5] |
| 7 | 调用链上下各一层补验（纪律12）：层号来源函数 0x55D360 调 0x473B10/0x48D080/0x55DEE0（含 `call[+0x1C]`），但这三个的 ecx 是**层[2]的元素 ObjectClass\***（排序比较器），不是 LayerClass 对象；`this` 不在层数组范围 | [已证] | w173_chain_check.txt [b][c]；w173_chA_detail.txt SITE 00473B26 |
| 8 | 全镜像 `mov [basereg+0x94],src`：原始 **172**（全宽度）/ **161** dword；dword 中 base=esp/ebp 栈槽 **116**（非对象字段）、base=对象寄存器 **45**。对象字段 45 按值：立即数 -1=**3**、L0..L4=**1**（仅 L0@0x54B76C）、寄存器=**41** | [已证] | w173_w94_precise.txt；w173_w94_byfunc.txt |
| 9 | 唯一立即数层号写 0x54B76C：fn 0x54B750 先 call 0x55AAC0，成功置 `[esi+0x94]=0` 且 vft=0x7ECE34（GetLayer 返回 0）⇒ 层 0 对象初始化 | [静态推断] | w173_fn54B750.txt；w173_getlayer_detail.txt |
| 10 | SetLayer(0x4A9720) 层号来自 `call [vptr+0x78]`；逐字符核对 GetLayer：ObjectClass/TechnoClass/BuildingClass/AnimClass 等默认返回 **2**（0x5F4260 `mov eax,2`）；BuildingLight/Particle/VoxelAnim/Wave 返回 **3**（`mov eax,3`）；RadSite 返回 **1**（`mov al,1`）；Neuron 返回 **0**。层4 未发现任何 GetLayer 返回 | [静态推断] | w173_getlayer_detail.txt；w173_layer_class.txt |
| 11 | 层号 0..4 ↔ 对象类别见下表；层 4 对象类别 [未证]（0 个 GetLayer 返回 4，且无立即数写 4） | 混合 | w173_layer_class.txt；w173_w94_precise.txt |

## 层号 ↔ 对象类别对照（SetLayer 的 [vptr+0x78]=GetLayer 返回值为准）

| 层 | 对象类别/场景 | 级别 | 证据 |
|---|---|---|---|
| 0 | vft=0x7ECE34 的初始化对象（0x54B750）；NeuronClass | [静态推断] | w173_fn54B750.txt；w173_getlayer_detail.txt |
| 1 | RadSiteClass（辐射站点）；MovieHandle | [静态推断] | w173_getlayer_detail.txt |
| 2 | 默认层：ObjectClass/TechnoClass/BuildingClass/AnimClass/Overlay/Terrain/Smudge/Radio 等（0x5F4260 返回 2） | [已证] | w173_getlayer_detail.txt |
| 3 | BuildingLightClass / ParticleClass / VoxelAnimClass / WaveClass | [已证] | w173_getlayer_detail.txt |
| 4 | 无 GetLayer 返回 4、无立即数写 4 ⇒ **未证** | [未证] | w173_layer_class.txt；w173_w94_precise.txt |

## 给审计员的核心数字（3 个）

1. **chA `call[reg+0x1C]`=142，chB 精确基址引用=7（范围=56），A∩B=0**。复算：`work/w173_scan.py`（两通道）+ `work/w173_verify.py` §[5]；A 通道数=disasm 全 .text 中 `mnemonic=='call' and op0.mem.disp==0x1C and base!=None`；B 通道数=操作数 imm/disp ∈ {0x8A0360,378,390,3A8,3C0}（精确）或 ∈[0x8A0360,0x8A03D8]（范围）；归属用区间包含。
2. **0x7E6060 在 .text 立即数出现次数=1（0x4A8660）**；0x5519B0 全镜像 dword 出现=1（虚表槽）、直接 call 站点=2。复算：`work/w173_chain_check.py` [a] + `work/w173_verify.py` [1][2]。这是"无虚派发 Add"的独立性证据（不依赖 atlas）。
3. **`mov [reg+0x94]` 写点：原始 172 / dword 161 / 对象字段 dword 45（值:-1=3, L0=1, reg=41）/ 栈槽 dword 116**。复算：`work/w173_w94_precise.py`；过滤 `mn=='mov' and op0.mem.disp==0x94`；按 `op0.size==4` 取 dword；base∈{esp,ebp} 归栈槽，其余归对象字段。
