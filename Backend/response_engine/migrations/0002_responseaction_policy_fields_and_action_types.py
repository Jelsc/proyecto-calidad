from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("response_engine", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="responseaction",
            name="decision_context",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="responseaction",
            name="policy_rule",
            field=models.CharField(default="manual_controlled_policy", max_length=64),
        ),
        migrations.AlterField(
            model_name="responseaction",
            name="action_type",
            field=models.CharField(
                choices=[
                    ("alert", "Alert"),
                    ("notify_admin", "Notify Admin"),
                    ("isolate_host", "Isolate Host"),
                    ("block_ip", "Block IP"),
                    ("limit_traffic", "Limit Traffic"),
                    ("cut_lateral_communication", "Cut Lateral Communication"),
                    ("mark_host_compromised", "Mark Host Compromised"),
                    ("suspend_user", "Suspend User"),
                ],
                max_length=32,
            ),
        ),
    ]
