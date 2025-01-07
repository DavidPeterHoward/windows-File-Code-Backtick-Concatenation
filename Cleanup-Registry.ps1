# Cleanup-Registry.ps1

$ErrorActionPreference = "Stop"

try {
    if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
        throw "This script requires administrative privileges. Please run as Administrator."
    }

    # List of possible old registry keys to remove
    $oldKeys = @(
        "Registry::HKEY_CLASSES_ROOT\*\shell\FileCon",
        "Registry::HKEY_CLASSES_ROOT\Directory\shell\FileCon",
        "Registry::HKEY_CLASSES_ROOT\Directory\Background\shell\FileCon",
        "Registry::HKEY_CLASSES_ROOT\*\shell\FileConcatenator",
        "Registry::HKEY_CLASSES_ROOT\Directory\shell\FileConcatenator",
        "Registry::HKEY_CLASSES_ROOT\Directory\Background\shell\FileConcatenator",
        "Registry::HKEY_CLASSES_ROOT\*\shell\File Concatenator",
        "Registry::HKEY_CLASSES_ROOT\Directory\shell\File Concatenator",
        "Registry::HKEY_CLASSES_ROOT\Directory\Background\shell\File Concatenator"
    )

    $removedCount = 0
    foreach ($key in $oldKeys) {
        if (Test-Path $key) {
            Write-Host "Removing old registry key: $key"
            Remove-Item -Path $key -Recurse -Force
            $removedCount++
        }
    }

    # Clean up settings
    $settingsKeys = @(
        "HKCU:\Software\FileConcatenator"
    )

    foreach ($key in $settingsKeys) {
        if (Test-Path $key) {
            Write-Host "Removing settings key: $key"
            Remove-Item -Path $key -Recurse -Force
            $removedCount++
        }
    }

    if ($removedCount -gt 0) {
        Write-Host "`nCleanup successful!" -ForegroundColor Green
        Write-Host "Removed $removedCount registry entries."
    } else {
        Write-Host "`nNo old registry entries found." -ForegroundColor Yellow
    }

} catch {
    Write-Host "`nCleanup failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}