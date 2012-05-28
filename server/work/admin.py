from django.contrib import admin
from server.work.models import *

class TaskAdmin(admin.ModelAdmin):
    list_display = ['c', 'd', 'status', 'started', 'finished', 'worker_id']
    list_filter = ['status', 'worker_id']


admin.site.register(Task, TaskAdmin)




