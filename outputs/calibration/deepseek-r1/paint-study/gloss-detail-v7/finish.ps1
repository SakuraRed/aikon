$ErrorActionPreference = 'Stop'
$studyRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$expectedRoot = [IO.Path]::GetFullPath('E:\GH\aikon\outputs\calibration\deepseek-r1\paint-study\gloss-detail-v7')
if ($studyRoot -ne $expectedRoot) { throw 'Unexpected study root' }
$items = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match 'python' -and $_.CommandLine -match 'gloss-detail-v7' -and $_.CommandLine -notmatch 'run_bounded'
} | Select-Object ProcessId,ParentProcessId,Name,CreationDate,CommandLine)
ConvertTo-Json -InputObject $items -Depth 4 | Set-Content -LiteralPath (Join-Path $studyRoot 'process-final.json') -Encoding utf8
$cachePath = Join-Path $studyRoot '__pycache__'
if (([IO.Path]::GetFullPath($cachePath) -eq ($expectedRoot + '\__pycache__')) -and (Test-Path -LiteralPath $cachePath)) {
    Remove-Item -LiteralPath $cachePath -Recurse -Force
}
Write-Output ('owned_worker_count=' + $items.Count)
