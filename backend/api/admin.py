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

        if summary_type == 'extractive':
            try:
                print("Пытаюсь сделать суммаризацию...")
                output_text = summarizer.summarize(input_text, length_param)
                print(f"Суммаризация успешна, длина результата: {len(output_text)}")

                if len(output_text) == len(input_text):
                    print("ВНИМАНИЕ: Результат совпадает с исходным текстом!")
                    print("Пробуем другой метод...")
                    alt_summarizer = ExtractiveSummarizer(method='lsa')
                    output_text = alt_summarizer.summarize(input_text, length_param)
                    print(f"Альтернативный метод, длина результата: {len(output_text)}")

            except Exception as e:
                print(f"ОШИБКА при суммаризации: {str(e)}")
                output_text = f"Ошибка: {str(e)}"
        else:
            output_text = "Абстрактивный метод будет добавлен позже"

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