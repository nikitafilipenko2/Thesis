from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import SummaryRequest
from .models import UploadedFile
from .serializers import SummaryRequestSerializer
from .serializers import UploadedFileSerializer
from .file_processor import FileProcessor
from .services.model_service import get_model
import time
import tempfile
import os


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
        input_text = request.data.get('input_text', '')
        model = request.data.get('model', 'extractive_textrank')
        length_param = request.data.get('length_param', 5)

        if not input_text:
            return Response(
                {'error': 'Текст не может быть пустым'},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_time = time.time()

        try:
            summarizer = get_model(model)

            if not summarizer:
                return Response(
                    {'error': f'Модель {model} не найдена'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if model.startswith('extractive'):
                if isinstance(length_param, dict):
                    sentences_count = 5
                else:
                    sentences_count = int(length_param)

                output_text = summarizer.summarize(input_text, sentences_count)
                length_value = sentences_count
            else:
                if isinstance(length_param, dict):
                    min_words = int(length_param.get('min', 50))
                    max_words = int(length_param.get('max', 150))
                else:
                    max_words = int(length_param) * 20
                    min_words = max_words // 2

                output_text = summarizer.summarize(
                    input_text,
                    max_length=max_words,
                    min_length=min_words
                )
                length_value = max_words
        except Exception as e:
            return Response(
                {'error': f'Ошибка: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        processing_time = time.time() - start_time

        data = {
            'input_text': input_text,
            'output_text': output_text,
            'summary_type': 'extractive' if model.startswith('extractive') else 'abstractive',
            'model_name': model,
            'length_param': length_value,
            'processing_time': processing_time
        }

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors, 'data': data},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_create(serializer)
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

        if uploaded_file.size > 10 * 1024 * 1024:
            return Response(
                {'error': 'Файл слишком большой (макс 10 МБ)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        filename = uploaded_file.name
        normalized_filename = filename.lower()
        allowed_content_types = {
            'txt': {'text/plain', 'application/octet-stream'},
            'pdf': {'application/pdf', 'application/octet-stream'},
            'docx': {
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/octet-stream',
            },
        }

        if normalized_filename.endswith('.txt'):
            file_type = 'txt'
        elif normalized_filename.endswith('.pdf'):
            file_type = 'pdf'
        elif normalized_filename.endswith('.docx'):
            file_type = 'docx'
        else:
            return Response(
                {'error': 'Поддерживаются только .txt, .pdf, .docx'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if uploaded_file.content_type not in allowed_content_types[file_type]:
            return Response(
                {'error': 'Неверный тип файла'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_type}') as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        try:
            extracted_text = FileProcessor.extract_text(tmp_path)

            if not extracted_text or not extracted_text.strip():
                return Response(
                    {'error': 'Из файла не удалось извлечь текст'},
                    status=status.HTTP_400_BAD_REQUEST
                )

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
            summarizer = get_model('extractive_textrank')
            model_name = 'extractive_textrank'
            output_text = summarizer.summarize(
                file_record.extracted_text,
                length_param
            )
        elif summary_type == 'abstractive':
            summarizer = get_model('abstractive_cointegrated')
            model_name = 'abstractive_cointegrated'
            if summarizer:
                output_text = summarizer.summarize(
                    file_record.extracted_text,
                    max_length=length_param * 20,
                    min_length=length_param * 10
                )
            else:
                output_text = 'Абстрактивная модель не загружена'
        else:
            model_name = ''
            output_text = 'Неизвестный тип суммаризации'

        processing_time = time.time() - start_time

        summary_data = {
            'input_text': file_record.extracted_text,
            'output_text': output_text,
            'summary_type': summary_type,
            'model_name': model_name,
            'length_param': length_param,
            'processing_time': processing_time
        }

        summary_serializer = SummaryRequestSerializer(data=summary_data)
        summary_serializer.is_valid(raise_exception=True)
        summary_serializer.save(user=request.user)

        file_serializer = self.get_serializer(file_record)

        return Response({
            'file': file_serializer.data,
            'summary': summary_serializer.data
        })
