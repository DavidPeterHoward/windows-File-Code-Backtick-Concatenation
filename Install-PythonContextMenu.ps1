# Install-PythonContextMenu.ps1

$ErrorActionPreference = "Stop"
$AppName = "FileCon"
$AppDescription = "File Concatenator (Python)"
$IconFile = "file_concatenator.ico"

try {
    if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
        throw "This script requires administrative privileges. Please run as Administrator."
    }

    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    $appPath = Join-Path $scriptPath "file_concatenator.py"
    $iconPath = Join-Path $scriptPath $IconFile

    $pythonPath = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Path
    if (-not $pythonPath) {
        throw "Python (pythonw.exe) not found in PATH. Please ensure Python is installed and in your system PATH."
    }

    if (-not (Test-Path $appPath)) {
        throw "Application file not found at: $appPath"
    }
    if (-not (Test-Path $iconPath)) {
        Write-Warning "Icon file not found at: $iconPath. Will use default Python icon."
        $iconPath = $pythonPath
    }

    $fileContext = @{
        Path = "Registry::HKEY_CLASSES_ROOT\*\shell\$AppName"
        Command = """$pythonPath"" ""$appPath"" ""%V"" ""%1"""
        Description = "Open with $AppName"
    }

    $folderContext = @{
        Path = "Registry::HKEY_CLASSES_ROOT\Directory\shell\$AppName"
        Command = """$pythonPath"" ""$appPath"" ""%V"""
        Description = "Open in $AppName"
    }

    $backgroundContext = @{
        Path = "Registry::HKEY_CLASSES_ROOT\Directory\Background\shell\$AppName"
        Command = """$pythonPath"" ""$appPath"" ""%V"""
        Description = "Open in $AppName"
    }

    function Remove-ExistingContextMenu {
        $paths = @($fileContext.Path, $folderContext.Path, $backgroundContext.Path)
        foreach ($path in $paths) {
            if (Test-Path $path) {
                Write-Host "Removing existing context menu entry: $path"
                Remove-Item -Path $path -Recurse -Force
            }
        }
    }

    function Add-ContextMenu {
        param (
            [hashtable]$Context
        )
        Write-Host "Creating registry key: $($Context.Path)"
        New-Item -Path $Context.Path -Force | Out-Null
        Set-ItemProperty -Path $Context.Path -Name "(default)" -Value $Context.Description
        Set-ItemProperty -Path $Context.Path -Name "Icon" -Value $iconPath
        
        $commandPath = Join-Path $Context.Path "command"
        New-Item -Path $commandPath -Force | Out-Null
        Set-ItemProperty -Path $commandPath -Name "(default)" -Value $Context.Command
    }

    Write-Host "`nInstalling $AppDescription context menu entries..."
    Write-Host "Application path: $appPath"
    Write-Host "Python interpreter: $pythonPath"
    Write-Host "Icon path: $iconPath`n"

    Remove-ExistingContextMenu

    Add-ContextMenu -Context $fileContext
    Add-ContextMenu -Context $folderContext
    Add-ContextMenu -Context $backgroundContext

    Write-Host "`nInstallation successful!" -ForegroundColor Green
    Write-Host "Context menu entries have been added for:"
    Write-Host "- Files: '$($fileContext.Description)'"
    Write-Host "- Folders: '$($folderContext.Description)'"
    Write-Host "- Background: '$($backgroundContext.Description)'"

} catch {
    Write-Host "`nInstallation failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}