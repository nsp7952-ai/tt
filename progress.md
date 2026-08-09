# Job Autopilot Progress

Этот файл содержит полную информацию о текущем состоянии проекта для передачи контекста между агентами.

## Последнее обновление

**Дата:** 2026-08-09  
**Статус:** Phase 1 завершен

---

## Реализованный функционал

### ✅ Завершенные задачи

#### 1. Структура проекта
- [x] Создана базовая структура проекта согласно спецификации
- [x] Настроен FastAPI application skeleton
- [x] Настроена SQLite база данных
- [x] Настроен `.env` конфигурационный файл

#### 2. Модели данных
Реализованы следующие модели в `/app/models.py`:
- [x] `Source` - источники вакансий (hh, hirify, telegram_channels)
- [x] `ProfileContext` - контекст кандидата
- [x] `GlobalFilter` - глобальный фильтр вакансий
- [x] `Vacancy` - вакансии
- [x] `Application` - отклики
- [x] `Contact` - контакты HR
- [x] `OutreachMessage` - исходящие сообщения
- [x] `TelegramChannel` - Telegram каналы для мониторинга
- [x] `TelegramAccount` - Telegram аккаунты
- [x] `AgentTask` - задачи браузерному агенту
- [x] `EventLog` - лог событий
- [x] `RunbookPrompt` - шаблоны промптов
- [x] `Setting` - настройки приложения

#### 3. Сервисы
Реализованы в `/app/services/`:
- [x] `filter_service.py` - фильтрация вакансий
- [x] `llm_service.py` - LLM интеграция
- [x] `vacancy_service.py` - управление вакансиями
- [x] `contact_service.py` - управление контактами
- [x] `agent_service.py` - управление задачами агента
- [x] `stats_service.py` - статистика
- [x] `alert_service.py` - алерты
- [x] `scheduler_service.py` - планировщик задач

#### 4. Источники
Реализованы в `/app/sources/`:
- [x] `base.py` - базовый класс SourceAdapter
- [x] `hh.py` - hh.ru источник
- [x] `hirify.py` - Hirify источник
- [x] `telegram_channels.py` - Telegram каналы источник

#### 5. Браузерные агенты
Реализованы в `/app/agents/`:
- [x] `base.py` - BrowserAgentProvider интерфейс
- [x] `manual.py` - ручной режим
- [x] `clipboard.py` - чтение из clipboard

#### 6. Web UI
##### Routes (`/app/web/routes/`):
- [x] `dashboard.py` - главная страница
- [x] `sources.py` - управление источниками
- [x] `filters.py` - фильтры
- [x] `profile.py` - профиль кандидата
- [x] `runbooks.py` - runbook промпты
- [x] `settings.py` - настройки
- [x] `vacancies.py` - вакансии
- [x] `applications.py` - отклики
- [x] `contacts.py` - контакты
- [x] `outreach.py` - рассылки
- [x] `stats.py` - статистика
- [x] `logs.py` - логи

##### Templates (`/app/web/templates/`):
- [x] `base.html` - базовый layout
- [x] `dashboard.html` - дашборд
- [x] `sources.html` - источники
- [x] `filters.html` - фильтры
- [x] `profile.html` - профиль
- [x] `runbooks.html` - runbooks
- [x] `settings.html` - настройки
- [x] `vacancies.html` - вакансии
- [x] `applications.html` - отклики
- [x] `contacts.html` - контакты
- [x] `outreach.html` - рассылки
- [x] `stats.html` - статистика
- [x] `logs.html` - логи

#### 7. Промпты
Реализованы в `/app/prompts/`:
- [x] `hh_search_apply.md` - поиск и отклик на hh
- [x] `hh_stats.md` - статистика hh
- [x] `hirify_contacts.md` - получение контактов Hirify
- [x] `telegram_parse.md` - парсинг Telegram постов

#### 8. API Endpoints
- [x] Health check endpoint
- [x] Settings CRUD API
- [x] Sources management API
- [x] Filters management API
- [x] Profile management API
- [x] Runbooks management API
- [x] Vacancies API
- [x] Applications API
- [x] Contacts API
- [x] Outreach API
- [x] Stats API
- [x] Logs API

---

## Текущие проблемы и баги

### 🔴 Критические проблемы

