# R208B 只读复核卡：T 形态编码二型（跨家族审计）

## 角色
审计员（只读复核，不得修改任何文件，不得读取 _r208/x1_tform.json 之外无关目录）

## 背景
gamemd.exe 的 RTTI 额外视图 vftable 中，有一类 slot0 是 this 调整 thunk。有主张称：
「T 形态共 101 条，字节形态统一为 83 6C 24 04 <imm8> E9 <rel32>」，且「立即数恒等于该 COL 的 mdisp」。
请独立核验这一主张是否对全部 101 条成立，特别是是否存在 imm32 编码（81 6C 24 04 <imm32> E9）。

## 可用
/home/t628/projects/ra2-campaign-forge/_r185/pe185.py（提供 RAW/dw/where/r2o/cstr）
python3-capstone

## 要求
1. 自己在内存里重建 COL 池与 vftable 起点（判据见下），不要依赖他人 json：
   COL 判据 = .rdata/.data 内 5 连 dword，w0 in {0,1,2}、w2==0、w3 落 .data 且 w3+8 处 C 串以 .?A 开头 @@ 结尾、w4 落 .rdata；
   vftable 起点 = 值等于 COL 地址、且 +4 落 .text 的唯一 dword 位置 + 4；
   额外视图 = COL 地址 != pCHD+16。
2. 统计额外视图总数，并按 slot0 首字节给出形态分布（至少区分 83 6C 24 04 / 81 6C 24 04 / C2 04 00 / 32 C0 C2 08 00 / 8B 44 24 04 / 其它）。
3. 对 83 与 81 两种编码逐条核对立即数 == mdisp，给出通过数/总数与例外清单。
4. 明确回答：是否存在 mdisp 大到 imm8 装不下（例如 1728）的条目？它在字节上用什么编码？
5. 若发现主张的措辞与字节不符，直接指出应如何订正（一句精确的话）。

## 交付
只输出一份结论清单：断言 N / FAIL M，每条带实测数字与地址。禁止预估。
脚本可写到 /tmp 下，不要写入项目目录除 _r208/x2_audit_tform.json 之外的任何位置。加 timeout 300。
