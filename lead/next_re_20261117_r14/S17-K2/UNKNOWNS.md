# S17-K2 · UNKNOWNS（未闭环清单）

> 只列本卡**未证 / 未改 / 需后续卡**的事项；已证结论见 `PROGRESS.md` 与 `EVIDENCE\T2_T3_EVIDENCE.txt`。

## U1 — 低地址段 `sub_XXXXXXXX` `[静态推断]` 剩余 7 行未改名（callgraph 弱信号）

原 10 行候选：`004068E0` / `0040E340` / `0041D6E0`* / `00427940` / `0042E410` / `00431B80`* / `00433CF0` / `004355B0` / `0043A5D0`* / `0043AE50`
（* = 本卡已改名 3 行，故实际仍剩 **7 行** `sub_`：/004068E0/0040E340/00427940/0042E410/00433CF0/004355B0/0043AE50）。

- 这 7 行中：
  - `0x4068E0` = 单 `ret` 桩（字节 `c3 90 90…`，1672 调用者），无任何 S17 语义，不改名。
  - `0x40E340`/`0x42E410`/`0x4355B0` = 通用链表插入 / 4-dword 构造 / 3-byte setter；字节确凿但**非 S17 专属**，被 census 以 callgraph 1 票误归 S17。保持 `sub_`，见 `DISAGREE.md` D3。
  - `0x427940`/`0x433CF0`/`0x43AE50` = 对象字段遍历 / word 数组解析 / 指针释放+清零；未见 IStream/Ole/Here_I_Am 任一 S17 原语，不猜测命名。
- **未闭环**：这些行的 subsystem 归属存疑（可能应归 S05 对象模型 / S22 通用工具），需另立卡逐行复核 census 证据链；本卡不强改 subsystem（派卡只授权 name/sem/grade 增量）。

## U2 — 3 行明确误归类的 `sub_` `[未证]`（ strings / RTTI 反证）

- `0x49F740` / `0x49F8B0`：字符串 `COPYPROTECTION - Received message from launcher` / `Shutdown` + `MapViewOfFileEx`(IAT `0x7E1244`) / `UnmapViewOfFile`(`0x7E1238`) + `RegOpenKeyExA(WChat\SysID)`(`0x7E100C`) ⇒ **copy-protection/注册表路径，非存档**。
- `0x773450`：RTTI `WebBrowser` (`vptr 0x7F743C`)+ 串 `Instantiating embedded WebBrowser`(`0x8495CC`)+ `CoCreateInstance`(`0x7E15FC`) ⇒ **内嵌浏览器构造器，非存档**。
- 三行均保持 `sub_` + `[未证]`，不打 S17 语义；见 `DISAGREE.md` D3。

## U3 — S17-F1 遗留（本卡不重开，引用存档）

1. **Save/Load 非一一对应**：Save 35 模板块 vs Load 16 助手入口（§946 已入账）；逐类映射未闭合。
2. **存档块内部 magic/id 表**：CONTENTS 流布局 `[未证]`（S17-F1 U4）。
3. **`[0xABCE08]` 全镜像复位写者**：审计 §946 §4 证伪「一次性」；本卡未触及。
4. **Load_Core 拆分**：`0x67E440`(749 B) vs `0x67E730`(4258 B) 归属（审计必改 3），本卡引用订正未重做。

## U4 — 真机 / KB 缺口（DoD 第 5/6 条）

- `S17-V1` 仍在 LIVE_QUEUE `WAIT_DEP`（前置 S17-F1 已入账但未提 RUNNING）；**无 S17 真机卡**，2 条关键运行时事实缺真机（见 `DOD.md` 第 5 条）。
- `KB\S17_*.md` 不存在（22 子系统全缺）；本卡按令不创建（见 `DOD.md` 第 6 条）。

## U5 — 本卡 delta 生效依赖

- `coverage_delta.tsv`（7 行）须下张 M 卡合入 `coverage.tsv` 才改动 PANEL；本卡**未改** `COVERAGE\coverage.tsv`、`PANEL.md`、`TARGETS.tsv` 之外的任何共享文件。
- 若审计降低某条 `[已证]`，atlas proved 可能回落到 49+3=52（仍 ≥50%，51.02%）；即便再降一条到 51 仍恰 50%。**最低安全线：4 条提级至少留 2 条**。
