from rest_framework import serializers
from .models import SummaryRequest

class SummaryRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummaryRequest
        fields = ['id', 'input_text', 'output_text', 'summary_type',
                  'length_param', 'created_at', 'processing_time']
        read_only_fields = ['id', 'created_at', 'output_text', 'processing_time']