# S03-C3 · 按 **D-40** 补齐环③（**只做 7 行，不扩面**）

> ⚠️ **本卡的每一行都已由独立审计确认「只差 ③ 落笔」** —— 字节级证据已在审计 VERDICT 里给出，你的活是**把 ③ 写成可核查的合同**，不是重新普查。

## D-40 的 `[已证]` 最小环集（`lead\PENDING_DECISIONS.md`）
**① 入口 + ② 类属/身份 + ③ 整体合同 + ④ 使用见证，任一缺不得升。**
- **③ = 「这个函数整体做什么」** —— 读什么、写什么、返回什么、调用约定、错误路径。
- **③ 不可被「某处写了个字段」顶替**（那是当年 31 行虚高的根因）。
- 「清零 + 置默认值」这类**机械可述只算 P，不算 ③ 闭合**。

## 工作面：7 行（**以盘上为准自己核**）
| entry | 盘上 subsystem | 盘上 grade | 盘上 name |
|---|---|---|---|
| `0065CAC0` | S03 | `[静态推断]` | `RawFileClass::slot2` |
| `004324B0` | S03 | `[静态推断]` | `CDFileClass::vslot10` |
| `00552490` | S03 | `[静态推断]` | `LCWStraw::slot2` |
| `006C9890` | S03 | `[静态推断]` | `FileStraw::slot1` |
| `00631CC0` | S03 | `[静态推断]` | `FilePipe::slot3` |
| `0065D150` | S03 | `[静态推断]` | `CDFileClass::slot3` |
| `00431E80` | S03 | `[静态推断]` | `BufferIOFileClass::vslot2` |
🔑 **审计已给的三条 ③ 线索（`S03_CRITERION\PROGRESS.md` §5，可直接引用但须自己复核字节）**：
- `0065CAC0`（`RawFileClass::slot2`）= **free 旧句柄 → `fopen`(`0x7D5408`) → 复位 `[+0xC]`/`[+0x10]` → 失败走 `vt+0x40`(`0xC,0,name`)**
- `004324B0`（`CDFileClass::vslot10`）= **`Seek(pos,origin)`：夹取 `[0,[+0x48]]`、按 `[+0x34]`/`[+0x3C]` 缓冲窗换算 `[+0x38]`、跨窗 call `0x431DD0` / `vt+0x28`**
- `00552490`（`LCWStraw::slot2`）= **`Read`：循环 `memcpy`(`0x7CA090`) + `[+0x10]` 剩余 + 按 `[+0xC]` 分支重填**
⚠️ 另 4 行（`006C9890` `00631CC0` `0065D150` `00431E80`）审计只给了「只差 ③ 落笔」的判定，**没给具体线索** —— 要你自己从字节读出来。

## 每行必须产出（缺一不可）
1. **③ 整体合同**：用 2–4 句说清「它整体做什么」，**必须带指令偏移**（如 `+0x09 895E10` / `+0x16 E8…`）。
   审查标准：一个没看过这函数的人读完你的描述，能预测它对内存/全局的影响。
2. **④ 使用见证**：direct call（`E8` 指令边界 + `site+5+rel32==entry` + 非自环）**或** 活 vtable 槽位派发（构造器装的活表 + `vt[slot]==entry` + site 不共用）。给站点地址。
3. **② 类属**：RTTI 链 `[vt-4]=COL → [COL+0xC]=TD → TD+8 内联串`；**读不到 fail-closed 停下，不许猜**。
4. **新语义栏全文**（要替换盘上那一栏）：**不得**再出现「槽语义未证」「弱信号」「线索」「未定」等字样。

## ⛔ 严禁（本项目已因此回退 53 行）
- **不得只靠 direct call 就声称 `[已证]`** —— D-40 明写 ④ 单独不够；
- `atexit` 析构器装的虚表（`push <dtor>; call 0x7C978A`）不是活 vptr；
- 「entry 在自己虚表里是第 K 槽」的槽号匹配 / slot-baseline；
- 「P=R=100%」「恰命中 N」式判据自证；
- **随机基线必须按「同子系统内随机取同样多行」算**（S21 实测 35.66%；按「随机 VA 命中 target」算出的 0.166% 是**地址算术**，对语义零信息）。

## 强制自证
- **⑨ 停机核验**：盘上 n / grade / name 自己重算（数值见上表）。
- **⑲ 自检**：capstone 5.0.7 无 `op.index`（`op.mem.index`，无 index 返 **0 非 None**）。
- **扫描覆盖 `.text` 100%**（基准 **1,392,592 指令 / 68,253 `E8`@边界**，以 **VirtualSize** 为准；扫到 SizeOfRawData 会多 1,594 条零填充）。
- **⑱ 按 entry 地址查全库冲突**（`docs\re\` + `re_atlas\kb\` + 台账 + `COVERAGE\`）—— 只报不改名。
- **`§8.5`**：`docs\re\` / `re_atlas\kb\` / 台账**不得作名字的第二条通道**。

## 交付（绝对路径，只写这里）
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C3\`
`PROGRESS.md`（≤50 行，**第一行写「补齐几行 ③」**）/ `UNKNOWNS.md` / `DISAGREE.md` / `EVIDENCE\` / `work\`
`coverage_delta.tsv`：8 列 `entry, subsystem(S03), name, one_line_semantics, grade, evidence_path, name_kind, 旧grade→新grade`
  （**name 保持盘上现值不动**；只改 semantics + grade）
**开工 10 分钟内先落骨架；每完成 1–2 行增量落盘。严禁建 venv / pip install / import 其他卡 work 代码。**

## 核心数字
① 补齐 ③ 的行数（目标 7）② 每行的 ③ 摘要 + 指令偏移 ③ 每行的 ④ 站点 ④ 若某行补不出 ③，写清缺什么（**如实交 0 算合格**）