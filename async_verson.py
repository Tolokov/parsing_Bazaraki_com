from asyncio import gather, run, set_event_loop_policy, WindowsSelectorEventLoopPolicy
from aiohttp import ClientSession
from ujson import dump

from math import ceil
from datetime import datetime
from sys import platform
from itertools import cycle


async def check_status_code(response):
    if response.status == 404:
        print(f'does not exist')
        return response
    elif response.status != 200:
        print(f'STATUS CODE: {response.status}')
        raise StopIteration(f'The site is not available or the address has changed')
    else:
        return response


async def get_total_pages(response) -> int:
    """Узнать количество товаров и количество страниц, которые в последствии будут использоваться при парсинге"""
    api_answer = await response.json()
    items = api_answer['count']
    pages = ceil(api_answer['count'] / 10)
    print(f'Товаров в категории {items} страниц для обработки {pages}')
    return pages


async def get_api_content(session, url, num, proxies) -> dict:
    """Поочередный обход всех страниц"""
    url = f'{url}&page={num}'
    p = next(proxies)
    print(p)
    async with session.get(url, proxy=p) as response:
        response = await check_status_code(response)
        items = dict()
        api_answer = await response.json()
        data_json = api_answer["results"]
        for content in data_json:
            items.update({content['id']: content})

        print(f'Loading content of page #: {num}... items: {len(items)}')
    return items


async def get_content_and_dump_to_dict(rubric, step, proxies):
    headers = {
     'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    }

    items = dict()

    async with ClientSession(headers=headers) as session:
        url = f'https://www.bazaraki.com/api/items/?rubric={rubric}'

        async with session.get(url, proxy=next(proxies))as response:
            pages = await get_total_pages(await check_status_code(response))

        async with session.get(url, proxy=next(proxies)) as response:

            previous_page = 1

            for next_page in range(1, pages + step + step, step):
                tasks = list()

                for num_page in range(previous_page, next_page):

                    task = get_api_content(session, url, num_page, proxies)

                    tasks.append(task)

                for item in await gather(*tasks):
                    items.update(item)

                previous_page = next_page
                print('---------------')

    print('Уникальных товаров:', len(items))
    return items


async def main(step, proxies):
    start = datetime.now()

    rubric = 5

    items = await get_content_and_dump_to_dict(rubric, step, proxies)

    with open('async_result.json', 'w') as f_json:
        dump(items, f_json, escape_forward_slashes=False, indent=4)

    end = datetime.now()
    print('Времени затрачено на выполнение скрипта: ', end - start)


if __name__ == '__main__':
    # https://proxy6.net/
    login = None
    password = None
    proxies = [
        f'http://{login}:{password}.29.53.90:11231',
        f'http://{login}:{password}.29.53.90:11232'
    ]
    proxies_cycle = cycle(proxies)

    if platform == 'win32':
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    run(main(step=1, proxies=proxies_cycle))


