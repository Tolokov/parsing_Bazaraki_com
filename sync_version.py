from requests import get
from json import dump
from math import ceil

from datetime import datetime


def timer(f):
    def dec(*args, **kwargs):
        start = datetime.now()
        result = f(*args, **kwargs)
        end = datetime.now()
        print('Времени затрачено на выполнение скрипта: ', end - start)
        return result
    return dec


def get_count_items(url: str) -> int:
    """Получение ответа от сервиса"""
    response = get(url)
    if response.status_code == 200:
        pages = response.json()["count"] / 10
        total_pages = ceil(pages)
        print(f'Found {response.json()["count"]} items and {total_pages} pages')
        return total_pages
    else:
        print(f'{url} does not exist')
        raise StopIteration('The site is not available or the address has changed')


def get_items(url:str, pages:int):
    """Парсинг содержимого, и разбиение на блоки с товарами"""
    items = dict()
    count_duplicate = 0
    for number_of_pages in range(1, pages + 1):
        link = url + f'&page={number_of_pages}'
        print(f'Loading page # {number_of_pages}/{pages}')
        response = get(link)
        if response.status_code == 200:
            api_answer = response.json()["results"]
            for content in api_answer:
                if content['id'] in items:
                    print('обнаружено совпадение')
                    count_duplicate += 1
                    print(link)
                items.update({content['id']: content})

    print('Дубликатов или совпадений:', count_duplicate)
    print('Уникальных товаров:', len(items))

    return items


@timer
def main():
    rubric = 5
    url = f'https://www.bazaraki.com/api/items/?rubric={rubric}'

    pages = get_count_items(url)
    items = get_items(url, pages)

    with open('content_from_Bazaraki.json', 'w') as f_json:
        dump(items, f_json, indent=4)


if __name__ == '__main__':
    main()
