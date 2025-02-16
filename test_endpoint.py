from http import HTTPStatus
from pprint import pprint

import requests


url = "http://localhost:10000/process-pdf/"

data = {
    "url": "https://api.slingacademy.com/v1/sample-data/files/text-and-table.pdf",  # URL должен явно указывать на ссылку с PDF-файлом
    "pages": "1-2"  # подробнее про диапазоны в README
}

response = requests.post(url, json=data)

if response.status_code == HTTPStatus.OK:
    print("Конвертация прошла успешно!")
    pprint("Ответ от сервера:", response.json())
else:
    print(f"Ошибка: {response.status_code}")
    print("Ответ от сервера:", response.text)
