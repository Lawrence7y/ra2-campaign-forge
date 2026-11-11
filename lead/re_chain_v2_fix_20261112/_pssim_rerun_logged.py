# -*- coding: utf-8 -*-
"""C1 收尾：重跑一次 _pssim_rerun.py，并补一份「带时间戳与退出码」的运行日志，
   使『重跑确实发生过』可闭环（原交付缺 _pssim_rerun_out.txt，产物同 sha 不足以独立证明）。
零真机：只调用磁盘上的 python 脚本，不启动 gamemd.exe/ra2loader/YURI.exe，不 attach，不读活进程内存。
写域：仅 lead/re_chain_v2_fix_20261112/（新建）。原 _pssim_rerun.py 及其既有产物保持零改动。
"""
import datetime
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
LEAD = os.path.join(REPO, "lead")
SYNTH = os.path.join(LEAD, "re_chain_synth_v2_20261111")
DRIVER = os.path.join(SYNTH, "_pssim_rerun.py")
DRIVER_STDOUT = os.path.join(HERE, "_pssim_rerun_driver_stdout.txt")
RUNLOG = os.path.join(HERE, "_pssim_rerun_runlog.txt")

# 重跑前后都要核对的既有产物（都在 SYNTH 写域内，由原 driver 重写；预期逐字节不变）
PRODUCTS = [
    ("_pssim_rerun_stdout.txt", os.path.join(SYNTH, "_pssim_rerun_stdout.txt")),
    ("_pssim_rerun_stderr.txt", os.path.join(SYNTH, "_pssim_rerun_stderr.txt")),
    ("_ps_disasm_out.txt", os.path.join(SYNTH, "_ps_disasm_out.txt")),
    ("_ps_disasm_out.json", os.path.join(SYNTH, "_ps_disasm_out.json")),
    ("_ps_disasm_rerun_copy.py", os.path.join(SYNTH, "_ps_disasm_rerun_copy.py")),
]
OLD_TXT = os.path.join(LEAD, "playerctrl_semantics_20261111", "_ps_disasm_out.txt")
OLD_JSON = os.path.join(LEAD, "playerctrl_semantics_20261111", "_ps_disasm_out.json")


def fp(p):
    if not os.path.isfile(p):
        return ("MISSING", -1)
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            n += len(b)
            h.update(b)
    return (h.hexdigest(), n)


def stamp():
    now = datetime.datetime.now().astimezone()
    utc = datetime.datetime.now(datetime.timezone.utc)
    return (now.isoformat(timespec="seconds"), utc.isoformat(timespec="seconds"))


def main():
    local0, utc0 = stamp()
    cmd = [sys.executable, "-I", "-X", "utf8", DRIVER]
    print("== C1 带运行日志的重跑 ==")
    print("start_local = %s" % local0)
    print("start_utc   = %s" % utc0)
    print("command     = %s" % " ".join(cmd))
    before = {name: fp(p) for name, p in PRODUCTS}
    driver_before = fp(DRIVER)
    print("[before] driver sha=%s size=%d" % (driver_before[0], driver_before[1]))
    for name, p in PRODUCTS:
        print("[before] %-28s sha=%s size=%d" % (name, before[name][0], before[name][1]))

    with open(DRIVER_STDOUT, "wb") as so:
        rc = subprocess.call(cmd, stdout=so, stderr=subprocess.STDOUT, cwd=SYNTH)
    local1, utc1 = stamp()

    after = {name: fp(p) for name, p in PRODUCTS}
    driver_after = fp(DRIVER)
    print("[driver] exit_code = %d" % rc)
    print("[after ] driver sha=%s size=%d (与 before 相同=%s)" %
          (driver_after[0], driver_after[1], driver_after == driver_before))
    for name, p in PRODUCTS:
        print("[after ] %-28s sha=%s size=%d  与 before 相同=%s" %
              (name, after[name][0], after[name][1], after[name] == before[name]))

    # 文件级对拍：重跑产物 vs 既有原件（只读）
    m_txt = after["_ps_disasm_out.txt"][0] == fp(OLD_TXT)[0]
    m_json = after["_ps_disasm_out.json"][0] == fp(OLD_JSON)[0]
    print("[match ] out.txt vs 既有原件 MATCH=%s ; out.json vs 既有原件 MATCH=%s" % (m_txt, m_json))
    print("[stdout] driver stdout 落盘 %s = %d B, sha=%s" %
          (os.path.basename(DRIVER_STDOUT), fp(DRIVER_STDOUT)[1], fp(DRIVER_STDOUT)[0]))
    print("end_local   = %s" % local1)
    print("end_utc     = %s" % utc1)

    # ---- 运行日志（时间戳 + 退出码 + 命令 + 产物指纹），使「重跑发生过」可闭环 ----
    with open(RUNLOG, "w", encoding="utf-8", newline="\n") as f:
        f.write("# _pssim_rerun.py 运行日志（C1 补件；本文件由 _pssim_rerun_logged.py 在本轮实跑后写出）\n")
        f.write("run_id              : C1-20261112-rerun-01\n")
        f.write("start_local         : %s\n" % local0)
        f.write("start_utc           : %s\n" % utc0)
        f.write("end_local           : %s\n" % local1)
        f.write("end_utc             : %s\n" % utc1)
        f.write("command             : %s\n" % " ".join(cmd))
        f.write("cwd                 : %s\n" % SYNTH)
        f.write("driver_exit_code    : %d\n" % rc)
        f.write("driver_sha256_before: %s (%d B)\n" % (driver_before[0], driver_before[1]))
        f.write("driver_sha256_after : %s (%d B)\n" % (driver_after[0], driver_after[1]))
        f.write("driver_stdout_file  : %s\n" % DRIVER_STDOUT)
        f.write("driver_stdout_sha256: %s (%d B)\n" % (fp(DRIVER_STDOUT)[0], fp(DRIVER_STDOUT)[1]))
        f.write("probe_stdout        : _pssim_rerun_stdout.txt  %s (%d B)\n" %
                (after["_pssim_rerun_stdout.txt"][0], after["_pssim_rerun_stdout.txt"][1]))
        f.write("probe_stderr        : _pssim_rerun_stderr.txt  %s (%d B)\n" %
                (after["_pssim_rerun_stderr.txt"][0], after["_pssim_rerun_stderr.txt"][1]))
        f.write("rerun_out_txt_sha256: %s (%d B)\n" % (after["_ps_disasm_out.txt"][0], after["_ps_disasm_out.txt"][1]))
        f.write("rerun_out_json_sha256:%s (%d B)\n" % (after["_ps_disasm_out.json"][0], after["_ps_disasm_out.json"][1]))
        f.write("file_level_match_txt : %s\n" % m_txt)
        f.write("file_level_match_json: %s\n" % m_json)
        f.write("products_unchanged   : %s\n" % all(after[n] == before[n] for n, _ in PRODUCTS))
        f.write("note                : 探针 stdout 恒 0 B（脚本把 print 重定向进内部缓冲）；"
                "本日志的时间戳/退出码/driver stdout 由本轮 subprocess.call 实跑产生，"
                "可与 _pssim_rerun_driver_stdout.txt 的 [1]-[5] 判定日志互证。\n")
        f.write("zero_live_machine   : 未启动 gamemd.exe/ra2loader/YURI.exe，未 attach，未读活进程内存，未写 hook/采样/MiniDump 代码。\n")
    print("[runlog] 已写出 %s (%d B)" % (RUNLOG, fp(RUNLOG)[1]))
    print("== DONE ==")


if __name__ == "__main__":
    main()
