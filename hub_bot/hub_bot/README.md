# Панель ссылок через Telegram-бота

1. Создайте бота у @BotFather, получите токен.
2. Узнайте свой Telegram ID у @userinfobot.
3. Запуск:
   pip install -r requirements.txt
   BOT_TOKEN=... ADMIN_ID=... python bot.py
4. Сервер отдаёт мини-приложение на `/` и ссылки на `/api/links`.
   Нужен публичный HTTPS-адрес (хостинг, Render, Railway, VPS + домен).
5. Если мини-приложение открывается с этого же сервера (адрес `/`), ничего менять не нужно.
   Если хостите HTML отдельно — впишите `const API_URL = "https://ваш-домен"` в channel_hub.html.
6. Адрес сервера укажите в BotFather: /newapp или /setmenubutton.
7. В боте: /panel → выберите кнопку → отправьте ссылку YouTube.
