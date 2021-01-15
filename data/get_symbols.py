""""
Get stock tickers (or name of the asset you want to trade)
and save them into local MySQL database.
"""

__author__ = 'Han Xiao (Aaron)'

import bs4
import requests
import pymysql
import datetime

def get_sp500_wiki():
    """
    Scrape S&P500 constituents from Wiki.
    https://en.wikipedia.org/wiki/List_of_S%26P_500_companies

    --------
    :return: A list of tuple (will be saved into SQL later).
    """
    # Stores the current time that will be used for recording 'created-at' information
    now = datetime.datetime.utcnow()

    # Scrape text data from wiki by using requests and BeautifulSoup
    # Based on structure, select info we need, which is the symbol table
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, 'html.parser')
    symbols_list = soup.select('table')[0].select('tr')[1:]

    symbols = []
    for i, symbol in enumerate(symbols_list):
        tds = symbol.select('td')
        symbols.append(
            (
                tds[0].select('a')[0].text,  # Ticker
                'stock',                     # Asset Type
                tds[1].select('a')[0].text,  # Company Name
                tds[3].text,                 # Sector
                'USD',                       # currency
                now,                         # created_date
                now                          # last_updated_date
            )
        )

    return symbols


def sp500_to_sql(symbols:list):
    """
    :param symbols: The list of tuples that we get from previous function
    :return: No return, save info to MySQL
    """
    # Note: I use Wampserver with PhpMyAdmin in Windows; But in Mac-OS, I use MAMP with PhpMyAdmin.
    # Since I already have MySQL before, so I use different port 3308 instead of default 3306
    db = pymysql.connect(host='localhost', user='root', password='',
                         database='eod_equities', port=3308,
                         charset='utf8')
    # Initialize cursor
    cur = db.cursor()

    # cursor commands
    column_str = """`‘ticker‘`, `‘instrument‘`, `‘name‘`, `‘sector‘`, `‘currency‘`, `‘created_date‘`, `‘last_updated_date‘`"""
    insert_str = ("%s, " * 7)[:-2]
    final_str = "INSERT INTO `‘symbol‘`(%s) VALUES (%s)" % (column_str, insert_str)

    for i in range(len(symbols)):
        cur.execute(final_str,
                    (symbols[i][0],
                     symbols[i][1],
                     symbols[i][2],
                     symbols[i][3],
                     symbols[i][4],
                     symbols[i][5],
                     symbols[i][6]))

    db.commit()
    cur.close()
    db.close()

def get_northward():
    ""

if __name__ == '__main__':
    symbols_500 = get_sp500_wiki()
    sp500_to_sql(symbols_500)


