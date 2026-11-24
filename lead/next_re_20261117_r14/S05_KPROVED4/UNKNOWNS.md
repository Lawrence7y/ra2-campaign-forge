# S05-KPROVED4 · UNKNOWNS

卡号 S05-KPROVED4。目标只读；本文件只写本卡目录。处理 8 行 = 00704350（上卡回退行，必重审）+ 其余 7 行未并入的 S05 A 集合行。
A 集合全集 A=41（`S05_KPROVED3\_audit\EVIDENCE\q8_pool.json` A_list，与 SURVEY_RING24 主口径 A=41 一致）；
排除集 = S05_KPROVED2(8) + S05_KPROVED3(8) = 16 行；剩余 25 行 + 回退行 1 = 26 候选，选 8 行处理。

## 1 · 00704350 —— 维持 [静态推断]（③b 不成立，不进 delta）

上卡 a-S05-KPROVED3 已把 00704350 从 delta 回退；本卡独立重审后**维持回退**，不凑 [已证]。
- ③b② 原引证三处 `cmp reg,-1`：+0x01A8 `cmp edi,-1/je +0x01D2`、+0x01D5 `cmp ebx,-1/je +0x01FE`、+0x0201 `cmp eax,-1/je +0x020A…+0x022B`。
  逐条打完三闸后续：edi/ebx/eax 均为三个候选 cell 的 `[cell+0x44]`（House 索引）。
  - 非 -1 路：`mov ecx,[0xa83d84]; mov edx,[ecx+idx*4]; test byte[edx+0x2b5];` 通过则 `lea eax,[ecx+ebp-1] / ret`（ecx=[0x843124]，ebp 为入口取得的 -N）。三闸成功路返回**同一表达式**，仅源寄存器 edi/ebx/eax 不同。
  - -1 路：闸1→闸2(+0x01D2)、闸2→闸3(+0x01FE)、闸3→+0x022B `add esi,0x388`（换下一个候选对象）。
  ⇒ 这是「[obj+0x44] 为 −1 就换下一个候选对象」的**回退链**：既非可证伪错误码/返回约定（③b②不成立），
  且命中 §8.7 判据 6「只有参数不同、汇入同一表达式」的细则#1 排除。
- ③b④ 两条 3 元循环：+0x05B7..+0x05C8 = `mov esi,[ecx]/test [esi+0x140]/jne/inc eax/add ecx,4/cmp eax,3/jl` —— **纯读无写**；
  +0x05D5..+0x0639 循环体本身无显式对象写，唯一写在被调 0x547150 内经指针的间接缓冲写，弱于 00716150 已自陈的栈累加器写口径。
- 全函数扫：`jmp dword/word ptr` 计算跳表 = 0；`B8 imm32 C3` = 0；`cmp reg,-1` 仅此 3 处；返回常量桩 = 0。
  ⇒ 无可交的「真正互异」③b 证据（各闸动作非互异、无错误码集合）。**维持 [静态推断]，理由进 UNKNOWNS，不进 delta。**
- 其余三环均成立（①入口形态 +0x0000 16B 对齐；②单持有表 007F4960[187] TechnoClass；④direct 站点 004DB08C）。

## 2 · 006F3F40 —— ③a，不进 delta

5 站点 direct 与 ①/② 均成立（②2 表同槽9 FootClass/TechnoClass→⑯基类级 TechnoClass）。
③b 不成立：+0x005D/+0x00D7/+0x016C/+0x01F4/+0x0243/+0x0294 六块是**顺序独立**的
「字段非空则 new(push size)+ctor+存到不同偏移」惰性初始化 if，不是单一选择子上的 switch/跳表（③b①不成立）；
无 -1 哨兵/错误码、无 B8 imm32 C3、无回边循环。整体为机械初始化流 = ③a，留 [静态推断]。

## 3 · 005F9720 —— ③a，不进 delta

①/②（ObjectTypeClass slot5 单表）/④（10 direct 站点）成立。
③b 不成立：+0x001E..+0x00EE 逐字段判空→dtor/free 再写 0；+0x01C4..+0x01E4 有界清零循环
（ecx=0x12，4 处显式写/add eax,8/dec ecx/jne）。D-42 ③a 明列「清零 + 置默认值」为机械可述；
循环有写有界但语义整体是清零而非有信息 I/O。③b③ 要求「成员 ctor 数 + vt + 对象大小」三件，此处仅 dtor/free，
无 ctor/vt 装配，不达。留 [静态推断]。

## 4 · 007171A0 —— ③a，不进 delta

①/②（TechnoTypeClass slot13 单表）/④（4 direct 站点）成立。
③b 不成立：448 指令 / 104 call 的线性字段转储，无回边(jmptbl=0/back=0)、无 -1 哨兵、无返回码集合、无 switch。③a。

## 5 · 006F6CA0 —— ③a，不进 delta

①/②（TechnoClass slot54 单表）/④（2 direct 站点）成立。
③b 不成立：+0x0011 call 0x5f4ec0 判 al 否则返回 0，其后顺序写字段 + 若干 call；
仅 +0x0175 cmp eax,0xf 一处常量比较（单一分支非多路），无 -1 哨兵/返回码集/回边/switch。③a。

## 6 · ③b 基率审计口径差（非 FAIL，登记透明）

本卡 D-42-faithful 双档检测器（同 S05_KPROVED3 口径，跨卡可比，seed 20261119/2000 次/池=S05 `[静态推断]` 387 行）：
strict **0.235142 (91/387)**、loose **0.379845 (147/387)**，MC 均值 1.8365 / 2.9975。
a-S05-KPROVED3 独立审计用更严检测器得 strict 0.188630 (73/387)、loose 0.291990 (113/387)。
两者差异来自 ③b③/④ 操作化宽严（本卡检测器 = 前序执行卡口径），非数据分歧；本报告同时列两值。
每档均注明操作化（见 EVIDENCE/baselines.json `operation`），且 K=N·p、E[8]=8·p 为恒等式，不作校验（M3）。
