# -*- coding: utf-8 -*-
"""帧沿触发采样候选件（D-20 步骤 A）——**候选，未定谳，未校准**。

⚠️ 本文件内建两个**必须保留**的未证标记，任何下游分析不得移除：
    MARKER_ALPHA_UNCALIBRATED  ——「代理量 → 成本时间」的 alpha 映射未校准（D-19 判 F4）
    MARKER_SUFFICIENCY_UNPROVEN ——「采样充分性」未证（D-19 判 F2/F9/F10）

设计依据（逐条对应 D-19 裁决书 §1「执行步骤」第 4–6 条）：
  * 复用既有 500 Hz 帧号轮询；观测到 `CurrentFrame` 变化时**追加读取**四 VA；
  * **四 VA 地址不连续**（0x0087E8E0 / 0x00A8EC34 / 0x00B0CE88 / 0x00A8ED50），
    因此**不是**一次原子的 16 字节快照；本件逐次读取并逐次打时间戳；
  * 帧号**前后各读一次**，`f_pre != f_post` ⇒ 标 `cross_frame`，样本归属为
    「跨帧区间 [f_pre, f_post]」，**不硬认某一帧**；
  * `df > 1` ⇒ 标 `edge_missed`（漏沿），**不做逐帧插值、不补造中间帧**；
  * `df == 0` ⇒ 帧号冻结，累计**冻结持续时段**，但**不宣称业务字段冻结**；
  * `df < 0` ⇒ 重置 / 回绕 / 进程重启**无法区分**，该区间标 `unjudgeable`；
  * 任一次读取失败 ⇒ 该字段记 `None`，**绝不补 0**。

权限边界（写入本文件头部以免被误用）：
  本件是**候选件**，不是已验收的观测卡。真机使用须走隔离载体 + 清场复验，
  禁止 taskkill 生产进程、禁止修改用户存档、禁止 hook / 注入 / 挂线程 / dump。

作者：RE 线驱动器（自做）。零真机、本文件不含任何自动发射逻辑。
"""

from __future__ import annotations

import json
import time

# --------------------------------------------------------------------------
# 两个必须保留的未证标记
# --------------------------------------------------------------------------
MARKER_ALPHA_UNCALIBRATED = "alpha_uncalibrated"
MARKER_SUFFICIENCY_UNPROVEN = "sampling_sufficiency_unproven"

FIELD_MARKERS = (MARKER_ALPHA_UNCALIBRATED, MARKER_SUFFICIENCY_UNPROVEN)

# --------------------------------------------------------------------------
# 字段表（读序 = 此列表顺序，固定不得重排；重排会改变时间戳归属）
# --------------------------------------------------------------------------
FRAME_VA = 0x00A8ED84  # CurrentFrame（逻辑帧计数器 u32）

# (key, va, 语义一句话, 能不能说什么 / 不能说什么)
FIELDS = (
    (
        "gen_stamp",
        0x0087E8E0,
        "工作区代际【尝试】代理（PathFinder::GenerationStamp, this+0x28）",
        "能说：搜索入口/同步重试/回绕各推进了几次代际。"
        "不能说：实际展开节点数、单次搜索耗时、搜索是否成功。",
    ),
    (
        "threat_calls",
        0x00A8EC34,
        "索敌入口调用【累计】代理（Greatest_Threat 0x6F8DF0 入口自增）",
        "能说：入口被调用了几次。"
        "不能说：每次扫描了多少单位、扫描工作量、索敌耗时。",
    ),
    (
        "dirty_rect_count",
        0x00B0CE88,
        "脏矩形向量当前 Count（0x00B0CE78 向量 +0x10）",
        "能说：当前脏矩形队列里有几条。"
        "不能说：屏内可见单位数、每帧绘制调用数、渲染耗时；"
        "Count 少/为 0 不能单独排除渲染成本（合并/删除会改写它）。",
    ),
    (
        "bullet_count",
        0x00A8ED50,
        "注册 Bullet 对象向量 Count",
        "能说：注册表里有几个 Bullet 对象。"
        "不能说：本帧实际活跃更新数（更新另受对象 +0x98 活跃标志门控）、"
        "动画/伤害总成本。",
    ),
)

FIELD_KEYS = tuple(k for k, _, _, _ in FIELDS)

