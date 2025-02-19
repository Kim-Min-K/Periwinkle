from django.shortcuts import render
from accounts.models import Post


def homeView(request):
    user = request.user
    posts = Post.objects.all().order_by("-published")

    context = {
        "username": user.username,
        "github_username": user.github_username,
        "posts": posts,
    }

    return render(request, "home.html", context)
