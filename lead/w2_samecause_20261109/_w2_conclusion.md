# W2 双时点同源检验结论（lead/w2_samecause_20261109/_w2_conclusion.md）

检验对象：lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md §4.2 条 2（:154）W2 最短触发链
中的假设「同一持续根因横跨 pre/post 两时点可一次造成」，及 :146 表行评级「罕见（同根因双时点；评级为推理）」。

## 绑定行（本轮 hashlib 实算，_w2_probe_out.txt B 节 9/9 MATCH）

W2 链载体（受核对象）MATRIX_DEFECT_REACHABILITY.md：
被核对象 SHA256 = cd03a91aac610cd0e7d6f3c70008d5a8d351896173aa0ee9d5d035675f2746d6，字节数 = 27825

两时点代码本体 lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py：
被核对象 SHA256 = ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2，字节数 = 412759

## 结论：部分同源

## 1. 两时点操作与依赖清单

T0 = make_pre（候选 :6623 调 → :4580-4613）：对 carrier_dir/"except.txt"（:6624）纯只读
exists(:4598)/stat(:4602)/sha256_file(:4607→:431-437 open 'rb')。位置在 backup :6619 之后、
launch :6701 之前；载体目录是本趟 :5153-5154 排他 os.mkdir 新建（c_{stamp}_{pid}，不复用）。

T1 = copy_post（finalize 第 1 项 :6166-6168 调 → :4701-4826）：src = carrier_dir/"except.txt"
（:4716，与 T0 同一路径串；finalize 的 carrier_dir = fin_carrier = TRIP_CARRIER["dir"] :7325 = 同一
新建载体）；读 :4756/:4766/:4767 + 写 dst = out_dir/except_post_*.txt（:4771-4772，out_dir=WORKDIR :7359，
载体在 WORKDIR/"ct" :6556 ⇒ 同卷同树不同目录）。读与写同在 :4755-4772 一个 try 内，任一异常 →
:4777-4785 ERROR×3 → :4786 read_error → :4788 classify → :4790 raise。T1 之前游戏已被
terminate_owned_process 终止并确认退出（:7307 → :1181-1235，:1199「返回值=进程退出是否已由本趟句柄确认」）。

| 依赖 | T0 make_pre | T1 copy_post |
|---|---|---|
| 源路径串合法/存在/stat | ✓ | ✓（同串同对象） |
| 源读数据 ACL | ✓（sha open） | ✓（read_bytes）同一条 |
| 源共享模式（他方独占拒读） | ✓ | ✓ |
| AV 对该路径扫描策略 | ✓（新建载体件） | ✓（崩溃写后件）——策略同、事件两次独立 |
| 载体卷可用 | ✓ | ✓（同卷） |
| 游戏进程句柄 | ✗（未启动） | △ 仅 term 失败（:7311/:7314-7318，finalize 照跑 :7358） |
| out_dir 存在/写 ACL/磁盘空间/新建件 AV 扫描 | ✗ | ✓（T1-only 整块） |

同一文件：是。同一目录：是。同一磁盘：是。同一句柄：否（两次独立 open）。

## 2. 实跑证据（写域内受控实验；python -I -X utf8；真函数经 importlib 静态装载、零改动）

_w2_probe.py → _w2_probe_out.txt：
- B：编排方 9 件指纹 9/9 MATCH（只读域零改动实算凭证）。
- D（R5）：非法字符(win123)/ENOTDIR(win3)/超长>260(win123) 三类路径 py3.12.10 下 Path.exists
  全部吞为 False → 真 make_pre 全落 absent_confirmed，**不产 error 态**（与连评件自身 out:149-150 一致）。
- E（ACL·deny-(RD)）：同一 ACE 持续下 T0 真 make_pre → state=error（exists=True，sha open
  PermissionError winerror 13）；T1 真 copy_post 同文件 → PermissionError → read_error →
  verdict=post_read_error（pre_state=error，正是 W2 格）。一因双时点复现成功。
- F（ACL·deny-R）：同样 stat 过、open 拒 → T0 error + T1 read_error（py3.12.10 对 winerror 5 不吞）。
- G（share-mode=0 独占句柄）：os.stat/exists 仍通过、open 拒 winerror 13 → 机理上独占句柄
  也能双时点拦读；但现实时序 T0 无游戏进程（见 §3-R1）。
- H（dst 写失败，out_dir=普通文件）：FileNotFoundError → read_error=post_read_error ⇒ 写侧失败
  也落 read_error，但它是 T1-only 源（make_pre 零写）。
- S0/S2 对照：无 deny 时 T0=present、T1 复制成功 leftover_unchanged/high——正常路径无异常。

