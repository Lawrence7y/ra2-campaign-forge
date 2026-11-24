# DISAGREE · W31 与任务书前提 / 既有措辞的分歧

> 状态：**已记录，不迁就** ｜ 2026-11-13 ｜ 纯静态只读

## 1. 弹窗文字与任务书字面不符（**任务书原串在 CSF 中检索不到**）

- 任务书与 W27 报告写作「**無法啟動選取地圖!**」。
- 官方 `ra2md.csf`（`langmd.mix` `entry[2] id=0xBD835079`，332,973 B，5,211 标签）中
  `MSG:UnableMapSelect` 的**精确文本**是 `無法啟始選取地圖！\n`：
  - `啟始` ≠ `啟動`
  - 全角 `！` ≠ 半角 `!`
  - 结尾有 `\n`
- 后果：用任务书原串 `無法啟動選取地圖` 检索 CSF 得 **0 命中**；本卡改用子串
  `無法啟始` / `選取地圖` 才定位到标签。`[本次实测]`（`s01` stdout）
- 处置：报告统一写**实际 CSF 文本**，并在 `WHY_MAP_FAILS.md` 标注差异；不把任务书字面
  当作引擎字符串。任务书方法第 1 步「检索『無法啟動選取地圖』」按字面执行会失败，
  本卡按「检索子串」完成，未改道 UTF-16LE（因为 CSF 确实命中了）。

## 2. 标签名形如 `GUI:xxx` 的前提不成立

- 任务书推测标签「形如 `GUI:xxx`」。实际是 **`MSG:UnableMapSelect`**（`MSG:` 前缀）。
- `GUI:Continue` 是结算屏**按钮**标签（`.data` VA `0x0081B438`），与错误弹窗文本不是同一条。
  `[本次实测]`（`s01`/`s02`）

## 3. 任务书「核心方法第 3 步」列出的候选判定，没有一条是实际失败点

任务书列举了「目标文件是否存在、地图头是否合法、theater 资源、战斗表登记、serial/序号、
EndOfGame 标记」作为回溯目标。本卡实测的判定链是：

1. Scenario 对象非空 → `Invalid Scenario pointer!`
2. battle/side 表查得非 NULL → `Invalid side!`
3. **`MAPSELMD.INI` 装载** → `Unable to initialize choices!` / `Failed to load MAPSELMD.INI`
4. **按当前地图名反查 `MAPSELMD.INI` 阶段表**（或 `SkipMapSelect=yes` 时按 stage 序号 +
   候选 `Scenario=` 字符串比对） → `Invalid stage!`
5. choice/font 对象分配 → `Unable to create font!`

实际触发点是 **第 4 步「`MAPSELMD.INI` 阶段树登记」**，不是目标文件存在性、地图头、
theater、战斗表登记或 `EndOfGame`。`EndOfGame` 在我方 `ECH02.MAP` 为 `yes`、
`ECH01.MAP` 为 `no`，均不参与此弹窗判定。`[本次读码]` `[本次实测]`
（W27 sandbox 两图 `[Basic]` 原文字节见 `s12` stdout）

## 4. 「`NextScenario` 推进」这一表述容易误导：默认配置下它根本不参与推进

- W27 sandbox 的 `ECH01.MAP` 显式写了 `SkipMapSelect=no`（W28 的 `basic_sections_dump.txt`
  里官方图的 `[Basic]` 是精简版、无此键，缺省亦为 0）。`[本次实测]`
- `SkipMapSelect==0` ⇒ `0x00685A40 je` ⇒ `call 0x005ADD10`，**`NextScenario` 缓冲区
  `[Scen+4]` 在这条路径上不被读取**；引擎改用 `[Scen+0x125C]`（当前图名）查
  `MAPSELMD.INI`。因此把「起不来」归因于 `NextScenario` 的写法/大小写/行尾/MIX vs 散装，
  在静态上都不成立。`[本次读码]` `[静态推断]`
- 这与 W28 的 `[形式相同]` 结论方向一致（不是写法问题），但**成因不同**：W28 的
  「推断 B：`Scenario=` 走文件系统、`NextScenario` 走 MIX/CRC 查找」本卡**不支持** ——
  两条路径都经过 `CCFileClass`（磁盘优先，`0x00473D10`），真正的差异是**是否进入
  `MapSelect` 状态机**。`[静态推断]`

## 5. 关于 `CCFileClass::Get_File = 0x473D10` 的命名

- 任务书称 `0x473D10` 为 `Get_File`（磁盘优先）。本卡复核 `0x00473D2D`
  `e8 de e1 fb ff` = `call 0x431f10`、`0x00473D32` `84 c0` = `test al,al`，字节与
  「磁盘优先」行为一致。`[本次实测]`
- 但 vtable `0x007E16B0` 实测：`+0x04=0x00401940`(GetFileName)、`+0x14=0x00473C50`、
  `+0x1C=0x00473D10`。并行卡 W33 把 `0x473D10` 称为 `CCFileClass::Open`、
  `0x473C50` 称为 `Is_Available`（先 MIX 后磁盘）。**这是命名差异，不是行为分歧**；
  本卡只引用「磁盘优先」这一已复核的字节事实，不卷入命名。`[本次读码]` `[转引]`

## 6. 本卡自身的一次被推翻的中间结论（如实保留）

- `s09` 曾据「`MAPSELMD.INI` 不在任何顶层 MIX 索引、也不散装」得出「文件缺失」的结论，
  **该结论是错的**：`ra2md.mix` 的 `entry[14] id=0xFBE0D09D` 是一个**嵌套加密头 MIX**，
  展开后 `[20] id=0x922B8CE7` 正是 `MAPSELMD.INI`（5,573 B）。
  `s10`/`s11` 已独立复核；`s09` 原始 stdout 保留不改，另附
  `EVIDENCE\CORRECTION_s09.md`。`[本次实测]`
- 副作用：`zlib.crc32("MAPSELMD.INI")=0x922B8CE7` 与真实 MIX 实测 entry id
  **交叉核对成立**（只是要下钻一层嵌套 MIX），满足任务书的 CRC 纪律。

## 7. 与「不要迁就」相关的边界

- 本卡**未**启动 `gamemd.exe`、未 attach/读活进程、未写 `ra2youli`、未写仓库
  `ra2forge/`、未改 W21–W30 任何目录、未做 git 写操作。
- 本卡**未**把 `ra2forge/mixlib.py` 的实现当作引擎行为证据：仅在 `s09`/`s10`/`s11`
  用它**解码 MIX 索引**（工具），CRC 一律自行用 `zlib.crc32` 计算并与真实 entry id 对照。
- 结论中凡引用并行卡 W33 的部分标 `[转引]`；本卡独立复核过的部分标 `[本次实测]`/`[本次读码]`。
