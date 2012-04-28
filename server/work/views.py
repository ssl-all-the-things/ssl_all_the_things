from django.shortcuts import get_object_or_404, render_to_response
# Create your views here.
from django.http import HttpResponseRedirect, HttpResponse
from server.work.models import *
import datetime


def get_work(request, id):
    task = Task.objects.filter(status="O").all()[0]
    task.status = "IP"
    task.started = datetime.datetime.now()
    task.worker_id = id
    task.save()
    return HttpResponse("\n".join(["%s %d" % (task.bucket, octet) for octet in range(256)]))
    
