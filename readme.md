Ниже — готовый подробный Markdown для кодового агента. Его можно вставить в Codex, Claude, Cursor, Windsurf или другой coding agent как спеку проекта.

---

```markdown
# Job Autopilot — персональный автономный пайплайн поиска и откликов

Ты — coding agent, который должен спроектировать и реализовать локальный персональный сервис для автоматизации поиска работы, откликов, сбора контактов HR, мониторинга Telegram-каналов, генерации сопроводительных писем и алертов.

Сервис делается для одного пользователя, локально, без публичного доступа.

---

## 1. Цель проекта

Создать локальный оркестратор, который:

1. Мониторит источники вакансий:
   - hh.ru;
   - hirify;
   - Telegram-каналы.

2. Применяет глобальные и платформенные фильтры вакансий.

3. Исключает нежелательных работодателей.

4. Находит подходящие вакансии:
   - Golang developer;
   - backend developer;
   - full stack с выраженным backend-уклоном;
   - уровень middle и выше;
   - удалёнка обязательна.

5. Генерирует сопроводительные письма и ответы на вопросы при отклике с помощью LLM на основе базового контекста кандидата.

6. Отправляет отклики через hh.ru с помощью браузерного агента Codex или совместимого browser agent.

7. Использует Hirify как источник контактов HR / нанимающих менеджеров:
   - email;
   - Telegram;
   - другие контакты.

8. Мониторит Telegram-каналы программно, без браузерного агента, если это возможно.

9. Собирает статистику:
   - найденные вакансии;
   - отклики;
   - пропуски;
   - ошибки;
   - ответы HR;
   - изменения статусов.

10. Отправляет алерты в Telegram-бот:
   - новый HR написал;
   - вакансия найдена;
   - отклик отправлен;
   - отклик не удался;
   - сводка за последние N часов.

11. Имеет UI для управления:
   - источниками;
   - фильтрами;
   - LLM-контекстом;
   - runbook-промптами;
   - API-ключами;
   - вакансиями;
   - откликами;
   - контактами;
   - рассылками;
   - логами и статистикой.

---

## 2. Ключевые продуктовые требования

### 2.1. UI

Интерфейс должен быть локальным web-приложением.

Предпочтительный вариант:

- локальный web server;
- открывается в браузере на `http://127.0.0.1:8000`;
- desktop-версия не нужна на первом этапе.

UI должен позволять:

- включать и выключать источники;
- настраивать глобальный фильтр;
- настраивать отдельные фильтры для hh.ru и hirify;
- задавать базовый контекст кандидата;
- загружать CV;
- редактировать runbook-промпты;
- задавать API-ключи;
- смотреть вакансии;
- смотреть отклики;
- смотреть контакты;
- смотреть исходящие сообщения;
- смотреть статистику;
- смотреть логи;
- запускать задачи вручную;
- получать ссылки / кнопки для ручного запуска Codex, если автоматическая интеграция недоступна.

---

### 2.2. Источники

Необходимо поддерживать источники:

1. `hh`
   - поиск вакансий;
   - отклики;
   - статистика по откликам.

2. `hirify`
   - поиск вакансий;
   - извлечение контактов HR;
   - подготовка outreach-сообщений.

3. `telegram_channels`
   - мониторинг пула Telegram-каналов;
   - извлечение вакансий;
   - извлечение контактов;
   - передача в общий pipeline.

Каждый источник можно включить или выключить в UI.

---

### 2.3. Фильтры

Система должна иметь:

1. Глобальный фильтр.
2. Пер-сорсовые фильтры.

Пользователь должен мочь:

- использовать глобальный фильтр;
- отключить глобальный фильтр;
- включить только платформенные фильтры для hh и hirify;
- переопределять глобальный фильтр для конкретного источника.

Фильтры должны быть представлены в UI как JSON editor + человекочитаемые поля.

---

### 2.4. LLM-генерация без заранее подготовленной базы ответов

Заранее подготовленной базы ответов не будет.

Все тексты генерируются LLM в момент отклика / outreach на основе:

- базового контекста кандидата;
- CV;
- описания вакансии;
- требований вакансии;
- глобальных фильтров;
- настроек тона и ограничений.

Пользователь должен мочь редактировать базовый контекст через UI.

---

### 2.5. Codex / browser agent

Для hh.ru и hirify основной исполнитель — Codex с Chrome extension или совместимый браузерный агент.

Оркестратор должен:

- формировать runbook prompt;
- передавать его агенту;
- получать результат;
- сохранять результат в базу;
- обновлять статусы сущностей.

Если прямого API для Codex нет, реализовать несколько режимов:

1. `manual`
   - UI генерирует prompt;
   - пользователь копирует prompt в Codex;
   - пользователь вставляет результат обратно в UI.

2. `clipboard_browser`
   - система открывает Codex в браузере;
   - вставляет prompt;
   - пользователь нажимает execute.

3. `browser_bridge`
   - экспериментальный режим;
   - Playwright / CDP управляет уже залогиненным браузером;
   - prompt вставляется автоматически;
   - ответ агента читается автоматически.

4. `api`
   - если доступен API endpoint / CLI / SDK;
   - используется ключ или сессия.

Архитектура должна абстрагировать Codex за интерфейсом `BrowserAgentProvider`, чтобы позже заменить Codex на другой browser agent.

---

### 2.6. Telegram

Telegram используется в нескольких ролях:

1. Мониторинг Telegram-каналов.
2. Отправка outreach-сообщений по найденным контактам.
3. Получение входящих сообщений от HR.
4. Алерты пользователю через отдельный Telegram bot.

Для мониторинга каналов и работы с личным Telegram-аккаунтом использовать программный сервис на Telethon или Pyrogram, а не браузерный агент.

Поддержать отдельные Telegram-аккаунты:

- `channels_reader` — для чтения каналов;
- `outreach_account` — для переписки с HR;
- `alerts_bot` — для служебных алертов.

На MVP можно использовать один аккаунт для каналов и outreach, но архитектура должна поддерживать несколько аккаунтов.

---

### 2.7. Алерты

Telegram bot должен отправлять:

- новый входящий контакт похож на HR;
- вакансия найдена и подходит;
- вакансия отклонена фильтром;
- отклик отправлен;
- отклик не отправлен;
- контакт найден;
- outreach отправлен;
- outreach failed;
- сводка за последние N часов.

