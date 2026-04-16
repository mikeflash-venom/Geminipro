# start_neo4j.ps1 - 启动Neo4j数据库

param(
    [string]$DatabaseName = "graphrag2.7.0"
)

Write-Host "=== 启动Neo4j数据库 ===" -ForegroundColor Green

# 查找数据库目录
$dbPath = "$env:APPDATA\Neo4j Desktop\Application\neo4jDatabases"

if (-not (Test-Path $dbPath)) {
    Write-Host "错误: 未找到Neo4j数据库目录" -ForegroundColor Red
    Write-Host "路径: $dbPath" -ForegroundColor Yellow
    Write-Host "请先在Neo4j Desktop中创建一个数据库" -ForegroundColor Yellow
    exit 1
}

$databases = Get-ChildItem -Path $dbPath -Directory

if ($databases.Count -eq 0) {
    Write-Host "错误: 未找到任何数据库" -ForegroundColor Red
    Write-Host "请先在Neo4j Desktop中创建一个数据库" -ForegroundColor Yellow
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
    # 显示可用数据库
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
                $dbVersion = if ($info.version) { " (版本: $($info.version))" } else { "" }
                Write-Host "  $i. $dbName$dbVersion"
                $dbList += @{Index=$i-1; Db=$db; Info=$info; Name=$dbName}
                $i++
            } catch {
                Write-Host "  $i. $($db.Name) (无法读取信息)"
                $dbList += @{Index=$i-1; Db=$db; Info=$null; Name=$db.Name}
                $i++
            }
        }
    }
    
    if ($dbList.Count -eq 0) {
        Write-Host "错误: 没有可用的数据库" -ForegroundColor Red
        exit 1
    }
    
    if ($dbList.Count -eq 1) {
        $selectedDb = $dbList[0].Db
        Write-Host ""
        Write-Host "自动选择: $($dbList[0].Name)" -ForegroundColor Green
    } else {
        Write-Host ""
        $choice = Read-Host "请选择数据库 (1-$($dbList.Count))"
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
    }
}

# 查找安装目录
$installation = Get-ChildItem -Path $selectedDb.FullName -Filter "installation-*" -Directory | Select-Object -First 1

if (-not $installation) {
    Write-Host "错误: 未找到安装目录" -ForegroundColor Red
    Write-Host "数据库路径: $($selectedDb.FullName)" -ForegroundColor Yellow
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
Write-Host "=== 启动信息 ===" -ForegroundColor Green
Write-Host "数据库: $($selectedDb.Name)" -ForegroundColor Cyan
Write-Host "安装目录: $($installation.FullName)" -ForegroundColor Cyan
Write-Host "bin目录: $binPath" -ForegroundColor Cyan

# 切换到bin目录并启动
Set-Location $binPath
Write-Host ""
Write-Host "执行启动命令..." -ForegroundColor Yellow
Write-Host "命令: .\neo4j-admin server start" -ForegroundColor Gray

try {
    & .\neo4j-admin server start
    
    Write-Host ""
    Write-Host "=== Neo4j启动成功！ ===" -ForegroundColor Green
    Write-Host "访问地址: http://localhost:7474" -ForegroundColor Cyan
    Write-Host "Bolt地址: bolt://localhost:7687" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "默认用户名: neo4j" -ForegroundColor Yellow
    Write-Host "默认密码: neo4j (首次登录需要修改)" -ForegroundColor Yellow
} catch {
    Write-Host ""
    Write-Host "错误: 启动失败" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

