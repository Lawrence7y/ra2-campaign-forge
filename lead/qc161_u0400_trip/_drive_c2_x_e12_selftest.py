# -*- coding: utf-8 -*-
"""_drive_c2_x_e12_selftest.py — E12 候选驱动件的离线自检套件（全离线，零真机，零游戏启动）。

覆盖派单要求的六类：
  A 组 组件分臂 mock：闩检测切换 / 慢采样节律（0.1 s→1 Hz）/ hook6 与锚比对 / CPU 增量计算 /
      闩+30 s 截图 / 窗口枚举通道逐秒独立 / 输出 schema（close_rows 兼容 + _e2 附加段）/
      分叉表两主臂（P1/丁）/ finalize 全套
  B 组 三态与故障注入：哨兵读败显式（不误判闩）/ hook6 轴读败 / CPU 返回 None（句柄权不足形）/
      CPU 抛异常 / CPU 基线即败 / ws 读败 / 枚举异常 / OpenProcess=0（权限缺失）/ 残留进程 /
      BOOT 变化 / 投递失败 / 零样本 / 载体创建失败 / 载体身份不符 / 兑现趟自然退
  C 组 通用停止条件：#32770/确认/保存/网络命中 ⇒ 停+只留证据不升级；非交互新窗 ⇒ 保守停；
      except 哈希中途变化 ⇒ 停；既有窗不触停；停止趟 finalize 仍跑
  D 组分叉标签机（§9 A4 语义逐臂）：spin×在位⇒P1 / spin×不在位⇒丁 / ≈0⇒阻塞族 /
      中间带⇒ambiguous / CPU 不可读⇒不冒充 / hook6 读败⇒undetermined / 混合态 / ws 增长注记 /
      未闩与闩后零行不虚构
  E 组 硬闸：gate_decision 四组合 + 真子进程实测（无参=0、--approved=0、--live=3、
      --live --selftest 自检优先）+ 母版哈希自验拒不符/拒不可读
  F 组 变异（关键行改动⇒预期必红）：闩常量 / 节律旁路 / 哨兵读败吞成假值 / hook6 读败吞成不在位 /
      CPU 分母 / 慢行旁路 / 停止旁路 / finalize 跳过 / BOOT 断言旁路 / live 闸篡改 /
      E2 段删除 / 交互关键字清空 / 闩+30 截图旁路

纪律：替身=替换 v2 模块的 OPS 字典与模块属性（v2 run_fault_tests 同法），测后必还原；
MYCARD/GAME_SRC 等指向 tempfile 沙箱；真实冻结件/载体树/游戏目录/台账零写入；
子进程测 argv 无「--live --approved」组合 ⇒ 绝无发射路径；子进程以 E12_SUITE_NO_CHILDREN 防递归。
"""
import hashlib
import importlib.util
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

DRIVER_PATH = HERE / "_drive_c2_x_e12.py"
V2_PATH = HERE / "_drive_c2_x_probe_v2.py"
EC_PATH = HERE / "_drive_c2_x_earlyclose.py"
WANT_V2 = "6afe2711136c3b52344cd435f6dbd64508378a1e019c552228ff4f5e653d13b9"
WANT_EC = "2e970eec43fe37ff02cab98e71bce9c764d11d758ab2a7b31b495100d109c2e1"

RESULTS = []
NO_CHILDREN = bool(os.environ.get("E12_SUITE_NO_CHILDREN"))


def check(cid, name, ok, ev=""):
    RESULTS.append((cid, name, bool(ok), str(ev)[:200]))
    print("[%s] %-8s %-58s %s" % ("OK" if ok else "RED", cid, name, str(ev)[:110]))
    return bool(ok)


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ★ 纪律同驱动件：先验母版哈希，再 import（不符⇒rc=4 拒载，绝不加载未验件）
_ec_h, _v2_h = sha256(EC_PATH), sha256(V2_PATH)
if _ec_h != WANT_EC or _v2_h != WANT_V2:
    print("!! 母版哈希不符（ec=%s v2=%s）⇒ 自检拒绝 import 加载" % (_ec_h[:16], _v2_h[:16]))
    sys.exit(4)
import _drive_c2_x_probe_v2 as V2      # noqa: E402
import _drive_c2_x_earlyclose as EC    # noqa: E402
import _drive_c2_x_e12 as D            # noqa: E402  （其模块级再次自验母版哈希=双保险）

check("H-00", "母版哈希自验通过方可 import（早窗件/v2 实读对钉）",
      _ec_h == WANT_EC and _v2_h == WANT_V2 and EC.HOLD_AFTER_WINDOW == 6.0,
      "ec=%s… v2=%s… hold=%s watch=%s" % (_ec_h[:12], _v2_h[:12],
                                          EC.HOLD_AFTER_WINDOW, EC.WATCH_S))
FROZEN_BEFORE = {p: sha256(p) for p in (V2_PATH, EC_PATH, DRIVER_PATH)}

# ---------------------------------------------------------------------------
# 沙箱夹具（tempfile；不触碰真实 GAME_SRC/载体树/游戏目录）
_SANDBOX = Path(tempfile.mkdtemp(prefix="e12_st_root_"))
_SRC = _SANDBOX / "src"
_GUARD = _SANDBOX / "guard"
_C2 = _SANDBOX / "c2"
for _d in (_SRC, _GUARD, _C2):
    _d.mkdir(parents=True)
for _i in range(V2.SRC_FILE_COUNT - 2):
    (_SRC / ("f%03d" % _i)).write_bytes(b"Z")
(_SRC / "gamemd.exe").write_bytes(b"Z")
# 夹具 ini：sha16/尺寸走替身 sha16，但 read_bytes 长度须命中 16,496 预检
_head = b"[Logic]\r\nEnableRC4Guard=1\r\n"
(_SRC / "ra2render.ini").write_bytes(_head + b"X" * (D.SRC_INI_SIZE - len(_head) - 2) + b"\r\n")
(_GUARD / "rc4_loader.exe").write_bytes(b"L")
(_C2 / "ra2rc4guard_c2.dll").write_bytes(b"D")
assert (_SRC / "ra2render.ini").stat().st_size == D.SRC_INI_SIZE, "夹具 ini 尺寸须=16,496"

INIT_K, INIT_U = 500000000, 200000000      # CPU 基线（100 ns 单位）
MAIN_WIN = {"hwnd": 0x1234, "title": "Yuri's Revenge", "class": "Yuri's Revenge", "visible": True}
EXCEPT_ORIG, EXCEPT_NEW = "6694b75e46a6e773", "deadbeefdeadbeef"