Частота сводок настраивается.

Допустимая задержка: 1–2 часа.

---

### 2.8. Статистика

Система должна считать статистику:

- по hh.ru;
- по hirify;
- по telegram_channels;
- по outreach;
- по incoming HR messages.

Метрики:

- найдено вакансий;
- прошло фильтры;
- отклонено фильтрами;
- отправлено откликов;
- неудачных откликов;
- найдено контактов;
- отправлено outreach;
- получено ответов;
- ошибки;
- skip reasons.

Статистика должна быть доступна в UI и в Telegram-сводках.

---

## 3. Технические ограничения и принципы

### 3.1. Локальность

Сервис работает локально:

- backend на localhost;
- база локальная;
- секреты локальные;
- публичный доступ не нужен.

---

### 3.2. Расширяемость источников

Каждый источник должен реализовывать общий интерфейс:

```python
class SourceAdapter:
    source_name: str

    async def fetch(self) -> list[RawVacancy]:
        ...

    async def apply(self, vacancy: Vacancy, payload: ApplicationPayload) -> ActionResult:
        ...

    async def collect_stats(self) -> StatsResult:
        ...
```

Добавление нового источника не должно ломать существующие.

---

### 3.3. Расширяемость агентов

Все действия через браузерного агента должны идти через abstraction:

```python
class BrowserAgentProvider:
    async def dispatch(self, task: AgentTask) -> AgentTaskResult:
        ...

    async def healthcheck(self) -> bool:
        ...
```

Провайдеры:

- `ManualAgentProvider`
- `ClipboardBrowserAgentProvider`
- `BrowserBridgeAgentProvider`
- `OpenAIAgentProvider`
- `LocalPlaywrightAgentProvider`

---

### 3.4. Dry-run

Должен быть глобальный режим:

```env
DRY_RUN=true
```

В dry-run:

- вакансии находятся;
- фильтруются;
- LLM генерирует тексты;
- контакты сохраняются;
- но реальная отправка откликов / outreach не выполняется;
- все действия пишутся в лог как simulated.

---

### 3.5. Идемпотентность

Система не должна:

- откликаться дважды на одну вакансию;
- писать одному контакту дважды по одной вакансии;
- обрабатывать одно и то же Telegram-сообщение дважды;
- создавать дубли компаний / контактов.

Для этого использовать:

- source + source_id;
- url hash;
- company normalized name;
- contact normalized value;
- message_id + chat_id.

---

### 3.6. Обработка ошибок

Любая ошибка должна приводить к:

- статусу `failed`;
- сохранению reason;
- event log;
- опциональному алерту.

Система не должна падать целиком из-за одной вакансии, одного контакта или одного сообщения.

---

## 4. Рекомендуемый технологический стек

Использовать следующий стек:

### Backend

- Python 3.12+
- FastAPI
- SQLModel или SQLAlchemy 2.x
- SQLite
- Alembic — опционально, для MVP можно `create_all()`
- APScheduler
- Pydantic v2
- httpx
- loguru
- python-dotenv
- Jinja2
- HTMX
- Alpine.js
- Tailwind CSS через CDN или локальный build

### Telegram

- Telethon или Pyrogram
- asyncio
- separate session files

### LLM

- OpenAI-compatible client
- поддержка любого endpoint:
  - OpenAI;
  - Anthropic-compatible proxy;
  - OpenRouter;
  - local model;
  - любой custom base_url.

### Browser agent

- Codex Chrome extension как основной внешний агент;
- Playwright как дополнительный bridge или fallback;
- browser-use опционально позже.

### Frontend

Локальный web UI:

- FastAPI routes;
- Jinja2 templates;
- HTMX для интерактивности;
- Alpine.js для легких UI состояний;
- Tailwind CSS.

Desktop не нужен. Позже можно обернуть в Tauri, если потребуется.

---

## 5. Архитектура системы

```text
┌────────────────────────────┐
│        Local Web UI        │
│ FastAPI + Jinja + HTMX     │
└─────────────┬──────────────┘
              │
┌─────────────▼──────────────┐
│        Orchestrator        │
│ scheduler, filters, state  │
└─────┬────────┬────────┬────┘
      │        │        │
┌─────▼───┐ ┌──▼─────┐ ┌▼────────────────┐
│ HH      │ │Hirify  │ │ Telegram channels│
│ source  │ │source  │ │ source           │
└─────┬───┘ └──┬─────┘ └┬────────────────┘
      │        │         │
┌─────▼────────▼─────┐  ┌▼────────────────┐
│ Browser Agent      │  │ Telegram service │
│ Codex / Playwright │  │ Telethon         │
└─────┬──────────────┘  └┬────────────────┘
      │                  │
┌─────▼──────────────────▼────┐
│           Storage           │
│ SQLite, logs, events, files │
└─────────────────────────────┘
```

---

## 6. Структура проекта

Создать следующую структуру:

```text
job-autopilot/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── filter_service.py
│   │   ├── llm_service.py
│   │   ├── vacancy_service.py
│   │   ├── contact_service.py
│   │   ├── application_service.py
│   │   ├── outreach_service.py
│   │   ├── stats_service.py
│   │   ├── alert_service.py
│   │   └── scheduler_service.py
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── hh.py
│   │   ├── hirify.py
│   │   └── telegram_channels.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── manual.py
│   │   ├── clipboard.py
│   │   ├── browser_bridge.py
│   │   └── openai_agent.py
│   ├── telegram/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── channel_reader.py
│   │   ├── outreach_sender.py
│   │   ├── incoming_monitor.py
│   │   └── alerts_bot.py
│   ├── web/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── dashboard.py
│   │   │   ├── sources.py
│   │   │   ├── filters.py
│   │   │   ├── profile.py
│   │   │   ├── runbooks.py
│   │   │   ├── vacancies.py
│   │   │   ├── applications.py
│   │   │   ├── contacts.py
│   │   │   ├── outreach.py
│   │   │   ├── stats.py
│   │   │   ├── settings.py
│   │   │   └── logs.py
│   │   └── templates/
│   │       ├── base.html
│   │       ├── dashboard.html
│   │       ├── sources.html
│   │       ├── filters.html
│   │       ├── profile.html
│   │       ├── runbooks.html
│   │       ├── vacancies.html
│   │       ├── applications.html
│   │       ├── contacts.html
│   │       ├── outreach.html
│   │       ├── stats.html
│   │       ├── settings.html
│   │       └── logs.html
│   ├── prompts/
│   │   ├── hh_search_apply.md
│   │   ├── hh_stats.md
│   │   ├── hirify_contacts.md
│   │   ├── telegram_parse.md
│   │   ├── generate_application.md
│   │   ├── generate_outreach.md
│   │   └── classify_hr_message.md
│   └── cli.py
├── data/
│   ├── db.sqlite
│   ├── sessions/
│   ├── uploads/
│   ├── logs/
│   └── screenshots/
├── .env
├── requirements.txt
└── README.md
```

