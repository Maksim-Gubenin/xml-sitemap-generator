import logging

from crawler import SiteCrawler, SitemapGenerator

logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO)


if __name__ == "__main__":
    """
    Пример использования web-crawler с генерацией sitemap.xml.

    Этапы:
    1. Сканирование сайта и сбор ссылок
    2. Генерация sitemap.xml
    3. Валидация созданного файла
    """
    start_url = "https://asmu.ru/"

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
