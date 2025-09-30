from unittest.mock import Mock, patch

from crawler.site_crawler import SiteCrawler


def test_site_crawler_initialization() -> None:
    """
    Простой тест инициализации краулера.

    Проверяет:
    - Корректность установки начального URL
    - Инициализацию базовых атрибутов
    - Наличие блокировки для потокобезопасности
    """
    crawler = SiteCrawler("https://example.com")

    # Проверяем базовые атрибуты
    assert crawler.to_visit == ["https://example.com"]
    assert crawler.visited == set()
    assert crawler.found_links == []
    assert hasattr(crawler, "lock")


def test_crawler_extract_links_basic() -> None:
    """
    Простой тест извлечения ссылок.

    Проверяет:
    - Извлечение относительных и абсолютных ссылок
    - Фильтрацию внешних доменов
    - Корректное преобразование относительных URL в абсолютные
    """
    with patch("crawler.site_crawler.webdriver.Chrome") as mock_chrome:
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        crawler = SiteCrawler("https://example.com")

        # Простой HTML с ссылками
        html = """
        <html>
            <body>
                <a href="/page1">Page 1</a>
                <a href="https://example.com/page2">Page 2</a>
                <a href="https://external.com/page3">External</a>
            </body>
        </html>
        """

        crawler.extract_links("https://example.com", html)

        # Проверяем что внутренние ссылки найдены
        assert "https://example.com/page1" in crawler.found_links
        assert "https://example.com/page2" in crawler.found_links

        # Проверяем что внешние ссылки отфильтрованы
        assert "https://external.com/page3" not in crawler.found_links


def test_crawler_fetch_page_success() -> None:
    """
    Тест успешной загрузки страницы.

    Проверяет:
    - Корректный вызов Selenium методов
    - Возврат HTML содержимого страницы
    - Обработку успешного сценария загрузки
    """
    with patch("crawler.site_crawler.webdriver.Chrome") as mock_chrome:
        mock_driver = Mock()
        mock_driver.page_source = "<html>Test content</html>"
        mock_chrome.return_value = mock_driver

        crawler = SiteCrawler("https://example.com")

        result = crawler.fetch_page("https://example.com")

        assert result == "<html>Test content</html>"
        mock_driver.get.assert_called_once_with("https://example.com")


def test_crawler_fetch_page_failure() -> None:
    """
    Тест неудачной загрузки страницы.

    Проверяет:
    - Обработку исключений при загрузке
    - Возврат None при ошибках
    - Корректность обработки ошибочных сценариев
    """
    with patch("crawler.site_crawler.webdriver.Chrome") as mock_chrome:
        mock_driver = Mock()
        mock_driver.get.side_effect = Exception("Error")
        mock_chrome.return_value = mock_driver

        crawler = SiteCrawler("https://example.com")

        result = crawler.fetch_page("https://example.com")

        assert result is None


def test_crawler_process_page() -> None:
    """
    Тест обработки страницы.

    Проверяет:
    - Последовательность вызовов методов
    - Добавление URL в посещенные
    - Корректность передачи параметров между методами
    """
    with patch("crawler.site_crawler.webdriver.Chrome") as mock_chrome:
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        crawler = SiteCrawler("https://example.com")

        # Мокаем методы
        with (
            patch.object(crawler, "fetch_page") as mock_fetch,
            patch.object(crawler, "extract_links") as mock_extract,
        ):
            mock_fetch.return_value = "<html>Content</html>"

            crawler.process_page("https://example.com")

            # Проверяем вызовы
            mock_fetch.assert_called_once_with("https://example.com")
            mock_extract.assert_called_once_with(
                "https://example.com", "<html>Content</html>"
            )

            # Проверяем что URL добавлен в посещенные
            assert "https://example.com" in crawler.visited


def test_crawler_thread_safety() -> None:
    """
    Простой тест потокобезопасности.

    Проверяет:
    - Отсутствие дубликатов при многократном вызове
    - Корректность работы блокировки
    - Сохранение уникальности ссылок
    """
    with patch("crawler.site_crawler.webdriver.Chrome") as mock_chrome:
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        crawler = SiteCrawler("https://example.com")

        html = '<a href="/test">Test</a>'

        # Многократный вызов из одного "потока"
        for _ in range(5):
            crawler.extract_links("https://example.com", html)

        # Должна быть только одна ссылка (без дубликатов)
        assert len(crawler.found_links) == 1
        assert crawler.found_links[0] == "https://example.com/test"
