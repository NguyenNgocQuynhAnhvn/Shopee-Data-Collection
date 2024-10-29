# helpers.py
import pickle
from time import sleep
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException 
from selenium.webdriver.common.by import By 


def scroll_down(driver, time_sleep=1):
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Cuộn xuống dưới cùng của trang
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(time_sleep)

        # Chờ trang tải thêm nội dung
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        # Nếu chiều cao trang không đổi, tức là đã tải hết nội dung
        if new_height == last_height:
            break
        last_height = new_height  # Cập nhật chiều cao trang mới


def save_cookie(driver, cookie_name):
    with open(cookie_name, 'wb') as file:
        pickle.dump(driver.get_cookies(), file)

def load_cookie(driver, cookie_name):
    with open(cookie_name, 'rb') as file:
        for cookie in pickle.load(file):
            driver.add_cookie(cookie)

def log_error(text, filename="log_error.txt"):
    with open(filename, "a", encoding='utf-8') as f:
        f.write(text + "\n")

def get_data(soup, selector):
    try:
        return soup.select(selector)[0].text
    except IndexError:
        return None

def info_shop(soup):
    res = {'Đánh giá': None, 'tỉ lệ phản hồi': None, 'tham gia': None, 'Sản phẩm': None, 'thời gian phản hồi': None, 'Người theo dõi': None}
    res['shop_name'] = get_data(soup, ".fV3TIn")
    brand = get_data(soup, ".ZUZ1FO") or ('mall' if get_data(soup, ".official-shop-new-badge") == '' else 'normal')
    res['shop_brand'] = brand
    for i in soup.select('.NGzCXN > .YnZi6x'):
        try:
            res[i.label.text] = i.span.text
        except AttributeError:
            pass
    return res

def extract_feedback(soup):
    feedback_count = 0
    feedbacks = []
    feedback_list = soup.find_all('div', class_='shopee-product-rating')
    for feedback in feedback_list:
        user_name = feedback.find('a').text if feedback.find('a') else "Ẩn danh"
        star_rating = len(feedback.find_all('svg', class_='icon-rating-solid--active'))
        comment_div = feedback.find('div', style=lambda v: v and 'color: rgba(0, 0, 0, 0.87)' in v)
        comment = " ".join(comment_div.stripped_strings) if comment_div else None
        feedbacks.append({'user_name': user_name, 'star_rating': star_rating, 'comment': comment})
    
    
    return feedbacks
def scrape_all_feedback(driver, max_pages=10):
    all_feedbacks = []
    page_count = 0  # Biến đếm trang

    while page_count < max_pages:
        # Lấy mã nguồn của trang hiện tại
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Gọi hàm extract_feedback để lấy feedback từ trang hiện tại
        feedbacks = extract_feedback(soup)
        all_feedbacks.extend(feedbacks)

        try:
            # Tìm và click vào nút "next page"
            next_button = driver.find_element(By.XPATH, "//button[contains(@class, 'shopee-icon-button shopee-icon-button--right ')]")
            next_button.click()
            sleep(2)  # Đợi một chút để trang tải xong
            
            page_count += 1  # Tăng biến đếm trang
        except NoSuchElementException:
            # Nếu không tìm thấy nút "next page", thoát khỏi vòng lặp
            break

    return all_feedbacks

def extract_data(driver, soup):
    res = {
        'name_product': get_data(soup, ".WBVL_7 > span"),
        'price_origin': get_data(soup, ".qg2n76"),
        'price': get_data(soup, ".G27FPf"),
        'rate': get_data(soup, ".dQEiAI"),
        'review_count': get_data(soup, ".e2p50f > div[class='F9RHbS']"),
        'sale_count': get_data(soup, ".AcmPRb"),
        'like_count': get_data(soup, ".w2JMKY > .rhG6k7"),
        'fee_delivery': get_data(soup, ".PZGOkt"),
        'is_flash_sale': 1 if get_data(soup, ".x7M8PV") else 0,
        'quantity': get_data(soup, ".OaFP0p > div > div:nth-child(2)"),
        'descibe': get_data(soup, ".e8lZp3"),
        'detail': get_data(soup, ".Gf4Ro0")
    }
    shop = info_shop(soup.find(class_="page-product__shop"))
    res.update(shop)
    res['feedbacks'] = scrape_all_feedback(driver, max_pages=10)
    return res
