# -*- coding: utf-8 -*-
"""D-13b 纯逻辑捕获编排状态机（零采样实现 / 零系统接口 / 零 import）。

授权与边界
----------
- 立 D-13b：lead/d27_ruling_20261106/RULING_D27.md:8（§0 定谳 main: B）。
- 上限：RULING_D27.md:32「本次不授权编写真实采样候选或执行采样……D-13b 的上限仅为
  离线设计、获准读取的既有离线材料分析和纯模型/合成数据单测」。
- 本文件是「纯模型/合成数据单测」的对象：只用 dict / list / tuple / str / int / float
  与纯 Python 控制流；本文件没有任何 import 语句，没有任何进程、内存或系统接口调用。
- 唯一写域：lead/d13b_design_20261106/（TASK.md:7）。

本状态机负责的四件事（题给分工）
--------------------------------
1. 窗内配额上限（quota_cap）
2. 冷却期（cooldown_ms）
3. 停止与回退转换（含正常退出路径）
4. 同一停滞被多次观察时的去重（事件匹配判定）

★ 三条裁决更正（写错即废；TASK.md:50-55 / RULING_D27.md:44、:48、:52）
----------------------------------------------------------------------
(1) 不写「长停不存在」。正确表述：当前 97 窗按现规则保留的事件中未识别到 >=1s 平台，
    语义漏检及跨场景代表性未闭合（RULING_D27.md:52）。
(2) 不把「停顿 >1s 即确认终局」当结束态真值。>1s 在本模型中只作 **[保守停止预算]**
    （budget_stop_ms）：命中后进入 DISARMED_BUDGET，只少采、不断言长停不存在，
    **不产生任何结束态语义状态**（RULING_D27.md:44、TASK.md:53、TASK.md:66）。
(3) n=1681（保留标签数）与 n=1737（full97 全部候选，含 56 个 false）不是同口径，
    不得直接对照（RULING_D27.md:48）。本模型不消费这两个数，仅作口径声明。

★ 必须避开的两处既有代码缺陷（TASK.md:59-66）
----------------------------------------------
- lead/stall_event_def_20261106/_stall_probe.py:169-189：整窗无推进无条件判 false 并
  continue，完全不看后续窗。⇒ 本模型 window_end 不无条件关闭停滞，而是保持 open_stalls
  打开、语义记 UNKNOWN，携带到后续窗再看（_enter_window 只归零窗内配额，不丢注册表）。
- lead/stall_event_def_20261106/_stall_probe.py:211-224：末段平台只看紧邻下一窗，
  未观察到恢复即判终局冻结。⇒ 本模型「未观察到恢复」一律 UNKNOWN；只有
  stall_recovered（正向证据）才写 RECOVERED，且绝不写终局语义真值。
  本模块的语义取值集合里根本不存在「结束 / 终局」这一项，见 SEM_* 与 SEMANTIC_VALUES。

★ 指标定位（RULING_D27.md:44、:67；TASK.md:119-121）
----------------------------------------------------
<50ms / <=20ms / <10ms / 最多 3 次 / >=3.0s 冷却 / 100ms 清理 / rc=0 全部是
[待论证指标]；模型通过不能验证真实运行上界，也不保证 rc=0。
系统调度时延、扰动、资源释放、真实栈可解析性均为 [未验]
（RULING_D27.md:42、:67；STALL_EVENT_DEFINITION.md:216、:218）。
本模型的时钟 t_ms 是合成逻辑时钟，不是任何真实系统时间。
"""

# ---------------------------------------------------------------------------
# 状态（观测会话的编排状态，不是对局语义状态）
# ---------------------------------------------------------------------------
ST_ARMED = "ARMED"                     # 已武装，可评估捕获
ST_COOLDOWN = "COOLDOWN"               # 冷却抑制中（可由时间回退）
ST_DISARMED_BUDGET = "DISARMED_BUDGET" # [保守停止预算] 命中后的少采态，非语义真值
ST_EXITED = "EXITED"                   # 正常退出路径的终态（观测会话结束，不是对局结束态真值）

STATE_VALUES = (ST_ARMED, ST_COOLDOWN, ST_DISARMED_BUDGET, ST_EXITED)

