import logging
import sys
from urllib.parse import urlparse

from crawler import SiteCrawler, SitemapGenerator

logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO)


def get_user_url() -> str:
    """
    Получает URL от пользователя с валидацией.

    Returns:
        Валидный URL для сканирования
    """

    print("XML Sitemap Generator")
    print("=" * 40)

    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        url = sys.argv[1]
        print(f"Используется URL из аргументов: {url}")
        return url

    print("Введите URL сайта для сканирования (например: https://example.com)")
    print("Или нажмите Enter для использования примера (https://asmu.ru)")

    while True:
        user_input = input("URL: ").strip()

        if not user_input:
            default_url = "https://asmu.ru"
            print(f"Используется пример: {default_url}")
            return default_url

        try:
            parsed = urlparse(user_input)
            if parsed.scheme and parsed.netloc:
                return user_input
            else:
                print("Неверный формат URL. Используйте: https://example.com")
        except Exception:
            print("Ошибка в URL. Попробуйте еще раз.")


if __name__ == "__main__":
    """
    Пример использования web-crawler с генерацией sitemap.xml.

    Этапы:
    1. Сканирование сайта и сбор ссылок
    2. Генерация sitemap.xml
    3. Валидация созданного файла
    """
    start_url = get_user_url()

    # Парсинг сайта
    crawler = SiteCrawler(start_url)
    links = crawler.crawl()

    print(f"\nНайдено ссылок: {len(links)}")

    # Генерация sitemap
    sitemap_generator = SitemapGenerator(start_url)

    try:
        sitemap_file = sitemap_generator.generate_sitemap(
            links, output_file="sitemap.xml"
        )

        # Проверяем валидность
        if sitemap_generator.validate_sitemap(sitemap_file):
            print(f"Sitemap успешно создан: {sitemap_file}")
            print(f"URL в sitemap: {len(links)}")
        else:
            print("Ошибка при создании sitemap")

    except Exception as e:
        print(f"Ошибка: {e}")
