from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import SummaryRequest
from .models import UploadedFile
from .serializers import SummaryRequestSerializer
from .serializers import UploadedFileSerializer
from .file_processor import FileProcessor
from .services.model_service import get_model
import json
import time
import tempfile
import os


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


@login_required
@require_POST
def home_upload_view(request):
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return render(
            request,
            'api/partials/home_feedback.html',
            {'message': 'Файл не выбран', 'level': 'danger'},
            status=400,
        )

    if uploaded_file.size > 10 * 1024 * 1024:
        return render(
            request,
            'api/partials/home_feedback.html',
            {'message': 'Файл слишком большой (макс 10 МБ)', 'level': 'danger'},
            status=400,
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
        return render(
            request,
            'api/partials/home_feedback.html',
            {'message': 'Поддерживаются только .txt, .pdf, .docx', 'level': 'danger'},
            status=400,
        )

    if uploaded_file.content_type not in allowed_content_types[file_type]:
        return render(
            request,
            'api/partials/home_feedback.html',
            {'message': 'Неверный тип файла', 'level': 'danger'},
            status=400,
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_type}') as tmp:
        for chunk in uploaded_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        extracted_text = FileProcessor.extract_text(tmp_path)

        if not extracted_text or not extracted_text.strip():
            return render(
                request,
                'api/partials/home_feedback.html',
                {'message': 'Из файла не удалось извлечь текст', 'level': 'danger'},
                status=400,
            )

        data = {
            'original_filename': filename,
            'file_size': uploaded_file.size,
            'file_type': file_type,
            'extracted_text': extracted_text,
        }

        serializer = UploadedFileSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        response = render(
            request,
            'api/partials/home_feedback.html',
            {'message': f'Файл загружен: {filename}', 'level': 'success'},
        )
        response['HX-Trigger'] = json.dumps({
            'homeFileUploaded': {
                'text': extracted_text,
                'filename': filename,
            }
        })
        return response
    except Exception as e:
        return render(
            request,
            'api/partials/home_feedback.html',
            {'message': str(e), 'level': 'danger'},
            status=400,
        )
    finally:
        os.unlink(tmp_path)


@login_required
@require_POST
def home_summarize_view(request):
    input_text = request.POST.get('input_text', '')
    model = request.POST.get('model', 'extractive_textrank')

    if not input_text.strip():
        return render(
            request,
            'api/partials/home_summary_result.html',
            {'error': 'Введите текст или загрузите файл'},
            status=400,
        )

    start_time = time.time()

    try:
        summarizer = get_model(model)
        if not summarizer:
            return render(
                request,
                'api/partials/home_summary_result.html',
                {'error': f'Модель {model} не найдена'},
                status=400,
            )

        if model.startswith('extractive'):
            sentences_count = int(request.POST.get('sentence_count', 5))
            output_text = summarizer.summarize(input_text, sentences_count)
            length_value = sentences_count
        else:
            min_words = int(request.POST.get('min_words', 50))
            max_words = int(request.POST.get('max_words', 150))
            output_text = summarizer.summarize(
                input_text,
                max_length=max_words,
                min_length=min_words,
            )
            length_value = max_words
    except Exception as e:
        return render(
            request,
            'api/partials/home_summary_result.html',
            {'error': f'Ошибка: {str(e)}'},
            status=500,
        )

    processing_time = time.time() - start_time

    data = {
        'input_text': input_text,
        'output_text': output_text,
        'summary_type': 'extractive' if model.startswith('extractive') else 'abstractive',
        'model_name': model,
        'length_param': length_value,
        'processing_time': processing_time,
    }

    serializer = SummaryRequestSerializer(data=data)
    if not serializer.is_valid():
        return render(
            request,
            'api/partials/home_summary_result.html',
            {'error': 'Не удалось сохранить результат'},
            status=400,
        )

    serializer.save(user=request.user)

    context = {
        'output_text': output_text,
        'processing_time': processing_time,
        'words_count': len(output_text.split()),
        'sentences_count': len([item for item in output_text.replace('!', '.').replace('?', '.').split('.') if item.strip()]),
    }
    return render(request, 'api/partials/home_summary_result.html', context)


@login_required
@require_POST
def file_summarize_view(request, pk):
    file_record = get_object_or_404(UploadedFile, pk=pk, user=request.user)

    if not file_record.extracted_text:
        return render(
            request,
            'api/partials/file_summary_feedback.html',
            {'message': 'Не удалось извлечь текст из файла', 'level': 'danger'},
            status=400,
        )

    summary_type = request.POST.get('summary_type', 'extractive')

    try:
        length_param = int(request.POST.get('length_param', 5))
    except (TypeError, ValueError):
        return render(
            request,
            'api/partials/file_summary_feedback.html',
            {'message': 'Параметр длины должен быть числом', 'level': 'danger'},
            status=400,
        )

    start_time = time.time()

    if summary_type == 'extractive':
        summarizer = get_model('extractive_textrank')
        model_name = 'extractive_textrank'
        output_text = summarizer.summarize(file_record.extracted_text, length_param)
    elif summary_type == 'abstractive':
        summarizer = get_model('abstractive_cointegrated')
        model_name = 'abstractive_cointegrated'
        if not summarizer:
            return render(
                request,
                'api/partials/file_summary_feedback.html',
                {'message': 'Абстрактивная модель не загружена', 'level': 'danger'},
                status=400,
            )
        output_text = summarizer.summarize(
            file_record.extracted_text,
            max_length=length_param * 20,
            min_length=length_param * 10,
        )
    else:
        return render(
            request,
            'api/partials/file_summary_feedback.html',
            {'message': 'Неизвестный тип суммаризации', 'level': 'danger'},
            status=400,
        )

    processing_time = time.time() - start_time

    summary_data = {
        'input_text': file_record.extracted_text,
        'output_text': output_text,
        'summary_type': summary_type,
        'model_name': model_name,
        'length_param': length_param,
        'processing_time': processing_time,
    }

    serializer = SummaryRequestSerializer(data=summary_data)
    if not serializer.is_valid():
        return render(
            request,
            'api/partials/file_summary_feedback.html',
            {'message': 'Не удалось сохранить результат', 'level': 'danger'},
            status=400,
        )

    serializer.save(user=request.user)

    response = HttpResponse('')
    response['HX-Redirect'] = '/history/'
    return response
