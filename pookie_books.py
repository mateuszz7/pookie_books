import argparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import re

options = Options()
options.headless = True

def get_static_page(url):
    html_text = requests.get(url).text
    return BeautifulSoup(html_text, 'html.parser')

def get_dynamic_page(url):
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    html = driver.page_source
    driver.quit()
    return BeautifulSoup(html, 'html.parser')

def get_dynamic_page_wait(url, by, name):
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    WebDriverWait(driver, 5).until_not(
        EC.presence_of_element_located((by, name))
    )
    html = driver.page_source
    driver.quit()
    return BeautifulSoup(html, 'html.parser')

def get_dynamic_page_sleep(url):
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    import time
    time.sleep(3)
    html = driver.page_source
    driver.quit()
    return BeautifulSoup(html, 'html.parser')

def get_dynamic_page_loop(url, word):
    import time
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    html = driver.page_source
    i = 0
    while word not in html and i != 3:
        time.sleep(1)
        html = driver.page_source
        i += 1
    driver.quit()
    return BeautifulSoup(html, 'html.parser')

def check_in_prism(title, author, council, lib_url):
    # hardcoded
    query = '/items?query=title%3A%28{}%29+AND+author%3A%28{}%29&facet%5B0%5D=nature%3A%22novel%22&facet%5B0%5D=language%3A"eng"'.format(title, author)
    book_query = "/items/"

    # get books
    parsed = get_static_page(lib_url + query)
    book_ids = []
    if parsed.find("div", {"id": "searchResults"}):
        book_ids = [result.get("value") for result in parsed.find("div", {"id": "searchResults"}).find_all("input", {"name": "bib_id"})]

    # get book avaliability
    availability = {}
    for id in book_ids:
        url = lib_url + book_query + id
        book_page = get_static_page(url)
        available = book_page.find("p", {"class": "branches"})
        if available and 'no copies' not in available.get_text().lower():
            availability[url] = available.get_text()

    # print results if any
    if availability:
        print(council.upper())
        for url, text in availability.items():
            print('-', text)
            print(url)
        print()

def check_in_sirs(title, author, council, lib_url):
    # hardcoded
    query = f'/search/results?qu=&qu=TITLE%3D"{title}"&qu=AUTHOR%3D"{author}"+&te=ILS&av=0&h=1&te=ILS&FRBR=1'

    # get results
    parsed = get_dynamic_page_wait(lib_url + query, By.CLASS_NAME, "smallSpinner")
    availability = []

    if parsed.find("span", {"id": "availableDiv0"}):
        i = 0
        while parsed.find("span", {"id": f"availableDiv{i}"}):
            availability.append(parsed.find("span", {"id": f"availableDiv{i}"}).find_all("span")[-1].get_text())
            i += 1
    elif parsed.find("span", {"id": "holdsCountDiv0"}):
        i = 0
        while parsed.find("span", {"id": f"holdsCountDiv{i}"}):
            availability.append(parsed.find("span", {"id": f"holdsCountDiv{i}"}).find_all("span")[-1].get_text())
            i += 1
    elif parsed.find("span", {"id": "ercAvailableDiv_hitlist0"}):
        i = 0
        while parsed.find("span", {"id": f"ercAvailableDiv_hitlist{i}"}):
            availability.append(parsed.find("span", {"id": f"ercAvailableDiv_hitlist{i}"}).find_all("span")[-1].get_text())
            i += 1
    elif parsed.find_all(class_="displayElementText text-p highlightMe PARENT_AVAILABLE"):
        for found in parsed.find_all(class_="displayElementText text-p highlightMe PARENT_AVAILABLE"):
            availability.append(found.get_text()[1:])
    # single ones
    elif parsed.find("span", {"id": "ercAvailableDiv_detail0"}):
        availability.append(parsed.find("span", {"id": "ercAvailableDiv_detail0"}).find_all("span")[-1].get_text())
    elif parsed.find("span", {"id": "totalAvailable0"}):
        availability.append(parsed.find("span", {"id": "totalAvailable0"}).get_text())

    # print results if any
    if availability:
        print(council.upper())
        for available in availability:
            print('- Available', available)
            print(lib_url + query)
        print()

