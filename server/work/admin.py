from django.contrib import admin
from server.work.models import *

class TaskAdmin(admin.ModelAdmin):
    list_display = ['bucket', 'status', 'started', 'finished', 'worker_id']
    list_filter = ['status']

admin.site.register(Task, TaskAdmin)




