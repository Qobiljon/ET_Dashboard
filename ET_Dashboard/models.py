from django.db import models


class Campaigns(models.Model):
    id = models.AutoField(primary_key=True)
    creatorEmail = models.EmailField(null=False)
    title = models.CharField(max_length=256)
    notes = models.TextField(default='', null=False)
    participants = models.TextField(default='', null=False)
