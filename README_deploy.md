# Deploy Guide — MẠCH Analysis

## Lần đầu tiên

1. Install dependencies:
   ```bash
   npm install -g staticrypt
   ```

2. Set password (một lần, không cần lại):
   ```bash
   export MACH_PASSWORD="your-password-here"
   ```
   Hoặc thêm vào `~/.bashrc` / `~/.zshrc` để không phải set lại mỗi session.

3. Chạy deploy:
   ```bash
   bash deploy.sh
   ```

## Mỗi lần update content

```bash
bash deploy.sh
```

Script tự động: render → encrypt → push.

Nếu đã update data (CSV), xóa cache trước để tránh stale charts:

```bash
rm -rf _freeze/ && bash deploy.sh
```

## Lưu ý bảo mật

- **KHÔNG share password qua email.** Chỉ Zalo/Slack riêng tư.
- Password không được lưu trong bất kỳ file nào trong repo.
- `.staticrypt.json` (salt file) **nên commit** — chứa encryption salt, giúp git diff clean. Không chứa password.
- Nếu cần đổi password: chạy lại `deploy.sh` với password mới — toàn bộ HTML sẽ được re-encrypt.

## Test local

Sau khi chạy `deploy.sh`:

```bash
start docs/index.html     # Windows Git Bash
open docs/index.html      # macOS
```

Phải thấy password prompt. Nhập đúng password → vào được report.