class StubProc:
    def __init__(self):
        self.pid = 4242

    def wait(self, timeout=5):
        return 0


def make_ops(mode="hang", v2mod=None, **over):
    """虚拟时钟替身 OS。now() 微推进；sleep(s) 推进 s 秒 ⇒ 节律/闩相对时刻可精确断言。
    mode: hang / spin_absent / blocked / natural_exit / dialog / newwin / except_change /
          openfail / cpu_none / cpu_raise / ws_fail / readfail_all / boot_change
    over: residual / post_fail / mkdir_fail / identity_fail / hook6("present"|"absent"|"fail") /
          enum_raise / pt_raise"""
    V = v2mod or V2
    st = {"t": 1000.0, "launched": False, "killed": False, "enum_calls": 0, "pt_calls": 0,
          "sleeps": [], "hook6_state": "absent" if mode == "spin_absent" else "present",
          "ws": 23168, "cpu": [INIT_K, INIT_U], "t_close": None}

    def _latched():
        return st["t_close"] is not None and st["t"] > st["t_close"] + 0.05

    def _axis_fault(name):
        """E2 轴故障注入的作用域闸=仅在闩后（慢采样窗口）生效。
        理由：ws_kb/枚举/CPU 与 hold 期 phase_sentinels 共用同一 OPS seam；若不设界，
        故障会先打崩 hold 期⇒测不到「慢行逐轴显式失败态」这一目标形态（真实世界同构）。"""
        return _latched() and (mode == name or over.get(name) or over.get(name + "_k"))

    def now():
        st["t"] += 0.001
        return st["t"]

    def sleep(s):
        st["sleeps"].append(round(float(s), 4))
        st["t"] += float(s)

    def list_procs():
        d = {os.getpid(): "python.exe"}
        if st["launched"] and not st["killed"]:
            d.update({4242: "gamemd.exe", 4243: "rc4_loader.exe"})
        if over.get("residual"):
            d.update({7777: "gamemd.exe"})
        return d

    def read_mem(h, addr, size):
        if mode == "readfail_all" or over.get("readfail"):
            return None, 299
        if addr == V.BAIL_SITE and size == D.HOOK6_NBYTES:
            hs = over.get("hook6", st["hook6_state"])
            if hs == "fail":
                return None, 299
            return bytes.fromhex(D.HOOK6_ANCHOR if hs == "present" else "c305488b0f00"), 0
        if addr == V.G_EXITSTATE:
            return struct.pack("<I", 1 if _latched() else 0), 0
        if addr == V.G_HWND:
            return struct.pack("<I", 0 if _latched() else 0x1234), 0
        if addr == V.G_SINGLETON:
            return struct.pack("<I", 0 if _latched() else 16641088), 0
        return struct.pack("<I", 1), 0

    def vquery(h, addr):
        if addr == V.BAIL_SITE and over.get("hook6", st["hook6_state"]) == "fail":
            return ((V.MEM_COMMIT if over.get("commit", True) else V.MEM_FREE), addr, 0x1000), 0
        return (V.MEM_COMMIT, addr, 0x1000), 0

    def process_times(h):
        st["pt_calls"] += 1
        if _axis_fault("cpu_none") or over.get("pt_none"):
            return None, 5
        if _axis_fault("cpu_raise") or over.get("pt_raise"):
            raise OSError("GetProcessTimes denied (err=5)")
        spin = mode in ("hang", "spin_absent", "dialog", "newwin", "except_change")
        # 首次调用=闩基线（不步进）；其后每次 +1e7·100ns=1.0 核秒（自旋侧）或 +0（阻塞侧）
        if spin and _latched() and st["pt_calls"] > 1:
            st["cpu"][0] += 10000000
        return {"kernel": st["cpu"][0], "user": st["cpu"][1]}, 0

    def working_set_kb(h):
        if _axis_fault("ws_fail"):
            raise OSError("psapi unavailable")
        st["ws"] += 0 if _latched() else 1024
        return st["ws"]

    def enum_windows(pid):
        st["enum_calls"] += 1
        if _axis_fault("enum_raise"):
            raise OSError("EnumWindows denied")
        wins = [dict(MAIN_WIN)]
        if _latched() and st["t"] > (st["t_close"] + 1.0):
            if mode == "dialog":
                wins.append({"hwnd": 0x9999, "title": "警告", "class": "#32770", "visible": True})
            elif mode == "newwin":
                wins.append({"hwnd": 0x8888, "title": "Other", "class": "SomeClass", "visible": True})
        return wins

    def open_process(access, pid):
        if (mode == "openfail" or over.get("openfail")) and access == D.WATCH_ACCESS:
            return 0
        return 1

    def wait0(h):
        if mode == "waitfail":
            return 0xFFFFFFFF          # WAIT_FAILED
        if mode == "natural_exit" and _latched() and st["t"] > st["t_close"] + 2.5:
            return V.WAIT_OBJECT_0
        return 258

    def get_exit_code(h):
        if mode == "waitfail":
            return False, 0
        return (True, 0) if wait0(h) == V.WAIT_OBJECT_0 else (True, 259)

    def post_close(hwnd):
        if over.get("post_fail"):
            return False, 1400
        st["t_close"] = now()
        return True, 0

    def isfile(p):
        s = str(p)
        if "except.txt" in s:
            return True                       # 夹具：恒在（哈希随模式/时刻变，见 sha16）
        return Path(p).is_file()

    def sha16(p):
        s = str(p)
        if "ra2render.ini" in s:
            return D.SRC_INI_SHA16
        if "except.txt" in s:
            return EXCEPT_NEW if (mode == "except_change" and _latched()) else EXCEPT_ORIG
        if "gamemd.exe" in s:
            return V.GAMEMD_SHA16
        if "rc4_loader.exe" in s:
            return V.LOADER_SHA16
        if "harness7" in s:
            return V.H7_SHA16
        if "_rc4_ab_probe" in s:
            return V.PROBE_SHA16
        return V.real_sha16(p)

    def boot_ms():
        return 5000001 if mode == "boot_change" else 5000000

    def mkdir(d):
        if over.get("mkdir_fail"):
            raise OSError("mkdir denied")
        Path(d).mkdir(parents=True, exist_ok=True)

    return {
        "now": now, "sleep": sleep,
        "popen": lambda argv, cwd, env: (st.__setitem__("launched", True), StubProc())[1],
        "open_process": open_process, "close_handle": lambda h: None,
        "wait0": wait0, "get_exit_code": get_exit_code,
        "terminate": lambda h: st.__setitem__("killed", True),
        "read_mem": read_mem, "vquery": vquery, "post_close": post_close,
        "enum_windows": enum_windows, "window_pid": lambda hwnd: (4242, 99),
        "list_procs": list_procs,
        "query_image": lambda pid: str(V.CURRENT_CARRIER[0] / "gamemd.exe"),
        "under_carrier": lambda img, c: os.path.normcase(str(img)).startswith(
            os.path.normcase(str(c)) + os.sep),
        "find_main_window": lambda pid: 0x1234,
        "copy_file": lambda s, d: shutil.copy2(s, d), "mkdir": mkdir,
        "rmtree": lambda d: shutil.rmtree(d, ignore_errors=True),
        "exists": lambda p: Path(p).exists(), "isfile": isfile,
        "read_bytes": lambda p: Path(p).read_bytes(),
        "carrier_identity_ok": (lambda c: (False, "reparse_point")) if over.get("identity_fail")
        else (lambda c: (True, "ok")),
        "working_set_kb": working_set_kb,
        "capture_screen": lambda p: Path(p).write_bytes(b"PNGSTUB"),
        "sha16": sha16,
        "sha256_file": lambda p: (V.C2_DLL_SHA256 if "rc4guard_c2" in str(p)
                                  else hashlib.sha256(Path(p).read_bytes()).hexdigest()),
        "process_times": process_times, "boot_ms": boot_ms,
        "__st": st,
    }


