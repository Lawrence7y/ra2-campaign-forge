# CONT-PERF01：测量工具交付核对与真实采样就绪证据

依据 PROJECT_DIRECTION.md、WORK_CHAIN.md、RESUME_20261003_PERF_INTEGRATE.md。复用普通会话 session-e2f68aee-3694-4dda-bf7c-32104e7b930b，核验工作区路径/成员、模型/goal 和旧任务终态。PERF-INT01 已交付：集成工具 sha256 bf17cd07bc36c0a63e350b139519a43628ae73ca22bfb4b588480ca777b1018c；原型 2e12948a84392c8e7877f632fb16d3f082787bb2ce0dbbd496179712aa46106c。本轮不重做集成，先验证现件、退出码与已记录证据是否相符。

Codex 裁定 PD-CARD-01 基准身份钉桩归本性能普通会话，原 EXP001 队友不得重复执行。下一步先离线建立真机采样的就绪证据；不把名义 H1 单位数当 actual_units，不把 ra2opt 改过的 exe 当 pristine。

拆两包并行，单写者：BASE-ID 包只写 out/re_work/work_chain/CONTINUE_20261003/perf/baseline/**，只读核对 ra2bench、ra2youli、原备份的 exe/DLL/INI/H1 地图指纹与来源，提取实际单位计数工具和旧 H1 证据的能力/缺口，给出原版、补丁关闭、开启三臂是否真实可构造。不能复制/部署/安装游戏文件。CRASH-TRIAGE 包只写同级 crash/**，只读盘点实际 except/log/dump、复现与已有候选根因，区分真崩溃、正常退出、仪器失败；无 dump/调用栈则明确不足，不能编造根因。

调度者独立复算与状态只写同级 control/**。独立审计只写同级 review/**，待两个包完成再核验关键指纹与至少一条不存在文件/错误哈希负控。每条证据写真实路径、时点、命令退出码与算法。内部 shell 无效的命令验证交有效的获准外部通道。

交付包含下一张 LIVE-M0 采样卡草案：专用 ra2bench、实际单位计数来源、固定步骤、三次重复、帧/tick 分离、仪器开销、重复性/缺测处理、预算、停止条件和独占实例。该草案交 Codex 裁定后执行；本卡不启动游戏、不写进程内存、不改 Hook、配置、存档或联机行为。

外部仅三家，内部仅获准三模型，禁止两条官方 DeepSeek 路由。核对后台 maxConcurrent=0 与在飞任务，不重启/取消。真实可并行两包立即派出，记录 task ID、实际模型与回执；不要把派发 accepted 当完成。本普通会话独立验收并向主协调索引提供只读路径，不写总表。
