# Язык документации

## Правило языка для спецификаций

- Все документы спецификаций (requirements.md, design.md, tasks.md) ДОЛЖНЫ быть написаны на русском языке
- Технические термины могут оставаться на английском (например, GitHub Actions, PyInstaller, Homebrew)
- Названия команд, переменных и кода остаются на английском
- Комментарии в коде пишутся на английском

## Примеры

### Правильно ✅
```markdown
### Требование 1

**Пользовательская история:** Как пользователь macOS, я хочу установить aa через Homebrew...

#### Критерии приемки

1. WHEN пользователь выполняет `brew install aa` THEN Система SHALL установить бинарник
```

### Неправильно ❌
```markdown
### Requirement 1

**User Story:** As a macOS user, I want to install aa via Homebrew...

#### Acceptance Criteria

1. WHEN a user runs `brew install aa` THEN the System SHALL install the binary
```

## Исключения

- README.md может быть на английском (для международной аудитории)
- Код и комментарии в коде на английском
- Commit messages на английском
- Issue/PR descriptions могут быть на любом языке
