# CONT-MAIN01：EXP001 收尾与可信门禁修复

依据 PROJECT_DIRECTION.md、WORK_CHAIN.md 及用户本轮授权。Codex 路线裁定：先修复会把坏证据放行的门禁，再依赖其推进安全补丁；暂不实施引擎 Hook、存档、联机及 ra2opt apply。

原普通调度会话 session-a8c40820-2b10-4970-a8a4-82646bb93d73 复用。先确认工作区 3796a7ca-9fbe-4b5f-a605-372270afdeef 的路径和成员关系、当前模型、goal、所有旧任务终态及 Harness 运行上限。禁止重启、取消或重复派工。

第一包收尾：核对 B-r1b、E-r1、I′、J6、FV4 真件。acceptance.json 的 rework_log 仍有 IN FLIGHT，STATUS.md 下一步及跨线状态也过期；以实际终态更新，仅本会话写 EXP001/control/**、EXP001/STATUS.md。旧快照不删除，哈希注明测量时点；任何新编辑后的 JSON 须重新真实解析。

第二包 GI-FIX01：唯一实现者写 tools/audit_bytes.py、tools/verify_anchors.py、out/re_work/work_chain/CONTINUE_20261003/main/worker/**；独立审计者只写同级 review/**；调度者只写同级 control/**。其余文件、游戏镜像、原 claims、ra2* 代码只读。开始前确认这两工具没有其他活动写者。

先复现再修：claims 不匹配/不可读必须非零；空 claims 或空期望字节不能 PASS；格式错误明确非零，不能静默丢弃坏行。保留合法 BSS 声明，独立读取 PE 核对文件范围与虚拟零填充边界，不假装 BSS 有磁盘字节。新增正整数 --min-claims，显式全库门禁使用 --min-claims 323；与 --limit 互斥，抽样输出明确范围，不称全库或生产安全放行。不要把 323 硬编码成所有合法小样本的最低数，不以数量当语义覆盖率。

保留修前快照，使用合成 PE/claims 及实际镜像只读回归。验收须包含正确小集、单字节错误、不可读 VA、空文件、只有注释、空字节/坏格式、BSS 边界、最小数不足与参数互斥；记录真实命令、解释器、stdout/stderr、退出码及前后指纹。审计算法不调用被审映射器；负控必须先证明能击穿修前版本。修改算法争议交 Codex，禁止为变绿弱化判据。

外部仅 Antigravity/ZCode/Qoder CN；内部仅 xiaomi/mimo-v2.6-flash、step/step-3.7-flash、step/step-5-preview。显式核验身份。实现与审计有依赖，收尾复核与实现可在互斥写域并行。原调度者不得自己代写执行实现。后台 notify_complete=true 或当前通道等效回执。DSH shell 已知异常，不反复探针或绕过权限。

公共索引唯一写者为本总协调会话；先只维护 CONTINUE_20261003/main/control/INDEX.md，汇总另外两线只读结果，不写其 control。先报告真实执行 running/等待依赖/待验收和 task ID；必要工作实际派出后回报，accepted 不算验收。
