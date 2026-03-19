from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0004_chatmessage_image_and_content_blank"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="chatmessage",
            new_name="chat_chatme_is_read_24fa80_idx",
            old_name="chat_chatme_is_read_97dd73_idx",
        ),
    ]
