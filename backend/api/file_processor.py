import os
import PyPDF2
import docx


class FileProcessor:
    @staticmethod
    def extract_text_from_txt(file_path):
        # Пробуем разные кодировки
        encodings = ['utf-8', 'cp1251', 'latin-1', 'koi8-r']
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    content = f.read()
                    print(f"Успешно прочитано с кодировкой {enc}: {len(content)} символов")
                    return content
            except UnicodeDecodeError:
                print(f"Не получилось с кодировкой {enc}")
                continue
        raise UnicodeDecodeError(f"Не удалось прочитать файл ни с одной кодировкой")

    @staticmethod
    def extract_text_from_pdf(file_path):
        print(f"Читаем PDF файл: {file_path}")
        text = ""
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            print(f"Страниц в PDF: {len(pdf_reader.pages)}")
            for i, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                    print(f"Страница {i + 1}: {len(page_text)} символов")
        return text

    @staticmethod
    def extract_text_from_docx(file_path):
        print(f"Читаем DOCX файл: {file_path}")
        doc = docx.Document(file_path)
        paragraphs = [paragraph.text for paragraph in doc.paragraphs]
        print(f"Параграфов в DOCX: {len(paragraphs)}")
        return '\n'.join(paragraphs)

    @classmethod
    def extract_text(cls, file_path):
        print(f"Извлекаем текст из: {file_path}")
        if file_path.endswith('.txt'):
            return cls.extract_text_from_txt(file_path)
        elif file_path.endswith('.pdf'):
            return cls.extract_text_from_pdf(file_path)
        elif file_path.endswith('.docx'):
            return cls.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {file_path}")