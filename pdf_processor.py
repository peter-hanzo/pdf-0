from http import HTTPStatus
import os
import subprocess
import zipfile

import requests


def download_pdf(url, output_path):
    """
    Скачивание PDF по ссылке
    """

    response = requests.get(url, stream=True)
    if response.status_code == HTTPStatus.OK:
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return output_path
    raise ValueError("Ошибка скачивания PDF")


def get_pdf_page_count(input_pdf):
    """
    Возвращает кол-во страниц в PDF с помощью pdfinfo
    """

    command = ["pdfinfo", input_pdf]
    result = subprocess.run(command, capture_output=True, text=True, check=True)

    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":")[1].strip())
    
    raise ValueError("Не удалось извлечь количество страниц из PDF")


def parse_pages(pages_str, max_pages):
    """
    Парсинг строки с номерами страниц и диапазонами
    + проверка, входят ли страницы из pages в кол-во доступных страниц
    """

    pages = []
    for part in pages_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            try:
                start, end = int(start), int(end)
                if start > max_pages or end > max_pages:
                    raise ValueError(f"Диапазон выходит за пределы количества страниц в PDF ({max_pages})")
                if start > end:
                    raise ValueError(f"Некорректный диапазон: начало диапазона больше конца ({part})")
                pages.extend(range(start, end + 1))
            except ValueError:
                raise ValueError(f"Некорректный диапазон: {part}")
        else:
            try:
                page = int(part)
                if page > max_pages:
                    raise ValueError(f"Номер страницы {page} выходит за пределы количества страниц в PDF ({max_pages})")
                pages.append(page)
            except ValueError:
                raise ValueError(f"Некорректный номер страницы: {part}")

    return sorted(set(pages))


def create_zip(output_folder, pdf_name):
    """
    Создание ZIP-архива c PNG (без сжатия)
    """

    pdf_output_folder = os.path.join(output_folder, pdf_name)
    zip_path = os.path.join(output_folder, f"{pdf_name}.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zipf:
        for root, _, files in os.walk(pdf_output_folder):
            for file in files:
                if file.endswith('.png'):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, pdf_output_folder)
                    zipf.write(file_path, arcname)
    return zip_path


def extract_pages_as_png(input_pdf, output_folder, pages=None):
    """
    Конвертирует страницы PDF в PNG (все страницы или указанные)
    Для явного указания качества стоит раскомментить флаг -r
    """

    os.makedirs(output_folder, exist_ok=True)

    if pages is None:
        command = [
            "pdftoppm",
            "-png",
            # "-r", "300",
            input_pdf,
            os.path.join(output_folder, "page")
        ]
        subprocess.run(command, check=True)
    else:
        for page in pages:
            command = [
                "pdftoppm",
                "-png",
                "-f", str(page),
                "-l", str(page),
                # "-r", "300",
                input_pdf,
                os.path.join(output_folder, f"page")
            ]
            subprocess.run(command, check=True)
    
    return output_folder
