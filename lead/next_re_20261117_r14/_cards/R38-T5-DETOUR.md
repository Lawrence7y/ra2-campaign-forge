# 卡 · R38-T5 · 本镜像的 `.detour` 节：它是什么，是否动摇 `F29` 的结论

## 〇 · 你是谁、做什么

你是**执行员**（负责实际字节工作）。上一轮证实 `0x7E11C8` = KERNEL32 `InterlockedIncrement`（Hint=432），
同时发现本镜像多出一个**非标准 `.detour` 节**（VA=0x793000 / raw=0x497000 / vsize=0x2718 / rsize=0x3000），
并断言「导入布局非原版」。**这个断言现在只有「多了一个节」这一条证据，没有内容级分析。**

你的任务：把 `.detour` 节读清楚，判定它**是否动摇** `F29` 的结论。

只读源文件；产物只写 `lead\next_re_20261117_r14\R17_R70_T5_DETOUR`（不存在就建）。
**禁止修改** `R14_COMMON.md` / `LEAD_LOCK` / `GOAL_THREE_TARGETS_20261018.md` / `STATUS_BOARD.md` / `BOARD_ARCHIVE.md` / 任何 `FACT_INDEX.tsv`。

## 一 · 要回答的 5 个问题

**Q1 · `.detour` 节里到底有什么？**
节头全字段（Name/VirtualSize/VirtualAddress/SizeOfRawData/PointerToRawData/Characteristics）。
节内 10,008 字节（vsize）的**结构画像**：多少非零字节、是否含可读 ASCII 串（列出所有长度 ≥6 的串）、
是否有明显的函数序言（`55 8B EC` / `83 EC`）或 ret 结尾。

**Q2 · 导入描述符（ILT/IBN）是否真的落在 `.detour` 里？**
上一轮 T1 报告说「`.detour` 节承载 ILT 与名字区」。请独立核：
`Import Directory RVA = 0x7955C0` 落在哪个节？各 `IMAGE_IMPORT_DESCRIPTOR` 的 `FirstThunk`（如 KERNEL32 的 `0x3E10D0`）落在哪个节？
`IMAGE_IMPORT_BY_NAME`（如 `0x7941F0` 的 `InterlockedIncrement`）落在哪个节？**逐项给出节名。**

**Q3 · 这个镜像是否被改过？（只给可核事实，不下定性结论）**
列出你能**机械判定**的「非标准迹象」清单，每条附证据：
例如节数与标准 4 节的差异、`.detour` 这个名字是否出现在标准 MSVC 链接产物中（若你无法判定，写「无法判定」）、
`TimeDateStamp`、`CheckSum`、节表是否按 VA 升序排列、是否有节重叠。
**不要**推断「谁改的」——只列事实。

**Q4 · 这对 `F29` 的结论有没有影响？**
`F29` 现在的结论是：`0x6C2AC0` 处 `call [0x7E11C8]` 是对 `[this+4]` 的 `InterlockedIncrement`（AddRef），
且 `0x7E11C8` **经导入表证实**为 KERNEL32 的该函数。
请判：`.detour` 的存在是否让「导入名 `InterlockedIncrement`」这一步变得不可信？
（提示：导入名是**明文 IBN 字符串**，与节叫什么名字无关。）
给出：**不影响 / 影响（说明）**，并说明理由。

**Q5 · 正控（必须做）**
另取**一个标准节**（如 `.data`）做同样的结构画像（前 64 字节 hex + 是否含 ASCII 串），
用来对比说明你的「节画像」程序在两个节上都能给出合理输出。

## 三 · 纪律

1. 禁止用「按字节扫 E8/C3/C2」当函数入口判据。
2. 地址一律 `0x` 前缀大写十六进制；offset 用 `0x`+小写或大写要统一并在报告里声明。
3. 每个结论给可复算依据（文件偏移 / RVA 换算 / 原始字节）。
4. 取不到写「未取得」，**严禁编造**；**不要**对「谁改的 / 为什么改」做定性推断。

## 四 · 交付格式（严格照此，中文，纯文本，写进你目录的 `REPORT.md`）

```
Q1 | .detour: VA=0x.. vsize=0x.. raw=0x.. rsize=0x.. ; 非零字节=?/? ; ASCII串(<6字以上)=<列表> ; 函数序言迹象=<有/无>
Q2 | Import dir 0x7955C0 -> 节=? ; KERNEL32 FirstThunk 0x3E10D0 -> 节=? ; IBN 0x7941F0 -> 节=?
Q3 | 非标准迹象: ①<...> ②<...> ... | 无法判定项: <...>
Q4 | 对 F29 的影响: 不影响 / 影响 | 理由: <...>
Q5 | 正控节 <..> 前64字节=<hex> ; 含ASCII=<?> ⇒ 画像程序可用
OVERALL | <一句话：.detour 是什么性质、要不要在 F29 里保留「非原版」这条限定>
```

最后加 `## 复算脚本`。
