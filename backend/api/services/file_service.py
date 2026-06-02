import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from api.file_processor import FileProcessor, FileProcessorError


class FileServiceError(Exception):
    pass


@dataclass
class ProcessedUpload:
    original_filename: str
    file_size: int
    file_type: str
    extracted_text: str


ALLOWED_FILE_TYPES = {
    ".txt": {
        "file_type": "txt",
        "content_types": {"text/plain", "application/octet-stream"},
    },
    ".pdf": {
        "file_type": "pdf",
        "content_types": {"application/pdf", "application/octet-stream"},
    },
    ".docx": {
        "file_type": "docx",
        "content_types": {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/octet-stream",
        },
    },
}

MAX_UPLOAD_SIZE = 10 * 1024 * 1024


def _resolve_file_type(filename, content_type):
    extension = Path(filename).suffix.lower()
    file_config = ALLOWED_FILE_TYPES.get(extension)
    if not file_config:
        raise FileServiceError("Поддерживаются только .txt, .pdf и .docx файлы")
    if content_type not in file_config["content_types"]:
        raise FileServiceError("Неверный MIME-тип файла")
    return file_config["file_type"]


def extract_uploaded_file(uploaded_file):
    if uploaded_file is None:
        raise FileServiceError("Файл не выбран")
    if uploaded_file.size > MAX_UPLOAD_SIZE:
        raise FileServiceError("Файл слишком большой. Максимальный размер: 10 МБ")

    file_type = _resolve_file_type(uploaded_file.name, uploaded_file.content_type)

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as temp_file:
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
        temp_path = temp_file.name

    try:
        extracted_text = FileProcessor.extract_text(temp_path)
    except FileProcessorError as error:
        raise FileServiceError(str(error)) from error
    finally:
        os.unlink(temp_path)

    if not extracted_text.strip():
        raise FileServiceError("Из файла не удалось извлечь текст")

    return ProcessedUpload(
        original_filename=uploaded_file.name,
        file_size=uploaded_file.size,
        file_type=file_type,
        extracted_text=extracted_text,
    )
