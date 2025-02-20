from django.shortcuts import render, redirect, get_object_or_404
from .forms import AuthorCreation, AvatarUpload, EditProfile
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import Authors, FollowRequest, Comment, Like
from .serializers import authorSerializer, CommentSerialier, LikeSerializer
from django.http import QueryDict
from api.follow_views import *
from api.viewsets import FollowersViewSet, FollowRequestViewSet
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import redirect, render
from django.http import HttpResponse
from .models import Post
import uuid
import requests


def loginView(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("pages:home")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "login.html")


def uploadAvatar(request):
    user = request.user
    print("\n--- Upload Avatar View Started ---")
    if request.method == "POST":
        print("POST request received")
        print("POST data:", request.POST)
        print("FILES data:", request.FILES)
        form = AvatarUpload(request.POST, request.FILES, instance=user)
        print("Form instance:", user.avatar, user.avatar_url)
        if form.is_valid():
            if "avatar" in request.FILES:
                user.avatar = request.FILES["avatar"]
                user.avatar_url = None
            elif form.cleaned_data.get("avatar_url"):
                user.avatar_url = form.cleaned_data["avatar_url"]
                user.avatar = None
            form.save()
            return redirect("accounts:profile", username=user.username)
        else:
            print("\nFORM ERRORS:")
            print("Non-field errors:", form.non_field_errors())
            for field in form:
                print(f"Field {field.name}: {field.errors}")
            print("\nCleaned data:", form.cleaned_data)
    else:
        form = AvatarUpload()
    return render(request, "avatar.html", {"form": form})


def registerView(request):
    if request.method == "POST":

        # Add a "host" field in the post request and set it to our server's / proxy's host name
        print(" RegisterView/request.POST : " + str(request.POST))
        ordinary_dict = dict(request.POST.dict())
        ordinary_dict["host"] = request.build_absolute_uri("/api/")
        query_dict = QueryDict("", mutable=True)
        query_dict.update(ordinary_dict)
        print(" RegisterView/QueryDict : " + str(query_dict))

        form = AuthorCreation(query_dict)
        if form.is_valid():
            form.save()
            return redirect("accounts:login")
        print(f"Error: {form.errors}")
    else:
        form = AuthorCreation()
    return render(request, "register.html", {"form": form})


def profileView(request, username):
    author = get_object_or_404(Authors, username=username)
    ownProfile = request.user.is_authenticated and (request.user == author)

    # Connections field
    friends = getFriends(request, author.row_id.hex).data["friends"]
    followers = (FollowersViewSet.as_view({"get": "list"}))(
        request, author.row_id.hex
    ).data["followers"]
    requesters = getFollowRequests(request, author.row_id.hex).data["requesters"]
    suggestions = getSuggestions(request, author.row_id.hex).data["suggestions"]
    followees = getFollowees(request, author.row_id.hex).data["followees"]
    sent_requests = getSentRequests(request, author.row_id.hex).data["sent_requests"]

    context = {
        "author": author,
        "ownProfile": ownProfile,
        "friends": friends,
        "followers": followers,
        "requesters": requesters,
        "suggestions": suggestions,
        "followees": followees,
        "sent_requests": sent_requests,
        "follower_count": len(followers),
        "followee_count": len(followees),
    }

    return render(request, "profile.html", context)


def acceptRequest(request, author_serial, fqid):
    requester = Authors.objects.get(id=fqid)
    requestee = Authors.objects.get(row_id=uuid.UUID(hex=author_serial))
    follow_request = get_object_or_404(
        FollowRequest, requester=requester, requestee=requestee
    )
    response = acceptFollowRequest(request, follow_request.id)
    return redirect("accounts:profile", username=requestee.username)


def declineRequest(request, author_serial, fqid):
    requester = Authors.objects.get(id=fqid)
    requestee = Authors.objects.get(row_id=uuid.UUID(hex=author_serial))
    follow_request = get_object_or_404(
        FollowRequest, requester=requester, requestee=requestee
    )
    response = declineFollowRequest(request, follow_request.id)
    print(response)
    return redirect("accounts:profile", username=requestee.username)