---

## 7. Модель данных

Использовать SQLModel / SQLAlchemy.

### 7.1. Source

```python
class Source:
    id: str                  # hh | hirify | telegram_channels
    name: str
    enabled: bool
    use_global_filter: bool
    local_filter_json: dict
    config_json: dict
    updated_at: datetime
```

---

### 7.2. ProfileContext

Хранит базовый контекст кандидата.

```python
class ProfileContext:
    id: int
    name: str
    markdown_text: str
    cv_file_path: str | None
    tone: str
    constraints_text: str
    stop_words_text: str
    salary_expectation: str | None
    remote_only: bool
    min_grade: str
    allow_full_stack: bool
    full_stack_backend_focus_min: float
    updated_at: datetime
```

---

### 7.3. GlobalFilter

```python
class GlobalFilter:
    id: int
    enabled: bool
    filter_json: dict
    updated_at: datetime
```

---

### 7.4. Vacancy

```python
class Vacancy:
    id: str
    source: str
    source_id: str | None
    url: str
    title: str
    company: str | None
    location: str | None
    remote: bool | None
    grade_hint: str | None
    salary_text: str | None
    description_text: str | None
    raw_json: dict
    status: str
    match_score: int | None
    match_reason: str | None
    skip_reason: str | None
    created_at: datetime
    updated_at: datetime
```

Статусы vacancy:

```text
new
filtered_out
matched
applied
application_failed
contact_found
outreach_sent
skipped
archived
```

---

### 7.5. Application

```python
class Application:
    id: str
    vacancy_id: str
    source: str
    status: str
    cover_letter: str | None
    generated_answers_json: dict | None
    agent_task_id: str | None
    external_status: str | None
    created_at: datetime
    updated_at: datetime
```

Статусы application:

```text
pending
generating
ready
submitted
failed
skipped
viewed
invite
rejected
no_response
unknown
```

---

### 7.6. Contact

```python
class Contact:
    id: str
    source: str
    vacancy_id: str | None
    company: str | None
    person_name: str | None
    role_hint: str | None
    contact_type: str       # telegram | email | phone | other
    value_normalized: str
    value_raw: str
    status: str
    created_at: datetime
    updated_at: datetime
```

Статусы contact:

```text
new
queued
outreach_sent
replied
failed
duplicate
archived
```

---

### 7.7. OutreachMessage

```python
class OutreachMessage:
    id: str
    contact_id: str
    channel: str             # telegram | email
    subject: str | None
    body: str
    cv_attached: bool
    status: str
    sent_at: datetime | None
    error: str | None
    created_at: datetime
```

Статусы outreach:

```text
draft
queued
sent
failed
replied
```

---

### 7.8. TelegramChannel

```python
class TelegramChannel:
    id: int
    username_or_id: str
    name: str | None
    enabled: bool
    last_message_id: int | None
    last_checked_at: datetime | None
```

---

### 7.9. TelegramAccount

```python
class TelegramAccount:
    id: int
    name: str                 # channels_reader | outreach | alerts
    session_file: str
    api_id: str
    api_hash: str
    phone: str | None
    enabled: bool
```

---

### 7.10. AgentTask

```python
class AgentTask:
    id: str
    source: str
    task_type: str
    prompt_text: str
    provider: str
    status: str
    input_json: dict
    result_json: dict | None
    error: str | None
    created_at: datetime
    updated_at: datetime
```

Типы задач:

```text
hh_search_apply
hh_stats
hirify_contacts
browser_custom
```

Статусы:

```text
created
queued
dispatched
running
completed
failed
cancelled
```

---

### 7.11. EventLog

```python
class EventLog:
    id: int
    entity_type: str
    entity_id: str | None
    event_type: str
    payload_json: dict
    created_at: datetime
```

---

### 7.12. RunbookPrompt

```python
class RunbookPrompt:
    id: str
    source: str
    task_type: str
    name: str
    template_text: str
    enabled: bool
    updated_at: datetime
```

---

### 7.13. Setting

```python
class Setting:
    key: str
    value: str
    is_secret: bool
    updated_at: datetime
```

---

## 8. Конфигурация

Использовать `.env` и таблицу `Setting`.

Приоритет:

1. UI settings.
2. `.env`.
3. default values.

### Основные переменные

```env
APP_ENV=local
DEBUG=true
HOST=127.0.0.1
PORT=8000
DRY_RUN=true

DATABASE_URL=sqlite:///data/db.sqlite

LLM_PROVIDER=openai_compatible
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=4000

TELEGRAM_BOT_TOKEN=
TELEGRAM_ALERT_CHAT_ID=

TELEGRAM_API_ID=
TELEGRAM_API_HASH=

CODEX_PROVIDER=manual
CODEX_API_KEY=
CODEX_BROWSER_PROFILE_PATH=
CODEX_UI_URL=

SCREENSHOTS_DIR=data/screenshots
UPLOADS_DIR=data/uploads
LOGS_DIR=data/logs

SCHEDULER_ENABLED=true
HH_SEARCH_INTERVAL_MINUTES=120
HH_STATS_INTERVAL_MINUTES=120
HIRIFY_INTERVAL_MINUTES=120
TELEGRAM_CHANNELS_INTERVAL_MINUTES=30
ALERT_SUMMARY_INTERVAL_MINUTES=120
```

---

## 9. Фильтры

### 9.1. Глобальный фильтр

Пример JSON:

```json
{
  "enabled": true,
  "remote_only": true,
  "min_grade": "middle",
  "primary_keywords": [
    "golang",
    "go",
    "backend",
    "back-end",
    "бэкенд"
  ],
  "secondary_keywords": [
    "kubernetes",
    "postgresql",
    "docker",
    "grpc",
    "microservices"
  ],
  "exclude_keywords": [
    "junior",
    "intern",
    "trainee",
    "стажер",
    "джуниор",
    "office only"
  ],
  "allow_full_stack": true,
  "full_stack_backend_focus_min": 0.6,
  "blacklist": {
    "companies": [
      {
        "name": "Current Employer",
        "aliases": ["Current Co", "CE"],
        "domains": ["current.ru"],
        "inn": []
      }
    ]
  }
}
```

---

### 9.2. Пер-сорсовые фильтры

Для каждого источника хранить:

```json
{
  "use_global_filter": true,
  "override": {
    "remote_only": true,
    "min_grade": "middle"
  }
}
```

Если `use_global_filter=false`, использовать только `local_filter_json`.

Если `use_global_filter=true`, взять глобальный фильтр и применить override сверху.

---

### 9.3. Порядок применения фильтра

1. Нормализовать вакансию.
2. Применить source enabled.
3. Применить source local filter / global filter.
4. Применить blacklist.
5. Применить LLM classification, если hard filters passed.
6. Сохранить результат.

---

### 9.4. LLM classification

LLM должен возвращать:

```json
{
  "match": true,
  "score": 88,
  "remote": true,
  "grade": "middle",
  "is_golang": true,
  "backend_focus": 0.8,
  "reasons": [],
  "red_flags": []
}
```

---

## 10. LLM-контекст

### 10.1. Base Context

Пользователь задает через UI:

- имя;
- целевая роль;
- грейд;
- стек;
- опыт;
- удалёнка;
- зарплатные ожидания;
- tone of voice;
- ограничения;
- stop words;
- что нельзя упоминать;
- дополнительные комментарии.

CV может быть загружен как файл:

- pdf;
- md;
- txt.

Система должна:

- хранить файл;
- извлекать текст;
- показывать текст в UI;
- позволять редактировать извлеченный текст вручную.

---

### 10.2. Context pack для LLM

Каждый LLM-запрос должен получать:

```json
{
  "profile_context": "...",
  "cv_text": "...",
  "constraints": "...",
  "vacancy": {
    "title": "...",
    "company": "...",
    "description": "...",
    "remote": true,
    "grade_hint": "middle"
  },
  "source": "hh",
  "task": "generate_application"
}
```

---

### 10.3. Генерация ответов без базы ответов

Для вопросов анкеты LLM должен генерировать ответы только из контекста.

Prompt должен требовать:

- не выдумывать факты;
- если данных недостаточно, вернуть `can_answer=false`;
- отвечать кратко;
- сохранять деловой тон;
- учитывать remote only;
- не упоминать нежелательные темы.

Ответ LLM:

```json
{
  "answers": [
    {
      "question": "Опыт коммерческой разработки на Go?",
      "answer": "3 года коммерческой разработки на Go.",
      "can_answer": true,
      "confidence": 0.93
    }
  ]
}
```

Если `can_answer=false`, система должна:

- пометить вакансию как skip;
- сохранить reason `cannot_answer_required_question`.

Поведение настраивается:

```text
unknown_question_policy = skip | generate_best_effort
```

По умолчанию: `skip`.

---

## 11. Источники

### 11.1. HH source

HH source отвечает за:

- поиск вакансий;
- передачу вакансий в фильтр;
- постановку задачи браузерному агенту на отклик;
- сбор статистики по откликам.

Режимы:

1. `hh_search_apply`
   - агент ищет вакансии;
   - фильтрует;
   - откликается.

2. `hh_stats`
   - агент собирает обновления по откликам.

Оркестратор должен хранить:

- search query URL;
- число страниц;
- лимит вакансий за run;
- статус последней задачи.

---

### 11.2. Hirify source

Hirify source отвечает за:

- поиск вакансий;
- фильтрацию;
- извлечение контактов;
- сохранение контактов;
- генерацию outreach.

Основная задача browser agent:

```text
hh/hirify search -> vacancy page -> contacts block -> extract contacts
```

Hirify не должен обязательно отправлять отклик внутри платформы. Его главная цель — контакты.

---

### 11.3. Telegram channels source

Telegram channels source — программный сервис.

Он должен:

- подключаться к Telegram аккаунту;
- читать список каналов;
- получать новые сообщения;
- дедуплицировать сообщения;
- передавать текст в LLM parser;
- сохранять вакансии и контакты.

Не использовать браузерный агент для чтения каналов, если доступен Telethon/Pyrogram.

---

## 12. Codex / Browser Agent integration

### 12.1. AgentTask

Каждая задача агенту сохраняется в `AgentTask`.

Поля:

```python
task_type = "hh_search_apply" | "hh_stats" | "hirify_contacts"
source = "hh" | "hirify"
prompt_text = rendered runbook
input_json = filters, profile, limits
result_json = agent response
```

---

### 12.2. Agent provider interface

```python
class BrowserAgentProvider:
    async def dispatch(self, task: AgentTask) -> AgentTaskResult:
        raise NotImplementedError

    async def healthcheck(self) -> bool:
        raise NotImplementedError
```

---

### 12.3. Manual provider

UI показывает:

- task id;
- prompt;
- кнопку copy;
- кнопку open Codex;
- поле для вставки результата;
- кнопку save result.

Manual provider:

- создает task;
- помечает `dispatched`;
- ждет, пока пользователь вставит result JSON.

---

### 12.4. Clipboard browser provider

Provider:

- открывает Codex UI URL;
- копирует prompt в clipboard;
- пользователь вставляет и запускает.

Это полуручной режим.

---

### 12.5. Browser bridge provider

Экспериментальный режим.

Provider:

- запускает Playwright persistent context;
- использует профиль браузера пользователя;
- открывает Codex UI;
- вставляет prompt;
- нажимает submit;
- ждет завершения;
- извлекает текст результата;
- сохраняет result.

Требования:

- feature flag;
- screenshots;
- timeout;
- fallback to manual;
- не блокировать всю систему при ошибке.

---

### 12.6. API provider

Если есть API:

