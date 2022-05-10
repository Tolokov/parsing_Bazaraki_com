from asyncio import gather, run, set_event_loop_policy, WindowsSelectorEventLoopPolicy
from aiohttp import ClientSession
from ujson import dump

from math import ceil
from datetime import datetime


async def get_total_pages(url: str) -> int:
    """Узнать количество товаров и страниц для последующего обхода"""

    async with ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 404:
                print(f'{url} does not exist')
            elif response.status != 200:
                print(f'STATUS CODE: {response.status}')
                raise StopIteration(f'The site is not available or the address has changed')
            else:
                api_answer = await response.json()
                items = api_answer['count']
                pages = ceil(api_answer['count'] / 10)
                print(f'Товаров в категории {items} страниц для обработки {pages}')  # Добавить номер рубрики
                return pages


async def get_content_and_dump_to_json(url: str, num: int) -> dict:
    """Поочередный обход всех страниц"""

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    }

    url = f'{url}&page={num}'
    items = dict()
    async with ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            if response.status == 404:
                print(f'{url} does not exist')
            elif response.status == 403:
                raise StopIteration('ACCESS DENIED!')
            elif response.status != 200:
                print(f'STATUS CODE: {response.status}')
                raise StopIteration(f'The site is not available or the address has changed')
            else:
                api_answer = await response.json()
                data_json = api_answer["results"]
                for content in data_json:
                    items.update({content['id']: content})

            print(f'Loading content of page #: {num}... items: {len(items)}')
    return items


async def main(step=10):
    rubric = 5
    url = f'https://www.bazaraki.com/api/items/?rubric={rubric}'

    pages = await get_total_pages(url)
    # pages = 10
    items = dict()

    previous_page = 1
    for next_page in range(1, pages + step, step):
        tasks = list()

        for num_page in range(previous_page, next_page):
            task = get_content_and_dump_to_json(url, num_page)
            tasks.append(task)

        for item in await gather(*tasks):
            items.update(item)

        previous_page = next_page
        print('---------------')

    print('Дубликатов или совпадений:', pages -  len(items))
    print('Уникальных товаров:', len(items))

    with open('async_result.json', 'w') as f_json:
        dump(items, f_json, escape_forward_slashes=False, indent=4)


if __name__ == '__main__':
    start = datetime.now()

    set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    run(main(step=1))

    end = datetime.now()
    print('Времени затрачено на выполнение скрипта: ', end - start)