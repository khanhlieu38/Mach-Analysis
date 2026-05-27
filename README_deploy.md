# Deploy Guide — MẠCH Analysis

## Lần đầu tiên

1. Install dependencies:
   ```bash
   npm install -g staticrypt
   ```

2. Set password (một lần, không cần lại):

   **Windows PowerShell** — thêm vào `$PROFILE`:
   ```powershell
   $env:MACH_PASSWORD = "your-password-here"
   ```

   **Git Bash / macOS** — thêm vào `~/.bashrc` / `~/.zshrc`:
   ```bash
   export MACH_PASSWORD="your-password-here"
   ```

3. Chạy deploy:

   **Windows PowerShell:**
   ```powershell
   .\deploy.ps1
   ```

   **Git Bash / macOS:**
   ```bash
   bash deploy.sh
   ```

## Mỗi lần update content

```powershell
.\deploy.ps1        # Windows
```
```bash
bash deploy.sh      # Git Bash / macOS
```

Script tự động: render → encrypt → push.

Nếu đã update data (CSV), xóa cache trước để tránh stale charts:

```powershell
Remove-Item -Recurse -Force _freeze/; .\deploy.ps1    # Windows
```
```bash
rm -rf _freeze/ && bash deploy.sh                      # Git Bash
```

## Lưu ý bảo mật

- **KHÔNG share password qua email.** Chỉ Zalo/Slack riêng tư.
- Password không được lưu trong bất kỳ file nào trong repo.
- `.staticrypt.json` (salt file) **nên commit** — chứa encryption salt, giúp git diff clean. Không chứa password.
- Nếu cần đổi password: chạy lại deploy script với password mới — toàn bộ HTML sẽ được re-encrypt.

## Test local

Sau khi chạy deploy script:

```powershell
Start-Process docs\index.html    # Windows
```
```bash
open docs/index.html             # macOS
start docs/index.html            # Windows Git Bash
```

Phải thấy password prompt. Nhập đúng password → vào được report.
