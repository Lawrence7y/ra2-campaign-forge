# LEAD_VERIFY_W54（早期） · `.SAV` 是 OLE2 复合文档 —— 坐标系纠正 + 一个意外收获

> 记录人：Lead（本会话）｜ 时间：2026-11-13 22:35
> 来源：W54（Hy4）中途通报；其最终报告 `SAVE_DETERMINISM.md` 尚未交付。以下均为它 `[本次实测]` 且我认可的**结构性**发现。

---

## 1. 首要不变量：`.SAV` 不是平面字节流

`[转引·W54 实测]` 全部 8 份 `.SAV` 头 8 字节都是 `d0 cf 11 e0 a1 b1 1a e1` ⇒ **OLE2 / MS-CFB 复合文档**。
- `minor=0x003E`、`major=3`（512 B 扇区）、mini-sector shift=6（64 B）、mini stream cutoff=0x1000、header=512 B
- 内含 **15 个具名 stream**：`CONTENTS`（游戏状态）+ 14 个元数据流（`Version` / `Internal Version` / `Scenario Description` / `Player House` / `Start Time` / `Last Save Time` / `Play Time` / `Executable Name` / `Player Name` / `Player Name2` / `Scenario Number` / `Campaign` / `GameType` / `\x05SummaryInformation`）

`[签发·坐标系纠正]` **按 raw file 绝对偏移做逐字节比较是错的坐标系**：DIFAT/FAT 扇区位置随 `CONTENTS` 长度漂移。
`[本次实测]` 四份存档尺寸全不同：`1,405,384` / `1,382,212` / `1,382,156` / `1,366,595`。

⇒ **今后任何「存档字节比较」必须解析 CFB、按 stream 名比较**，不得用 raw offset。

---

## 2. 非确定性字段已定位（全部是同一个墙钟时间戳的副本）

`[转引]` 共 **68 个绝对字节**，全部由**同臂 diff 实证**，未凭猜测扩大：
- `Start Time` / `Last Save Time` / `Play Time`：三个 8 B FILETIME，**同一文件内三者相等**，跨趟不同（A1 = 2026-11-13 13:18:58.551 UTC，A2 = 13:21:19.060）
- `\x05SummaryInformation` 内 3 个 `VT_FILETIME` 属性（CreateDateTime / LastSaveDateTime / EditTime）
- CFB Root Entry 的 mtime（目录项 0 @ `0x6C`）
- 派生项：目录项 15 的 `CONTENTS` stream size、header `@0x2C` 的 #FAT sectors、DIFAT 里的 FAT 扇区号

`[我的评价]` 这个结论很干净：**非确定性来源只有一个 —— 存档时刻的墙钟时间**及其在 CFB 结构里的派生。这符合直觉（游戏不会把时间之外的东西随机化），也说明白名单**有界且可解释**。

---

## 3. 元数据平面现在可用；`CONTENTS` 平面仍不可用

`[转引]` **掩码后元数据平面完全相等**：`A1 == A2 == B1 == B2`，且 8 份样本全部与 A1 相等（**0 差异字节**）。
⇒ `[签发]` **「元数据平面」现在是一个可用的可比量。**

`[转引]` **但全文件掩码后 A1 ≠ A2**：仍有 **1,344,989** 个未掩码差异字节（首个 @abs 4352），原因：
- `CONTENTS` 是**长度可变、随游戏 tick 变化**的状态流（A1/A2 的 LCP = 0，**0 个相同的 512 B 块**）
- 四趟存档点 **frame 分别 2404 / 2408 / 2441 / 2412**，**未按 W45 规格要求的 ≤1 拍对齐**

`[W54 的处置，我认可]` **它没有写「存档字节等价成立」**，而是如实说「白名单对 full file 不足」。

---

## 4. 交叉臂结果：没看到超噪声的装包效应，但不足以判等价

`[转引]` `A1 vs B1` 掩码后差异 **1,344,847** 字节，与同臂噪声 **1,344,989** **同量级**
⇒ **没有观察到超出噪声带的装包效应**，但同样**不能据此判等价**（这正是 W45 判定「不可判」的同一逻辑）。

---

## 5. ★ 意外收获：`.SAV` 里的具名 stream 可解一个老缺口

`[我的判断]` 存档内含 **`Campaign`** / **`Scenario Number`** / **`Scenario Description`** / `GameType` 等具名元数据流。

这直接关系到 **W27 留下的一个未闭合项**：
> `Q3_load_selected = null`（存档列表框选中项读不出来）⇒ 当时只能说「加载了某份存档并进入游戏」，**不能证明加载的正是目标存档**。

`[签发]` **现在有了独立手段**：读存档内的 `Scenario Number` / `Campaign` / `Scenario Description`，就能**在游戏外证明某份 `.sav` 属于哪个战役/哪一关**。
⇒ `[建议]` 后续任何存读档验证，应当**读 `.SAV` 元数据流做身份核对**，而不是依赖 UI 选中项。这比 `LB_GETTEXT` 或首槽高亮可靠得多。

---

## 6. W54 给出的 W45 重跑三条硬前置（我采纳）

1. **用 `frame == N` 门限对齐存档点**（W45 `UNKNOWNS U6` 已记「Esc 菜单打开后 frame 冻结且四趟值不同」）
2. **改为 CFB stream 级比较**，而非 raw 偏移
3. **至少再取两份同 frame 的同臂存档**，重测 `CONTENTS` 平面噪声基线

---

## 7. 我不签发 / 保留

- 最终报告与白名单 JSON、diff TSV 尚未交付；我只认可上面这些结构性结论
- 「68 个字节」这个计数我**未独立复算**（需要 CFB 解析器）
- `CONTENTS` 流的内部结构（是否 LZO 压缩、是否有自身头部）**未解** ⇒ 即使对齐到同一 frame，两份 `CONTENTS` 是否应逐字节相等**仍未定谳**
- 四趟 frame 未对齐是**实验设计缺陷**（W45 的规格要求 ≤1 拍），不是 W54 的问题
