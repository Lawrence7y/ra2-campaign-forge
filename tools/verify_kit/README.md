# verify_kit · 操作验证工具包

配套三件套：

- 操作流程：`skill/verify-workflow/SKILL.md`
- 派卡模板：`docs/re/dispatch/VERIFY_CARD_TEMPLATE.md`
- 本工具包的自测证据（2026-10-03 实录）：
  `out/re_work/work_chain/CONTINUE_20261003/lead/verify_kit/VERIFY_KIT_REPORT.md`

全部脚本只用 Python 3.12 标准库。**运行口径**：`PYTHONDONTWRITEBYTECODE=1` +
`python -B`，本包不得在任何目录产生 `__pycache__` / `*.pyc`（import 枚举落 pyc
会污染零写入证明——EXP001-H 实例）。所有落盘经 `_vk_io.py` 单点写出
（规范化路径、拒绝 `..` 上行），输出文件的父目录必须已存在。

## 文件清单

| 文件 | 作用 |
|---|---|
| `snapshot.py` | 目录快照：相对路径 + 字节数 + mtime_ns + sha256 → JSON |
| `diff_snapshot.py` | 比对两份快照，输出新增/删除/内容变化/仅 mtime 变化 + 明确 zero-writes 结论 |
| `boundary_scan.py` | 在脚本/命令清单里查被禁 API 词元（词表可配置，自引用字面量可掩码） |
| `run_rc.py` | 独立采集退出码：输出、退出码、命令原文分三个文件，退出码不内嵌输出 |
| `_vk_io.py` | 内部落盘 helper（上列工具共用，不单独调用） |
| `selftest/run_selftest.sh` | 负控全套一键自测（26 条断言） |

## run_rc.py · 独立退出码采集

为什么需要它：`vrepo/raw/03_validate.txt` 第 2 行就是反例——退出码以
`__EXIT_CODE=0` 内嵌在输出文件里、由同一进程自述，ACCEPTANCE.md L36 定性为
"零个独立 `.exitcode` 件……跨包不可比"。本工具把**输出**与**退出码**分成两个
文件，由 runner 落盘，子进程无法自报家门。

```bash
export PYTHONDONTWRITEBYTECODE=1
# 三件套：<out>（合并 stdout+stderr 原始字节）、<out>.exitcode、<out>.cmdline
python -B tools/verify_kit/run_rc.py --out raw/01_step -- python -B your_tool.py --do-it
echo "outer_rc=$?"     # run_rc 透传子命令退出码
```

裸壳口径（不用工具时，Bash）：

```bash
your_cmd > raw/01_step 2>&1; rc=$?; printf '%d' "$rc" > raw/01_step.exitcode
# 管道之后 $? 是 tee 的！必须取第一个：
your_cmd 2>&1 | tee raw/01_step; rc=${PIPESTATUS[0]}; printf '%d' "$rc" > raw/01_step.exitcode
```

裸壳口径（PowerShell）：

```powershell
your_cmd 2>&1 | Tee-Object -FilePath raw\01_step
Set-Content -Path raw\01_step.exitcode -Value $LASTEXITCODE
```

**子 shell 身份陷阱（本机实测）**：经 `run_rc.py` 派生裸名 `bash` 时，
Windows PATH 解析可能命中 **WSL bash** 而非 Git Bash（`/d/...` 路径不识别、
输出混入 UTF-16 wsl 横幅）。要派 shell 子命令，用绝对路径：

```bash
python -B tools/verify_kit/run_rc.py --out raw/02_step -- "D:\Git\usr\bin\bash.exe" -c "exit 3"
```

选项：`--cwd DIR` 指定子进程工作目录；`--timeout SEC` 超时杀子进程并把退出码
记为 124（注意：孙进程可能残留）。`run_rc.py` 自身退出码 = 子命令退出码
（127 = 无法启动，126 = 不能执行，2 = 用法错误）。

## snapshot.py / diff_snapshot.py · 零写入证明

