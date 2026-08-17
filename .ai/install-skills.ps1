# SPDX-License-Identifier: MIT
<#
.SYNOPSIS
    Install skills from .ai/skills/ into user-level agent directories.

.DESCRIPTION
    Thin wrapper around .ai/install-skills.py so Windows users do not need to
    remember the interpreter or the script path. Every argument is passed
    through unchanged.

.EXAMPLE
    .\.ai\install-skills.ps1 --list

.EXAMPLE
    .\.ai\install-skills.ps1 --all --platform claude,cursor

.EXAMPLE
    .\.ai\install-skills.ps1 --skill clean-code --platform all --copy
#>
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PassThruArgs
)

$ErrorActionPreference = 'Stop'

$script = Join-Path $PSScriptRoot 'install-skills.py'
if (-not (Test-Path $script)) {
    throw "Cannot find $script"
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $python) {
    throw 'Python 3 is required but was not found on PATH.'
}

if (-not $PassThruArgs -or $PassThruArgs.Count -eq 0) {
    $PassThruArgs = @('--list')
}

& $python.Source $script @PassThruArgs
exit $LASTEXITCODE
