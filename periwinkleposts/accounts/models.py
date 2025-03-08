from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinLengthValidator
import uuid
from datetime import datetime
from django.utils import timezone
class Authors(AbstractUser):
    row_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    host = models.CharField(max_length=200, blank=False, null=False)
    id = models.CharField(max_length=200, default=None, unique=True)
    displayName = models.CharField(max_length=200, default="John Doe")
    is_approved = models.BooleanField(default=False)

    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)  # For image links
    github_username = models.CharField(
        max_length=100, blank=True, null=True, unique=True
    )
    local = models.BooleanField(default=True)

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if self.id is None:
            self.id = str(self.host) + "authors/" + str(self.row_id.hex)
        super().save(*args, **kwargs)

    def avatar_display(self):
        if self.avatar_url:
            return self.avatar_url
        elif self.avatar:
            return self.avatar.url
        else:
            return None


class Follow(models.Model):
    follower = models.ForeignKey(
        Authors, on_delete=models.CASCADE, related_name="following"
    )
    followee = models.ForeignKey(
        Authors, on_delete=models.CASCADE, related_name="followers"
    )
    followed_since = models.DateTimeField(
        auto_now_add=True
    )  # Timestamp of follow action

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "followee"], name="unique_follow"
            ),
            models.CheckConstraint(
                check=~models.Q(follower=models.F("followee")),
                name="prevent_self_follow",
            ),
        ]

    def __str__(self):
        return f"{self.follower} follows {self.followee}"


class FollowRequest(models.Model):
    requestee = models.ForeignKey(
        Authors, on_delete=models.CASCADE, related_name="requesters"
    )
    requester = models.ForeignKey(
        Authors, on_delete=models.CASCADE, related_name="requesting"
    )
    requested_since = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["requestee", "requester"], name="unique_request"
            ),
            models.CheckConstraint(
                check=~models.Q(requester=models.F("requestee")),
                name="prevent_self_follow_request",
            ),
        ]

    def __str__(self):
        return f"{self.requester} is requesting {self.requestee}"


class Post(models.Model):
    VISIBILITY_CHOICES = [
        ("PUBLIC", "Public"),
        ("UNLISTED", "Unlisted"),
        ("FRIENDS", "Friends-Only"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    author = models.ForeignKey(
        Authors, on_delete=models.SET_NULL, null=True, related_name="posts"
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    content = models.TextField()
    contentType = models.CharField(
        max_length=50,
        choices=[
            ("text/plain", "Plain Text"),
            ("text/markdown", "Markdown"),
        ],
    )
    image = models.ImageField(upload_to="image/", blank=True)
    video = models.FileField(upload_to="video/", null=True, blank=True)
    published = models.DateTimeField(auto_now_add=True)
    page = models.CharField(max_length=200, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default="PUBLIC")

    def __str__(self):
        return self.title


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        Authors, on_delete=models.CASCADE, related_name="comments"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    comment = models.TextField()
    published = models.DateTimeField(default = timezone.now)
    content_type = models.CharField(
        max_length=50,
        choices=[
            ("text/plain", "Plain Text"),
            ("text/markdown", "Markdown"),
        ],
        default="text/plain",
    )


    def __str__(self):
        return f"{self.author.displayName} commented on {self.published}"

class Like(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(Authors, on_delete=models.CASCADE, related_name='likes')
    # https://stackoverflow.com/questions/8609192/what-is-the-difference-between-null-true-and-blank-true-in-django
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes', null = True, blank = True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes', null = True, blank = True)
    published = models.DateTimeField(default = timezone.now)
    class Meta:
        constraints = [
        models.UniqueConstraint(fields=['author', 'post'], name='unique_like_post'),
        models.UniqueConstraint(fields=['author', 'comment'], name='unique_like_comment')
        ]


    def __str__(self):
        if self.post:
            return f"{self.author.displayName} like post {self.post.title}"
        else:
            return f"{self.author.displayName} like comment {self.comment.id}"

class SiteSettings(models.Model): # for the admin to set site-wide settings
    require_approval = models.BooleanField(default=True)

    def __str__(self):
        return f"Require Approval: {self.require_approval}"