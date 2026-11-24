# S17-K6 · UNKNOWNS

## U1 · 未交 delta 的 8 行
- `004068E0`：单 `ret` no-op；K5 同源退级且与 `WWDebug_Printf` 地址冲突，归属待 D-37。
- `0040E340`：GenericNode 链接操作；无类/域锚。
- `00427940`：`TEM`/`.SHP` 装载；调用者 S09/S21，非 S17；无存档串锚。
- `0042E410`：4×dword POD setter；类型不可区分（RectangleStruct/LTRBStruct 等都可能）。
- `00433CF0`：UTF-16 文本宽度/折行 walker；UI/Drawing 域，无 S17 锚。
- `0049F740`/`0049F8B0`：COPYPROTECTION，已由审计排除。
- `00773450`：RTTI 证 WebBrowser，已由审计排除。

## U2 · 两条新名的证据级别
- `MemoryBuffer::Clear` 与 `ColorStruct::ColorStruct` 的**类型名**来自工程 YRpp 源码声明，不是 RTTI TypeDescriptor；按 R14_COMMON §9.5 不升 `[已证]`，只记 `[静态推断]`。
- 若 Lead 严格禁止非 RTTI 类型名，机械降级名建议：`0043AE50→Clear_OwnedBuffer3`、`004355B0→Set_RGB3`；命名语义与 delta 计数不变。

## U3 · 待独立审计
- 需异族审计独立复算：两条函数体末字节到 ret、RTTI 链 `.?AVCCFileClass@@`、`4019A3/4019B3` 调用点、YRpp 三处行号、以及 9 列 delta 格式。
