from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_uploadedfile'),
    ]

    operations = [
        migrations.AddField(
            model_name='summaryrequest',
            name='model_name',
            field=models.CharField(blank=True, max_length=100, verbose_name='Название модели'),
        ),
    ]