_MOD_ATTRS = ("MYCARD", "GAME_SRC", "GUARD_DIR", "C2_DIR", "PROBE", "H7")


def _install(ops, v2mod=None):
    V = v2mod or V2
    saved = {"__v": V}
    for a in _MOD_ATTRS:
        saved[a] = getattr(V, a)
    saved["__ops"] = dict(V.OPS)
    saved["__tmp_mycard"] = Path(tempfile.mkdtemp(prefix="e12_st_mycard_"))
    V.MYCARD = saved["__tmp_mycard"]
    V.GAME_SRC, V.GUARD_DIR, V.C2_DIR = _SRC, _GUARD, _C2
    V.PROBE = type("P", (), {"game_procs": staticmethod(lambda: [])})()
    V.H7 = None
    for k in list(V.OPS):
        V.OPS.pop(k, None)
    V.OPS.update({k: v for k, v in ops.items() if k != "__st"})
    saved["__st"] = ops["__st"]
    return saved


def _uninstall(saved):
    V = saved.pop("__v")
    tmp_mycard = saved.pop("__tmp_mycard")
    for a in _MOD_ATTRS:
        setattr(V, a, saved[a])
    for k in list(V.OPS):
        V.OPS.pop(k, None)
    V.OPS.update(saved["__ops"])
    shutil.rmtree(tmp_mycard, ignore_errors=True)


def trip_once(mode, watch_s=10.0, slow_sleep_s=1.0, latch_shot_after_s=2.0,
              except_check_every_s=1.0, trip_index=1, boot_ref=None, drive=D, **over):
    """在替身 OS 下跑单趟。drive=驱动模块（变异件传其替身模块）。
    注：驱动通过 V2.OPS 取 OS，故替身须装进「驱动 import 的那个 V2」——
        主件与变异件各自的 V2 由 drive.V2 给出。"""
    ops = make_ops(mode=mode, v2mod=drive.V2, **over)
    saved = _install(ops, drive.V2)
    try:
        rec = drive.run_trip(trip_index=trip_index, boot_ref=boot_ref, watch_s=watch_s,
                             slow_sleep_s=slow_sleep_s, latch_shot_after_s=latch_shot_after_s,
                             except_check_every_s=except_check_every_s)
        # ★ 趟目录在替身 MYCARD（tempfile）下，_uninstall 即删 ⇒ 必须在卸载前取回 timeline
        try:
            rec["_tl_inmem"] = load_tl(rec)
        except Exception as e:
            rec["_tl_inmem"] = {"__unreadable": repr(e)[:120]}
        return rec, ops
    finally:
        _uninstall(saved)


def load_tl(rec):
    if rec.get("_tl_inmem") is not None:
        return rec["_tl_inmem"]
    return json.loads((Path(rec["out_dir"]) / "timeline.json").read_text(encoding="utf-8"))


def _st(rec, ops):
    return ops["__st"]


# ---------------------------------------------------------------------------
def schema_check(rec, tl):
    bad = []
    need = ("trip_tag", "verdict", "closed_at_s", "close_rows_n", "except_before", "exit_kind",
            "close_delivery", "gamemd_pid", "hold_tl_n", "watch_s", "protocol",
            "latch_detected", "latch_row_index", "latch_after_close_s", "slow_sample_rows",
            "slow_rows_n", "hook6_state", "hook6_state_counts", "cpu_delta_median_s",
            "ws_delta_kb", "e2_fork_label", "e2_summary", "stop_triggered", "boot_ms_at_start",
            "trip_index", "e2_params")
    miss = [k for k in need if k not in rec]
    if miss:
        bad.append("rec_missing=%s" % miss)
    if rec.get("trip_tag") != D.TRIP_TAG_E12:
        bad.append("tag=%s" % rec.get("trip_tag"))
    if rec.get("watch_s") != 10.0:
        bad.append("watch_s=%s" % rec.get("watch_s"))
    if "window+6.0s" not in rec.get("protocol", "") or "E2-slow1Hz" not in rec.get("protocol", ""):
        bad.append("protocol=%s" % rec.get("protocol"))
    if len(tl.get("close_rows") or []) != rec.get("close_rows_n"):
        bad.append("close_rows_n=%s len=%s" % (rec.get("close_rows_n"), len(tl.get("close_rows") or [])))
    keys = {"t", "wait", "code", "code_read_ok", "exitstate", "frame", "hwnd", "singleton", "tick"}
    if tl.get("close_rows") and not all(keys <= set(r.keys()) for r in tl["close_rows"]):
        bad.append("close_row_keys_drift")
    if tl.get("close_rows") and not all(isinstance(r.get("tick"), int) for r in tl["close_rows"]):
        bad.append("tick_not_int⇒判器 C8 抛（早窗行形态未保持）")
    if set(tl.keys()) != {"hold_tl", "close_rows", "_e2"}:
        bad.append("tl_keys=%s" % sorted(tl.keys()))
    e2 = tl.get("_e2") or {}
    if e2.get("params", {}).get("hook6_anchor") != D.HOOK6_ANCHOR:
        bad.append("e2_params_hook6")
    if e2.get("params", {}).get("bail_site_hex") != hex(V2.BAIL_SITE):
        bad.append("e2_params_site=%s" % e2.get("params", {}).get("bail_site_hex"))
    if e2.get("params", {}).get("watch_access_hex") != hex(D.WATCH_ACCESS):
        bad.append("e2_params_access")
    if not all(k in e2 for k in ("latch", "slow_sample_rows", "summary", "stop_triggered")):
        bad.append("e2_keys")
    for r in e2.get("slow_sample_rows") or []:
        if not all(k in r for k in ("cpu", "hook6", "visible_windows", "ws_kb", "pair_close_row_index")):
            bad.append("slow_axis_missing:%s" % sorted(r.keys()))
            break
    if rec.get("slow_rows_n") != len(rec.get("slow_sample_rows") or []):
        bad.append("rec slow_rows_n≠len(slow_sample_rows)")
    if len(e2.get("slow_sample_rows") or []) != rec.get("slow_rows_n"):
        bad.append("_e2 slow 行数≠rec slow_rows_n")
    _srows = e2.get("slow_sample_rows") or []
    if [x["t"] for x in _srows] != sorted(set(x["t"] for x in _srows)):
        bad.append("slow t 非严格单调")
    if any(not (0 <= x["pair_close_row_index"] < len(tl.get("close_rows") or [])) for x in _srows):
        bad.append("pair_close_row_index 越界")
    if _srows and tl["_e2"]["latch"] and tl["_e2"]["latch"]["row_index"] >= _srows[0]["pair_close_row_index"]:
        bad.append("首慢行未晚于闩行（闩行不应产慢行）")
    if tl.get("hold_tl") and "hook6" not in tl["hold_tl"][0]:
        bad.append("hold_tl_no_hook6")
    return bad


