# Документ дизайна

## Обзор

Система дистрибуции для CLI инструмента `aa` основана на современном подходе с использованием PyPI и UV. Основной метод использования - `uvx aa-cli` для разового запуска или `uv tool install aa-cli` для постоянной установки.

**Ключевой принцип:** Максимальная простота - никаких бинарников, никакого Homebrew, никакого сложного CI/CD, только стандартный Python packaging через PyPI.

## Архитектура

### Компоненты и их взаимодействие

```
Developer                    PyPI                        End User
    |                          |                             |
    | git tag v0.1.0          |                             |
    | git push --tags         |                             |
    |------------------------>|                             |
    |                          |                             |
    |                   [GitHub Actions]                     |
    |                          |                             |
    |                   uv build                             |
    |                          |                             |
    |                   Publish to PyPI                      |
    |                          |                             |
    |                   [PyPI: aa-cli]                       |
    |                          |                             |
    |                          |     uvx aa-cli              |
    |                          |<----------------------------|
    |                          |                             |
    |                          |     Download & Run          |
    |                          |---------------------------->|
    |                          |                             |
    |                          |     OR: uv tool install     |
    |                          |<----------------------------|
    |                          |                             |
    |                          |     Install globally        |
    |                          |---------------------------->|
```

### Репозитории

**Основной репозиторий (`umaxfun/aa`):**
- Локальный путь: `/Users/umaxfun/prj/asana-tools`
- GitHub URL: `https://github.com/umaxfun/asana-tools`
- Содержит:
  - Исходный код приложения (`aa/`)
  - Конфигурация проекта (`pyproject.toml`)
  - GitHub Actions workflow (`.github/workflows/publish.yml`)
  - Документация (`README.md`)

**PyPI:**
- Package URL: `https://pypi.org/project/aa-cli/`
- Package name: `aa-cli`
- Command name: `aa`

## Компоненты и интерфейсы

### 1. pyproject.toml

**Назначение:** Конфигурация Python пакета

**Ключевые секции:**

```toml
[project]
name = "aa-cli"
version = "0.1.0"
description = "Automatic human-readable ID assignment for Asana tasks"
requires-python = ">=3.12"
dependencies = [
    "click>=8.1.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0.0",
]

[project.scripts]
aa = "aa.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Принципы:**
- Имя пакета `aa-cli` для избежания trademark проблем
- Команда остается `aa` для удобства
- Минимальные зависимости
- Использование современного build backend (hatchling)

### 2. GitHub Actions Workflow

**Файл:** `.github/workflows/publish.yml`

**Триггер:**
```yaml
on:
  push:
    tags:
      - 'v*'
```

**Jobs:**

**Job: Publish to PyPI**
1. Checkout кода
2. Setup Python 3.12
3. Install UV
4. Build package: `uv build`
5. Publish to PyPI: `uv publish` (с PYPI_TOKEN)
6. Create GitHub Release

**Принципы:**
- Один простой job
- Использование UV для всех операций
- Автоматическая публикация при создании тега
- GitHub Release создается после успешной публикации на PyPI

### 3. Методы установки

**Метод 1: uvx (рекомендуемый)**
```bash
# Разовый запуск
uvx aa-cli init
uvx aa-cli scan
uvx aa-cli update

# UV автоматически:
# 1. Скачивает пакет из PyPI
# 2. Создает временный venv
# 3. Запускает команду
# 4. Кеширует для последующих запусков
```

**Метод 2: uv tool install (для постоянного использования)**
```bash
# Установка
uv tool install aa-cli

# Теперь команда aa доступна глобально
aa init
aa scan
aa update

# Обновление
uv tool upgrade aa-cli

