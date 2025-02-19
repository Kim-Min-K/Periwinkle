from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Authors, Follow, Post
from django.utils.html import mark_safe


# so the replaced users still shows up in the auth panel
class AuthorsAdmin(UserAdmin):
    list_display = ("username", "email", "is_staff", "is_active", "github_username")
    fieldsets = UserAdmin.fieldsets + (
        (
            "Additional Info",
            {
                "fields": ("github_username", "avatar_preview", "avatar_url", "avatar"),
            },
        ),
    )
    readonly_fields = ("avatar_preview",)

    def avatar_preview(self, obj):
        if obj.avatar:
            # Display an image preview; adjust dimensions as needed.
            return mark_safe(
                f'<img src="{obj.avatar.url}" alt="Avatar" style="max-width: 100px; max-height: 100px;" />'
            )
        return "No Avatar"

    avatar_preview.short_description = "Avatar Preview"


class FollowsAdmin(admin.ModelAdmin):
    list_display = ("follower", "followee", "followed_since")


class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "is_deleted", "published")
    search_fields = ("title", "author__displayName")


admin.site.register(Authors, AuthorsAdmin)
admin.site.register(Follow, FollowsAdmin)
admin.site.register(Post, PostAdmin)
