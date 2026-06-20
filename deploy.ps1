param(
    [string]$Password = $env:MACH_PASSWORD,
    [switch]$BuildOnly
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $Root
$Staging = Join-Path $Root ".deploy-staging"
$Backup = Join-Path $Root ".deploy-backup"
$Docs = Join-Path $Root "docs"

function Assert-ExitCode([string]$Action) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Action failed with exit code $LASTEXITCODE"
    }
}

function Remove-SafeDirectory([string]$Path) {
    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $allowed = @(
        [System.IO.Path]::GetFullPath($Staging),
        [System.IO.Path]::GetFullPath($Backup)
    )
    if ($fullPath -notin $allowed) {
        throw "Refusing to remove unexpected directory: $fullPath"
    }
    if (Test-Path -LiteralPath $fullPath) {
        Remove-Item -LiteralPath $fullPath -Recurse -Force
    }
}

function Get-PathRelativeTo([string]$BasePath, [string]$FullPath) {
    $base = [System.IO.Path]::GetFullPath($BasePath).TrimEnd("\") + "\"
    $full = [System.IO.Path]::GetFullPath($FullPath)
    if (-not $full.StartsWith($base, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside expected base directory: $full"
    }
    return $full.Substring($base.Length)
}

foreach ($command in @("quarto", "python", "npx")) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Missing required command: $command"
    }
}
if (-not $BuildOnly -and -not (Get-Command "git" -ErrorAction SilentlyContinue)) {
    throw "Missing required command: git"
}

if (-not $Password) {
    $secure = Read-Host "Nhap mat khau MACH" -AsSecureString
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        $Password = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    }
    finally {
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}
if (-not $Password) {
    throw "Password khong duoc de trong."
}

Remove-SafeDirectory $Staging
Remove-SafeDirectory $Backup

try {
    Write-Host "-> Rendering Quarto site into staging..."
    quarto render --output-dir .deploy-staging
    Assert-ExitCode "Quarto render"

    $searchIndex = Join-Path $Staging "search.json"
    if (Test-Path -LiteralPath $searchIndex) {
        Remove-Item -LiteralPath $searchIndex -Force
    }

    python scripts/validate_site.py raw $Staging --require-site-layout
    Assert-ExitCode "Raw site validation"

    $htmlFiles = @(Get-ChildItem -LiteralPath $Staging -Filter "*.html" -Recurse -File)
    $expectedPaths = @(
        $htmlFiles | ForEach-Object {
            Get-PathRelativeTo $Staging $_.FullName
        } | Sort-Object
    )

    Write-Host "-> Encrypting $($htmlFiles.Count) HTML files in place..."
    foreach ($file in $htmlFiles) {
        npx --no-install staticrypt $file.FullName `
            --directory $file.DirectoryName `
            --password $Password `
            --remember 7 `
            --template-title "MACH - Bao cao Nghien cuu" `
            --template-instructions "Nhap mat khau de truy cap" `
            --template-button "Truy cap"
        Assert-ExitCode "StatiCrypt encryption for $($file.FullName)"
    }

    $actualPaths = @(
        Get-ChildItem -LiteralPath $Staging -Filter "*.html" -Recurse -File |
            ForEach-Object { Get-PathRelativeTo $Staging $_.FullName } |
            Sort-Object
    )
    if (Compare-Object $expectedPaths $actualPaths) {
        throw "Encrypted HTML paths do not match raw staging paths."
    }

    python scripts/validate_site.py encrypted $Staging --require-site-layout
    Assert-ExitCode "Encrypted site validation"

    $hadDocs = Test-Path -LiteralPath $Docs
    if ($hadDocs) {
        Move-Item -LiteralPath $Docs -Destination $Backup
    }
    try {
        Move-Item -LiteralPath $Staging -Destination $Docs
    }
    catch {
        if ($hadDocs -and (Test-Path -LiteralPath $Backup)) {
            Move-Item -LiteralPath $Backup -Destination $Docs
        }
        throw
    }
    Remove-SafeDirectory $Backup
}
finally {
    Remove-SafeDirectory $Staging
}

if ($BuildOnly) {
    Write-Host "Done. Encrypted docs/ built and validated; Git was not changed."
    exit 0
}

Write-Host "-> Publishing encrypted docs/..."
git add docs/
Assert-ExitCode "git add"
git diff --cached --quiet -- docs/
$diffCode = $LASTEXITCODE
if ($diffCode -eq 0) {
    Write-Host "No encrypted output changes; skipping commit and push."
    exit 0
}
if ($diffCode -ne 1) {
    throw "git diff failed with exit code $diffCode"
}

git commit -m "Deploy: update encrypted site $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
Assert-ExitCode "git commit"
git push
Assert-ExitCode "git push"

Write-Host "Done. Site live tai https://khanhlieu38.github.io/Mach-Analysis/"
