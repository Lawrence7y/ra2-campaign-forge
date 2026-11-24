# 未核验与边界清单（UNKNOWNS）

> 审计卡：W52（第二轮交叉一致性审计）  
> 约束声明：本轮审计严格限定为「文本与产物一致性核对」，**不重做反汇编、不启动游戏、不重跑回归测试脚本**。下列事项未在本轮由 W52 独立实测或逐字节复算。

1. **未重做二进制反汇编与内存/入口点核验**
   - `gamemd.exe` 中 `0x005AE320`、`0x005ADD95..0x005ADDCF`、`0x005ADFF3`、`0x005ADEE0..0x005ADEFA`、`0xA8F7AD` 等地址、VA/RVA/FOFF 对应关系、以及隐藏 `ListBox(1109)` 门控逻辑，均未重新反汇编核实。

2. **未启动游戏复现真机测试**
   - W39 三臂（`w39_skip_no.ndjson`）、W40 CSF 五臂（`live_results.json` / `live_extra_results.json`）、W44 C 线端到端三趟（`K1`/`K2`/`K3` 及 `run.ndjson` / `saveload.ndjson` / `repair.ndjson` / `restore_proof.ndjson`）的 `WinSta0\Default` 前台表现、游戏内动画/界面与读档实机行为均未重跑游戏验证。

3. **未独立重跑离线回归套件**
   - `regress_dlc_v12.py`（57 用例）与 `regress_dlc_v13.py`（82 用例，含 `S3_1..S3_25`）及 W41 / W42 / W43 相关测试脚本未在本轮重新执行；回归结果数字仅核对了落盘日志（如 `W43_b_line_s3\EVIDENCE\regress_full.stdout.txt`、`W43_b_line_s3\out\SUMMARY.txt`、`W43_b_line_s3\out\S3_21.log`、`W43_b_line_s3\out\S3_25.log`）。

4. **未逐行核对大型校验清单与十六进制字节记录**
   - `W44_c_line_e2e` 中 `restore_proof.ndjson` 所记录的 15 项还原前后字节核对未逐条重算对比。
   - `W43_b_line_s3` 中 `case_S3_25` 产出的 `SHA256_COMPAT_V13_V12.txt` 未做全文件逐行哈希核对；`TRACK_B_gates.json` 内嵌基线产物哈希亦未对源包重新重算哈希。

5. **未对截图做像素级图像内容/OCR 核验**
   - 对 `W44_c_line_e2e\out\*campaign_menu*.png` 只核对了文件大小（`2562915 B`、`235266 B`）与 SHA-256 指纹（`0C7FB5FB…`、`16F2E0A3…`），未对 W44 或 W40 全部截图做像素级视觉读图校验。

6. **关联「已撤回陈述」在更早期非主审子目录工卡正文中的全仓逐一排查**
   - 已核明 9 份最新主审文件及直接关联的 `LEAD_FINDING_campaign_text_is_csf.md:78`、`LEAD_W29_VERIFY.md:95` 等处残余活口，以及 `LEAD_FACT_map_error_label.md` 漏列的 `W33 NEXTSCENARIO_FLOW.md:43,45` 与 `W28 NEXTSCENARIO_FORM.md:5,15`；但未对全部历史工卡目录中是否还零星残留 `LB_GETCOUNT=0` 等旧说法做全仓全量扫描记录。
