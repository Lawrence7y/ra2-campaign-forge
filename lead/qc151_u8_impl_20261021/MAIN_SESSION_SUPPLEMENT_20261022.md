# U8 `--allow-loader` 补丁 · 主会话独立复核（非核验替身，仅记录发现）

> **性质**：离线只读 + 静态/行为测试。**零真机、零注入。**
> **时刻**：2026-10-22 01:2x
> **定位**：这是**主会话自己做的补充复核**，**不替代**异族核验（`dwfrun-56fce513`，千问 qfmodel 在飞）。
> 按「执行者 ≠ 核验者」纪律，**最终判定以异族核验报告为准**；本卡只登记我在等它时独立查到的、交付者自测**未覆盖**的事项。

---

## §0 结论摘要

| # | 项 | 结果 |
|--:|---|---|
| A1 | 反向重建 diff（16 hunk，7439→7559 行） | ✅ 与交付者 `u8.diff` 同源 |
| A2 | `allow_loader_authorized` 八条真值表（我自建） | ✅ **8/8 全对**，含属性缺失不抛异常 |
| A3 | 默认路径仍指向 `gamemd.exe` | ✅ `:1234` |
| A4 | 授权路径指向 `ra2loader.exe` | ✅ `:1229` |
| A5 | `resolve_pid` 的 `expect_name` 配套（关键，非可选） | ✅ `:6702-6704` 正确接线 |
| A6 | 未授权时 S-4 命中仍 62 | ✅ `:1150-1159` 未被绕过 |
| A7 | 授权不放宽「枚举失败」收口 | ✅ `:1078` 分支在授权块 `:1132` 之前 |
| **A8** | **★ 授权趟的收尾只终止 loader，不终止 gamemd 子进程** | **⚠️ 真实缺口（见 §2）** |
| A9 | 未授权时 `via_loader` 由 `None` 变 `False`（注释称"逐字相同"） | ⚠️ 记录字段偏差，无控制流影响（异族核验独立发现，我复核成立） |

---

## §1 我独立做的验证（可复跑）

### §1.1 反向重建（不用交付者的 diff）

```
基线 7439 行 / 补丁 7559 行 / 差异块 16
insert   基线 341-340   → 补丁 341-384   (44行)   ← 授权函数 + 常量块
replace  基线 991       → 补丁 1035      (1行)    ← s4_injection_gate 签名
insert   基线 1000-999  → 补丁 1044-1049 (6行)    ← docstring
insert   基线 1079      → 补丁 1129-1149 (21行)   ← 授权旁路
replace  基线 1138-1139 → 补丁 1209-1210 (2行)    ← launch_direct 签名
replace  基线 1145      → 补丁 1216      (1行)
insert   基线 1147      → 补丁 1218-1226 (9行)    ← docstring
replace  基线 1148-1150 → 补丁 1228-1239 (12行)   ← exe 选择分支
replace  基线 1152-1153 → 补丁 1241-1244 (4行)
replace  基线 1180-1181 → 补丁 1271-1273 (3行)    ← resolve_pid 签名
insert   基线 1191      → 补丁 1283-1293 (11行)   ← docstring
replace  基线 1192      → 补丁 1295      (1行)
replace  基线 1194      → 补丁 1297      (1行)
insert   基线 6197      → 补丁 6300-6306 (7行)    ← parse_args 注册
replace  基线 6582      → 补丁 6692-6698 (7行)    ← main 授权判定 + 调用
replace  基线 6585-6586 → 补丁 6701-6706 (6行)    ← expect_name + authorized 传参
```

**16 个 hunk 全部可归因到「加 `--allow-loader` 通道」这一件事**，无顺手改动、无常量调整。

### §1.2 八条真值表（我自建，用 `ast` 抽函数后 `exec`，不复用交付者脚本）

| case | 结果 | 期望 | |
|---|---|---|---|
| 无 `allow_loader` 属性 | `False` | `False` | ✅ **不抛 AttributeError**（用 `getattr(..., False)`） |
| `allow_loader=False` | `False` | `False` | ✅ |
| `True` + `trip_id=None` | `False` | `False` | ✅ |
| `True` + `trip_id=''` | `False` | `False` | ✅ |
| `True` + `trip_id='  '` | `False` | `False` | ✅ |
| `True` + `'T1'` vs 传入 `'T2'` | `False` | `False` | ✅ |
| `True` + `'T1'` vs 传入 `'T1'` | `True` | `True` | ✅ |
| `True` + `'  T1  '` vs 传入 `'T1'` | `True` | `True` | ✅ 归一正确 |

### §1.3 S-4 分支顺序（关键：授权不得放宽枚举失败）