# ---------------------------------------------------------------------------
# 语义标签：★ 刻意不含任何「结束 / 终局 / 已证非停滞」取值。
# UNKNOWN 是本模型对「数据不足 / 未观察到恢复 / 缺窗」的唯一诚实输出。
# ---------------------------------------------------------------------------
SEM_UNKNOWN = "UNKNOWN"                  # 未知 / 数据不足 / 未观察到恢复
SEM_RECOVERED = "RECOVERED"              # 正向证据：帧号再次推进
SEM_ANOMALY_REWIND = "ANOMALY_REWIND"    # 帧号回滚异常（标异常，不当恢复、不当终局）
SEM_BUDGET_ONLY = "BUDGET_STOP_ONLY"     # 保守停止预算命中，仍非语义真值

SEMANTIC_VALUES = (SEM_UNKNOWN, SEM_RECOVERED, SEM_ANOMALY_REWIND, SEM_BUDGET_ONLY)

# ---------------------------------------------------------------------------
# 观测种类（合成 / 既有离线时序的事件流，纯数据）
# ---------------------------------------------------------------------------
KIND_STALL = "stall_ongoing"       # 停滞持续观察（携带 stall_id / duration_ms）
KIND_RECOVERED = "stall_recovered" # 正向恢复证据
KIND_WINDOW_END = "window_end"     # 窗末截断 / 整窗无推进
KIND_WINDOW_GAP = "window_gap"     # 缺窗
KIND_REWIND = "frame_rewind"       # 帧号回滚
KIND_UNKNOWN = "unknown"           # 未知状态 / 数据不足
KIND_TERMINATE = "terminate"       # 显式正常退出请求（不是由「未观察到恢复」推断）

KIND_VALUES = (KIND_STALL, KIND_RECOVERED, KIND_WINDOW_END, KIND_WINDOW_GAP,
               KIND_REWIND, KIND_UNKNOWN, KIND_TERMINATE)

# ---------------------------------------------------------------------------
# 参数依据（每个数字都必须带定位标记；RULING_D27.md:44 / TASK.md:119-121）
# ---------------------------------------------------------------------------
PARAM_BASIS = {
    "quota_cap": "[待论证指标] STALL_EVENT_DEFINITION.md:206（单测量窗内最多允许采样 3 次）；"
                 "RULING_D27.md:44 把『最多 3 次』定为待论证指标，模型通过不背书真实上界",
    "cooldown_ms": "[待论证指标] STALL_EVENT_DEFINITION.md:206（两次采样间隔强制冷却 >=3.0s）；"
                   "RULING_D27.md:44 / :67 不背书",
    "budget_stop_ms": "[保守停止预算][待论证指标] STALL_EVENT_DEFINITION.md:207（>1.0s 去使能）"
                      "经 RULING_D27.md:44、TASK.md:53 更正：只可作保守停止预算，不得当结束态真值；"
                      "停止只会少采，不会把长停误判为不存在（TASK.md:66）",
    "threshold_ms": "口径 B 定义值（离线可复算）：_stall_probe.py:28（T_DEFAULT=0.100）、"
                    ":100（dur >= thr）、STALL_EVENT_DEFINITION.md:31（d>=T=0.100s）。"
                    "矛盾提示：STALL_EVENT_DEFINITION.md:191 自身判定累积判定耗时 >=100ms 不合格"
                    "（已记入 BUDGET_MODEL.json 段②）；本模型只做门槛门控，不改判定口径",
    "exit_budget_ms": "[待论证指标][未验] STALL_EVENT_DEFINITION.md:208（100ms 内零残留 / rc=0）；"
                      "RULING_D27.md:67 明确不背书；本模型仅记录该数值与状态转换，不验证",
    "retry_policy": "[估算] 设计选择（非实测）：同一停滞在首次成功捕获之前，后续观察可重新过门；"
                    "一旦 captured=True 即永久去重。真实运行行为 [未验]",
}

