"""RA2 / YR 稳定性与性能优化工具链。

与 `ra2forge`（战役生成）并列的独立模块，只读或"带备份地"修改游戏目录本身：

- PE 层：Large Address Aware（4GB 内存寻址）、栈/堆保留空间
- 渲染层：cnc-ddraw 升级与按 RA2/YR 调优的 ddraw.ini
- 配置层：ra2md.ini / ra2.ini 键值调优（保留用户设置）
- 系统层：Windows 兼容性标记（AppCompatFlags）修正、高优先级启动器
- 诊断层：audit 报告 + 一键回滚（restore）

所有写操作都经过 `backup.BackupSet` 记录，`python -m ra2opt restore` 可完全还原。
"""

__version__ = "1.0.0"

# 已知引擎版本指纹。用 `.text`（代码段）的 SHA-256 做键：LAA（COFF 头位）/ 栈 / 堆
# 这些优化只改 PE 头字段，代码段字节不变，所以打完补丁后仍能认出引擎版本，
# 而整文件 SHA-256 会被我们自己的补丁改掉。`full_sha256` 仅用于首次识别时的记录。
KNOWN_GAMEMD = {
    "c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738": {
        "name": "Yuri's Revenge 1.001 (2001-10-31)",
        "size": 4825360,
        "full_sha256": "db264305c8a6963d17f5d189a5a9720d9c95f7757cc19c534c2fbe4e015255aa",
        "text_sha256": "c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738",
        "notes": "官方 1.001 版本，签名时间 2001-10-31，含第三方 Detours 段（.detour）",
    },
}

GAMEMD_EXE = "gamemd.exe"
RA2MD_EXE = "ra2md.exe"
RA2_EXE = "ra2.exe"
GAME_EXES = (GAMEMD_EXE, RA2MD_EXE, RA2_EXE)

# 权威数据：cnc-ddraw 在 2021(v4.4.7) → 2024(v7.1.0) 之间针对 RA2 的修复，
# 来自官方 release notes（audit 报告里会引用）。
CNCDDRAW_RA2_FIXES = (
    ("v6.3", "Steam 版红色警戒 2 崩溃 workaround"),
    ("v6.4", "非活动窗口下的步兵鼠标输入修复"),
    ("v7.0", "特权指令崩溃修复；窗口尺寸与整型缩放修复"),
    ("v7.1", "无硬件加速时 OpenGL 崩溃、退出时崩溃、GDI 限速器支持等"),
)

