# Настройка Cookies для YouTube

## Зачем это нужно

YouTube блокирует ботов и требует cookies для подтверждения, что запросы идут от реального пользователя.

## Как получить cookies

### Способ 1: Расширение для браузера (самый простой)

1. Установи расширение "Get cookies.txt LOCALLY" для Chrome/Firefox:
   - Chrome: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
   - Firefox: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/

2. Зайди на youtube.com и войди в свой аккаунт

3. Нажми на иконку расширения

4. Нажми "Export" → сохрани файл как `youtube_cookies.txt`

5. Загрузи файл в корень проекта (туда же где main.py)

### Способ 2: Вручную через DevTools

1. Открой youtube.com в браузере

2. Нажми F12 (открыть DevTools)

3. Перейди на вкладку "Application" → "Cookies" → "https://www.youtube.com"

4. Скопируй все cookies в формате Netscape

5. Создай файл `youtube_cookies.txt` с этим содержимым

## Формат файла cookies

Файл должен быть в формате Netscape:

```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	0	CONSENT	YES+
.youtube.com	TRUE	/	FALSE	1234567890	VISITOR_INFO1_LIVE	xxxxx
```

## Безопасность

⚠️ **ВАЖНО:**
- НЕ делись файлом cookies с другими
- НЕ загружай его в публичный GitHub
- Файл `youtube_cookies.txt` уже добавлен в `.gitignore`
- Cookies истекают через ~6 месяцев, нужно будет обновить

## После добавления cookies

1. Загрузи `youtube_cookies.txt` в корень проекта
2. Сделай commit и push на GitHub
3. Railway автоматически задеплоит
4. YouTube заработает!

## Проверка

После деплоя попробуй:
```
/play https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Если работает - всё готово! 🎉
