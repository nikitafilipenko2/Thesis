from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_summaryrequest_model_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='uploadedfile',
            name='file',
        ),
    ]
