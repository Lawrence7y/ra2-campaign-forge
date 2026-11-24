你是 RA2 Campaign Forge 的**独立复核卡 W53**。任务：**独立复核「散装文件优先于 MIX 内同名条目」这条字节级结论**——它是后续所有修法的地基。

工作目录：`D:\Project\ra2-campaign-forge`。**第一件事：立刻建目录 `lead\next_re_20261112_r02\W53_override_independent\` 并写 `STARTED.txt`（带时间戳）。**

## 为什么派你
这条结论支撑了三件已落地的能力：散装 `MAPSELMD.INI` 驱动推进（真机已证）、散装 `ra2md.csf` 覆盖文案（真机已证）、以及未来所有「散装投放」的修法。原卡 W29 给的判定，Lead 手算过 3 处 `rel32` 目标，但**未完整独立反汇编**。

## 目标镜像
`ra2bench\gamemd.exe`，4,825,360 B，SHA-256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`
`ImageBase=0x400000`，`RELOCS_STRIPPED`，`.text` RVA==FOFF==0x1000（⇒ `.text` 内 `FOFF = VA − 0x400000`）。

## 要独立判定
1. **`CCFileClass::Get_File = 0x473D10`**：完整反汇编该函数，画出控制流。回答：磁盘尝试与 MIX 查找的**先后顺序**是什么？磁盘命中后是否**跳过** MIX 分支（跳到哪个地址）？`mode&2` 位的作用？有没有其它分支能绕过磁盘？
2. **`MixFileClass::Find = 0x5B4430`**：它是「首个命中返回」还是「后者覆盖」？遍历顺序是 FIFO（先装载者优先）还是 LIFO？给指令级依据。
3. **Lead 手算过的三处，请独立复算**（不要看我的结论先算，最后再对照）：
   - `0x473D2D` 的 `E8 DE E1 FB FF` 目标是否为 `0x431F10`
   - `0x473D68` 的 `E8 C3 06 14 00` 目标是否为 `0x5B4430`
   - `0x473D34` 的 `jne` 目标是否为 `0x473E39`
4. **反例检验**：有没有任何代码路径**先查 MIX 再查磁盘**？请给出你的检索方法与覆盖度（**不要用线性扫描冒充完整 xref**）。

## 纪律
- 纯离线只读：不启动游戏、不 attach、不写 `ra2youli`、不改仓库、不动 `W21`–`W52`、git 只读
- **不要取 `.game_instance.lock`**（真机卡在持锁）
- 分级：`[本次实测]`/`[本次读码]`/`[静态推断]`/`[转引]`/`[待运行验证]`
- capstone；**`ret` 不是函数结束判据**（该函数有中段分支尾）；**等距指针表 ≠ vtable**；**线性扫描 ≠ 完整 xref**
- 最后才读 `W29_override_order\OVERRIDE_ORDER.md` 与 `REVIEW\LEAD_VERDICT_CSF_live.md` 做对照，单列「一致/不一致」
- 若结论有误，直接说 —— 这是地基，错了上面全塌

## 交付（只写这个目录）
`W53_override_independent\`：`STARTED.txt`、`INDEPENDENT_VERDICT.md`（四问逐答 + 控制流图 + 三处 rel32 复算 + 对照）、`EVIDENCE\`、`DISAGREE.md`

（若处于只读 /plan 约束无法写盘，请在回复正文里完整给出上述内容。）