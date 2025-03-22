from django.contrib import admin
from api.models import *

@admin.register(ExternalNode)
class NodeAdmin(admin.ModelAdmin):
    list_display = ('nodeURL', 'username', 'team_name')
