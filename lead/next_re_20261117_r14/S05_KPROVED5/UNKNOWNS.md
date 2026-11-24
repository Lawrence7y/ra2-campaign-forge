# S05-KPROVED5 · UNKNOWNS

写域仅本卡目录；gamemd.exe 只读（SHA-256 73201CC0…F67476 现场复核）；未改 coverage.tsv / 台账 / R14_COMMON / STATUS_BOARD / ra2youli / 其它卡目录 / _audit；未建 venv、未 pip install、未 git commit。

## 行源与排除集（先读 delta 后合成）
- S05 A 集合 = 41 行（SURVEY_RING24 主口径 ②仅RTTI × ④严格档，S05 A=41），从 classification.tsv 按 has2_rtti=1 ∧ has4_strict=1 复算恰 41。
- 排除集 19 行唯一 = S05_KPROVED2(8) ∪ S05_KPROVED3(8) ∪ S05_KPROVED4(3)；SEMFIX_SLOTS3 的 7 行是 KPROVED3 子集（去掉回退行 00704350），已含在内，无新增。
- 剩余池 = 41 − 19 = 22 行。本卡按复杂度/代表性取 8 行处理。

## 逐行未并入理由（四环中③仅 ③a）
- **U1 00709A40 TechnoClass::slot289**：①✓(16B/nop) ②✓(单表 007F4960 slot289 TechnoClass) ④✓(站点 004D82D9)。③ a：4 条 jcc 仅 2 个相异目标（+0xB/+0x12 同型查空闸同跳 0x709A59；+0x25/+0x33 同型 al 判同跳 0x709A7C），各闸动作不构成"互斥多路"。被调 0x71ABC0/vt[308]→0x70F110/vt[268]→0x705D50/0x6385C0 虽相异，但选择由同型闸决定，违 M4（00704350 回退同类）与 §8.7 判据6（0047AF10 同类判 ③a）。严格档（跳表/错误码/内存形状/循环）全不成立。⇒ ③a，不进 delta。
- **U2 005F9720 ObjectTypeClass::slot5**：③a 析构/清零；+0x1C4..+0x1E4 有界清零循环（ecx=0x12、4 处显式写、add eax,8、dec ecx、jne）整体是 memset 式清零非"有信息 I/O"，且无 ctor 数+vt+对象大小三件（D-42 细则#2）；与 S05_KPROVED4/EVIDENCE/ROW_005F9720.txt 同型判定。
- **U3 006F3F40 FootClass::slot9→基类 TechnoClass::slot9**：②多表同槽（FootClass 007E8C94 + TechnoClass 007F4960）归基类级。③a：6 个顺序独立惰性构造块（各自"字段非空→new+构造+存偏移"），非单一选择子 switch；无错误码/循环/ctor 形状。依 S05_KPROVED4 同型判定。
- **U4 006F6CA0 TechnoClass::slot54**：③a 线性初始化（前置校验+GetCellAt+坐标换算+逐段虚调写字段），7 jcc 为独立 flag/null 守卫，无合同闭合要素。依 S05_KPROVED4 同型判定。
- **U5 006F4A70 TechnoClass::slot73**：③a 2 闸布尔谓词（+0x8 call 0x5f5850 判 al、+0x11 test [esi+0x418]），仅 2 闸 < 细则#1 的 ≥3，一路虚调 push 0xd，无其它合同要素。
- **U6 00711F00 AircraftTypeClass::slot33→基类 TechnoTypeClass::slot33**：②多表同槽（4 TypeClass 表）归基类级。③a 浮点缩放换算（单 edi 非空闸 + 两路 [vt+0xac] + 0x50bdf0/0x50beb0/fmul/0x7c5f00），无跳表/错误码/循环/内存形状。
- **U7 0070E2B0 TechnoClass::slot85**：③a 标志写入 setter（连续写多个偏移 + 单闸 cmp dl,al→je 写 0/1），无合同闭合要素。
- **U8 0040BA50 VectorClass<TechnoClass*>::vslot3**：③a 容器 Clear（§8.4 slot3=Clear：2 闸同目标 AND + call 0x7c8b3d free + 写 {4,8,0xd}=0）；原始命中另 1 处 0086E1D4 非 vtable 已排除；机械可述。

## 无其它不确定项
- entry 形态、② 持有表（全镜像 4 对齐原始命中 + RTTI fail-closed，1214 表与权威一致）、④ 站点（全 .text 1,392,592 指令 / 68,253 E8@边界，体外非自环）均实测一致，无 UNKNOWN。
- ③b 基率（严格/宽松两档，seed 20261119，2000 次，池=S05 [静态推断] 387 行）见 EVIDENCE/baselines.json。
