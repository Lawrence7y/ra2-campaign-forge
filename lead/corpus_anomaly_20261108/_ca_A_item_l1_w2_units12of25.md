# _ca_A · l1_20261023e4/measure_w2.json「仅 12/25 units 有效读」归因核查（只读）

- 核查人：语料归因员·GLM（动态工作流子件）；日期 2026-11-08；零真机、零采样代码、未改任何语料/台账。
- 被核断言：`lead/slowframe_round2_20261107/SLOWFRAME_PROXY.md:221`「l1_20261023e4/measure_w2.json 仅 12/25 个 units 有效读（_proxy_scan_corpus_out.txt:62），中断原因未查」。
- 被核对象（本会话实算 hashlib）：
  - `l1_20261023e4/measure_w2.json` **SHA256 = 8d85ac02ff78e228fc12f65da2c3f8850e6fda0c1f3f35d5ca7aec5dbe2b0540，字节数 = 106895**（与编排方盘点一致）
  - `SLOWFRAME_PROXY.md` SHA256 = 5fe880595965de4e0b39639c0d4a80d626476a9715f1cae5efd7361a0c8985d3，26916 B（与盘点一致）
  - `_proxy_scan_corpus_out.txt` SHA256 = fa54da803e3246a2d6de1313b92f7f3afb0dc70bb7799238386ba8e0ed076efb，11997 B
  - 同趟 w0：8799e08d…，271414 B；w1：9439e8ef…，233984 B（均与盘点一致）
