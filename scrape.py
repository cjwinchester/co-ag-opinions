import time
import csv

import requests
from bs4 import BeautifulSoup


# where all the magic happens
BASE_URL = 'https://coag.gov/resources/formal-ag-opinions'

# a hat for our data file
HEADERS = ['date', 'ag', 'title', 'pdf_link', 'description']


def get_max_page():
    '''get the last page number from the CO AG opinion search results page'''

    r = requests.get(BASE_URL)

    # soup the HTML
    soup = BeautifulSoup(r.text, 'html.parser')

    # find the nav element with the last page number
    lastpage = soup.find('li', class_='next') \
                   .previous_sibling.previous_sibling \
                   .text

    # return it but as a number
    return int(lastpage)


def extract_data(html):
    '''given the html of a page of CO AG opinions, extract the bits of data
    and return in a list of dicts'''

    # soup the page
    soup = BeautifulSoup(html, 'html.parser')

    # find the invididual entries
    entries = soup.find('div', class_='view-content') \
                  .find_all('div', class_='views-row')

    def parse_entry(entry):
        '''parse out the bits of an entry and return as a dict'''

        # find the link
        a = entry.find('a')

        # grab the href
        link = a['href']

        # ... and the title
        title = a.text.strip().replace('AG Opinion No. ', '')

        # and the name of the attorney general what did the opinin'
        ag = entry.find(
            'span',
            class_='views-field-field-attorney-general'
        ).text.strip()

        # grab the date part of the date (metadata ftw)
        date = entry.find('span', class_='date-display-single')['content'] \
                    .split('T')[0]

        # find the description and replace some cruft
        description = entry.find('div', class_='field-content').text.strip() \
                           .replace('“', '') \
                           .replace('”', '') \
                           .replace('"', '') \
                           .replace('’', "'")

        # marry our headers and data and return a dict
        return dict(zip(HEADERS, [date, ag, title, link, description]))

    # return entries parsed in a list comp
    return [parse_entry(x) for x in entries]


# get max page
lastpage = get_max_page()

# open a CSV to write out to
with open('ag-opinions.csv', 'w') as outfile:

    # create a writer object
    writer = csv.DictWriter(outfile, fieldnames=HEADERS)

    # write the headers
    writer.writeheader()

    # page numbers start at 0 (!) -- loop over the range to lastpage
    for i in range(0, lastpage):

        # get the page
        r = requests.get(BASE_URL, params={'page': i})
        r.raise_for_status()

        # let us know what we're up to
        print('Scraping page {}'.format(i+1))

        # grab the data
        data = extract_data(r.text)

        # write it to file
        writer.writerows(data)

        # pause a few secs
        time.sleep(2)
