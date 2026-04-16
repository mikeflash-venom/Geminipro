$paths = @(
    "$env:APPDATA\Neo4j Desktop\Application\neo4jDatabases",
    "$env:APPDATA\neo4j-desktop\Application\neo4jDatabases"
)

foreach ($p in $paths) {
    if (Test-Path $p) {
        Write-Host "Found database directory: $p" -ForegroundColor Green
        $dbs = Get-ChildItem -Path $p -Directory
        if ($dbs) {
            foreach ($db in $dbs) {
                $dbJson = Join-Path $db.FullName "database.json"
                if (Test-Path $dbJson) {
                    try {
                        $info = Get-Content $dbJson -Raw | ConvertFrom-Json
                        Write-Host "  Database: $($info.name)" -ForegroundColor Cyan
                        Write-Host "    ID: $($db.Name)" -ForegroundColor Gray
                    } catch {}
                }
            }
        } else {
            Write-Host "  No databases found" -ForegroundColor Yellow
        }
    }
}




