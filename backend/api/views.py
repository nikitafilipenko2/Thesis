from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import SummaryRequest
from .serializers import SummaryRequestSerializer
from .summarization import ExtractiveSummarizer
import time
from .abstractive import AbstractiveSummarizer
from .models import UploadedFile
from .serializers import UploadedFileSerializer
from .file_processor import FileProcessor
import tempfile
import os

extractive_summarizer = ExtractiveSummarizer(method='textrank')
abstractive_summarizer = None  # Пока не загружаем

def get_abstractive_summarizer():
    global abstractive_summarizer
    if abstractive_summarizer is None:
        try:
            print("Начинаю загрузку абстрактивной модели (5 ГБ)...")
            print("Это займет 5-10 минут в первый раз")
            abstractive_summarizer = AbstractiveSummarizer()
            print("Модель успешно загружена!")
        except Exception as e:
            print(f"НЕ УДАЛОСЬ ЗАГРУЗИТЬ МОДЕЛЬ: {e}")
            abstractive_summarizer = None
    return abstractive_summarizer

class SummaryRequestViewSet(viewsets.ModelViewSet):
    serializer_class = SummaryRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = SummaryRequest.objects.all()

    def get_queryset(self):
        return SummaryRequest.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def summarize(self, request):
        print("=== МЕТОД SUMMARIZE ВЫЗВАН ===")

        input_text = request.data.get('input_text', '')
        summary_type = request.data.get('summary_type', 'extractive')
        length_param = int(request.data.get('length_param', 5))

        print(f"Параметры: тип={summary_type}, длина={length_param}")
        print(f"Длина текста: {len(input_text)} символов")

        if not input_text:
            return Response(
                {'error': 'Текст не может быть пустым'},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_time = time.time()

        try:
            if summary_type == 'extractive':
                print("Экстрактивный метод...")
                output_text = extractive_summarizer.summarize(input_text, length_param)



            elif summary_type == 'abstractive':

                print("Абстрактивный метод...")

                print("Получаем суммаризатор...")

                summ = get_abstractive_summarizer()

                print(f"Суммаризатор получен: {summ}")

                if summ:

                    try:

                        print("Вызываем summarize...")

                        output_text = summ.summarize(

                            input_text,

                            max_length=length_param * 20,

                            min_length=length_param * 10

                        )

                        print("Суммаризация выполнена")

                    except Exception as e:

                        print(f"Ошибка при вызове summarize: {e}")

                        output_text = f"Ошибка: {e}"

                else:

                    output_text = "Абстрактивная модель не загрузилась. Попробуй позже."

        except Exception as e:
            print(f"ОШИБКА: {str(e)}")
            output_text = f"Ошибка: {str(e)}"

        processing_time = time.time() - start_time
        print(f"Время обработки: {processing_time} сек")

        data = {
            'input_text': input_text,
            'output_text': output_text,
            'summary_type': summary_type,
            'length_param': length_param,
            'processing_time': processing_time
        }

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        print("=== ЗАПРОС ОБРАБОТАН ===")
        return Response(serializer.data)


class FileUploadViewSet(viewsets.ModelViewSet):
    serializer_class = UploadedFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = UploadedFile.objects.all()

    def get_queryset(self):
        return UploadedFile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response(
                {'error': 'Файл не выбран'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверка размера (макс 10 МБ)
        if uploaded_file.size > 10 * 1024 * 1024:
            return Response(
                {'error': 'Файл слишком большой (макс 10 МБ)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Определяем тип файла
        filename = uploaded_file.name
        if filename.endswith('.txt'):
            file_type = 'txt'
        elif filename.endswith('.pdf'):
            file_type = 'pdf'
        elif filename.endswith('.docx'):
            file_type = 'docx'
        else:
            return Response(
                {'error': 'Поддерживаются только .txt, .pdf, .docx'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Сохраняем временно файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_type}') as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        try:
            # Извлекаем текст
            extracted_text = FileProcessor.extract_text(tmp_path)

            # Создаем запись в БД
            data = {
                'original_filename': filename,
                'file_size': uploaded_file.size,
                'file_type': file_type,
                'extracted_text': extracted_text
            }

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            return Response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        finally:
            # Удаляем временный файл
            os.unlink(tmp_path)

    @action(detail=True, methods=['post'])
    def summarize(self, request, pk=None):
        file_record = self.get_object()

        if not file_record.extracted_text:
            return Response(
                {'error': 'Не удалось извлечь текст из файла'},
                status=status.HTTP_400_BAD_REQUEST
            )

        summary_type = request.data.get('summary_type', 'extractive')
        length_param = int(request.data.get('length_param', 5))

        start_time = time.time()

        if summary_type == 'extractive':
            output_text = extractive_summarizer.summarize(
                file_record.extracted_text,
                length_param
            )
        elif summary_type == 'abstractive':
            summ = get_abstractive_summarizer()
            if summ:
                output_text = summ.summarize(
                    file_record.extracted_text,
                    max_length=length_param * 20,
                    min_length=length_param * 10
                )
            else:
                output_text = "Абстрактивная модель не загружена"
        else:
            output_text = "Неизвестный тип суммаризации"

        processing_time = time.time() - start_time

        # Сохраняем результат как обычный запрос
        summary_data = {
            'input_text': file_record.extracted_text[:500] + "...",
            'output_text': output_text,
            'summary_type': summary_type,
            'length_param': length_param,
            'processing_time': processing_time
        }

        summary_serializer = SummaryRequestSerializer(data=summary_data)
        summary_serializer.is_valid(raise_exception=True)
        summary_serializer.save(user=request.user)

        return Response({
            'file': serializer.data,
            'summary': summary_serializer.data
        })