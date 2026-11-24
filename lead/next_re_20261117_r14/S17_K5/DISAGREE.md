# S17-K5 · DISAGREE

## D0 · 基线：无 DISAGREE
- 现场读盘 102/92/54 与卡面完全一致（时点 2026-11-18T07:33:00+08:00），按纪律 9 未停机。

## D1 · 严格 named 口径提醒（非基线分歧）
- 主台账 92 个 named 中含 `CStreamClass::slotN`、`T_TClassFactory_*::slotN`、`SwizzleManagerClass::slotN` 等旧占位名；卡面/基线仍按非 `sub_` 计为 named。
- 本卡不碰旧行；新交 `DebugLogSink_behavior` 不是 `sub_`/`slotN`/`vslotN`/`Class::sub_`，不会增加占位水分。

## D2 · K3 对 0049F740/0049F8B0 的“不可定”理由确有漏项，但结论仍应移出 S17
- K3 漏掉的是字符串路；本卡已补齐：直接 push `COPYPROTECTION - Received message from launcher.` / `COPYPROTECTION - Shutdown` / `WChat\SysID`，并由 MapViewOfFileEx / UnmapViewOfFile / RegOpenKeyExA 独立闭合。
- 但两者分别是 launcher 共享内存映射与 COPYPROTECTION 关停/注册表清理；唯一直接调用者分别落在 S09/S04 [未证] 函数，体内无 RTTI/vptr、无 vtable 引用。建议 D-37 把这两行从 S17 改归属（具体 S 编号由 D-37 裁定）。

## D3 · 004068E0 的跨域性
- 它当前在 S17 台账内，但语义是跨子系统 no-op debug/log sink（1,672 调用点、1,492 个字符串 push）。本卡只按当前 entry 交 S17 delta；若 D-37 改归属，named 比例不降。

## D4 · 00773450
- RTTI 实读 `.?AVWebBrowser@@`，不是 S17；建议 D-37 同步考虑改归属。
