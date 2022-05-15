# Bot service

## Этот репозиторий содержит код сервиса работы с ботами приложения stat-inc

### Сервис обладает следующим функционалом:

- создание ботов
- накрутка лайков и подписок в социальной сети ***ВКонтакте***

#### Стек технологий:

- python 3.10
- FastAPI 0.75.1
- docker

### Запуск

**Для работы сервиса ботов необходим gateway сервис!** 

```
git clone https://gitlab.com/stat-inc/bot-service.git
cd bot-service
docker-compose up -d --build
```

**Документация находится по адресу http://127.0.0.1:8001/docs**
