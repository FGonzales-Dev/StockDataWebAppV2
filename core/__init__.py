from __future__ import absolute_import, unicode_literals

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
default_app_config = 'core.apps.CoreConfig'

# Import the tasks module to ensure tasks are registered
from . import tasks_firestore