$nodesFile = "E:\graphrag\graphrag-2.7.0\test_0114-2\output\neo4j_import\nodes.csv"
$relsFile = "E:\graphrag\graphrag-2.7.0\test_0114-2\output\neo4j_import\relationships.csv"

Write-Host "=== Checking Nodes CSV ===" -ForegroundColor Green
if (Test-Path $nodesFile) {
    $header = Get-Content $nodesFile -Head 1
    Write-Host "Header: $header"
    Write-Host ""
    $data = Get-Content $nodesFile -Head 2 | Select-Object -Last 1
    Write-Host "First data row (first 200 chars):"
    Write-Host $data.Substring(0, [Math]::Min(200, $data.Length))
} else {
    Write-Host "File not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Checking Relationships CSV ===" -ForegroundColor Green
if (Test-Path $relsFile) {
    $header = Get-Content $relsFile -Head 1
    Write-Host "Header: $header"
    Write-Host ""
    $data = Get-Content $relsFile -Head 2 | Select-Object -Last 1
    Write-Host "First data row (first 300 chars):"
    Write-Host $data.Substring(0, [Math]::Min(300, $data.Length))
    
    Write-Host ""
    Write-Host "Checking :START_ID and :END_ID format:" -ForegroundColor Yellow
    $cols = $header -split ','
    $startIdx = -1
    $endIdx = -1
    for ($i = 0; $i -lt $cols.Length; $i++) {
        if ($cols[$i] -eq ':START_ID') { $startIdx = $i }
        if ($cols[$i] -eq ':END_ID') { $endIdx = $i }
    }
    
    if ($startIdx -ge 0 -and $endIdx -ge 0) {
        $dataCols = $data -split ','
        if ($dataCols.Length -gt $startIdx -and $dataCols.Length -gt $endIdx) {
            $startId = $dataCols[$startIdx]
            $endId = $dataCols[$endIdx]
            Write-Host "  :START_ID value: $startId" -ForegroundColor Cyan
            Write-Host "  :END_ID value: $endId" -ForegroundColor Cyan
            
            $isUuid = ($startId.Length -eq 36 -and $startId -match '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
            if ($isUuid) {
                Write-Host "  Format: UUID (correct)" -ForegroundColor Green
            } else {
                Write-Host "  Format: Text (incorrect - should be UUID)" -ForegroundColor Red
            }
        }
    }
} else {
    Write-Host "File not found" -ForegroundColor Red
}




