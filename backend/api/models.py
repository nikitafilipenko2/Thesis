from django.db import models
from django.contrib.auth.models import User


class SummaryRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')
    input_text = models.TextField(verbose_name='Исходный текст')
    output_text = models.TextField(blank=True, verbose_name='Реферат')
    SUMMARY_TYPES = [
        ('extractive', 'Экстрактивный'),
        ('abstractive', 'Абстрактивный'),
    ]
    summary_type = models.CharField(max_length=20, choices=SUMMARY_TYPES, verbose_name='Тип реферирования')
    length_param = models.IntegerField(default=5, verbose_name='Параметр длины')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    processing_time = models.FloatField(null=True, blank=True, verbose_name='Время обработки (сек)')
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Запрос на реферирование'
        verbose_name_plural = 'Запросы на реферирование'
    def __str__(self):
        return f"Запрос #{self.id} от {self.created_at.strftime('%d.%m.%Y %H:%M')}"