- использовать API key;
- отправлять prompt;
- получать JSON result.

---

### 12.7. Требования к результату агента

Все runbooks должны требовать от агента возвращать strict JSON.

Базовый формат:

```json
{
  "status": "success | partial | failed",
  "task_type": "hh_search_apply",
  "items": [],
  "errors": [],
  "metrics": {
    "found": 0,
    "matched": 0,
    "applied": 0,
    "skipped": 0,
    "failed": 0
  }
}
```

---

## 13. Telegram service

### 13.1. Telegram accounts

Поддержать несколько session files:

```text
data/sessions/channels_reader.session
data/sessions/outreach.session
```

CLI команды:

```bash
python -m app.cli tg-login --account channels_reader
python -m app.cli tg-login --account outreach
```

---

### 13.2. Channel reader

Job:

1. читает enabled channels;
2. получает новые сообщения;
3. пропускает уже обработанные;
4. вызывает LLM parser;
5. сохраняет vacancy / contact;
6. отправляет event.

---

### 13.3. Incoming monitor

Мониторит входящие сообщения outreach account.

Для нового входящего сообщения:

1. проверить, известен ли контакт;
2. если нет — создать contact candidate;
3. классифицировать сообщение через LLM;
4. если похоже на HR — создать alert;
5. обновить outreach conversation state.

---

### 13.4. Outreach sender

Отправляет сообщения:

- Telegram username;
- Telegram user id;
- email через SMTP/Gmail API позже.

Перед отправкой:

- проверить дедупликацию;
- проверить контакт в blacklist;
- проверить вакансию;
- сгенерировать сообщение;
- прикрепить CV, если нужно.

---

### 13.5. Alerts bot

Отдельный Telegram bot отправляет пользователю:

- immediate alerts;
- summary alerts.

Типы алертов:

```text
hr_message_received
application_submitted
application_failed
contact_found
outreach_sent
outreach_failed
summary
```

---

## 14. UI specification

### 14.1. Dashboard

Показать:

- статус источников;
- статус агентов;
- статус Telegram;
- последние события;
- счетчики за 24 часа;
- кнопки manual run:
  - HH search apply;
  - HH stats;
  - Hirify contacts;
  - Telegram channels sync;
  - send summary.

---

### 14.2. Sources page

Таблица источников:

- enabled;
- use global filter;
- last run;
- last status;
- interval minutes;
- actions.

Действия:

- enable/disable;
- edit local filter;
- run now;
- view logs.

---

### 14.3. Filters page

Две зоны:

1. Global filter.
2. Source filters.

Для global filter:

- enabled;
- remote_only;
- min_grade;
- allow_full_stack;
- backend_focus_min;
- keywords;
- exclude_keywords;
- blacklist editor;
- JSON editor.

Для source filters:

- use global;
- override JSON;
- test filter button.

---

### 14.4. Profile page

Разделы:

- basic info;
- markdown context;
- CV upload;
- extracted CV text;
- constraints;
- stop words;
- tone;
- salary expectation;
- remote only;
- min grade;
- allow full stack.

Кнопки:

- save;
- preview context pack;
- test LLM generation.

---

### 14.5. Runbooks page

Список runbook prompts:

- source;
- task type;
- enabled;
- updated_at.

Editor:

- template text;
- variables;
- preview with current profile/filter;
- save;
- reset to default.

---

### 14.6. Vacancies page

Фильтры:

- source;
- status;
- company;
- remote;
- grade;
- created_at range.

Таблица:

- title;
- company;
- source;
- remote;
- grade;
- score;
- status;
- created_at.

Detail drawer:

- raw JSON;
- description;
- match reason;
- skip reason;
- application;
- contacts;
- events.

---

### 14.7. Applications page

Таблица:

- vacancy title;
- company;
- source;
- status;
- external status;
- created_at;
- updated_at.

Detail:

- cover letter;
- generated answers;
- agent task;
- error;
- events.

---

### 14.8. Contacts page

Таблица:

- company;
- person name;
- contact type;
- value;
- source;
- vacancy;
- status.

Detail:

- outreach messages;
- related vacancy;
- events.

---

### 14.9. Outreach page

Таблица:

- contact;
- channel;
- subject / first line;
- status;
- sent_at.

Actions:

- regenerate message;
- send now;
- mark failed;
- archive.

---

### 14.10. Stats page

Фильтры:

- period: 1h / 6h / 24h / 7d / custom;
- source.

Показать:

- found;
- matched;
- skipped;
- applied;
- failed;
- contacts found;
- outreach sent;
- replies received;
- top skip reasons;
- top errors.

---

### 14.11. Settings page

Разделы:

- LLM;
- Telegram bot;
- Telegram user accounts;
- Codex / agent;
- scheduler;
- dry-run;
- intervals;
- secrets.

Все секретные поля:

- mask;
- show only last 4 chars;
- edit without displaying full value.

---

### 14.12. Logs page

Показать:

- event logs;
- agent tasks;
- scheduler runs;
- LLM calls;
- telegram errors.

Фильтры:

- level;
- entity_type;
- event_type;
- source;
- date range.

---

## 15. API endpoints

### System

```text
GET  /api/health
GET  /api/dashboard
POST /api/run/{source}/{task_type}
```

### Sources

```text
GET  /api/sources
GET  /api/sources/{source_id}
POST /api/sources/{source_id}/toggle
POST /api/sources/{source_id}/filter
```

### Filters

```text
GET  /api/filters/global
PUT  /api/filters/global
POST /api/filters/test
```

### Profile

```text
GET  /api/profile
PUT  /api/profile
POST /api/profile/cv/upload
POST /api/profile/test-generation
```

### Runbooks

```text
GET  /api/runbooks
GET  /api/runbooks/{id}
PUT  /api/runbooks/{id}
POST /api/runbooks/{id}/preview
```

### Vacancies

```text
GET  /api/vacancies
GET  /api/vacancies/{id}
POST /api/vacancies/{id}/archive
```

### Applications

```text
GET  /api/applications
GET  /api/applications/{id}
```

### Contacts

```text
GET  /api/contacts
GET  /api/contacts/{id}
```

### Outreach

```text
GET  /api/outreach
POST /api/outreach/{id}/send
POST /api/outreach/{id}/regenerate
```

### Stats

