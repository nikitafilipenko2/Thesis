from django.contrib import admin
from .models import SummaryRequest

@admin.register(SummaryRequest)
class SummaryRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'summary_type', 'created_at', 'processing_time')
    list_filter = ('summary_type', 'created_at')
    search_fields = ('user__username', 'input_text')