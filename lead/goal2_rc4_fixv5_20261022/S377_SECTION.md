
## §377　异族核验 A 组 3 缺陷已修 + B 组 harness6 全绿 + 公开仓泄漏核查

**依据**：v8 §7「执行者与核验者必须是不同模型家族」；铁律 2（cpp/h 不上公开仓）
**本件定位**：离线，零真机。核验方为 GLM 族，与执行者 DeepSeek 异族。

---

### 一、异族核验 A 组结果（探针 `_rc4_ab_probe.py`）

第一次派发（三组打包）**第三次中断**，零交付。改为**拆成最小单组**后一次成功。

| 编号 | 判定 | 缺陷 |
|:--|:--|:--|
| A1 | PASS | 默认不启动 |
| A2 | PASS | B 臂 pid 来自 gamemd（实现方式与描述不同，语义等价） |
| A3 | PASS | `relative_to` 非 `startswith` |
| **A4** | **FAIL** | `a8_sweep` 的 verdict 只进诊断字段，**不驱动控制流** |
| A5 | PASS | `clean_exit` 不引用 except.txt |
| A6 | PASS | B 臂不用 `proc.poll()`（上一轮我自修的假绿确认修好） |
| **A7** | **FAIL** | `safe_name` 无冒号拒绝、无 `.dll` 后缀要求 |
| **A8** | **FAIL** | 启动后主体无 try/finally，异常即留活进程 |
| A9 | PASS | 单例读取早于 WM_CLOSE |

**6 PASS / 3 FAIL**。三条 FAIL 全部成立，且 A4/A8 同源（自我豁免型缺陷）。

---

### 二、★ 三条缺陷的实质

**A4 + A8 同源：正控形同虚设。**
`a8_sweep` 自带枚举器正控（失败返回 `V_FAIL_ENUM` + sentinel），
但该 verdict 只被塞进 `rec["a8"]`，主流程从不读它 ——
于是「枚举器坏了」与「零残留」在最终报告里**无法区分**。
正控写了却不用，比不写更糟：它给人一种"已经验证过"的错觉。

叠加启动后无 try/finally，`_cleanup` 只在 4 个显式点被调用：
写 dump、读 except.txt、copy2 日志任一处抛异常，就跳过清扫，**留下活的 gamemd**。

**A7：NTFS ADS 绕过。**
`Path("foo:bar.dll").name` 仍是整串，`name != Path(name).name` 挡不住；
而 `foo:bar.dll` 在 Windows 下是"`foo` 的备用数据流"，落盘位置不受控。
⇒ 我原先的"单层无分隔符"检查在这条路径上是**漏的**。

---

### 三、三处修复

| 编号 | 修复 |
|:--|:--|
| **A7** | `safe_name` 显式拒 `:`（并写明 ADS 理由）；新增 `safe_dll_name` 要求 `.dll` 结尾，`main()` 改用它 |
| **A4** | `rec` 提升 `a8_verdict` / `a8_enum_ok` / `cleanup_ok`；`main()` 读 `a8_verdict`，非 PASS 即置 `results_aborted` 并 **return 3** |
| **A8** | 主体拆到 `_one_trip_body`，**`finally` 成为唯一清扫出口**；`_cleanup` 加幂等短路；新增**按已知 pid 定向击杀**（不把清扫全押在枚举器上）；异常路径记 `unhandled_exception` |

---

### 四、验证（自写门禁 + 运行级）

| 门禁 | 内容 | 结果 |
|:--|:--|:--|
| `_verify_probe_a4a7a8.py` | 20 条静态断言 + **6 条负控**（改回旧写法必须转红） | **6/6 PASS** |
| `_verify_a8_runtime.py` | 桩替换做**运行级**验证：异常路径上 finally 是否真的执行清扫 | **8/8 PASS** |

**★ 为什么要有运行级验证**：静态门禁只能证明"`finally` 这几个字在文件里"，
证明不了"它真的会被执行"。桩替换证明了三件事：
- 建载体阶段抛异常 ⇒ 不崩到调用方，且**零进程启动**
- 附加调试器失败 ⇒ `_cleanup` 被调用**恰好一次**
- 正常路径 ⇒ `_cleanup` 也**恰好一次**（不重复清扫）

---

### 五、★ 本轮我自己写的两个门禁都有缺陷（如实记录）

**缺陷 1：负控变异误命中他处。**
"A8 去掉 finally" 的负控第一版用 `s.replace("    finally:\n", ...)`，
只替换**第一个** `finally:` —— 而文件里第一个 finally 在 L254，与 `one_trip` 无关。
变异后断言全绿 ⇒ 负控 FAIL（转红 0/8）。
修正：变异串加上下文 `"    finally:\n        rec = state[\"rec\"]"`，精确对准 `one_trip`。

**缺陷 2：桩时钟恒定致死循环。**
`_verify_a8_runtime.py` 第一版把 `P.time` 桩成 `time=lambda: 0.0`，
而主体的调试循环条件是 `while time.time() - t_attach < debug_timeout` ——
`0.0 - 0.0 < 0.1` 恒真 ⇒ **死循环**，`timeout 120` 后 EXIT=124。
修正：桩成**递增**时钟（每次 +0.05）。

⇒ 教训：**门禁自身的 bug 会伪装成"被测物通过"或"被测物卡死"。**
两个缺陷都是我自己写门禁时引入的，与被测物无关。

---