- 语料根：`D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\`

## 1. 数值复核：12/25 属实

「有效」判定标准（来自 harness 代码，非自造）：每秒 1 行 counters 副读（`qc151_trip.harness7.py:4000-4004`），每字段独立经 `ReadProcessMemory` 读 u32（:3897-3913，4 字节须全读否则视为失败），任一项读失败该字段写 `null` 不写 0（:3953、:3964-3970）。**units 字段非 null 即有效读**。

实跑（python -I -X utf8 逐行打印 counters）：

```
len(counters) = 25
[00] t_rel=  0.000 units=640 ... ws_kb=139980 shape={"g_valid": true, "b_valid": true}
…（[01]–[11] 同为 units=640, ws_kb≈138868–139980, g_valid/b_valid=true）
[12] t_rel= 12.016 units=None inf=None g=None b=None techno=None ws_kb=20 pf_kb=64 shape={"g_valid": null, "b_valid": null}
…（[13]–[24] 全部 None / ws_kb=20 / pf_kb=64）
```

→ 25 行中前 12 行（t_rel 0.000–11.012）units 有效，第 13 行（t_rel=12.016）起 13 行全 null。**12/25 成立**；且 `_proxy_scan_corpus_out.txt:62` 该行第 9 列=12，与断言引用一致。

## 2. 中断原因：可归因（直接层面）——被测 gamemd.exe 在窗中段进入不可读终止态

trip = QC161-U0800-L1-20261023E4，map=spawnfix8（0add791d…），gamemd.exe sha 73201cc0…（`carrier_post_state.json` 与 measure_w2.json 内 `gamemd_sha256` 互证；A8 行「直启 gamemd，无 loader 派生进程」→ Popen pid=22628 即 gamemd.exe，主窗 hwnd 662272 pid=22628）。

证据链（全部本会话实读）：

1. **samples 断崖**：5949 个有效样本连续覆盖 t_span=11.894575 s（p50 步长 2.48 ms、max 6.7 ms、无 >50 ms 空洞），之后直到 25 s 窗末再无有效样本；`stats.max_stall_s = 11.894575` 恰等于有效样本总跨度；`error = "ReadProcessMemory 失败 6190 次（有效样本 5949）"`。失败期读失败退避 1 ms 继续守窗（harness :3980、:3995-3997），错误串由 :4012 生成——**是实况记录，不是采样器故障**。
2. **工作集塌缩**：counters ws_kb 从 139,980/138,868 KB（t_rel≤11）跳到 20 KB（t_rel≥12.016）。ws_kb/pf_kb 经 GetProcessMemoryInfo 实测，失败写 null（:3929-3945）——20/64 是实测残影值，为进程终止态特征；活进程不可能 20 KB。
3. **窗末取证**：rec 行 `measure_forensics_w2`（qc151_fields.json，ts=2026-10-26T20:00:48）：game_title=""（主窗标题读空）、fg_hwnd=198964 fg_title="BuddySwitch 整合预览版"、focus_ok=false、current_frame=null、**empty_window=true**；紧随 `verdict="degraded"`，note「★ QC208 空窗降级：w2:empty」——harness 自己已把 w2 判为空窗并落 `measure_w2_end_x.png`。
4. **趟末旁证**：ISOLATION `CreateToolhelp32Snapshot(pid=22628) 失败: err=299`（ERROR_PARTIAL_COPY，20:00:52-53）；TERM 身份核验通过（pid 22628 创建时间仍匹配）→ terminate_sent=true → `wait_returncode=0`（20:00:53）；WER 扫描 `wer_report_count=0`（其自带注记：NO_NEW_REPORT ≠ 证明没崩）。
5. **JSON 未截断**：文件尾 80 字节为完整 `"verdict": "ok", "error": "ReadProcessMemory 失败 6190 次（有效样本 5949）"}`；samples.t/f 等长（5949/5949）。
6. **同趟对照**：w0 全窗正常（12501 样本、737 帧边沿、fps_avg=29.44、25/25 有效）；w1 帧号 3557→3668 后于 20:00:03（QC213P2 frozen_final 时刻）值被重置为 0 并持续到窗末（logic_frames=-3557）——**窗中断之前，游戏帧钟已在 w1 停摆/换景**。
7. **时间对齐**：t_abs0=1793016023.182 → 20:00:23.18（本地）；最后有效样本 ≈ 20:00:35.08；measure_w2.json mtime=20:00:48.20（窗末）。except 件 `except_post_20261026T200053072552.txt` 文件名时间戳=**采集时刻**（harness :5644 `datetime.now()` 命名；:5642-5645 为 read_bytes→write_bytes 新写文件，mtime=采集时刻），其内容与趟前被动基线（U-5，rec 行 baseline_source=passive_read）**集合差为零**（`except_set_diff.json`：pre/post 各 1046 行、new=0、gone=0、new_exception_count=0）——**该崩溃转储是历史遗留件，不是本趟所写，不能作为本趟中断的崩溃证据**。

**归因结论（直接层面）**：w2 窗内 t_rel≈11.89 s（墙钟 20:00:35.1）起，gamemd.exe 对所有被测地址停止可读（RPM 全失败）、工作集塌缩至终止态残影值、主窗标题读空——被测游戏进程在第三个采样窗中段自行退出/进入终止态，采样器按纪律守满 25 s 并如实记 6190 次失败。12/25 即由此而来。

**不可归因（深层原因）**：游戏为何在 w1 末停帧换景（CurrentFrame 值重置为 0）、又为何在 20:00:35 退出——语料内无任何记录：except.txt 零新增行、WER 零报告、无 abort 件、趟末 exit code 0 与 terminate_sent 并存使「自行干净退出 vs 终止竞态」不可区分；w2 末前台已被第三方应用（BuddySwitch 整合预览版）占据，但其与 20:00:35 事件的先后仅能夹逼在 (20:00:23, 20:00:48]，语料无法定序。**此深层原因未查（语料无据），不补造。**

## 3. 纪律声明

以上只确立「窗口内容/进程状态差异」：w2 是「进程终止态空窗」，w0 是「战斗活跃窗」。**不构成任何引擎快慢的因果机制结论**（该趟 w0 活跃段 fps_avg=29.44、frame_ms_p50=32.62 ms，与其余趟健康段同量级）。

## 4. 附：本会话只读核查产出的证据摘录件（均在本写域）

- `_ca_harness_sampler_3890_4110.txt`（采样器/有效读定义原文）
- `_ca_harness_term_1369_1460.txt`（终止流程原文）、`_ca_harness_except_5620_5670.txt`（except 采集原文）
- `_ca_rec_rows_A.txt`、`_ca_rec_rows_2000_2005.txt`（l1 趟 rec 台账摘录）
- `_ca_tmp_grep_harness*.txt`（harness 检索索引）、`_ca_png_probe.py`（stdlib PNG 解码探针）
- 注：Read 工具两次渲染 `measure_w2_end_x.png` 均返回与本文件无关的环境截图（工具侧异常），故未采信其图像渲染；截图内容改由 `_ca_png_probe.py` 像素直读判定（87% 浅灰空面，avg=(228,230,231)）。
