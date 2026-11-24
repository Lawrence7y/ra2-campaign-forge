# W105 PROGRESS

- 2026-11-14 19:24 读 R09_COMMON.md + LEAD_FINDINGS_R09.md（L1/L2/L4/L5）。
- 2026-11-14 19:27 写 census.py（capstone 线性扫描，修 W99 两缺陷：按指令边界解码 + 全编码形式）。
- 2026-11-14 19:30 首跑：A=102/B=454/Cw=75/Cr=154；修立即数十进制解析、SIB 位掩码两 bug。
- 2026-11-14 19:33 修 FPU 方向表（fstp/fistp/fnstcw 为写）；+0x30 补充扫描。A=114/B=442。
- 2026-11-14 19:38 Lead 补丁：装虚表 A-excluded 判据（19 条剔除）、条件写/链头←next 检测。真候选 95。
- 2026-11-14 19:41 复核 0x47EA90 全函数：**完整摘链**（head==this 守卫摘头 + 链中遍历摘除 + next 清零）；
  脚本"unlink-head 不比较 this"标签勘误——比较在 0x47EAB9。
- 2026-11-14 19:45 落 WRITE_SITES.md / UNKNOWNS.md / PROGRESS.md / DISAGREE.md。
- 结论：无条件整链替换 = 无；UAF 假设静态无法判定；W100 判据已写进报告 §5。
