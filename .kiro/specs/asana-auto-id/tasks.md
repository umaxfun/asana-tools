# Implementation Plan

- [ ] 1. Создать минимальный запускаемый CLI с командой init
  - Настроить pyproject.toml с зависимостями (click, httpx, pydantic, pyyaml) и entry point aa
  - Создать структуру aa/ с __init__.py, __main__.py, cli.py
  - Создать aa/commands/init.py с командой для создания шаблона .aa.yml
  - Реализовать создание конфига с полями asana_token, interactive, projects
  - Добавить проверку существования файла
  - Настроить базовое логирование
  - Подключить команду init к главной CLI группе
  - **Результат: можно запустить `uv run aa init` и получить .aa.yml**
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 10.1, 11.1, 13.2, 13.4_

- [ ] 3. Добавить Pydantic модели для конфига
  - Создать aa/models/__init__.py и aa/models/config.py
  - Реализовать ProjectConfig и Config с валидацией
  - Обновить команду init чтобы генерировать конфиг через модели
  - **Результат: `uv run aa init` создает валидный конфиг с правильной структурой**
  - _Requirements: 2.2, 10.5_
  
- [ ]* 3.1 Написать property тест для валидации конфигурации
  - **Property 2: Configuration validation rejects invalid configs**
  - **Validates: Requirements 2.2**

- [ ] 4. Добавить загрузку и валидацию конфига
  - Создать aa/utils/__init__.py и aa/utils/config_loader.py
  - Реализовать load_config() с валидацией через Pydantic
  - Добавить обработку ошибок (файл не найден, невалидный YAML)
  - Создать команду `aa validate` для проверки конфига
  - **Результат: `uv run aa validate` проверяет .aa.yml и выводит ошибки или OK**
  - _Requirements: 2.1, 2.2, 7.1, 7.2, 7.3_

- [ ] 5. Реализовать ID Manager и тестовую команду
  - Создать aa/core/__init__.py и aa/core/id_manager.py
  - Реализовать extract_id() с regex для извлечения ID
  - Реализовать has_id() для проверки наличия ID
  - Реализовать generate_next_root_id() и generate_next_subtask_id()
  - Создать команду `aa test-id <task_name> <project_code>` для тестирования извлечения ID
  - **Результат: `uv run aa test-id "PRJ-5 My task" PRJ` выводит "Found ID: PRJ-5"**
  - _Requirements: 2.4, 3.3, 3.4, 3.5_

- [ ]* 5.1 Написать property тесты для ID Manager
  - **Property 1: ID extraction and formatting consistency** (Requirements 2.4)
  - **Property 8: Root task ID format** (Requirements 3.3)
  - **Property 9: Subtask ID format** (Requirements 3.4)
  - **Property 10: Nested subtask ID format** (Requirements 3.5)

- [ ] 6. Добавить работу с кэшем
  - Создать aa/models/cache.py с ProjectCache и CacheData
  - Создать aa/utils/cache_manager.py с load_cache() и save_cache()
  - Добавить find_max_id() в IDManager
  - Создать команду `aa cache-info` для просмотра кэша
  - **Результат: `uv run aa cache-info` показывает содержимое .aa.cache.yaml**
  - _Requirements: 2.5, 2.7, 8.1, 8.2, 8.3, 8.4_

- [ ]* 6.1 Написать property тесты для кэша
  - **Property 4: Maximum ID detection** (Requirements 2.5)
  - **Property 6: Cache persistence round-trip** (Requirements 2.7, 3.8, 8.4)

- [ ] 7. Реализовать Asana API клиент и тестовую команду
  - Создать aa/models/task.py с AsanaTask и TaskUpdate
  - Создать aa/core/asana_client.py с AsanaClient
  - Реализовать get_project_tasks() с сортировкой
  - Реализовать get_task_subtasks()
  - Добавить retry логику и обработку ошибок
  - Создать команду `aa list-tasks <project_id>` для просмотра задач
  - **Результат: `uv run aa list-tasks 123456` выводит список задач из Asana**
  - _Requirements: 2.3, 11.3, 12.1, 12.3_