# ---------------------------------------------------------------------------
# 必列未验（RULING_D27.md:42、:67；TASK.md:115；STALL_EVENT_DEFINITION.md:212-219）
# ---------------------------------------------------------------------------
UNVERIFIED = (
    "系统调度时延 / 轮询到发指令的真实耗时 [未验]（RULING_D27.md:42）",
    "GC / 分页影响与采样扰动对帧率的影响 [未验]（STALL_EVENT_DEFINITION.md:218）",
    "资源释放时序 / 100ms 零残留 / rc=0 [未验][待论证指标]（RULING_D27.md:67）",
    "真实调用栈格式与可解析性 [未验]（STALL_EVENT_DEFINITION.md:216）",
    "被测线程实际响应 / 目标线程精准定位 [未验]（STALL_EVENT_DEFINITION.md:201、:218）",
    "首次在线观察延迟（中断 / 调度）及真实首次采到时刻 [未验]（BUDGET_MODEL.json 段①）",
)

# 默认参数（全部可由构造参数覆盖，便于合成时序单测）
DEFAULT_QUOTA_CAP = 3            # [待论证指标]
DEFAULT_COOLDOWN_MS = 3000.0     # [待论证指标] >=3.0s
DEFAULT_BUDGET_STOP_MS = 1000.0  # [保守停止预算][待论证指标] >1.0s
DEFAULT_THRESHOLD_MS = 100.0     # 口径 B 定义值（离线可复算）
DEFAULT_EXIT_BUDGET_MS = 100.0   # [待论证指标][未验]


