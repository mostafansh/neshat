"""CLAUDE.md rule 2: a committed read is never edited.

The Python model already refuses to save an existing Read. This trigger makes the database
itself refuse any UPDATE, so no other path (the admin, a script, a mistake) can change one.
"""

from django.db import migrations

CREATE = """
CREATE TRIGGER reading_read_never_updated
BEFORE UPDATE ON reading_read
BEGIN
    SELECT RAISE(ABORT, 'A committed read is never edited.');
END;
"""

DROP = "DROP TRIGGER IF EXISTS reading_read_never_updated;"


class Migration(migrations.Migration):
    dependencies = [("reading", "0002_case_study_enrollment_presentation_imageaccess_and_more")]

    operations = [migrations.RunSQL(CREATE, reverse_sql=DROP)]
