# Harness Unlimited

DSH 本机辅助插件，依据用户“解除限制”的要求，将 Harness Pilot 的 `maxConcurrent=0` 应用于已经加载的任务管理器。只在下次启动任务前更新上限，保留现有任务实例、子进程和完成回执，不重载 Harness Pilot。

主插件源码已支持 0=不限数量，设置页也显示该含义；此辅助插件用于当前进程无需重启即可应用。运行时设置仍可改回正整数。只改变本地任务数量限制，不处理供应商限流、权限、模型或审批。

本机模块路径固定为 `D:/Project/dsh-harness-pilot/lib/tasks.js`。启用后会在 Harness Pilot 数据目录写 `unlimited-live.json`，便于核验宿主 PID 和应用时点。
