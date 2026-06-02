from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from rest_framework.test import APIClient

from api.abstractive import AbstractiveSummarizer
from api.models import SummaryRequest, UploadedFile
from api.services.file_service import FileServiceError, ProcessedUpload
from api.services.summarization_service import SummarizationServiceError, summarize_file_text, summarize_text


class SummarizationServiceTests(TestCase):
    def test_summarize_text_rejects_empty_input(self):
        with self.assertRaises(SummarizationServiceError):
            summarize_text("", "extractive_textrank", 3)

    @patch("api.services.summarization_service.get_model")
    @patch("api.services.summarization_service.is_extractive_model", return_value=True)
    def test_summarize_text_uses_extractive_model(self, is_extractive_model, get_model):
        summarizer = Mock()
        summarizer.summarize.return_value = "Краткий результат"
        get_model.return_value = summarizer

        payload = summarize_text("Исходный текст", "extractive_textrank", 4)

        summarizer.summarize.assert_called_once_with("Исходный текст", 4)
        self.assertEqual(payload.summary_type, "extractive")
        self.assertEqual(payload.output_text, "Краткий результат")
        self.assertEqual(payload.model_name, "extractive_textrank")

    @patch("api.services.summarization_service.get_model")
    @patch("api.services.summarization_service.is_extractive_model", return_value=False)
    def test_summarize_text_uses_abstractive_model(self, is_extractive_model, get_model):
        summarizer = Mock()
        summarizer.summarize.return_value = "Абстрактивный результат"
        get_model.return_value = summarizer

        payload = summarize_text(
            "Научный текст",
            "cointegrated/rut5-base-absum",
            {"min": 40, "max": 120},
        )

        summarizer.summarize.assert_called_once_with(
            "Научный текст",
            max_length=120,
            min_length=40,
        )
        self.assertEqual(payload.summary_type, "abstractive")
        self.assertEqual(payload.length_param, 120)

    @patch("api.services.summarization_service.summarize_text")
    def test_summarize_file_text_uses_default_abstractive_model(self, summarize_text_mock):
        summarize_text_mock.return_value = SimpleNamespace()

        summarize_file_text("Текст", "abstractive", 5)

        summarize_text_mock.assert_called_once_with("Текст", "cointegrated/rut5-base-absum", 5)


class AbstractiveSummarizerTests(TestCase):
    def test_build_chunks_splits_long_text(self):
        summarizer = AbstractiveSummarizer.__new__(AbstractiveSummarizer)
        summarizer.model_name = "cointegrated/rut5-base-absum"
        summarizer.CHUNK_SIZE = 60
        summarizer.CHUNK_OVERLAP = 10

        text = (
            "Первое предложение достаточно длинное для теста. "
            "Второе предложение тоже длинное. "
            "Третье предложение завершает пример."
        )
        chunks = summarizer._build_chunks(text)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 60 for chunk in chunks))

    def test_summarize_runs_pipeline_for_each_chunk_and_final_merge(self):
        summarizer = AbstractiveSummarizer.__new__(AbstractiveSummarizer)
        summarizer.model_name = "cointegrated/rut5-base-absum"
        summarizer.CHUNK_SIZE = 40
        summarizer.CHUNK_OVERLAP = 5
        summarizer.summarizer = Mock(
            side_effect=[
                [{"summary_text": "summary one"}],
                [{"summary_text": "summary two"}],
                [{"summary_text": "summary three"}],
                [{"summary_text": "final summary"}],
            ]
        )

        result = AbstractiveSummarizer.summarize(
            summarizer,
            "Первое длинное предложение для теста. Второе длинное предложение для теста.",
            max_length=80,
            min_length=30,
        )

        self.assertEqual(result, "final summary")
        self.assertGreaterEqual(summarizer.summarizer.call_count, 3)


class WebViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="secret123")
        self.client = Client()
        self.client.login(username="tester", password="secret123")

    def test_home_page_contains_footer_text(self):
        response = self.client.get("/")

        self.assertContains(
            response,
            "Выпускная квалификационная работа студента направления 02.03.03 Филипенко Н.С.",
        )
        self.assertContains(response, "Краснодар")
        self.assertContains(response, "2026 г.")
        self.assertContains(response, "КубГУ")

    @patch("api.web_views.summarize_text")
    def test_home_summarize_view_saves_summary_request(self, summarize_text_mock):
        summarize_text_mock.return_value = SimpleNamespace(
            input_text="Большой текст",
            output_text="Краткое содержание",
            summary_type="extractive",
            model_name="extractive_textrank",
            length_param=3,
            processing_time=0.12,
        )

        response = self.client.post(
            "/summarize/",
            {
                "input_text": "Большой текст",
                "model": "extractive_textrank",
                "sentence_count": 3,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(SummaryRequest.objects.count(), 1)
        saved = SummaryRequest.objects.get()
        self.assertEqual(saved.model_name, "extractive_textrank")
        self.assertContains(response, "Краткое содержание")

    @patch("api.web_views.extract_uploaded_file")
    def test_home_upload_view_saves_uploaded_file(self, extract_uploaded_file_mock):
        extract_uploaded_file_mock.return_value = ProcessedUpload(
            original_filename="sample.txt",
            file_size=12,
            file_type="txt",
            extracted_text="Извлеченный текст",
        )

        upload = SimpleUploadedFile("sample.txt", b"text", content_type="text/plain")
        response = self.client.post("/upload/", {"file": upload})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(UploadedFile.objects.count(), 1)
        self.assertContains(response, "Файл загружен: sample.txt")


class ApiViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="apiuser", password="secret123")
        self.client = APIClient()
        self.client.login(username="apiuser", password="secret123")

    @patch("api.api_views.summarize_text")
    def test_api_summarize_creates_summary_request(self, summarize_text_mock):
        summarize_text_mock.return_value = SimpleNamespace(
            input_text="Исходный текст",
            output_text="Результат",
            summary_type="extractive",
            model_name="extractive_textrank",
            length_param=2,
            processing_time=0.08,
        )

        response = self.client.post(
            "/api/requests/summarize/",
            {
                "input_text": "Исходный текст",
                "model": "extractive_textrank",
                "length_param": 2,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(SummaryRequest.objects.count(), 1)
        self.assertEqual(response.data["model_name"], "extractive_textrank")

    @patch("api.api_views.extract_uploaded_file")
    def test_api_upload_creates_uploaded_file_record(self, extract_uploaded_file_mock):
        extract_uploaded_file_mock.return_value = ProcessedUpload(
            original_filename="paper.txt",
            file_size=21,
            file_type="txt",
            extracted_text="Текст файла",
        )

        upload = SimpleUploadedFile("paper.txt", b"text", content_type="text/plain")
        response = self.client.post("/api/files/upload/", {"file": upload})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(UploadedFile.objects.count(), 1)
        self.assertEqual(response.data["original_filename"], "paper.txt")

    @patch("api.api_views.summarize_file_text")
    def test_api_file_summarize_creates_summary_request(self, summarize_file_text_mock):
        file_record = UploadedFile.objects.create(
            user=self.user,
            original_filename="paper.txt",
            file_size=21,
            file_type="txt",
            extracted_text="Текст файла",
        )
        summarize_file_text_mock.return_value = SimpleNamespace(
            input_text="Текст файла",
            output_text="Краткое содержание файла",
            summary_type="abstractive",
            model_name="cointegrated/rut5-base-absum",
            length_param=100,
            processing_time=0.33,
        )

        response = self.client.post(
            f"/api/files/{file_record.id}/summarize/",
            {
                "summary_type": "abstractive",
                "model_name": "cointegrated/rut5-base-absum",
                "length_param": 5,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(SummaryRequest.objects.count(), 1)
        self.assertEqual(response.data["summary"]["model_name"], "cointegrated/rut5-base-absum")

    @patch("api.api_views.extract_uploaded_file", side_effect=FileServiceError("Файл не выбран"))
    def test_api_upload_returns_validation_error(self, extract_uploaded_file_mock):
        response = self.client.post("/api/files/upload/", {})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Файл не выбран")
