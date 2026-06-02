import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SummaryRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('input_text', models.TextField(verbose_name='Исходный текст')),
                ('output_text', models.TextField(blank=True, verbose_name='Реферат')),
                ('summary_type', models.CharField(choices=[('extractive', 'Экстрактивный'), ('abstractive', 'Абстрактивный')], max_length=20, verbose_name='Тип реферирования')),
                ('length_param', models.IntegerField(default=5, verbose_name='Параметр длины')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('processing_time', models.FloatField(blank=True, null=True, verbose_name='Время обработки (сек)')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Запрос на реферирование',
                'verbose_name_plural': 'Запросы на реферирование',
                'ordering': ['-created_at'],
            },
        ),
    ]
