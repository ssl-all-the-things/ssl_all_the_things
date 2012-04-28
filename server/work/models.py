from django.db import models

# Create your models here.

class Task(models.Model):
    bucket = models.CharField(max_length=12, db_index=True, unique=True)
    status = models.CharField(  max_length=4, 
                                db_index=True,
                                choices = (
                                    ("O", "Open"),
                                    ("IP", "In Progress"),
                                    ("F", "Finished")
                                ),
                                default = "O")
    started = models.DateTimeField(null=True, blank=True)
    finished = models.DateTimeField(null=True, blank=True)
    worker_id = models.CharField(max_length=64, null=True, blank=True)



