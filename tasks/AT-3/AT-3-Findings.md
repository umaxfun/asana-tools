# AT-3: Технические находки

## Asana API: Проблема с эндпоинтом `/workspaces/{gid}/projects`

**Проблема:** При запросе списка проектов без параметра `limit` API возвращает ошибку 400:

```json
{
  "errors": [
    {
      "message": "The result is too large. You should use pagination (may require specifying a workspace)!"
    }
  ]
}
```

**Решение:** Всегда использовать параметр `limit` для пагинации:

```python
params = {
    "opt_fields": "gid,name",
    "archived": "false",  # Серверная фильтрация
    "limit": 100          # Обязательно!
}
```

**Тестирование через curl:**

```bash
# Без limit - ошибка 400
curl "https://app.asana.com/api/1.0/workspaces/{gid}/projects?opt_fields=gid,name,archived"

# С limit - работает
curl "https://app.asana.com/api/1.0/workspaces/{gid}/projects?limit=100&archived=false"
```

## Asana API: Rate Limiting при массовых запросах

**Проблема:** При сканировании 100+ проектов параллельно (`asyncio.gather(*tasks)`) API блокирует запросы на 120 секунд с кодом 429.

**Решение 1 - Ограничение параллелизма:**

```python
semaphore = asyncio.Semaphore(5)  # Максимум 5 одновременных запросов

async def process_project(project):
    async with semaphore:
        code = await detect_project_code(client, project["gid"])
        await asyncio.sleep(0.5)  # Задержка между запросами
        return project
```

**Решение 2 - Пропуск сканирования для больших воркспейсов:**

```python
if len(all_projects) >= 100:
    # Пропустить сканирование, вернуть только первый проект
    all_projects = all_projects[:1]
```

## Asana API: Отсутствие фильтрации "избранных" проектов

**Проблема:** Нет способа получить через API только проекты, отображаемые в sidebar пользователя.

**Проверенные варианты:**

- `/users/me/favorites?resource_type=project` - требует workspace, возвращает пустой список
- `/user_task_lists` - несуществующий эндпоинт
- Параметры `members`, `owner` в `/projects` - не помогают

**Вывод:** Фильтрация избранных проектов недоступна через API. Пользователь должен вручную выбрать нужные проекты из конфига.

## Click: Конфликт локальных и глобальных опций

**Проблема:** Если команда имеет локальную опцию с тем же именем, что и глобальная, возникает конфликт.

**Решение:** Дублировать опцию на уровне команды и обновлять логирование вручную:

```python
@click.command()
@click.option("-v", "--verbose", count=True, help="Increase verbosity")
def my_command(verbose: int):
    if verbose > 0:
        level = logging.INFO if verbose == 1 else logging.DEBUG
        logging.getLogger().setLevel(level)
```

**Альтернатива:** Использовать только глобальные опции, но их нужно указывать ДО имени команды:

```bash
# Работает с глобальной опцией
aa-cli -vv init

# Работает с локальной опцией
aa-cli init -vv
```

## Выводы

1. **Всегда используйте параметр `limit` при запросах к Asana API** для избежания ошибки "result too large"
2. **Ограничивайте параллелизм** при массовых запросах через `asyncio.Semaphore`
3. **Проверяйте количество элементов** перед сканированием и пропускайте операцию для больших датасетов
4. **Asana API не предоставляет фильтрацию избранных проектов** - нужен ручной выбор
5. **Дублируйте критичные опции CLI** на уровне команд для удобства использования
