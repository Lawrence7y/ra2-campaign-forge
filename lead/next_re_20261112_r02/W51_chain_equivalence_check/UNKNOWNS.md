# UNKNOWNS · W51 未覆盖项与待运行验证

> 状态：**纯离线只读文本比对 + 关键字节抽查完成；未运行游戏、未 attach、未修改 `W21`–`W50` 或 `REVIEW/`** ｜ 2026-11-13

## 1 · 静态层面未展开验证的部分

1. **`GUI:Continue` (`0x0046E8BD`, ID `0x6D1`) 到 `0x0055D14A` (`call 0x685670`) 之间的 UI 消息派发桥** `[静态未展开]`
   - 本卡抽查确认 `0x0046E8BD` 在 `CampScor.cpp` 创建 `GUI:Continue` 控件（`0x6D1`），并确认 `0x0055D14A call 0x685670` 经 `0x006859C7 je 0x685a10` 进入 `SkipMapSelect` 分派；但两者之间经由哪个回调/循环状态位触发 `0x0055D14A`，W31 未追踪、W33 未给出中间指令证据，本卡亦未展开整块 UI 事件循环。

2. **两卡所列 `0x005ADD10` / `0x005ADE20` 之外的间接调用（虚表/函数指针）覆盖度** `[静态推断]`
   - W31 通过全 `.text` `E8/E9 rel32` 扫描确认直接调用仅 `0x00685A52`、`0x00685A5C`、`0x00685A74` 3 处；本卡未重新执行全镜像间接引用或虚表调用图审计，不能以静态方式绝对排除存在间接调用入口。

3. **W34/W43 提到的其余 `REVIEW/` 文件（如 `LEAD_VERDICT_Q2_CLOSED.md`、`LEAD_VERIFY_W37.md`、`LEAD_W29_VERIFY.md` 等）的交叉遗留** `[范围外]`
   - 本卡任务范围限定于核对 W31 (`WHY_MAP_FAILS.md`)、W33 (`NEXTSCENARIO_FLOW.md`)、Lead 合图 (`LEAD_VERDICT_map_start_root_cause.md`) 与 W34 (`MAPSELMD_SPEC.md`) 的判定链等价性；未越界修改 `REVIEW/` 文档，也未对与 MapSelect 判定链无关的其它结论逐卡重测。

## 2 · 仍需运行时证据（静态互证无法替代）的部分

1. **负对照（W27/W39 `frame=210` 报错帧）在活进程中究竟落在 `MapSelect::Init` 哪一条失败出口** `[待运行验证]`
   - W31 指出 `0x005AE220` 内存在 4 条带调试日志的失败出口（`Invalid Scenario pointer!` / `Invalid side!` / `Unable to initialize choices!` / `Invalid stage!` / 另加 `Unable to create font!`），且 `[Scen+0x125C]` 在胜利结算后的实时内容未在真机抓取。即使 W39 后续通过补齐 `MAPSELMD.INI` 跑通了 `A1→A2`，仍未在负对照弹窗帧通过断点/调试日志直接捕获 `"MapSelect: Invalid stage!\n"` 或 `MapSel.CPP:0x86` 命中记录。

2. **`SkipMapSelect=yes` 失败出口（`0x005ADFF3` vs `0x005AE0CD..0x005AE0F1` 静默返回 → `0x005ADEFA` / `MapSel.CPP:0x98`）在真机上的实际触发路径** `[待运行验证]`
   - `SkipMapSelect=yes` 路径在 `W39` 等真机测试中同样属于未测/未闭合项；候选不匹配时「不打印 `Invalid stage!` 直接靠 `[Scen+0x125C]` 空串返回 `AL=0`」属于本次静态读码结论，尚无活进程断点验证。

## 3 · 纪律自查

- 纯离线只读：未启动 `gamemd.exe`、未 attach/读活进程、未取 `.game_instance.lock`、未写 `ra2youli/`、未修改 `ra2forge/`、未修改 `W21`–`W50` 或 `REVIEW/`。
- 仅在 `lead\next_re_20261112_r02\W51_chain_equivalence_check\` 写入 `STARTED.txt`、`CHAIN_EQUIVALENCE.md`、`UNKNOWNS.md`。
- 关键 VA / RVA / FOFF 与原始字节均由本次离线脚本对 `ra2bench\gamemd.exe` 实测反汇编核对。
