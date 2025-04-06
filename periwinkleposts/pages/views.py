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
from inbox.models import Inbox
import json
User = get_user_model()

# # This is how a Node is registered!
# @staff_member_required
# def nodeView(request):
#     if request.method == "POST":
#         form = AddNode(request.POST)
#         if form.is_valid():
#             print("Form is Valid")
#             node_url = form.cleaned_data["nodeURL"].rstrip("/")
#             username = form.cleaned_data["username"]
#             password = form.cleaned_data["password"]

#             print("Username:", username, "Password:", password)

#             # Attempt to authenticate with the remote node
#             test_url = f"{node_url}/api/ping/"

#             try:
#                 response = requests.get(test_url, auth=HTTPBasicAuth(username, password), timeout=5)
#                 if response.status_code == 200:
#                     # Create the ExternalNode instance but don’t save it yet
#                     node = ExternalNode(
#                         nodeURL=node_url,
#                         username=username,
#                         password=password,
#                     )

#                     node.save()  # Save to DB

#                     # Begin data sync
#                     node_fetch.get_node_data(node)

#                     return redirect("pages:home")
#                 else:
#                     messages.error(request, f"Authentication failed: status code {response.status_code}")

#             except requests.exceptions.RequestException as e:
#                 messages.error(request, f"Failed to connect to node: {str(e)}")

#         else:
#             print(form.errors)  # Debug form errors

#     else:
#         form = AddNode()

#     return render(request, "node.html", {"form": form})

@staff_member_required
def nodeView(request):
    if request.method == "POST":
        form = AddNode(request.POST)
        if form.is_valid(): #import node fetch funcs and call them and print their results 
            node = ExternalNode(
                nodeURL=form.cleaned_data["nodeURL"],
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            data = node_fetch.get_node_data(node)
            print(data)
            node.save()
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


def inbox_item_view(request, row_id):
    author = get_object_or_404(Authors, row_id=row_id)
    if request.user != author:
        return HttpResponseForbidden("You aren't allowed here.")
    raw_items = Inbox.objects.filter(author=author).order_by("-received")
    posts, comments, likes, follows = [], [], [], []

    for item in raw_items:
        try:
            content = item.content if isinstance(item.content, dict) else json.loads(item.content)
        except Exception as e:
            print(f"Error decoding inbox content: {e}")
            content = {}

        display = ""
        type = item.type
        received = item.received
        author_name = content.get("author", {}).get("displayName", "Someone")
        published = content.get("published", "")[:10] if "published" in content else received.strftime("%Y-%m-%d")

        if type == "post":
            title = content.get("title", "a post")
            body = content.get("content", "")
            display = f"{author_name} made a new post  '{title}' :\
            <br><span class='text-black text-lg'>{body}</span>\
            <br><span class='text-sm'>On {published}</span>"

        elif type == "comment":
            post_url = content.get("post", "")
            post_id = post_url.split("/")[-1] if post_url else None
            comment_text = content.get("comment", "")
            post_title = "your post"
            if post_id:
                try:
                    from accounts.models import Post
                    post_obj = Post.objects.get(id=post_id)
                    post_title = post_obj.title
                except Post.DoesNotExist:
                    post_title = post_id  
            display = f"{author_name} commented on your post '{post_title}' :{comment_text}<br><span class='text-sm'>On {published}</span>"


        elif type == "like":
            liked_object = content.get("object", "")
            sentence = "something"
            if "commented" in liked_object:
                comment_id = liked_object.rstrip("/").split("/")[-1]
                try:
                    comment = Comment.objects.get(id=comment_id)
                    comment_text = comment.comment
                    sentence = f"your comment: '<span class=\"font-bold\">{comment_text}</span>'"
                except Comment.DoesNotExist:
                    sentence = "your comment"
            else:
                post_id = liked_object.rstrip("/").split("/")[-1]
                try:
                    post = Post.objects.get(id=post_id)
                    post_title = post.title
                    sentence = f"your post: '<span class=\"font-bold\">{post_title}</span>'"
                except Post.DoesNotExist:
                    sentence = "your post"
            display = f"{author_name} liked {sentence}"

        elif type == "follow":
            actor = content.get("actor", {})
            follower_name = actor.get("displayName", "Someone")
            display = f"{follower_name} wants to follow you"

        item_data = {
            "id": item.id,
            "type": type,
            "content": content,
            "received": received,
            "display": display,
        }

        if type == "post":
            posts.append(item_data)
        elif type == "comment":
            comments.append(item_data)
        elif type == "like":
            likes.append(item_data)
        elif type == "follow":
            follows.append(item_data)

    context = {
        "posts": posts,
        "comments": comments,
        "likes": likes,
        "follows": follows,
    }
    return render(request, "inbox.html", context)
