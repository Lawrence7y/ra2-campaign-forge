# S21-DIRECT · S21（战役流程）纯 direct 通道升格

## 盘上现态（Lead 实测）
`S21`：**n=129、named=91**（门槛 117，差 26）、**proved=26**（门槛 65，**差 39**）、`[静态推断]` **91 行**、`[未证]` 12。
⇒ 本卡**只做 proved**（不动名字、不动 subsystem）。

## 唯一判据：direct call
`E8 rel32`：① 在**指令边界** ② **`site+5+rel32==entry`** ③ **调用者 ≠ 本行体内**。

## ⛔ 严禁（已 4 次踩坑）
- `atexit` 析构器虚表（`push <dtor>; call 0x7C978A`）；
- 槽号匹配 / slot-baseline；
- `exact` 派发除非「静态 global + 构造器活 vptr + `vt[slot]==entry` + site 不共用」；
- 「P=R=100%」式判据自证。

## 强制自证
1. **扫描覆盖 `.text` 100%**（基准 **1,392,592 指令 / 68,253 `E8`@边界**），报实测值；交付站点须落在范围内。
2. **⑲ 自检**：capstone 5.0.7 无 `op.index`（`op.mem.index`，无 index 返 **0 非 None**）。
3. **⑨ 停机核验**：S21 = 129 行 / named 91 / proved 26 / `[静态推断]` 91。
4. **⑱ 按 entry 地址查全库冲突** —— 只报不改名。
5. **基线 + 差分**（新错源 B：随机基线对同源系统性错误零鉴别力）。

## 交付
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21_DIRECT\`：`PROGRESS.md`（≤50 行）/ `UNKNOWNS.md` / `EVIDENCE\` / `work\` /
`coverage_delta.tsv`（8 列，只放 direct 行，**只动 grade**）/ `VIRTUAL_SKIPPED.tsv`。
**开工 10 分钟内先落骨架；每 3–5 行增量落盘。严禁建 venv / pip install。**

## 核心数字
① direct 升格行数 ② 扫描规模与覆盖率 ③ 基线+差分 ④ `VIRTUAL_SKIPPED` 行数 ⑤ 并入后 S21 proved