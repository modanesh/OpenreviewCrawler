import numpy as np
import pandas as pd
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def extract_urls():
    options = Options()
    browser = webdriver.Chrome(options=options, executable_path=executable_path)
    browser.get(url)
    data_id_list = []
    done = False
    page = 1
    while not done:
        print('Page: {}'.format(page))
        for item in browser.find_elements_by_class_name("note"):
            data_id = item.get_attribute('data-id')
            data_id_list.append(data_id)
        if page < 10:
            browser.find_element_by_xpath('//*[@id="all-submissions"]/nav/ul/li[13]/a').click()
            sleep(5)
            page += 1
        else:
            done = True
    data_id_list = list(set(data_id_list))
    print('Number of submission: {}'.format(len(data_id_list)))
    with open('urls.txt', 'w') as urls_txt:
        for data_id in data_id_list:
            urls_txt.write('https://openreview.net/forum?id={}\n'.format(data_id))


def extract_reviews():
    options = Options()
    driver = webdriver.Chrome(options=options, executable_path=executable_path)
    driver.get(url)

    with open("urls.txt", "r") as f:
        lines = f.readlines()

    ratings = dict()
    decisions = dict()
    for link in lines:
        try:
            driver.get(link)
            xpath = '//div[@id="note_children"]//span[@class="note_content_value"]/..'
            cond = EC.presence_of_element_located((By.XPATH, xpath))
            WebDriverWait(driver, 60).until(cond)

            elems = driver.find_elements_by_xpath(xpath)
            assert len(elems), 'empty ratings'
            ratings[link] = pd.Series([
                x.text.split(': ')[1] for x in elems if x.text.startswith('Recommendation:')
            ], dtype=str)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(link, e)
            ratings[link] = pd.Series(dtype=str)
            decisions[link] = 'Unknown'
    df = pd.DataFrame(ratings).T
    df['decision'] = pd.Series(decisions)
    df.index.name = 'paper_id'
    df.to_csv('ratings.tsv', sep='\t')


def process_reviews(paper_id):
    df = pd.read_csv("ratings.tsv", sep='\t')
    score_map = {'Strong Reject': 0, 'Weak Reject': 1, 'Weak Accept': 2, 'Strong Accept': 3}
    scores = df.applymap(lambda s: score_map.get(s) if s in score_map else s).mean(axis=1)
    sorted_scores = scores.sort_values()
    paper_index = df.index[df['paper_id'] == paper_id].tolist()[0]
    paper_score = scores[df.index == paper_index].values[0]
    np_sorted_scores = sorted_scores.to_numpy()
    paper_range = np.where((np_sorted_scores == paper_score) == True)
    top_section = paper_range[0][0] / len(np_sorted_scores)
    print("chosen paper is in the top:", 1 - top_section)


if __name__ == '__main__':
    executable_path = '/usr/local/bin/chromedriver'  # path to your executable browser
    url = 'https://openreview.net/group?id=robot-learning.org/CoRL/2022/Conference#all-submissions'
    wanted_paper_id = "https://openreview.net/forum?id=XXXXXXXXXXXX\n"
    extract_urls()
    extract_reviews()
    process_reviews(wanted_paper_id)
