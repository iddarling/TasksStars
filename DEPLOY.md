# Деплой на Render.com

## Быстрый старт (Blueprint)

1. Запушьте код в GitHub репозиторий
2. В Render Dashboard нажмите "New +" → "Blueprint"
3. Укажите URL вашего репозитория
4. Render автоматически создаст:
   - PostgreSQL базу данных
   - Backend сервис (FastAPI)
   - Frontend сервис (Next.js)

## Ручной деплой

### Backend

1. Создайте новый Web Service
2. Укажите:
   - Runtime: Python 3.11
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `cd backend && ./start-production.sh`

3. Добавьте Environment Variables:
   - `DATABASE_URL` - URL PostgreSQL базы
   - `SECRET_KEY` - случайная строка для JWT
   - `VAPID_PUBLIC_KEY` - для push-уведомлений (опционально)
   - `VAPID_PRIVATE_KEY` - для push-уведомлений (опционально)
   - `VAPID_EMAIL` - email для VAPID

### Frontend

1. Создайте новый Web Service
2. Укажите:
   - Runtime: Node 18
   - Build Command: `cd frontend && npm install && npm run build`
   - Start Command: `cd frontend && npm start`

3. Добавьте Environment Variables:
   - `NEXT_PUBLIC_API_URL` - URL backend сервиса (например `https://taskstars-backend.onrender.com`)

## Важные замечания

- Бесплатный план Render "засыпает" после 15 минут неактивности
- База данных на бесплатном плане хранится 90 дней
- При деплое через Blueprint имена сервисов будут: `taskstars-backend` и `taskstars-frontend`

## После деплоя

1. Обновите `CORS_ORIGINS` в `backend/app/core/config.py` если frontend получит другой URL
2. Сгенерируйте VAPID ключи для push-уведомлений:
   ```bash
   npx web-push generate-vapid-keys
   ```
