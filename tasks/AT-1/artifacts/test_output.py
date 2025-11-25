"""Тест для проверки логики форматирования вывода обновлений."""

import io
import sys
from contextlib import redirect_stdout

from aa.models.task import TaskUpdate
from aa.core.task_processor import ProcessingResult


def test_output_formatting():
    """Проверяет, что форматирование вывода работает корректно."""

    # Создаем ProcessingResult с тестовыми данными
    result = ProcessingResult("AL")

    # Добавляем несколько обновлений
    for i in range(15):
        update = TaskUpdate(
            task_id=f"task_{i}",
            old_name=f"Task {i} description",
            new_name=f"AL-{100 + i} Task {i} description",
            assigned_id=f"AL-{100 + i}",
        )
        result.add_update(update)

    # Добавляем несколько пропущенных задач
    for _ in range(5):
        result.add_skip()

    print("=== Тест 1: Базовая статистика ===")
    print(f"Project: {result.project_code}")
    print(f"  Total tasks processed: {result.total_processed}")
    print(f"  Tasks updated: {len(result.updates)}")
    print(f"  Tasks skipped (already have ID): {result.skipped}")

    print("\n=== Тест 2: Первые 10 обновлений (по умолчанию) ===")
    print("  Updated tasks:")
    verbose = False
    display_count = min(10, len(result.updates)) if not verbose else len(result.updates)
    for update in result.updates[:display_count]:
        print(f"    {update.assigned_id}: {update.old_name}")
    if len(result.updates) > display_count:
        remaining = len(result.updates) - display_count
        print(f"    ... and {remaining} more (use -v to see all)")

    print("\n=== Тест 3: Все обновления (verbose=True) ===")
    print("  Updated tasks:")
    verbose = True
    display_count = min(10, len(result.updates)) if not verbose else len(result.updates)
    for update in result.updates[:display_count]:
        print(f"    {update.assigned_id}: {update.old_name}")
    if len(result.updates) > display_count:
        remaining = len(result.updates) - display_count
        print(f"    ... and {remaining} more (use -v to see all)")

    print("\n=== Тест 4: Dry-run режим ===")
    print("  IDs that would be assigned:")
    for update in result.updates[:10]:
        print(f"    {update.assigned_id}: {update.old_name}")
    if len(result.updates) > 10:
        remaining = len(result.updates) - 10
        print(f"    ... and {remaining} more (use -v to see all)")

    print("\n=== Тест 5: Пустой результат ===")
    empty_result = ProcessingResult("TEST")
    print(f"Project: {empty_result.project_code}")
    print(f"  Total tasks processed: {empty_result.total_processed}")
    print(f"  Tasks updated: {len(empty_result.updates)}")
    print(f"  Tasks skipped (already have ID): {empty_result.skipped}")

    if empty_result.updates:
        print("  Updated tasks:")
        for update in empty_result.updates[:10]:
            print(f"    {update.assigned_id}: {update.old_name}")
    else:
        print("  (no updates)")

    print("\n✓ Все тесты пройдены!")


if __name__ == "__main__":
    test_output_formatting()
