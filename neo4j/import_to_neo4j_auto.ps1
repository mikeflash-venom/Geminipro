param(
    [string]$DatabaseName = "graphrag2.7.0",
    [string]$DatabaseId = "1f25b0f9-3f20-46c7-bed2-0d7a792fb180",
    [string]$SourceDir = "E:\graphrag\graphrag-2.7.0\test_0114-2\output\neo4j_import"
)

Write-Host "=== Auto Import GraphRAG Data to Neo4j ===" -ForegroundColor Green
Write-Host "Database: $DatabaseName" -ForegroundColor Cyan
Write-Host "Database ID: $DatabaseId" -ForegroundColor Cyan
Write-Host ""

$dbPath = "$env:APPDATA\Neo4j Desktop\Application\neo4jDatabases\database-$DatabaseId"

if (-not (Test-Path $dbPath)) {
    Write-Host "Database directory not found, searching..." -ForegroundColor Yellow
    $allDbs = Get-ChildItem -Path "$env:APPDATA\Neo4j Desktop\Application\neo4jDatabases" -Directory -ErrorAction SilentlyContinue
    $found = $false
    
    if ($allDbs) {
        foreach ($db in $allDbs) {
            $dbJson = Join-Path $db.FullName "database.json"
            if (Test-Path $dbJson) {
                try {
                    $info = Get-Content $dbJson -Raw | ConvertFrom-Json
                    if ($info.name -eq $DatabaseName -or $db.Name -like "*$DatabaseId*") {
                        $dbPath = $db.FullName
                        $found = $true
                        Write-Host "Found database: $($db.FullName)" -ForegroundColor Green
                        break
                    }
                } catch {
                }
            }
        }
    }
    
    if (-not $found) {
        Write-Host "Error: Database '$DatabaseName' not found" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Found database directory: $dbPath" -ForegroundColor Green
}

$installation = Get-ChildItem -Path $dbPath -Filter "installation-*" -Directory | Select-Object -First 1

if (-not $installation) {
    Write-Host "Error: Installation directory not found" -ForegroundColor Red
    exit 1
}

$importPath = Join-Path $installation.FullName "import"

if (-not (Test-Path $importPath)) {
    Write-Host "Creating import directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $importPath -Force | Out-Null
    Write-Host "Import directory created" -ForegroundColor Green
}

Write-Host ""
Write-Host "Import目录: $importPath" -ForegroundColor Cyan

$nodesFile = Join-Path $SourceDir "nodes.csv"
$relsFile = Join-Path $SourceDir "relationships.csv"

if (-not (Test-Path $nodesFile)) {
    Write-Host "Error: nodes.csv not found" -ForegroundColor Red
    Write-Host "Path: $nodesFile" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $relsFile)) {
    Write-Host "Error: relationships.csv not found" -ForegroundColor Red
    Write-Host "Path: $relsFile" -ForegroundColor Yellow
    exit 1
}

$nodesSize = (Get-Item $nodesFile).Length / 1KB
$relsSize = (Get-Item $relsFile).Length / 1KB
Write-Host ""
Write-Host "Source file info:" -ForegroundColor Cyan
Write-Host "  nodes.csv: $([math]::Round($nodesSize, 2)) KB" -ForegroundColor Gray
Write-Host "  relationships.csv: $([math]::Round($relsSize, 2)) KB" -ForegroundColor Gray

Write-Host ""
Write-Host "Copying files..." -ForegroundColor Yellow

Copy-Item $nodesFile -Destination $importPath -Force
Write-Host "  [OK] nodes.csv copied" -ForegroundColor Green

Copy-Item $relsFile -Destination $importPath -Force
Write-Host "  [OK] relationships.csv copied" -ForegroundColor Green

Write-Host ""
Write-Host "Files copied successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "1. Start database '$DatabaseName' in Neo4j Desktop" -ForegroundColor Yellow
Write-Host "2. Click 'Open' to open Neo4j Browser" -ForegroundColor Yellow
Write-Host "3. Execute import statements from import_to_neo4j.cypher" -ForegroundColor Yellow
Write-Host ""