- [ ]* 7.1 Написать property тест для сортировки задач
  - **Property 3: Task sorting by creation date**
  - **Validates: Requirements 2.3**

- [ ] 8. Реализовать команду aa scan
  - Создать aa/commands/scan.py
  - Добавить опции --config, --project, --debug, --ignore-conflicts
  - Реализовать загрузку конфига, получение задач, извлечение ID
  - Добавить detect_conflicts() в IDManager
  - Реализовать обновление и сохранение кэша
  - Подключить к CLI
  - **Результат: `uv run aa scan` создает .aa.cache.yaml с найденными ID**
  - _Requirements: 2.1, 2.3, 2.4, 2.5, 2.6, 2.7, 4.1, 4.2, 9.1, 9.2, 9.3_

- [ ]* 8.1 Написать property тесты для scan
  - **Property 5: Conflict detection triggers error** (Requirements 2.6, 9.1)
  - **Property 17: Conflict resolution with ignore flag** (Requirements 9.2)
  - **Property 18: Duplicate ID detection** (Requirements 9.3)

- [ ] 9. Реализовать Task Processor и команду aa update с dry-run
  - Создать aa/core/task_processor.py с TaskProcessor
  - Реализовать process_task_hierarchy() для рекурсивной обработки
  - Добавить update_cache_for_id() в IDManager
  - Создать aa/commands/update.py с опцией --dry-run
  - Реализовать dry-run режим (только вывод, без изменений)
  - Подключить к CLI
  - **Результат: `uv run aa update --dry-run` показывает какие ID будут присвоены**
  - _Requirements: 3.2, 3.7, 5.1, 5.2, 5.3, 5.4_

- [ ]* 9.1 Написать property тесты для dry-run
  - **Property 7: Tasks with existing IDs are skipped** (Requirements 3.2)
  - **Property 14: Dry-run prevents modifications** (Requirements 5.1, 5.3, 5.4)

- [ ] 10. Добавить реальное обновление задач в aa update
  - Реализовать update_task_name() в AsanaClient
  - Добавить логику обновления задач в TaskProcessor
  - Реализовать сохранение кэша после обновления
  - Добавить параллельную обработку проектов через asyncio.gather()
  - **Результат: `uv run aa update` реально обновляет задачи в Asana и сохраняет кэш**
  - _Requirements: 3.1, 3.6, 3.8, 4.1, 4.2, 4.3, 4.4, 12.2, 12.3_

- [ ]* 10.1 Написать property тесты для update
  - **Property 11: Counter increment on ID assignment** (Requirements 3.7)
  - **Property 12: Project code consistency** (Requirements 4.3)
  - **Property 13: Project ID mapping** (Requirements 4.4)
  - **Property 15: Root task counter usage** (Requirements 8.1)
  - **Property 16: Subtask counter usage** (Requirements 8.2)

- [ ] 11. Добавить глобальные опции и финальную полировку
  - Добавить глобальные опции --config и --debug в CLI
  - Настроить логирование на основе --debug
  - Добавить обработку исключений
  - Удалить тестовые команды (validate, test-id, cache-info, list-tasks)
  - **Результат: `uv run aa --help` показывает только init, scan, update с опциями**
  - _Requirements: 6.1, 6.4, 7.1, 7.2_

- [ ] 12. Checkpoint - Убедиться что все работает
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 13. Написать интеграционные тесты
  - Настроить pytest и pytest-asyncio
  - Создать моки для AsanaClient
  - Написать тест для полного flow: init -> scan -> update
  - Написать тест для обработки иерархии задач
  - Написать тест для обработки ошибок API

- [ ]* 14. Добавить документацию
  - Создать README.md с установкой через uv
  - Добавить примеры использования команд
  - Документировать формат конфигурации и кэша
  - Описать формат ID и иерархию
