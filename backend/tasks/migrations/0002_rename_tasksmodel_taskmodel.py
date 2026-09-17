from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("tasks", "0001_initial")]

    operations = [
        migrations.RenameModel(old_name="TasksModel", new_name="TaskModel"),
    ]
