from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("detection", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="detectionresult",
            name="engine_version",
            field=models.CharField(default="ml-isoforest-v1", max_length=32),
        ),
    ]
