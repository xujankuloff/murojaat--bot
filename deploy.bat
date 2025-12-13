@echo off
REM --- GitHub repository tayyorlash ---
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/xujankuloff/murojaat-bot.git
git push -u origin main

REM --- Render.com deploy bo‘yicha eslatma ---
echo.
echo -------------------------------
echo Tayyor! Endi Render.com ga kiring:
echo 1. New → Web Service
echo 2. GitHub repository ni tanlang: murojaat-bot
echo 3. Environment: Python 3
echo 4. Build Command: pip install -r requirements.txt
echo 5. Start Command: python bot.py
echo 6. Environment Variables qo‘shing: BOT_TOKEN = "SIZNING_BOT_TOKEN"
echo 7. Deploy tugmasini bosing
echo -------------------------------
pause