def sendFollowRequest(request, fqid):
    requestee = Authors.objects.get(id=fqid)
    requester = Authors.objects.get(id=request.user.id)
    requestee_serializer = authorSerializer(requestee)
    requester_serializer = authorSerializer(requester)

    follow_request = {
        "type": "follow",
        "summary": f"{requester.username} wants to follow {requestee.username}",
        "actor": requester_serializer.data,
        "object": requestee_serializer.data,
    }

    response = requests.post(
        f"{requestee.host}authors/{requestee.row_id.hex}/inbox",
        headers={"Content-Type": "application/json"},
        json=follow_request,
    )

    if not response.ok:
        raise Exception(response.json().get("message"))

    return redirect("accounts:profile", username=request.user.username)

@login_required #ensures that this only works if user is logged in/authenticated, not sure if really needed???
def edit_profile(request):
    user = request.user
    
    if request.method == 'POST':
        form = EditProfile(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('accounts:profile', username=user.username)
    else:
        form = EditProfile(instance=user) #prefill with current/existing data
    
    return render(request, 'edit_profile.html', {'form': form})

# I used https://www.geeksforgeeks.org/how-to-create-a-basic-api-using-django-rest-framework/ to do the api stuff

from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action


class authorAPI(viewsets.ModelViewSet):
    queryset = Authors.objects.all()
    serializer_class = authorSerializer
    permission_classes = [permissions.IsAuthenticated]

    # some extra code to add a custom route for get requests. this provides the logged in users profile, and serves mostly as an example!
    @action(detail=False, methods=["get"])
    def profile(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)


def create_post(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        content = request.POST.get("content")
        content_type = request.POST.get("contentType")
        image = request.FILES.get("image")

        if not all([title, description, content, content_type]):
            return HttpResponse("All fields are required.", status=400)

        try:
            post = Post(
                title=title,
                description=description,
                content=content,
                contentType=content_type,
                author=request.user,
                image=image,
            )
            post.save()
            return redirect("pages:home")
        except Exception as e:
            return HttpResponse(f"An error occurred: {str(e)}", status=500)

    return render(request, "home.html", {"error": "Only POST method is allowed."})


def delete_post(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(Post, id=post_id, author=request.user)
        post.is_deleted = True
        post.save()
        return redirect("pages:home")

    return render(request, "home.html", {"error": "Only POST method is allowed."})


#--------------Comment----------------
class CommentView(viewsets.ModelViewSet):
    serializer_class = CommentSerialier
    queryset = Comment.objects.all().order_by('published') 
    
    # detail = True meant for a specific object
    @action(detail = True, methods = ['get'])
    def post_comments(self, request, author_serial, post_serial):
        post = get_object_or_404(Post, id = post_serial)
        comments = Comment.objects.filter(post = post).order_by('published')
        serialier = self.get_serializer(comments, many = True)
        return Response(serialier.data)
    
    def create(self, request, author_serial, post_serial):
        post = get_object_or_404(Post, id = post_serial)
        serializer = self.get_serializer(data = request.data)
        if serializer.is_valid():
            serializer.save(author=author_serial, post = post)
            return redirect("pages:home")
        return render(request, "home.html", {"error": "Something wents wrong"})
    
class LikeView(viewsets.ModelViewSet):
    serializer_class = LikeSerializer
    queryset = Like.objects.all().order_by('published')

    
    @action(detail=True, methods=["get"])
    def post_likes(self, request, author_serial, post_serial):
        post = get_object_or_404(Post, id=post_serial)
        likes = Like.objects.filter(post=post).order_by("published")
        serializer = self.get_serializer(likes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"])
    def like_post(self, request, author_serial, post_serial):
        post = get_object_or_404(Post, id=post_serial)
        like, created = Like.objects.get_or_create(author=request.user, post=post)
        serializer = self.get_serializer(like)
        return redirect("pages:home")