# NAMED_PUSH_AUDIT10 — SUMMARY（S20_B3，1 行）

审计员：agent-200（异族独立审计，非 Hy4 非 DeepSeek）。
只采信本会话自读 PE 字节 + 自写 capstone 反汇编；未引用执行器 `EVIDENCE\ROW_*.txt`，未复用其脚本。

## 目标与工具链

| 项 | 值 |
|---|---|
| 目标 | `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe` |
| SHA-256 实测 | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（与期望一致） |
| ImageBase / `.text` | `0x400000` / `[0x401000, 0x7E038D)`（节表：VSize `0x3DF38D`） |
| 工具 | capstone 5.0.7（**skipdata=True**）+ pefile 2024.8.26，Python 3.12.10，无 venv、未 pip install |
| 复算全量输出 | `_work\RECOMPUTE.txt` |

## 取行方法

`NAMED_PUSH_S20_B3\delta.tsv` 为 6 列表头 `entry/subsystem/name/one_line_semantics/grade/evidence_path`，
数据行 **恰 1 行**：`00763200  S20  WaveClass::slot8`（grade `[已证]`）。本次审计即该 1 行，无抽样、无剔除。

## 结论

**报告行数 1 ｜ PASS 1 ／ FAIL 0**

| entry | subsystem | verdict | ring3b | same_source | 一句话 |
|---|---|---|---|:--:|---|
| `00763200` | S20 | **PASS** | `3b2` | no | 五环自成：② vt `007F6BF4` slot8 → `.?AVWaveClass@@`；③b② 全局 `DVC<WaveClass*>` 的 Find 未命中返 `-1` 被 `0076323D`/`00763240` 显式消费，命中路 `00763261` 非栈前移压缩带 `0076326D` 回边；④ 构造器 `0075EA3F` 活表锚（非 atexit、行外） |

**FAIL 逐条原因**：无。

## 对执行器三项自报的独立确认（本卡指定要确认的三点）

| 执行器自报 | 独立复核 | 结论 |
|---|---|---|
| ④ 体内 `00763206` 自装表落析构器内，按 ㉓ 排除 | `00763206 c7 07 f4 6b 7f 00` 确在本 entry（scalar deleting destructor）体内；析构器的 vptr 复位是编译器固定前奏，不证运行期活性 | ✅ 排除正确 |
| 改用构造器锚 `0075EA3F` | `0075EA3F c7 06 f4 6b 7f 00`，宿主 `[0075E950, 0075EBD3)`；`0075E956 call 005F3900` 基类构造在前；`0075EAC4..0075EAF9` 把 this 追加进全局容器（构造语义收敛）；无 `push <dtor>; call 007C978A`（非 atexit）；行外 | ✅ 锚点成立 |
| ③ 为 ③b② | 容器 vt `007E9CE4` = `DynamicVectorClass<PAVWaveClass>`（RTTI 自读），活表由静态初始化 `004E67FD` 装入、死表 `007E9D04` 才由 atexit `004E6820` 写；`vt+0x10`=`004EAFD0`，`004EAFEF 83 C8 FF or eax,-1` + `C2 04 00 ret 4`；调用侧 `FF 52 10`→`83 F8 FF`→`74 2D je` 零间隔 | ✅ ③b② 成立 |

## 对"析构器 + 容器移除是否构成 ③b"的专门结论

1. **哨兵被真检查、真分支**：`0076323D 83 F8 FF`(cmp eax,-1) → `00763240 74 2D`(je `0076326F`)，零间隔；
   命中侧 `0076324C 49`(dec)/`0076324F`(落盘)/`00763261 89 54 81 FC`(非栈前移写)/`0076326D 7C E8`(回边)。
2. **按本线既有口径，构成 ③b②**：D-42 ③b② 认"可伪证的错误码/返回约定"，D-46 (A) 只排除 **bool 主输出**；
   `-1` 是下标型失败哨兵，被显式 `cmp`/`je` 消费，符合窄读法。**不因"这是析构器"降级**——③b 判的是合同可伪证性，
   与函数是否业务函数无关。
3. **但我记下真实弱点，不替执行器掩盖**：`-1` 归属**被调方** `004EAFD0`，本 entry 自身 `007632C9 8B C7` 返回 `this`、
   无错误码；即"可伪证返回约定"落在调用侧消费。已写入 `verdict.tsv` reason 与 `VERDICT.md` §2-③。
   **若 Lead 收紧为"只认本 entry 自身返回码"，本行须随整批改判**（同形者不止本行，见下）。

## 口径一致性提醒（须整批处理，非单行问题）

本行 ③b② 与已判 PASS 的 `NAMED_PUSH_AUDIT8`/`00442230` **操作码与 disp8 逐字节同构**
（`ff 52 10` / `83 f8 ff` / `74 xx` / `49` / `89 54 81 fc` / `7c xx`），父类析构 `005F3B80`
（`005F3BBF ff 52 10`→`005F3BC2 83 f8 ff`→`005F3BC5 74 2d`）是第三份同样副本
⇒ 这是引擎 `DVC::Delete` 的通用内联展开，**不具函数级判别力（零区分度）**。
故"析构器 + 容器移除"这一形态的正确定位是**整批口径问题**：要么整批按 ③b② 收（本卡判 PASS 即此口径），
要么整批回退（连带 `NAMED_PUSH_AUDIT2/8/9` 的十余行同类 PASS），**不宜单行否掉**。

## 瑕疵记账（不影响 PASS）

- 第 4 列漏写 `00763221 call 007258D0`、`0076327E ff 50 0c`（成员虚析构）、`00763295 call 007C8B3D`（释放成员缓冲）。
- `0075ED37`（析构器 `0075ED30` 体内）亦写 `007F6BF4`：属非删除析构器副本，非 atexit ⇒ 不构成 ㉓ 死表；
  本表活身份另有 `0075EA3F`/`0075ECAA`/`0075F6A4` 三个非 atexit 写点支撑。
- 容器 `00A8EC38` 落在 `.data` 虚拟区但超出行数据（RawSize 至 VA `0087E000`），文件初值为空，
  只能靠静态初始化 `004E67E0` 定值；从文件直读该 dword 会得 0（读法陷阱，非本行事实问题）。

## 只写范围自检

本卡仅写 `NAMED_PUSH_AUDIT10\`（`SUMMARY.md` / `VERDICT.md` / `verdict.tsv` / `_work\`）。
未修改 `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账及任何 `NAMED_PUSH_*` 目录。
