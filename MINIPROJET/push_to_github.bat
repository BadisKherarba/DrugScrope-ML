@echo off
setlocal enabledelayedexpansion

echo ==============================================================================
echo  DrugScope AI - Automated GitHub Publishing Script
echo  Target Repository: https://github.com/BadisKherarba/DrugScrope-ML
echo ==============================================================================
echo.

:: 1. Check if git is in PATH, if not, search standard installation paths
where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    if exist "C:\Program Files\Git\cmd\git.exe" (
        echo [INFO] Found Git at C:\Program Files\Git\cmd\git.exe
        set "PATH=C:\Program Files\Git\cmd;%PATH%"
    ) else if exist "C:\Program Files\Git\bin\git.exe" (
        echo [INFO] Found Git at C:\Program Files\Git\bin\git.exe
        set "PATH=C:\Program Files\Git\bin;%PATH%"
    ) else if exist "%LOCALAPPDATA%\Programs\Git\cmd\git.exe" (
        echo [INFO] Found Git at %LOCALAPPDATA%\Programs\Git\cmd\git.exe
        set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%PATH%"
    ) else (
        echo [ERROR] Git was not found on your system.
        echo Please install Git for Windows from: https://git-scm.com/
        pause
        exit /b 1
    )
)

:: 2. Initialize Git repo if needed
if not exist ".git" (
    echo [INFO] Initializing Git repository...
    git init
)

:: 3. Stage and commit files
echo [INFO] Staging all files...
git add .

echo [INFO] Committing changes...
git commit -m "Initial commit: DrugScope AI kinase dataset, EDA audit, outlier analysis and graphs" 2>nul || echo [INFO] Files already committed.

:: 4. Set branch and remote
git branch -M main
git remote remove origin 2>nul
git remote add origin https://github.com/BadisKherarba/DrugScrope-ML.git

:: 5. Push to GitHub
echo.
echo [INFO] Pushing code to https://github.com/BadisKherarba/DrugScrope-ML.git ...
git push -u origin main

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [INFO] Standard push failed (repository may already contain a README/file).
    echo [INFO] Attempting rebase pull and push...
    git pull origin main --rebase 2>nul
    git push -u origin main
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==============================================================================
    echo  SUCCESS: Pushed all files to https://github.com/BadisKherarba/DrugScrope-ML
    echo ==============================================================================
) else (
    echo.
    echo ==============================================================================
    echo  [!] If push failed due to authentication:
    echo      Run: git push -u origin main
    echo      and sign in via the browser or personal access token.
    echo ==============================================================================
)

pause
