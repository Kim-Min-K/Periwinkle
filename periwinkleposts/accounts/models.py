from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinLengthValidator
import uuid

class Authors(AbstractUser):
    row_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    host = models.CharField(max_length=200, blank=False, null=False)
    id = models.CharField(max_length=200, default=None, unique=True)
    displayName = models.CharField(max_length=200, default="John Doe")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    github_username = models.CharField(max_length=100, blank=True, null=True, unique=True)
    
    
    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if self.id is None:
            self.id = str(self.host)+"authors/"+str(self.row_id.hex)
        super().save(*args, **kwargs)

class Follow(models.Model):
    follower = models.ForeignKey(Authors, on_delete=models.CASCADE, related_name="following") 
    followee = models.ForeignKey(Authors, on_delete=models.CASCADE, related_name="followers") 
    followed_since = models.DateTimeField(auto_now_add=True)  # Timestamp of follow action

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['follower', 'followee'], name='unique_follow'),
            models.CheckConstraint(
                check=~models.Q(follower=models.F('followee')),
                name='prevent_self_follow'
            ),
        ]

    def __str__(self):
        return f"{self.follower} follows {self.followee}"
    
class FollowRequest(models.Model):
    requestee = models.ForeignKey(Authors, on_delete=models.CASCADE, related_name="requesters")
    requester = models.ForeignKey(Authors, on_delete=models.CASCADE, related_name="requesting")
    requested_since = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['requestee', 'requester'], name='unique_request'),
            models.CheckConstraint(
                check=~models.Q(requester=models.F('requestee')),
                name='prevent_self_follow_request'
            ),
        ]
    
    def __str__(self):
        return f"{self.requester} is requesting {self.requestee}"