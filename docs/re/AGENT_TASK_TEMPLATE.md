# 派工任务卡固定前缀模板（Lead 专用 · 强制附带）
# Mandatory Dispatch Prefix for All Delegated Agents

> **后续任务目标依据（2026-10-02）**：[项目目标与后续逆向方向](../PROJECT_DIRECTION.md)。新卡须填写下面的交付关联字段；既有静态取证禁令不因方向调整而解除，真机或实现任务须在专门任务卡中明确执行边界。

> 用法：任何派给 **Antigravity / DSH 子代理 / MiMo / ZCode** 的任务，**第一段必须是本模板**，只替换 `<>` 占位符，不得删节。
> 目的：让执行方从一开始就知道**边界、证据标准、回报格式**，避免交付后返工。
> 配套：回报格式见 `docs/re/AGENT_DELIVERY_FORMAT.md`（两者成对使用）。

---

```text
【任务卡 <TASK-ID>】<一句话目标>

◆ 项目方向：docs/PROJECT_DIRECTION.md
◆ 工作链：docs/WORK_CHAIN.md；调度/验收 DSH DeepSeek V4.1 Flash；执行 <harness/模型/会话或subagent ID>
◆ 执行池：外部仅 Antigravity / ZCode / Qoder CN（全部实际可用模型）；DSH 内部仅 MiMo V2.6 Flash / Step 3.7 Flash / Step 5 Preview；不得使用清单外外部产品或内部模型
◆ 难度与模型依据：<简单/中等/困难；风险、选型理由、额度切换原因；允许池见 WORK_CHAIN.md §2.1>
◆ 交付关联：<A 性能/稳定性 | B 安全修改 | C DLC框架/工具 | 独立审计 | 长期探索>
◆ 待解决问题/能力：<用户可见问题或交付缺口；已有证据与具体未知点>
◆ 验收场景与判据：<场景、指标、对照、重复次数；静态任务说明证据验收>
◆ 兼容影响：<原版行为 / 存读档 / 联机 / 内容包；不涉及项说明理由>
◆ 依赖与停止条件：<依赖卡、有效预算、命中或无法继续时的交付条件>
◆ 后续使用方与回填：<使用结果的任务/模块、证据登记路径>

◆ 执行方：<Antigravity | DSH子代理 | MiMo | ZCode>      ◆ 期望耗时：<X 分钟>
◆ 工作区：D:\Project\ra2-campaign-forge（Windows）
◆ 基线二进制：ra2youli\gamemd.exe（YR 1.001，MD5 4f37486e5b0dbe2ae5f45aeee0f98367），
  ImageBase 0x400000，.text VA 0x401000，FileOffset = VA - 0x400000 —— 【只读，禁止写盘】
  > 【W3-Lead勘误 E-W3-01】改前：FileOffset = VA - 0x400000；改后：FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)（本镜像 .text/.rdata/.data 为 VA − 0x400000，但 .rsrc/.detour 为 VA − 0x6FC000）；依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]

◆ 写作用域（越界即交付不合格）
  允许写：<路径清单>
  禁止写：ra2render\**、ra2youli\**（除明确授权项）、REVERSE_ENGINEERING_AND_PATCHES.md、
          其他 docs\re\*.md、任何他人产物目录
  纪律：要改别人文件时**不要直接改**，写进回报 [3] 勘误清单交 Lead

◆ 绝对禁止
  1) 启动游戏 / 进程注入 / 挂调试器 / 改 gamemd.exe      2) 伪造“已实测”标记
  3) 用推测充当结论                                    4) 越界写入

◆ 证据标准（每条结论必须可回溯）
  [实证] = VA + FileOffset + 原始机器码字节 + Capstone 反汇编 + xref 调用点
  [推演] = 基于 ABI/EFLAGS/栈平衡/编译器代码生成的严格推导
  [待实测] = 需真机动态拦截；必须给可执行取证步骤与判定标准
  机器可读断言写入 <claims 路径>，格式固定：0xVA = HEXBYTES # 注释
  反汇编一律**定点解码**（从已知函数入口或已确认边界起解），线性扫描结果只作候选

◆ 必答问题（逐条回答，缺一即不合格）
  Q1 ...
  Q2 ...

◆ 交付物
  <新文档路径 / 追加小节 / 脚本目录 / claims 路径>

◆ 自证门禁（必须实跑并把**原文输出**贴进回报）
  python tools\verify_anchors.py                      → 须 323/323 PASS
  python tools\audit_bytes.py <你的 claims.txt>       → 须全部 OK

◆ 回报格式：**严格按 docs/re/AGENT_DELIVERY_FORMAT.md 的 10 节骨架**输出
  [META]/[0]结论摘要/[1]逐条结论表/[2]证据块/[3]勘误/[4]未闭环/[5]作用域合规
  /[6]门禁原文/[7]风险红线/[8]交付物清单/[9]待裁决项
  缺节 = 交付不合格；勘误必须单列，不得藏在正文里
```

---

## 使用注意
1. **一个任务卡只装一个目标**；不相关的活拆卡（写作用域互斥优先）。
2. `ra2render/**` 同一时刻只允许一个写者；代码轨在飞时不得派文档轨去改同一主题。
3. 派卡时必须同时给 `--file`/priority paths（Antigravity）或附路径提示（DSH/MiMo），并声明权限姿态。
4. 回报到达后 Lead 的动作见 `AGENT_DELIVERY_FORMAT.md §D`（独立复算 → 越界扫描 → 门禁亲跑 → 抽验 → 登记）。
