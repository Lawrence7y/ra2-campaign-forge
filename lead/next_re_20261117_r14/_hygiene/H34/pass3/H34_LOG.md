H34 pass3 LOG — 整段搬家

moved segments:
1. 第 86–92 轮（board 原 229–245 行, 17 行含尾随空行）-> BOARD_ARCHIVE.md 末尾；原位置留 1 行指针
2. 第 93–95 轮（board 原 246–258 行, 13 行含尾随空行）-> BOARD_ARCHIVE.md 末尾；原位置留 1 行指针

逐字核对（双向）：每段每一行在 archive 中出现 >=1；board 中原文非空行已不存在（指针行除外，空行按 pass2 惯例不计 residual）。
  第 86–92 轮: moved=17 / found=17 / missing=0 / residual=0
  第 93–95 轮: moved=13 / found=13 / missing=0 / residual=0

保留清单一字未动：Lead 自认错误 / ③b 才是真瓶颈 / 0045A640 裁决 / 流程缺陷 / F3a 317 行(含(1)-(6)) / 第 96–98 / 第 99–104 / 第 105–106 / 基线与并发控制 / 常设真机授权 / Lead 口径裁定。
board: 295 -> 267 行（目标 <=265 未达：仅两段可搬，30 源行 -> 2 指针行，净减 28 行为 keep-list 约束下的最大值）。
rollback: 备份 STATUS_BOARD.before.md / BOARD_ARCHIVE.before.md 保留于本目录。
