# S13-K8RECHK DISAGREE

D1 · **与裁决 §8.8「9 对是错源 ㉓ 的典型形态」不一致（数字层面）**。
实测可辩护/不可辩护 = **11/7**，与裁决的「+11、11 行可辩护」核心数字一致；但裁决括注的「9 对」与实测不符：
- 真正触发 ㉓ 成对争抢（基类死表 vs 派生活表、同一 global 同一 slot0）的是 **7 对**，对应 7 个不可辩护行（Bomb/Warhead/Weapon/Bullet/Kamikaze/Parasite/RadSite）。
- DamageGroup 是第 8 个容器族但无 global vptr 写（仅栈局部），**未形成成对争抢**；2 个普通类 dtor（0075E510/0065BED0）无对。
- 若按卡面自己的猜测「9 对 = 18 行（对/行混算）」，则 18 行全为 ㉓ 形态，与「11 行可辩护」直接矛盾。
⇒ 建议把 §8.8 该括注更正为「7 对 / 7 行不可辩护；另 1 族(DamageGroup)及 2 普通类未触发」。本卡不改 R14_COMMON.md，照 11/7 执行。

D2 · **DamageGroup 两行的口径边界（政策项，交 Lead 裁）**。
0048AFD0/0048B020 的 vt 无 global 绝对写。若「活 vptr」严格定义为「必须是某个 global 的终态值」，则这两行无活 vptr 见证，应转不可辩护（delta 11→9）。本卡按 RULING §8.8 ㉓ 字面（核「是否由构造器装、是否被 atexit 装、是否成对争抢」）——两行均不触发死表/争抢——判可辩护。见 UNKNOWNS #2。

D3 · **KamikazeControl 基类写点宿主函数归因**。
s3 自动函数边界把 0x54e31d 归到内层循环头 0x54e2e0（OTHER）；逐字节反汇编（EVIDENCE\DISASM_s4_out.txt）证实其真宿主为 atexit 析构器 0x54e2d0（push 0x54e2d0@0x54e293 → call 0x7C978A@0x54e2c7）。RECHECK_18.tsv 已按真值记 ATEXIT_DTOR，结论（不可辩护）不受影响。

D4 · **未改项声明**：未改台账 / R14_COMMON.md / COVERAGE\ / 其它卡目录（尤其未写 _audit\）；未 git commit；未写 ra2youli\。
