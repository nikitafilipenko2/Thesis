from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import SummaryRequest
from .models import UploadedFile


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