```
:1078  ← 枚举失败分支（EXIT_MODULE_ENUM_FAILED=63）  ★ 在授权块之前
:1132  ← if authorized: 降级 WARN
:1151  ← 未授权命中 ⇒ 62
```
⇒ **授权只放宽"命中"，不放宽"枚举失败"。** ✅

---

## §2 ⚠️ A8：授权趟的收尾只终止 loader，不终止 gamemd 子进程（**真实缺口**）

### §2.1 事实

| 项 | 证据 |
|---|---|
| 收尾只终止 `LAUNCH_TOKEN.proc` | `:7323` `term_proc = LAUNCH_TOKEN.proc if …`；`:7334` `terminate_owned_process(rec, term_proc, term_pid, term_ct)` |
| 授权趟 `LAUNCH_TOKEN.proc` = **loader 进程** | `launch_direct` 里 `subprocess.Popen([str(exe)])`，`exe = carrier_dir / ALLOW_LOADER_EXE`（`:1229`） |
| loader 会另起 `gamemd.exe` | U8 真机探针实测：`launch_pid=38192`（loader）→ `gamemd_pid=41604`，**两个不同 PID**（`u8probe_20261021/v1v2_out.txt`） |
| **harness3 没有"按载体路径清扫残留进程"的机制** | `QueryFullProcessImageNameW` 在补丁件里出现 **0 次** |

### §2.2 后果

- 授权趟收尾时只 `TerminateProcess(loader)`；**gamemd 子进程不受影响，继续存活并占用载体目录**。
- 随后 `delete_owned_carrier` 会 `shutil.rmtree` ⇒ 大概率 `PermissionError`（DLL 映像仍映射）⇒ `EXIT_CARRIER_DELETE_FAILED = 27`。
- 更严重的是**违反用户硬约束**：「每次真机复制的游戏本体都要在测试完成后删掉」——若 gamemd 残留，载体删不掉。
- **U8 的真机探针之所以通过，是因为探针自带清扫**（`u8_v1v2_probe.py:196-220` 用 `QueryFullProcessImageNameW` 按载体路径扫 `gamemd.exe`/`ra2loader.exe` 并 `TerminateProcess`）。**harness3 没有这段**。

### §2.3 严重性判定

- **不是**安全漏洞（没有放开任何禁止面）。
- **是**运维缺陷：授权趟会留下 gamemd 残留 + 载体删除失败 ⇒ 触发 27 号收尾失败 ⇒ 该趟判 `VOID`。
- **影响范围**：只有 `--allow-loader` 授权趟（B0/B1 臂）。基线臂 A 不受影响。

### §2.4 建议修法（未实施，待 Lead 裁决）

在 `delete_owned_carrier` **之前**加一段「按载体路径清扫」：

```python
# 伪代码：仅授权趟需要，但建议无条件加（幂等）
for pid in enumerate_gamemd_and_loader():
    img = query_full_image_name(pid)
    if carrier_dir.lower() in img.lower():
        TerminateProcess(pid); Wait(5s)
```

**为什么不直接改**：这是在用 harness 的改动，按「补丁副本制」须走副本 + diff + 回执 + 异族核验；且它会影响**所有**趟（不只授权趟），属范围扩张，须 Lead 裁决。

---

## §3 诚实边界

| # | 边界 |
|--:|---|
| 1 | **A8 是静态推断 + 探针旁证，未在真机上验证"gamemd 残留导致 27"** | 需授权趟真机跑一次才能定谳（属用户在场动作） |
| 2 | 本卡**不是**异族核验 | 最终判定以 `dwfrun-56fce513`（千问）为准 |
| 3 | 未核 `parse_args` 的 `--allow-loader` 是否 `store_true` | 交付者自测称已注册；我在 `:6300-6306` 看到注册，但未逐字读 |

---

## §4 可复跑

```text
1) 反向重建   : difflib.SequenceMatcher(None, base_lines, patched_lines, autojunk=False).get_opcodes()
2) 八条真值表 : ast.parse → 取 allow_loader_authorized → compile+exec → 8 组 SimpleNamespace
3) S-4 顺序   : grep -n "EXIT_MODULE_ENUM_FAILED\|if authorized:\|EXIT_INJECTION_SUSPECTED" <patched>
4) A8 收尾    : :7323 term_proc=LAUNCH_TOKEN.proc / :7334 terminate_owned_process / :1229 exe=ALLOW_LOADER_EXE
5) 无清扫机制 : grep -c QueryFullProcessImageNameW <patched>  → 0
6) 探针有清扫 : u8probe_20261021/u8_v1v2_probe.py:196-220
```

---

*（本卡完成于 2026-10-22 01:2x，离线。A8 为真实缺口，附静态证据 + 探针旁证；最终判定权在异族核验。）*
