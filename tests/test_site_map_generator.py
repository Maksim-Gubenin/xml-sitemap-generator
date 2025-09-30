import tempfile
from pathlib import Path

import pytest

from crawler.site_map_generator import SitemapGenerator


def test_sitemap_generator_initialization() -> None:
    """
    Простой тест инициализации генератора sitemap.

    Проверяет:
    - Корректное извлечение домена из базового URL
    - Установку стандартного namespace
    """
    generator = SitemapGenerator("https://example.com")

    # Проверяем базовые атрибуты
    assert generator.base_domain == "example.com"
    assert generator.namespace == "http://www.sitemaps.org/schemas/sitemap/0.9"


def test_sitemap_generator_validate_url() -> None:
    """
    Тест валидации URL.

    Проверяет:
    - Принятие внутренних URL (того же домена)
    - Отклонение внешних URL (других доменов)
    """
    generator = SitemapGenerator("https://example.com")

    # Внутренние URL должны проходить валидацию
    assert generator.validate_url("https://example.com/page") is True
    assert generator.validate_url("https://example.com/about") is True

    # Внешние URL должны не проходить валидацию
    assert generator.validate_url("https://google.com") is False
    assert generator.validate_url("https://github.com") is False


def test_sitemap_generator_escape_xml_chars() -> None:
    """
    Тест экранирования XML символов.

    Проверяет корректное преобразование:
    - Амперсанда (& → &amp;)
    - Кавычек (" → &quot;)
    - Угловых скобок (< → &lt;, > → &gt;)
    """
    generator = SitemapGenerator("https://example.com")

    # Тестируем экранирование
    assert generator.escape_xml_special_chars("test&test") == "test&amp;test"
    assert generator.escape_xml_special_chars('"quote"') == "&quot;quote&quot;"
    assert generator.escape_xml_special_chars("<tag>") == "&lt;tag&gt;"
    assert generator.escape_xml_special_chars("normal") == "normal"


def test_sitemap_generate_empty_urls() -> None:
    """
    Тест генерации sitemap с пустым списком URL.

    Проверяет:
    - Вызов исключения при пустом списке URL
    - Корректность текста исключения
    """
    generator = SitemapGenerator("https://example.com")

    # Должна быть ошибка при пустом списке
    with pytest.raises(ValueError, match="Список URL не может быть пустым"):
        generator.generate_sitemap([])


def test_sitemap_generate_basic() -> None:
    """
    Базовый тест генерации sitemap.

    Проверяет:
    - Создание XML файла
    - Наличие базовой XML структуры
    - Включение указанных URL в sitemap
    """
    generator = SitemapGenerator("https://example.com")

    # Создаем временный файл
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
        temp_file = f.name

    try:
        urls = [
            "https://example.com/",
            "https://example.com/about",
            "https://example.com/contact",
        ]

        # Генерируем sitemap
        result_file = generator.generate_sitemap(urls, temp_file)

        # Проверяем что файл создан
        assert Path(result_file).exists()

        # Проверяем базовое содержимое
        with open(result_file, "r", encoding="utf-8") as f:
            content = f.read()

        assert "<?xml" in content
        assert "<urlset" in content
        assert "https://example.com/" in content

    finally:
        # Удаляем временный файл
        Path(temp_file).unlink(missing_ok=True)


def test_sitemap_validate_correct_file() -> None:
    """
    Тест валидации корректного sitemap файла.

    Проверяет:
    - Принятие валидного sitemap файла
    - Корректность XML структуры
    """
    generator = SitemapGenerator("https://example.com")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
        temp_file = f.name

    try:
        urls = ["https://example.com/"]
        generator.generate_sitemap(urls, temp_file)

        # Должен пройти валидацию
        assert generator.validate_sitemap(temp_file) is True

    finally:
        Path(temp_file).unlink(missing_ok=True)


def test_sitemap_validate_incorrect_file() -> None:
    """
    Тест валидации некорректного файла.

    Проверяет:
    - Отклонение некорректного XML файла
    - Обработку файлов с неправильной структурой
    """
    generator = SitemapGenerator("https://example.com")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
        # Пишем некорректный XML
        f.write("not xml content")
        temp_file = f.name

    try:
        # Должен не пройти валидацию
        assert generator.validate_sitemap(temp_file) is False

    finally:
        Path(temp_file).unlink(missing_ok=True)


def test_sitemap_filter_external_urls() -> None:
    """
    Тест фильтрации внешних URL.

    Проверяет:
    - Включение внутренних URL в sitemap
    - Исключение внешних URL из sitemap
    - Корректность фильтрации по домену
    """
    generator = SitemapGenerator("https://example.com")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
        temp_file = f.name

    try:
        urls = [
            "https://example.com/internal",  # Должен остаться
            "https://google.com/external",  # Должен быть отфильтрован
            "https://example.com/another",  # Должен остаться
        ]

        result_file = generator.generate_sitemap(urls, temp_file)

        with open(result_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Проверяем что внутренние URL есть
        assert "https://example.com/internal" in content
        assert "https://example.com/another" in content

        # Проверяем что внешние URL отфильтрованы
        assert "https://google.com/external" not in content

    finally:
        Path(temp_file).unlink(missing_ok=True)
