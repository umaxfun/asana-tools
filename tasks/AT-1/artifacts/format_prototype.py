"""Прототип функции форматирования деталей обновлений."""

from aa.models.task import TaskUpdate


def format_update_details(updates: list[TaskUpdate], limit: int | None = None) -> str:
    """
    Форматирует детали обновлений для вывода пользователю.

    Args:
        updates: Список обновлений задач
        limit: Максимальное количество обновлений для показа (None = все)

    Returns:
        Отформатированная строка с деталями
    """
    if not updates:
        return ""

    lines = []

    # Определяем количество обновлений для показа
    display_count = len(updates) if limit is None else min(limit, len(updates))

    # Форматируем каждое обновление
    for update in updates[:display_count]:
        lines.append(f"\n  {update.assigned_id}: {update.new_name}")
        lines.append(f"    Was: {update.old_name}")

    # Если есть еще обновления, которые не показываем
    if limit and len(updates) > limit:
        remaining = len(updates) - limit
        lines.append(f"\n  ... and {remaining} more task(s)")

    return "\n".join(lines)


def format_update_details_compact(
    updates: list[TaskUpdate], limit: int | None = None
) -> str:
    """
    Компактный формат вывода деталей обновлений.

    Args:
        updates: Список обновлений задач
        limit: Максимальное количество обновлений для показа (None = все)

    Returns:
        Отформатированная строка с деталями в компактном виде
    """
    if not updates:
        return ""

    lines = []

    # Определяем количество обновлений для показа
    display_count = len(updates) if limit is None else min(limit, len(updates))

    # Форматируем каждое обновление
    for update in updates[:display_count]:
        # Показываем только если название изменилось
        if update.old_name != update.new_name:
            lines.append(f"    {update.assigned_id}: {update.old_name}")

    # Если есть еще обновления, которые не показываем
    if limit and len(updates) > limit:
        remaining = len(updates) - limit
        lines.append(f"    ... and {remaining} more")

    return "\n".join(lines)


# Тестовые данные
if __name__ == "__main__":
    # Создаем тестовые TaskUpdate
    test_updates = [
        TaskUpdate(
            task_id="123",
            old_name="Implement feature X",
            new_name="AL-132 Implement feature X",
            assigned_id="AL-132",
        ),
        TaskUpdate(
            task_id="124",
            old_name="Fix bug Y",
            new_name="AL-133 Fix bug Y",
            assigned_id="AL-133",
        ),
        TaskUpdate(
            task_id="125",
            old_name="Update documentation",
            new_name="AL-134 Update documentation",
            assigned_id="AL-134",
        ),
        TaskUpdate(
            task_id="126",
            old_name="Refactor code",
            new_name="AL-135 Refactor code",
            assigned_id="AL-135",
        ),
        TaskUpdate(
            task_id="127",
            old_name="Add tests",
            new_name="AL-136 Add tests",
            assigned_id="AL-136",
        ),
    ]

    print("=== Тест 1: Полный формат (без лимита) ===")
    print(format_update_details(test_updates[:3]))

    print("\n\n=== Тест 2: Полный формат (с лимитом 2) ===")
    print(format_update_details(test_updates, limit=2))

    print("\n\n=== Тест 3: Компактный формат (без лимита) ===")
    print(format_update_details_compact(test_updates[:3]))

    print("\n\n=== Тест 4: Компактный формат (с лимитом 3) ===")
    print(format_update_details_compact(test_updates, limit=3))

    print("\n\n=== Тест 5: Пустой список ===")
    print(format_update_details([]))
    print("(должно быть пусто)")
