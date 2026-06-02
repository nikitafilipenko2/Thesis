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
        print("=== Р РњР•РўР Р” SUMMARIZE Р вЂ™Р В«Р вЂ”Р вЂ™Р С’Р Сњ ===")

        input_text = request.data.get('input_text', '')
        model = request.data.get('model', 'extractive_textrank')
        length_param = request.data.get('length_param', 5)

        print(f"Р СљР С•Р Т‘Р ВµР В»РЎРЉ: {model}")
        print(f"Р СџР В°РЎР‚Р В°Р СР ВµРЎвЂљРЎР‚РЎвЂ№ Р Т‘Р В»Р С‘Р Р…РЎвЂ№: {length_param}")
        print(f"Р вЂќР В»Р С‘Р Р…Р В° РЎвЂљР ВµР С”РЎРѓРЎвЂљР В°: {len(input_text)} РЎРѓР С‘Р СР Р†Р С•Р В»Р С•Р Р†")

        if not input_text:
            return Response(
                {'error': 'Р СћР ВµР С”РЎРѓРЎвЂљ Р Р…Р Вµ Р СР С•Р В¶Р ВµРЎвЂљ Р В±РЎвЂ№РЎвЂљРЎРЉ Р С—РЎС“РЎРѓРЎвЂљРЎвЂ№Р С'},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_time = time.time()

        try:
            summarizer = get_model(model)

            if not summarizer:
                return Response(
                    {'error': f'Р СљР С•Р Т‘Р ВµР В»РЎРЉ {model} Р Р…Р Вµ Р Р…Р В°Р в„–Р Т‘Р ВµР Р…Р В°'},
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
            print(f"Р С›Р РЃР ВР вЂР С™Р С’: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Р С›РЎв‚¬Р С‘Р В±Р С”Р В°: {str(e)}'},
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

        print(f"Р РЋР С•РЎвЂ¦РЎР‚Р В°Р Р…Р ВµР Р…Р С•, ID: {serializer.data.get('id')}")
        print(f"Р вЂ™РЎР‚Р ВµР СРЎРЏ Р С•Р В±РЎР‚Р В°Р В±Р С•РЎвЂљР С”Р С‘: {processing_time} РЎРѓР ВµР С”")
        print("=== Р вЂ”Р С’Р СџР В Р С›Р РЋ Р С›Р вЂР В Р С’Р вЂР С›Р СћР С’Р Сњ ===")

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
                {'error': 'Р В¤Р В°Р в„–Р В» Р Р…Р Вµ Р Р†РЎвЂ№Р В±РЎР‚Р В°Р Р…'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if uploaded_file.size > 10 * 1024 * 1024:
            return Response(
                {'error': 'Р В¤Р В°Р в„–Р В» РЎРѓР В»Р С‘РЎв‚¬Р С”Р С•Р С Р В±Р С•Р В»РЎРЉРЎв‚¬Р С•Р в„– (Р СР В°Р С”РЎРѓ 10 Р СљР вЂ)'},
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
                {'error': 'Р СџР С•Р Т‘Р Т‘Р ВµРЎР‚Р В¶Р С‘Р Р†Р В°РЎР‹РЎвЂљРЎРѓРЎРЏ РЎвЂљР С•Р В»РЎРЉР С”Р С• .txt, .pdf, .docx'},
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
                {'error': 'Р СњР Вµ РЎС“Р Т‘Р В°Р В»Р С•РЎРѓРЎРЉ Р С‘Р В·Р Р†Р В»Р ВµРЎвЂЎРЎРЉ РЎвЂљР ВµР С”РЎРѓРЎвЂљ Р С‘Р В· РЎвЂћР В°Р в„–Р В»Р В°'},
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
                output_text = "Р С’Р В±РЎРѓРЎвЂљРЎР‚Р В°Р С”РЎвЂљР С‘Р Р†Р Р…Р В°РЎРЏ Р СР С•Р Т‘Р ВµР В»РЎРЉ Р Р…Р Вµ Р В·Р В°Р С–РЎР‚РЎС“Р В¶Р ВµР Р…Р В°"
        else:
            output_text = "Р СњР ВµР С‘Р В·Р Р†Р ВµРЎРѓРЎвЂљР Р…РЎвЂ№Р в„– РЎвЂљР С‘Р С— РЎРѓРЎС“Р СР СР В°РЎР‚Р С‘Р В·Р В°РЎвЂ Р С‘Р С‘"

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
