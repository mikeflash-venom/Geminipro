# stop_neo4j.ps1 - 停止Neo4j数据库

param(
    [string]$DatabaseName = ""
)

Write-Host "=== 停止Neo4j数据库 ===" -ForegroundColor Green

# 查找数据库目录
$dbPath = "$env:APPDATA\Neo4j Desktop\Application\neo4jDatabases"

if (-not (Test-Path $dbPath)) {
    Write-Host "错误: 未找到Neo4j数据库目录" -ForegroundColor Red
    Write-Host "路径: $dbPath" -ForegroundColor Yellow
    exit 1
}

$databases = Get-ChildItem -Path $dbPath -Directory

if ($databases.Count -eq 0) {
    Write-Host "错误: 未找到任何数据库" -ForegroundColor Red
    exit 1
}

# 选择数据库
$selectedDb = $null
if ($DatabaseName) {
    $selectedDb = $databases | Where-Object {
        $dbJson = Join-Path $_.FullName "database.json"
        if (Test-Path $dbJson) {
            try {
                $info = Get-Content $dbJson -Raw | ConvertFrom-Json
                $info.name -eq $DatabaseName
            } catch {
                $false
            }
        } else { 
            $false 
        }
    } | Select-Object -First 1
}

if (-not $selectedDb) {
    # 如果有多个数据库，显示列表
    if ($databases.Count -gt 1) {
        Write-Host ""
        Write-Host "可用数据库:" -ForegroundColor Cyan
        $i = 1
        $dbList = @()
        foreach ($db in $databases) {
            $dbJson = Join-Path $db.FullName "database.json"
            if (Test-Path $dbJson) {
                try {
                    $info = Get-Content $dbJson -Raw | ConvertFrom-Json
                    $dbName = if ($info.name) { $info.name } else { $db.Name }
                    Write-Host "  $i. $dbName"
                    $dbList += @{Index=$i-1; Db=$db; Name=$dbName}
                    $i++
                } catch {
                    Write-Host "  $i. $($db.Name)"
                    $dbList += @{Index=$i-1; Db=$db; Name=$db.Name}
                    $i++
                }
            }
        }
        
        Write-Host ""
        $choice = Read-Host "请选择要停止的数据库 (1-$($dbList.Count))"
        try {
            $selectedIndex = [int]$choice - 1
            if ($selectedIndex -ge 0 -and $selectedIndex -lt $dbList.Count) {
                $selectedDb = $dbList[$selectedIndex].Db
                Write-Host "已选择: $($dbList[$selectedIndex].Name)" -ForegroundColor Green
            } else {
                Write-Host "无效选择" -ForegroundColor Red
                exit 1
            }
        } catch {
            Write-Host "无效输入" -ForegroundColor Red
            exit 1
        }
    } else {
        # 只有一个数据库，自动选择
        $selectedDb = $databases | Select-Object -First 1
        $dbJson = Join-Path $selectedDb.FullName "database.json"
        if (Test-Path $dbJson) {
            try {
                $info = Get-Content $dbJson -Raw | ConvertFrom-Json
                $dbName = if ($info.name) { $info.name } else { $selectedDb.Name }
                Write-Host "自动选择数据库: $dbName" -ForegroundColor Green
            } catch {
                Write-Host "使用数据库: $($selectedDb.Name)" -ForegroundColor Green
            }
        }
    }
}

# 查找安装目录
$installation = Get-ChildItem -Path $selectedDb.FullName -Filter "installation-*" -Directory | Select-Object -First 1

if (-not $installation) {
    Write-Host "错误: 未找到安装目录" -ForegroundColor Red
    exit 1
}

$binPath = Join-Path $installation.FullName "bin"
$adminPath = Join-Path $binPath "neo4j-admin.bat"

if (-not (Test-Path $adminPath)) {
    Write-Host "错误: 未找到neo4j-admin.bat" -ForegroundColor Red
    Write-Host "路径: $adminPath" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "数据库: $($selectedDb.Name)" -ForegroundColor Cyan
Write-Host "执行停止命令..." -ForegroundColor Yellow

# 切换到bin目录并停止
Set-Location $binPath
try {
    & .\neo4j-admin server stop
    Write-Host ""
    Write-Host "Neo4j已停止" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "错误: 停止失败" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

