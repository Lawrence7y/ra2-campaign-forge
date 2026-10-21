"""③ 真机 deploy → smoke → rollback → 哈希复核（一个完整周期）。

★ 纪律：
  - 母本零改动：只读 `ra2render/` 与 `lead/` 下的件，绝不写。
  - 部署只落**隔离载体**（`WORKDIR/ct/c_<stamp>_<pid>`），复用 harness3 的
    `create_isolated_carrier` 语义（排他 mkdir + 逐件复读验 SHA）。
  - 每步留痕：`_deploy_cycle.json` 记录每一步的前后哈希。
  - 趟后必删载体 + 零残留进程（用户硬要求）。

阶段：
  S1 deploy   把合批 DLL + ini.v2 放进载体，记录部署前后哈希
  S2 smoke    起 ra2loader（加载合批 DLL），读模块表确认 DLL 在进程内
  S3 rollback 把载体里的 DLL/ini 还原成原版字节，复核哈希 == 原版
  S4 verify   复核母本三件未改动 + 载体删除 + 零残留
"""
import ctypes
import hashlib
import json
import os
import shutil
import time
from ctypes import wintypes as wt
from datetime import datetime
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead"
TRIP = LEAD / "qc161_u0400_trip"
SRC = TRIP / "_src_L1_sf8_20261020"
OUT = LEAD / "goal3_deploy_cycle_20261021"

MERGED_DLL = LEAD / "goal3_p1sbh_merge_20261020/build/ra2render_merged.dll"
INI_V2 = LEAD / "goal3_verifyhooks_fix_20261020/ra2render.ini.v2"

MOTHER_CPP = ROOT / "ra2render/blitter_hooks.cpp"
MOTHER_INI = ROOT / "ra2render/ra2render.ini"

MOTHER_CPP_SHA16 = "656e6b4e48cdd251"
MOTHER_INI_SHA16 = "27c9a60c55a8a1b4"

k32 = ctypes.WinDLL("kernel32", use_last_error=True)


