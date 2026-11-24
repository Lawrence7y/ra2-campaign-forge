# posctrl_ps.ps1 — Q5 正控「法 1」：PowerShell 独立实现（只读，不写任何文件，只 print）。
#
# 独立性：不复用任何 Python 代码。用 .NET Directory/File 枚举自写 BFS，
# 不复用 measure_clean.py 的 os.walk，也不复用 Get-ChildItem 的默认语义。
#
# 档 A 口径（同 mev675.py:49 PRIMARY_EXT + :251-289 stage_scale）：
#   根       : D:\Project\ra2-campaign-forge\lead
#   扩展名   : .tsv .txt .json .md .csv .log
#   排除     : 任意深度目录名 == '.git'；本卡 out 目录
#   隐藏文件 : 计入（枚举文件系统条目，不看 Hidden 属性）
#   目录链接 : 显式不跟随（ReparsePoint 跳过）
param(
  [string]$Lead = 'D:\Project\ra2-campaign-forge\lead',
  [string]$Out  = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R72_T1_CLEANSCALE'
)
$ErrorActionPreference = 'Stop'

$exts = @('.tsv', '.txt', '.json', '.md', '.csv', '.log')
$outFull = [System.IO.Path]::GetFullPath($Out).TrimEnd('\')

$n = 0
$total = [int64]0
$stack = [System.Collections.Generic.Stack[string]]::new()
$stack.Push([System.IO.Path]::GetFullPath($Lead).TrimEnd('\'))

while ($stack.Count -gt 0) {
  $dir = $stack.Pop()
  try {
    foreach ($e in [System.IO.Directory]::EnumerateFileSystemEntries($dir)) {
      $attr = [System.IO.File]::GetAttributes($e)
      $isDir = ($attr -band [System.IO.FileAttributes]::Directory) -ne 0
      if ($isDir) {
        $name = [System.IO.Path]::GetFileName($e)
        if ($name -ieq '.git') { continue }
        if (($attr -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { continue }
        if ($e.TrimEnd('\') -ieq $outFull) { continue }
        $stack.Push($e)
      } else {
        $ext = [System.IO.Path]::GetExtension($e).ToLowerInvariant()
        if ($exts -notcontains $ext) { continue }
        $len = ([System.IO.FileInfo]$e).Length
        $n++
        $total += $len
      }
    }
  } catch [System.UnauthorizedAccessException] {
    Write-Warning "access denied: $dir"
  }
}
"posctrl_ps files=$n bytes=$total"