def check_in_spydus(title, author, council, lib_url):
    # hardcoded
    if 'ALLENQ' in lib_url:
        query = f'?ENTRY1_NAME=TI&ENTRY1=%22{title}%22&ENTRY1_TYPE=K&ENTRY1_OPER=%2B&ENTRY2_NAME=CR&ENTRY2=%22{author}%22&ENTRY2_TYPE=K&ENTRY2_OPER=-&ENTRY3_NAME=BS&ENTRY3=%5Belectronic+resource%5D&ENTRY3_TYPE=K&ENTRY3_OPER=%2B&ENTRY4_NAME=BS&ENTRY4=&ENTRY4_TYPE=K&ENTRY4_OPER=%2B&PD=&CD=&LANG=ENG*English&NRECS=100&SORTS=HBT.SOVR&SEARCH_FORM=%2Fcgi-bin%2Fspydus.exe%2FMSGTRN%2FWPAC%2FALL&_SPQ=1&FORM_DESC=All+resources+-+Advanced+search&ISGLB=0&csrf=undefined'
    else:
        query = f'?ENTRY1_NAME=TI&ENTRY1=%22{title}%22&ENTRY1_TYPE=K&ENTRY1_OPER=%2B&ENTRY2_NAME=AU&ENTRY2=%22{author}%22&ENTRY2_TYPE=K&ENTRY2_OPER=-&ENTRY3_NAME=BS&ENTRY3=%5Belectronic+resource%5D&ENTRY3_TYPE=K&ENTRY3_OPER=%2B&ENTRY4_NAME=DDC&ENTRY4=&ENTRY4_OPER=%2B&PD=&ADD=&LANG=ENG*English&NRECS=100&SORTS=HBT.SOVR&SEARCH_FORM=%2Fcgi-bin%2Fspydus.exe%2FMSGTRN%2FWPAC%2FCOMB&_SPQ=1&FORM_DESC=Library+catalogue+-+Advanced+search&ISGLB=0&csrf=undefined'

    # get results
    parsed = get_dynamic_page(lib_url + query)
    availability = {}

    base_url = lib_url.split('/cgi-bin')[0]
    for found in parsed.find_all("a", {"data-target": "#holdingsDlg"}):
        a_parsed = get_static_page(base_url + found['href'])
        availability[base_url + found['href']] = len(re.findall('Available', a_parsed.text))

    # print results if any
    if availability:
        print(council.upper())
        for url, text in availability.items():
            print('- Available', text)
            print(url)
        print()

def check_in_multiple(title, author, council, lib_url):
    # hardcoded
    query = f'/search?term={title}&field=TITLE&facets=%255B%257B%2522Name%2522%253A%2522LANGUAGE%2522%252C%2522Selected%2522%253A%255B%2522ENG%2522%255D%257D%252C%257B%2522Name%2522%253A%2522FORMAT%2522%252C%2522Selected%2522%253A%255B%2522BOOK%2522%255D%257D%255D&listview=true&sort=any&limit=&page=1'

    # get results
    parsed = get_dynamic_page_loop(lib_url + query, '"ltr"')
    availability = []

    if parsed.find_all("div", {"dir": "ltr"}):
        for found in parsed.find_all("div", {"dir": "ltr"})[0].find_all("span"):
            if "No" not in found.get_text():
                availability.append(found.get_text())

    # print results if any
    if availability:
        print(council.upper())
        for available in availability:
            print('- Available', available)
            print(lib_url + query)
        print()

def check_in_war(title, author, council, lib_url):
    # hardcoded
    query = f'/search?p_p_id=searchResult_WAR_arenaportlet&p_p_lifecycle=1&p_p_state=normal&p_r_p_arena_urn%3Aarena_facet_queries=&p_r_p_arena_urn%3Aarena_search_query=%28mediaClass_index%3Ahardback+OR+mediaClass_index%3Apaperback%29+AND+language_index%3Aeng+AND+%28author_index%3A%22{author}%22+OR+contributor_index%3A%22{author}%22%29+AND+%28title_index%3A%22{title}%22+OR+titleMain_index%3A%22{title}%22%29&p_r_p_arena_urn%3Aarena_search_type=solr&p_r_p_arena_urn%3Aarena_sort_advice=field%3DRelevance%26direction%3DDescending'

    # get results
    parsed = get_static_page(lib_url + query)
    availability = {}

    urls = []
    for found in parsed.find_all("div", {"class": "arena-record-title"}):
        urls.append(found.find("a")['href'])

    for url in urls:
        a_parsed = get_dynamic_page_wait(url, By.CSS_SELECTOR, '[alt="Loading..."]')
        total = [int(found.find("span", {"class": "arena-value"}).get_text()) for found in a_parsed.find_all("div", {"class": "arena-holding-nof-available-for-loan"})]
        if total:
            availability[url] = sum(total)

    # print results if any
    if availability:
        print(council.upper())
        for url, text in availability.items():
            print('- Available', text)
            print(url)
        print()

