@echo off
REM ====================================================================
REM W86 最小实验 · 候选1：ETW 短试采（D3D9 Present + DxgKrnl Present 关键字）
REM 依据 RULING_GPT61SOL.md Q3：有停止条件的短试采；三问答不出即停，不扩大。
REM 必须以管理员身份运行。
REM
REM provider（本机 Get-WinEvent 实测在机，2026-11-14）：
REM   Microsoft-Windows-D3D9    {783ACA0A-790E-4D7F-8451-AA850511C6B9}
REM     EventID 1 = Task "Present" Opcode Start   (pSwapchain, Flags)   <- 提交层
REM     EventID 2 = Task "Present" Opcode Stop    (Result)
REM   Microsoft-Windows-DxgKrnl {802EC45A-1E99-4B83-9920-87C98277BA9D}
REM     keyword Present = 0x8000000
REM     184=Present 469/470=PresentQueuePacket 171-173=PresentHistory
REM     116/259/386=MMIOFlip 系 1068=CompleteIndirectPresent(显示层)
REM
REM 判读三问（采完必须逐条回答，答不出即停）：
REM   Q1 事件能否稳定关联 gamemd.exe（按 ProcessId 过滤；pSwapchain 分组）
REM   Q2 记录层级：D3D9 id1/2 = 提交(submit)；DxgKrnl 1068/505 = 显示(displayed)
REM      —— 报告措辞必须与实际层级一致，不得混称
REM   Q3 丢失：logman stop 输出的 lost events 必须为 0（有效区间内）
REM ====================================================================
setlocal
set W86DIR=%~dp0
if "%W86DIR:~-1%"=="\" set W86DIR=%W86DIR:~0,-1%
set ETLDIR=%W86DIR%\etl_out
if not exist "%ETLDIR%" mkdir "%ETLDIR%"
set ETL=%ETLDIR%\W86P.etl

echo [1/5] 创建 ETW 会话 W86P ...
logman stop W86P -ets >nul 2>&1
logman create trace W86P -ow -o %ETL% ^
  -p {783ACA0A-790E-4D7F-8451-AA850511C6B9} 0xffffffff 5 ^
  -p {802EC45A-1E99-4B83-9920-87C98277BA9D} 0x8000000 4 ^
  -nb 128 1024 -ets
if errorlevel 1 (
  echo [FATAL] 会话创建失败——是否管理员？是否已有同名会话？
  exit /b 1
)

echo [2/5] 会话已启动。现在【手动】正常启动游戏（不要改任何文件），
echo       进入对局后玩 2-5 分钟，然后回到本窗口按任意键停止采集。
echo       gamemd 的 PID 可在另一个窗口用: tasklist /fi "imagename eq gamemd.exe" 查得。
pause >nul

echo [3/5] 停止会话（输出含 lost events 计数，务必存档）...
logman stop W86P -ets

echo [4/5] 转储 ETL -^> XML ...
tracerpt %ETL% -o %ETLDIR%\W86P.xml -of XML -y

echo [5/5] 快速判读（ProcessId 归属粗查）:
powershell -NoProfile -Command ^
  "$x=[xml](Get-Content '%ETLDIR%\W86P.xml' -Encoding Unicode);" ^
  "$ev=$x.EventData.Events.Event;" ^
  "'total events: '+$ev.Count;" ^
  "'D3D9 provider events: '+($ev | Where-Object {$_.Provider.Guid -eq '{783aca0a-790e-4d7f-8451-aa850511c6b9}'} | Measure-Object).Count;" ^
  "'按进程分布(前12):';" ^
  "$ev | Group-Object {$_.ProcessID} -NoElement | Sort-Object Count -Descending | Select-Object -First 12 | ForEach-Object {'  pid='+$_.Name+'  n='+$_.Count};"
echo.
echo 下一步：把 XML 交给解析脚本/人工核对 —— 过滤 pid==gamemd 且 EventID==1，
echo        对 SystemTime 差分得「提交间隔」中位/p95/p99 + 每分钟超 max(50ms,3T) 次数。
echo 语义纪律：D3D9 id1/2 只能叫「提交间隔」；displayed 层看 DxgKrnl 1068/505 是否出现。
echo 丢失检查：上面 logman stop 的输出里 lost events 若非 0，本段数据按裁决无效。
endlocal
