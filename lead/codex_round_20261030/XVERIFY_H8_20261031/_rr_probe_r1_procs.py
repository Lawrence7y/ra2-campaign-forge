# -*- coding: utf-8 -*-
"""RR-P1（R-1 复验）：用 importlib 加载**原件**发射器（母本 / v2 副本），实测
   sizeof(PE32) / 字段面 / list_procs() / game_procs()；并对 kill_under 做
   **只读桩**选择面测试（桩替 k32，绝不真终止任何进程、绝不启动游戏）。

v1 退役副本（sha16 abb8b0ec4619e665）从 git index 取源，仅做**静态字段面 + sizeof
离线复算**（不 exec 外部源，避免注入面争议）。
"""
import ctypes
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
HERE = Path(__file__).resolve().parent
COPY = ROOT / "lead/goal1_harness8_20261031/_launch_h8_20261031.py"
MASTER = ROOT / "lead/qc161_u0400_trip/_launch_l1_20261023.py"
V1_PATH_IN_GIT = "lead/goal1_harness8_20261031/_launch_h8_20261031.py"


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def load(path, name):
    sp = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(sp)
    sys.modules[name] = m
    sp.loader.exec_module(m)
    return m


def probe_enum(tag, m):
    names = [f[0] for f in m.PE32._fields_]
    procs = m.list_procs()
    return {"tag": tag,
            "sha16": sha16({"rr_copy": COPY, "rr_master": MASTER}[tag]),
            "sizeof": ctypes.sizeof(m.PE32),
            "n_fields": len(names),
            "has_parent_field": "th32ParentProcessID" in names,
            "fields": names,
            "list_procs_count": len(procs),
            "game_procs": m.game_procs(),
            "last_error_after_enum": ctypes.get_last_error(),
            "own_pid_present": str(__import__("os").getpid()) in
                               [str(k) for k in procs.keys()],
            }