```bash
export PYTHONDONTWRITEBYTECODE=1
# 修前（排除口径要记进报告，修后必须逐字同参）
python -B tools/verify_kit/snapshot.py <目标目录或仓库根> --out raw/pre_snapshot.json \
  --exclude ra2youli --exclude ra2bench --exclude .mimosa --exclude __pycache__ --exclude "*.pyc"
# ……执行你的改动……
# 修后（同参）+ 比对
python -B tools/verify_kit/snapshot.py <同一目标> --out raw/post_snapshot.json \
  --exclude ra2youli --exclude ra2bench --exclude .mimosa --exclude __pycache__ --exclude "*.pyc"
python -B tools/verify_kit/diff_snapshot.py raw/pre_snapshot.json raw/post_snapshot.json
echo "diff_rc=$?"    # 0 = VERDICT: zero-writes；1 = WRITES-DETECTED；2 = 错误
```

要点：

- **zero-writes 判据 = 无新增、无删除、无内容变化**（内容以 sha256 为准）。
  仅 mtime 变化**不计为写入**（读文件不得算写文件），但会逐条列出 `MTIME_ONLY`
  供复核——本仓库有"读受护 .py 也会 touch mtime"的先例，不能只看 verdict。
- 快照排除的目录对 diff 不可见 ⇒ 排除口径越宽，结论越弱；报告必须附排除清单。
- 空目录不可见（只跟踪文件）；被杀毒/索引器短暂锁住的文件会进 `errors` 并在
  diff 里以 NOTE 提示"unreadable files weaken the verdict"。
- PowerShell 下同一 python 命令原样可用，末尾用 `$LASTEXITCODE` 取 rc。

## boundary_scan.py · 写入边界自证

```bash
export PYTHONDONTWRITEBYTECODE=1
# 扫单个脚本（rc 0=干净 / 1=有命中 / 2=错误）
python -B tools/verify_kit/boundary_scan.py path/to/your_script.py
# 扫目录（跳过 __pycache__ 与大于 8MiB 的文件）
python -B tools/verify_kit/boundary_scan.py tools/ --exclude __pycache__
# 自定义词表：一行一个词元，# 注释
python -B tools/verify_kit/boundary_scan.py cmd_list.txt --wordlist my_words.txt
```

内置词元（默认词表，见源码 `DEFAULT_WORDLIST`）：跨进程写入/分配/线程类
Windows API 四件 + 读内存/改保护两件 + `shutil` 拷贝家族四件。词元按
**标识符边界**字面匹配：`shutil.copy` 不会误中 `shutil.copyfile`（要一起抓就
都列进词表）。

**自引用掩码（必须配正负对照用，防止扫描器变哑巴）**：源码中
`# >>> verify_kit wordlist (self) >>>` … `# <<< verify_kit wordlist (self) <<<`
之间的行被视为"引用字面量"不计命中（行号保持不变）。**先证伪再采信**：

```bash
python -B tools/verify_kit/boundary_scan.py tools/verify_kit/boundary_scan.py                # 期望 rc=0 CLEAN
python -B tools/verify_kit/boundary_scan.py --no-self-exclude tools/verify_kit/boundary_scan.py  # 期望 rc=1 FINDINGS
```

`--no-self-exclude` 就是为了证明掩码真的在工作（关掉就命中），不是橡皮图章。

## selftest/run_selftest.sh · 一键负控自测

```bash
bash tools/verify_kit/selftest/run_selftest.sh <临时目录>
echo "selftest_rc=$?"   # 0 = 全部 PASS；非 0 = 有 FAIL，逐行看输出
```

覆盖：写入必被检出（NC-1）、未动即 zero-writes（NC-2）、仅 mtime 触碰不升格为
写入但必须被标出（NC-2b）、脏样本必命中（NC-3）、净样本必零命中（NC-4）、
自排除掩码开/关对照（NC-5）、失败退出码独立成文件且不内嵌（NC-6）、成功路径
（NC-7）。临时目录自足，不碰任何真实目录。

## 环境注意（本机实测）

- 派 shell 子命令用 `D:\Git\usr\bin\bash.exe` 绝对路径（见上）。
- 一切 python 调用带 `-B`；`python -m py_compile` 会落 pyc，**语法检查用**
  `python -B -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" file.py`。
- 输出文件统一记**原始字节**（run_rc 不做转码）——子进程输出的编码毛病
  （如 WSL 横幅的 UTF-16）会原样保留，这恰恰是仪器身份问题的证据。
