from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import SummaryRequest
from .serializers import SummaryRequestSerializer
from .models import UploadedFile
from .serializers import UploadedFileSerializer
from .file_processor import FileProcessor
from .services.model_service import get_model
import time
import tempfile
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages


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
        print("=== РМЕТРД SUMMARIZE Р’Р«Р—Р’РђРќ ===")

        input_text = request.data.get('input_text', '')
        model = request.data.get('model', 'extractive_textrank')
        length_param = request.data.get('length_param', 5)

        print(f"РњРѕРґРµР»СЊ: {model}")
        print(f"РџР°СЂР°РјРµС‚СЂС‹ РґР»РёРЅС‹: {length_param}")
        print(f"Р”Р»РёРЅР° С‚РµРєСЃС‚Р°: {len(input_text)} СЃРёРјРІРѕР»РѕРІ")

        if not input_text:
            return Response(
                {'error': 'РўРµРєСЃС‚ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј'},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_time = time.time()

        try:
            summarizer = get_model(model)

            if not summarizer:
                return Response(
                    {'error': f'РњРѕРґРµР»СЊ {model} РЅРµ РЅР°Р№РґРµРЅР°'},
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
            print(f"РћРЁРР‘РљРђ: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'РћС€РёР±РєР°: {str(e)}'},
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

        print(f"РЎРѕС…СЂР°РЅРµРЅРѕ, ID: {serializer.data.get('id')}")
        print(f"Р’СЂРµРјСЏ РѕР±СЂР°Р±РѕС‚РєРё: {processing_time} СЃРµРє")
        print("=== Р—РђРџР РћРЎ РћР‘Р РђР‘РћРўРђРќ ===")

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
                {'error': 'Р¤Р°Р№Р» РЅРµ РІС‹Р±СЂР°РЅ'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if uploaded_file.size > 10 * 1024 * 1024:
            return Response(
                {'error': 'Р¤Р°Р№Р» СЃР»РёС€РєРѕРј Р±РѕР»СЊС€РѕР№ (РјР°РєСЃ 10 РњР‘)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        filename = uploaded_file.name
        if filename.endswith('.txt'):
            file_type = 'txt'
        elif filename.endswith('.pdf'):
            file_type = 'pdf'
        elif filename.endswith('.docx'):
            file_type = 'docx'
        else:
            return Response(
                {'error': 'РџРѕРґРґРµСЂР¶РёРІР°СЋС‚СЃСЏ С‚РѕР»СЊРєРѕ .txt, .pdf, .docx'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_type}') as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        try:
            extracted_text = FileProcessor.extract_text(tmp_path)

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
                {'error': 'РќРµ СѓРґР°Р»РѕСЃСЊ РёР·РІР»РµС‡СЊ С‚РµРєСЃС‚ РёР· С„Р°Р№Р»Р°'},
                status=status.HTTP_400_BAD_REQUEST
            )

        summary_type = request.data.get('summary_type', 'extractive')
        length_param = int(request.data.get('length_param', 5))

        start_time = time.time()

        if summary_type == 'extractive':
            summarizer = get_model('extractive_textrank')
            output_text = summarizer.summarize(
                file_record.extracted_text,
                length_param
            )
        elif summary_type == 'abstractive':
            summarizer = get_model('abstractive_cointegrated')
            if summarizer:
                output_text = summarizer.summarize(
                    file_record.extracted_text,
                    max_length=length_param * 20,
                    min_length=length_param * 10
                )
            else:
                output_text = "РђР±СЃС‚СЂР°РєС‚РёРІРЅР°СЏ РјРѕРґРµР»СЊ РЅРµ Р·Р°РіСЂСѓР¶РµРЅР°"
        else:
            output_text = "РќРµРёР·РІРµСЃС‚РЅС‹Р№ С‚РёРї СЃСѓРјРјР°СЂРёР·Р°С†РёРё"

        processing_time = time.time() - start_time

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
            messages.success(request, 'Р’С‹ СѓСЃРїРµС€РЅРѕ РІРѕС€Р»Рё')
            return redirect('home')
        else:
            messages.error(request, 'РќРµРІРµСЂРЅС‹Р№ Р»РѕРіРёРЅ РёР»Рё РїР°СЂРѕР»СЊ')
    return render(request, 'api/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Р’С‹ РІС‹С€Р»Рё РёР· СЃРёСЃС‚РµРјС‹')
    return redirect('login')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            messages.error(request, 'РџР°СЂРѕР»Рё РЅРµ СЃРѕРІРїР°РґР°СЋС‚')
        elif len(password) < 6:
            messages.error(request, 'РџР°СЂРѕР»СЊ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ РЅРµ РјРµРЅРµРµ 6 СЃРёРјРІРѕР»РѕРІ')
        else:
            from django.contrib.auth.models import User
            try:
                user = User.objects.create_user(username=username, password=password)
                messages.success(request, 'Р РµРіРёСЃС‚СЂР°С†РёСЏ СѓСЃРїРµС€РЅР°! РўРµРїРµСЂСЊ РІРѕР№РґРёС‚Рµ')
                return redirect('login')
            except:
                messages.error(request, 'РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ СЃ С‚Р°РєРёРј РёРјРµРЅРµРј СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚')

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
