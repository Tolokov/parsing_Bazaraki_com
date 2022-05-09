from requests import get
import asyncio
import json
from math import ceil


def get_count_items(url: str) -> int:
    response = get(url)
    if response.status_code == 200:
        print(f'Found {response.json()["count"]} items')
        pages = response.json()["count"] / 10
        return ceil(pages)
    else:
        print(f'{url} does not exist')
        raise StopIteration('The site is not available or the address has changed')


def get_items(url:str, number_of_pages:int):
    items = dict()
    count_duplicate = 0
    for number_of_pages in range(1, number_of_pages + 1):
        link = url + f'&page={number_of_pages}'
        print('.', sep='')
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


def main():
    rubric = 5
    url = f'https://www.bazaraki.com/api/items/?rubric={rubric}'

    number_of_pages = get_count_items(url)
    items = get_items(url, number_of_pages)

    with open('content_from_Bazaraki.json', 'w') as f_json:
        json.dump(items, f_json, indent=4)


if __name__ == '__main__':
    main()
