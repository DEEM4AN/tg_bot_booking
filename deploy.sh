#!/bin/bash
SERVER="dima@192.168.1.6"

echo "📦 Пушим код..."
git add . && git commit -m "add time to logs-$(date +%Y%m%d-%H%M%S)" && git push

echo "🚀 Деплоим на сервер..."
ssh $SERVER "cd /opt/bot && git pull && docker compose up -d --build"

echo "✅ Готово!"



#chmod +x deploy.sh