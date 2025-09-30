# 🕷️ XML Sitemap Generator

Веб-краулер для автоматического сканирования сайтов и генерации sitemap.xml файлов.

## 🚀 Возможности

- **Автоматическое сканирование** сайтов с поддержкой JavaScript
- **Многопоточная обработка** страниц для высокой производительности  
- **Фильтрация ссылок** (только HTTP/HTTPS, внутренние страницы)
- **Генерация валидных sitemap.xml** файлов согласно стандарту
- **Валидация результатов** на соответствие спецификации

## 📦 Установка
```bash
    git clone https://github.com/Maksim-Gubenin/xml-sitemap-generator
    cd xml-sitemap-generator
```

### Требования
- Python 3.12+
- Chrome/Chromium браузер
- Poetry (для управления зависимостями)

### Установка зависимостей
```bash
  poetry install
```

🎯 Использование

Способ 1: Интерактивный режим
```bash
poetry run python main.py
```

Способ 2: Указание URL в аргументах
```bash
poetry run python main.py https://example.com
```

⚙️ Настройка
Ограничение количества страниц
В site_crawler.py измените max_pages в методе crawl():

```python
def crawl(self) -> List[str]:
    max_pages: int = 1000  # Измените на нужное значение
```