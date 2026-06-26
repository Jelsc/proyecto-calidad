from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("incidents", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ResponseAction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "action_type",
                    models.CharField(
                        choices=[
                            ("alert", "Alert"),
                            ("isolate_host", "Isolate Host"),
                            ("block_ip", "Block IP"),
                            ("suspend_user", "Suspend User"),
                        ],
                        max_length=32,
                    ),
                ),
                ("target_value", models.CharField(blank=True, max_length=128)),
                ("notes", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("simulated", "Simulated"), ("executed", "Executed"), ("failed", "Failed")],
                        default="simulated",
                        max_length=16,
                    ),
                ),
                ("simulated", models.BooleanField(default=True)),
                ("control_mode", models.CharField(default="controlled", max_length=32)),
                ("executed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "incident",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="response_actions", to="incidents.incident"),
                ),
            ],
            options={
                "ordering": ("-executed_at",),
            },
        ),
    ]