```text
GET /api/stats?period=24h&source=hh
```

### Logs

```text
GET /api/logs
GET /api/agent-tasks
GET /api/agent-tasks/{id}
```

---

## 16. Scheduler

Использовать APScheduler.

Jobs:

```text
job_hh_search_apply
job_hh_stats
job_hirify_contacts
job_telegram_channels_sync
job_telegram_incoming_monitor
job_alert_summary
job_cleanup_old_events
```

Каждый job:

- имеет interval;
- может быть включен/выключен;
- пишет run log;
- не запускается повторно, если предыдущий run еще active.

---

## 17. Prompt and runbook templates

### 17.1. HH search apply runbook

```markdown
# Role

You are a browser agent operating inside an authenticated hh.ru session.

# Task

Perform HH job search and application run.

# Constraints

- Use only current authenticated hh.ru session.
- Do not perform actions outside hh.ru.
- Do not bypass security checks.
- If a CAPTCHA, unusual check, or unresolved block appears, mark the item as failed/skipped and continue.
- Do not apply to blacklisted companies.
- Apply only to vacancies matching the filter below.
- Return strict JSON only.

# Candidate Context

{{profile_context}}

# CV

{{cv_text}}

# Global Filter

{{global_filter_json}}

# Source Filter

{{source_filter_json}}

# Run Parameters

{{run_params_json}}

# Steps

1. Open the saved HH search URL.
2. Collect vacancy cards from the configured number of pages.
3. For each vacancy:
   - extract title, company, URL, grade hint, remote hint, salary hint;
   - skip if already processed;
   - apply hard filters;
   - skip if blacklisted;
   - open vacancy page if it passes hard filters;
   - analyze description;
   - skip if frontend-heavy full stack;
   - skip if not remote;
   - skip if grade below middle;
   - generate application payload using LLM if needed.
4. If vacancy is applicable and application form is simple:
   - open apply form;
   - fill cover letter;
   - generate answers to required questions only from candidate context;
   - if a required question cannot be answered confidently, skip vacancy;
   - submit application;
   - verify submission result.
5. Record all results.

# Output

Return strict JSON:

{
  "status": "success | partial | failed",
  "task_type": "hh_search_apply",
  "items": [
    {
      "vacancy_url": "string",
      "title": "string",
      "company": "string",
      "action": "applied | skipped | failed",
      "reason": "string | null",
      "match_score": 0,
      "remote": true,
      "grade": "string | null",
      "cover_letter": "string | null",
      "answers": []
    }
  ],
  "metrics": {
    "found": 0,
    "matched": 0,
    "applied": 0,
    "skipped": 0,
    "failed": 0
  },
  "errors": []
}
```

---

### 17.2. HH stats runbook

```markdown
# Role

You are a browser agent operating inside an authenticated hh.ru session.

# Task

Collect recent application statistics and status updates.

# Constraints

- Use only hh.ru.
- Do not submit new applications.
- Do not change data.
- Return strict JSON only.

# Steps

1. Open the user's applications page.
2. Collect applications from the last {{hours}} hours.
3. For each application extract:
   - vacancy URL;
   - vacancy title;
   - company;
   - application date;
   - current status;
   - invitation flag;
   - rejection flag;
   - viewed flag if visible.
4. Return results.

# Output

Return strict JSON:

{
  "status": "success | partial | failed",
  "task_type": "hh_stats",
  "items": [
    {
      "vacancy_url": "string",
      "title": "string",
      "company": "string",
      "applied_at": "string | null",
      "status": "string",
      "viewed": false,
      "invite": false,
      "rejected": false
    }
  ],
  "metrics": {
    "total": 0,
    "viewed": 0,
    "invites": 0,
    "rejections": 0,
    "no_response": 0
  },
  "errors": []
}
```

---

### 17.3. Hirify contacts runbook

```markdown
# Role

You are a browser agent operating inside an authenticated Hirify session.

# Task

Find suitable vacancies and extract HR contacts.

# Constraints

- Use only Hirify.
- Do not send messages inside Hirify unless explicitly configured.
- Do not bypass security checks.
- Return strict JSON only.

# Candidate Context

{{profile_context}}

# Filter

{{global_filter_json}}

# Source Filter

{{source_filter_json}}

# Steps

1. Open Hirify search page.
2. Collect vacancy cards.
3. Apply filters.
4. For each suitable vacancy:
   - open vacancy page;
   - locate contacts block;
   - reveal contacts if needed;
   - extract contact text;
   - extract emails, Telegram usernames, names, roles.
5. Normalize contacts.
6. Return strict JSON.

# Output

Return strict JSON:

{
  "status": "success | partial | failed",
  "task_type": "hirify_contacts",
  "items": [
    {
      "vacancy_url": "string",
      "title": "string",
      "company": "string",
      "remote": true,
      "grade": "string | null",
      "contacts": [
        {
          "type": "telegram | email | phone | other",
          "value_raw": "string",
          "value_normalized": "string",
          "person_name": "string | null",
          "role_hint": "string | null"
        }
      ],
      "action": "contact_found | skipped | failed",
      "reason": "string | null"
    }
  ],
  "metrics": {
    "found": 0,
    "matched": 0,
    "contacts_found": 0,
    "skipped": 0,
    "failed": 0
  },
  "errors": []
}
```

---

### 17.4. Telegram post parser prompt

```markdown
You are a vacancy parser.

Analyze the Telegram post and extract structured data.

Post text:

{{post_text}}

Return strict JSON only:

{
  "is_vacancy": true,
  "title": "string | null",
  "company": "string | null",
  "grade": "junior | middle | senior | unknown",
  "remote": true,
  "stack": [],
  "contact_tg": "string | null",
  "contact_email": "string | null",
  "apply_url": "string | null",
  "salary_text": "string | null",
  "reasons": []
}
```

---

### 17.5. Application generation prompt

```markdown
You are generating an application for a job vacancy.

Use only the candidate context below.
Do not invent facts.
If required information is missing, mark can_answer=false.

Candidate context:

{{profile_context}}

CV:

{{cv_text}}

Constraints:

{{constraints_text}}

Vacancy:

{{vacancy_json}}

Questions:

{{questions_json}}

Return strict JSON only:

{
  "cover_letter_short": "string",
  "cover_letter_medium": "string",
  "answers": [
    {
      "question": "string",
      "answer": "string",
      "can_answer": true,
      "confidence": 0.0
    }
  ],
  "risk_notes": []
}
```

