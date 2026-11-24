@echo off
rem ra2opt 启动器 - 由 `python -m ra2opt apply` 生成，可安全删除
rem 作用：以高优先级启动游戏，减少被其他进程抢占造成的卡顿。
rem 直接双击 gamemd.exe 也能玩，只是没有这个优先级提升。
cd /d "%~dp0"
start "" /high "gamemd.exe"
