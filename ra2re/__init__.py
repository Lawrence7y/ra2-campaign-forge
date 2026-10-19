"""RA2 / 尤复 底层现代化的逆向工具集。

与 `ra2forge`（战役生成）、`ra2opt`（稳定性优化）并列的第三个模块，服务于
[docs/REWRITE_ROADMAP.md](../../docs/REWRITE_ROADMAP.md) 里的里程碑：

- `M0 基线测量`：perf-profile
- `M1 渲染接管`：定位 `Blitter` / `BSurface` 的 vtable 与 blit 实现
- `M2 oracle 骨架`：`symbols.json` + 可对拍的行为函数

本模块**只读**原版二进制，不修改任何游戏文件。
"""

__version__ = "0.1.0"
