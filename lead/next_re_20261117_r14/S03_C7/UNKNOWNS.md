# S03-C7 UNKNOWNS

卡号 S03-C7；`gamemd.exe` 只读 SHA-256 `73201CC0…F67476`。本文件登记「任一环不成立、不进 delta」的 8 行作业面内行，以及口径/池边界等未能闭合项。

## U1 · A 集合与排除集合成（可复算，无UNK）
- S03 A=31（SURVEY_RING24 MATRIX，`classification.tsv` has4_strict=1 实测 31）。
- 排除 23 = C4(7) ∪ C5(5) ∪ C6(7) ∪ 黑名单(00431F10/00473AE0/0047AF10/0065D240)；余 8 行 = 本卡作业面。M43 2 行 + SEMFIX 4 行均在 C6 内，无额外扣减。00432050 在 C6 排除集内、另作独立复核（见 DISAGREE D1），不占 8 行、不进 delta。

## U2 · 00473C00（CCFileClass::slot11）—— ③ 环不成立（③a）
- ② 成立（CCFileClass vt0x7E16B0 slot11）④ 成立（26 站点），但 ③ 仅 2 道闸（`+0x009 je`、`+0x01C jne`），不达 D-42 细则#1「≥3 互斥闸」；无回边/跳表/`cmp -1`/GetLastError。getter 语义（缓存命中/取 Size/按名解析）属机械可述。按"任一环不成立不进 delta"维持 `[静态推断]`。

## U3 · 00473CE0（CCFileClass::slot13）—— ③ 环不成立（③a）
- ②/④ 成立（42 站点）。`+0x006 test ecx,ecx` 的 `ecx=lea [esi+0x58]` 恒非 0（死分支/编译残迹），有效体 = 构空容器(`+0x00E call 0x43AD00`)+清 1 字段(`+0x015`)+委托(`+0x01C call 0x4325C0`)，单次构造+单次清零+单次委托，③a。维持 `[静态推断]`。

## U4 · 00473FC0（CCFileClass::slot2）—— ③ 环不成立（③a）
- ②/④ 成立（14 站点）。5 指令、0 闸：`+0x004 mov [ecx+0x68],0` + `+0x00C call 0x47AE10`（委托 CDFile Open）；清零+单调用，③a。维持 `[静态推断]`。

## U5 · 0047AAB0（CDFileClass::slot7）—— ③ 环不成立（③a）
- ②/④ 成立（2 站点）。纯转发桩：`mov eax,[esp+4]; push eax; call 0x431F70; ret 4`，D-42 ③a 原文形态。维持 `[静态推断]`。

## U6 · 00631D30（FilePipe::slot1）—— ③ 环不成立（③a）
- ② 成立（5 表持有 slot1：SHAPipe/FilePipe/BufferPipe/Pipe/PKPipe → ⑯=Pipe）；④ 成立（6 站点）。体为 `mov ecx,[ecx+4]; test; je; mov eax,[ecx]; jmp [eax+4]` + NULL 返回，正是 D-42 ③a 逐字示例。维持 `[静态推断]`。

## U7 · ③b 基率池口径边界
- 池 = 盘上 `coverage.tsv` S03 grade=`[静态推断]` 且 entry 在 `SURVEY_RING24/EVIDENCE/classification.tsv` 有 CFG extent = **91 行**；C4 报 111、C5 报 102、C6 审计复算 85，截面不同（M 卡逐轮并入使 `[静态推断]` 池缩小），不可跨卡直接比。本卡两档均用 91 池、seed 20261119、2000 次取 8。strict K=18/91=19.78%、loose K=32/91=35.16%。`K=8×p` 仅恒等式，不作校验（§8.7 判据3）。

## U8 · 00432050 改写归属
- 复核确认为缓冲**写**（见 `EVIDENCE/REPROCESS_00432050.md`），正确语义与 ③b 证据已给出；但此行在 C6 排除集内、不在本卡 8 行，不进本卡 delta。盘上仍 `[静态推断]`（M43 未并入）；改写须由后续 M 卡执行，本卡无权改 coverage.tsv。

## U9 · 未做真机 / 无 venv
- 本卡纯静态：未启动 gamemd.exe、未写进程内存、未 pip install、未建 venv、未改 `ra2youli\`、未改 COVERAGE/台账/COMMON/其它卡目录。
