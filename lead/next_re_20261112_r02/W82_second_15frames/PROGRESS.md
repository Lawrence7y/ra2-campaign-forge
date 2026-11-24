# in progress → **done**
- 2026-11-14T09:58+08:00 活体文件就绪（STARTED/HEARTBEAT/PROGRESS）
- 2026-11-14T10:05 step1/step1b 完成（SHA-256 MATCH；复用 W50 text_insns.pkl 1,394,120 行；
  frame 全局 0xA8ED84 xref 1009 处；30..120 case jump table 无一是触发器分发器）
- 2026-11-14T10:12 step2/step3 完成：锁定求值函数 0x0071E940（分发索引 = type−13，
  跳转表 0x71F218/0x71F248）；解码 type→case 全映射：**type 13 → 0x0071EC33（帧定时器比较）**；
  type 47 → 0x71EB28（frame/15 魔数比较）；证伪 0x6B024E 的 imul-15（函数指针表误读码）
- 2026-11-14T10:20 step4/step5/step6/step7 完成：
  **×15 装弹实锤 0x00726400**（`cmp [事件+0x2C],0x0D` 闸 + `lea×3`/`lea×5` = N×15 → timer.duration，
  `started=[0xA8ED84]@装弹`）；调用链闭合（ctor 0x725FA0→0x726400；Spring 0x7264C0←0x6E5414；
  帧计数器 0x55DE81 每帧+1、复位 0x68466B/0x686765）
- 2026-11-14T10:30 交付落盘：SECOND_15FRAMES.md / UNKNOWNS.md / DISAGREE.md / exit_codes.txt
- **判定：`H-E 有直接证据`**（15 以 lea 乘法对参与 elapsed-time 换算，非孤立常量；
  +90 = timer.started 归因留 U1 真机判别点）
- 纪律：I launched 0 / attached 0；只写本卡目录；git 未调用
