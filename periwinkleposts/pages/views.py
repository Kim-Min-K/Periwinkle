from django.shortcuts import render, redirect
from accounts.models import Post, Follow
import commonmark
from django.utils.safestring import mark_safe
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
import requests
from rest_framework.exceptions import ValidationError
from requests.auth import HTTPBasicAuth
from .forms import *

User = get_user_model()

@staff_member_required
def nodeView(request):
    if request.method == "POST":
        form = AddNode(request.POST)
        if form.is_valid():
            form.save()  
            return redirect("pages:home")  
        else:
            print(form.errors)  # Debug form errors in the terminal
    
    else:
        form = AddNode()

    return render(request, "node.html", {"form": form})

@login_required
def homeView(request):
    user = request.user
    
    # Fetch Public Posts
    public_posts = Post.objects.filter(visibility="PUBLIC", is_deleted=False)

    # Fetch Friends-Only Posts
    friends_posts = Post.objects.filter(
        visibility="FRIENDS", 
        is_deleted=False, 
        author__in=[author for author in User.objects.all() if is_friend(user, author)] + [user]
    )

    # Fetch Unlisted Posts
    unlisted_posts = Post.objects.filter(
        visibility="UNLISTED", 
        is_deleted=False, 
        author__in=[author for author in User.objects.all() if is_following(user, author)] + [user]
    )

    # Combine the Posts and Order by Published Date
    posts = (public_posts | friends_posts | unlisted_posts).distinct().order_by("-published")

    #convert content in posts where contentType == "text/markdown"
    for post in posts:
        if post.contentType == "text/markdown":
            post.content = markdown_to_html(post.content)

    context = {
        "username": user.username,
        "github_username": user.github_username,
        "posts": posts,
    }

    return render(request, "home.html", context)

def markdown_to_html(md_text):
    #use CommonMark functions to convert markdown to html
    parser = commonmark.Parser()
    renderer = commonmark.HtmlRenderer()
    return mark_safe(renderer.render(parser.parse(md_text)))

def is_friend(user, author):
    return Follow.objects.filter(follower=user, followee=author).exists() and \
           Follow.objects.filter(follower=author, followee=user).exists()

def is_following(user, author):
    return Follow.objects.filter(follower=user, followee=author).exists()
