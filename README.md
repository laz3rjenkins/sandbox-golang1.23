## Сервис-песочница для Go 1.23

Этот проект — HTTP‑сервис на Python/Flask, который **компилирует и выполняет пользовательский код на Go 1.23 в изолированном контейнере** и позволяет:

- **/debug/** — один запуск программы с произвольным консольным вводом;
- **/testing/** — прогон программы на наборе тестов с проверкой результатов пользовательской Python‑функцией `checker`.

Go‑код выполняется внутри Docker‑контейнера под отдельным системным пользователем с ограниченными правами.

---

## Технологии

- **Python 3.8**
- **Flask** — HTTP API;
- **pytest, pytest-mock** — тесты;
- **Docker + docker‑compose** — контейнер с Go и sandbox‑пользователем;
- **Go 1.23.3** — компиляция и выполнение пользовательского кода.

---

## Развёртывание через Docker (рекомендуемый способ)

### Быстрый старт

Из корня репозитория:

```bash
cd scripts
./up
```

Скрипт:

- создаёт внешний volume `import` и сеть `localhost` (если их ещё нет);
- собирает образ из `docker/Dockerfile`;
- поднимает сервис `sandbox-go123` в фоне.

После успешного старта сервис будет доступен по адресу:

- `http://localhost:9010/` — HTML‑страница;
- `http://localhost:9010/debug/` — API для единичного запуска;
- `http://localhost:9010/testing/` — API для тестового прогона.

Остановить контейнер (без удаления):

```bash
cd scripts
./stop
```

Полностью остановить и удалить контейнер/сеть/volume:

```bash
cd scripts
./down
```

Повторный запуск уже собранного контейнера:

```bash
cd scripts
./start
```

Параметры песочницы задаются в `docker/docker-compose.yml`:

- `SANDBOX_USER_UID=999`
- `SANDBOX_DIR=/sandbox`
- `PYTHONPATH=/app/src`

---

## Локальный запуск без Docker (для разработки)

> В продакшене и для полноценного тестирования рекомендуется использовать Docker. Локальный запуск предполагает, что у вас уже установлен Go нужной версии и корректно настроены права файловой системы.

1. Установите Python‑зависимости (через `pipenv` или напрямую):

```bash
cd src
pip install -r <(pipenv lock -r)  # либо используйте Pipfile/Pipfile.lock по своему вкусу
```

Или:

```bash
cd src
pipenv install --dev
pipenv shell
```

2. Установите и настройте Go (если ещё не установлен) версии, совместимой с 1.23.

3. Установите переменные окружения (опционально):

- `SANDBOX_USER_UID` — UID пользователя, под которым будет запускаться Go‑код (по умолчанию текущий UID);
- `SANDBOX_USER_GID` — GID пользователя (по умолчанию текущий GID);
- `SANDBOX_DIR` — каталог песочницы (по умолчанию системный temp‑каталог);
- `TIMEOUT` — лимит времени выполнения (по умолчанию 5 секунд).

4. Запустите Gunicorn:

```bash
cd src
./start.sh
```

По умолчанию приложение будет доступно на `http://0.0.0.0:9010/`.

---

## API

Формат запросов и ответов — **JSON**.
Все детали схем запросов/ответов описаны в:

- `docs/debug.md` — эндпоинт `/debug/`;
- `docs/testing.md` — эндпоинт `/testing/`.

Кратко:

- **POST `/debug/`**
  - Тело запроса:
    - `code: str` — Go‑код;
    - `data_in: ?str` — консольный ввод (опционально).
  - Ответ `200 OK`:
    - `result: str | null` — stdout программы;
    - `error: str | null` — ошибка компиляции/исполнения (если есть).

- **POST `/testing/`**
  - Тело запроса:
    - `code: str` — Go‑код;
    - `checker: str` — Python‑функция `def checker(right_value: str, value: str) -> bool: ...`;
    - `tests: [ { data_in: str, data_out: str }, ... ]` — набор тестов.
  - Ответ `200 OK`:
    - `num: int` — количество тестов;
    - `num_ok: int` — количество успешных тестов;
    - `ok: bool` — все ли тесты прошли;
    - `tests: [ { ok, error, result }, ... ]` — подробности по каждому тесту.

В случае ошибок валидации (`400`) и внутренних ошибок сервиса (`500`) возвращаются структуры, описанные в `docs/debug.md` и `docs/testing.md`.

---

## Примеры запросов

### 1. Отладочный запуск `/debug/`

```bash
curl -X POST http://localhost:9010/debug/ \
  -H "Content-Type: application/json" \
  -d '{
    "code": "package main\nimport \"fmt\"\nfunc main(){ var x int; fmt.Scan(&x); fmt.Println(x*2) }",
    "data_in": "21"
  }'
```

Ожидаемый ответ (`200 OK`):

```json
{
  "result": "42",
  "error": null
}
```

### 2. Прогон тестов `/testing/`

```bash
curl -X POST http://localhost:9010/testing/ \
  -H "Content-Type: application/json" \
  -d '{
    "code": "package main\nimport \"fmt\"\nfunc main(){ var x int; fmt.Scan(&x); fmt.Println(x*x) }",
    "checker": "def checker(right_value: str, value: str) -> bool:\n    return right_value.strip() == value.strip()",
    "tests": [
      { "data_in": "2", "data_out": "4" },
      { "data_in": "3", "data_out": "9" }
    ]
  }'
```

---

## Тестирование

### В контейнере (рекомендуется)

Контейнер должен быть запущен (`./scripts/up` или `./scripts/start`).

```bash
cd scripts
./tests
```

Скрипт выполняет:

```bash
docker exec -it sandbox-go123 pytest -vv -p no:cacheprovider /app/src
```