# 记录 schema 版本：改字段/语义必须升版，下游按版本拒收旧件
# V1→V2：修复读失败断裂状态机（A1 复核 R4）+ 键名自解释（R5）
# V2→V3：D-21 裁 A —— read_sample 增「复用前读」模式（每沿 5 读），
#        新增 f_pre_reused / reads_per_sample / ts.f_pre_anchor_known 三个字段
SCHEMA = "FRAME_EDGE_V3"

# dt/df 物理相容性上界：隐含帧率超过此值即记 implausible_df 告警。
# 取 1000 fps：远高于 YR 的 31.25 逻辑帧与任何实测（87 窗实测 1000/p50 = 5.5–31.6 Hz），
# 但仍能拦住「10 ms 内 df=50 ⇒ 5000 fps」这类明显不可能的读数。
MAX_PLAUSIBLE_FPS = 1000.0


# --------------------------------------------------------------------------
# 核心：纯函数式，不碰 Windows API，可离线单测
# --------------------------------------------------------------------------
def read_one(reader, va: int):
    """单次 u32 读取。reader(va) 失败必须返回 None（不得返回 0）。

    ★ 严格类型：`bool` 是 `int` 子类，但 `True/False` 绝不该冒充读数 ⇒ 拒收。
    ★ 越界（<0 或 >0xFFFFFFFF）⇒ 拒收，不当成有效计数。
    """
    try:
        v = reader(va)
    except Exception:
        return None
    if isinstance(v, bool):
        return None
    if not isinstance(v, int):
        return None
    if v < 0 or v > 0xFFFFFFFF:
        return None
    return v


def read_sample(reader, clock, f_pre=None, t_pre=None):
    """按固定读序采一个样本：帧号前读 → 四字段 → 帧号后读。

    返回 dict，字段齐全；任何失败项为 None（**不补 0**）。

    ★ D-21 裁 A（限定执行）新增「**复用前读**」模式：
      调用方若**已经**在上一拍读过帧号（既有 500 Hz 轮询本来就每拍读一次），
      把该读数与本拍读前时刻分别传入 `f_pre` / `t_pre`，
      本函数就**不再自读前帧号** ⇒ 每沿新增读由 6 次降为 **5 次**
      （四 VA + `f_post`），与 W4 `Q3_FRAME_EDGE_SPEC.md:318-328` 的 5 读设计对齐。
      - 传 `f_pre=None`（缺省）⇒ 保持原「自读前帧号」行为（6 次），**向后兼容、不改旧调用**。
      - 传 `t_pre` 时它必须是**外层读 `f_pre` 之前**取的时刻；
        **不得**把进入本函数的时刻冒充外层 f 的读前时刻（D-21 第 2 条）。
      - 无论是否复用，前锚的取值时刻都**只能界定在 (t_pre, 首个业务读起点) 内**，
        **不得宣称精确取数时刻**（W4 规格 §5.2 第 2 条）。

    时间戳口径（D-19 §1 第 5 条「每字段或读段起止时间戳」）：
      * `ts[key]` = 该次读取**发起之前**的 clock()（起点；读取延迟本身不可测）
      * `ts["f_post_start"]` / `ts["segment_end"]` = 读段的**闭合止点**
      * `ts["segment_start"]` = **业务追加段的起点**（复用模式下等于首个业务读之前那一刻，
        而**不是** S0 的读前锚 —— 两者在复用模式下是**不同**时刻，本函数分开记：
        `ts["f_pre"]` = 复用的外层读前锚 `t_pre`；`ts["segment_start"]` = 业务段起点）
      ★ 相邻字段之间的耗时上界 = 后一字段的 ts − 前一字段的 ts（含循环开销）。
    """
    reuse = f_pre is not None
    rec = {
        "schema": SCHEMA,
        "markers": list(FIELD_MARKERS),
        "va": {"frame": FRAME_VA},
        "ts": {},
        # ★ D-21：显式记录本样本走的是哪条路径，使「5 读 / 6 读」可被下游机械核对
        "f_pre_reused": reuse,
        "reads_per_sample": (5 if reuse else 6),
        "f_pre": None,
        "f_post": None,
        "cross_frame": None,
        "values": {},
    }

    if reuse:
        # 复用前读：不再调 reader(FRAME_VA)，也不再取新 clock() 当前锚
        rec["f_pre"] = f_pre
        if t_pre is None:
            # 没给外层读前时刻 ⇒ 当前锚**不可判**（记 None，不拿进入时刻冒充）
            rec["ts"]["f_pre"] = None
            rec["ts"]["f_pre_anchor_known"] = False
        else:
            rec["ts"]["f_pre"] = t_pre
            rec["ts"]["f_pre_anchor_known"] = True
    else:
        rec["ts"]["segment_start"] = clock()
        rec["ts"]["f_pre"] = rec["ts"]["segment_start"]
        rec["ts"]["f_pre_anchor_known"] = True
        rec["f_pre"] = read_one(reader, FRAME_VA)

    # 业务追加段起点：复用模式下与 S0 锚**分开**记（D-21 第 2 条）
    if reuse:
        rec["ts"]["segment_start"] = clock()

    for key, va, _sem, _bnd in FIELDS:
        rec["va"][key] = va
        rec["ts"][key] = clock()
        rec["values"][key] = read_one(reader, va)

    rec["ts"]["f_post_start"] = clock()
    rec["ts"]["f_post"] = rec["ts"]["f_post_start"]
    rec["f_post"] = read_one(reader, FRAME_VA)
    # ★ A1 复核（R2）修复：读段闭合止点。没有它就无法度量 f_post 的读取耗时，
    #   也无法得到整段突发墙钟（下游算「观测延迟」时必需）。
    rec["ts"]["segment_end"] = clock()

    # 只有前后两次都读到，才能判跨帧；否则 cross_frame 记 None（不可判）
    if rec["f_pre"] is None or rec["f_post"] is None:
        rec["cross_frame"] = None
    else:
        rec["cross_frame"] = bool(rec["f_pre"] != rec["f_post"])

    return rec


