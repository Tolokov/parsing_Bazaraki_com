from aiohttp import ClientSession
from ujson import dump
from asyncio import gather, run, set_event_loop_policy, WindowsSelectorEventLoopPolicy

from math import ceil
from datetime import datetime
from sys import platform
from itertools import cycle


class SaveJson:
    """Saving data from the dictionary into a json"""

    def __init__(self, name: str, dict_to_dump: dict):
        self._name = name if '.json' in name else f'{name}.json'
        self._dict_to_dump = dict_to_dump

        with open(self._name, 'w') as f:
            dump(self._dict_to_dump, f, escape_forward_slashes=False, indent=4)
            print(self._name, ' is save!')

    def __str__(self):
        return self._name


class ProxiesList(cycle):
    """List of proxy servers to be used for parsing"""

    def __call__(self):
        return self.__next__()


class TimerDecorator:
    start = datetime.now()

    def __init__(self, func):
        self._function = func

    def __call__(self, *args, **kwargs):
        func = self._function(*args, **kwargs)
        return func

    def __del__(self):
        self.finish = datetime.now()
        self.stop = self.finish - self.start
        self.result_print = ('Program is finish: {}').format(self.stop)
        print(self.result_print)


class Parser:

    def __init__(self, rubric: int, step: int, proxies):
        self.rubric = rubric
        self.step = step
        self.proxies = proxies
        self.response = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/39.0.2171.95 Safari/537.36'
        }
        self.pages = None
        self.items = None

    async def check_status_code(self):
        if self.response.status == 404:
            print(f'does not exist')
            self.response = None
        elif self.response.status != 200:
            print(f'STATUS CODE: {self.response.status}')
            raise StopIteration(f'The site is not available or the address has changed')

    async def get_total_pages(self):
        """To know the number of products and the number of pages that will be used in the parsing"""
        api_answer = await self.response.json()
        self.items = int(api_answer['count'])
        self.pages = ceil(api_answer['count'] / 10)
        if self.pages >= 3000:
            self.pages = 3000
            print('The maximum number of requests to the api has been exceeded, the limit is set to 3 thousand')
        print(f'Items in category: {self.items} pages to process: {self.pages}')

    async def get_api_content(self, session, url, num_page, proxies):
        url = f'{url}&page={num_page}'
        items = dict()
        async with session.get(url, proxy=proxies) as self.response:
            await self.check_status_code()
            if self.response is not None:
                api_answer = await self.response.json()
                data_json = api_answer["results"]
                for content in data_json:
                    items.update({content['id']: content})
                # print(f'Loading content of page: #{num_page}... items: {len(items)}')
        return items

    async def get_content_and_convert_to_dict(self):

        items = dict()

        async with ClientSession(headers=self.headers) as session:
            url = f'https://www.bazaraki.com/api/items/?rubric={self.rubric}'

            async with session.get(url, proxy=self.proxies()) as self.response:
                await self.check_status_code()
                await self.get_total_pages()

                previous_page = 1

                for next_page in range(1, self.pages + self.step, self.step):
                    tasks = list()
                    for num_page in range(previous_page, next_page + 1):

                        task = self.get_api_content(session, url, num_page, self.proxies())
                        tasks.append(task)

                    for item in await gather(*tasks):
                        items.update(item)

                    previous_page = next_page
                    print(f'... page #{num_page}')
        print('Unique items:', len(items))
        return items


async def main(step, proxies):
    """Starting the data collection process from bazaraki com"""

    all_rubrics = {
        # "Cars": "5",
        # "Motorbikes": "2352",
        # "Auto parts": "6", # more 3000 pages
        # "Auto accessories": "2795",
        # "Motorbike parts, accessories": "17",
        # "Tractors, parts": "2952",
        # "Trucks, truck parts": "557",
        # "Boats, sailing, marine equipment": "4",
        # "Buses": "2713",
        # "Vans": "2381",
        # "Tools, equipment": "3120",
        # "Lifts, cranes": "3134",
        # "Trailers": "2335",
        # "Caravans": "3239",
        # "Quads, ATV, buggy": "290",
        # "Go-karts": "2718",
        "Aircraft": "3285"
    }


    for title_rubric, rubric in all_rubrics.items():
        print(f'Rubric {title_rubric} #{rubric} is parsing...')

        p = Parser(rubric, step, proxies)
        items = await p.get_content_and_convert_to_dict()

        print()
        SaveJson(f'jsons\\Bazaraki-{title_rubric}-{rubric}', items)


if __name__ == "__main__":
    # Чем больше прокси приобретено, тем быстрее будут собираться данные с сайта
    # https://proxy6.net/en/?r=406356
    # приобретаем самый дешевый за 3.60
    # указываем полученные логин и пароль, а так-же выданные ip-адреса уникально для каждой строки

    login = ''
    password = ''
    proxy_id = ''

    proxies = ProxiesList([
        f'http://{login}:{password}@{proxy_id}',
        f'http://{login}:{password}@{proxy_id}',
        f'http://{login}:{password}@{proxy_id}',
        f'http://{login}:{password}@{proxy_id}',
        f'http://{login}:{password}@{proxy_id}',
    ])

    if platform == 'win32':
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    TimerDecorator(run(main(step=4, proxies=proxies)))
