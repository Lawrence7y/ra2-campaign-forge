# S03-C8 UNKNOWNS

卡号 S03-C8；`gamemd.exe` 只读 SHA-256 `73201CC0…F67476`（现场复算）。本文件登记「任一环不成立、不进 delta」的 5 行作业面行、每行缺什么，以及口径/池边界等未能闭合项。

## U0 · 作业面为何是 5 行而非 8（可复算，无 UNK）
- S03 A=31（SURVEY_RING24 `A_strict.json` ∩ `classification.tsv` has4_strict=1，与 MATRIX S03 A=31 一致）。
- 排除集合成（唯一 26）：C4 delta 7 ∪ C5 delta 5 ∪ C6 delta 7 ∪ C7 delta 3 = 22 互不相交；SEMFIX_SLOTS2 S03 4 全落 C6 内（无新增）；已判不成立 5 中 00432050 已在 C6、另 4（00431F10/00473AE0/0047AF10/0065D240）新增 ⇒ 22+4=26。
- A 剩余 = 31−26 = **5 行**。任务「只做 8 行，不得扩」是范围上限：不扩面到排除集行、不从 A 池外凑第 6–8 行。本卡对这 5 行全部作业，不虚构 3 行。

## U1 · 00473C00（CCFileClass::slot11）—— 缺 ③b（③a）
- ② 成立（单持有表 CCFileClass vt0x7E16B0 slot11 → ⑯=CCFileClass）；④ 成立（26 站点，骨架齐）。
- **③ 环不成立**：仅 2 道 jcc（`+0x009 je` 缓存空、`+0x01C jne` open 态），判据数 2 < D-42 细则#1 的 ≥3 互斥闸；backedge=0，无跳表/`cmp -1`/`0x8000xxxx`/GetLastError（`+0x015 call 0x431F10` 的 al 为 open 布尔非错误码）、无 ≥2 vt 写或 ≥10 字段布局断言、无循环写。整体是 getter（缓存命中取 Size / open 则委托 `+0x048 call 0x4325A0` / 未开则虚 Open 后 `+0x03A call 0x5B4430` 按名解析）——D-42 ③a 机械可述。缺的是**可证伪的关键判据**（≥3 互斥闸动作互异 / 错误码返回约定 / 形状断言 / 完整 I/O 循环），任一即可升 ③b，此处全无。维持 `[静态推断]`。

## U2 · 00473CE0（CCFileClass::slot13）—— 缺 ③b（③a）
- ② 成立（CCFileClass slot13）；④ 成立（42 站点）。
- **③ 环不成立**：`+0x003 lea ecx,[esi+0x58]` 取字段地址恒非 0 ⇒ `+0x006 test` / `+0x008 je` 为死分支（编译残迹，有效 jcc 仅 1）；有效体 = `+0x00E call 0x43AD00`（构空容器）+ `+0x015 mov [esi+0x64],0`（清 1 字段）+ `+0x01C call 0x4325C0`（委托 Close）。构容器 1 次调用 < ③b③ 界线（≥2 vt 写或 ≥10 字段断言），无回边/跳表/错误码/循环写。单次构造+单次清零+单次委托 ⇒ ③a。缺可证伪关键判据。维持 `[静态推断]`。

## U3 · 00473FC0（CCFileClass::slot2）—— 缺 ③b（③a）
- ② 成立（CCFileClass slot2）；④ 成立（14 站点）。
- **③ 环不成立**：5 指令、0 闸、0 回边；`+0x004 mov [ecx+0x68],0`（清字段）+ `+0x00C call 0x47AE10`（委托 CDFile Open）+ ret 4。D-42 ③a「清零+单调用」。被调 0x47AE10 体内有路径遍历循环（SEMFIX_SLOTS2 记其 ③b④），但**本函数**按自身体判 ③（D-40「③不可被某处写字段顶替」），不可借被调方合同。缺可证伪关键判据。维持 `[静态推断]`。

## U4 · 0047AAB0（CDFileClass::slot7）—— 缺 ③b（③a）
- ② 成立（单表 CDFileClass slot7 → ⑯=CDFileClass）；④ 成立（2 站点）。
- **③ 环不成立**：纯转发桩 4 指令 `mov eax,[esp+4] / push eax / call 0x431F70 / ret 4`，D-42 ③a 原文逐字同形。无闸/回边/跳表/错误码/形状断言。缺可证伪关键判据。维持 `[静态推断]`。

## U5 · 00631D30（FilePipe::slot1）—— 缺 ③b（③a）
- ② 成立（5 表同 slot1 → ⑯=基类 Pipe）；④ 成立（6 站点）。
- **③ 环不成立**：D-42 ③a 逐字同形 `mov ecx,[ecx+4] / test / je / mov eax,[ecx] / jmp [eax+4]` + 空则 `xor eax,eax; ret`。纯转发桩+NULL 哨兵；n_jcc=1、backedge=0、无 `jmp [reg*scale]` 跳表。缺可证伪关键判据。维持 `[静态推断]`。

## U6 · ③b 基率池口径边界
- 池 = 当前盘上 `coverage.tsv` S03 grade=`[静态推断]` ∩ `SURVEY_RING24/EVIDENCE/classification.tsv` 有自写 CFG extent = **88 行**；seed 20261119，2000 次取 8 不放回。strict K=17/88=19.32% E[8]=1.5455 MC=1.5285；loose K=27/88=30.68% E[8]=2.4545 MC=2.4510。
- 与 C4(111)/C5(102)/C6 审计(85)/C7(91) 池大小不同（M 卡逐轮并入使 `[静态推断]` 池缩小）；本卡 88 是 C7 3 行并入后截面。检测器自写：strict ③b① 只认物理跳表、③b④ 要求回边体内显式非栈写+界判+推进（M7）；loose 加细则#1 ≥3 体内互斥闸。`K=N·p` 仅恒等式，不作校验（M3）。不跨卡直接比基率。

## U7 · 未做真机 / 无 venv / 写域
- 纯静态：未启动 gamemd.exe、未写进程内存、未 pip install、未建 venv、未改 `ra2youli\`；未改 COVERAGE/台账/R14_COMMON/STATUS_BOARD/其它卡目录；未写 `_audit\`。所有输出仅落 `S03_C8\`（含 `EVIDENCE\`/`work\`）。delta 0 行 = 实际 0 行（M6/M7）。
