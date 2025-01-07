# Install-ContextMenu.ps1

# Script metadata
$ErrorActionPreference = "Stop"
$AppName = "FileCon"
$AppDescription = "File Concatenator"
$IconFile = "file_concatenator.ico"

try {
    # Verify admin privileges
    if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
        throw "This script requires administrative privileges. Please run as Administrator."
    }

    # Get script and application paths
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    $appPath = Join-Path $scriptPath "file_concatenator.py"
    $iconPath = Join-Path $scriptPath $IconFile

    # Verify python installation and get full path
    $pythonPath = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Path
    if (-not $pythonPath) {
        throw "Python (pythonw.exe) not found in PATH. Please ensure Python is installed and in your system PATH."
    }

    # Verify required files exist
    if (-not (Test-Path $appPath)) {
        throw "Application file not found at: $appPath"
    }
    if (-not (Test-Path $iconPath)) {
        Write-Warning "Icon file not found at: $iconPath. Will use default Python icon."
        $iconPath = $pythonPath
    }

    # Registry entries configuration
    $fileContext = @{
        Path = "Registry::HKEY_CLASSES_ROOT\*\shell\$AppName"
        Command = """$pythonPath"" ""$appPath"" ""%V"" ""%1"""  # Added %V for directory context
        Description = "Open with $AppName"
    }

    $folderContext = @{
        Path = "Registry::HKEY_CLASSES_ROOT\Directory\shell\$AppName"
        Command = """$pythonPath"" ""$appPath"" ""%V"""  # Use %V for directory path
        Description = "Open in $AppName"
    }

    $backgroundContext = @{
        Path = "Registry::HKEY_CLASSES_ROOT\Directory\Background\shell\$AppName"
        Command = """$pythonPath"" ""$appPath"" ""%V"""  # Use %V for current directory
        Description = "Open in $AppName"
    }

    # Function to remove existing context menu entries
    function Remove-ExistingContextMenu {
        $paths = @($fileContext.Path, $folderContext.Path, $backgroundContext.Path)
        foreach ($path in $paths) {
            if (Test-Path $path) {
                Write-Host "Removing existing context menu entry: $path"
                Remove-Item -Path $path -Recurse -Force
            }
        }
    }

    # Function to create context menu entry
    function Add-ContextMenu {
        param (
            [hashtable]$Context
        )
        
        # Create main registry key
        Write-Host "Creating registry key: $($Context.Path)"
        New-Item -Path $Context.Path -Force | Out-Null
        Set-ItemProperty -Path $Context.Path -Name "(default)" -Value $Context.Description
        Set-ItemProperty -Path $Context.Path -Name "Icon" -Value $iconPath
        
        # Create command subkey
        $commandPath = Join-Path $Context.Path "command"
        New-Item -Path $commandPath -Force | Out-Null
        Set-ItemProperty -Path $commandPath -Name "(default)" -Value $Context.Command
    }

    # Main installation process
    Write-Host "`nInstalling $AppDescription context menu entries..."
    Write-Host "Application path: $appPath"
    Write-Host "Python interpreter: $pythonPath"
    Write-Host "Icon path: $iconPath`n"

    # Remove existing entries
    Remove-ExistingContextMenu

    # Add new context menu entries
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