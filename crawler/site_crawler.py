import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class SiteCrawler:
    """
    Web-crawler для сканирования сайтов и сбора ссылок.

    Особенности:
    - Обработка страниц в много поточном режиме
    - Поддержка сайтов с загрузкой контента
        через JavaScript с помощью Selenium
    - Защита от дубликатов и зацикливания
    """

    def __init__(self, start_url: str) -> None:
        """
        Инициализация краулера.

        Args:
            start_url: Список начальных URL для сканирования

        Attributes:
            visited: Множество уже обработанных URL
            to_visit: Очередь URL для обработки
            found_links: Список всех найденных уникальных ссылок
            lock: Блокировка для потокобезопасности
            driver: Selenium WebDriver для работы с JavaScript
        """
        self.visited: Set[str] = set()
        self.to_visit: List[str] = [start_url]
        self.found_links: List[str] = []
        self.lock: threading.Lock = threading.Lock()

        # Настройка Selenium WebDriver для работы в фоновом режиме
        chrome_options = Options()
        # Запуск без графического интерфейса
        chrome_options.add_argument("--headless")
        # Отключение песочницы для снижения вероятности ошибок
        chrome_options.add_argument("--no-sandbox")
        # Уменьшает вероятность сбоев при нехватке памяти
        chrome_options.add_argument("--disable-dev-shm-usage")
        # Инициализация web driver
        self.driver: webdriver.Chrome = webdriver.Chrome(options=chrome_options)

    def fetch_page(self, url: str) -> Optional[str]:
        """
        Загружает содержимое веб-страницы с выполнением JavaScript.

        Процесс:
        1. Переход по указанному URL
        2. Ожидание загрузки DOM
        3. Дополнительное время для выполнения JavaScript
        4. Возврат итогового HTML

        Args:
            url: URL страницы для загрузки

        Returns:
            HTML-код страницы или None в случае ошибки
        """

        try:
            self.driver.get(url)
            # Ожидание загрузки содержимого body
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            # Дополнительная пауза для выполнения JavaScript
            time.sleep(2)
            return self.driver.page_source
        except Exception as e:
            logging.error(f"Не удалось загрузить {url}: {e}")
            return None

    def extract_links(self, url: str, html: str) -> None:
        """
        Извлекает все ссылки со страницы и добавляет их в очередь для обработки.

        Процесс:
        1. Парсинг HTML и поиск всех тегов <a> с атрибутом href
        2. Преобразование относительных ссылок в абсолютные
        3. Фильтрация нежелательных ссылок (не web-схемыб
            якорные ссылки на ту же страницу)
        4. Потокобезопасное добавление уникальных ссылок в рабочие очереди

        Args:
            url: Базовый URL страницы, используется для преобразования
                 относительных ссылок в абсолютные
            html: HTML-код страницы для парсинга

        Фильтрация ссылок:
            - Отсеиваются не-HTTP/HTTPS схемы (mailto:, javascript:, tel: и т.д.)
            - Игнорируются якорные ссылки, ведущие на ту же страницу (#section)
            - Опционально можно ограничиться только основным доменом
        """

        soup = BeautifulSoup(html, "html.parser")
        base_domain = urlparse(url).netloc
        current_page_path = urlparse(url).path

        for anchor in soup.find_all("a", href=True):
            href_value = anchor.get("href")
            if not href_value or not isinstance(href_value, str):
                continue

            link: str = href_value
            full_url: str = urljoin(url, link)
            parsed = urlparse(full_url)

            # 1. Фильтруем не-HTTP ссылки
            if parsed.scheme not in ("http", "https"):
                continue

            # 2. Фильтруем якорные ссылки.
            # Пропускаем если: есть фрагмент И тот же домен И тот же путь
            # urlparse("scheme://netloc/path;parameters?query#fragment")
            # ParseResult(
            #            scheme='scheme', netloc='netloc',
            #            path='/path;parameters', params='',
            #            query='query', fragment='fragment'
            #            )
            if (
                parsed.fragment
                and parsed.netloc == base_domain
                and parsed.path == current_page_path
            ):
                continue

            # 3. Ограничиваемся только основным доменом
            if parsed.netloc != base_domain:
                continue

            # Потокобезопасное добавление
            with self.lock:
                if (
                    full_url not in self.visited
                    and full_url not in self.to_visit
                    and full_url not in self.found_links
                ):
                    self.found_links.append(full_url)
                    self.to_visit.append(full_url)
                    logging.info(f"Найдена ссылка: {full_url}")

    def process_page(self, url: str) -> None:
        """
        Парсинг страницы: загружает контент и извлекает ссылки.

        Args:
            url: URL страницы для обработки

        Процесс:
            1. Логирование начала обработки
            2. Загрузка HTML с JavaScript
            3. Извлечение ссылок из загруженного контента
            4. Отметка URL как обработанного
        """
        logging.info(f"Обрабатывается: {url}")

        html: Optional[str] = self.fetch_page(url)
        if html:
            self.extract_links(url, html)

        with self.lock:
            self.visited.add(url)

    def crawl(self) -> List[str]:
        """
        Метод для запуска процесса сканирования сайта.

        Алгоритм работы:
        1. Создание пула потоков
        2. Обработка URL из очереди
        3. Ограничение общего количества обрабатываемых страниц
        4. Автоматическое добавление новых найденных ссылок в очередь

        Returns:
            Список всех найденных уникальных ссылок
        """

        max_pages: int = 1000

        # Использование ThreadPoolExecutor для многопоточной обработки
        with ThreadPoolExecutor(max_workers=3) as executor:
            while self.to_visit and len(self.visited) < max_pages:
                url: Optional[str] = None

                # Пока один поток работает со списком,
                # другие потоки ждут, когда lock будет снят
                with self.lock:
                    if self.to_visit:
                        url = self.to_visit.pop(0)
                        if url in self.visited:
                            continue
                        self.visited.add(url)

                if url:
                    executor.submit(self.process_page, url)

                # Пауза для снижения нагрузки на целевой сервер
                time.sleep(1)

        # Корректное завершение работы WebDriver
        self.driver.quit()
        return self.found_links
