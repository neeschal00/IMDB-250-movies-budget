"""
Script to fetch data from each website of imdb top 250 movies list and load them in pandas dataframe and
stroe them in different file formats
"""


import pandas as pd
import requests
from bs4 import BeautifulSoup
from pprint import pprint
import asyncio
import aiohttp
import re




class MovieEarnings: #type:ignore
    """
    Class to scrape the imdb top 250 list and get the box office collection available in each website and fetch
    the data asynchronously
    """

    def __init__(self)->None:

        self.imdb_link:str = "https://www.imdb.com/chart/top"
        headers:dict = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36 Edg/87.0.664.52'
        }

        self.soup:object = BeautifulSoup(requests.get(self.imdb_link,headers=headers).content,'lxml')
        main_table = self.soup.find('div',class_='article').find('div',class_='lister').find('table').find('tbody',class_='lister-list')

        #table conts
        self.table_contents = main_table.find_all('td',class_='titleColumn')

        self.movies_all = [] #imdb movies link


        for half_link in self.table_contents:
            all_link = 'https://www.imdb.com'+half_link.find('a')['href']
            self.movies_all.append(all_link)
        # pprint(self.movies_all)

        asyncio.get_event_loop().run_until_complete(self.get_all_sites(self.movies_all))


    async def getContent(self,session:object,url:str)->None:
        async with session.get(url) as response: #sharing session


            default = {
                'Position': re.compile(r"(?<=chttp_tt_)\d+").search(url).group(0),
                'Title': None,
                'Rating': None,
                'Budget': None,
                'Opening Weekend USA':None,
                'Gross USA': None,
                'Cumulative Worldwide Gross':None
            }
            resp_cont = await response.text() #awaiting the response received from the link passed
            soup = BeautifulSoup(resp_cont,'lxml')


            name = soup.find('div',id="main_top").find('div',class_="title_wrapper").find('h1').text
            default['Title'] = name.replace('\xa0','').strip()


            rating = soup.find('div',id="main_top").find('div',class_="ratingValue").find('strong').find('span').text
            default['Rating'] = rating

            find_data = soup.find('div',id='titleDetails').find_all('div',class_='txt-block')

            for all_d in find_data:
                check = all_d.find('h4')

                if check != None:
                    if check.text in ['Budget:','Opening Weekend USA:','Gross USA:','Cumulative Worldwide Gross:']:
                        if check.text == 'Budget:':
                            budget_d = check.parent
                            budget_d.span.replaceWith('')
                            budget_d.h4.replaceWith('')
                            # print(budget_d.text.strip())
                            default['Budget'] = budget_d.text.strip()

                        elif check.text == 'Opening Weekend USA:':
                            open_week = check.parent
                            open_week.span.replaceWith('')
                            open_week.h4.replaceWith('')
                            # print(open_week.text.strip())
                            default['Opening Weekend USA'] = open_week.text.strip().strip(',')

                        elif check.text == 'Gross USA:':
                            gross_usa = check.parent
                            # gross_usa.span.replaceWith('')
                            gross_usa.h4.replaceWith('')
                            # print(gross_usa.text.strip())
                            default['Gross USA'] = gross_usa.text.strip()

                        elif check.text == 'Cumulative Worldwide Gross:':
                            worldwide_gross = check.parent
                            # worldwide_gross.span.replaceWith('')
                            worldwide_gross.h4.replaceWith('')
                            # print(worldwide_gross.text.strip())
                            default['Cumulative Worldwide Gross'] = worldwide_gross.text.strip()
            print(default)
            self.earning.append(default)

    async def get_all_sites(self,sites:list)->None:
        async with aiohttp.ClientSession() as session:
            tasks = []
            self.earning = []

            for url in sites:
                task = asyncio.ensure_future(self.getContent(session,url)) #concurrent run
                tasks.append(task)

            await asyncio.gather(*tasks,return_exceptions=True)

if __name__ == "__main__":

    obj = MovieEarnings()

    #working with pandas portion
    pd.set_option('display.max_columns',6) #setting the dataframe max values to show
    pd.set_option('display.max_rows',250)

    data = obj.earning

    df = pd.DataFrame(data)
    df.sort_values(by="Rating",ascending=False,inplace=True) #inplace for permanent sort

    #Converting into different file formats
    df.to_excel('imdb_boxOffice.xlsx',index=False)
    df.to_json('imdb_boxOffice.json',orient='records')
    df.to_csv('imdb_boxOffice.csv', index=False)

