# W29 · UNKNOWNS（静态未闭环项 + 最小取证设计）

> 原则：**做不到就写清楚，并给最小实验**，比编一个结论有用。以下均不影响 `OVERRIDE_ORDER.md` 的核心定谳（散装优先），但影响"端到端"与若干细节。

## U1 · 端到端：游戏是否真的采用散装 `ra2md.csf` 并改变 UI 文本
- **现状**：静态只到 `CCFileClass::Get_File` 的**分支顺序**与 `0x7346A0` 的**调用链**（[本次实测]）。没有运行期证据表明散装 CSF 真被读、 `" FSC"` 检查真通过、战役条 `Description=` 真从新标签取值。
- **等级**：`[待运行验证]`。
- **最小实验**：`OVERRIDE_ORDER.md` §4 的 **实验 A**（故意损坏的散装 CSF → 观察 `Unable to initialize 'ra2.csf'` 弹框）与 **实验 B**（完整 CSF + `DESC:MYCAMP` → 观察战役条简介）。A 是无需 UI 文本的强判据。

## U2 · CSF 的"MIX 内同名条目"究竟在哪一个 MIX / 哪个 CRC 名
- **现状（[本次实测]）**：
  - `ra2bench` 游戏目录**无散装** `*.csf` / `*.str`（`override_order.py` 尾部输出）⇒ 现运行态 CSF 必来自 MIX。
  - `langmd.mix` 未加密（flags=`0x0001`），索引布局 `4+6+10*12+bodySize+20 == filesize` 自洽、按**有符号 id** 升序；其条目 2（`id=0xBD835079`, `off=0x9930`, `size=332973`）起始处即 `" FSC"` CSF 魔数（绝对 `0x99B2`）⇒ **langmd.mix 内确有 CSF**。
  - 但 `crc32("RA2MD.CSF")=0x42CBEDCB` 与 `crc32("RA2.CSF")=0x0ADB1469` **都不在** `langmd.mix` 的 10 个 id 里（已试 12 个常见名，均未命中）。
  - `language.mix` / `ra2md.mix` / `ra2.mix` 的 flags=`0x0003`（`flags&2=1`，**加密**）⇒ 条目表无法明文读取，静态搜 `0x42CBEDCB` 全文 0 命中（`EVIDENCE/recon6_stdout.txt`）。
- **未闭环**：`0x7346A0` 请求的 `ra2md.csf` 到底命中哪个 MIX 的哪个 id；以及 `langmd.mix` 里那个 CSF 的真实文件名。可能解释：① 该 CSF 在加密的 `language.mix` 内；② MIX 条目名与 `"RA2MD.CSF"` 不同（语言变体/别名）；③ 我对 `0x7346A0` 名字构造的理解有未看到的分支（但 `0x7346F7`–`0x73474B` 的 `strchr`+截断+`strcat(".csf")` 已逐字节复核，可能性低）。
- **等级**：`[静态推断-弱]`（存在性确定）/ 具体对应关系 `[待运行验证]`。
- **最小实验**：在真机卡里对 `0x473D68`（`MixFileClass::Find`）下断，抓取 CSF 加载时的 `ecx`（名字）与命中的 `MixFileClass*` / 容器名（`[mix+0xC]`）；或用调试器在 `0x734777` 之后 dump `0xB13EB0` 缓冲（=实际请求名）与 `0x5B450D` 返回的 `ebp`。纯文件投放版本：实验 A 已能证明散装被优先，**不需要**先解决 U2。
- **重要**：U2 **不削弱**核心结论 —— 磁盘命中时 MIX 分支被跳过，散装 CSF **不需要 MIX 内存在同名条目**即可独立生效。

## U3 · `CCFileClass::Open` 与 `Get_File` 顺序相反的运行期后果
- **现状（[本次实测]）**：`Open`（`0x473C50`）先做 MIX 存在性探测（`0x473C8B`），再试磁盘（`0x473CA2`）；`Get_File`（`0x473D10`）相反。已论证 Open 的 MIX 探测是"无输出参数的可用性探测"，命中只置 `[esi+0x68]=1`，不设置 `[esi+0x58]` 缓冲。
- **未闭环**：`Read`（`0x473B10`）在 `Is_Available` 为真时走 `[esi+0x58]` / 磁盘句柄的精确分支语义；`0x47AAB0`（`Get_File` 两个尾部分支都调用它）的完整语义；`0x473E24`（MIX 未命中尾部）是否在某些 mode 下二次尝试磁盘。未逐分支展开。
- **等级**：`[静态推断-强]`（不影响"磁盘优先"），细节 `[待运行验证]`。
- **最小实验**：在 `0x473D2D` / `0x473D68` / `0x473E24` / `0x473E39` 四处下断，构造"散装存在 / 散装不存在但 MIX 存在 / 两者都不存在"三态，记录实际走到的分支与返回值。

