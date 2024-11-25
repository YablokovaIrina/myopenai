import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin


def init_driver():
    options = webdriver.ChromeOptions()
    options.headless = True
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def parse_page(driver, url):
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    data = {
        'url': url,
        'title': soup.title.string if soup.title else 'No Title',
        'text': extract_relevant_text(soup)
    }

    links = {urljoin(url, a['href']) for a in soup.find_all('a', href=True) if
             urlparse(urljoin(url, a['href'])).netloc == urlparse(url).netloc}

    return data, links


def extract_relevant_text(soup):
    main_section = soup.find('main', class_='nx-w-full nx-min-w-0 nx-max-w-6xl nx-px-6 nx-pt-4 md:nx-px-12')
    if not main_section:
        return []

    excluded_divs = main_section.find_all('div', class_=[
        'nextra-breadcrumb nx-mt-1.5 nx-flex nx-items-center nx-gap-1 nx-overflow-hidden nx-text-sm nx-text-gray-500 dark:nx-text-gray-400 contrast-more:nx-text-current',
        'nextra-callout nx-overflow-x-auto nx-mt-6 nx-flex nx-rounded-lg nx-border nx-py-2 ltr:nx-pr-4 rtl:nx-pl-4 contrast-more:nx-border-current contrast-more:dark:nx-border-current nx-border-blue-200 nx-bg-blue-100 nx-text-blue-900 dark:nx-border-blue-200/30 dark:nx-bg-blue-900/30 dark:nx-text-blue-200',
        'nx - w - full nx - min - w - 0 nx - leading - 7'
    ])

    excluded_paragraphs = [p for div in excluded_divs for p in div.find_all('p')]

    relevant_text = set()

    for p in main_section.find_all('p'):
        if p not in excluded_paragraphs and p.get_text(strip=True):
            relevant_text.add(p.get_text(separator='\n', strip=True))

    for span in main_section.find_all('span'):
        if 'nx-sr-only' in span.get('class', []) or span.find_parent(
                'ul', class_='nx-mt-6 nx-list-disc first:nx-mt-0 ltr:nx-ml-6 rtl:nx-mr-6')\
                or span.find_parent('div') in excluded_divs:
            continue
        text = span.get_text(separator='\n', strip=True)

        if text and "(opens in a new tab)" not in text:
            relevant_text.add(text)

    return list(relevant_text)


def crawl_site(driver, start_url):
    visited = set()
    to_visit = [start_url]
    site_data = []

    while to_visit:
        url = to_visit.pop(0)
        if url not in visited:
            print(f"Обрабатываем: {url}")
            visited.add(url)
            page_data, links = parse_page(driver, url)
            site_data.append(page_data)
            to_visit.extend(links - visited)

    return site_data


def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def main():
    start_url = 'https://www.promptingguide.ai/ru'
    driver = init_driver()

    try:
        site_data = crawl_site(driver, start_url)
        save_to_json(site_data, 'data.json')
        print("Данные успешно сохранены в 'data.json'")
    finally:
        driver.quit()


if __name__ == '__main__':
    main()