def _raises(fn, exc=RuntimeError):
    try:
        fn()
        return False
    except exc:
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
def main_suite() -> int:
    print("== E12 候选驱动件离线自检（零真机·零发射·零游戏启动）==")
    print("驱动件 sha256=%s" % sha256(DRIVER_PATH))

    # ---------- A 组 组件分臂 ----------
    r, ops = trip_once("hang")
    tl, st = load_tl(r), _st(r, ops)
    check("A-01", "闩检测切换（exitstate==1⇒latch_detected+行号+相对关窗时刻）",
          r["verdict"] == "OK" and r["latch_detected"] is True and r["latch_row_index"] == 1
          and isinstance(r["latch_after_close_s"], float),
          "idx=%s after=%s rows=%s" % (r["latch_row_index"], r["latch_after_close_s"], r["close_rows_n"]))
    _sr = tl["_e2"]["slow_sample_rows"]
    _dt = [round(_sr[i + 1]["t"] - _sr[i]["t"], 3) for i in range(len(_sr) - 1)]
    check("A-02", "慢采样节律=1 Hz（慢行 t 差分≈1.000；闩前 0.1 s 主循环节律在录）",
          bool(_dt) and all(abs(x - 1.0) < 0.01 for x in _dt) and st["sleeps"].count(0.1) >= 1
          and all(x["pair_close_row_index"] > tl["_e2"]["latch"]["row_index"] for x in _sr),
          "dt=%s… fast0.1=%s" % (_dt[:3], st["sleeps"].count(0.1)))
    check("A-03", "闩后慢行≈观察秒数（1 Hz）且明显少于总行数",
          3 <= r["slow_rows_n"] <= r["close_rows_n"] - 2,
          "slow=%s close=%s" % (r["slow_rows_n"], r["close_rows_n"]))
    check("A-04", "hook6 与锚比对：现读==e91a1f941790⇒present_stable（闩时刻亦录）",
          r["hook6_state"] == "present_stable"
          and tl["_e2"]["latch"]["hook6_at_latch"]["hex"] == D.HOOK6_ANCHOR
          and tl["hold_tl"][0]["hook6"] == D.HOOK6_ANCHOR, r["hook6_state"])
    check("A-05", "CPU 增量计算：自旋侧每慢秒=+10^7·100ns=1.0 s；基线=闩时刻读数",
          tl["_e2"]["slow_sample_rows"]
          and all(abs(x["cpu"]["delta_s"] - 1.0) < 1e-9 for x in tl["_e2"]["slow_sample_rows"])
          and tl["_e2"]["latch"]["cpu_baseline"] == {"kernel": INIT_K, "user": INIT_U},
          "med=%s" % r["cpu_delta_median_s"])
    check("A-06", "分叉标签=P1 第一候选（CPU≈1 核×hook6 在位，§9 A4）",
          "P1_first_candidate" in r["e2_fork_label"], r["e2_fork_label"])
    check("A-07", "闩+30 s 加一张截图（tag=latch_plus_30 在录；自检节拍=闩+2 s 模拟）",
          any(s["tag"] == "latch_plus_30" for s in r.get("shots", [])),
          "%s" % [s["tag"] for s in r.get("shots", [])])
    check("A-08", "finalize 全套仍跑（a8 清扫 PASS+载体删+双时点证据）",
          r.get("a8_verdict") == "PASS" and r.get("carrier_deleted") is True
          and "after_kill" in r.get("except_at", {}),
          "a8=%s del=%s" % (r.get("a8_verdict"), r.get("carrier_deleted")))
    bad = schema_check(r, tl)
    check("A-09", "输出 schema（_rec E2 段齐全/timeline 三段/close_rows 原形态兼容）",
          not bad, bad)
    check("A-10", "窗口枚举通道逐秒独立在跑（补 A 线 R1 挂死期窗面盲区）",
          st["enum_calls"] >= r["slow_rows_n"], "enum=%s slow=%s" % (st["enum_calls"], r["slow_rows_n"]))
    check("A-11", "hold 期沿用早窗件 phase_sentinels（hook6/ws/可见窗随早窗纪律入 hold_tl）",
          5 <= r["hold_tl_n"] <= 7 and "ws_kb" in tl["hold_tl"][0]
          and tl["hold_tl"][0]["visible_windows"], "hold_n=%s" % r["hold_tl_n"])

    r2, ops2 = trip_once("spin_absent")
    check("A-12", "spin×hook6 不在位 ⇒ 丁第一候选（§9 A4 分叉二）",
          r2["hook6_state"] == "absent_persistently" and "丁_first_candidate" in r2["e2_fork_label"],
          "%s / %s" % (r2["hook6_state"], r2["e2_fork_label"]))
    bad = schema_check(r2, load_tl(r2))
    check("A-13", "spin_absent 趟 schema 同形", not bad, bad)

    # ---------- B 组 三态 / 故障注入 ----------
    r3, _ = trip_once("blocked")
    check("B-01", "CPU≈0 ⇒ 阻塞族标签（甲/乙-1尾/CRT/丙-阻塞 ⇒ E3 另裁；不冒充自旋）",
          r3["cpu_delta_median_s"] == 0.0 and "blocked_family" in r3["e2_fork_label"],
          "med=%s %s" % (r3["cpu_delta_median_s"], r3["e2_fork_label"]))

    rf, _ = trip_once("readfail_all")
    tlf = load_tl(rf)
    check("B-02", "哨兵全读败 ⇒ 三态 read_fail 显式落行、不误判闩",
          rf["verdict"] == "OK" and rf["latch_detected"] is False
          and all(isinstance(x["exitstate"], dict) and x["exitstate"]["state"] == "read_fail"
                  for x in tlf["close_rows"]), "%s" % rf["e2_fork_label"])
    check("B-03", "hook6 随 hold 期 phase_sentinels 亦显式 read_fail（不吞）",
          tlf["hold_tl"][0]["hook6"] == {"state": "read_fail"} and rf["slow_rows_n"] == 0,
          "%s" % tlf["hold_tl"][0]["hook6"])

    rh, _ = trip_once("hang", hook6="fail")
    tlh = load_tl(rh)
    check("B-04", "hook6 轴单独读败 ⇒ all_read_fail+detail(rpm/vquery)，CPU 轴不受染",
          rh["hook6_state"] == "all_read_fail"
          and all(x["hook6"]["state"] == "read_fail" and "rpm_err" in x["hook6"]["detail"]
                  for x in tlh["_e2"]["slow_sample_rows"])
          and tlh["_e2"]["summary"]["cpu_ok_deltas_n"] >= 3,
          "cpu_ok=%s" % tlh["_e2"]["summary"]["cpu_ok_deltas_n"])
    check("B-05", "hook6 三态未决时分叉=undetermined（读败绝不冒充 P1/丁）",
          "undetermined" in rh["e2_fork_label"], rh["e2_fork_label"])

    rc1, _ = trip_once("cpu_none")
    check("B-06", "GetProcessTimes 返回 None（句柄权不足形）⇒ read_fail 显式+cpu_axis_unreadable",
          rc1["e2_summary"]["cpu_ok_deltas_n"] == 0 and rc1["cpu_delta_median_s"] is None
          and rc1["e2_fork_label"] == "cpu_axis_unreadable"
          and rc1["hook6_state"] == "present_stable",
          "%s / %s" % (rc1["e2_fork_label"], rc1["hook6_state"]))
    rc2, _ = trip_once("cpu_raise")
    tlc2 = load_tl(rc2)
    check("B-07", "GetProcessTimes 抛异常 ⇒ api_exception 留痕且趟不崩（异常不吞）",
          rc2["verdict"] == "OK"
          and all(x["cpu"]["state"] == "api_exception" for x in tlc2["_e2"]["slow_sample_rows"]),
          "%d 行" % len(tlc2["_e2"]["slow_sample_rows"]))
    rcn, _ = trip_once("hang", pt_raise=True)
    check("B-08", "CPU 基线读取即败 ⇒ latch.cpu_baseline_state=read_fail（不虚构基线）",
          load_tl(rcn)["_e2"]["latch"]["cpu_baseline_state"] == "read_fail"
          and rcn["e2_fork_label"] == "cpu_axis_unreadable", "baseline fail")
    rw, _ = trip_once("hang", ws_fail=True)
    tlw = load_tl(rw)
    check("B-09", "ws_kb 轴读败 ⇒ 显式 read_fail；hook6/CPU 轴不受染、分叉仍 P1 候选",
          all(isinstance(x["ws_kb"], dict) and x["ws_kb"]["state"] == "read_fail"
              for x in tlw["_e2"]["slow_sample_rows"])
          and rw["hook6_state"] == "present_stable" and "P1_first_candidate" in rw["e2_fork_label"],
          "ws_delta=%s" % rw["ws_delta_kb"])
    re1, _ = trip_once("hang", enum_raise=True)
    tle = load_tl(re1)
    check("B-10", "枚举轴异常 ⇒ read_fail 留痕；其余轴照常；不冒充「无新窗」",
          all(x["visible_windows"]["state"] == "read_fail" for x in tle["_e2"]["slow_sample_rows"])
          and re1["hook6_state"] == "present_stable", "enum 故障面")

    ro, _ = trip_once("openfail")
    check("B-11", "watch 句柄 OpenProcess=0（权限缺失形）⇒ OpenProcess_watch 硬停",
          ro["verdict"] == "FAIL" and "OpenProcess_watch" in ro["fail"], ro["fail"][:40])
    rr, _ = trip_once("hang", residual=True)
    check("B-12", "预检残留进程 ⇒ 停（precheck_residual_procs）",
          rr["verdict"] == "FAIL" and "residual" in rr["fail"], rr["fail"][:40])
    rpv, _ = trip_once("hang", post_fail=True)
    check("B-13", "WM_CLOSE 投递失败 ⇒ FAIL 且 finalize 清扫仍跑（G-5/G-9 纪律）",
          rpv["verdict"] == "FAIL" and "PostMessageW" in rpv["fail"]
          and rpv.get("carrier_deleted") is True, "%s / a8=%s" % (rpv["fail"][:26], rpv.get("a8_verdict")))
    rmd, _ = trip_once("hang", mkdir_fail=True)
    check("B-14", "载体创建失败 ⇒ FAIL@mkdir（无泄漏、不删他树）",
          rmd["verdict"] == "FAIL" and rmd["phase"] == "mkdir", "phase=%s" % rmd["phase"])
    ridt, _ = trip_once("hang", identity_fail=True)
    check("B-15", "载体身份不符 ⇒ 前置拦 carrier_identity",
          ridt["verdict"] == "FAIL" and "carrier_identity" in ridt["fail"], ridt["fail"][:40])
    rnat, _ = trip_once("natural_exit")
    check("B-16", "兑现趟（自然退）⇒ 短慢行、exit_kind=natural、final code=int",
          rnat["verdict"] == "OK" and rnat["exited"] is True and rnat["exit_kind"] == "natural"
          and isinstance(rnat["final_exitcode"], int) and 0 <= rnat["slow_rows_n"] <= 3,
          "exit_after=%s slow=%s" % (rnat["exit_after_close_s"], rnat["slow_rows_n"]))
    rzero, _ = trip_once("hang", watch_s=-1.0)
    check("B-17", "零 close 样本 ⇒ FAIL（承 v2 G-9）",
          rzero["verdict"] == "FAIL" and "zero_close_samples" in rzero["fail"], rzero["fail"][:40])
    rbref, _ = trip_once("hang", boot_ref={"boot_ms": 111111})
    check("B-18", "跨趟 BOOT 读数变化 ⇒ 停（stop_condition:boot_changed_between_trips）",
          rbref["verdict"] == "FAIL" and "boot_changed" in rbref["fail"], rbref["fail"][:40])
    rbc, _ = trip_once("boot_change", boot_ref={"boot_ms": 5000000})
    check("B-19", "boot_change 形态同样被拦（读数≠参考即停，无方向假设）",
          rbc["verdict"] == "FAIL" and "boot_changed" in rbc["fail"], rbc["fail"][:40])
    rwf, _ = trip_once("waitfail")
    check("B-20", "Wait 三态补全：WAIT_FAILED ⇒ exit_kind=wait_error（不冒充「仍活/挂死」）",
          rwf["verdict"] == "OK" and str(rwf["exit_kind"]).startswith("wait_error:")
          and rwf["exited"] is False, "exit_kind=%s" % rwf["exit_kind"])

    # ---------- C 组 通用停止条件 ----------
    rd, _ = trip_once("dialog")
    tld = load_tl(rd)
    check("C-01", "#32770 新窗 ⇒ stop_triggered=interaction_window（命中证据入 stop.evidence）",
          rd["stop_triggered"]["reason"] == "interaction_window"
          and rd["stop_triggered"]["evidence"]["hits"],
          "%s" % rd["stop_triggered"]["evidence"]["new_windows"])
    check("C-02", "停止=只留证据不升级（stop_evidence 截图+exit_kind 标注+verdict 不 FAIL）",
          any(s["tag"] == "stop_evidence" for s in rd.get("shots", []))
          and rd["exit_kind"].startswith("stopped_by_condition") and rd["verdict"] == "OK",
          "exit_kind=%s" % rd["exit_kind"])
    check("C-03", "停止即退出慢采样（命中行完整落记录后停）",
          len(tld["_e2"]["slow_sample_rows"]) == rd["stop_triggered"]["slow_index"] + 1,
          "slow=%s idx=%s" % (rd["slow_rows_n"], rd["stop_triggered"]["slow_index"]))
    rnew, _ = trip_once("newwin")
    check("C-04", "非交互关键字新可见窗 ⇒ 保守停 new_visible_window（E2「新窗即停」）",
          rnew["stop_triggered"]["reason"] == "new_visible_window"
          and not rnew["stop_triggered"]["evidence"]["hits"], rnew["stop_triggered"]["reason"])
    rex, _ = trip_once("except_change", except_check_every_s=0.5)
    check("C-05", "except.txt 哈希中途变化 ⇒ stop=except_changed（before/now 俱在录）",
          rex["stop_triggered"]["reason"] == "except_changed"
          and rex["stop_triggered"]["evidence"]["before"] == EXCEPT_ORIG
          and rex["stop_triggered"]["evidence"]["now"] == EXCEPT_NEW,
          json.dumps(rex["stop_triggered"]["evidence"], ensure_ascii=False)[:70])
    check("C-06", "停止趟 finalize 仍跑（证据双时点+清扫+载体删）",
          rex.get("carrier_deleted") is True and "after_kill" in rex.get("except_at", {})
          and rex["a8_verdict"] == "PASS", "%s" % rex.get("except_at"))
    for kw in ("#32770", "确认", "保存", "confirm", "save", "网络"):
        nw, hits = D.interaction_hits([{"hwnd": 9, "title": kw, "class": "D"}], [{"hwnd": 0x1234}])
        check("C-07:%s" % kw, "交互关键字命中「%s」（纯函数）" % kw, bool(hits), "%d new" % len(nw))
    nw0, hits0 = D.interaction_hits(
        [{"hwnd": 5, "title": "Yuri's Revenge", "class": "Yuri's Revenge"}],
        [{"hwnd": 0x1234, "title": "Yuri's Revenge", "class": "Yuri's Revenge"}])
    check("C-08", "同名新句柄 ⇒ 记新窗但不定性交互（关键字零命中）",
          len(nw0) == 1 and not hits0, "new=%d hits=%d" % (len(nw0), len(hits0)))

    # ---------- D 组分叉标签机（纯函数臂） ----------
    def srow(d=None, hk="present", ws=None, cpu_state="ok"):
        return {"cpu": ({"state": "ok", "delta_s": d} if cpu_state == "ok"
                        else {"state": cpu_state, "delta_s": None}),
                "hook6": {"state": hk}, "ws_kb": ws}
    f1 = D.summarize_e2(True, [srow(0.99, "present", 60000), srow(1.0, "present", 60100)])
    check("D-01", "标签机：spin×在位 ⇒ P1 第一候选", "P1_first_candidate" in f1["e2_fork_label"], f1["e2_fork_label"])
    f2 = D.summarize_e2(True, [srow(1.0, "absent", 60000), srow(0.98, "absent", 60000)])
    check("D-02", "标签机：spin×不在位 ⇒ 丁第一候选", "丁_first_candidate" in f2["e2_fork_label"], f2["e2_fork_label"])
    f3 = D.summarize_e2(True, [srow(0.0, "present"), srow(0.0, "present")])
    check("D-03", "标签机：CPU≈0 ⇒ blocked_family（E3 另裁侧）", "blocked_family" in f3["e2_fork_label"], f3["e2_fork_label"])
    f4 = D.summarize_e2(True, [srow(0.5, "present"), srow(0.5, "present")])
    check("D-04", "标签机：中间带 ⇒ cpu_ambiguous（带外不硬判）", f4["e2_fork_label"] == "cpu_ambiguous", f4["e2_fork_label"])
    f5 = D.summarize_e2(True, [{"cpu": {"state": "ok", "delta_s": None}, "hook6": {"state": "present"}, "ws_kb": 1},
                               {"cpu": {"state": "read_fail"}, "hook6": {"state": "present"}, "ws_kb": 1}])
    check("D-05", "标签机：CPU 不可读 ⇒ cpu_axis_unreadable（不冒充阻塞）",
          f5["e2_fork_label"] == "cpu_axis_unreadable", f5["e2_fork_label"])
    f6 = D.summarize_e2(True, [srow(1.0, "read_fail"), srow(1.0, "read_fail")])
    check("D-06", "标签机：hook6 全读败 ⇒ undetermined（不冒充 P1/丁）", "undetermined" in f6["e2_fork_label"], f6["e2_fork_label"])
    f7 = D.summarize_e2(True, [srow(1.0, "present"), srow(1.0, "absent")])
    check("D-07", "标签机：present/absent 混合 ⇒ mixed_lost_at_some_row+undetermined",
          f7["hook6_state"] == "mixed_lost_at_some_row" and "undetermined" in f7["e2_fork_label"],
          f7["hook6_state"])
    f8 = D.summarize_e2(True, [srow(1.0, "present", 60000), srow(1.0, "present", 70000)])
    check("D-08", "ws_kb 闩后净增>1 MB ⇒ 加载未完侧注记（动摇「宿主已进入」）",
          f8["ws_delta_kb"] == 10000 and "note_ws_growing" in f8, "ws_delta=%s" % f8["ws_delta_kb"])
    f9 = D.summarize_e2(True, [])
    check("D-09", "闩后零慢行 ⇒ latched_but_no_slow_rows（不虚构分叉）",
          str(f9["e2_fork_label"]).startswith("latched_but_no_slow_rows"), f9["e2_fork_label"])
    f10 = D.summarize_e2(False, [])
    check("D-10", "未闩趟 ⇒ not_triggered_no_latch 且轴全 None（不虚构）",
          f10["e2_fork_label"] == "not_triggered_no_latch" and f10["cpu_delta_median_s"] is None
          and f10["hook6_state"] == "not_triggered", f10["e2_fork_label"])
    check("D-11", "阈值常量与 §9 A4 语义一致（spin≥0.7 > block≤0.2，中间带存在）",
          (D.SPIN_MIN_DELTA, D.BLOCK_MAX_DELTA) == (0.7, 0.2), "%s/%s" % (D.SPIN_MIN_DELTA, D.BLOCK_MAX_DELTA))
    drv_src = DRIVER_PATH.read_text(encoding="utf-8")
    check("D-12", "禁比率表述纪律：件内零「成功率/兑现率/百分比/概率」文案",
          not any(s in drv_src for s in ("成功率", "兑现率", "百分比", "概率")), "词面扫描")

    # ---------- E 组 硬闸 ----------
    check("E-01", "gate_decision 四组合（离线 0/0；live 无授权 3；live+approved 开闸）",
          D.gate_decision(False, False) == 0 and D.gate_decision(False, True) == 0
          and D.gate_decision(True, False) == 3 and D.gate_decision(True, True) == -1,
          "%s" % [D.gate_decision(l, a) for l in (0, 1) for a in (0, 1)])
    check("E-02", "母版哈希自验：钉值不符⇒RuntimeError（先验哈希后才谈 import）",
          _raises(lambda: D.verify_frozen_masters({"_drive_c2_x_probe_v2.py": "0" * 64})), "拒不符")
    check("E-03", "母版哈希自验：文件不可读⇒RuntimeError（不静默放行）",
          _raises(lambda: D.verify_frozen_masters({"_no_such_master.py": "1" * 64})), "拒不可读")
    if NO_CHILDREN:
        check("E-04", "子进程实测组（父进程已完成，本进程=子进程跳过防递归）", True, "env-guard")
    else:
        py = sys.executable
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        r1 = subprocess.run([py, str(DRIVER_PATH)], capture_output=True, env=env, timeout=300)
        r2 = subprocess.run([py, str(DRIVER_PATH), "--approved"], capture_output=True, env=env, timeout=300)
        r3 = subprocess.run([py, str(DRIVER_PATH), "--live"], capture_output=True, env=env, timeout=300)
        r4 = subprocess.run([py, str(DRIVER_PATH), "--live", "--selftest"],
                            capture_output=True, env=dict(env, E12_SUITE_NO_CHILDREN="1"), timeout=900)
        o1 = r1.stdout.decode("utf-8", "replace")
        o2 = r2.stdout.decode("utf-8", "replace")
        o3 = r3.stdout.decode("utf-8", "replace")
        check("E-04", "实测 无参离线 rc=0（不发射、零 ops 绑定）",
              r1.returncode == 0 and "gamemd" not in o1, "rc=%d" % r1.returncode)
        check("E-05", "实测 --approved 单给 rc=0 且明示「透传不自动跑」",
              r2.returncode == 0 and "透传" in o2, "rc=%d" % r2.returncode)
        check("E-06", "实测 --live 无授权 rc=3 恒拒",
              r3.returncode == 3 and "需 --approved" in o3, "rc=%d" % r3.returncode)
        check("E-07", "实测 --live --selftest：自检分支优先于 live 闸（rc=0）且零发射",
              r4.returncode == 0 and "E12 SELFTEST" in r4.stdout.decode("utf-8", "replace"),
              "rc=%d" % r4.returncode)

    # ---------- F 组 变异 ----------
    for name, caught, ev in _run_mutations():
        check("F:%s" % name, "变异被抓出：%s" % name, caught, ev)

    # ---------- G 组 冻结件零写入 ----------
    for p, h in FROZEN_BEFORE.items():
        check("G:%s" % p.name, "本套件运行前后哈希不变：%s" % p.name, sha256(p) == h, sha256(p)[:16])

    bad = [c for c, _, ok, _ in RESULTS if not ok]
    print("\n== E12 SELFTEST: %d 项，红=%d ⇒ %s ==" % (
        len(RESULTS), len(bad), "ALL-PASS" if not bad else "FAIL " + ",".join(bad)))
    print("件 sha256: e12=%s" % sha256(DRIVER_PATH))
    print("           earlyclose=%s" % sha256(EC_PATH))
    print("           v2=%s" % sha256(V2_PATH))
    return 0 if not bad else 1


