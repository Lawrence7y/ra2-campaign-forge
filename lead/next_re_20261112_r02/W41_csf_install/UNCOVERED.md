# UNCOVERED · W41（CSF 纳入安装/备份/卸载链路）未覆盖与不确定项

> 状态：**离线实现 + 回归已闭环**；真机行为**未验证**（由 W40 负责）。
> 日期：2026-11-13 ｜ run_id = `NEXT_RE_20261112_R02`
> 分级：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` / `[待运行验证]`

---

## U1 · 真机 CSF 覆盖行为（核心，本卡不碰）

`[转引]` W29 静态结论 + `[转引]` W30 `UNCOVERED.md §2`：散装
`ra2md.csf` 是否真的优先于 `langmd.mix` 内同名条目、是否真把
`BATTLEMD98.INI` 的 `Description=RA2F:...` 解析成文本而不是
`MISSING:'RA2F:...'`、以及引擎 `0x734799` 的 `" FSC"` 检查 /
`0x6BD85A` 的 `Unable to initialize 'ra2.csf'` 弹窗，**本卡未启动游戏、
未 attach、未做任何进程级验证**。本卡严格遵守纯离线红线。

因此：

- 本卡**不写「CSF 功能可用」**，也不宣称「装上就能进游戏」。
- 本卡只保证：写进游戏目录的 `ra2md.csf` 是**完整合法 CSF**（含全部
  5,211 个官方标签），且安装/备份/卸载链路在**离线文件系统层面**正确
  （CREATE / verify / DELETE / 逐字节还原 / 冲突零写入）。
- `[待运行验证]` 「装了完整克隆 + 追加标签的散装 csf 后，引擎能正常启动且
  战役描述显示为文本」——归 W40。

---

## U2 · 完整性守卫的作用域（重要边界，别扩大引用）

`[本次读码]` 强制守卫 `csf.assert_complete_csf()` 的调用点是：

1. `builder._emit_csf_artifacts()` 的每一处写出（含 `csf_out` 与包内
   `ra2md.csf`）都走 `write_csf(..., require_complete=True)` /
   `append_or_set_label(..., require_complete=True)`，并在末尾对最终产物
   再做一次 `assert_complete_csf()`；
2. `csf.write_csf()` / `csf.append_or_set_label()` 的 `require_complete`
   参数**默认 `False`**。

⇒ **低层 `csf.write_csf(path, minimal)` 仍能写出最小 CSF**。这是**刻意的**：

- W30 的 `CSF1/CSF3/CSF4` 故意用 `create_csf()` 造 1–3 标签的最小 CSF 来测
  读写/追加/边界能力，任务书要求「不得削弱既有 51 例」，若把守卫无差别
  塞进 `write_csf()` 默认路径会直接打断这些用例；
- 与 W34 `mapselmd.validate_official_base()` 的分层一致：守卫在**产出安装
  产物**的编排层强制，而低层原语保持通用。

`[静态推断]` 因此「任何绕过 `builder`、直接 import `ra2forge.csf` 调用
`write_csf()` 的第三方代码」不受本守卫约束。本卡的保证边界是
**`ra2forge` CLI / `install` 链路产出的 `ra2md.csf`**，不是整个
`csf.py` 模块的任意调用。引用时不得把 U2 扩大成「csf.py 永远写不出
最小 CSF」。

---

## U3 · `--allow-csf-out-in-game` 会产生未登记孤儿文件（W21 风险）

`[本次读码]` 该危险开关（默认关闭）是「显式确认」通道：给了它，
`--csf-out` 可以直写游戏目录。它**绕过 install 的
preflight/备份/清单**，所以：

- 写进去的 `ra2md.csf` **不在 `ra2forge_install.json` 里**；
- 随后的 `uninstall` **不会删除它**（W21 孤儿文件同一类风险）；
- `[本次实测]` `CSF_INST4` 已证明该路径仍产出完整合法克隆（5,212 标签、
  基线 5,211 齐全），且 `BUILD_REPORT.txt` 打了 `[WARN]` 明示上述风险。

`[静态推断]` 建议：生产上不要用这个开关；正确通道是
`build --install <dir>` / `install --package <pkg> --game <dir>`，
它把 `ra2md.csf` 走完整链路（`CSF_INST2` 已证明卸载逐字节还原）。
若确已用该开关直写过，需**手工**移除那个散装 csf（见 `APPLY.md §5.3`）。

---

## U4 · 守卫比「标签名集合」，不比值内容 / 不锁官方 SHA

`[本次读码]` `assert_complete_csf()` 的官方基线检查是 **case-fold 后的
标签名集合 ⊇ 5,211 个官方名**，另加魔数/版本/计数/值类型四类结构检查。
它**不**检查：

- 每个标签的**文本值**是否与官方一致（例如把 `MSG:UnableMapSelect` 的
  文本改坏但保留标签名，仍会通过守卫）；
- 精确的官方 `sha256`（其他语言版本 / 合法改过值的完整官方克隆允许通过，
  与 W34 `validate_official_base()` 对 user-supplied base 不锁 SHA 的策略一致；
  **内置**基线本身则锁死 `size + sha256`）。

`[静态推断]` 这是「防最小/部分 CSF 导致启动失败」的针对性守卫，不是
「防篡改/防恶意内容」的完整性校验。W30 `append_or_set_label()` 的
`verify=True` 逐标签往返校验保证了**我们追加的那一条**不改坏既有标签，
但「用户自备的 `--csf-base` 是否字节可信」不在本卡能力内。

`[转引]` case-fold 比对依据：CSF 标签在引擎里大小写不敏感
（`csf.get_label(case_insensitive=True)` / `append_or_set_label` 均有该参数）。
若某语言版官方 CSF 的标签名**大小写不同**也仍被接受；若某天出现
标签名本身增删的版本，会被判 PARTIAL 而拒 —— 属保守拒绝，需重新提取基线。

---

## U5 · 游戏目录判定与别名/跨平台

`[本次读码]` `_csf_out_ownership_guard()` 用「目录含 `gamemd.exe`」判定游戏
目录（与 `install.preinstall_plan()` 一致），并检查显式 `--install` 目录
+ `--csf-out` 的所有祖先。

`[静态推断]` 边界：

- 一个**没有** `gamemd.exe` 的游戏目录（精简安装 / 判定文件被改名）不会被
  识别为游戏目录，守卫不触发；
- Windows junction / 目录符号链接 / 大小写别名等 reparse point 形态未做
  `realpath` 级 anti-alias 复核（只对 `--csf-out` **目标本身**做了
  `is_symlink()` 拒绝）；`install` 链路自身有更完整的
  `_dest_safety_error` / `_slot_namespace_errors` 别名门，但 build 侧守卫
  没有复用那一整套（`[本次读码]`）。
- 非 Windows 平台的 POSIX 只读行为、`WinError 32` 锁句柄、`SIGINT`
  异步中断沿用 `[转引]` W26/W30 既有未覆盖项，未独立实测。

---

## U6 · 拒绝时的「零写入」边界（已收紧，但仍说明）

`[本次读码]` 针对 `--csf-out` 落在游戏目录内的情形，守卫被移到 `build()`
**第一个文件系统写之前**（`design_mod.validate()` 之后、`out.mkdir()` 之前），
所以拒绝时连包输出目录都不会创建 → 整个 build 零写入。
`[本次实测]` `CSF_INST4c` 断言「游戏目录 `sha_tree` 逐字节不变 + 目标文件
不存在」，`CSF_INST4c2` 断言「包输出目录 `out_inst4/` 也不存在」—— 二者
共同证明拒绝时整个 build 零写入。

`[本次读码]` install 侧的 definite conflict 拒绝发生在 `preinstall_plan()`
（只读分类）之后的 `install_package()` 开头，位于 `---- first filesystem
write happens below ----` 之前；`[本次实测]` `CSF_INST3e` 用
`sha_tree(game)` 逐字节证明了零写入。

---

## U7 · `--csf-base` 是只读输入，不在归属守卫内

`[本次读码]` 归属守卫只管**写目标** `--csf-out`（以及显式 `--install` 目录）。
`--csf-base` 只是被 `read_csf()` 读取的源，`builder` 从不对它写入，因此
没有为它做「落在游戏目录内」判定。`[静态推断]` 一个恰好位于游戏目录内的
`--csf-base`（例如用户拿游戏目录里的散装 csf 当基底）会被**读取**并通过
完整性守卫后克隆到 `--csf-out`；这不会写游戏目录，但会把游戏目录里那个
文件的内容带进构建产物 —— 属用户显式指定，未额外拦截。

---

## U8 · 未提供的开关（明确记录，避免被当成遗漏）

- `[本次实测]` **没有** `--allow-partial-csf`：遵循任务书「不建议」。
  唯一路径是「基于官方基底克隆」，`--allow-partial-csf` 若存在会重新
  打开 W29 的启动失败风险，故不实现。
- `[本次实测]` `--allow-csf-out-in-game` 是**路径归属**开关（默认关闭、
  需显式确认 + 目标身份判定），与「部分 CSF」无关；它不能产出部分 CSF
  （`CSF_INST4e` 证明显式路径仍受 `require_complete=True` 约束）。

---

## U9 · 继承项与未独立复跑项

- `[转引]` W30 `UNCOVERED.md §3`（未知 CSF 值类型跨记录边界）、§4
  （`mixlib.write_mix()` 仍用旧 `crc_hash()`）、§5（非 Windows 等）全部
  沿用，本卡未改 `mixlib.py`、未碰 `write_mix()`。
- `[转引]` W34 `UNCOVERED.md` 关于 MAPSELMD 的未覆盖项沿用，本卡
  `mapselmd.py` 逐字节未改。
- `[待运行验证]` 全部「引擎是否真的接受」类问题 → W40。
- `[本次实测]` 本卡 57/57 用例全部在 `W41_csf_install/sandbox/` 的
  inert 游戏目录（`gamemd.exe` 是纯占位文本，从不执行）里跑通。
