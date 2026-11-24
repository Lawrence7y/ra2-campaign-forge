H34 pass4 LOG — 整段搬家

moved segments:
1. 第 96–98 轮（board 原 231–244 行, 14 行含尾随空行）-> BOARD_ARCHIVE.md 末尾；原位置留 1 行指针
2. 第 99–104 轮（board 原 245–259 行, 15 行含尾随空行）-> BOARD_ARCHIVE.md 末尾；原位置留 1 行指针

逐字核对（双向）：每段每一行在 archive 中出现 >=1；board 中原文非空行已不存在（指针行除外，空行按 pass2 惯例不计 residual）。
  第 96–98 轮: moved=14 / found=14 / missing=0 / residual=0
  第 99–104 轮: moved=15 / found=15 / missing=0 / residual=0

保留清单一字未动：Lead 自认错误 / ③b 才是真瓶颈 / 0045A640 裁决 / 流程缺陷 / F3a 317 行(含(1)-(6)) / 第 105–106 / 第 107–109 / 第 110 / 基线与并发控制 / 常设真机授权 / Lead 口径裁定。
board: 294 -> 267 行（可搬仅两段，29 源行 -> 2 指针行，净减 27；keep-list + 2 指针约束下的地板为 267，目标 <=265 不可达）。
rollback: 备份 STATUS_BOARD.before.md / BOARD_ARCHIVE.before.md 保留于本目录。