def check_in_primo(title, author, council, lib_url):
    # hardcoded
    title = title.replace('+', '%20')
    query = f'/search?query=title,contains,"{title}",AND&query=creator,contains,"{author}",AND&pfilter=lang,exact,eng,AND&pfilter=rtype,exact,books,AND&tab=BL_Available&search_scope=BL_Available&sortby=rank&vid=44BL_INST:BLL01&lang=en&mode=advanced&offset=0'

    # get results
    parsed = get_dynamic_page_loop(lib_url + query, 'results-per-page')
    availability = {}

    for found in parsed.find_all("h3", {"class": "item-title"}):
        availability[found.find('a')['href']] = "Should be available"

    # print results if any
    if availability:
        print(council.upper())
        for url, text in availability.items():
            print('-', text)
            print(url)
        print()

prism_urls = {
    'islingtion': 'https://prism.librarymanagementcloud.co.uk/islington',
    'barnet': 'https://prism.librarymanagementcloud.co.uk/barnet',
    'wandsworth': 'https://prism.librarymanagementcloud.co.uk/wandsworth',
    'greenwich': 'https://prism.librarymanagementcloud.co.uk/royalgreenwich',
    'bromley': 'https://prism.librarymanagementcloud.co.uk/bromley',
}

sirs_urls = {
    'barbican and community': 'https://col.ent.sirsidynix.net.uk/client/en_GB/default',
    'barking and dagenham': 'https://llc.ent.sirsidynix.net.uk/client/en_GB/barking-and-dagenham',
    'hillingdon': 'https://hldn.ent.sirsidynix.net.uk/client/en_GB/public',
    'brent': 'https://llc.ent.sirsidynix.net.uk/client/en_GB/brent',
    'hammersmith and fulham': 'https://tlc.ent.sirsidynix.net.uk/client/en_GB/lbhf',
    'newham': 'https://llc.ent.sirsidynix.net.uk/client/en_GB/newham',
    'redbridge': 'https://llc.ent.sirsidynix.net.uk/client/en_GB/redbridge',
    'kensington and chelsea': 'https://trib.ent.sirsidynix.net.uk/client/en_GB/rbkc',
    'hackney': 'https://llc.ent.sirsidynix.net.uk/client/en_GB/hackney',
    'westminster': 'https://elibrary.westminster.gov.uk/client/en_GB/wcc',
    'hounslow': 'https://libraries.hounslow.gov.uk/client/en_GB/hounslow',
    'havering': 'https://libraries.havering.gov.uk/client/en_GB/havering/',
    'kingston': 'https://llc.ent.sirsidynix.net.uk/client/en_GB/kingston',
}

spydus_urls = {
    'camden': 'https://camden.spydus.co.uk/cgi-bin/spydus.exe/ENQ/WPAC/BIBENQ',
    'southwark': 'https://southwark.spydus.co.uk/cgi-bin/spydus.exe/ENQ/WPAC/BIBENQ',
    'richmond': 'https://richmond.spydus.co.uk/cgi-bin/spydus.exe/ENQ/WPAC/ALLENQ',
}

multiple_urls = {
    'enfield': 'https://libraries.enfield.gov.uk',
    'tower hamlets': 'https://ideastore.towerhamlets.gov.uk/',
    'harrow': 'https://libraries.harrow.gov.uk',
    'ealing': 'https://libraries.ealing.gov.uk',
    'haringey': 'https://libraries.haringey.gov.uk',
    'waltham forest': 'https://libraries.walthamforest.gov.uk',
    'sutton': 'https://libraries.sutton.gov.uk',
    'merton': 'https://libraries.merton.gov.uk',
    'croydon': 'https://libraries.croydon.gov.uk',
    'lewisham': 'https://libraries.lewisham.gov.uk',
}

war_urls = {
    'bexley': 'https://arena.yourlondonlibrary.net/web/bexley',
    'lameth': 'https://libraries.lambeth.gov.uk'
}

primo_urls = {
    'british library': 'https://bll01.primo.exlibrisgroup.com/discovery'
}

parser = argparse.ArgumentParser()
parser.add_argument("title", type=str, help="title of book with '+' as spaces, e.g. lessons+in+chemistry")
parser.add_argument("author", type=str, help="last name of author, e.g. garmus")
args = parser.parse_args()

title=args.title
author=args.author

for council, url in prism_urls.items():
    check_in_prism(title, author, council, url)

for council, url in sirs_urls.items():
    check_in_sirs(title, author, council, url)

for council, url in spydus_urls.items():
    check_in_spydus(title, author, council, url)

check_in_multiple(title, author, 'multiple', multiple_urls['enfield'])

for council, url in war_urls.items():
    check_in_war(title, author, council, url)

for council, url in primo_urls.items():
    check_in_primo(title, author, council, url)