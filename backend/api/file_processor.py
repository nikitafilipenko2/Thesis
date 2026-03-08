import os
import PyPDF2
import docx


class FileProcessor:
    @staticmethod
    def extract_text_from_txt(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def extract_text_from_pdf(file_path):
        text = ""
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    @staticmethod
    def extract_text_from_docx(file_path):
        doc = docx.Document(file_path)
        return '\n'.join([paragraph.text for paragraph in doc.paragraphs])

    @classmethod
    def extract_text(cls, file_path):
        if file_path.endswith('.txt'):
            return cls.extract_text_from_txt(file_path)
        elif file_path.endswith('.pdf'):
            return cls.extract_text_from_pdf(file_path)
        elif file_path.endswith('.docx'):
            return cls.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {file_path}")