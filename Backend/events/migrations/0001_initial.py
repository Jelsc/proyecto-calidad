from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TrafficEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_ip", models.GenericIPAddressField()),
                ("destination_ip", models.GenericIPAddressField()),
                ("protocol", models.CharField(max_length=16)),
                ("destination_port", models.PositiveIntegerField(blank=True, null=True)),
                ("payload", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("ingested_by", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
    ]