class PE32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
                ("th32ProcessID", wt.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
                ("th32ParentProcessID", wt.DWORD),
                ("pcPriClassBase", ctypes.c_long), ("dwFlags", wt.DWORD),
                ("szExeFile", wt.WCHAR * 260)]


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def sha_full(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def list_procs():
    k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
    k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
    h = k32.CreateToolhelp32Snapshot(2, 0)
    if not h or h == ctypes.c_void_p(-1).value:
        return {}
    out = {}
    e = PE32()
    e.dwSize = ctypes.sizeof(PE32)
    k32.Process32FirstW.argtypes = [wt.HANDLE, ctypes.POINTER(PE32)]
    k32.Process32NextW.argtypes = [wt.HANDLE, ctypes.POINTER(PE32)]
    ok = k32.Process32FirstW(h, ctypes.byref(e))
    while ok:
        out[e.th32ProcessID] = e.szExeFile
        ok = k32.Process32NextW(h, ctypes.byref(e))
    k32.CloseHandle(h)
    return out


def procs_with_parent():
    """pid -> (name, parent_pid)，用于找 ra2loader 派生的 gamemd。"""
    k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
    k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
    h = k32.CreateToolhelp32Snapshot(2, 0)
    if not h or h == ctypes.c_void_p(-1).value:
        return {}
    out = {}
    e = PE32()
    e.dwSize = ctypes.sizeof(PE32)
    k32.Process32FirstW.argtypes = [wt.HANDLE, ctypes.POINTER(PE32)]
    k32.Process32NextW.argtypes = [wt.HANDLE, ctypes.POINTER(PE32)]
    ok = k32.Process32FirstW(h, ctypes.byref(e))
    while ok:
        out[e.th32ProcessID] = (e.szExeFile, e.th32ParentProcessID)
        ok = k32.Process32NextW(h, ctypes.byref(e))
    k32.CloseHandle(h)
    return out


def find_gamemd_under(loader_pid):
    """★ ra2loader 不是注入目标：它 CreateProcess 出 gamemd，再把 DLL 注入 gamemd。
    ⇒ 模块表必须查 **gamemd 的 pid**，不是 loader 的 pid（U8 实证：
    launch_pid=38192 而 gamemd_pid=41604，两者不同）。"""
    for _ in range(40):
        table = procs_with_parent()
        for pid, (nm, ppid) in table.items():
            if nm.lower() == "gamemd.exe" and ppid == loader_pid:
                return pid
        # 也接受孙进程（loader -> 中间层 -> gamemd）
        for pid, (nm, ppid) in table.items():
            if nm.lower() == "gamemd.exe":
                anc, depth = ppid, 0
                while anc and anc in table and depth < 4:
                    if anc == loader_pid:
                        return pid
                    anc = table[anc][1]
                    depth += 1
        time.sleep(0.25)
    return None


def game_procs():
    return [(pid, n) for pid, n in list_procs().items()
            if n.lower() in ("gamemd.exe", "ra2loader.exe", "game.exe")]


def modules_of(pid):
    """Toolhelp32 枚举模块（64 位 Python 读 32 位进程的可靠路径）。"""
    k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
    k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
    TH32CS_SNAPMODULE = 0x00000008
    TH32CS_SNAPMODULE32 = 0x00000010

    class MODULEENTRY32W(ctypes.Structure):
        _fields_ = [("dwSize", wt.DWORD), ("th32ModuleID", wt.DWORD),
                    ("th32ProcessID", wt.DWORD), ("GlblcntUsage", wt.DWORD),
                    ("ProccntUsage", wt.DWORD),
                    ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)),
                    ("modBaseSize", wt.DWORD), ("hModule", wt.HMODULE),
                    ("szModule", wt.WCHAR * 256), ("szExePath", wt.WCHAR * 260)]

    h = k32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid)
    if not h or h == ctypes.c_void_p(-1).value:
        return None
    out = []
    me = MODULEENTRY32W()
    me.dwSize = ctypes.sizeof(MODULEENTRY32W)
    k32.Module32FirstW.argtypes = [wt.HANDLE, ctypes.POINTER(MODULEENTRY32W)]
    k32.Module32NextW.argtypes = [wt.HANDLE, ctypes.POINTER(MODULEENTRY32W)]
    ok = k32.Module32FirstW(h, ctypes.byref(me))
    while ok:
        out.append({
            "name": me.szModule,
            "path": me.szExePath,
            "base": int(ctypes.cast(me.modBaseAddr, ctypes.c_void_p).value or 0),
            "size": int(me.modBaseSize),
        })
        ok = k32.Module32NextW(h, ctypes.byref(me))
    k32.CloseHandle(h)
    return out


def kill_under(cdir):
    k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k32.OpenProcess.restype = wt.HANDLE
    k32.QueryFullProcessImageNameW.argtypes = [
        wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD)]
    k32.QueryFullProcessImageNameW.restype = wt.BOOL
    k32.TerminateProcess.argtypes = [wt.HANDLE, wt.UINT]
    k32.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]
    k32.CloseHandle.argtypes = [wt.HANDLE]
    target = str(cdir).lower()
    killed = []
    for pid, nm in game_procs():
        hp = k32.OpenProcess(0x0001 | 0x1000, False, pid)
        if not hp:
            continue
        try:
            buf = ctypes.create_unicode_buffer(1024)
            ln = wt.DWORD(1024)
            if k32.QueryFullProcessImageNameW(hp, 0, buf, ctypes.byref(ln)):
                if target in buf.value.lower():
                    k32.TerminateProcess(hp, 1)
                    k32.WaitForSingleObject(hp, 6000)
                    killed.append((pid, nm))
        finally:
            k32.CloseHandle(hp)
    return killed


def rm_tree(cdir):
    last = None
    for i in range(8):
        time.sleep(1.0 + i * 0.5)
        try:
            shutil.rmtree(cdir)
            return True, None
        except Exception as e:
            last = e
    return False, last


