#!/usr/bin/env pwsh
# Wrapper script to run Poetry commands in PowerShell

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

# Ensure Poetry is available
$poetryPath = (Get-Command poetry -ErrorAction SilentlyContinue)
if (-not $poetryPath) {
    Write-Error "Poetry is not installed or not in PATH"
    exit 1
}

# Run the Poetry command
poetry @Arguments