def main():
    res = {}
    mc = load(COPY, "rr_copy")
    mm = load(MASTER, "rr_master")
    res["COPY_v2"] = probe_enum("rr_copy", mc)
    res["MASTER"] = probe_enum("rr_master", mm)
    res["reps"] = {"copy": [len(mc.list_procs()) for _ in range(3)],
                   "master": [len(mm.list_procs()) for _ in range(3)]}

    # ---- v1 静态复算：从 git index 取源，只解析 PE32._fields_ 列表，AST 求字面量 ----
    import ast
    v1_src = subprocess.run(["git", "-C", str(ROOT), "show", ":" + V1_PATH_IN_GIT],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace").stdout
    res["v1_in_git_index"] = bool(v1_src.strip())
    res["v1_sha16"] = hashlib.sha256(v1_src.encode("utf-8")).hexdigest()[:16] if v1_src.strip() else None
    if v1_src.strip():
        tree = ast.parse(v1_src)
        fields = None
        for n in ast.walk(tree):
            if isinstance(n, ast.ClassDef) and n.name == "PE32":
                for st in n.body:
                    if isinstance(st, ast.Assign) and getattr(st.targets[0], "id", "") == "_fields_":
                        fields = [ast.literal_eval(e.elts[0]) for e in st.value.elts]
        res["v1_fields"] = fields
        res["v1_has_parent_field"] = fields is not None and "th32ParentProcessID" in fields

        # sizeof 离线复算：用与原件同类型构造一个临时 Structure（不涉及任何外部代码）
        import ctypes as C
        from ctypes import wintypes as W
        typemap = {"DWORD": W.DWORD, "POINTER(c_ulong)": C.POINTER(C.c_ulong),
                   "c_long": C.c_long, "WCHAR*260": W.WCHAR * 260}
        fname = "RR_PE32_V1"
        ns_tmp = {}
        # 直接按母本字段去掉 parent 一行构造，验证 560
        keep = [f for f in fields]
        # 用真实类型（按字段名推断）
        def ctype_for(nm):
            if nm in ("dwSize", "cntUsage", "th32ProcessID", "th32ModuleID",
                      "cntThreads", "th32ParentProcessID", "dwFlags"):
                return W.DWORD
            if nm == "th32DefaultHeapID":
                return C.POINTER(C.c_ulong)
            if nm == "pcPriClassBase":
                return C.c_long
            if nm == "szExeFile":
                return W.WCHAR * 260
            raise KeyError(nm)
        dyn = type(fname, (C.Structure,), {"_fields_": [(f, ctype_for(f)) for f in keep]})
        res["v1_sizeof_recomputed"] = C.sizeof(dyn)
        dyn2 = type("RR_PE32_MASTER", (C.Structure,),
                    {"_fields_": [(f, ctype_for(f)) for f in mm.PE32._fields_ and
                                  [x[0] for x in mm.PE32._fields_]]})
        res["master_sizeof_recomputed"] = C.sizeof(dyn2)

    # ---- kill_under 选择面（只读桩，零真终止） ----
    calls = {"open": [], "terminate": []}
    carrier = HERE / "rr_fake_ct_c_000000000000_12345"

    _SYNTH_GAMES = {7771, 7772}   # 只有这两个「图像路径」落在载体目录下

    class _StubFn:
        """可赋 argtypes/restype 的桩函数（kill_under 开头会写这些属性）。"""
        def __init__(self, impl):
            self._impl = impl
            self.argtypes = None
            self.restype = None

        def __call__(self, *a, **k):
            return self._impl(*a, **k)

    class FakeK32:
        def __init__(self, real):
            self._real = real
            self._fns = {
                "OpenProcess": _StubFn(self._OpenProcess),
                "QueryFullProcessImageNameW": _StubFn(self._Query),
                "TerminateProcess": _StubFn(self._Term),
                "WaitForSingleObject": _StubFn(lambda hp, ms: 0),
                "CloseHandle": _StubFn(lambda hp: 1),
            }

        def __getattr__(self, item):
            fns = self.__dict__.get("_fns", {})
            if item in fns:
                return fns[item]
            return getattr(self.__dict__["_real"], item)

        def _OpenProcess(self, acc, inherit, pid):
            calls["open"].append(pid)
            return pid + 100000

        def _Query(self, hp, flags, buf, ln):
            # 桩：只写 buf.value（母本 kill_under 仅读 buf.value，不读 ln）
            pid = hp - 100000
            if pid in _SYNTH_GAMES:
                buf.value = str(carrier) + "\\gamemd.exe"
            else:
                buf.value = r"C:\Windows\System32\svchost.exe"
            return 1

        def _Term(self, hp, code):
            calls["terminate"].append(hp - 100000)
            return 1

    orig_lp, orig_k32 = mc.list_procs, mc.k32
    try:
        mc.list_procs = lambda: {7771: "gamemd.exe", 7772: "GameMD.EXE",
                                 7773: "gamemd.exe", 7774: "notepad.exe",
                                 7775: "ra2loader.exe", 7776: "game.exe"}
        mc.k32 = FakeK32(orig_k32)
        killed = mc.kill_under(carrier)
    finally:
        mc.list_procs, mc.k32 = orig_lp, orig_k32

    res["kill_under_selectivity"] = {
        "killed": killed,
        "opened_pids": calls["open"],
        "terminated_pids": calls["terminate"],
        "PASS_only_carrier_match": sorted(k[0] for k in killed) == [7771, 7772],
        "zero_false_positive_on_unrelated":
            7773 not in calls["terminate"] and 7774 not in calls["terminate"]
            and 7775 not in calls["terminate"] and 7776 not in calls["terminate"],
        "note": "7775/7776 名字不在 kill_under 白名单（ra2loader.exe 在？见 raw）",
    }
    print(json.dumps(res, ensure_ascii=False, indent=1))
    (HERE / "rr_p1_r1.stdout.txt").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
