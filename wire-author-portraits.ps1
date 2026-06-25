<#
Wires the current root-level author portrait PNGs into Astro's public asset tree.

Run from anywhere inside the Bookstacks repo:

  pwsh .\tools\wire-author-portraits.ps1

By default this copies the files, leaving the root originals in place. Add -Move
to move them instead.
#>
[CmdletBinding()]
param(
    [switch]$Move
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Find-BookstacksRoot {
    $dir = (Get-Location).Path

    while ($true) {
        $hasAstroConfig = Test-Path -LiteralPath (Join-Path $dir 'astro.config.mjs')
        $hasSrc = Test-Path -LiteralPath (Join-Path $dir 'src')

        if ($hasAstroConfig -and $hasSrc) {
            return $dir
        }

        $parent = Split-Path -Parent $dir
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $dir) {
            throw 'Could not find the Bookstacks repo root. Run this from inside the repo.'
        }

        $dir = $parent
    }
}

$repoRoot = Find-BookstacksRoot
$targetDir = Join-Path $repoRoot 'public\img\authors'
$slugs = @('austen-jane', 'kafka-franz', 'tolstoy-leo')

New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

foreach ($slug in $slugs) {
    $source = Get-ChildItem -LiteralPath $repoRoot -File |
        Where-Object { $_.BaseName -ieq $slug -and $_.Extension -ieq '.png' } |
        Select-Object -First 1

    if ($null -eq $source) {
        throw "Missing root-level source file: $slug.png"
    }

    $target = Join-Path $targetDir "$slug.png"

    if ($Move) {
        Move-Item -LiteralPath $source.FullName -Destination $target -Force
        Write-Host "Moved  $($source.Name) -> public/img/authors/$slug.png"
    }
    else {
        Copy-Item -LiteralPath $source.FullName -Destination $target -Force
        Write-Host "Copied $($source.Name) -> public/img/authors/$slug.png"
    }
}

Write-Host ''
Write-Host 'Expected public URLs after build/dev server starts:'
foreach ($slug in $slugs) {
    Write-Host "  /img/authors/$slug.png"
}
