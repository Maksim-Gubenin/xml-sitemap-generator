"""
Пакет инструментов для сканирования веб-сайтов и создания карты сайта.
"""

from crawler.site_crawler import SiteCrawler
from crawler.site_map_generator import SitemapGenerator

__all__ = ["SiteCrawler", "SitemapGenerator"]