# Удаление
uv tool uninstall aa-cli
```

**Принципы:**
- uvx - для пробы и разового использования (рекомендуется)
- uv tool - для постоянных пользователей
- Оба метода дают идентичный результат

## Модели данных

### PyPI Package Metadata

**Структура:**
```python
{
    "name": "aa-cli",
    "version": "0.1.0",
    "description": "Automatic human-readable ID assignment for Asana tasks",
    "author": "umaxfun",
    "license": "MIT",  # или другая
    "requires_python": ">=3.12",
    "dependencies": [
        "click>=8.1.0",
        "httpx>=0.27.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0.0"
    ],
    "entry_points": {
        "console_scripts": [
            "aa=aa.cli:main"
        ]
    }
}
```

### GitHub Release

**Структура:**
```
Release v0.1.0
├── Tag: v0.1.0
├── Title: "Release v0.1.0"
├── Body: Auto-generated release notes
└── Assets: (опционально, не обязательны)
```

**Принципы:**
- Release создается после успешной публикации на PyPI
- Assets не нужны (пакет уже на PyPI)
- Release notes генерируются автоматически

## Correctness Properties

*Свойство - это характеристика или поведение, которое должно выполняться для всех валидных выполнений системы - по сути, формальное утверждение о том, что система должна делать. Свойства служат мостом между человеко-читаемыми спецификациями и машинно-проверяемыми гарантиями корректности.*

### Property 1: Package name consistency
*For any* установленный пакет, имя пакета на PyPI должно быть `aa-cli`, а команда в терминале должна быть `aa`
**Validates: Requirements 3.2, 3.3**

### Property 2: Installation method equivalence
*For any* метод установки (uvx, uv tool, homebrew), функциональность команды `aa` должна быть идентичной
**Validates: Requirements 9.5**

### Property 3: Version consistency
*For any* релиз, версия в pyproject.toml, версия на PyPI, версия в GitHub Release и версия выводимая командой `aa --version` должны совпадать
**Validates: Requirements 7.5**

### Property 4: Dependency isolation
*For any* метод установки, зависимости пакета не должны конфликтовать с другими установленными пакетами
**Validates: Requirements 2.5**

### Property 5: Cross-platform compatibility
*For any* поддерживаемая платформа (Linux, macOS, Windows), все команды должны работать идентично
**Validates: Requirements 9.1, 9.2, 9.3**

## Обработка ошибок

### Ошибки публикации на PyPI

**Сценарий:** GitHub Actions не может опубликовать на PyPI

**Обработка:**
1. Workflow падает с ошибкой
2. GitHub Release не создается
3. Разработчик получает уведомление
4. Необходимо исправить проблему и пересоздать тег

**Принципы:**
- Fail-fast: если PyPI публикация упала, не создавать Release
- Логи ошибок доступны в GitHub Actions
- Возможность повторной публикации после исправления

### Ошибки установки

**Сценарий:** Пользователь не может установить пакет

**Возможные причины:**
1. UV не установлен → Инструкция по установке UV
2. Python версия < 3.12 → Сообщение о требуемой версии
3. Проблемы с сетью → Повторить попытку
4. PyPI недоступен → Подождать или использовать зеркало

**Принципы:**
- Четкие сообщения об ошибках
- Инструкции по устранению в документации
- Fallback методы не нужны (PyPI достаточно надежен)

## Стратегия тестирования

### Unit тесты

**Что тестируем:**
- Основную функциональность CLI команд
- Парсинг конфигурации
- Логику работы с Asana API

**Не тестируем:**
- Процесс публикации на PyPI (проверяется вручную)
- Установку через разные методы (проверяется вручную)

### Integration тесты

**Что тестируем:**
- Полный flow команд (init → scan → update)
- Работу с реальными конфигурационными файлами

### Manual тесты (обязательны перед релизом)

**Checklist:**
1. ✅ Собрать пакет локально: `uv build`
2. ✅ Установить локально: `uv tool install dist/aa_cli-0.1.0-py3-none-any.whl`
3. ✅ Проверить команду: `aa --version`
4. ✅ Проверить основные команды: `aa init`, `aa scan`
5. ✅ Удалить: `uv tool uninstall aa-cli`
6. ✅ Создать тег и проверить автоматическую публикацию
7. ✅ Проверить установку из PyPI: `uvx aa-cli --version`
8. ✅ Обновить Homebrew formula и проверить установку

**Принципы:**
- Каждый релиз должен быть проверен вручную
- Автоматические тесты не заменяют ручную проверку
- Пользователь должен физически убедиться что все работает

## Workflow релиза

### Шаг 1: Подготовка
1. Обновить версию в `pyproject.toml`
2. Обновить `CHANGELOG.md` (если есть)
3. Закоммитить изменения
4. Запустить тесты локально

### Шаг 2: Создание релиза
1. Создать тег: `git tag v0.1.0`
2. Запушить тег: `git push origin v0.1.0`
3. GitHub Actions автоматически:
   - Соберет пакет
   - Опубликует на PyPI
   - Создаст GitHub Release

### Шаг 3: Проверка
1. Проверить что пакет появился на PyPI
2. Проверить что `uvx aa-cli --version` работает
3. Проверить GitHub Release создан

**Принципы:**
- Весь процесс полностью автоматизирован
- Никаких ручных шагов после создания тега
- Пользователи получают обновление немедленно
