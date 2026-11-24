# UNKNOWNS.md — P0-GATE-C 未闭环项
> 只写未闭环；已闭环项见 PROGRESS.md / BIT0_ZERO11.md / FINAL_PATH.txt。

## U1. arg1 [esp+0x1c] 未定论
- **为什么未闭环**：gate 0x47C620 是 thiscall + 3 栈参（ret 0xC）；entry 后 `[esp+0x1c]`=arg1（调用者最后一个 push）。全函数内 arg1 只在 **0x47C9CD `mov ecx,[esp+0x1c]`** 出现，位于 `[0xA8ED6B]!=0 → 0x47C878 → 0x47C88D` 分支尾段；实测输入 [0xA8ED6B]=0 不走该支，故本卡路径未触达 arg1 的使用点。
- **观测到的 [esp+0x1c] 取值集合**（10 个直接 E8 调用点，EVIDENCE/p8_arg1vals.txt）：栈局部地址 `lea [esp+0x1c]` / `lea [esp+0x20]`（out-param 形态）、对象域指针 `[reg+0x67C]`（BuildingTypeClass* 域）、小整数 1 / 5、NULL(ebp=0)。无单一语义。
- **缺什么**：0x47C9xx–0x47CAxx 尾段逐指令打完（discipline #2：输出截断≠不存在）+ 0x5657A0 返回对象的类 RTTI（COL+0xC→TD+8，读不到 fail-closed）+ 运行时 arg1 实值。缺任一项不得给 arg1 定语义。

## U2. 0xE58 的 8 个非 INI 写点语义是否已定
写点来源（EVIDENCE/t1_values_and_e58.txt）：
1. 0x465210 `mov [esi+0xE58],ebx` — fn 0x465010，slot 0x7E4584→`.?AVBuildingTypeClass@@`；ctor/加载后置 0（ebx=0 于该路径）。**语义：BuildingTypeClass::WallType/闸关联类型初始化，[静态推断]（未追 ebx 全写入点）。**
2. 0x465531 `mov [esi+0xE58],eax` — fn 0x465450，eax=`[0xA8ED2C + idx*4]`（全局类型表查表）。**语义：INI 加载的 gate 类型表回写，[静态推断]。**
3. 0x465D18 `mov [esi+0xE58],edx` — fn 0x465CC0，edx=`[0xA8ED2C + idx*4]`。**语义：同上分支（另一加载路径），[静态推断]。**
4. 0x523AF8 `mov [esi+0xE58],ebx` — fn 0x5239D0，ebx=0，伴 `[esi+0xE54]=0, [esi+0xE5D]=0` 后 `call 0x711ae0`。**语义：析构/清除 BuildingTypeClass 扩展字段，[静态推断]。**
5. 0x524E98 `mov [esi+0xE58],ebx` — fn 0x524D70，slot 0x7EB630→`.?AVInfantryTypeClass@@`，同一清除模板。**语义：InfantryTypeClass 析构清除，[静态推断]。**
6. 0x7471A5 `mov [esi+0xE58],ebx` — fn 0x7470D0，RTTI fail-closed；批量字段置位后写 0。**语义：某 TypeClass 构造默认 0，[未证]。**
7. 0x747BC4 `mov [esi+0xE58],eax` — fn 0x747620，slot 0x7F627C→`.?AVUnitTypeClass@@`，eax 来自 `call 0x5B40B0` 返回值。**语义：UnitTypeClass 初始化/加载，[静态推断]。**
8. 0x748098 `mov [esi+0xE58],eax` — fn 0x74800A，eax=`[esi+0xE58]` 读出后经过 0x7C9FF0/0x5B40B0 再写回（**读改写**）。**语义：+0xE58 作为输入参与解析后回写，[未证]。**
- **缺什么**：#6/#8 的 RTTI（fail-closed）+ 每点 value 的完整上游 def-use；未做 ⇒ 8 点均不能给 [已证] 语义。注意：本卡路径只需要「四标志全 0」这一**实测取值**，不依赖 8 点语义定名。

## U3. 11 处 bit0=0 写点的卡面用词与字面值不符
- 卡面/前稿称「直接写 0 共 11 处」。逐字节核对（EVIDENCE/p6_verify.txt）：11 处 = `c6 ?? 14 IMM`，IMM 依次为 00,00,00,02,00,00,42,62,48,70,64。**仅 5 处 imm=0，6 处非零但 bit0=0。**
- 分类已按「bit0=0 集合」全 11 处做完（BIT0_ZERO11.md），结论不受影响；但卡面用词应改「bit0=0 直接写点 11（其中字面 0 仅 5）」。

## U4. register-derived bit0 写点未逐一追值
- 51 个非 ESP byte 写点中：imm bit0=0 11（已分类）、imm bit0=1 14、**register/mem 值 26**（t3_u3_bit0_counts.txt）。
- 构造链上已知：0x4D34E0 `or dl,4`、0x5F3B39 `or al,2` 保 bit0；0x6F322F `or al,1` 置 bit0；0x4101B3 `and cl,0xF8` 清 bit0 但**在 0x6F322F 之前**（链序 5F3900→410170 先于 6F2B40 的写回），故构造出口 bit0=1。
- **缺什么**：其余 register-derived 写点的完整 def-use + 运行时可达性；因此「bit0 恒 1」仅在**工厂构造路径**上 [已证]，全域恒 1 推断保留。

## U5. gate this（ecx）类名未定
- 0x47C620 无 vtable slot（EVIDENCE/p6_verify.txt 空），RTTI fail-closed；arg2 = `.?AVBuildingTypeClass@@` 已证（COL 0x7FC618→TD 0x8193A8→TD+8），this 仅能由调用者 `mov ecx,eax@0x5657A0` / `mov ecx,[reg+0x67C]` 间接推断为 BuildingClass 族，**未证**。

## U6. 真机观测必要性
- 本卡字节级结论（路径条件、bit0 构造恒 1、写读计数、23W/100R）可独立复算；但「引擎是否允许建筑与步兵同格」总判断受 U1/U2/U4 限制 = **[静态推断]**。
- ⇒ **仍需要真机观测**；D-36 请裁的硬件断点（对 [infantry+0x14] 写 0 / 对 0x47C738 命中）不应撤销。

## U7. bit0 写点 #1 (0x4CCA64) 的 ebx 精确类未定（分类为结构推断）
- 0x4CCA20 所属 vtable 0x7E89F4 = FlyLocomotionClass 次基类 vtable（COL 0x800658, offset=4, TD 0x8223E8）；见 EVIDENCE/p11_direct.txt 末尾澄清。
- 写点目标 ebx = arg1，被 type==2 / [+0x6C4]+0xE0D 查询的对象是 edi = arg2；二者在数据流上角色分离（0x55A710 把 ebx 写入 edi 的 +4/+8），故判为「out-holder 回写，不可能命中在册步兵」。
- **缺什么**：ebx 的 RTTI（该函数 ecx=this 未使用，两个显式参数都无法从 vtable 定类）+ 是否存在 ebx==edi 的调用点。按 fail-closed，此点结论为 [静态推断]（结构分离），非字节级 [已证]；若审计要求逐点 RTTI，则 11/11 的全域结论应整体降为 [静态推断]。
