# Учет личных финансов

Приложение для учета и анализа личных финансов с графическим интерфейсом на Python.

## Требования

- Anaconda или Miniconda
- MySQL Server

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd finance-tracker
```

2. Создайте и активируйте conda-окружение:
```bash
conda env create -f environment.yml
conda activate finance
```

3. Создайте базу данных MySQL:
```bash
mysql -u root -p < Data/create_database.sql
```

4. Настройте конфигурацию:
- Откройте `Scripts/config.ini`
- Укажите параметры подключения к базе данных
- При необходимости измените настройки интерфейса

## Запуск

```bash
conda activate finance
python Scripts/main.py
```

## Функциональность

- Добавление доходов и расходов
- Категоризация транзакций
- Просмотр истории операций
- Генерация текстовых отчетов
- Визуализация данных (графики)
- Настраиваемый интерфейс

## Структура проекта
```
Work/
  ├── Data/          # SQL-скрипты и данные
  ├── Graphics/      # Сгенерированные графики
  ├── Library/       # Модули для работы с БД и отчетами
  ├── Output/        # Текстовые отчеты
  └── Scripts/       # Основной скрипт приложения
```

## Обновление окружения

При изменении зависимостей в `environment.yml`:
```bash
conda env update -f environment.yml
```