def classify_edge(prev_f, cur_f):
    """判定帧沿形态。返回 dict(kind=..., df=...)。

    kind ∈ {"unjudgeable", "same", "edge", "edge_missed"}
      unjudgeable——前后任一缺失，或 df < 0（重置/回绕/进程重启无法区分）
      same       —— 帧号未变（冻结段内）
      edge       —— df == 1，正常单帧沿
      edge_missed—— df >  1，漏沿（**不插值、不补造中间帧**）

    ★ 注意：本函数**不**负责区分「窗口首样本」与「读失败恢复点」。
      那两件事由 `FrameEdgeTracker` 用 `initialized` / `prev_lost` 两个正交状态处理，
      **不再用 `prev_f is None` 一个变量承载两种含义**（A1 复核 R4 的修复）。
    """
    if prev_f is None:
        return {"kind": "unjudgeable", "df": None}
    if cur_f is None:
        return {"kind": "unjudgeable", "df": None}
    df = cur_f - prev_f
    if df < 0:
        return {"kind": "unjudgeable", "df": df}
    if df == 0:
        return {"kind": "same", "df": 0}
    if df == 1:
        return {"kind": "edge", "df": 1}
    return {"kind": "edge_missed", "df": df}


class FrameEdgeTracker:
    """帧沿跟踪器：喂 (t, f_post) 的帧号序列，产出沿事件与冻结段统计。

    只在**帧号变化**时产出一个 edge 事件（含该次读取的四字段样本）。
    冻结段（帧号连续相同）单独累计持续时长，**不宣称业务字段冻结**。
    """

    def __init__(self):
        self.prev_f = None
        self.prev_t = None
        self.freeze_start_t = None
        self.freeze_max_s = 0.0
        # ★ A1 复核（R4）修复：把「窗口首样本」与「上一轮读失败断裂」拆成两个正交状态。
        #   原实现只用 `prev_f is None` 一个变量承载两种含义，导致：
        #     [100, None, 100] ⇒ 跨断裂把两头判成 same，虚报 freeze_max_s
        #     [100, None, 150] ⇒ 跨断裂求差，虚报 edge_missed / missed_frames
        #   修复后：一旦出现 f is None 就置 prev_lost，恢复点一律记 unjudgeable，
        #   **不跨断裂比较、不跨断裂累计冻结、不跨断裂求差**。
        self.initialized = False   # 本窗是否已捕获过首个有效帧号
        self.prev_lost = False     # 上一轮采样是否读失败（数据流断裂）
        self.counts = {
            "samples": 0,
            "first": 0,
            "edge": 0,
            "edge_missed": 0,
            "unjudgeable": 0,
            "null_frames": 0,
            "null_fields": 0,
            "cross_frame": 0,
            # ★ 新增：恢复点（读失败后第一个有效帧号）——单列，不混入 unjudgeable
            "resume_after_loss": 0,
            # ★ 新增：dt/df 物理不相容的告警数（见 _df_dt_plausible）
            "implausible_df": 0,
        }
        # 漏沿累计：所有 edge_missed 的 df-1 之和 = 未观测到的帧数（下界）
        self.missed_frames = 0

    def feed(self, t, f, sample=None):
        """喂入一次观测。返回 edge 事件 dict 或 None。

        sample 为该次观测同时读到的四字段（可为 None = 只喂帧号）。
        """
        self.counts["samples"] += 1

        # ---------- 读失败：切断一切跨轮比较状态 ----------
        if f is None:
            self.counts["null_frames"] += 1
            # ★ 必须立刻切断冻结计时：否则读失败的墙钟会被算进「帧号未变」的时长
            self.freeze_start_t = None
            # ★ 标记数据流断裂：下一个有效帧号不可与断裂前的 prev_f 比较
            self.prev_lost = True
            return None

        # ---------- 窗口首样本 ----------
        if not self.initialized:
            self.counts["first"] += 1
            self.initialized = True
            self.prev_lost = False
            self.prev_f = f
            self.prev_t = t
            self.freeze_start_t = None
            return None

        # ---------- 读失败后的恢复点：不可与断裂前比较 ----------
        if self.prev_lost:
            # 跨断裂区间一律不可判：不产事件、不累计冻竭、不累计漏沿
            self.counts["resume_after_loss"] += 1
            self.prev_lost = False
            self.prev_f = f
            self.prev_t = t
            self.freeze_start_t = None
            return None

        cls = classify_edge(self.prev_f, f)
        # ★ 必须在覆盖 self.prev_t 之前抓住上一拍时刻：dt/df 判定与事件字段都要用它
        prev_t = self.prev_t

        if cls["kind"] == "unjudgeable":
            # df<0：重置 / 回绕 / 进程重启 三者当前不可区分
            self.counts["unjudgeable"] += 1
            self.freeze_start_t = None
        elif cls["kind"] == "same":
            # 冻结段：从首次同值开始计
            if self.freeze_start_t is None:
                self.freeze_start_t = prev_t if prev_t is not None else t
            span = t - self.freeze_start_t
            if span > self.freeze_max_s:
                self.freeze_max_s = span
        else:  # edge / edge_missed
            if self.prev_f is not None and self.freeze_start_t is not None:
                span = t - self.freeze_start_t
                if span > self.freeze_max_s:
                    self.freeze_max_s = span
                self.freeze_start_t = None
            if cls["kind"] == "edge":
                self.counts["edge"] += 1
            elif cls["kind"] == "edge_missed":
                self.counts["edge_missed"] += 1
                self.missed_frames += (cls["df"] - 1)
                # ★ dt/df 物理相容性检查：隐含帧率超过 MAX_PLAUSIBLE_FPS ⇒ 记告警
                if self._df_dt_plausible(cls["df"], prev_t, t) is False:
                    self.counts["implausible_df"] += 1

        self.prev_f = f
        self.prev_t = t

        if cls["kind"] in ("edge", "edge_missed"):
            ev = {
                "schema": SCHEMA,
                "markers": list(FIELD_MARKERS),
                "t": t,
                "f": f,
                "kind": cls["kind"],
                "df": cls["df"],
                # df>1 时样本归属为「自上一观测帧到本帧的聚合」，不是单帧真值
                "attribution": ("single_frame" if cls["df"] == 1
                                else "aggregate_over_%d_frames" % cls["df"]),
            }
            if cls["df"] > 1:
                ev["df_dt_plausible"] = self._df_dt_plausible(
                    cls["df"], prev_t, t)
            if sample is not None:
                ev["values"] = dict(sample.get("values") or {})
                ev["ts"] = dict(sample.get("ts") or {})
                ev["cross_frame"] = sample.get("cross_frame")
                if ev["cross_frame"]:
                    self.counts["cross_frame"] += 1
                self.counts["null_fields"] += sum(
                    1 for v in ev["values"].values() if v is None)
            return ev
        return None

    @staticmethod
    def _df_dt_plausible(df, t_prev, t_cur):
        """df 与墙钟间隔是否物理相容。

        判据：隐含帧率 df/(t_cur−t_prev) 不得超过 MAX_PLAUSIBLE_FPS。
        取 1000 fps 作上界（远高于 YR 的 31.25 fps 逻辑帧与任何实测值，
        但仍能拦住「10 ms 内 df=50 = 5000 fps」这类明显不可能的读数）。
        t 缺失或间隔 <=0 ⇒ 无法判 ⇒ 返回 None（不猜）。
        """
        if t_prev is None or t_cur is None:
            return None
        dt = t_cur - t_prev
        if dt <= 0:
            return None
        return (df / dt) <= MAX_PLAUSIBLE_FPS

    def stats(self):
        return {
            "schema": SCHEMA,
            "markers": list(FIELD_MARKERS),
            "counts": dict(self.counts),
            "missed_frames_lower_bound": self.missed_frames,
            # ★ A1 复核（R5）修复：键名自解释。旧名 `freeze_max_s` 会被下游自动化
            #   直接读成「业务冻结时长」，而它只是【帧号】连续未变的时长。
            "frame_clock_freeze_max_s": round(self.freeze_max_s, 6),
            "note": ("`frame_clock_freeze_max_s` 只说明【CurrentFrame 帧号】连续未变的"
                     "最长时段；不得据此宣称业务字段冻结（D-19 F5/F11）。"
                     "读失败的墙钟不计入（断裂会立刻切断冻结计时）。"),
        }