---

### 17.6. Outreach generation prompt

```markdown
You are generating a direct outreach message to a recruiter or hiring contact.

Use only candidate context and vacancy data.
Do not invent facts.
Keep it short, polite and direct.

Candidate context:

{{profile_context}}

Vacancy:

{{vacancy_json}}

Contact:

{{contact_json}}

Return strict JSON only:

{
  "subject": "string | null",
  "message": "string",
  "should_attach_cv": true
}
```

---

### 17.7. HR message classifier prompt

```markdown
You are classifying an incoming message.

Determine whether it looks like a recruiter / HR / hiring outreach.

Message:

{{message_text}}

Return strict JSON only:

{
  "is_hr_message": true,
  "confidence": 0.0,
  "intent": "job_outreach | recruiter_follow_up | unknown",
  "asks_resume": false,
  "asks_experience": false,
  "asks_salary": false,
  "summary": "string"
}
```

---

## 18. Roadmap by phases

Не разбивать на дни. Использовать фазы.

---

### Phase 0: Project skeleton

Цель: поднять базовый проект.

Задачи:

- создать структуру проекта;
- настроить FastAPI;
- настроить SQLite;
- настроить `.env`;
- настроить logging;
- создать базовый layout UI;
- добавить dashboard заглушку.

Acceptance criteria:

- `uvicorn app.main:app` запускается;
- UI открывается;
- `/api/health` отвечает ok;
- база создается автоматически.

---

### Phase 1: Data model and settings

Цель: реализовать модели и настройки.

Задачи:

- создать все таблицы;
- реализовать CRUD для settings;
- реализовать CRUD для sources;
- реализовать CRUD для profile context;
- реализовать CRUD для global filter;
- реализовать CRUD для runbook prompts.

Acceptance criteria:

- источники можно включать/выключать;
- настройки сохраняются;
- profile context редактируется;
- фильтры сохраняются как JSON;
- runbooks редактируются.

---

### Phase 2: UI foundation

Цель: сделать базовый UI.

Страницы:

- dashboard;
- sources;
- filters;
- profile;
- runbooks;
- settings;
- logs.

Acceptance criteria:

- все страницы рендерятся;
- формы сохраняют данные;
- секреты маскируются;
- есть базовая навигация.

---

### Phase 3: Filter engine

Цель: реализовать фильтрацию вакансий.

Задачи:

- реализовать schema для фильтров;
- реализовать merge global/source filters;
- реализовать blacklist normalization;
- реализовать keyword checks;
- реализовать grade checks;
- реализовать remote checks;
- реализовать full stack backend focus check;
- добавить test filter endpoint.

Acceptance criteria:

- можно отправить тестовый vacancy JSON;
- система возвращает pass/skip и reason;
- blacklist работает;
- source override работает;
- global disable работает.

---

### Phase 4: LLM service

Цель: реализовать LLM integration.

Задачи:

- добавить LLM client;
- поддерживать OpenAI-compatible endpoint;
- реализовать prompt rendering;
- реализовать JSON output parsing;
- реализовать retry;
- реализовать fallback при invalid JSON;
- логировать token usage и duration.

Acceptance criteria:

- LLM вызывается из UI test button;
- можно сгенерировать cover letter;
- можно классифицировать vacancy;
- можно распарсить Telegram post;
- ошибки сохраняются в logs.

---

### Phase 5: Vacancy pipeline

Цель: создать общий pipeline вакансий.

Задачи:

- реализовать RawVacancy -> Vacancy normalization;
- реализовать dedupe;
- реализовать status transitions;
- реализовать event logging;
- реализовать сохранение match/skip reasons.

Acceptance criteria:

- одна и та же вакансия не создается дважды;
- видны причины skip;
- видны reasons match;
- статусы корректно меняются.

---

### Phase 6: Agent abstraction

Цель: абстрагировать браузерного агента.

Задачи:

- создать `BrowserAgentProvider`;
- реализовать `ManualAgentProvider`;
- реализовать UI page для agent tasks;
- реализовать prompt preview;
- реализовать result paste;
- реализовать сохранение AgentTask;
- подготовить интерфейс для browser_bridge.

Acceptance criteria:

- можно создать task;
- можно посмотреть prompt;
- можно скопировать prompt;
- можно вставить result JSON;
- система парсит result;
- status обновляется.

---

### Phase 7: HH source via agent

Цель: реализовать HH search/apply и stats через agent.

Задачи:

- создать runbook prompts для HH;
- реализовать `hh_search_apply` task;
- реализовать `hh_stats` task;
- реализовать импорт result items;
- создавать applications;
- обновлять application statuses;
- связывать вакансии и applications.

Acceptance criteria:

- ручной запуск task работает;
- result JSON сохраняется;
- applications появляются в UI;
- ошибки видны;
- повторный запуск не дублирует отклики.

---

### Phase 8: Hirify source via agent

Цель: реализовать Hirify contact discovery.

Задачи:

- создать runbook prompt;
- реализовать `hirify_contacts` task;
- импортировать contacts;
- дедуплицировать contacts;
- связывать contact с vacancy;
- готовить outreach draft.

Acceptance criteria:

- contacts появляются в UI;
- duplicates помечаются;
- контакты привязаны к вакансиям;
- можно сгенерировать outreach message.

---

### Phase 9: Telegram channels source

Цель: программно мониторить Telegram-каналы.

Задачи:

- настроить Telethon client;
- реализовать CLI login;
- реализовать список каналов;
- реализовать poller;
- реализовать LLM parser;
- сохранять vacancies и contacts;
- дедуплицировать messages.

Acceptance criteria:

- новые посты обрабатываются один раз;
- вакансии появляются в UI;
- контакты появляются в UI;
- можно включить/выключить канал;
- ошибки Telegram логируются.

---

### Phase 10: Outreach

Цель: реализовать рассылку CV + сообщения по контактам.

Задачи:

- реализовать outreach generation;
- реализовать queue;
- реализовать Telegram sender;
- реализовать attach CV;
- реализовать dedupe;
- реализовать статусы sent/failed/replied;
- добавить UI page.

