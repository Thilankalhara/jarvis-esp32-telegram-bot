# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 2.1.x   | :white_check_mark: |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x: |

## Reporting a Vulnerability

If you discover a security issue in this project, please report it responsibly.

- **Email:** thilankalhara8@gmail.com
- **GitHub:** https://github.com/Thilankalhara
- **Preferred channel:** email first, then GitHub issues if email is unavailable.

Please include:
- A clear description of the issue
- Steps to reproduce the problem
- Any affected files, config values, or environments
- Whether the issue impacts the Telegram bot, installer, or ESP32 firmware

We aim to acknowledge reports within 48 hours and respond with a remediation plan within 5 business days.

## Security Best Practices

- Do not store secrets in source control. Keep `.env` out of Git.
- Use strong passwords for `BOT_PASSWORD` and `WINDOWS_PC_PASSWORD`.
- Restrict `ALLOWED_TELEGRAM_USERS` to only trusted Telegram accounts.
- Keep your ESP32 firmware and PC agent dependencies up to date.

## Security Controls in J.A.R.V.I.S.

- Password-protected Telegram login via `/login <password>`.
- Session invalidation when `BOT_PASSWORD` changes.
- Emergency stop in the GUI that immediately terminates the bot.
- Installer detects locked `JARVIS_Control_Center.exe` before extraction.

---

© 2026 Thilankalhara. All rights reserved.
