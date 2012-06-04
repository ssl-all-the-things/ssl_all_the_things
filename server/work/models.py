from django.db import models

# Create your models here.

class Task(models.Model):
    # The work tasks  consist of *.*.c.d
    c = models.IntegerField(db_index=True)
    d = models.IntegerField(db_index=True)
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

class EndPoint(models.Model):
    ip = models.IPAddressField()
    port = models.IntegerField()
    rev_dns = models.CharField(max_length=256, null=True, blank=True)
    
    def __unicode__(self):
        return u"%s:%s" % (self.ip, self.port)

class Certificate(models.Model):
    endpoint = models.ForeignKey(EndPoint)
    subject_commonname = models.CharField(max_length=256, null=True, blank=True)
    pem = models.TextField()

    def __unicode__(self):
        return self.subject_commonname

    
    