# --------------------------------------------------------------------------
# 记录格式化：JSON Lines，逐条自足（不依赖外部上下文）
# --------------------------------------------------------------------------
def to_jsonl(rec) -> str:
    """把一条记录序列化为单行 JSON（ensure_ascii=False，无内嵌换行）。"""
    return json.dumps(rec, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def parse_jsonl(line: str):
    """反序列化并做 schema 校验；不合规返回 None（不抛）。"""
    try:
        rec = json.loads(line)
    except Exception:
        return None
    if not isinstance(rec, dict):
        return None
    if rec.get("schema") != SCHEMA:
        return None
    return rec


# --------------------------------------------------------------------------
# 真机适配层（仅在显式启用时使用；本模块 import 不触发任何系统调用）
# --------------------------------------------------------------------------
class RpmReader:
    """只读 RPM 适配器：open → 多次 read → close。

    ★ 只在 `enable=True` 且给了明确 pid 时才尝试开句柄。
    ★ 不做进程枚举、不扫全机、不写目标内存、不注入。
    """

    def __init__(self, pid: int, enable: bool = False):
        self.pid = int(pid)
        self.enable = bool(enable)
        self.handle = None
        self.err = None

    def open(self):
        if not self.enable:
            self.err = "RpmReader disabled (enable=False)"
            return False
        try:
            import ctypes
            from ctypes import wintypes as wt
            k32 = ctypes.windll.kernel32
            k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
            k32.OpenProcess.restype = wt.HANDLE
            PROCESS_QUERY_INFORMATION = 0x0400
            PROCESS_VM_READ = 0x0010
            h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
                                False, self.pid)
            if not h:
                self.err = "OpenProcess failed err=%d" % ctypes.GetLastError()
                return False
            self.handle = h
            return True
        except Exception as exc:  # pragma: no cover - 平台相关
            self.err = "OpenProcess raised: %r" % (exc,)
            return False

    def read_u32(self, va: int):
        if self.handle is None:
            return None
        try:
            import ctypes
            from ctypes import wintypes as wt
            k32 = ctypes.windll.kernel32
            k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p,
                                              ctypes.c_void_p, ctypes.c_size_t,
                                              ctypes.POINTER(ctypes.c_size_t)]
            k32.ReadProcessMemory.restype = wt.BOOL
            buf = ctypes.c_uint32(0)
            got = ctypes.c_size_t(0)
            ok = k32.ReadProcessMemory(self.handle, ctypes.c_void_p(va),
                                       ctypes.byref(buf), ctypes.sizeof(buf),
                                       ctypes.byref(got))
            if not ok or got.value != ctypes.sizeof(buf):
                return None
            return buf.value
        except Exception:  # pragma: no cover - 平台相关
            return None

    def close(self):
        if self.handle is not None:
            try:
                import ctypes
                ctypes.windll.kernel32.CloseHandle(self.handle)
            except Exception:  # pragma: no cover
                pass
            self.handle = None


def now():
    return time.perf_counter()
