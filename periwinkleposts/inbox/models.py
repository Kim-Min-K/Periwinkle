from django.db import models
from accounts.models import Authors
import uuid
# Create your models here.
class Inbox(models.Model):
   inbox_type = [
       ('post', 'Post'),
       ('comment', "Comment"),
       ('like', 'Like'),
       ('follow', 'Follow'),
   ]
   id = models.UUIDField(primary_key=True, default=uuid.uuid4)
   author = models.ForeignKey(Authors, on_delete=models.CASCADE, related_name='inbox_items')
   type = models.CharField(choices=inbox_type)
   content = models.JSONField()
   received = models.DateTimeField(auto_now_add=True)


  


