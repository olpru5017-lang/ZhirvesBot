# 🚀 Быстрый деплой Discord Music Bot

Выбери один из вариантов - всё автоматически установится, включая FFmpeg!

---

## Вариант 1: Railway (Рекомендуется) ⭐

**Самый простой способ - 2 минуты!**

1. Зарегистрируйся на [Railway.app](https://railway.app)
2. Нажми "New Project" → "Deploy from GitHub repo"
3. Выбери этот репозиторий
4. Добавь переменную окружения:
   - `DISCORD_TOKEN` = твой токен бота
5. Railway автоматически:
   - Установит FFmpeg
   - Установит все зависимости
   - Запустит бота
6. Готово! ✅

**Бесплатный план:** 500 часов в месяц (достаточно для круглосуточной работы)

---

## Вариант 2: Render.com

1. Зарегистрируйся на [Render.com](https://render.com)
2. Нажми "New" → "Blueprint"
3. Подключи GitHub репозиторий
4. Render автоматически найдет `render.yaml`
5. Добавь переменную `DISCORD_TOKEN` в настройках
6. Нажми "Apply"
7. Готово! ✅

**Бесплатный план:** Неограниченно, но засыпает после 15 минут бездействия

---

## Вариант 3: Docker (Любой хостинг)

Если у тебя есть VPS или любой хостинг с Docker:

```bash
# 1. Клонируй репозиторий
git clone <твой-репозиторий>
cd discord-music-bot

# 2. Создай .env файл
echo "DISCORD_TOKEN=твой_токен_здесь" > .env

# 3. Запусти одной командой
docker-compose up -d
```

Готово! Бот работает в фоне. FFmpeg установится автоматически.

**Команды управления:**
```bash
docker-compose logs -f        # Посмотреть логи
docker-compose restart        # Перезапустить
docker-compose down           # Остановить
```

---

## Вариант 4: Heroku

1. Установи [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Выполни команды:

```bash
# Логин в Heroku
heroku login

# Создай приложение
heroku create твое-имя-бота

# Добавь buildpack для FFmpeg
heroku buildpacks:add --index 1 https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git

# Добавь токен
heroku config:set DISCORD_TOKEN=твой_токен_здесь

# Задеплой
git push heroku main
```

Готово! ✅

---

## Получение Discord токена

1. Иди на [Discord Developer Portal](https://discord.com/developers/applications)
2. Создай "New Application"
3. Перейди в "Bot" → "Add Bot"
4. Нажми "Reset Token" и скопируй токен
5. Включи "Message Content Intent" в настройках бота
6. Пригласи бота на сервер через OAuth2 URL Generator:
   - Scope: `bot`
   - Permissions: `3165184` (View Channels, Send Messages, Connect, Speak)

---

## Проверка работы

После деплоя бот должен:
1. Появиться онлайн в Discord
2. Показать статус "🎵 Ready to play music"
3. Отвечать на команду `/help`

Если что-то не работает - проверь логи на хостинге.

---

## Что установится автоматически

✅ Python 3.10  
✅ FFmpeg (для аудио)  
✅ discord.py  
✅ yt-dlp  
✅ Все остальные зависимости  

**Тебе нужно только:**
1. Выбрать хостинг
2. Добавить токен Discord
3. Всё! 🎉
