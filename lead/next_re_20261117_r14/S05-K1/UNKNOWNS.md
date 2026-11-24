# S05-K1 · UNKNOWNS.md — 保留 `[未证]` 的条目（不臆造语义）

## 1. S05 `[未证]`/无名 127 条的处理去向
`work/filter_s05.py` 筛出 127 条（[未证]102 + sub_ 127，并集 127），分类：

| 类别 | 条数 | 处置 |
|---|---:|---|
| 对象字段双重支撑（本卡 §LAYOUT） | 8 字段（覆盖 25 条 one_line 含字段偏移项） | 升 `[已证]`（8 字段 → coverage_delta） |
| 构造器误归/降级（D2–D5） | 4 主 + 变体 14 | 交 coverage_delta（S05 具名） |
| 虚表槽实现 `ClassName::slotN (+0x4N)` | 227 条 `[静态推断]` | **不动**（本卡只恢复 slot 归属类，不给语义；`slot` 语义未证即未证） |
| "ObjectModel/Vtables region guess" 的 `sub_XXXXXXXX [未证]` | 约 90 条 | **保留 `[未证]`**：多为 vtable/数据区地址被当函数（atlas 下界伪影），本卡未对其逐条证"是函数"，按纪律 2 不二次筛选也不臆断 |

## 2. 无法定论的字段假设（列而不判）
- **`+0x1AC` 数据字段假设**：扫描见 `call [reg+0x1AC]` 20 处（虚槽形态）而数据字段归属 0；按纪律 4 不给语义。若确需数据字段，须另找该类自己的 `mov [this+0x1AC],X` 写点 + ≥3 读点。
- **`AbstractClass +0x14..+0x1C`**：`kb/11 §0.3` 记 3 个 dword 未序列化、纯运行时态；本卡未定位其写点归属，保留 `[未证]`。
- **`+0x94` 的 49/112 细分**：`R14_COMMON §4.7 / 台账 §939` 已给对象字段 49 / 其它 112；本卡只独立复算总数 172（吻合），**未重做逐站细分**（不重抄已证，纪律）。
- **`MissionClass`/`RadioClass` 构造器具体地址**：RTTI 链与 vtable 已证，但本卡未逐条定位其 ctor 入口（抽象基类无 push-size 分配点）；保留 `[静态推断]`。

## 3. 抽象基类 GetSize 桩的可比性
6 个抽象中间基类（AbstractClass/ObjectClass/MissionClass/RadioClass/TechnoClass/FootClass）GetSize 均为 `0x4C9150` 桩返回 0；本卡**无法**用分配点核对（它们从不直接实例化），这不是失败而是"不可比"。与 `kb/20 §0.2 作用域修正` 的 9 个抽象桩类（另加 AbstractTypeClass/ObjectTypeClass/TechnoTypeClass）口径一致。

## 4. 基线数字（纪律 1：先测基线）
- 静态 vtable 初始化链 `C7 05 <obj><vt>` 批量通道：345 写 / 245 个不同 vt / **243 解析出具名 RTTI（99.2%）**；2 个失败值 `0x807A68`、`0x80808080`（后者是 memset 常量，非 vtable）。
- 基线对照：200 个随机 4 对齐 `.rdata` 非 vtable 地址 → **1 个"解析出名"（0.5%）**。99.2% vs 0.5% ⇒ 判据特异，非"随便挑也过"。
- GetSize 双向 4/4、槽数 10/10、RTTI 名 10/10 的基线：上述 C7 05 通道 + `.rdata` 定界，均先经随机对照（0.5%）排除空判据。
