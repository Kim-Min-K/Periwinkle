from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import Post, Follow, Authors,FollowRequest, Comment,Like,Post,SiteSettings,Follow
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
#import api.node_fetch as node_fetch_utils
from api import node_fetch
from django.contrib import messages

User = get_user_model()

# This is how a Node is registered!
@staff_member_required
def nodeView(request):
    if request.method == "POST":
        form = AddNode(request.POST)
        if form.is_valid():
            print("Form is Valid")
            node_url = form.cleaned_data["nodeURL"].rstrip("/")
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            print("Username:", username, "Password:", password)

            # Attempt to authenticate with the remote node
            test_url = f"{node_url}/api/ping/"

            try:
                response = requests.get(test_url, auth=HTTPBasicAuth(username, password), timeout=5)
                if response.status_code == 200:
                    # Create the ExternalNode instance but don’t save it yet
                    node = ExternalNode(
                        nodeURL=node_url,
                        username=username,
                        password=password,
                    )

                    node.save()  # Save to DB

                    # Begin data sync
                    node_fetch.get_node_data(node)

                    return redirect("pages:home")
                else:
                    messages.error(request, f"Authentication failed: status code {response.status_code}")

            except requests.exceptions.RequestException as e:
                messages.error(request, f"Failed to connect to node: {str(e)}")

        else:
            print(form.errors)  # Debug form errors

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

#Allows users to view inbox
#also if "inbox.html -> it render accounts:inbox.html"
def inboxView(request, row_id):
    # Check if the logged-in user is the author
    author = get_object_or_404(Authors, row_id=row_id)
    if request.user != author:
        return HttpResponseForbidden("You aren't allowed here.")

    return render(request, "inbox.html")

