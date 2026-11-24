# SEMFIX-S10 · 给 **25 行 `[已证]`** 补写语义栏（**只改语义，不动 grade**）

> ⚠️ **本卡不升不降任何 grade。** 这 25 行的 grade **已经过 `AUDIT-SEM-SELF` 判为 P1（③b 成立）**，
> 但它们盘上的语义栏仍是旧模板语（「槽语义未证」/「线索/弱信号」）⇒ **行内自相矛盾**。本卡的任务是把语义写对。

## 依据
`AUDIT-SEM-SELF`（DeepSeek v4.1-flash high，只读测量）对全表 95 行「`[已证]` 但语义自陈未证」逐行独立反汇编，判 **P1=73 / P2=22**。
它在 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\ROW_VERDICTS.tsv` 的 **`criterion` 列**里为每个 P1 行写了**具体字节证据**（跳表地址 / 回边 / 哨兵写点 / vt 写点）。
⇒ **本卡就是把这些 `criterion` 转写成人类可读的 ③ 合同。**

## 工作面（25 行，**全部已给 P1 判据**）
- `0045A560`（S10）：`同 0040F0A0 形态：复制循环 head=0x45A5AE(读/写/inc/cmp 齐)，DV<InfantryClass*> slot2 SetCapacity`
- `0045A610`（S10）：`查找循环 + 未命中 or eax,-1；DV<InfantryClass*> slot4 FindItemIndex`
- `004D4200`（S10）：`多闸互斥：[+0x5A4]→计时路径；[+0x674] 空则 E_POINTER(0x80004003@0x4D4217)；vt[+0x10] 谓词；[+0xB4]==-1 则 vt[+0x484] 并 ret 1；否则`
- `004D4280`（S10）：`跳表 0x4D4B04 共 4 槽、cmp bound=3，目标全落 .text`
- `004D4B20`（S10）：`守卫链 + 4 个互斥动作结局；vt[+0x2C]==15 选择(0x4D4B38 sub/neg/sbb/not/and)；[+0x2B4] 的 vt[+0x2C]==6；0x70D0D0(0xE)；尾 RNG 0x6`
- `004D4CB0`（S10）：`同 004D4B20 形态(90 指令)，结局 0x4D4D39/0x4D4D26/0x4D4D86 三路互斥`
- `004D4DC0`（S10）：`170 指令 13 jcc：byte[+0x390]→vt[+0x1C8]→0x703590+0x5657A0(GetCellAt)+vt[+0x480] 链，随后 byte[+0x68E] 分支`
- `004D5070`（S10）：`严格循环 head=0x4D5118 span=41(读16/写3/cmp)；FootClass slot135`
- `004D5350`（S10）：`186 指令 18 jcc：byte[+0x6D4] 闸、vt[+0x39C] 谓词、vt[+0x2C]==15 选择、[+0xEC3] 状态位，结局互斥`
- `004D6AA0`（S10）：`严格循环 head=0x4D6F7A span=41(读16/写3/cmp)；FootClass slot136，30 调用`
- `004D9290`（S10）：`严格循环 head=0x4D93B9 span=7(读3/写1/cmp)；FootClass slot144`
- `004DA2C0`（S10）：`显式状态分派：sub eax,0/je(态0)、dec eax/jne(其它)，态0 写 0xBC=1(0x4DA2FF)、态1 写 0xBC=0(0x4DA2E6)，各态动作链不同`
- `004DA530`（S10）：`722 指令 98 jcc 31 调用；FootClass slot23(0x5C) 多路守卫+动作链`
- `004DDF90`（S10）：`同族状态分派：[+0xBC] 态 0/1 各带独立动作链(0x4DDFDB 态0 调 vt[+0x53C]；0x4DDFA9 态1 调 vt[+0x1E8]/[+0x1EC])`
- `0051F3E0`（S10）：`5 道互斥闸：[+0x6C0][+0xEC2]、0x70D0D0(0xE)、[+0x2B4] 的 vt[+0x2C]==6、[+0x520][+0x1577]、[+0x1701]，随后 vt[+0x480] 动作`
- `005B2FD0`（S10）：`任务状态转移：0xAC==0x1C 且 arg==5 则不动，否则写 0xAC=arg、0xB4=-1、0xB8=0、0xBC=0、0xC0=帧、0xC4=0、0xC8=帧、0xCC=arg、0xD0=0(0x5B2FE`
- `005B3060`（S10）：`跳表 0x5B34E8 共 32 槽、cmp bound=0x1F，目标全落 .text；MissionClass slot23`
- `005B3570`（S10）：`状态转移：排队任务 0xB4→当前 0xAC、0xB4 置 -1、0xB8 清 0、0xBC 清 0、时间戳 0xC8/[+0xCC]/[+0xD0] 由 0xA8ED84 写；0xB4==-1 则返 0(0x5B35C`
- `005B35E0`（S10）：`多路：0x1C 且 arg==5 → 跳过；0x13 → 跳过；arg==-1 → 跳过；等值判断后写 0xB4/0xB8，再按 arg 字节与 vt[+0x200]/[+0x1EC] 分派`
- `005B3650`（S10）：`三路互斥：0x1C&arg5 跳过、0x13 跳过、否则若 0xB4!=-1 则 0xB4→0xB0 并写 0xAC，反之 0xB0←0xAC/0xAC←arg`
- `005B36B0`（S10）：`转移+可证伪返回：[+0xB0]!=-1 则搬到 0xAC、0xB0 置 -1、0xB8 清 0、ret al=1；否则 ret al=0`
- `006B1850`（S10）：`复制循环 head=0x6B189E span=6；DV<SlaveManagerClass*> slot2`
- `006B1900`（S10）：`查找循环 + 未命中 or eax,-1；DV<SlaveManagerClass*> slot4`
- `006B8660`（S10）：`复制循环 head=0x6B86AE span=6；DV<SpawnManagerClass*> slot2`
- `006B8710`（S10）：`查找循环 + 未命中 or eax,-1；DV<SpawnManagerClass*> slot4`

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
- **⑨ 停机核验**：这 25 行在盘上都应是 `[已证]`；自己核对（不符即停下报告）。
- **⑮ 体内出现**：你在语义里引用的每个地址/偏移，**必须在体内真出现**（不能只抄 `criterion`）。抽样复核 ≥5 行。
- **⑲**：capstone 5.0.7 无 `op.index`（`op.mem.index`，无 index 返 **0 非 None**）。

## 交付
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_S10\`
`PROGRESS.md`（≤40 行，第一行写「补写几行」）/ `EVIDENCE\` / `work\`
`coverage_delta.tsv`：8 列 `entry, subsystem, name, one_line_semantics, grade, evidence_path, name_kind, 旧grade→新grade`
  （⚠️ **grade 列必须与盘上完全相同**，即 `[已证]`→`[已证]`；name 也必须与盘上逐字相同）
**开工 10 分钟内先落骨架；每完成 5 行增量落盘。严禁建 venv / pip install。**

## 核心数字
① 补写行数（目标 25）② 每行新语义的字符数（应 ≥80）③ 抽样复核的 ⑤ 体内命中率 ④ grade/name 零变更自证