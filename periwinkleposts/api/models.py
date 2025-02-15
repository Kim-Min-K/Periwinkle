from django.db import models


# Create your models here.

class FollowRequest(models.Model):
    requestee = models.ForeignKey(Authors, on_delete=models.CASCADE, related_name="requesters")
    requester = models.ForeignKey(Authors, on_delete=models.CASCADE, related_name="requesting")
    requested_since = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['requestee', 'requester'], name='unique_request')
        ]
    
    def __str__(self):
        return f"{self.requester} is requesting {self.requestee}"