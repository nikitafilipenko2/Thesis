from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from api.models import SummaryRequest, UploadedFile
from api.serializers import SummaryRequestSerializer, UploadedFileSerializer
from api.services.file_service import FileServiceError, extract_uploaded_file
from api.services.summarization_service import (
    SummarizationServiceError,
    summarize_file_text,
    summarize_text,
)


class SummaryRequestViewSet(viewsets.ModelViewSet):
    serializer_class = SummaryRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = SummaryRequest.objects.all()

    def get_queryset(self):
        return SummaryRequest.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"])
    def summarize(self, request):
        input_text = request.data.get("input_text", "")
        model_name = request.data.get("model", "extractive_textrank")
        length_param = request.data.get("length_param", 5)

        try:
            summary = summarize_text(input_text, model_name, length_param)
        except SummarizationServiceError as error:
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response({"error": f"Ошибка: {error}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = self.get_serializer(data=summary.__dict__)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors, "data": summary.__dict__},
                status=status.HTTP_400_BAD_REQUEST,
            )

        self.perform_create(serializer)
        return Response(serializer.data)


class FileUploadViewSet(viewsets.ModelViewSet):
    serializer_class = UploadedFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = UploadedFile.objects.all()

    def get_queryset(self):
        return UploadedFile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"])
    def upload(self, request):
        try:
            processed_upload = extract_uploaded_file(request.FILES.get("file"))
        except FileServiceError as error:
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=processed_upload.__dict__)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def summarize(self, request, pk=None):
        file_record = self.get_object()

        if not file_record.extracted_text:
            return Response(
                {"error": "Не удалось извлечь текст из файла"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        summary_type = request.data.get("summary_type", "extractive")
        model_name = request.data.get("model_name")

        try:
            length_param = int(request.data.get("length_param", 5))
            summary = summarize_file_text(
                file_record.extracted_text,
                summary_type,
                length_param,
                model_name=model_name,
            )
        except (TypeError, ValueError):
            return Response(
                {"error": "Параметр длины должен быть числом"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except SummarizationServiceError as error:
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response({"error": f"Ошибка: {error}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = SummaryRequestSerializer(data=summary.__dict__)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        file_serializer = self.get_serializer(file_record)
        return Response({"file": file_serializer.data, "summary": serializer.data})
