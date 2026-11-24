# S17-K5 · UNKNOWNS

## U1 · 9 条未进本卡 delta 的残行
- `0040E340`：链表 splice；无 RTTI/vptr/串，调用者跨多域；只可报通用行为，不造名。
- `00427940`：`TEM`/`.SHP` + `FileSystem::LoadFile`；对象类和 S17 归属未闭合。
- `0042E410`：4-dword 通用 setter；无 owner identity。
- `00433CF0`：UTF-16 分派 walker；更像 UI/文本域；未找到 S17 锚。
- `004355B0`：3-byte 通用 setter；无 owner identity。
- `0043AE50`：条件 delete + 清零；缺 RTTI/vptr，不能落到具体类析构名。
- `0049F740`：语义已由镜像串+API 定为 launcher IPC/共享内存映射；**归属待 D-37**，不在 S17 delta。
- `0049F8B0`：语义已由镜像串+API 定为 COPYPROTECTION 关停/注册表 `WChat\SysID` 清理；**归属待 D-37**，不在 S17 delta。
- `00773450`：RTTI 证为 `WebBrowser` 构造；**归属待 D-37**，不在 S17 delta。

## U2 · 基线口径
- 现盘 92/102 包含历史 `slotN` 名；按“严格 named”重判旧行可能降低基线，但这超出本卡写域，已留 D1 给审计。

## U3 · 004068E0 的归属
- 名字 `DebugLogSink_behavior` 由 no-op body + 全局日志调用约定支撑；它不是 S17 专属语义，但当前台账 entry 在 S17。若 D-37 将其移出 S17，分母变 101，named 仍为 92/101=91.09%，门槛不受损。
