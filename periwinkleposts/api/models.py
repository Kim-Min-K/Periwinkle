from django.db import models


class ExternalNode(models.Model):
    nodeURL = models.URLField(primary_key=True, unique=True)
    username = models.CharField(max_length=40)
    password = models.CharField(max_length=40)
    team_name = models.CharField(max_length=40)
    def __str__(self):
        return f"{self.team_name} ({self.nodeURL})"
    


    