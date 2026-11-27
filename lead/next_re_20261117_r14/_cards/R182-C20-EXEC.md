# R182 执行卡 · C20 三方路径一致性（只读复核 + 独立复算）

## 你的角色
执行员（exec）。**只读**：不得修改任何文件，不得派生子代理。用时上限 8 分钟。

## 背景（一句话）
本仓有主门禁 lead/next_re_20261117_r14/check_disc.py，本轮（R182）在 C19 之后新增了 C20：
把 gate_runner.py 的 LEDGER 常量也纳入「三方路径必须指同一份台账」的判定。
C19 只守 facts_floors.EXPECT_CUR 与指针两方，gate_runner 那份从未被告知。

## 请逐条回答（每条都要给可复算的命令与输出）

Q1. 跑一次生产主门禁，确认它现在 exit 0 且输出里同时有 C19 与 C20 两个 ok 行。
    命令：cd /home/t628/projects/ra2-campaign-forge && python3 lead/next_re_20261117_r14/check_disc.py

Q2. 独立数一遍：check_disc.py 源码里 C20 块（从行首 '# ---- C20 [R182 新增]' 到行首 '# ---- C5 CR 抽查 ----'）
    内**是否出现任何版本号字面量**（形如 R17_R13x_FACTINDEX_Vnnn）。期望 0 处。给出你的计数命令与结果。

Q3. 独立核一遍三处的版本目录字面量是否**各自独立**：
    lead/next_re_20261117_r14/check_disc.py、/home/t628/projects/ra2-campaign-forge/_r160/facts_floors.py、
    /home/t628/projects/ra2-campaign-forge/_r161/gate_runner.py。
    逐文件给「形如 'R17_R13x_FACTINDEX_Vnnn' 的单引号字面量」出现次数，并说明 check_disc 的命中
    是否全部在注释里。

Q4. 复算 C20 的核心等式：三处（gate_runner.LEDGER 的 os.path.join(TIER, 'DIR', 'FILE')、
    facts_floors.EXPECT_CUR 的同形写法、指针文件 lead/next_re_20261117_r14/FACT_INDEX_CURRENT.md
    的「相对路径」字段）解析出的绝对路径是否字符串逐字相同。给出三者路径与你的解析方式。

Q5. 独立验证 C20 有分辨力（**只读、只在 /tmp 里做，绝不碰生产**）：
    把 gate_runner.py 与 check_disc.py 拷到 /tmp 下任意目录，在**拷贝**里把 gate_runner 的
    LEDGER 版本从 V563 改成 V562，然后**不要**运行整份 check_disc（那需要完整镜像），
    改用你自己的 5 行小程序复现 C20 的两条比较（runner vs facts、runner vs pointer），
    报告改前/改后这两条比较的真假。若你选择用完整 /tmp 镜像跑 check_disc，请注意：
    镜像里的 _r160 与 _r161 **必须建实体目录**，绝不能建成指向生产的软链 ——
    本项目 R182 已经因为软链 + unlink 误删过生产文件 _r160/facts_floors.py（26,147 B），
    恢复方式是对 R17_LEAD_BASELINE 里的备份做确定性重放。**请勿重犯。**

Q6. 读出 facts_floors.py 里 MASTER_SHA256 与 CUR_SHA256 两个常量的完整 64 位值，
    并跑 /home/t628/projects/ra2-campaign-forge/_r160/facts_floors.py 确认 exit 0。

Q7. 如实回答：C20 这条判据**能证什么、不能证什么**？请只用你自己的实测来支撑，
    不要复述卡面说法。特别地：三处**同时**改成指向同一份旧版本时，C20 会是绿还是红？

## 输出要求
把 Q1–Q7 的答案写进 /home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/_r182/r182_exec_report.md
（**只写这一个文件**）。每条给「命令 / 原始输出关键行 / 你的结论」。禁止判断题里没问的事。
