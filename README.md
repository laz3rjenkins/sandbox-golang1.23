# Go Execution API

API для компиляции и выполнения программ на языке Golang (1.23).  

---

## Технологии

- Python 3.13
- Flask 3.1.2
- Pytest 8.4.2
- Go 1.23
- Docker / Docker Compose

---

## Установка и запуск локально

1. Клонировать репозиторий:
```bash
git clone git@github.com:laz3rjenkins/sandbox-golang1.23.git
cd sandbox-golang1.23
```

## Запуск в Docker

### Запуск контейнера
```bash
cd docker
docker compose -f docker-compose.yml build --no-cache
docker compose up -d   
```
Контейнер будет доступен по порту 9002:
```bash
http://localhost:9002/
```