### 六、异族核验 B 组：harness6 派生完整性 **7/7 全 PASS**

| 编号 | 判定 | 关键证据 |
|:--|:--|:--|
| B1 母本未改动 | PASS | 母本 427456 B / `f1e5bc7b0ff30c9c`；派生 461535 B / `a67cc05edd5034f8`，与期望一致 |
| B2 零删除行 | PASS | Counter 多重集：母本 7781 行，派生 8451 行，**deficit=0，总缺失=0**；difflib 交叉验证 17 opcode，删除/替换=0，8 个纯 insert 块（+670 行） |
| B3 WER 按 `.Name` 配对 | PASS | 先记 `.Name`→`cur`，`.Value` 时 `sig[cur]=val`；全文件无数字索引取值；乱序样本实测正确还原 |
| B4 枚举失败返 None | PASS | 初值全 None + `V_FAIL`；4 条失败分支全 return；桩测 4 路径无一为 0 |
| B5 近限 WARN 不改退出码 | PASS | 127–130 仅 `[WARN]` 并正常返回；131/132 才 `RuntimeError`；140 字符生成器仍硬停（防绕过有效） |
| B6 `--close-mode` 默认 terminate | PASS | 默认值 + 模块级双保险 + 取值回落 + **无条件**落盘 `close_fallback_terminate` |
| B7 `terminate_owned_process` 逐字节一致 | PASS | AST 抽函数体：双方均 4299 B、`sha256=220084465b33c637…`、diff 输出为空 |

**残余风险（不构成判负）**：WER `Sig[]` 若写成**交错布局**
（`Sig[0].Name / Sig[1].Name / Sig[0].Value / Sig[1].Value`），
实测第二个值被丢弃 ⇒ `{B:1}`、`pairs=[(B,1),(None,2)]`。
方向是"少报而非误读"，符合 B3 的"禁止按索引"要求，
但会让异常代码在交错布局下**静默缺失**。本机无 WER 目录可验证真实布局，仅作提示。

---

### 七、★★ 公开仓泄漏核查（本轮新发现，比台账原记录更严重）

`gh repo view` 实测 `visibility=PUBLIC`。逐件核查：

**原台账只记了 cpp/h，实际还有编译产物：**

| 文件 | 大小 | 在 HEAD？ |
|:--|--:|:--|
| `ra2render/blitter_hooks.cpp` | 227,989 B | 是 |
| `ra2render/ra2render.h` | 33,415 B | 是 |
| `ra2render/dllmain.cpp` / `ra2loader.cpp` | 1,451 / 2,818 B | 是 |
| `lead/goal3_p1sbh_merge_20261020/_work/p1base.cpp` | 257,433 B | 是 |
| `lead/.../\_work/out_fuzz0.cpp` | 273,750 B | 是 |
| **`ra2render/ra2render.dll`** | **163,328 B** | **是（新发现）** |
| **`ra2render/*.obj` ×3** | 139,606 / 8,282 / 5,512 B | **是（新发现）** |

**好消息（逐条核实，非推断）**：
- `gamemd.exe` / `.dmp` / `.mix` / `ra2youli/` / `ra2bench/` 在 HEAD **零命中**
- 6 个源码件全扫 `api_key|secret|password|token|BEGIN RSA`，**仅命中 `s_visionToken` 等变量名**，无明文密钥

**引入路径**：全部来自**单个提交** `b7f0508`（2026-10-21），
该提交 1166 files / 1,444,161 insertions，而提交信息只提 `tools/dump_ini_keyindex.py` 等三件。
⇒ 根因是**提交前未核 `git --cached --name-only`**，与既有记忆
[多会话 git 索引抢占] 同源。

**处置**：见 `LEAK_AUDIT_RA2RENDER.md`，三方案（A 只删当前树 / B 改写历史 / C 维持）
已列出，**均未执行** —— 改写历史 + `--force` 推公开仓不可逆，须用户裁决。
`.obj`/`.dll` 无争议（编译产物进版本库无合理理由），但本轮**未擅自删除**，
因为删除当前树不改变历史，且需与用户选定的方案配套。

---

### 八、本轮卫生检查

| 项 | 结果 |
|:--|:--|
| 残留游戏进程 | **0** |
| 三处母本 | `ra2youli/gamemd.exe` = `73201cc0` ✓；`ra2youli/ra2render.dll` = `39cbd665` ✓；`ra2render/ra2render.dll` = `626f98b6` ✓ |
| `.pyc`（排除快照） | 4 个，均在 `__pycache__/` 内且已被 `.gitignore:30` 覆盖，未跟踪 |
| `out/ct` | 仅 `.mimosa` / `.zcode` 元数据，无游戏载体 |

---

### 九、对 §4 待办的影响

| 待办 | 状态变化 |
|:--|:--|
| **9 / ②-A A/B** | ✅ 探针 3 处真实缺陷已修并双重验证（静态 6/6 负控 + 运行级 8/8）；**异族复核待返** |
| **①-1 harness6** | ✅ **异族 7/7 全 PASS**，派生完整性闭环 |
| **待办 7** | ⏳ 异族复算中（C 组） |
| **①** | ⛔ **仍阻塞**：开机会话 2026-10-21 09:45（uptime 38.9 h），实测 4 趟全 10 档，`pre_fps15` 未达 25 ⇒ 须用户重启 |
| **铁律 2** | ⚠️ **已违反且未处置**：需用户在 A/B/C 三方案中裁决 |