Acceptance criteria:

- можно отправить сообщение контакту;
- CV прикрепляется;
- повторная отправка тому же контакту блокируется;
- статус виден в UI;
- ошибки видны.

---

### Phase 11: Incoming HR monitor and alerts

Цель: отслеживать входящие HR-сообщения и алертить.

Задачи:

- мониторить incoming messages;
- классифицировать HR-like messages;
- создавать alert;
- отправлять alert через Telegram bot;
- обновлять contact / outreach state;
- реализовать summary alert.

Acceptance criteria:

- новое входящее сообщение от неизвестного контакта классифицируется;
- если похоже на HR — приходит alert;
- summary за N часов приходит;
- события видны в UI.

---

### Phase 12: Stats and dashboard

Цель: реализовать нормальную статистику.

Задачи:

- реализовать stats queries;
- реализовать period filters;
- реализовать source filters;
- реализовать dashboard counters;
- реализовать top skip reasons;
- реализовать top errors.

Acceptance criteria:

- статистика за 1h / 6h / 24h / 7d работает;
- данные совпадают с event logs;
- dashboard показывает актуальные счетчики.

---

### Phase 13: Scheduler

Цель: автоматизировать запуск по расписанию.

Задачи:

- включить APScheduler;
- добавить intervals в settings;
- добавить per-job enable/disable;
- добавить last run status;
- добавить run history.

Acceptance criteria:

- scheduler запускает jobs;
- jobs не дублируются параллельно;
- в UI видно last run;
- можно запустить job вручную.

---

### Phase 14: Hardening

Цель: стабилизировать MVP.

Задачи:

- добавить dry-run;
- добавить retries для LLM;
- добавить timeouts;
- добавить screenshots для browser bridge;
- добавить fallback manual;
- добавить экспорт JSON/CSV;
- добавить backup SQLite;
- улучшить обработку Telegram FloodWait / rate limits;
- улучшить логирование.

Acceptance criteria:

- система не падает от одной ошибки;
- dry-run работает;
- ошибки понятны;
- можно восстановить состояние после рестарта.

---

## 19. Important implementation rules for coding agent

1. Не использовать hardcoded secrets.
2. Все секреты хранить в `.env` или settings table.
3. Не логировать API keys, tokens, session cookies.
4. Все LLM-ответы парсить строго как JSON.
5. Если JSON невалидный, сделать один retry с просьбой вернуть valid JSON.
6. Если retry не помог, сохранить ошибку и skip.
7. Все действия писать в EventLog.
8. Любая отправка должна проверять dedupe.
9. Все source adapters должны быть заменяемыми.
10. Все agent providers должны быть заменяемыми.
11. UI должен быть простым, но функциональным.
12. Не делать desktop app.
13. Не делать публичный auth на первом этапе.
14. Приложение должно работать на localhost.
15. Все интервалы по умолчанию: 1–2 часа.
16. Telegram channels polling может быть чаще: 15–30 минут.
17. Heavy browser tasks не должны запускаться чаще, чем configured interval.
18. Если Codex bridge нестабилен, система должна fallback в manual mode.
19. Все runbook prompts должны редактироваться из UI.
20. Все фильтры должны редактироваться из UI.
21. Profile context должен редактироваться из UI.
22. CV должен загружаться через UI.
23. Никакой заранее фиксированной базы ответов.
24. Все ответы генерируются LLM из profile context.
25. Если LLM не может ответить на обязательный вопрос, по умолчанию skip.

---

## 20. MVP scope

Минимально жизнеспособный продукт должен уметь:

1. Запускать локальный web UI.
2. Хранить profile context.
3. Хранить global filter.
4. Хранить source filters.
5. Включать/выключать источники.
6. Редактировать runbook prompts.
7. Создавать agent task для HH.
8. Создавать agent task для Hirify.
9. Принимать result JSON от агента.
10. Сохранять вакансии.
11. Сохранять applications.
12. Сохранять contacts.
13. Мониторить Telegram-каналы через Telethon.
14. Генерировать outreach сообщения через LLM.
15. Отправлять алерты через Telegram bot.
16. Показывать статистику.
17. Работать в dry-run mode.

---

## 21. Future extensions

После MVP можно добавить:

- email outreach;
- LinkedIn source;
- Habr Career;
- Habr Freelance;
- vector search для лучшего matching;
- автоматический разбор входящих писем;
- автоклассификация диалогов по папкам Telegram;
- экспорт отчетов в CSV;
- A/B тестирование сопроводительных;
- локальная LLM;
- Playwright direct HH apply без Codex;
- self-healing selectors;
- desktop wrapper через Tauri.

---

## 22. Definition of Done

Проект считается выполненным, если:

- локальный web UI работает;
- источники включаются и выключаются;
- фильтры настраиваются;
- profile context редактируется;
- runbook prompts редактируются;
- Codex tasks создаются и сохраняются;
- result JSON от агентов импортируется;
- вакансии сохраняются;
- отклики сохраняются;
- контакты сохраняются;
- Telegram-каналы мониторятся;
- алерты приходят;
- статистика отображается;
- dry-run работает;
- нет критических падений при одиночных ошибках;
- README содержит инструкции запуска.

---

## 23. Recommended first implementation order

Кодовому агенту рекомендуется начать в таком порядке:

1. FastAPI app skeleton.
2. SQLite models.
3. Settings and secrets.
4. Profile context UI.
5. Global filter UI.
6. Source UI.
7. Runbook UI.
8. LLM service.
9. Manual agent provider.
10. HH agent task flow.
11. Hirify agent task flow.
12. Telegram channel reader.
13. Telegram alerts bot.
14. Stats page.
15. Scheduler.
16. Hardening.

---

## 24. Critical notes

- Codex Chrome extension может не иметь стабильного API. Поэтому сначала реализовать manual provider.
- Browser bridge для Codex считать экспериментальным.
- Telegram channels лучше делать программно через Telethon/Pyrogram.
- Hirify пока лучше использовать только для извлечения контактов, не для массовых действий внутри платформы.
- HH apply через browser agent должен быть максимально простым и пропускать сложные случаи.
- Все спорные случаи лучше skip, чем ломать pipeline.
- Архитектура должна быть готова к замене Codex на любой другой browser agent.
```
