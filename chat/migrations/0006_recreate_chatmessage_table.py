from django.db import migrations


def create_chatmessage_table(apps, schema_editor):
    existing_tables = set(schema_editor.connection.introspection.table_names())
    if "chat_chatmessage" in existing_tables:
        return

    ChatMessage = apps.get_model("chat", "ChatMessage")
    schema_editor.create_model(ChatMessage)


def drop_chatmessage_table(apps, schema_editor):
    existing_tables = set(schema_editor.connection.introspection.table_names())
    if "chat_chatmessage" not in existing_tables:
        return

    ChatMessage = apps.get_model("chat", "ChatMessage")
    schema_editor.delete_model(ChatMessage)


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0016_booking_bookingacceptancenotification_and_more"),
        ("chat", "0005_rename_chat_chatme_is_read_97dd73_idx_chat_chatme_is_read_24fa80_idx"),
    ]

    operations = [
        migrations.RunPython(create_chatmessage_table, drop_chatmessage_table),
    ]
