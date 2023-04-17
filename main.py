import datetime
import json
import os.path
from time import sleep

from selenium import webdriver
from selenium.common import StaleElementReferenceException
from selenium.webdriver.common.by import By
from csv import writer
from selenium.webdriver.chrome.options import Options

if not os.path.exists('./scraped_html'):
    os.mkdir('./scraped_html')

page = 1
scrape_on_page = 0
page_iterator_index = 0

# instance of Options class allows
# us to configure Headless Chrome
options = Options()

# this parameter tells Chrome that
# it should be run without UI (Headless)
options.add_argument('--headless')


browser = webdriver.Chrome()
browser.get('https://service.ariba.com/Discovery.aw/109560019/aw?awh=r&awssk=_2tQV4wZ')
sleep(5)
browser.find_element(By.XPATH, "//*[contains(text(), 'All Categories')]").click()

sleep(10)


with open('progress.json', 'r') as f:
    data = json.loads(f.read())
    page = data['page']
    scrape_on_page = data['scrape_on_page']


def is_scraped(position):
    global page
    global scrape_on_page
    global page_iterator_index

    if page > page_iterator_index:
        return True

    if page == page_iterator_index and position < data['scrape_on_page']:
        return True

    return False


done = False


def save_to_scv():
    row = list()

    stats_nums = [x.text for x in browser.find_elements(By.CLASS_NAME, "statsDataContainer")]
    activity_data = [x.text for x in browser.find_elements(By.XPATH, "//li[@class='adap-ADSPB-list']")]
    seller_profile = [x.text for x in browser.find_elements(By.CLASS_NAME, "SellerProfileDataValue")]
    try:
        row.append(browser.find_element(By.CLASS_NAME, "SupplierHeaderProfileName").text)
    except Exception as e:
        row.append("")

    try:
        row.append(browser.find_element(By.CLASS_NAME, "SupplierHeaderAddress").text)
    except Exception as e:
        row.append("")
    try:
        row.append(next(filter(lambda x: 'Transaction Spend' in x, stats_nums)).replace('\nTransaction Spend', ''))
    except Exception as e:
        row.append("")

    try:
        row.append(next(filter(lambda x: 'Transacting Relationships:' in x, activity_data)).replace('Transacting Relationships:', ''))
    except Exception as e:
        row.append("")

    try:
        row.append(next(filter(lambda x: 'Transaction Count:' in x, activity_data)).replace('Transaction Count:', ''))
    except Exception as e:
        row.append("")

    try:
        row.append(next(filter(lambda x: 'Business Type:' in x, seller_profile)).replace('Business Type:', ''))
    except Exception as e:
        row.append("")

    try:
        row.append(next(filter(lambda x: 'State of Incorporation:' in x, seller_profile)).replace('State of Incorporation:', ''))
    except Exception as e:
        row.append("")

    try:
        row.append(next(filter(lambda x: 'Type of Org:' in x, seller_profile)).replace('Type of Org:', ''))
    except Exception as e:
        row.append("")
    try:
        row.append(browser.find_element(By.CLASS_NAME, "SellerProfileText").text)
    except Exception as e:
        row.append("")

    try:
        row.append(next(filter(lambda x: 'Subscription:' in x, activity_data)).replace('Subscription:', ''))
    except Exception as e:
        row.append("")

    with open('scraped_data.csv', 'a') as f:
        writer_obj = writer(f)
        writer_obj.writerow(row)


while not done:
    to_scrape = browser.find_elements(By.CLASS_NAME, "SupplierSearchResultTitle")

    loaded_current_page = False

    while not loaded_current_page:
        try:
            browser.find_element(By.ID, "currentpage")
            loaded_current_page = True
        except Exception as e:
            continue

    if page_iterator_index + 1 != int(browser.find_element(By.ID, "currentpage").text):
        print("Fix current page")
        page_iterator_index = int(browser.find_element(By.ID, "currentpage").text)

    while len(to_scrape) == 0 and int(browser.find_element(By.ID, "currentpage").text) != page_iterator_index + 1:
        to_scrape = browser.find_elements(By.CLASS_NAME, "SupplierSearchResultTitle")
        sleep(1)

    print(f"Work on page {page_iterator_index}")

    for x in range(len(to_scrape)):
        print(f"Item {x}")
        if not is_scraped(x):
            _to_scrape = browser.find_elements(By.CLASS_NAME, "SupplierSearchResultTitle")

            if len(_to_scrape) == 0:
                sleep(10)
                _to_scrape = browser.find_elements(By.CLASS_NAME, "SupplierSearchResultTitle")

            _to_scrape[x].click()

            loaded_single_page = False
            loaded_single_page_tried = 0
            while not loaded_single_page:
                loaded_single_page_tried += 1
                loaded_single_page = len(browser.find_elements(By.CLASS_NAME, "SupplierHeaderProfileName")) > 0
                sleep(1)
                if loaded_single_page_tried > 5:
                    break

            if not loaded_single_page:
                continue

            try:
                browser.find_element(By.CLASS_NAME, "SupplierHeaderProfileName").text
                with open(f'scraped_html/{browser.find_element(By.CLASS_NAME, "SupplierHeaderProfileName").text.replace("/", "_")}.html', 'w') as f:
                    f.write(browser.page_source)
            except Exception as e:
                with open(f'scraped_html/MissingTitle_{page_iterator_index}_{x}.html', 'w') as f:
                    f.write(browser.page_source)
            save_to_scv()

            browser.find_element(By.XPATH, "//td[contains(text(), 'Done')]").click()

        scrape_on_page += 1

        if not is_scraped(x):
            with open('progress.json', 'w') as f:
                f.write(json.dumps({"page": page_iterator_index, "scrape_on_page": x}))



    scrape_on_page = 0
    page_iterator_index += 1


    print("Try do next")
    tried = 0
    while len(browser.find_elements(By.XPATH, "//div[@id='next']")) == 0:
        tried += 1
        sleep(1)

        if tried > 10:
            done = True
            break

    try:
        browser.find_elements(By.XPATH, "//div[@id='next']")[0].click()
    except StaleElementReferenceException as e:
        done_next = False
        while not done_next:
            try:
                browser.find_elements(By.XPATH, "//div[@id='next']")[0].click()
            except Exception as e:
                continue
            done_next = True
    except Exception as e:
        done = True
        break

    print(f"Finish page {page_iterator_index}")
    sleep(4)


browser.close()


