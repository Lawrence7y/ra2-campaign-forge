# _lb_VERIFY.md — 合订本逐字照抄核验与纪律自检（2026-11-09）

> 本件记录「草案正文逐字照抄」的实际核验命令与输出，以及铁律自检结论。
> 所有命令均在本会话以 `python -I -X utf8`（绝对路径 / 内联 -c）实跑；未跑的项不记「通过」。

## 1 逐字照抄核验（5 段正文 × 源件标记区）

**核验命令**（本会话实跑，输出见 §2）：

```
cd /d/Project/ra2-campaign-forge && python -I -X utf8 -c "<内联脚本>"
  逻辑：对 5 份单件草案件，取 `## ↓↓↓ 草案正文…` 与 `## ↑↑↑ 草案正文结束…` 两标记行之间的行；
        在合订本 `_lb_BOUND_VOLUME.md` 中按章节序号定位「#### ↓↓↓ 草案正文（逐字照抄…）」块，
        取对应块内文本，逐字节比较（str ==，源件与合订本均 newline='' 读取，保持 LF）。
```

**输出（最终构建后）**：

```
VERBATIM_OK 1 §605 bytes=4735
VERBATIM_OK 2 §606 bytes=4097
VERBATIM_OK 3 §607 bytes=4894
VERBATIM_OK 4 §608 bytes=6318
VERBATIM_OK 5 §609 bytes=8388
ALL_VERBATIM = True
```

- 注意：首次构建时 Python 文本层把 `\n` 翻成 `\r\n`（源件为纯 LF），核验判 FAIL；已把 `_lb_build.py` 改为 `sys.stdout.buffer.write(...encode('utf-8'))` 二进制写 stdout，重跑后合订本 `CRLF=0 / LF=288`，5 段全部 `VERBATIM_OK`。**最终件为修复后版本**。
- 5 段抽取段指纹（`_lb_fp_out.txt` BODY 行，hashlib 实算）：
  - §605 `5c37adc6e64dd245b3392ed554a2185b489ab683496b9b223b6622af4bc86a6c` / 4735 B
  - §606 `030f5a62328ec661c814f531ff5e54f43db2ac7c8cbd88d4e8d1050c9961bdc6` / 4097 B
  - §607 `e9842d41f27d70b80067c5a6b89afe81ab63eb0422c7eda741d1c5983a3df698` / 4894 B
  - §608 `24a497e8f63aece592a7a863cdb7d03a93d438dfa3f657dba1c1aaca260b775b` / 6318 B
  - §609 `f4c3433a0141afbc59da7b72fdf679aacbae8b0ed9276530089a6a6528501682` / 8388 B

## 2 绑定行格式核验

**核验命令**：

```
python -I -X utf8 -c "import re; b=open(...,newline='').read();
  bl=re.findall(r'被核对象 SHA256 = ([0-9a-f]{64})，字节数 = ([0-9]+)',b); print(len(bl),bl)"
```

**输出**：`BINDING_LINES = 5`，5 行均为「被核对象 SHA256 = <64 位十六进制>，字节数 = <数字>」，中间无路径/括号/星号/反引号/空格；对应值 = 5 份单件草案件编排方基线指纹与字节数（7806 / 6714 / 7703 / 10080 / 18980）。

## 3 编排方基线指纹 11 件（开工 + 收尾两次实算）

- 开工：本会话 `python -I -X utf8 -c "...hashlib..."` 内联批跑 11 件，输出逐件 `OK` + 完整 64 位 SHA + 字节数。
- 收尾：`_lb_build.py` stderr 段 `=== BASELINE 11 (hashlib) ===` 再次 11/11 `OK`（`_lb_fp_out.txt`）。
- 两台账 `=== TAIL ===` 段复算：`PENDING` = `3765eddb…` / 52419 B、`GOAL` = `2baa0de4…` / 759518 B，与编排方基线逐位一致 ⇒ **台账零改动**。
- `git log -1` = `2657458`（本会话实查），无新提交；`git status --short` 两件仍为会话开始时的 `MM` 状态（Leader 既有改动），本任务未再写入。

## 4 铁律自检

| 项 | 结论 | 依据 |
|:--|:--|:--|
| 零真机 | 通过 | 未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存 |
| 零采样代码 | 通过 | 未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析 |
| 绝对只读 | 通过 | 两台账 + 5 个只读源域全程 Read/grep/hashlib，未改一字（收尾指纹同值） |
| 唯一写域 | 通过 | 全部新增落在 `lead/ledger_bound_20261109/`，前缀 `_lb_` |
| 草案正文逐字照抄 | 通过 | §1 `ALL_VERBATIM = True`（修复 CRLF 后） |
| 绑定行格式 | 通过 | §2 `BINDING_LINES = 5`，格式固定 |
| 不替 Leader 决定顺序 | 通过 | 第五区通篇「建议/宜/留 Leader」，Q1–Q7 列前置问题不代裁 |
| 不 commit / 不 push | 通过 | `git log -1` 未变 |
| Python 纪律 | 通过 | 一律 `python -I -X utf8` + 绝对路径；指纹用 hashlib |

## 5 本写域产出清单（最终）

| 文件 | 字节数 | 说明 |
|:--|--:|:--|
| `_lb_BOUND_VOLUME.md` | 60272 | 合订本正文（最终，纯 LF；SHA256 = `7770da46b5c684add476ec286673d70d73f332fb5ac286d07cabcdaadc4eac43`） |
| `_lb_build.py` | 36779 | 构建脚本（print-only，binary stdout；stderr=指纹；散文段排版归一化用占位符保护 5 段正文） |
| `_lb_fp_out.txt` | 2141 | 11 件基线 + 5 段 BODY 抽取指纹 + 两台账 TAIL 复算 |
| `_lb_VERIFY.md` | 本件 | 逐字照抄核验与纪律自检 |
| `_lb_verify_print.py` | 本脚本 | 生成本件的 print-only 脚本 |

> 注：附录 B 列的是合订本产出 4 件；本 `_lb_verify_print.py` 为核验辅助脚本，一并落在写域，前缀 `_lb_`。
