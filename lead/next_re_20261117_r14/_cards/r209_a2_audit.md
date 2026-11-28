# R209 A2 · 只读复核（精简版，5 项）：额外视图 vftable 三槽 thunk 三元组

你是审计员，只读。禁止修改任何文件。**严格 5 项，不要扩展，不要写长篇报告。**
被测对象：/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe
参考产物（可读，但不得作为唯一依据）：/home/t628/projects/ra2-campaign-forge/_r209/q3.json

## 只做这 5 项
- A. .text 段全域搜索字节模式 83 6C 24 04，对每个命中检查其后是否紧跟 1 字节立即数再跟 E9 rel32；
  给出命中总数。再对 81 6C 24 04 做同样检查（注意 81 后是 4 字节立即数，E9 在 +8，rel 在 +9，
  落点 = 该地址 + 13 + rel）。给出两类的地址列表与总数。
- B. 用下列判据重建 RTTI 对象定位器 COL 记录：在 .rdata 与 .data 中按 dword 扫描 w[k]，
  要求 w[k] 属于 {0,1,2}、w[k+2]==0、w[k+3] 落在 .data 段、w[k+4] 落在 .rdata 段、
  且 cstr(w[k+3]+8) 以 .?A 开头并以 @@ 结尾。给出记录总数。
- C. 按 w[k+4] 分组给出组数。再为每组找 vftable：在 .rdata 与 .data 中找所有值等于该 COL 地址的
  dword 位置 x，要求 dw(x+4) 落在 .text，唯一者取 vt=x+4。给出 vftable 总数与总槽数
  （槽数 = 从 vt 起连续、每 dword 都落 .text 的个数）。
- D. 统计有多少张 vftable 的槽值本身是第 A 项找到的 thunk 地址。对这些表，
  列出 (slot0,slot1,slot2) 三元组去重后的个数；统计三个槽的 thunk 立即数是否都等于该表
  对应 COL 的 mdisp（w[k+1]，有符号）。给分子/分母。
- E. 对第 D 项涉及的每个 thunk，跳到它的 E9 落点，反汇编该函数，找第一个 ret 指令的立即数。
  统计 slot0 落点的 ret 立即数集合、slot1 的、slot2 的。

## 纪律
- 最多 20 个回合内完成。先一条命令跑完 A 项，再一条跑 B+C，再一条跑 D+E。
- 禁止对整段 .text 开 capstone 的 detail 模式一次性 disasm（会 OOM）；只用小窗口。
- 每项输出 PASS 或 FAIL 加实测数字。最后一行：断言 5 项 / FAIL M 项。
- 严禁在任何输出里使用反引号。
- 如果你发现主会话的口径含混，用一句话点出即可，不要展开。
