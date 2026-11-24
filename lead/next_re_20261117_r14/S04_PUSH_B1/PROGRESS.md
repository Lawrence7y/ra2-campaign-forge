# S04-PUSH B1 — PROGRESS

- 批次 B1 = S04 前 18 行（entry 升序），输出目录 `S04_PUSH_B1\`。
- 判据：D-40 四环，②与④须独立证据链；③只认③b；余量仅 6 行，宁严不宽。
- 目标只读，SHA-256 现场一致；capstone 5.0.7 skipdata=True。
- 骨架/delta 表头/base_rate 骨架开工先落；随后逐行核、逐行落盘 EVIDENCE。
- 计数口径：核完行 / 四环齐全（严格 D-40）。

## 进度（每 5 行追加）

### checkpoint @ 5 行（00407550 … 00474810）
- [x] 5 / 18 已核；4 行 EVIDENCE + 1 行（00407550 ③无 falsifiable）落盘。
- 观察：5 行 entry 作为 4B VA 全镜像 dword 命中均 0（无虚表槽）；direct caller 均真实边界 E8。四环齐全 0。
- 四环齐全累计：0。

### checkpoint @ 10 行（… 004767C0）
- [x] 10 / 18 已核；EVIDENCE 累计 10 份落盘。
- 观察：00475D70 体内有 `TypeList<int>`/`VectorClass<int>` 局部对象 vtable 写（7 处），但非本函数 this 的 vptr 安装；调用方窗口有 4 处 ecx handoff 候选，留待手工反汇编复核。四环齐全仍 0。
- 四环齐全累计：0。

### checkpoint @ 15 行（… 0048DF80）
- [x] 15 / 18 已核；EVIDENCE 累计 15 份落盘。
- 观察：无新增虚表槽命中；③b② 站点普遍成立（falsifiable 0/-1，eax 陷阱未触发）。四环齐全 0。
- 四环齐全累计：0。

### 收尾（16–18 行 + 咽喉复核）
- [x] 18 / 18 已核；EVIDENCE 累计 18 份落盘。
- [x] 咽喉复核：
  - verify2 全镜像 dword 扫描：18 行 entry 命中 0。
  - verify5/verify8：所有行 `mov [this],vt`=0；00475D70/00476B20 的 ecx handoff 候选经反汇编证伪（属相邻另一 call 的实参，非交付本行 this）。
  - verify6：仅 0051FB00 引用全局 0x87F7E8（多态别名 + 单点，不满足 §8.8/D-42）。
  - verify7：direct caller raw==boundary，全部真实边界 E8，但 direct-only 不足。
- [x] delta 0 行（仅表头）；base_rate、REPORT 定稿。

## 最终计数
- rows_checked = **18**
- all_four_rings = **0**
- delta 行数 = **0**
- 决定性缺环：②类身份（全 18 行 未取得）；④ 亦仅 direct-only。
