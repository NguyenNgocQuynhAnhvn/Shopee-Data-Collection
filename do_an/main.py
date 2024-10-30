import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm
import pandas as pd
from config import config
from helpers import scroll_down, save_cookie, load_cookie, log_error, extract_data, extract_feedback
from time import sleep
from bs4 import BeautifulSoup
import os

def setup_driver():
    chrome_options = Options()
    chrome_options.headless = False
    chrome_options.add_argument('disable-infobars')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--no-sandbox')
    driver = uc.Chrome(options=chrome_options)  
    driver.maximize_window()
    return driver

def get_start_page(save_file, details):
    """Xác định trang bắt đầu cho các brand_url cụ thể dựa trên số sản phẩm đã lưu trong file CSV, dùng cột 'detail'."""
    if os.path.exists(save_file):
        df = pd.read_csv(save_file)
        num_products = 0
        for brand_url in details:
            df_brand = df['detail'].str.contains(brand_url, case=False, na=False)
            num_products += df_brand.sum()
        return num_products // 60  # Giả định mỗi trang có 60 sản phẩm
    else:
        return 0

def scrape_page(driver, url_page, save_file):
    try:
        driver.get(url_page)
    except Exception as e:
        print(f"Lỗi khi truy cập URL: {e}")
        sleep(5)
        driver.get(url_page)  
    sleep(10)
    scroll_down(driver, 1.0)
    products = driver.find_elements(By.XPATH, '//li[@data-sqe="item"]')
    print(f"Tìm thấy {len(products)} sản phẩm trên {url_page}")
    if not products:
        print("Không tìm thấy sản phẩm nào!")
        return

    links = []
    for box in products:
        try:
            link_product = box.find_element(By.XPATH, './/a[@class="contents"]').get_attribute('href')
            link_image = box.find_element(By.XPATH, './/div[@class="relative z-0 w-full pt-full"]//img').get_attribute('src')
            links.append((link_product, link_image))
        except Exception as e:
            print(f"Lỗi khi lấy link từ một sản phẩm: {e}")
            continue
    for link, img in tqdm(links, desc="Scraping products", ncols=100, colour='green'):
        driver.get(link)
        sleep(8)
        scroll_down(driver, 0.9)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        data = extract_data(driver, soup)
        data.update({"link_image": img, "link_product": link})
        pd.DataFrame([data]).to_csv(save_file, mode='a', header=not os.path.exists(save_file), index=False)
if __name__ == "__main__":
    driver = setup_driver()
    driver.get(config['base_url'])
    load_cookie(driver, 'cookies.pkl')
    driver.refresh()
    save_file = 'shopee.csv'
    start_page = get_start_page(save_file, config['details'])
    for brand_url in config['brand_urls']:
        start_page = get_start_page(save_file, config['details'])
        for page in range(start_page, 20):  
            url_page = f"{config['base_url']}/{brand_url}?page={page}"
            log_error(f'# Brand: {brand_url}, Page: {page}')
            scrape_page(driver, url_page, save_file)
