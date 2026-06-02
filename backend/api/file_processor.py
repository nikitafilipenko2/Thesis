from pathlib import Path

import docx
import PyPDF2


class FileProcessorError(Exception):
    pass


class FileProcessor:
    TEXT_ENCODINGS = ("utf-8", "cp1251", "koi8-r", "latin-1")

    @classmethod
    def extract_text_from_txt(cls, file_path):
        for encoding in cls.TEXT_ENCODINGS:
            try:
                with open(file_path, "r", encoding=encoding) as source:
                    return source.read()
            except UnicodeDecodeError:
                continue
            except OSError as error:
                raise FileProcessorError(f"Не удалось открыть текстовый файл: {error}") from error
        raise FileProcessorError("Не удалось прочитать текстовый файл")

    @staticmethod
    def extract_text_from_pdf(file_path):
        try:
            with open(file_path, "rb") as source:
                pdf_reader = PyPDF2.PdfReader(source)
                text_chunks = []
                for page in pdf_reader.pages:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text_chunks.append(page_text.strip())
        except Exception as error:
            raise FileProcessorError(f"Не удалось обработать PDF-файл: {error}") from error
        return "\n".join(text_chunks)

    @staticmethod
    def extract_text_from_docx(file_path):
        try:
            document = docx.Document(file_path)
        except Exception as error:
            raise FileProcessorError(f"Не удалось обработать DOCX-файл: {error}") from error
        paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        return "\n".join(paragraphs)

    @classmethod
    def extract_text(cls, file_path):
        extension = Path(file_path).suffix.lower()
        if extension == ".txt":
            return cls.extract_text_from_txt(file_path)
        if extension == ".pdf":
            return cls.extract_text_from_pdf(file_path)
        if extension == ".docx":
            return cls.extract_text_from_docx(file_path)
        raise FileProcessorError(f"Неподдерживаемый формат файла: {extension}")