class CaptureStateMachine:
    """纯逻辑捕获编排状态机。所有状态都是普通 Python 数据结构。

    输入：process(obs) 接收一个 dict（合成 / 既有离线时序）：
        {
          "t_ms": float,          # 合成逻辑时钟（ms），不是真实系统时间
          "window": str,          # 测量窗 id
          "stall_id": str | None, # 停滞的物理身份（由离线检测器给定，独立于测量窗；
                                   #   跨窗同一停滞沿用同一 stall_id 即可合并去重）
          "frame": int | None,    # 观察到的帧号
          "duration_ms": float,   # 该停滞当前累积的恒帧时长
          "kind": str,            # KIND_* 之一
        }
    输出：一个 action dict（decision / reason / state_before / state_after / semantic ...），
          同时追加进 self.actions；decision == "CAPTURE" 的另追加进 self.captures。

    ★ 本类不触碰任何进程、内存或系统接口；不读活数据；不自行补采。
    """

    def __init__(self, quota_cap=DEFAULT_QUOTA_CAP,
                 cooldown_ms=DEFAULT_COOLDOWN_MS,
                 budget_stop_ms=DEFAULT_BUDGET_STOP_MS,
                 threshold_ms=DEFAULT_THRESHOLD_MS,
                 exit_budget_ms=DEFAULT_EXIT_BUDGET_MS):
        self.quota_cap = int(quota_cap)                     # [待论证指标]
        self.cooldown_ms = float(cooldown_ms)               # [待论证指标]
        self.budget_stop_ms = float(budget_stop_ms)         # [保守停止预算][待论证指标]
        self.threshold_ms = float(threshold_ms)             # 口径 B 定义值
        self.exit_budget_ms = float(exit_budget_ms)         # [待论证指标][未验] 仅记录，不验证

        self.state = ST_ARMED
        self.window = None
        self.window_capture_count = 0
        self.last_capture_t_ms = None

        self.seen = {}              # stall_id -> 去重记录（与 open_stalls 共享同一 dict 对象）
        self.open_stalls = {}       # stall_id -> 尚未被正向恢复解析的记录
        self.distinct_stall_count = 0

        self.captures = []          # decision == CAPTURE 的 action 列表
        self.actions = []           # 全部 action 列表
        self.audit = []             # 状态转换 / 决策审计（纯数据）

    # -- 内部工具（纯数据） -------------------------------------------------
    def _note(self, t_ms, msg):
        self.audit.append({"t_ms": t_ms, "state": self.state, "msg": msg})

    def _act(self, t_ms, window, stall_id, decision, reason,
             state_before, state_after, semantic, extra=None):
        a = {
            "t_ms": t_ms,
            "window": window,
            "stall_id": stall_id,
            "decision": decision,
            "reason": reason,
            "state_before": state_before,
            "state_after": state_after,
            "semantic": semantic,
        }
        if extra:
            a.update(extra)
        self.actions.append(a)
        if decision == "CAPTURE":
            self.captures.append(a)
        return a

    def _enter_window(self, win, t_ms):
        """换窗：只归零窗内配额；dedup 注册表与 open_stalls 一律保留（跨窗可合并）。

        这正是对 _stall_probe.py:169-189「完全不看后续窗」的反向设计：不丢未解析停滞。
        """
        prev = self.window
        prev_state = self.state
        self.window = win
        self.window_capture_count = 0
        if self.state == ST_DISARMED_BUDGET:
            # 回退路径之二：按窗界解除保守停止预算（预算是逐窗的，不是终局语义）。
            self.state = ST_ARMED
            self._note(t_ms, "[回退] 新测量窗 %r 开始：按窗界解除 [保守停止预算]，"
                       "DISARMED_BUDGET -> ARMED；先前停滞语义仍 UNKNOWN，不改写为结束态真值" % win)
        self._note(t_ms, "换窗 %r -> %r：窗内配额计数归零（entry_state=%s）；"
                   "dedup 注册表与 open_stalls 保留，支持跨窗合并 / 后续窗恢复"
                   % (prev, win, prev_state))

    # -- 主转换 -------------------------------------------------------------
    def process(self, obs):
        t_ms = float(obs["t_ms"])
        win = obs.get("window")
        sid = obs.get("stall_id")
        frame = obs.get("frame")
        dur = float(obs.get("duration_ms", 0.0))
        kind = obs.get("kind", KIND_UNKNOWN)

        # (0) 正常退出后幂等：EXITED 是观测会话终态（不是对局结束态语义真值）
        if self.state == ST_EXITED:
            return self._act(t_ms, win, sid, "SKIP", "EXITED_IDEMPOTENT",
                             ST_EXITED, ST_EXITED, SEM_UNKNOWN)

        # (1) 换窗：窗内配额归零，跨窗 dedup 不归零
        if win != self.window:
            self._enter_window(win, t_ms)

        # (2) 冷却期到点：回退到 ARMED（抑制的回退转换；>= 边界按 :206「>=3.0s」）
        if (self.state == ST_COOLDOWN and self.last_capture_t_ms is not None
                and (t_ms - self.last_capture_t_ms) >= self.cooldown_ms):
            self.state = ST_ARMED
            self._note(t_ms, "[回退] 冷却期 %.1fms 已过，COOLDOWN -> ARMED" % self.cooldown_ms)

        sb = self.state  # 本次决策前的状态（已含上述自动调整）

        # (3) 正常退出路径：显式请求 -> EXITED。★ 不是由「未观察到恢复」推断出来的。
        if kind == KIND_TERMINATE:
            self.state = ST_EXITED
            self._note(t_ms, "[正常退出路径] -> EXITED；100ms 零残留 / rc=0 为 "
                       "[待论证指标][未验]，模型仅记录状态转换，不验证真实资源释放")
            return self._act(t_ms, win, sid, "EXIT", "NORMAL_EXIT",
                             sb, self.state, SEM_UNKNOWN,
                             {"exit_budget_ms": self.exit_budget_ms,
                              "note": "[未验] 资源释放时序不由本模型验证"})

        # (4) 正向恢复证据：唯一能写 RECOVERED 的输入；并可回退保守停止预算
        if kind == KIND_RECOVERED:
            rec = self.seen.get(sid)
            if rec is not None:
                rec["semantic"] = SEM_RECOVERED
                rec["resolved"] = True
                self.open_stalls.pop(sid, None)
            if self.state == ST_DISARMED_BUDGET:
                # 回退路径之一：正向证据到位，保守停止的理由消失
                self.state = ST_ARMED
                self._note(t_ms, "[回退] 收到正向恢复证据，[保守停止预算] 解除，"
                           "DISARMED_BUDGET -> ARMED；不把先前停止改写成结束态语义真值")
            return self._act(t_ms, win, sid, "OBSERVE", "RECOVERY_OBSERVED",
                             sb, self.state, SEM_RECOVERED)

        # (5) 窗末截断 / 整窗无推进：不无条件判 false、不判终局；停滞保持打开
        if kind == KIND_WINDOW_END:
            self._note(t_ms, "窗末截断：open_stalls=%d 保持打开，语义 UNKNOWN；"
                       "携带到后续窗再看（避开 _stall_probe.py:169-189 / :211-224）"
                       % len(self.open_stalls))
            return self._act(t_ms, win, sid, "OBSERVE", "WINDOW_END_CARRIED",
                             sb, self.state, SEM_UNKNOWN,
                             {"open_stalls": len(self.open_stalls)})

        # (6) 缺窗：数据缺口 / 未观察到恢复 ≠ 终局；停滞保持打开
        if kind == KIND_WINDOW_GAP:
            self._note(t_ms, "缺窗：未观察到恢复不等于结束；open_stalls 保持打开，语义 UNKNOWN")
            return self._act(t_ms, win, sid, "OBSERVE", "WINDOW_GAP_UNKNOWN",
                             sb, self.state, SEM_UNKNOWN,
                             {"open_stalls": len(self.open_stalls)})

        # (7) 帧号回滚异常：不当恢复、不当终局，抑制本次捕获，语义标异常
        #     对应 RULING_D27.md:48：53 条排除标签的独立状态语义未全量核验，
        #     本模型不宣称「已证非真实停滞」。
        if kind == KIND_REWIND:
            rec = self.seen.get(sid)
            if rec is not None:
                rec["semantic"] = SEM_ANOMALY_REWIND
            self._note(t_ms, "帧号回滚：标为异常并抑制本次捕获；不写结束态语义真值，"
                       "也不宣称该停滞不存在（RULING_D27.md:48）")
            return self._act(t_ms, win, sid, "SKIP", "FRAME_REWIND_ANOMALY",
                             sb, self.state, SEM_ANOMALY_REWIND)

        # (8) 未知状态 / 数据不足：诚实输出 UNKNOWN，抑制捕获，不改状态
        if kind == KIND_UNKNOWN:
            return self._act(t_ms, win, sid, "SKIP", "UNKNOWN_INSUFFICIENT_DATA",
                             sb, self.state, SEM_UNKNOWN)

        if kind != KIND_STALL:
            return self._act(t_ms, win, sid, "SKIP", "UNRECOGNIZED_KIND",
                             sb, self.state, SEM_UNKNOWN)

        # (9) 停滞持续观察：去重登记 + 预算停止 + 捕获门控 -------------------
        is_new = sid not in self.seen
        if is_new:
            rec = {
                "stall_id": sid,
                "frame": frame,
                "first_t_ms": t_ms,
                "last_t_ms": t_ms,
                "first_window": win,
                "windows": [win],
                "observation_count": 1,
                "max_duration_ms": dur,
                "captured": False,
                "semantic": SEM_UNKNOWN,
                "resolved": False,
            }
            self.seen[sid] = rec
            self.open_stalls[sid] = rec
            self.distinct_stall_count += 1
        else:
            rec = self.seen[sid]
            rec["observation_count"] += 1
            rec["last_t_ms"] = t_ms
            if dur > rec["max_duration_ms"]:
                rec["max_duration_ms"] = dur
            if win not in rec["windows"]:
                rec["windows"].append(win)

        # (9a) 去重门：同一物理停滞至多一次 CAPTURE（事件匹配判定）
        if rec["captured"]:
            return self._act(t_ms, win, sid, "SKIP", "DUP_ALREADY_CAPTURED",
                             sb, self.state, rec["semantic"],
                             {"observation_count": rec["observation_count"]})

        # (9b) [保守停止预算]：>1s 只少采，不断言长停不存在，不产生结束态语义状态
        if dur >= self.budget_stop_ms:
            self.state = ST_DISARMED_BUDGET
            rec["semantic"] = SEM_BUDGET_ONLY
            self._note(t_ms, "[保守停止预算] dur=%.2fms >= %.2fms -> DISARMED_BUDGET；"
                       "停止只会少采，不把长停误判为不存在（TASK.md:66）；语义仍非终局真值"
                       % (dur, self.budget_stop_ms))
            return self._act(t_ms, win, sid, "SKIP", "BUDGET_STOP_CONSERVATIVE",
                             sb, self.state, SEM_BUDGET_ONLY,
                             {"note": "[保守停止预算] 非语义真值"})

        # (9c) 阈值门：口径 B 定义值 100ms（dur >= thr，_stall_probe.py:100）
        if dur < self.threshold_ms:
            return self._act(t_ms, win, sid, "SKIP", "BELOW_THRESHOLD",
                             sb, self.state, SEM_UNKNOWN,
                             {"duration_ms": dur, "threshold_ms": self.threshold_ms})

        # (9d) 保守停止态下不捕获（直到正向恢复或换窗回退）
        if self.state == ST_DISARMED_BUDGET:
            return self._act(t_ms, win, sid, "SKIP", "BUDGET_STOP_CONSERVATIVE",
                             sb, self.state, SEM_BUDGET_ONLY)

        # (9e) 冷却门 [待论证指标]
        if self.state == ST_COOLDOWN:
            return self._act(t_ms, win, sid, "SKIP", "COOLDOWN",
                             sb, self.state, SEM_UNKNOWN,
                             {"remaining_ms": self.cooldown_ms - (t_ms - self.last_capture_t_ms)})

        # (9f) 配额门 [待论证指标]
        if self.window_capture_count >= self.quota_cap:
            return self._act(t_ms, win, sid, "SKIP", "QUOTA_EXHAUSTED",
                             sb, self.state, SEM_UNKNOWN,
                             {"window_capture_count": self.window_capture_count,
                              "quota_cap": self.quota_cap})

        # (9g) 通过全部门 -> CAPTURE（纯模型决策，不执行任何真实抓取动作）
        self.window_capture_count += 1
        self.last_capture_t_ms = t_ms
        self.state = ST_COOLDOWN
        rec["captured"] = True
        self._note(t_ms, "CAPTURE stall_id=%r window=%r（窗内第 %d/%d 次）-> COOLDOWN"
                   % (sid, win, self.window_capture_count, self.quota_cap))
        return self._act(t_ms, win, sid, "CAPTURE", "CAPTURE_GRANTED",
                         sb, self.state, SEM_UNKNOWN,
                         {"window_capture_count": self.window_capture_count})

    # -- 批量 / 报告（纯数据） ----------------------------------------------
    def run(self, observations):
        return [self.process(o) for o in observations]

    def dedup_report(self):
        return {
            "total_actions": len(self.actions),
            "raw_stall_observations": sum(r["observation_count"] for r in self.seen.values()),
            "distinct_stalls": self.distinct_stall_count,
            "captures": len(self.captures),
            "per_stall": [
                {"stall_id": sid,
                 "observation_count": r["observation_count"],
                 "windows": list(r["windows"]),
                 "captured": r["captured"],
                 "semantic": r["semantic"],
                 "max_duration_ms": r["max_duration_ms"]}
                for sid, r in sorted(self.seen.items(), key=lambda kv: str(kv[0]))
            ],
        }

    def summary(self):
        return {
            "state": self.state,
            "window": self.window,
            "window_capture_count": self.window_capture_count,
            "quota_cap": self.quota_cap,                 # [待论证指标]
            "cooldown_ms": self.cooldown_ms,             # [待论证指标]
            "budget_stop_ms": self.budget_stop_ms,       # [保守停止预算][待论证指标]
            "threshold_ms": self.threshold_ms,           # 口径 B 定义值
            "exit_budget_ms": self.exit_budget_ms,       # [待论证指标][未验]
            "exit_budget_verified": False,               # 模型不验证真实资源释放 / rc=0
            "distinct_stalls": self.distinct_stall_count,
            "captures": len(self.captures),
            "actions": len(self.actions),
            "audit_entries": len(self.audit),
            "open_stalls": sorted(self.open_stalls.keys(), key=str),
            "note": "[未验] 系统时延 / 扰动 / 资源释放 / 真实栈可解析性不由本模型验证",
        }
