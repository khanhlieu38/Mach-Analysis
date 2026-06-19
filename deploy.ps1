param(
    [string]$Password = $env:MACH_PASSWORD
)

$ErrorActionPreference = "Stop"

# 1. Password
if (-not $Password) {
    $secure = Read-Host "Nhap mat khau MACH" -AsSecureString
    $Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    )
}

if (-not $Password) {
    Write-Error "Loi: password khong duoc de trong."
    exit 1
}

# 2. Render
Write-Host "-> Rendering Quarto site..."
quarto render
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# 3. Remove raw Quarto search index
$searchIndex = Join-Path "docs" "search.json"
if (Test-Path -LiteralPath $searchIndex) {
    Remove-Item -LiteralPath $searchIndex -Force
    Write-Host "-> Removed raw Quarto search index."
}

# 4. Encrypt — overwrite each HTML file in place
Write-Host "-> Encrypting docs/ with StatiCrypt..."
$htmlFiles = Get-ChildItem -Path docs -Filter "*.html" -Recurse

if ($htmlFiles.Count -eq 0) {
    Write-Error "Loi: khong tim thay HTML files trong docs/"
    exit 1
}

foreach ($f in $htmlFiles) {
    staticrypt $f.FullName `
        --directory $f.DirectoryName `
        --password $Password `
        --remember 7 `
        --template-title "MACH - Bao cao Nghien cuu" `
        --template-instructions "Nhap mat khau de truy cap" `
        --template-button "Truy cap"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

# 5. Push
Write-Host "-> Pushing to GitHub Pages..."
git add docs/
git commit -m "Deploy: update encrypted site $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git push

Write-Host "Done. Site live tai https://khanhlieu38.github.io/Mach-Analysis/"
