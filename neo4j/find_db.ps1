$dbPath = "$env:APPDATA\Neo4j Desktop\Application\neo4jDatabases"
if (Test-Path $dbPath) {
    Get-ChildItem -Path $dbPath -Directory | ForEach-Object {
        $dbJson = Join-Path $_.FullName "database.json"
        if (Test-Path $dbJson) {
            try {
                $info = Get-Content $dbJson -Raw | ConvertFrom-Json
                Write-Host "Database: $($info.name)"
                Write-Host "  ID: $($_.Name)"
                Write-Host "  Path: $($_.FullName)"
                Write-Host ""
            } catch {}
        }
    }
} else {
    Write-Host "Database directory not found"
}




