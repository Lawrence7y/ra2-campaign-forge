# _ak_REPRO.md — 与 STALE_PASS_INVENTORY.md:94-101 上游注射实证对齐

上游口径复刻（`_sp_gen_injected.py:4-12` / `_sp_gen_d28.py:4-10` / `_sp_gen_d29d30.py:6-19`）：只把**脚本副本**里的第二根针字面量换成 `TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ`，OR 结构不变；输入文档为原件逐字节副本。命令全文、EXIT、STDOUT、stdout_sha256 见 `_ak_runs.jsonl` 的 `REPRO_BASE` / `REPRO_INJECTED` 行。

| gate | BASE CMD | INJ CMD | BASE EXIT / STDOUT | INJ EXIT / STDOUT | 逐字一致 | stdout_sha256 一致 | 均 PASS | 能否复现 |
|---|---|---|---|---|---|---|---|---|
| d27 | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d27\repro_base\check_d27_BASE.py"` | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d27\repro_up\check_d27_UP.py"` | 0 / `'PASS: D-27 八项机械检查通过；裁决书引用 71 处\r\n'` | 0 / `'PASS: D-27 八项机械检查通过；裁决书引用 71 处\r\n'` | True | True | True | **能** |
| d28 | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d28\repro_base\a\b\check_d28_BASE.py"` | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d28\repro_up\a\b\check_d28_UP.py"` | 0 / `'PASS: D-28 全部 8 项机械检查通过 (exit 0)\r\n'` | 0 / `'PASS: D-28 全部 8 项机械检查通过 (exit 0)\r\n'` | True | True | True | **能** |
| d29 | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d29\repro_base\check_d29_BASE.py"` | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d29\repro_up\check_d29_UP.py"` | 0 / `'PASS\r\n'` | 0 / `'PASS\r\n'` | True | True | True | **能** |
| d30 | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d30\repro_base\check_d30_BASE.py"` | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d30\repro_up\check_d30_UP.py"` | 0 / `'PASS\r\n'` | 0 / `'PASS\r\n'` | True | True | True | **能** |

注射副本 SHA256 / 字节数（与 `STALE_PASS_INVENTORY.md:98-101` 登记的 INJ 前缀逐字符相符）：

- d27: `f404f58783ab4da0e59ef94afda5bcc97e69d58914465dad2a36769ab5d7af89`，3783 B
- d28: `f5ae184ca7ddc6cfb9965124e26d506992903305aabbdd1a3beb500eb4692314`，4569 B
- d29: `2399e95a43eaafa4ba5409b0850a89e3ed27a0ef345a8f9628bfbf641580ced5`，3934 B
- d30: `b1670537e12a6d7ccc48e636088016a0c482ae00bd3ee5280b810d88af9c7129`，3951 B

**差异原因**：本外壳把「k 个输入」拆到两份**单元素词表副本**上真实各跑一次，则 B 输入（第二根针被删）在 WB 副本上必 FAIL（`AND_k=False`）；而上游注射只改脚本词表里的一个词、仍保留 OR 另一词，原件的 `any(present)` 在输入不变时必然仍 PASS 且输出逐字一致。两者并不矛盾，是同一 OR 塌缩的两种观测面。

