# ra2-campaign-forge (t628 静态逆向精简库)

- **工作目录定位**：本目录是部署在 t628（Linux x86_64）上的精简静态逆向库（约 208 MB），包含 `ra2bench/gamemd.exe`（并已软链 `ra2youli/gamemd.exe`）、`out/reverse/symbols.json`、`YRpp/`、`re_atlas/`、`docs/`、`tools/`、`ra2forge/`、`ra2re/`、`lead/`。
- **本机可用工具**：`python3-capstone`、`python3-pefile`、`i686-w64-mingw32-objdump`、`rg`（ripgrep）、`harness-mem-budget`。
- **子代理内存配额纪律**：主会话派发子代理前必须先运行 `harness-mem-budget` 获取 `MAX_SUBAGENTS`，并发子代理数严禁超过该值（`0` 时主会话亲自执行，不派子代理）。
- **子代理模型与审计要求**：白名单 `work/cn:deepseek-v4.1-flash`、`work/cn:hy4flash-free`、`work/cn:hy4flash`、`zcode/GLM-5.3-Flash`；GLM 仅限 ≤8 项纯文本/路径/表格检查；跨家族审计（hy4 ↔ deepseek）且结论必须复算；卡面写入 `_cards/` 不得出现反引号。
- **任务边界**：
  - **可直接在本机跑**：PE 结构与段表分析、x86 反汇编、交叉引用扫描、字节锚点核验、R17 静态台账/清单核验、`ra2forge` 编译。
  - **需派发到 `win-main` 节点**：任何需要启动 `gamemd.exe` 窗口、Win32/DirectDraw 注入采样或 Ghidra GUI 的动态任务。
