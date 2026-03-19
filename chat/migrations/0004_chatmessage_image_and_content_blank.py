from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0003_chatmessage_is_read"),
    ]

    operations = [
        migrations.AlterField(
            model_name="chatmessage",
            name="content",
            field=models.TextField(blank=True, default="", max_length=1000),
        ),
        migrations.AddField(
            model_name="chatmessage",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="chat_images/"),
        ),
    ]
