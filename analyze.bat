@echo off
:: Build and run scene analyzer
setlocal

gcc -o bin\analyze_scene97.exe src\analyze_scene97.c -Iinclude
if errorlevel 1 (
    echo Compilation failed
    exit /b 1
)

bin\analyze_scene97.exe
pause
