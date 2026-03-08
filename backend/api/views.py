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
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages



extractive_summarizer = ExtractiveSummarizer(method='textrank')
abstractive_summarizer = None  # Пока не загружаем

_models = {}


def load_all_models():
    """Загружает все модели при старте приложения"""
    print("=" * 50)
    print("ЗАГРУЗКА ВСЕХ МОДЕЛЕЙ...")
    print("=" * 50)

    # Экстрактивные модели (они легкие, грузятся быстро)
    print("Загрузка экстрактивных моделей...")
    _models['extractive_textrank'] = ExtractiveSummarizer(method='textrank')
    _models['extractive_lsa'] = ExtractiveSummarizer(method='lsa')
    _models['extractive_lexrank'] = ExtractiveSummarizer(method='lexrank')
    print("✓ Экстрактивные модели загружены")

    # Абстрактивные модели (тяжелые, могут долго грузиться)
    print("\nЗагрузка абстрактивных моделей (это может занять несколько минут)...")

    try:
        print("  - Загрузка cointegrated/rut5-base-absum (500 МБ)...")
        _models['abstractive_cointegrated'] = AbstractiveSummarizer(
            model_name="cointegrated/rut5-base-absum"
        )
        print("  ✓ cointegrated загружена")
    except Exception as e:
        print(f"  ✗ Ошибка загрузки cointegrated: {e}")

    # try:
    #     print("  - Загрузка IlyaGusev/rut5_base_sum_gazeta (1.5 ГБ)...")
    #     _models['abstractive_rut5'] = AbstractiveSummarizer(
    #         model_name="IlyaGusev/rut5_base_sum_gazeta"
    #     )
    #     print("  ✓ ruT5 загружена")
    # except Exception as e:
    #     print(f"  ✗ Ошибка загрузки ruT5: {e}")
    #
    # try:
    #     print("  - Загрузка IlyaGusev/mbart_ru_sum_gazeta (5 ГБ)...")
    #     _models['abstractive_mbart'] = AbstractiveSummarizer(
    #         model_name="IlyaGusev/mbart_ru_sum_gazeta"
    #     )
    #     print("  ✓ mBART загружена")
    # except Exception as e:
    #     print(f"  ✗ Ошибка загрузки mBART: {e}")

    print("\n" + "=" * 50)
    print(f"ЗАГРУЖЕНО МОДЕЛЕЙ: {len(_models)}")
    print("=" * 50)

    return _models


def get_model(model_name):
    """Возвращает модель из кэша"""
    if not _models:
        load_all_models()
    return _models.get(model_name)
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
        model = request.data.get('model', 'extractive_textrank')
        length_param = request.data.get('length_param', 5)

        print(f"Модель: {model}")
        print(f"Параметры длины: {length_param}")
        print(f"Длина текста: {len(input_text)} символов")

        if not input_text:
            return Response(
                {'error': 'Текст не может быть пустым'},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_time = time.time()

        try:
            # Получаем модель из кэша
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
            print(f"ОШИБКА: {str(e)}")
            import traceback
            traceback.print_exc()
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

        print(f"Сохранено, ID: {serializer.data.get('id')}")
        print(f"Время обработки: {processing_time} сек")
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

        # Сериализуем сам файл для ответа
        file_serializer = self.get_serializer(file_record)

        return Response({
            'file': file_serializer.data,
            'summary': summary_serializer.data
        })


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, 'Вы успешно вошли')
            return redirect('home')
        else:
            messages.error(request, 'Неверный логин или пароль')
    return render(request, 'api/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Вы вышли из системы')
    return redirect('login')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            messages.error(request, 'Пароли не совпадают')
        elif len(password) < 6:
            messages.error(request, 'Пароль должен быть не менее 6 символов')
        else:
            from django.contrib.auth.models import User
            try:
                user = User.objects.create_user(username=username, password=password)
                messages.success(request, 'Регистрация успешна! Теперь войдите')
                return redirect('login')
            except:
                messages.error(request, 'Пользователь с таким именем уже существует')

    return render(request, 'api/register.html')


@login_required
def home_view(request):
    return render(request, 'api/home.html')


@login_required
def history_view(request):
    requests_list = SummaryRequest.objects.filter(user=request.user).order_by('-created_at')[:50]
    return render(request, 'api/history.html', {'requests': requests_list})


@login_required
def files_view(request):
    files_list = UploadedFile.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'api/files.html', {'files': files_list})


@login_required
def request_detail_view(request, pk):
    req = get_object_or_404(SummaryRequest, pk=pk, user=request.user)
    return render(request, 'api/request_detail.html', {'request': req})

load_all_models()