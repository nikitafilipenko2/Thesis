from django.contrib import admin
from .models import SummaryRequest, UploadedFile


@admin.register(SummaryRequest)
class SummaryRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'summary_type', 'model_name', 'created_at', 'processing_time', 'short_input', 'short_output')
    list_filter = ('summary_type', 'model_name', 'created_at')
    search_fields = ('user__username', 'input_text', 'output_text', 'model_name')
    readonly_fields = ('input_text', 'output_text', 'created_at', 'processing_time')

    def short_input(self, obj):
        return obj.input_text[:50] + '...' if len(obj.input_text) > 50 else obj.input_text

    short_input.short_description = 'Исходный текст'

    def short_output(self, obj):
        return obj.output_text[:50] + '...' if len(obj.output_text) > 50 else obj.output_text

    short_output.short_description = 'Реферат'

    fieldsets = (
        ('Пользователь', {
            'fields': ('user',)
        }),
        ('Параметры', {
            'fields': ('summary_type', 'model_name', 'length_param', 'processing_time', 'created_at')
        }),
        ('Тексты', {
            'fields': ('input_text', 'output_text'),
            'classes': ('wide',)
        }),
    )


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'original_filename', 'user', 'file_type', 'file_size', 'uploaded_at')
    list_filter = ('file_type', 'uploaded_at')
    search_fields = ('original_filename', 'user__username')
    readonly_fields = ('extracted_text',)

    fieldsets = (
        ('Пользователь', {
            'fields': ('user',)
        }),
        ('Информация о файле', {
            'fields': ('original_filename', 'file_type', 'file_size', 'uploaded_at')
        }),
        ('Извлеченный текст', {
            'fields': ('extracted_text',),
            'classes': ('wide',)
        }),
    )
