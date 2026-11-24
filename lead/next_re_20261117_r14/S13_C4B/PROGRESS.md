结论：这 3 条 P1=0 / P2=3 / P3=0；P2 占全部 3 条，S13 不能靠补③语义达标，必须依赖 D-39 裁决。
# S13-C4B PROGRESS（≤30 行）
已开始。筛选 SURVEY_D39/EVIDENCE/classification.tsv：subsystem=S13 且 class=C4，实测 76 行。
第 1 条候选地址：00468670（BulletClass::slot124；体内已证直调 12 个、固定全局最多）。
第 2 条候选地址：00629FD0（ParasiteClass::slot23；已证直调 9 个）。
第 3 条候选地址：0062A260（ParasiteClass::slot10；已证直调 4 个 + 固定全局读写）。
目标只读：gamemd.exe SHA-256 73201CC0…F67476 现场复核一致；Python 3.12.10 + capstone 5.0.7 + pefile 2024.8.26；未建 venv / 未 pip install / 未 import 其他卡 work。
⑨ 停机核验：coverage.tsv 盘上重算 S13 n=240 / named(S)=216 / proved=89，与卡面一致。
⑲ 自检：0x4386AB 为 `call dword ptr [edx+0x10]`；op.mem.index=0；操作数无 op.index 属性。
⑱ 冲突只报不改名：00468670 有 OPEN name 冲突（C02_census:BulletClass::slot124 vs S13-K1:BulletClass::Move/Update）；另两条未见按 entry 冲突。
候选挑选理由：从 76 行中按「体内固定全局读写 + 体内镜像内串 + call 已证函数」排序，取最好情况上界；00468670/00629FD0/0062A260 命中已证直调数 12/9/4。
① 入口环：三条均有明确 entry + atlas size（1304/645/573），capstone 从入口按指令边界解码。
② 类属环：00468670 → RTTI COL=0x7E46E0、TD=0x81AF70、.?AVBulletClass@@；00629FD0/0062A260 → COL=0x7EF88C、TD=0x836640、.?AVParasiteClass@@。
③ 语义环（00468670）：12 个已证直调（Unlimbo/RemoveFromLayer/RandomRanged/_ftol/MapClass/GetCellFloorHeight/SetLayer），固定全局 0x89DE30/34/38、0xA8B230、0x8871E0，语义=Bullet 放置/位置/层更新。
③ 语义环（00629FD0）：固定全局 0xA8ED84/0x8871E0/0xA8B230，9 个已证直调（UpdateSquid/_new/ParticleSystemClass::ctor/FrameCRC/AnimClass::AnimClass/RandomRanged/_ftol），语义=Parasite 投射物生成/状态分支。
③ 语义环（0062A260）：固定全局 0xA8ED5C/0xA8ED84/0xA8E7AC/0xAC4948/4C/50，4 个已证直调（FrameCRC/ControlledByPlayer/SetFocus/RevealArea3），语义=目标切换/释放旧寄生目标并刷新控制与揭示。
④ 判据：只接受 E8 指令边界 direct call（site+5+rel32==entry、非自环），或静态 global 接收者 + 构造器活 vptr + vt[slot]==entry + site 不共用的 exact 派发。
④ 实扫：capstone skipdata=True 解出 1,392,592 条指令、6,728 个 direct-call 目标；3 个 entry 的 direct call 站点均为 0。
④ 实扫：严格 exact dispatch（静态 global + 活 vptr + vt[slot]==entry + site 不共用）对 3 个 entry 均 0 命中；未使用 atexit 表、槽号匹配、slot-baseline 或「P=R=100%」式自证。
分档：00468670=P2；00629FD0=P2；0062A260=P2。P1=0 / P2=3 / P3=0。
一句话回答：补了③语义后，这 3 条仍全部缺严格④，不能升 [已证]；S13 无法靠补语义达标，必须依赖 D-39 裁决。
交付：C4_CLASSIFY.tsv（3 行）；EVIDENCE/SUMMARY.txt；work/scan_candidates.py 等独立复跑脚本。
