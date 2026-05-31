# Makefile wrapper for PowerShell
# This script runs make with proper syntax for PowerShell
param(
    [string]$Target = "viewer"
)

$makePath = "C:\msys64\usr\bin\make.exe"
if (Test-Path $makePath) {
    & $makePath $Target
} else {
    # Try to find make in PATH
    make $Target
}