## U4 · 多 `BATTLEMD*.INI` 冲突时的最终胜者
- **现状（[本次实测]）**：合并键 = `[Battles]` 条目名，`_stricmp`，同 ID 后装载者覆写（`0x46CE10`）；跨文件先后 = `FindFirstFileA/FindNextFileA` 枚举顺序。
- **未闭环**：引擎不保证该顺序；"NTFS 近似字母序 ⇒ `BATTLEMD98.INI` 通常胜出"只是 `[静态推断-弱]`。
- **最小实验**：投两个散装 `BATTLEMD01.INI` / `BATTLEMD02.INI`，同一战斗 ID 但不同 `Description`；在 `0x46CF60`（`call [edx+0x64]` 覆写点）下断记录覆写次序，或直接观察 UI 显示哪个值。

## U5 · `-CD` 参数 / CD 路径在运行期的真实语义
- **现状**：既有 `docs/re/fs_mix_load_chain_deep.md` §4 已给出静态链（`-CD` → `[0x89E410]` CD 路径链表 → 次级装载器二次 `FindFirstFileA`）；本卡复核 `[CD]/CDPath/InstallPath` 三编码 0 命中、`0x6BBFDB/0x6BC07C` 的 CWD 设置。
- **未闭环**：带 `-CD <dir>` 真机启动时 `0x47AFCF` / `0x47B08A` 的实际模式串、是否影响 CSF/INI 查找（静态推断：**不影响**）。
- **等级**：`[待运行验证]`（低优先，与 C 线无关）。

## U6 · `0x734990`（CSF 第二阶段）的完整语义
- **现状（[本次实测]）**：`0x7348BC` 以**同一** `0xB13EB0` 缓冲调用它（全 exe 唯一调用点），其内 `0x7349C2` 又一次 `Get_File`、读 `0x18` 头、检查 `" FSC"`、遍历 `" LBL"` 标签。已足以判定"单一 CSF 来源、无第二文件兜底"。
- **未闭环**：它是否重新打开同一文件、是否做增量/校验、失败时是否回退。
- **等级**：`[静态推断-强]`（单一来源），细节 `[待运行验证]`。

## U7 · 有界搜索的边界（防止把有限搜索写成全称证明）
- **搜索范围**：`gamemd.exe` 全 4,825,360 B；编码 = ASCII 精确 / ASCII 大小写不敏感 / UTF-16LE；检索对象 = 字面量 + 4 字节 LE imm32 xref + `E8 rel32` 原始调用扫描（`.text` 内、sync 无关）+ 指定函数体的 Capstone 反汇编。
- **未覆盖**：运行期动态生成的字符串（除本卡已定位的 `.csf` 拼接外）、经寄存器间接传入的地址、加密/压缩段、`blowfish.dll` 等外置模块、其它 `gamemd.exe` 版本。
- **反例校验**：`--selftest` N1/N1b（负控字节）、N2（MIX-first 反证）、N3（LIFO 反证）、N4（失同步反例）、N5（零命中≠不存在）、N6/N7（扫描器正控），8/8 PASS。
- ⇒ 本报告中所有"不存在 X"均为**上述范围内的有界结论**，不是运行期全称证明。

## U8 · MIX 加密条目表的静态不可读
- `language.mix` / `ra2md.mix` / `ra2.mix` 均为加密 MIX（flags&2=1），其条目表经 `PKStraw`（RSA+Blowfish，Blowfish 本体在动态加载的 `blowfish.dll`）解密。本卡**未**实现该解密，故这些 MIX 内的条目名/CRC 无法静态枚举。若真机卡需要精确清单，可用 XCC 类工具离线导出，或按 `docs/re/fs_mix_load_chain.md` §2 的公钥链复现（本卡不做）。