#### 1. Настройки не сохраняются корректно
**Файл:** `/app/web/routes/settings.py`

**Проблема:** 
- При сохранении настроек используется проверка `if data.telegram_api_id:`, которая пропускает сохранение если значение `None` или пустая строка
- Фронтенд не отправляет секретные значения (они маскируются), поэтому при повторном сохранении все секретные поля теряются
- Механизм сохранения должен проверять `_set` флаги и не перезаписывать существующие секреты пустыми значениями

**Затронутые настройки:**
- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_READER_SESSION`
- `TELEGRAM_OUTREACH_SESSION`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALERTS_CHAT_ID`
- `LLM_API_KEY`

**Решение:**
- Изменить логику сохранения на проверку наличия нового значения
- Если приходит пустое значение, но_setting уже существует - не перезаписывать
- Добавить отдельный endpoint для обновления секретных полей

#### 2. Browser Agent Provider без объяснений
**Файл:** `/app/web/templates/settings.html`

**Проблема:**
- Выпадающий список с типами агентов не показывает что каждый тип делает
- Пользователь не понимает разницу между `manual`, `clipboard`, `browser_bridge`, `api`
- Нет визуальной индикации влияния выбора на работу системы

**Решение:**
- Добавить динамическое описание для каждого типа провайдера
- Показать плюсы/минусы каждого режима
- Добавить recommendations для разных use cases

#### 3. Отсутствие подробных гайдов по получению ключей
**Файл:** `/app/web/templates/settings.html`

**Проблема:**
- Есть только базовая инструкция для Telegram
- Нет инструкций для:
  - Получения LLM API ключей (OpenAI, Anthropic, OpenRouter)
  - Получения Chat ID для Telegram бота
  - Получения session string для Telegram user account
  - Настройки browser bridge

**Решение:**
- Добавить expandable секции с подробными гайдами
- Добавить ссылки на соответствующие сервисы
- Добавить скриншоты или пошаговые инструкции

#### 4. Отсутствуют тултипы с объяснениями
**Файл:** `/app/web/templates/settings.html`

**Проблема:**
- Нет объяснений зачем нужна каждая настройка
- Пользователь не понимает влияние настроек на работу системы

**Решение:**
- Добавить тултипы или help text для каждого поля
- Объяснить что происходит при изменении каждой настройки
- Добавить recommended values

---

## В процессе разработки

### ✅ Завершенные задачи (текущая фаза)

#### 1. Исправление сохранения настроек ✅
- [x] Изменить `SettingsRequest` модель для обработки partial updates
- [x] Обновить `save_settings` endpoint для правильной обработки секретов
- [x] Добавить механизм "keep existing" для пустых значений через `*_keep_existing` флаги
- [x] Обновить frontend для отправки правильных payload

#### 2. Улучшение UI настроек ✅
- [x] Добавить тултипы и help text для Browser Agent Provider
- [x] Добавить dynamic description для каждого типа Browser Agent (Manual, Clipboard, Browser Bridge, API)
- [x] Добавить expandable guides:
  - Как получить LLM API ключ (OpenAI, Anthropic, OpenRouter)
  - Как узнать Chat ID для Telegram
  - Как получить Session String для Telethon
- [x] Добавить рекомендации по выбору режима работы
- [x] Перевести описания на русский язык

#### 3. Unit тесты ✅
- [x] Тесты для settings routes (`tests/test_settings.py`)
  - test_get_settings_empty
  - test_save_llm_settings
  - test_save_telegram_settings
  - test_save_scheduler_settings
  - test_save_browser_agent_provider
  - test_keep_existing_flag_prevents_overwrite
  - test_settings_response_includes_set_flags

---

## Планы

### 📋 Следующие фазы

#### Phase 1: Исправление настроек (текущая) ✅ ЗАВЕРШЕНА
- [x] Анализ инцидента с сохранением
- [x] Fix backend logic (добавлены keep_existing флаги)
- [x] Fix frontend UI (обновлен saveSettings для отправки правильных данных)
- [x] Add tooltips and guides (добавлены подробные гайды для всех ключей)
- [x] Add unit tests (7 тестов для settings routes)

#### Phase 2: Telegram Integration
- [ ] Реализовать Telethon client
- [ ] CLI login команда
- [ ] Channel reader poller
- [ ] Incoming message monitor
- [ ] Alerts bot

