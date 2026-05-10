# Extract scene data from FD2.EXE using PowerShell
$exePath = "D:\workspace\fd2ida\FD2\FD2.EXE"
$sceneTableOffset = 0x627D8
$maxScenes = 106

$exeData = [System.IO.File]::ReadAllBytes($exePath)

# Read pointer table
$pointers = @()
for ($i = 0; $i -lt $maxScenes; $i++) {
    $offset = $sceneTableOffset + ($i * 4)
    $ptr = [BitConverter]::ToUInt32($exeData, $offset)
    $pointers += $ptr
}

Write-Host "Extracted $($pointers.Count) scene pointers from 0x$($sceneTableOffset.ToString('X'))"

# Extract scenes of interest
$scenesOfInterest = @(99, 100, 101, 102, 103, 104, 105, 90, 91, 92, 93, 94, 95, 96, 97, 98, 0, 1, 2, 5)

foreach ($idx in $scenesOfInterest) {
    $ptr = $pointers[$idx]
    if ($ptr -eq 0) {
        Write-Host "Scene $idx`: NULL pointer"
        continue
    }
    
    # Parse scene data
    $sceneData = New-Object System.Collections.ArrayList
    $pos = $ptr
    
    # Entry count
    $entryCount = $exeData[$pos]
    $sceneData.Add($exeData[$pos]) | Out-Null
    $pos++
    
    # Parse entries
    for ($e = 0; $e -lt $entryCount; $e++) {
        $cmdType = $exeData[$pos]
        $paramCount = $exeData[$pos + 1]
        $sceneData.Add($cmdType) | Out-Null
        $sceneData.Add($paramCount) | Out-Null
        $pos += 2
        
        for ($p = 0; $p -lt $paramCount; $p++) {
            $sceneData.Add($exeData[$pos]) | Out-Null
            $sceneData.Add($exeData[$pos + 1]) | Out-Null
            $pos += 2
        }
    }
    
    $hexStr = ($sceneData | ForEach-Object { $_.ToString("X2") }) -join " "
    Write-Host "Scene $idx`: $($sceneData.Count) bytes at 0x$($ptr.ToString('X')), entries=$entryCount"
    Write-Host "  Hex: $hexStr"
}