def main():
    rec = {"started": datetime.now().isoformat(timespec="seconds"), "steps": {}}
    OUT.mkdir(parents=True, exist_ok=True)

    print("=" * 76)
    print("③ 真机 deploy → smoke → rollback → 哈希复核")
    print("=" * 76)

    # ---- 预检 ----
    print("\n[预检]")
    checks = [
        ("母本 blitter_hooks.cpp", sha16(MOTHER_CPP), MOTHER_CPP_SHA16),
        ("母本 ra2render.ini", sha16(MOTHER_INI), MOTHER_INI_SHA16),
        ("合批 DLL 在盘", str(MERGED_DLL.is_file()), "True"),
        ("ini.v2 在盘", str(INI_V2.is_file()), "True"),
        ("游戏进程数", str(len(game_procs())), "0"),
    ]
    ok = True
    for name, got, want in checks:
        good = got == want
        ok &= good
        print("  %-26s got=%-20s want=%-20s %s"
              % (name, got, want, "OK" if good else "MISMATCH"))
    if not ok:
        print("!! 预检不过，不发射")
        return 2

    # 路径长度预演（沿用 130 门禁）
    probe = OUT / "ct" / ("c_" + "0" * 12 + "_12345")
    plen = len(str(probe))
    print("  %-26s len=%d (门禁 130) %s"
          % ("载体目录预演", plen, "OK" if plen <= 130 else "BLOCK"))
    if plen > 130:
        return 2

    # ---- S1 deploy ----
    print("\n[S1 deploy]")
    stamp = datetime.now().strftime("%H%M%S%f")
    (OUT / "ct").mkdir(parents=True, exist_ok=True)
    cdir = OUT / "ct" / ("c_%s_%d" % (stamp, os.getpid()))
    os.mkdir(str(cdir))
    print("  载体:", cdir)

    # ★ 件集 = 冻结清单 88 件全量（与 U8 探针 / l1d 基线趟同口径）。
    #   ★ 教训：只放 9 件「最小启动链」时 gamemd 起不来（缺 .mix ⇒ 加载期即退），
    #     loader 的 `find_gamemd_under` 返回 None ⇒ 冒烟假失败。
    MANIFEST = TRIP / "_src_L1_sf8_20261020_MANIFEST.json"
    _mf = json.loads(MANIFEST.read_text(encoding="utf-8"))
    need = sorted(_mf["files"].keys())
    assert len(need) == 88, "冻结清单应为 88 条，实得 %d" % len(need)
    copied = []
    missing = []
    for n in need:
        s = SRC / n
        if not s.is_file():
            missing.append(n)
            continue
        d = cdir / n
        d.write_bytes(s.read_bytes())
        if sha_full(d) != sha_full(s):
            raise RuntimeError("复制校验失败: " + n)
        copied.append(n)

    dll_path = cdir / "ra2render.dll"
    ini_path = cdir / "ra2render.ini"

    pre = {
        "dll_orig_sha16": sha16(dll_path),
        "ini_orig_sha16": sha16(ini_path),
        "dll_orig_size": dll_path.stat().st_size,
        "ini_orig_size": ini_path.stat().st_size,
    }
    # 备份原版字节（回滚用）
    bak = OUT / "_orig_bak"
    bak.mkdir(exist_ok=True)
    (bak / "ra2render.dll").write_bytes(dll_path.read_bytes())
    (bak / "ra2render.ini").write_bytes(ini_path.read_bytes())

    # 部署
    dll_path.write_bytes(MERGED_DLL.read_bytes())
    ini_path.write_bytes(INI_V2.read_bytes())

    post = {
        "dll_deployed_sha16": sha16(dll_path),
        "ini_deployed_sha16": sha16(ini_path),
        "dll_deployed_size": dll_path.stat().st_size,
        "ini_deployed_size": ini_path.stat().st_size,
    }
    print("  复制 %d 件（缺 %d 件）" % (len(copied), len(missing)))
    if missing:
        print("  缺件:", missing)
    print("  DLL %s (%d B) → %s (%d B)"
          % (pre["dll_orig_sha16"], pre["dll_orig_size"],
             post["dll_deployed_sha16"], post["dll_deployed_size"]))
    print("  INI %s (%d B) → %s (%d B)"
          % (pre["ini_orig_sha16"], pre["ini_orig_size"],
             post["ini_deployed_sha16"], post["ini_deployed_size"]))
    assert post["dll_deployed_sha16"] == sha16(MERGED_DLL), "部署后 DLL 哈希不符"
    assert post["ini_deployed_sha16"] == sha16(INI_V2), "部署后 INI 哈希不符"
    rec["steps"]["S1_deploy"] = {"carrier": str(cdir), "copied": len(copied),
                                 "missing": missing, "pre": pre, "post": post}
    print("  ✅ S1 部署完成（部署后哈希 = 源件哈希）")

    # ---- S2 smoke ----
    print("\n[S2 smoke]")
    loader = cdir / "ra2loader.exe"
    smoke = {"launched": False, "loader_pid": None,
             "modules": None, "ra2render_loaded": False,
             "ra2render_base": None, "ra2render_size": None,
             "log_present": False}
    # 用 CreateProcessW（避免 shell；不带 stdio 重定向）
    class STARTUPINFOW(ctypes.Structure):
        _fields_ = [("cb", wt.DWORD), ("lpReserved", wt.LPWSTR),
                    ("lpDesktop", wt.LPWSTR), ("lpTitle", wt.LPWSTR),
                    ("dwX", wt.DWORD), ("dwY", wt.DWORD),
                    ("dwXSize", wt.DWORD), ("dwYSize", wt.DWORD),
                    ("dwXCountChars", wt.DWORD), ("dwYCountChars", wt.DWORD),
                    ("dwFillAttribute", wt.DWORD), ("dwFlags", wt.DWORD),
                    ("wShowWindow", wt.WORD), ("cbReserved2", wt.WORD),
                    ("lpReserved2", ctypes.c_void_p),
                    ("hStdInput", wt.HANDLE), ("hStdOutput", wt.HANDLE),
                    ("hStdError", wt.HANDLE)]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [("hProcess", wt.HANDLE), ("hThread", wt.HANDLE),
                    ("dwProcessId", wt.DWORD), ("dwThreadId", wt.DWORD)]

    si = STARTUPINFOW()
    si.cb = ctypes.sizeof(STARTUPINFOW)
    pi = PROCESS_INFORMATION()
    k32.CreateProcessW.argtypes = [
        wt.LPCWSTR, wt.LPWSTR, ctypes.c_void_p, ctypes.c_void_p,
        wt.BOOL, wt.DWORD, ctypes.c_void_p, wt.LPCWSTR,
        ctypes.POINTER(STARTUPINFOW), ctypes.POINTER(PROCESS_INFORMATION)]
    k32.CreateProcessW.restype = wt.BOOL

    okc = k32.CreateProcessW(
        str(loader), None, None, None, False, 0, None, str(cdir),
        ctypes.byref(si), ctypes.byref(pi))
    if not okc:
        smoke["err"] = "CreateProcessW failed: %d" % ctypes.get_last_error()
        print("  !! 启动失败:", smoke["err"])
    else:
        smoke["launched"] = True
        smoke["loader_pid"] = int(pi.dwProcessId)
        print("  loader pid =", pi.dwProcessId)
        k32.CloseHandle(pi.hThread)

        # ★ ra2render 注入的是 **gamemd**，不是 loader ⇒ 先找 gamemd 的 pid
        gm_pid = find_gamemd_under(pi.dwProcessId)
        smoke["gamemd_pid"] = gm_pid
        print("  gamemd pid =", gm_pid)
        target_pid = gm_pid if gm_pid else pi.dwProcessId
        smoke["module_enum_pid"] = target_pid

        # 等 DLL 加载
        # ★ 绝对时刻采样，不用相对 sleep 累加（否则第 n 轮总等时是前 n 项之和）
        found = None
        t_start = time.monotonic()
        for t_abs in (0.3, 0.6, 1.0, 1.6, 2.4, 3.5, 5.0, 7.0, 10.0, 14.0):
            wait = t_abs - (time.monotonic() - t_start)
            if wait > 0:
                time.sleep(wait)
            # gamemd 可能晚于 loader 出现，每轮重找
            if gm_pid is None:
                gm_pid = find_gamemd_under(pi.dwProcessId)
                if gm_pid:
                    smoke["gamemd_pid"] = gm_pid
                    target_pid = gm_pid
                    smoke["module_enum_pid"] = gm_pid
            mods = modules_of(target_pid)
            if mods:
                smoke["modules"] = len(mods)
                hit = [m for m in mods
                       if "ra2render" in m["name"].lower()]
                if hit:
                    found = hit[0]
                    smoke["found_at_s"] = round(time.monotonic() - t_start, 2)
                    break
        if found:
            smoke["ra2render_loaded"] = True
            smoke["ra2render_base"] = "0x%08X" % found["base"]
            smoke["ra2render_size"] = found["size"]
            print("  ✅ ra2render.dll 已加载 base=%s size=%d"
                  % (smoke["ra2render_base"], found["size"]))
        else:
            print("  !! 未在模块表中找到 ra2render（modules=%s）"
                  % smoke.get("modules"))

        # 读 ra2render.log 佐证（★ 完整留档到证据目录，不只截前 600 B）
        logp = cdir / "ra2render.log"
        if logp.is_file():
            smoke["log_present"] = True
            raw = logp.read_bytes()
            smoke["log_size"] = len(raw)
            txt = raw.decode("utf-8", errors="replace")
            smoke["log_head"] = txt[:600]
            smoke["log_tail"] = txt[-1200:]
            # ★ 关键标记计数（判定 P1 版本门 / SBH 守卫是否接线）
            smoke["markers"] = {
                k: txt.count(k) for k in
                ("VER-GATE", "SBH-GUARD", "SbhGuard", "VersionGate",
                 "G3-SPLIT", "版本门", "EnableSbhGuard")
            }
            ev = OUT / "_smoke_ra2render.log"
            ev.write_bytes(raw)
            smoke["log_evidence"] = str(ev)
            print("  ra2render.log 存在，%d B；标记 %s"
                  % (len(raw), smoke["markers"]))

        # 终止 loader 树
        killed = kill_under(cdir)
        print("  终止:", killed or "无")
        smoke["killed"] = killed
        k32.CloseHandle(pi.hProcess)

    rec["steps"]["S2_smoke"] = smoke

    # ---- S3 rollback ----
    print("\n[S3 rollback]")

    def _restore(dst, srcbytes, tries=20):
        """★ 进程刚被 TerminateProcess 时 DLL 映像仍被映射 ⇒ 写回会 PermissionError。
        ⇒ 退避重试到句柄真正释放（实测 ~2–6 s）。"""
        last = None
        for i in range(tries):
            try:
                Path(dst).write_bytes(srcbytes)
                return True, None
            except PermissionError as e:
                last = e
                time.sleep(0.5 + i * 0.25)
            except Exception as e:
                last = e
                time.sleep(0.5)
        return False, last

    ok_d, err_d = _restore(dll_path, (bak / "ra2render.dll").read_bytes())
    ok_i, err_i = _restore(ini_path, (bak / "ra2render.ini").read_bytes())
    if not (ok_d and ok_i):
        print("  !! 还原写入失败: dll=%s ini=%s" % (err_d, err_i))
    rb = {
        "dll_after_sha16": sha16(dll_path),
        "ini_after_sha16": sha16(ini_path),
        "dll_matches_orig": sha16(dll_path) == pre["dll_orig_sha16"],
        "ini_matches_orig": sha16(ini_path) == pre["ini_orig_sha16"],
        "dll_matches_src": sha16(dll_path) == sha16(SRC / "ra2render.dll"),
        "ini_matches_src": sha16(ini_path) == sha16(SRC / "ra2render.ini"),
    }
    print("  DLL → %s  等于原版=%s  等于源变体=%s"
          % (rb["dll_after_sha16"], rb["dll_matches_orig"], rb["dll_matches_src"]))
    print("  INI → %s  等于原版=%s  等于源变体=%s"
          % (rb["ini_after_sha16"], rb["ini_matches_orig"], rb["ini_matches_src"]))
    rec["steps"]["S3_rollback"] = rb
    print("  %s S3 回滚" % ("✅" if (rb["dll_matches_orig"] and rb["ini_matches_orig"]) else "❌"))

    # ---- S4 verify ----
    print("\n[S4 verify]")
    left_proc = game_procs()
    # 先杀再删
    kill_under(cdir)
    left_proc = game_procs()
    del_ok, del_err = rm_tree(cdir)
    v = {
        "mother_cpp_sha16": sha16(MOTHER_CPP),
        "mother_ini_sha16": sha16(MOTHER_INI),
        "mother_cpp_unchanged": sha16(MOTHER_CPP) == MOTHER_CPP_SHA16,
        "mother_ini_unchanged": sha16(MOTHER_INI) == MOTHER_INI_SHA16,
        "carrier_deleted": del_ok,
        "carrier_delete_err": str(del_err) if del_err else None,
        "leftover_procs": [{"pid": p, "name": n} for p, n in left_proc],
    }
    print("  母本 cpp %s  未改=%s" % (v["mother_cpp_sha16"], v["mother_cpp_unchanged"]))
    print("  母本 ini %s  未改=%s" % (v["mother_ini_sha16"], v["mother_ini_unchanged"]))
    print("  载体已删=%s" % v["carrier_deleted"])
    print("  残留进程=%s" % (v["leftover_procs"] or "无"))
    rec["steps"]["S4_verify"] = v

    # 清 bak（部署周期的中间件，不留在盘上）
    try:
        shutil.rmtree(bak)
        rec["steps"]["S4_verify"]["bak_removed"] = True
    except Exception as e:
        rec["steps"]["S4_verify"]["bak_removed"] = False
        rec["steps"]["S4_verify"]["bak_err"] = str(e)

    # ---- 总判 ----
    s1 = rec["steps"]["S1_deploy"]
    s2 = rec["steps"]["S2_smoke"]
    s3 = rec["steps"]["S3_rollback"]
    s4 = rec["steps"]["S4_verify"]
    verdicts = {
        "S1_deploy_ok": (s1["post"]["dll_deployed_sha16"] == sha16(MERGED_DLL)
                         and s1["post"]["ini_deployed_sha16"] == sha16(INI_V2)),
        "S2_smoke_ok": bool(s2.get("launched") and s2.get("ra2render_loaded")),
        "S3_rollback_ok": bool(s3["dll_matches_orig"] and s3["ini_matches_orig"]
                               and s3["dll_matches_src"] and s3["ini_matches_src"]),
        "S4_hygiene_ok": bool(s4["mother_cpp_unchanged"]
                              and s4["mother_ini_unchanged"]
                              and s4["carrier_deleted"]
                              and not s4["leftover_procs"]),
    }
    rec["verdicts"] = verdicts
    rec["all_pass"] = all(verdicts.values())
    rec["finished"] = datetime.now().isoformat(timespec="seconds")

    print("\n" + "=" * 76)
    for k, val in verdicts.items():
        print("  %-18s %s" % (k, "PASS" if val else "FAIL"))
    print("  总判: %s" % ("★ 完整周期 PASS" if rec["all_pass"] else "❌ 有项未过"))
    print("=" * 76)

    (OUT / "_deploy_cycle.json").write_text(
        json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n[结果]", OUT / "_deploy_cycle.json")
    return 0 if rec["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