#### Phase 3: Scheduler
- [ ] Настроить APScheduler
- [ ] Добавить jobs для всех источников
- [ ] Добавить UI для управления scheduler

#### Phase 4: Hardening
- [ ] Dry-run mode
- [ ] Error handling improvements
- [ ] Logging improvements
- [ ] Backup mechanism

---

## Технические детали

### Конфигурация базы данных
- **Type:** SQLite
- **Path:** `/workspace/job-autopilot/data/db.sqlite`
- **Миграции:** Auto create_all() (Alembic планируется)

### Переменные окружения
```env
APP_ENV=local
DEBUG=true
HOST=127.0.0.1
PORT=8000
DATABASE_URL=sqlite:///data/db.sqlite
LLM_PROVIDER=openai_compatible
DRY_RUN=true
```

### Зависимости
См. `/workspace/job-autopilot/requirements.txt`

---

## Известные ограничения

1. **Codex Integration:** Codex Chrome extension может не иметь стабильного API. Реализован только manual provider.
2. **Browser Bridge:** Экспериментальный режим, требует дополнительной разработки.
3. **Telegram Sessions:** Session strings должны генерироваться отдельно через Telethon.
4. **No Auth:** Локальное приложение без аутентификации (предназначено для одного пользователя).

---

## Чеклист для агентов

После реализации каждой фичи или фикса:

- [ ] Обновить этот файл (progress.md) с деталями изменений
- [ ] Добавить/обновить unit тесты
- [ ] Проверить что изменения не ломают существующий функционал
- [ ] Обновить документацию если нужно
- [ ] Убедиться что UI соответствует спецификации в readme.md

---

## Контакты и ресурсы

- **Спецификация:** `/workspace/readme.md`
- **Код:** `/workspace/job-autopilot/`
- **Документация:** README.md + этот файл

---

## Изменения в Phase 1 (Settings Fix)

### Backend изменения

#### Файл: `/app/web/routes/settings.py`

**Добавлено:**
- Новые поля в `SettingsRequest` для флагов `keep_existing`:
  - `llm_api_key_keep_existing`
  - `telegram_api_id_keep_existing`
  - `telegram_api_hash_keep_existing`
  - `telegram_reader_session_keep_existing`
  - `telegram_outreach_session_keep_existing`
  - `telegram_bot_token_keep_existing`
  - `telegram_alerts_chat_id_keep_existing`

**Изменено:**
- Логика `save_settings()` теперь проверяет флаги `keep_existing` перед перезаписью секретов
- Если `keep_existing=True` и значение пустое - существующее значение сохраняется

### Frontend изменения

#### Файл: `/app/web/templates/settings.html`

**Добавлено:**
1. **Dynamic Browser Agent Provider описание:**
   - Подробное описание каждого режима (Manual, Clipboard, Browser Bridge, API)
   - Плюсы/минусы каждого режима
   - Рекомендации по использованию
   
2. **Expandable Guides:**
   - LLM API Key Guide (OpenAI, Anthropic, OpenRouter)
   - Chat ID Guide (для личных чатов и групп/каналов)
   - Session String Guide (с примером кода на Python)

3. **Alpine.js state variables:**
   - `showLLMGuide`
   - `showChatIDGuide`
   - `showSessionGuide`

**Изменено:**
- Функция `saveSettings()` теперь отправляет payload с флагами `keep_existing`
- Опции Browser Agent Provider переведены на русский язык

### Tests

#### Файл: `/workspace/job-autopilot/tests/test_settings.py`

**Добавлено 7 unit тестов:**
1. `test_get_settings_empty` - проверка дефолтных значений
2. `test_save_llm_settings` - сохранение LLM конфигурации
3. `test_save_telegram_settings` - сохранение Telegram конфигурации
4. `test_save_scheduler_settings` - сохранение настроек планировщика
5. `test_save_browser_agent_provider` - сохранение browser agent provider
6. `test_keep_existing_flag_prevents_overwrite` - проверка работы флага keep_existing
7. `test_settings_response_includes_set_flags` - проверка наличия _set флагов в ответе

### Как запускать тесты

```bash
cd /workspace/job-autopilot
pytest tests/test_settings.py -v
```

