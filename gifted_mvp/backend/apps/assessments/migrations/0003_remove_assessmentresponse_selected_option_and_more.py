# Single selected_option FK → selected_options M2M (multi-select support), keeping data.

from django.db import migrations, models


def copy_single_to_many(apps, schema_editor):
    AssessmentResponse = apps.get_model("assessments", "AssessmentResponse")
    for response in AssessmentResponse.objects.exclude(selected_option__isnull=True):
        response.selected_options.add(response.selected_option_id)


class Migration(migrations.Migration):

    dependencies = [
        ("assessments", "0002_initial"),
        ("questions", "0002_question_content_questionoption_content_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="assessmentresponse",
            name="selected_options",
            field=models.ManyToManyField(related_name="+", to="questions.questionoption"),
        ),
        migrations.RunPython(copy_single_to_many, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="assessmentresponse",
            name="selected_option",
        ),
    ]