_w2_probe2.py → _w2_probe2_out.txt：目录级 (OI)(CI) deny-RD 下，文件删除重建后新件仍拒读
⇒ 继承型 ACE 跨「游戏重建 except.txt」持续（游戏重建 vs 追加行为未验——零真机不允许）。

## 3. 六类共同根因逐判

- R1 游戏句柄独占：**只能致 T1**。T0 先于 launch（:6623<:6701）且载体每趟新建（:5153-5154），
  无游戏句柄可握；T1 需 term_ok=False（:7307-7318）。
- R2 ACL 拒读：**能同时致两处**（探针 E/F 实证；探针 2 证明目录继承形态跨重建持续；
  文件级形态是否持续取决于游戏追加/重建——未验）。
- R3 AV 实时扫描：**部分**——策略持续同源，锁事件瞬时独立；双时点命中需两次竞态。
- R4 磁盘满：**只能致 T1**（make_pre 零写；探针 H 证写侧失败落 read_error）。
- R5 路径过长/非法字符：路径串同（形式上同源），但探针 D 实证 py3.12.10 全被 exists() 吞为
  absent_confirmed ⇒ **不触发 W2 链**（copy_post 走 src_missing :4756-4764，连 read_error 都没有）。
- R6 进程退出句柄未释放：**不能致两处**。Windows 进程终止即内核关闭其全部句柄（OS 语义；
  :1199 退出确认语义）；T0 时本趟进程尚未启动。残余形态=游戏僵死未退（并入 R1，T1-only）。

## 4. 概率重估（评级=推理，零真机未实测，与连评件 :17 同口径）

- 桥接子集「源读面持续阻断」：目录继承 deny-ACE 属**环境常量**（要么 0 要么每趟必现，非罕见
  随机事件；台账 GOAL :9173-9174 仅有测试覆盖枚举命中、未见真机趟 error_pre_snapshot/post_read_error
  记录——未验硬证明）；AV 对该路径持续拦截 ~1e-5–1e-3/趟。
- 「AV 瞬时锁」双击（连评件括号内成因之一）：非持续根因，需 T0/T1 两次独立竞态，~1e-6–1e-4/趟
  （极罕见档）。
- 不同源反事实（两独立因）：~1e-7–1e-5/趟（极罕见档）。
- ⇒ 「罕见」仅在把桥接限定为「源读面持续阻断」时成立；按现措辞（AV 瞬时锁算持续根因）偏高。
  W2 本体是文档标签误配（裁决件 RULING_MATRIX_AB.md:50/:60「两出口独立可同现、活性误配、取值层
  无损」），本轮探针 S1 独立复现误配（pre=error × read_error → post_read_error ≠ :4 声称
  error_pre_snapshot）；频率修正影响优先级，不推翻误配成立性。

## 5. 修正措辞提案（只描述，不改那件）

对 MATRIX_DEFECT_REACHABILITY.md:154（§4.2 条 2）建议改为：
「make_pre 在 :6623 对载体 except.txt 采集抛异常（源读面**持续阻断**：ACL 拒读〔目录继承 deny-ACE，
跨文件重建仍持续〕/AV 对该路径持续拦截 → error 态；AV **瞬时**锁非持续根因，双时点需两次独立竞态；
路径异常在 py3.12.10 实测〔非法字符/ENOTDIR/超长〕均被 exists() 吞为 absent_confirmed，不产 error 态）
+ 同趟收尾复制对**同一源路径**再失败（同一 ACE/拦截持续 ⇒ 一因双时点；游戏句柄〔T0 未启动、
term 成功即句柄随进程终止关闭〕与磁盘满〔仅写侧〕均只在收尾时点成立，不能单独桥接）→ read_error
先截（out:26 vs out:28）→ :4 声称 error_pre_snapshot 与实码 PRE 不符」。
:146 评级格建议注记：「罕见」仅限源读面持续阻断子集（deny-ACE 为环境常量、台账可证伪；AV 持续拦截
~1e-5–1e-3）；AV 瞬时锁双击 ~1e-6–1e-4、两独立因 ~1e-7–1e-5（均极罕见档）。

## 纪律自检

零真机（未启动 gamemd.exe/ra2loader/YURI.exe、未 taskkill、未读活进程内存）；零采样（无 hook/
MiniDump/SuspendThread/StackWalk/注入/动态内存解析）；受控文件操作（icacls deny/独占句柄/建删
临时件）全部落唯一写域 lead/w2_samecause_20261109/；只读域经 9 件指纹实算零改动；未 commit、未 push。
