from rest_framework import serializers
from .models import SummaryRequest
from .models import UploadedFile

class SummaryRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummaryRequest
        fields = ['id', 'input_text', 'output_text', 'summary_type',
                  'length_param', 'created_at', 'processing_time']
        read_only_fields = ['id', 'created_at']

class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'original_filename', 'file_size', 'file_type',
                  'extracted_text', 'uploaded_at']
        read_only_fields = ['id', 'extracted_text', 'uploaded_at']