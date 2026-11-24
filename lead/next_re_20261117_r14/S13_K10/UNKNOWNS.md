# S13-K10 UNKNOWNS — 未升级行与剩余问题

## 63 行仍 [静态推断]（原 106 行内）
- 这 63 行中多数是**非容器模板槽**：BombClass/BulletClass/WeaponTypeClass 等具体类的 slot5/6/10/13/...（如 00438A90、0046AE70、0075E0C0、00772CD0 等）。其体内合同含多个业务调用，无法用单一「读/写/返回」谓词互斥定名（例如 slot13 是 Load/Save 系列，slot5 是 Load 系列，需配对 INI 键名才能具名——超出本卡任务面）。
- 另有 0040F5E0（DynamicVectorClass<WarheadTypeClass*>::Clear）：字节合同明确，但 KICKOFF_R14_SUCCESSOR_3.md 标记 ④误绑（幽灵被调），按「四环缺一即不可升」保留 [静态推断]。
- 其余为 slot2=SetCapacity 的具体类（0040B740 等 Vec 版），K8 已把 DynVec 版升 [已证]，Vec 版本卡合同也吻合，但 K9/K8 的 exact 绑定只覆盖 DynVec 版；为避免 slot-baseline 嫌疑，本卡未纳入升级（可在后续卡补 exact 站点后升）。

## 仍待裁/未解（非本卡任务面）
- 名称归属与 K6 相同但 K6 被审计 FAIL：本卡用独立字节合同通道复证，审计需确认这是否构成 ⑰ 合格的「两通道各自提供对方给不出的信息」。
- D-37 未裁：这些行仍记 S13，不改分母/不改归属；模板实例是否应归 S22 由合卡员裁决。
- 0040F5E0 的幽灵被调是否已影响 K8 的 18 行 [已证]（其中不含 0040F5E0）：无直接影响；但同型风险提示后续卡需复查所有「exact」标签。