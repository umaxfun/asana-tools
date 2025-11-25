"""Проверка, что измененный модуль импортируется без ошибок."""

import sys
import importlib

try:
    # Импортируем измененный модуль
    from aa.commands import update

    print("✓ Модуль aa.commands.update успешно импортирован")

    # Проверяем наличие функции
    assert hasattr(update, "update_projects_async"), (
        "Функция update_projects_async не найдена"
    )
    print("✓ Функция update_projects_async найдена")

    # Проверяем наличие команды
    assert hasattr(update, "update"), "Команда update не найдена"
    print("✓ Команда update найдена")

    # Проверяем сигнатуру функции
    import inspect

    sig = inspect.signature(update.update_projects_async)
    params = list(sig.parameters.keys())

    print(f"\n  Параметры функции update_projects_async: {params}")

    expected_params = [
        "config",
        "project_code",
        "dry_run",
        "ignore_conflicts",
        "verbose",
    ]
    for param in expected_params:
        if param in params:
            print(f"  ✓ Параметр '{param}' присутствует")
        else:
            print(f"  ✗ Параметр '{param}' отсутствует")
            sys.exit(1)

    print("\n✓ Все проверки пройдены успешно!")

except ImportError as e:
    print(f"✗ Ошибка импорта: {e}")
    sys.exit(1)
except AssertionError as e:
    print(f"✗ Ошибка проверки: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Неожиданная ошибка: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
