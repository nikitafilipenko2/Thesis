from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import SummaryRequest
from .models import UploadedFile
from .serializers import SummaryRequestSerializer
from .services.model_service import get_model
import time


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
