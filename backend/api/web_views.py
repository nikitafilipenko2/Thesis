import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .models import SummaryRequest, UploadedFile
from .serializers import SummaryRequestSerializer, UploadedFileSerializer
from .services.file_service import FileServiceError, extract_uploaded_file
from .services.model_service import get_abstractive_model_choices
from .services.summarization_service import (
    SummarizationServiceError,
    summarize_file_text,
    summarize_text,
)


def _save_summary_request(user, payload):
    serializer = SummaryRequestSerializer(
        data={
            "input_text": payload.input_text,
            "output_text": payload.output_text,
            "summary_type": payload.summary_type,
            "model_name": payload.model_name,
            "length_param": payload.length_param,
            "processing_time": payload.processing_time,
        }
    )
    serializer.is_valid(raise_exception=True)
    serializer.save(user=user)


def _render_feedback(request, template_name, message, level, status=200):
    return render(
        request,
        template_name,
        {"message": message, "level": level},
        status=status,
    )


@login_required
def home_view(request):
    return render(
        request,
        "api/home.html",
        {"abstractive_models": get_abstractive_model_choices()},
    )


@login_required
def history_view(request):
    requests_list = SummaryRequest.objects.filter(user=request.user).order_by("-created_at")[:50]
    return render(request, "api/history.html", {"requests": requests_list})


@login_required
def files_view(request):
    files_list = UploadedFile.objects.filter(user=request.user).order_by("-uploaded_at")
    return render(
        request,
        "api/files.html",
        {
            "files": files_list,
            "abstractive_models": get_abstractive_model_choices(),
        },
    )


@login_required
def request_detail_view(request, pk):
    summary_request = get_object_or_404(SummaryRequest, pk=pk, user=request.user)
    return render(request, "api/request_detail.html", {"request": summary_request})


@login_required
@require_POST
def home_upload_view(request):
    try:
        processed_upload = extract_uploaded_file(request.FILES.get("file"))
    except FileServiceError as error:
        return _render_feedback(
            request,
            "api/partials/home_feedback.html",
            str(error),
            "danger",
            status=400,
        )

    serializer = UploadedFileSerializer(
        data={
            "original_filename": processed_upload.original_filename,
            "file_size": processed_upload.file_size,
            "file_type": processed_upload.file_type,
            "extracted_text": processed_upload.extracted_text,
        }
    )
    serializer.is_valid(raise_exception=True)
    serializer.save(user=request.user)

    response = _render_feedback(
        request,
        "api/partials/home_feedback.html",
        f"Файл загружен: {processed_upload.original_filename}",
        "success",
    )
    response["HX-Trigger"] = json.dumps(
        {
            "homeFileUploaded": {
                "text": processed_upload.extracted_text,
                "filename": processed_upload.original_filename,
            }
        }
    )
    return response


@login_required
@require_POST
def home_summarize_view(request):
    model_name = request.POST.get("model", "extractive_textrank")

    try:
        if model_name.startswith("extractive"):
            length_param = request.POST.get("sentence_count", 5)
        else:
            length_param = {
                "min": request.POST.get("min_words", 50),
                "max": request.POST.get("max_words", 150),
            }

        payload = summarize_text(
            input_text=request.POST.get("input_text", ""),
            model_name=model_name,
            length_param=length_param,
        )
        _save_summary_request(request.user, payload)
    except SummarizationServiceError as error:
        return render(
            request,
            "api/partials/home_summary_result.html",
            {"error": str(error)},
            status=400,
        )
    except Exception:
        return render(
            request,
            "api/partials/home_summary_result.html",
            {"error": "Не удалось сохранить результат суммаризации"},
            status=500,
        )

    context = {
        "output_text": payload.output_text,
        "processing_time": payload.processing_time,
        "words_count": len(payload.output_text.split()),
        "sentences_count": len(
            [
                item
                for item in payload.output_text.replace("!", ".").replace("?", ".").split(".")
                if item.strip()
            ]
        ),
    }
    return render(request, "api/partials/home_summary_result.html", context)


@login_required
@require_POST
def file_summarize_view(request, pk):
    file_record = get_object_or_404(UploadedFile, pk=pk, user=request.user)

    try:
        payload = summarize_file_text(
            input_text=file_record.extracted_text,
            summary_type=request.POST.get("summary_type", "extractive"),
            length_param=request.POST.get("length_param", 5),
            model_name=request.POST.get("model_name"),
        )
        _save_summary_request(request.user, payload)
    except SummarizationServiceError as error:
        return _render_feedback(
            request,
            "api/partials/file_summary_feedback.html",
            str(error),
            "danger",
            status=400,
        )
    except Exception:
        return _render_feedback(
            request,
            "api/partials/file_summary_feedback.html",
            "Не удалось сохранить результат суммаризации",
            "danger",
            status=500,
        )

    response = HttpResponse("")
    response["HX-Redirect"] = "/history/"
    return response
