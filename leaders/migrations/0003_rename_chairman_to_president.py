from django.db import migrations


def forwards(apps, schema_editor):
    Leader = apps.get_model('leaders', 'Leader')
    for old, new in [('chairman', 'president'), ('vice_chairman', 'vice_president')]:
        Leader.objects.filter(role=old).update(role=new)


def backwards(apps, schema_editor):
    Leader = apps.get_model('leaders', 'Leader')
    for new, old in [('president', 'chairman'), ('vice_president', 'vice_chairman')]:
        Leader.objects.filter(role=new).update(role=old)


class Migration(migrations.Migration):
    dependencies = [('leaders', '0002_alter_leader_role_alter_leader_title')]
    operations = [migrations.RunPython(forwards, backwards)]
