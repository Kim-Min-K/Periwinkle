from django.shortcuts import render
from accounts.models import Authors
from .models import Inbox
from api.models import ExternalNode

# Create your views here.
def inbox_view(request, author_id):
    node_list = ExternalNode.objects.all()

    context = {
        'data': node_list
    }

    return render(request, 'inbox.html', context)