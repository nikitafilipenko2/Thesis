from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import SummaryRequest
from .serializers import SummaryRequestSerializer
from .summarization import ExtractiveSummarizer
import time

summarizer = ExtractiveSummarizer(method='textrank')


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
        summary_type = request.data.get('summary_type', 'extractive')
        length_param = int(request.data.get('length_param', 5))

        if not input_text:
            return Response(
                {'error': 'Текст не может быть пустым'},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_time = time.time()

        if summary_type == 'extractive':
            output_text = summarizer.summarize(input_text, length_param)
        else:
            output_text = "Абстрактивный метод будет добавлен позже"

        processing_time = time.time() - start_time

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

        return Response(serializer.data)