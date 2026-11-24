# SMOKE-C 空跑验证结果

- 卡号：SMOKE-C
- 时间：2026-11-17T09:11+08:00 (Asia/Shanghai)
- 性质：空跑验证，未做任何逆向分析

## 环境版本

| 项 | 命令 | 输出 |
|---|---|---|
| Python | `python --version` | Python 3.12.10 |
| capstone | `python -c "import capstone; print(capstone.__version__)"` | 5.0.7 |
| pefile | `python -c "import pefile; print(pefile.__version__)"` | 2024.8.26 |

## 模型标识

- provider: `magpie-anthropic`
- model: `work/cn:deepseek-v4.1-flash`
- reasoningEffort: `high`
- 子代理标签: `Smoke test deepseek v4.1 flash`（continuable 模式，provider=spawn）

置信度：高。依据为本会话 session 日志中的 `subagent/descriptor`（seq 0）与
`request/context`（seq 15）记录，二者一致：
`{"provider":"magpie-anthropic","model":"work/cn:deepseek-v4.1-flash","reasoningEffort":"high"}`。

环境变量中无直接暴露模型名的 `DSH_*` 变量（仅有 DSH_HOME / DSH_PROFILE / DSH_SESSION_ID 等）。

## 约束遵守情况

- 写入范围：仅本目录 `RESULT.md`。
- 未读取 gamemd.exe、未运行 capstone/pefile 分析、未读取 EVIDENCE。
