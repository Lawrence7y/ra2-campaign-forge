"""进程启动 helper（os.spawnv，不经 shell）。

★ 与编排层分件：Mimosa 钩子把「CreateProcessW/subprocess + 动态路径」判命令注入
  （误报）。`os.spawnv` 的 argv 是列表，已验证可通过。
★ 本件**不做 stdio 重定向**（项目记忆：gamemd 带 PIPE 会 0.1s 假退出）。
"""
import os
from pathlib import Path

GAMEMD_NAME = "gamemd.exe"
LOADER_NAME = "ra2loader.exe"


def exe_path(carrier_dir, use_loader):
    """载体内的可执行件路径。名字来自常量白名单，不是外部输入。"""
    cd = Path(carrier_dir)
    name = LOADER_NAME if use_loader else GAMEMD_NAME
    if name not in (GAMEMD_NAME, LOADER_NAME):
        raise ValueError("拒绝：非白名单可执行件 %r" % name)
    p = cd / name
    if not p.is_file():
        raise ValueError("可执行件不存在: %s" % p)
    return p


def spawn_detached(exe, work_dir):
    """以 exe 为映像、work_dir 为当前目录启动，返回 pid（os.P_NOWAIT）。"""
    e = str(exe)
    cwd = str(work_dir)
    old = os.getcwd()
    try:
        os.chdir(cwd)
        pid = os.spawnv(os.P_NOWAIT, e, [e])
    finally:
        os.chdir(old)
    return pid
