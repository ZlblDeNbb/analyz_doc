# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY . .

# Устанавливаем системные зависимости для работы с PDF и ODT
RUN apt-get update && apt-get install -y \
    libpoppler-cpp-dev \
    libreoffice \
    && apt-get clean

# Устанавливаем зависимости проекта
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем Streamlit
RUN pip install streamlit

# Указываем порт для Streamlit
EXPOSE 8501

# Команда для запуска приложения
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.enableCORS=false"]
