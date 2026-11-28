# R201 卡 C（审计员 deepseek，只读，<=30 回合）：复核三条口径订正

## 环境
工作目录 /home/t628/projects/ra2-campaign-forge。已有产物 _r200/*.py（R200 原脚本）与 _r201/m0_baseline.py、_r201/m1_omdiff.py、_r201/m2_retbody.py、_r201/m3_storelevel.py 及其 .json。共享模块 _r185/pe185.py。capstone 可用。禁止反引号。你是只读审计员：不要改任何文件，只写你自己的脚本到 _r201/audit_c.py 并运行。

## 待复核主张（主会话称已实测，请你独立复算，逐条给 CONFIRM 或 REFUTE 并给数字）
A1. R200 脚本 _r200/m11_subfill.py 的宿主三分类里，第三支 else 的代码判据是「not has_main and not has_sub」，但落盘命名与正文表述为 only_main（只装主表）——即命名与判据不一致。请打开该脚本核对代码原文并给出行号。
A2. 用 R200 原口径（CALLAT 目标宿主 + min(下一 CALLAT 目标, 宿主+4096) 窗口）能复现 (both,only_sub,only_main) = (251,0,11)、宿主 262、子表 store 697、main11 11。
A3. 该 11 个 only_main 宿主里，有 6 个其窗口内 has_main=True（装了主表），5 个窗口内零装表。请独立复算这 6/5 的划分与具体地址。
A4. R200 窗口会在函数中间被截断：对每个 only_main 宿主，其窗口终点 hi 等于「下一个 CALLAT 目标」，而该处并不是函数结束（不是 ret/int3 之后）。请统计 11 个宿主里有多少个满足 窗口终点处不是 ret/int3 边界。
A5. 改用「从宿主线性反汇编到第一条 ret/int3」的真实函数体后，262 个宿主的三分类不再是 251/0/11。请复算你得到的 both/only_sub/none 三数。
A6. 在 store 级（分母 697 条子表 store，依据其所属真实函数体内是否另有主表 store）三分类不是 152/537/8 之外的同一组数——请独立复算你的 both/only_sub/none 三数，并与 152/537/8 对比。
A7. R200 正文「251 个同函数内主表 + 子表双装」这一表述，在真实函数体口径下不成立（both 显著小于 251）。请给你的判定与数字。
A8. 另有独立事实：697 条子表 store 中 disp8 与 imm 的 COL mdisp 相等 686 条、不等 11 条；不等的那 11 条正是 mdisp==0 的「主表装 +4/+8」特例。请复算。

## 输出纪律
- 每条给 CONFIRM / REFUTE / UNDETERMINED + 你的实测数字 + 你用的判据一句话。
- 末尾给「主会话可能夸大或表述不准的地方」清单，若无可写「无」。
- 全部断言 PASS/FAIL，末尾 SUMMARY asserts=N fails=M。不写反引号。单条 timeout 900。
