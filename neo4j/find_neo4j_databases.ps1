# find_neo4j_databases.ps1 - 查找Neo4j Desktop管理的数据库

Write-Host "=== 查找Neo4j数据库 ===" -ForegroundColor Green

$dbPath = "$env:APPDATA\Neo4j Desktop\Application\neo4jDatabases"

if (Test-Path $dbPath) {
    Write-Host ""
    Write-Host "找到数据库目录: $dbPath" -ForegroundColor Green
    $databases = Get-ChildItem -Path $dbPath -Directory

    if ($databases.Count -eq 0) {
        Write-Host "未找到任何数据库" -ForegroundColor Yellow
        Write-Host "请先在Neo4j Desktop中创建一个数据库" -ForegroundColor Yellow
        exit
    }

    foreach ($db in $databases) {
        Write-Host ""
        Write-Host "--- 数据库: $($db.Name) ---" -ForegroundColor Yellow

        $dbJson = Join-Path $db.FullName "database.json"
        if (Test-Path $dbJson) {
            try {
                $info = Get-Content $dbJson -Raw | ConvertFrom-Json
                Write-Host "  名称: $($info.name)"
                if ($info.version) {
                    Write-Host "  版本: $($info.version)"
                }
            }
            catch {
                Write-Host "  无法读取数据库信息" -ForegroundColor Red
            }
        }

        $installations = Get-ChildItem -Path $db.FullName -Filter "installation-*" -Directory
        if ($installations.Count -eq 0) {
            Write-Host "  未找到安装目录" -ForegroundColor Red
            continue
        }

        foreach ($install in $installations) {
            Write-Host "  安装目录: $($install.Name)"
            $binPath = Join-Path $install.FullName "bin"
            if (Test-Path $binPath) {
                Write-Host "  bin路径: $binPath" -ForegroundColor Cyan

                $admin = Get-ChildItem -Path $binPath -Filter "neo4j-admin*" -ErrorAction SilentlyContinue
                if ($admin) {
                    Write-Host "  neo4j-admin: $($admin.FullName)" -ForegroundColor Green
                }
                else {
                    Write-Host "  未找到neo4j-admin" -ForegroundColor Red
                }

                $confPath = Join-Path $install.FullName "conf\neo4j.conf"
                if (Test-Path $confPath) {
                    Write-Host "  配置文件: $confPath" -ForegroundColor Cyan
                }

                $importPath = Join-Path $install.FullName "import"
                if (Test-Path $importPath) {
                    Write-Host "  import目录: $importPath" -ForegroundColor Cyan
                }
            }
        }
    }

    Write-Host ""
    Write-Host "=== 使用说明 ===" -ForegroundColor Green
    Write-Host "启动Neo4j: .\start_neo4j.ps1" -ForegroundColor Cyan
    Write-Host "停止Neo4j: .\stop_neo4j.ps1" -ForegroundColor Cyan
}
else {
    Write-Host "未找到数据库目录: $dbPath" -ForegroundColor Red
    Write-Host "请先在Neo4j Desktop中创建一个数据库" -ForegroundColor Yellow
}
