# helpers.py
import pickle
from time import sleep
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException





def scroll_down(driver, pct=0.55, time_sleep=1):
    try:
        # Chờ cho phần tử body của trang xuất hiện
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        height = driver.execute_script("return document.body.scrollHeight")

        for i in range(0, int(height * pct), 300):
            driver.execute_script(f"window.scrollTo(0, {i});")
            sleep(time_sleep)

    except Exception as e:
        print(f"Lỗi khi cuộn trang: {e}")

        
# def scroll_down_product(driver, time_sleep=1):
#     last_height = driver.execute_script("return document.body.scrollHeight")

#     while True:
#         # Cuộn xuống dưới cùng của trang
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         sleep(time_sleep)

#         # Chờ trang tải thêm nội dung
#         new_height = driver.execute_script("return document.body.scrollHeight")
        
#         # Nếu chiều cao trang không đổi, tức là đã tải hết nội dung
#         if new_height == last_height:
#             break
#         last_height = new_height  # Cập nhật chiều cao trang mới


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

def get_data(soup, selector_string):
    try:
        data = soup.select(selector_string)
        return data[0].text
    except:
        return None

def info_shop(soup):
    res = {'Đánh giá': None,
            'tỉ lệ phản hồi': None,
            'tham gia': None,
            'Sản phẩm': None,
            'thời gian phản hồi': None,
            'Người theo dõi': None}
    res['shop_name'] = get_data(soup, ".fV3TIn")
    brand = get_data(soup, ".ZUZ1FO") # shop yêu thích
    if not brand:
        brand = 'mall' if get_data(soup, ".official-shop-new-badge")=='' else 'normal' # shop mall
    res['shop_brand'] = brand
    try:
        for i in soup.select('.NGzCXN > .YnZi6x'):
            try:
                res[i.label.text] = i.span.text
            except:
                pass
    except:
                pass
    return res

def extract_feedback(soup) -> list:
    """
    Hàm này để trích xuất feedback (tên người đánh giá, số sao, bình luận)
    """
    feedbacks = []
    # Tìm tất cả các thẻ chứa thông tin đánh giá
    feedback_list = soup.find_all('div', class_='shopee-product-rating')
    
    for feedback in feedback_list:
        try:
            author = feedback.find('div', class_='shopee-product-rating__main')
            if author.find('a'):
                user_name = author.find('a').text

            elif author.find('div'):
                user_name = author.find('div').text.strip()

            else:
                user_name = "Ẩn danh"
        except:
            user_name = "Ẩn danh"
        
        try:
            # Lấy số sao đánh giá bằng cách đếm số SVG có class 'icon-rating-solid--active'
            star_elements = feedback.find_all('svg', class_='icon-rating-solid--active')
            star_rating = len(star_elements)
        except:
            star_rating = None
        
        try:
            # Lấy bình luận
            # Bình luận nằm trong một thẻ <div> với style chứa 'color: rgba(0, 0, 0, 0.87)'
            comment_div = feedback.find('div', style=lambda value: value and 'margin-top: 0.75rem;' in value)
            if comment_div:
                # Loại bỏ các thẻ <span> để chỉ lấy phần bình luận
                for span in comment_div.find_all('span'):
                    span.decompose()
                comment = comment_div.get_text(separator=' ', strip=True)
            else:
                comment = None
        except:
            comment = None
        
        # Thêm feedback vào danh sách
        feedbacks.append({
            'user_name': user_name,
            'star_rating': star_rating,
            'comment': comment
        })
    
    return feedbacks

def scrape_all_feedback(driver, max_pages=30):
    all_feedbacks = []
    page_count = 0  # Biến đếm trang

    while page_count < max_pages:
        # Lấy mã nguồn của trang hiện tại
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Gọi hàm extract_feedback để lấy feedback từ trang hiện tại
        feedbacks = extract_feedback(soup)
        all_feedbacks.extend(feedbacks)

        try:
            # Tìm và cuộn tới nút "next page" để nó nằm trong viewport
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'shopee-icon-button shopee-icon-button--right')]"))
            )
            ActionChains(driver).move_to_element(next_button).perform()
            
            # Nhấp vào nút "next page" bằng JavaScript để tránh lỗi chặn nhấp chuột
            driver.execute_script("arguments[0].click();", next_button)
            sleep(2)  # Đợi một chút để trang tải xong

            page_count += 1  # Tăng biến đếm trang

        except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
            # Nếu gặp lỗi, thoát khỏi vòng lặp và chuyển sang link tiếp theo
            break

    return all_feedbacks

# def scrape_all_feedback(driver, max_pages=30):
#     all_feedbacks = []
#     page_count = 0  # Biến đếm trang

#     while page_count < max_pages:
#         # Lấy mã nguồn của trang hiện tại
#         soup = BeautifulSoup(driver.page_source, 'html.parser')
        
#         # Gọi hàm extract_feedback để lấy feedback từ trang hiện tại
#         feedbacks = extract_feedback(soup)
#         all_feedbacks.extend(feedbacks)

#         try:
#             # Tìm và click vào nút "next page"
#             next_button = driver.find_element(By.XPATH, "//button[contains(@class, 'shopee-icon-button shopee-icon-button--right')]")
#             next_button.click()
#             sleep(2)  # Đợi một chút để trang tải xong
            
#             page_count += 1  # Tăng biến đếm trang
#         except NoSuchElementException:
#             # Nếu không tìm thấy nút "next page", thoát khỏi vòng lặp
#             break

#     return all_feedbacks

def extract_data(driver, soup) -> dict:
    '''hàm này để trích xuất dữ liệu'''
    res = {}
    # lấy tên sản phẩm
    res['name_product'] = get_data(soup, ".WBVL_7 > span") #soup.find(class_="WBVL_7").span.text
    # lấy giá
    res['price_origin'] = get_data(soup, ".ZA5sW5")
    res['price'] = get_data(soup, ".IZPeQz B67UQ0")
    res['rate'] = get_data(soup, ".dQEiAI")
    res['review_count'] = get_data(soup, ".e2p50f > div[class='F9RHbS']")
    res['sale_count'] = get_data(soup, ".AcmPRb")
    res['like_count'] = get_data(soup, ".w2JMKY > .rhG6k7")
    res['fee_delivery'] = get_data(soup, ".PZGOkt")
    res['is_flash_sale'] = 1 if get_data(soup, ".x7M8PV") else 0
    res['quantity'] = get_data(soup, ".OaFP0p > div > div:nth-child(2)")
    res['descibe'] = get_data(soup, ".e8lZp3")
    res['detail'] = get_data(soup, ".Gf4Ro0")
    shop = info_shop(soup.find(class_="page-product__shop"))
    res.update(shop)
    
    res['feedbacks'] = scrape_all_feedback(driver, max_pages=30)

    return res


