# scraper.py
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm
import pandas as pd
from config import config
from helpers import scroll_down, save_cookie, load_cookie, log_error, extract_data, extract_feedback
from time import sleep
from bs4 import BeautifulSoup

def setup_driver():
    chrome_options = Options()
    chrome_options.headless = False
    chrome_options.add_argument('disable-infobars')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--no-sandbox')
    driver = uc.Chrome(chrome_options=chrome_options)
    driver.maximize_window()

    return driver


def scrape_page(driver, url_page, save_file):
    try:
        driver.get(link)
    except Exception as e:
        print(f"Lỗi khi truy cập URL: {e}")
        sleep(5)
        driver.get(link)  # Thử lại    sleep(15)
    scroll_down(driver, 1.0)
    # Lấy tất cả box sản phẩm
    products = driver.find_elements(By.XPATH, '//li[@data-sqe="item"]')
    print(f"Tìm thấy {len(products)} sản phẩm trên {url_page}")
    
    # Nếu không có sản phẩm, kết thúc hàm
    if not products:
        print("Không tìm thấy sản phẩm nào!")
        return

    # Lấy link sản phẩm và link ảnh
    links = []
    for box in products:
        try:
            # Lấy URL của sản phẩm và ảnh
            link_product = box.find_element(By.XPATH, './/a[@class="contents"]').get_attribute('href')
            link_image = box.find_element(By.XPATH, './/div[@class="relative z-0 w-full pt-full"]//img').get_attribute('src')
            links.append((link_product, link_image))
        except Exception as e:
            print(f"Lỗi khi lấy link từ một sản phẩm: {e}")
            continue
    
    # Trích xuất dữ liệu từ từng sản phẩm
    for link, img in tqdm(links, desc="Scraping products", ncols=100, colour='green'):
        driver.get(link)
        sleep(8)
        scroll_down(driver, 0.9)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # Lấy dữ liệu chi tiết sản phẩm
        data = extract_data(driver, soup)
        data.update({"link_image": img, "link_product": link})
        # Lưu dữ liệu vào file CSV
        pd.DataFrame([data]).to_csv(save_file, mode='a', header=not pd.io.common.file_exists(save_file), index=False)

if __name__ == "__main__":
    driver = setup_driver()
    driver.get(config['base_url'])
    load_cookie(driver, 'cookies.pkl')
    driver.refresh()

    save_file = 'shopee.csv'
    for page in range(20):
        log_error(f'# Page {page}')
        url_page = f"{config['base_url']}/{config['brand_url']}?page={page}"
        scrape_page(driver, url_page, save_file)
