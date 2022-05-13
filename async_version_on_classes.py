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
        self._dict_to_dump = dict_to_dump if bool(dict_to_dump) else self.fill_with_temporary_content()

        with open(self._name, 'w') as f:
            dump(self._dict_to_dump, f, escape_forward_slashes=False, indent=4)

    @staticmethod
    def fill_with_temporary_content():
        from string import ascii_lowercase
        return {k: v for v, k in enumerate(ascii_lowercase)}

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

    def __del__(self, ):
        self.finish = datetime.now()
        print('Program is finish: ', self.finish - self.start)


class Parser:
    """Создание сессии"""

    def __init__(self, rubric, step, proxies):
        self.rubric = rubric
        self.step = step
        self.proxies = proxies
        self.response = None

    async def get_api_content(self, session, url, num_page, proxies):
        url = f'{url}&page={num_page}'
        items = dict()
        async with session.get(url, proxy=proxies()) as self.response:
            await self.check_status_code()
            if self.response is not None:
                api_answer = await self.response.json()
                data_json = api_answer["results"]
                for content in data_json:
                    items.update({content['id']: content})
                print(f'Loading content of page: #{num_page}... items: {len(items)}')

        print(items.keys())
        return items

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
        items = api_answer['count']
        pages = ceil(api_answer['count'] / 10)
        print(f'Товаров в категории {items} страниц для обработки {pages}')
        return pages

    async def get_content_and_convert_to_dict(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
        }

        items = dict()

        async with ClientSession(headers=headers) as session:
            url = f'https://www.bazaraki.com/api/items/?rubric={self.rubric}'

            async with session.get(url, proxy=self.proxies()) as self.response:
                await self.check_status_code()
                pages = await self.get_total_pages()

                previous_page = 1

                for next_page in range(1, pages + self.step, self.step):
                    tasks = list()

                    for num_page in range(previous_page, next_page):
                        task = self.get_api_content(session, url, num_page, self.proxies)
                        tasks.append(task)

                    for item in await gather(*tasks):
                        items.update(item)

                    previous_page = next_page
                    print('---------------')

        print('Уникальных товаров:', len(items))
        return items


async def main(step=10):
    """"""
    login = ''
    password = ''
    proxies = [
        f'http://{login}:{password}@217.29.53.84:10171',
        f'http://{login}:{password}@217.29.53.84:10170',
        f'http://{login}:{password}@217.29.53.84:10169',
        f'http://{login}:{password}@217.29.53.84:10168',
        f'http://{login}:{password}@217.29.53.84:10167',
        f'http://{login}:{password}@217.29.53.84:10166',
        f'http://{login}:{password}@217.29.53.84:10165',
        f'http://{login}:{password}@217.29.53.84:10164',
        f'http://{login}:{password}@217.29.53.84:10163',
        f'http://{login}:{password}@217.29.53.107:11091',
    ]

    proxies = ProxiesList(proxies)

    rubric = 5

    p = Parser(rubric, step, proxies)
    items = await p.get_content_and_convert_to_dict()

    SaveJson(f'Bazaraki-Dump-rubrick-{rubric}', items)


if __name__ == "__main__":

    if platform == 'win32':
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    TimerDecorator(run(main(step=3)))
