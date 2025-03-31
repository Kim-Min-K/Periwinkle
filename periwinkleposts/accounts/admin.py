from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Authors, Follow, Post, Comment, Like, SiteSettings
from inbox.models import Inbox
from django.utils.html import mark_safe


# so the replaced users still shows up in the auth panel
class AuthorsAdmin(UserAdmin):
    list_display = ("row_id", "username", "id", "email", "is_staff", "displayName", "host", "is_active", "github_username", "is_approved")
    list_filter = ("is_staff", "is_approved")
    fieldsets = UserAdmin.fieldsets + (
        (
            "Additional Info",
            {
                "fields": ("github_username", "avatar_preview", "avatar_url", "avatar", "is_approved", "local"),
            },
        ),
    )
    readonly_fields = ("avatar_preview",)
    actions = ["approve_authors"]

    def avatar_preview(self, obj):
        if obj.avatar:
            # Display an image preview; adjust dimensions as needed.
            return mark_safe(
                f'<img src="{obj.avatar.url}" alt="Avatar" style="max-width: 100px; max-height: 100px;" />'
            )
        return "No Avatar"

    avatar_preview.short_description = "Avatar Preview"

    def approve_authors(self, queryset):
        queryset.update(is_approved=True)
    
    approve_authors.short_description = "Approve selected authors"


class FollowsAdmin(admin.ModelAdmin):
    list_display = ("follower", "followee", "followed_since")

class FollowRequestAdmin(admin.ModelAdmin):
    list_display = ("requester", "requestee", "requested_since")

class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "is_deleted", "published")
    search_fields = ("title", "author__displayName")

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('require_approval',)
    

admin.site.register(Authors, AuthorsAdmin)
admin.site.register(Follow, FollowsAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment)
admin.site.register(Like)
admin.site.register(Inbox)