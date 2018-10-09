import os
import re
import time
from random import uniform
from lxml.html import fromstring
from lxml.html.clean import Cleaner
from urllib.request import Request, urlopen


def request(link):
    req = Request(link, headers={'User-Agent': 'Tor/8.0.1'})

    with urlopen(req) as response:
        html = response.read().decode('utf-8')

    html = re.sub('\n', '     ', html)

    return html


def create_full_links(links):
    full_links = ['https://www.avito.ru' + link for link in links]
    
    return full_links


def clean_text(text):
    text = re.sub('\n', ' ', text)

    try:
        doc = fromstring(text)
        cleaner = Cleaner(style=True)
        doc = cleaner.clean_html(doc)
        text = doc.text_content()
    except:
        text = re.sub('<.*?>', '', text, flags=re.DOTALL)
        text = re.sub('<script>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub('<!--.*?-->', '', text, flags=re.DOTALL)

    return text


def find_ads(num):
    link = 'https://www.avito.ru/moskva/chasy_i_ukrasheniya?p=%s' % (num)
    sleep = uniform(0.0, 5.0)
    time.sleep(sleep)
    html = request(link)
    links = re.findall('<a class="item-description-title-link"[ \n]*itemprop="url"[ \n]*href="(.*?)"[ \n]*title="(.*?)">', html)
    links = [elem[0] for elem in links]

    return links


def collect_links_on_ads(main_html):
    last_page = re.search('\<a class\="pagination-page" href\="/moskva/chasy_i_ukrasheniya\?p\=([0-9]+)"\>Последняя\</a\>', main_html)

    if last_page != None:
        last_page = last_page.group(1)
    else:
        last_page = 100

    first_page_links = re.findall('<a class="item-description-title-link"[ \n]*itemprop="url"[ \n]*href="(.*?)"[ \n]*title="(.*?)">', main_html)
    first_page_links = [elem[0] for elem in first_page_links]
    first_page_links = create_full_links(first_page_links)

    all_links = first_page_links

    i = 2

    while len(all_links) < 10000:
        try:
            current_links = find_ads(i)
            current_links = create_full_links(current_links)
            all_links += current_links
            i += 1
        except:
            continue

    all_links = all_links[:10000]

    with open('all_links.txt', 'w', encoding='utf-8') as file:
        for l in all_links:
            file.write('%s\n' % (l))

    return all_links 


def check_info(req, html):
    m = re.search(req, html)

    if m != None:
        return clean_text(m.group(1))
    else:
        return ' '


def collect_adv_data(link):
    data = {}

    try:
        html = request(link)

        data['title'] = check_info('<div class="sticky-header-prop sticky-header-title">[ \n]*(.*?)[ \n]*</div>', html)
        data['seller'] = check_info('<span class="sticky-header-seller-text" title="(.*?)">', html)
        data['address'] = check_info('<span class="item-map-address" itemprop="address" itemscope itemtype="http://schema.org/PostalAddress"><span>(.*?)</span>', html)
        data['description'] = check_info('itemprop="description">[ \n]*(.*?)[ \n]*</div>', html)
        metadata = check_info('<div class="title-info-metadata-item">[ \n]*(.*?)[ \n]*</div>', html)
        
        if metadata != ' ':
            data['number'] = metadata.split(', ')[0]
            data['date'] = metadata.split(', ')[1]
        else:
            data['number'] = ' '
            data['date'] = ' '

        data['price'] = check_info('<span class="js-item-price" content="(.*?)" itemprop="price">.*?</span>', html)
        
        if data['price'] == ' ':
            data['price'] = check_info('<span class="price-value-string js-price-value-string">[ \n]*(.*?)[ \n]*</span>', html)
    except:
        with open('broken_links.txt', 'a', encoding='utf-8') as file:
            file.write('%s\n' % (link))
    
    return data


def create_corpus(all_links):
    for i, link in enumerate(all_links):
        sleep = uniform(0.0, 5.0)
        time.sleep(sleep)
        data = collect_adv_data(link)
        
        if data != {}:
            save_data(link, data)
            print(i)


def save_data(link, data):
    link = re.sub('.*/', '', link)

    keys = ['title', 'number', 'date', 'price', 'seller', 'address', 'description']

    for key in keys:
        if key not in data.keys():
            data[key] = ' '
    
    with open('%s.txt' % (link), 'w', encoding='utf-8') as file:
        file.write('title: %s\n' % (data['title']))
        file.write('number: %s\n' % (data['number']))
        file.write('date: %s\n' % (data['date']))
        file.write('price: %s\n' % (data['price']))
        file.write('seller: %s\n' % (data['seller']))
        file.write('address: %s\n\n' % (data['address']))
        file.write(data['description'])


def main():
    os.makedirs('avito_corpus')
    os.chdir('avito_corpus')

    main_link = 'https://www.avito.ru/moskva/chasy_i_ukrasheniya'
    main_html = request(main_link)
    all_links = collect_links_on_ads(main_html)
    create_corpus(all_links)


if __name__ == '__main__':
    main()
