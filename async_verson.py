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
        return None
    elif response.status != 200:
        print(f'STATUS CODE: {response.status}')
        raise StopIteration(f'The site is not available or the address has changed')
    else:
        return response


async def get_total_pages(response) -> int:
    """To know the number of products and the number of pages that will be used in the parsing"""
    api_answer = await response.json()
    items = api_answer['count']
    pages = ceil(api_answer['count'] / 10)
    print(f'Товаров в категории {items} страниц для обработки {pages}')
    return pages


async def get_api_content(session, url, num, proxies) -> dict:
    """Bypassing all pages one by one"""
    url = f'{url}&page={num}'
    p = next(proxies)
    # print(p) # used when debugging
    async with session.get(url, proxy=p) as response:
        response = await check_status_code(response)
        items = dict()
        if response is not None:
            api_answer = await response.json()
            data_json = api_answer["results"]
            for content in data_json:
                items.update({content['id']: content})

            print(f'Loading content of page: #{num}... items: {len(items)}')
    return items


async def get_content_and_convert_to_dict(rubric, step, proxies):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    }

    items = dict()

    async with ClientSession(headers=headers) as session:
        url = f'https://www.bazaraki.com/api/items/?rubric={rubric}'

        async with session.get(url, proxy=next(proxies)) as response:
            pages = await get_total_pages(await check_status_code(response))

            previous_page = 1

            for next_page in range(1, pages + step, step):
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


async def main(step: int, proxies: list):
    """

    :param step: Number of simultaneous requests. If there are too many requests from one address, the server will block access
    :param proxies: List of proxy servers through which requests will be sent
    :return: json file
    """
    start = datetime.now()

    proxies_cycle = cycle(proxies)

    rubric = 5

    items = await get_content_and_convert_to_dict(rubric, step, proxies_cycle)

    with open('async_result.json', 'w') as f_json:
        dump(items, f_json, escape_forward_slashes=False, indent=4)

    end = datetime.now()
    print('Времени затрачено на выполнение скрипта: ', end - start)


if __name__ == '__main__':
    # Чем больше прокси приобретено, тем быстрее будут собираться данные с сайта
    # https://proxy6.net/en/?r=406356
    # приобретаем самый дешевый за 3.60
    # указываем полученные логин и пароль, а так-же выданные ip-адреса уникально для каждой строки

    login = None
    password = None
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

    if platform == 'win32':
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    # С десятью прокси, можно установить step и выше, в зависимости от нагруженности сервера
    # 3793 позиций за 36 секунд
    run(main(step=100, proxies=proxies))
