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
        Command = """$pythonPath"" ""$appPath"" ""%1"""
        Description = "Extract with $AppName"
    }

    $folderContext = @{
        Path = "Registry::HKEY_CLASSES_ROOT\Directory\shell\$AppName"
        Command = """$pythonPath"" ""$appPath"" ""%1"""
        Description = "Open in $AppName"
    }

    # Function to remove existing context menu entries
    function Remove-ExistingContextMenu {
        $paths = @($fileContext.Path, $folderContext.Path)
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

    # Function to verify installation
    function Test-Installation {
        $success = $true
        $paths = @($fileContext.Path, $folderContext.Path)
        
        foreach ($path in $paths) {
            if (-not (Test-Path $path)) {
                $success = $false
                Write-Warning "Failed to verify registry key: $path"
            } else {
                $commandPath = Join-Path $path "command"
                if (-not (Test-Path $commandPath)) {
                    $success = $false
                    Write-Warning "Failed to verify command key: $commandPath"
                }
            }
        }
        
        return $success
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

    # Verify installation
    $success = Test-Installation

    if ($success) {
        Write-Host "`nInstallation successful!" -ForegroundColor Green
        Write-Host "You can now right-click on files or folders to:"
        Write-Host "- Extract content from files using '$($fileContext.Description)'"
        Write-Host "- Open folders in $AppName using '$($folderContext.Description)'"
    } else {
        throw "Installation completed with verification errors."
    }

} catch {
    Write-Host "`nInstallation failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Optional: Add registry entries cleanup on script completion
if ($success) {
    Write-Host "`nTo uninstall these context menu entries, run this script with the -Uninstall parameter"
    Write-Host "or delete the following registry keys manually:"
    Write-Host "- $($fileContext.Path)"
    Write-Host "- $($folderContext.Path)"
}