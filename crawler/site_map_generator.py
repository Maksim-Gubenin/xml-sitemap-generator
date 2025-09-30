import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List
from urllib.parse import urlparse
from xml.dom import minidom

logger = logging.getLogger(__name__)


class SitemapGenerator:
    """
    Генератор sitemap.xml файлов согласно стандарту sitemaps.org

    Особенности:
    - Создание валидных XML файлов sitemap
    - Экранирование специальных символов
    - Соответствие стандарту sitemap 0.9
    - Проверка на соответствие спецификации
    """

    def __init__(self, base_url: str):
        """
        Инициализация генератора карты сайта.

        Args:
            base_url: Базовый URL сайта для проверки принадлежности ссылок
        """

        self.base_domain = urlparse(base_url).netloc
        self.namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"

    def validate_url(self, url: str) -> bool:
        """
        Проверяет, принадлежит ли URL тому же домену, что и базовый URL.

        Args:
            url: URL для проверки

        Returns:
            True если URL принадлежит тому же домену
        """
        try:
            parsed_url = urlparse(url)
            return parsed_url.netloc == self.base_domain
        except Exception:
            return False

    def escape_xml_special_chars(self, text: str) -> str:
        """
        Экранирует специальные XML символы согласно стандарту.

        Args:
            text: Текст для экранирования

        Returns:
            Экранированная строка
        """
        escape_chars = {
            "&": "&amp;",
            "'": "&apos;",
            '"': "&quot;",
            ">": "&gt;",
            "<": "&lt;",
        }

        for char, replacement in escape_chars.items():
            text = text.replace(char, replacement)
        return text

    def generate_sitemap(
        self, urls: List[str], output_file: str = "sitemap.xml"
    ) -> str:
        """
        Генерирует файл sitemap.xml из списка URL.

        Args:
            urls: Список URL для включения в карту сайта
            output_file: Имя выходного файла

        Returns:
            Путь к созданному файлу

        Raises:
            ValueError: Если список URL пуст
        """
        if not urls:
            raise ValueError("Список URL не может быть пустым")

        # Создаем корневой элемент с namespace
        urlset = ET.Element("urlset")
        urlset.set("xmlns", self.namespace)

        # Добавляем schema location для валидации
        urlset.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        urlset.set(
            "xsi:schemaLocation", f"{self.namespace} {self.namespace}/sitemap.xsd"
        )

        # Множество, чтобы избежать дубликатов
        added_urls = set()

        for url in urls:
            # Проверяем и нормализуем URL
            if not self.validate_url(url):
                logging.warning(f"URL {url} пропущен - принадлежит другому домену")
                continue

            if url in added_urls:
                logging.debug(f"Дубликат URL пропущен: {url}")
                continue

            # Экранируем URL
            escaped_url = self.escape_xml_special_chars(url)

            # Создаем элемент URL
            url_element = ET.SubElement(urlset, "url")

            # Обязательный тег <loc>
            loc_element = ET.SubElement(url_element, "loc")
            loc_element.text = escaped_url

            # Необязательный тег <lastmod> - текущая дата
            lastmod_element = ET.SubElement(url_element, "lastmod")
            lastmod_element.text = datetime.now().strftime("%Y-%m-%d")

            # Необязательный тег <changefreq> - по умолчанию monthly
            changefreq_element = ET.SubElement(url_element, "changefreq")
            changefreq_element.text = "monthly"

            # Необязательный тег <priority> - по умолчанию 0.5
            priority_element = ET.SubElement(url_element, "priority")
            priority_element.text = "0.5"

            added_urls.add(url)

        # Создаем XML дерево
        rough_string = ET.tostring(urlset, encoding="utf-8")

        # Форматируем XML для читаемости
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ", encoding="utf-8")

        # Убираем лишние пустые строки из minidom
        pretty_xml_str = pretty_xml.decode("utf-8")
        pretty_xml_str = "\n".join(
            [line for line in pretty_xml_str.split("\n") if line.strip()]
        )

        # Записываем в файл
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(pretty_xml_str)

        logging.info(f"Sitemap создан: {output_file}")
        logging.info(f"Добавлено URL: {len(added_urls)}")

        return output_file

    def validate_sitemap(self, sitemap_file: str) -> bool:
        """
        Проверяет валидность созданного sitemap файла.

        Args:
            sitemap_file: Путь к файлу sitemap.xml

        Returns:
            True если файл валиден
        """
        try:
            tree = ET.parse(sitemap_file)
            root = tree.getroot()

            # Проверяем корневой элемент
            if root.tag != "{http://www.sitemaps.org/schemas/sitemap/0.9}urlset":
                logging.error("Неверный корневой элемент")
                return False

            # Проверяем наличие URL
            urls = root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}url")
            if not urls:
                logging.error("Нет URL в sitemap")
                return False

            logging.info(f"Sitemap валиден: {len(urls)} URL")
            return True

        except Exception as e:
            logging.error(f"Ошибка валидации sitemap: {e}")
            return False
