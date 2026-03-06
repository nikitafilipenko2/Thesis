from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import SummaryRequest
from .serializers import SummaryRequestSerializer


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
        data = request.data.copy()
        data['output_text'] = "Здесь будет результат суммаризации. Это временный ответ."

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(serializer.data)