# ---------------------------------------------------------------------------
# F 组：变异注入——驱动件源码关键行改动⇒独立模块加载⇒同一替身跑趟⇒断言「预期必红」
def _run_mutations():
    out = []
    src = DRIVER_PATH.read_text(encoding="utf-8")

    def build(tag, old, new):
        d = Path(tempfile.mkdtemp(prefix="e12_mut_%s_" % tag))
        for nm in (V2_PATH.name, EC_PATH.name):
            shutil.copy2(HERE / nm, d / nm)      # 母版哈希自验在 tmp 目录需可读（副本字节同）
        if old not in src:
            return d, None                        # 锚点未命中=源码漂移，变异无效（记红）
        p = d / "_drive_c2_x_e12.py"
        p.write_text(src.replace(old, new, 1), encoding="utf-8", newline="\n")
        return d, p

    def load(d, tag):
        for nm in ("_drive_c2_x_probe_v2", "_drive_c2_x_earlyclose"):
            sys.modules.pop(nm, None)             # 变异件从 tmp 副本 import ⇒ 用副本自己的 OPS
        sys.path.insert(0, str(d))
        try:
            spec = importlib.util.spec_from_file_location("e12_mut_%s" % tag, d / "_drive_c2_x_e12.py")
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
        finally:
            sys.path.remove(str(d))
        for nm in ("_drive_c2_x_probe_v2", "_drive_c2_x_earlyclose"):
            sys.modules.pop(nm, None)
        import _drive_c2_x_probe_v2 as _v
        import _drive_c2_x_earlyclose as _e
        sys.modules["_drive_c2_x_probe_v2"], sys.modules["_drive_c2_x_earlyclose"] = _v, _e
        return m

    # (tag, old, new, mode, over, assertion(rr, tlj), why)
    cases = [
        ("latch_const", "LATCH_VALUE = 1", "LATCH_VALUE = 7", "hang", {},
         lambda rr, tlj: rr["latch_detected"] is False, "闩常量改⇒闩永不可见"),
        ("rhythm", 'V2.OPS["sleep"](slow_sleep_s if latch is not None else FAST_SLEEP)',
         'V2.OPS["sleep"](FAST_SLEEP)', "hang", {},
         lambda rr, tlj: rr["slow_rows_n"] > 30 or (
             len(tlj["_e2"]["slow_sample_rows"]) > 1 and
             abs(tlj["_e2"]["slow_sample_rows"][1]["t"] -
                 tlj["_e2"]["slow_sample_rows"][0]["t"] - 1.0) > 0.01),
         "节律旁路⇒慢采样退化 10 Hz（行数暴增/t 差分失真）"),
        ("sentinel_readfail_swallowed", 'row[nm2] = val if kind == "ok" else {"state": kind}',
         'row[nm2] = val if kind == "ok" else 0', "readfail_all", {},
         lambda rr, tlj: all(isinstance(x["exitstate"], int) for x in tlj["close_rows"]),
         "读败吞成假值 0⇒三态失真"),
        ("hook6_swallow", 'return {"state": "read_fail", "detail": detail}',
         'return {"state": "absent", "hex": "swallowed"}', "hang", {"hook6": "fail"},
         lambda rr, tlj: rr["hook6_state"] != "all_read_fail", "hook6 读败吞成不在位⇒丁误判"),
        ("cpu_divisor", "CPU_TICK_DIVISOR = 1e7", "CPU_TICK_DIVISOR = 1e5", "hang", {},
         lambda rr, tlj: abs((rr["cpu_delta_median_s"] or 0) - 1.0) > 1e-9,
         "CPU 单位改 100 倍⇒分叉阈值全失真"),
        ("slow_append_removed", "slow.append(srow)", "pass", "hang", {},
         lambda rr, tlj: rr["slow_rows_n"] == 0, "慢行旁路⇒闩后零证据"),
        ("stop_bypass", "if stop:\n                    break", "if False:\n                    break",
         "dialog", {}, lambda rr, tlj: rr["slow_rows_n"] > 1, "停止旁路⇒新窗后仍续采"),
        ("no_finalize", "V2.finalize(rec, carrier, out_dir, proc)", "pass", "hang", {},
         lambda rr, tlj: "a8_verdict" not in rr, "清扫被跳⇒残留检查缺失"),
        ("boot_assert", 'if boot_ref is not None and rec["boot_ms_at_start"] != boot_ref.get("boot_ms"):',
         'if boot_ref is None and rec["boot_ms_at_start"] != boot_ref.get("boot_ms"):', "hang",
         {"__boot_ref": {"boot_ms": 111111}},
         lambda rr, tlj: rr.get("verdict") == "OK" and "boot_changed" not in str(rr.get("fail", "")),
         "BOOT 断言旁路⇒跨会话不停（合法语法变异，语义级）"),
        ("live_gate", "    if not approved:\n        return 3",
         "    if not approved:\n        return -1", None, {}, None, "live 闸篡改⇒未授权即开闸"),
        ("schema_e2_dropped", 'rec["e2_summary"] = e2_summary', "pass", "hang", {},
         lambda rr, tlj: "e2_summary" not in rr, "E2 段被删⇒schema 断言必红"),
        ("kw_dropped",
         'INTERACTION_KEYS = ("#32770", "＃32770", "32770", "确认", "保存", "confirm", "save", "network", "网络")',
         "INTERACTION_KEYS = ()", "dialog", {},
         lambda rr, tlj: (rr["stop_triggered"] or {}).get("reason") != "interaction_window",
         "交互关键字清空⇒#32770 不再定性交互"),
        ("latch30_shot", "if (not latch30_shot_done", "if (False and not latch30_shot_done", "hang", {},
         lambda rr, tlj: not any(s["tag"] == "latch_plus_30" for s in rr.get("shots", [])),
         "闩+30 截图旁路⇒证据缺失"),
    ]
    for tag, old, new, mode, over, assertion, why in cases:
        d, p = build(tag, old, new)
        if p is None:
            out.append((tag, False, "%s ⇒ 变异锚点未命中（源码漂移）" % why))
            shutil.rmtree(d, ignore_errors=True)
            continue
        caught, ev = False, ""
        try:
            m = load(d, tag)
            if tag == "live_gate":
                caught = (m.gate_decision(True, False) == -1)
                ev = "闸被开=%s" % caught
            else:
                boot_ref = over.pop("__boot_ref", None)
                rr, opsx = trip_once(mode, watch_s=10.0, latch_shot_after_s=2.0,
                                     except_check_every_s=0.5, boot_ref=boot_ref,
                                     drive=m, **over)
                tlj = load_tl(rr) if isinstance(rr.get("_tl_inmem"), dict) else {}
                if "_tl_inmem" in rr:
                    rr.pop("_tl_inmem", None)
                caught = bool(assertion(rr, tlj))
                ev = "latch=%s slow=%s fork=%s stop=%s" % (
                    rr.get("latch_detected"), rr.get("slow_rows_n"),
                    str(rr.get("e2_fork_label"))[:24], (rr.get("stop_triggered") or {}).get("reason"))
        except Exception as e:
            caught = True
            ev = "变异致件不可用/异常⇒视为必红：%s" % repr(e)[:60]
        finally:
            shutil.rmtree(d, ignore_errors=True)
        out.append((tag, caught, "%s ⇒ %s" % (why, ev)))
    return out


run_suite = main_suite

if __name__ == "__main__":
    try:
        sys.exit(main_suite())
    finally:
        shutil.rmtree(_SANDBOX, ignore_errors=True)
