# 1. Используем официальный образ Python
# Используем slim-версию для уменьшения размера образа
FROM python:3.11-slim

# 2. Устанавливаем переменные окружения
# Предотвращает запись .pyc файлов
ENV PYTHONDONTWRITEBYTECODE 1
# Гарантирует, что вывод Python не буферизуется
ENV PYTHONUNBUFFERED 1

# 3. Создаем рабочую директорию внутри контейнера
WORKDIR /app

# 4. Устанавливаем системные зависимости
# build-essential и другие пакеты могут понадобиться для сборки некоторых Python-пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# 5. Копируем файл зависимостей и устанавливаем их
# Копируем сначала только этот файл, чтобы Docker мог кэшировать этот слой,
# если зависимости не менялись.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 6. Копируем весь остальной код проекта в рабочую директорию
COPY . .
