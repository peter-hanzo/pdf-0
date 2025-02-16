import os
import zipfile

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from pdf_processor import create_zip, download_pdf, extract_pages_as_png, get_pdf_page_count, parse_pages


app = FastAPI()

# Папки для хранения PDF и PNG
PDF_FOLDER = "/app/pdfs"
PNG_FOLDER = "/app/pngs"
PNG_PATH_PREFIX = "pngs"

app.mount("/static", StaticFiles(directory=PNG_FOLDER, html=True), name="static")


@app.post("/process-pdf/")
async def process_pdf(request: Request) -> dict:
    """
    Проверяет ссылку, кол-во страниц, соответствие формата указанных pages и конвертирует PDF-файл.
    Возвращает JSON с ссылкой на папку с файлами и статусом.
    """
    
    data = await request.json()
    url = data.get("url")
    pages = data.get("pages")

    if not url:
        raise HTTPException(status_code=400, detail="Missing URL")

    if not url.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="URL must ends with .pdf")

    try:
        pdf_name = os.path.basename(url)
        pdf_path = os.path.join(PDF_FOLDER, pdf_name)

        # Скачиваем ПДФ
        download_pdf(url, pdf_path)

        if pages:
            max_pages = get_pdf_page_count(pdf_path)
            try:
                pages = parse_pages(pages, max_pages)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid pages format: {str(e)}")

        folder_name = os.path.splitext(pdf_name)[0]
        output_folder = os.path.join(PNG_FOLDER, folder_name)

        os.makedirs(output_folder, exist_ok=True)

        # Здесь ПДФ-ки превращаются в .png
        extract_pages_as_png(pdf_path, output_folder, pages)

        return {"status": "success", "message": "PDF processed", "folder_url": f"/{PNG_PATH_PREFIX}/{folder_name}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/{PNG_PATH_PREFIX}/{folder_name}/")
async def list_files(folder_name: str) -> HTMLResponse:
    """
    Возвращает HTML-страницу со списком файлов в указанной папке и ссылку для скачивания архива
    """
    folder_path = os.path.join(PNG_FOLDER, folder_name)

    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail="Folder not found")

    files = os.listdir(folder_path)
    files = [f for f in files if os.path.isfile(os.path.join(folder_path, f))]

    # Рисует простенькую HTML-структуру
    html_content = f"<h1>{folder_name}</h1><ul>"
    for file in sorted(files):
        file_url = f"/{PNG_PATH_PREFIX}/{folder_name}/{file}"
        html_content += f'<li><a href="{file_url}">{file}</a></li>'

    zip_url = f"/{PNG_PATH_PREFIX}/{folder_name}/download/"
    html_content += f'<br><a href="{zip_url}">Загрузить архив с файлами</a>'
    html_content += "</ul>"
    
    return HTMLResponse(content=html_content)


@app.get("/{PNG_PATH_PREFIX}/{folder_name}/download/")
async def download_folder_as_zip(folder_name: str) -> FileResponse:
    """
    Скачивает все файлы из папки как ZIP-архив без сжатия
    """
    folder_path = os.path.join(PNG_FOLDER, folder_name)

    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail="Folder not found")

    zip_filename = f"{folder_name}.zip"
    zip_filepath = os.path.join(PNG_FOLDER, zip_filename)
    
    zip_file = create_zip(zip_filepath, zip_filename)

    return FileResponse(zip_file, media_type='application/zip', filename=zip_filename)


@app.get("/{PNG_PATH_PREFIX}/{folder_name}/{filename}")
async def get_png(folder_name: str, filename: str) -> FileResponse:
    """
    Возвращает PNG файл по имени из указанной папки
    """

    file_path = os.path.join(PNG_FOLDER, folder_name, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")
