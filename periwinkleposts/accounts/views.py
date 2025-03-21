from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from .forms import AuthorCreation, AvatarUpload, EditProfile
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import Authors, FollowRequest, Comment, Like, Post, SiteSettings, Follow
from .serializers import authorSerializer, CommentSerializer, LikeSerializer
from django.http import QueryDict
from api.viewsets import *
from django.shortcuts import redirect, render
from django.http import HttpResponse
from .models import Post
import uuid
import requests
from pages.views import markdown_to_html
from django.db.models import Q
from django.urls import reverse_lazy, reverse
from django.contrib.auth.views import LogoutView
from rest_framework.views import APIView
from urllib.parse import unquote
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
            return redirect("accounts:profile", row_id=user.row_id)
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
        ordinary_dict["host"] = request.build_absolute_uri("/api/") if "host" not in ordinary_dict else ordinary_dict["host"]
        query_dict = QueryDict("", mutable=True)
        query_dict.update(ordinary_dict)
        print(" RegisterView/QueryDict : " + str(query_dict))

        form = AuthorCreation(query_dict)
        if form.is_valid():
            user = form.save(commit=False)  #create user but don’t save yet

            #get site settings to check if approval is required currently
            site_settings = SiteSettings.objects.first()
            approval_required = True  # Default to requiring approval

            if site_settings:
                approval_required = site_settings.require_approval

            # Set approval status
            if approval_required: #if approval is required, set user to not approved, else set to approved
                user.is_approved = False
            else:
                user.is_approved = True
            user.save()  #save it now
            return redirect("accounts:login")
        print(f"Error: {form.errors}")
    else:
        form = AuthorCreation()
    return render(request, "register.html", {"form": form})


def profileView(request, row_id):
    author = get_object_or_404(Authors, row_id=row_id)
    
    if author.is_staff:
        author = request.user

    ownProfile = request.user.is_authenticated and (request.user == author)
    if not ownProfile:
        posts = author.posts.filter(is_deleted=False, visibility="PUBLIC").order_by("-published")
    else:
        posts = author.posts.filter(is_deleted=False).order_by("-published")
    # Connections field
    friends = (FriendsViewSet.as_view({'get': 'getFriends'}))(request,author.row_id).data["authors"]
    followers = (FollowersViewSet.as_view({"get": "list"}))(request, author.row_id).data["authors"]
    followees = (FolloweesViewSet.as_view({"get": "getFollowees"}))(request, author.row_id).data["followees"]
    requesters = (FollowRequestViewSet.as_view({'get': 'getFollowRequests'}))(request, author.row_id).data["authors"]
    suggestions = requests.get(request.user.host[:-5] + reverse("api:getRequestSuggestions", args=[request.user.row_id])).json()["authors"]
    sent_requests = requests.get(request.user.host[:-5] + reverse("api:getFollowRequestOut", args=[author.row_id])).json()["authors"]

    for post in posts:
        if post.contentType == "text/markdown":
            post.content = markdown_to_html(post.content)
    isFollowee = Follow.objects.filter(followee=author, follower=request.user).exists()
    isPending = FollowRequest.objects.filter(requestee=author, requester=request.user).exists()
    isFriend = (
        Follow.objects.filter(followee=author, follower=request.user).exists() and
        Follow.objects.filter(followee=request.user, follower=author).exists()
    )

    context = {
        "author": author,
        "ownProfile": ownProfile,
        "isFollowee": isFollowee,
        "isFriend": isFriend,
        "isPending": isPending,
        "friends": friends,
        "followers": followers,
        "requesters": requesters,
        "suggestions": suggestions,
        "followees": followees,
        "sent_requests": sent_requests,
        "follower_count": len(followers),
        "followee_count": len(followees),
        "post_count": len(posts),
        "posts": posts,
    }

    return render(request, "profile.html", context)


def acceptRequest(request, author_serial, requester_serial):
    response = requests.post(request.user.host[:-5] + reverse("api:acceptFollowRequest", args=[author_serial, requester_serial]))
    if not response.ok:
        raise Exception("Accept request failed")
    return redirect("accounts:profile", row_id=request.user.row_id)


def declineRequest(request, author_serial, requester_serial):
    response = requests.post(request.user.host[:-5] + reverse("api:declineFollowRequest", args=[author_serial, requester_serial]))
    if not response.ok:
        raise Exception("Decline request failed")
    return redirect("accounts:profile", row_id=request.user.row_id)

def unfollow(request, author_serial, fqid):
    followee = Authors.objects.get(id=fqid)
    author = Authors.objects.get(row_id=author_serial)
    (FolloweesViewSet.as_view({'post':'unfollow'}))(request, author_serial, fqid)
    return redirect("accounts:profile", row_id=request.user.row_id)


def sendFollowRequest(request, author_serial):
    requestee = Authors.objects.get(row_id=author_serial)
    requester = Authors.objects.get(row_id=request.user.row_id)
    requestee_serializer = authorSerializer(requestee)
    requester_serializer = authorSerializer(requester)

    follow_request = {
        "type": "follow",
        "summary": f"{requester.username} wants to follow {requestee.username}",
        "actor": requester_serializer.data,
        "object": requestee_serializer.data,
    }

    url = requestee.host[:-5] + reverse("api:followRequest", args=[requestee.row_id])
    
    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json=follow_request,
    )

    if not response.ok:
        raise Exception(response.json().get("message"))

    return redirect("accounts:profile", row_id=request.user.row_id)


@login_required  # ensures that this only works if user is logged in/authenticated, not sure if really needed???
def edit_profile(request):
    user = request.user

    if request.method == "POST":
        form = EditProfile(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect("accounts:profile", row_id = user.row_id)
    else:
        form = EditProfile(instance=user)  # prefill with current/existing data

    return render(request, "edit_profile.html", {"form": form})

def approval_pending(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    if request.user.is_approved:
        return redirect('pages:home')
    return render(request, "approval_pending.html")

class CustomLogoutView(LogoutView):
    def get_next_page(self):
        if not self.request.user.is_approved:
            return reverse_lazy('accounts:login')
        return self.next_page or self.get_redirect_url() or reverse_lazy('accounts:login')


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
        video = request.FILES.get("video")
        visibility = request.POST.get("visibility")

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
                video=video,
                visibility=visibility,
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

def edit_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    
    # Check ownership
    if request.user != post.author:
        return redirect('accounts:profile', row_id=request.user.row_id)
    
    if request.method == 'POST':
        post.title = request.POST.get('title', post.title)
        post.description = request.POST.get('description', post.description)
        post.content = request.POST.get('content', post.content)
        post.visibility = request.POST.get('visibility', post.visibility)

        print("your request:", request.FILES)
        if 'image' in request.FILES:
            # print("YES",request.FILES)
            post.image = request.FILES['image']
        if 'video' in request.FILES:
            # print("YES",request.FILES)
            post.video = request.FILES['video']
        post.save()
        return redirect('accounts:profile', row_id=request.user.row_id)

    return render(request, 'edit_post.html', {
        'post': post,
        'visibility_choices': Post.VISIBILITY_CHOICES
    })

def view_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    return render(request, 'view_post.html', {'post': post})

def is_friend(user, author):
    return Follow.objects.filter(follower=user, followee=author).exists() and \
               Follow.objects.filter(follower=author, followee=user).exists()

# --------------Comment----------------
class CommentSchema(SwaggerAutoSchema):
    def  get_tags(self,operation_keys=None):
        return ["Comment"]
class CommentView(viewsets.ModelViewSet):
    swagger_schema=CommentSchema
    serializer_class = CommentSerializer
    queryset = Comment.objects.all().order_by("published")
 
    def create(self, request, author_serial):
        post_serial = request.data.get("post")
        post = get_object_or_404(Post, id= post_serial)  
        serializer = self.get_serializer(data = request.data)
        if request.user.is_authenticated:
            author = request.user
        else:
            author_data = request.data.get("author")
            if not author_data:
                return Response({"error": "Author data is required for remote comments"}, status=400)
            author, _ = Authors.objects.get_or_create(id=author_data["id"], defaults=author_data)
        if serializer.is_valid():
            serializer.save(author=author, post = post)
        if request.headers.get("Accept") == "application/json" or request.content_type == "application/json":
            return Response(serializer.data, status=201)
        else:
            redirect_url = request.META.get("HTTP_REFERER", "pages:home")  
            return redirect(redirect_url)

        
    def comment_list(self, request):
        comments = Comment.objects.all().order_by("-published")  
        serializer = CommentSerializer(comments, many=True, context = {'request': request})  
        return Response(serializer.data, status=200)
    
    def retrieve(self, request, author_serial, comment_serial):
        comment = get_object_or_404(Comment, id=comment_serial)
        serializer = self.get_serializer(comment)
        return Response(serializer.data)
   
    def all_comments(self, request, author_serial):
        author = get_object_or_404(Authors, row_id = author_serial)
        # is_remote = request.get_host() != author.host
        # if is_remote:
        #     comments = Comment.objects.filter(
        #         author=author,
        #         post__visibility__in=["PUBLIC", "UNLISTED"]
        #     ).order_by("-published")
        # else:
        #     comments = Comment.objects.filter(author=author).order_by("-published")
        comments = Comment.objects.filter(author=author).order_by("-published")
        page = self.paginate_queryset(comments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(comments, many=True)
        return Response(serializer.data)
    
    def get_post_comments(self, request, author_serial, post_serial):
        post = get_object_or_404(Post, id = post_serial)
        comments = Comment.objects.filter(post=post).order_by("published")
        serializer = self.get_serializer(comments, many = True)
        return Response(serializer.data, status = 200)

    def known_post_comments(self,request, post_fqid):
        decoded_post_fqid = unquote(post_fqid)
        post_id = decoded_post_fqid.split("/")[-1]
        post = get_object_or_404(Post, id = post_id)
        comments = Comment.objects.filter(post=post).order_by("published")
        serializer = self.get_serializer(comments, many = True)
        return Response(serializer.data, status = 200)
    
    def get_comment(self, request, author_serial, post_serial, remote_comment_fqid):
        try:
            if remote_comment_fqid.startswith("http"):
                return Response({"error": "Only local comments are supported currently"}, status=400)

            comment = get_object_or_404(Comment, id=remote_comment_fqid, post__id=post_serial)
            serializer = self.get_serializer(comment)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def author_commented(self, request, author_fqid):
        decoded_author_fqid = unquote(author_fqid)  
        author_id = decoded_author_fqid.split("/")[-1]  
        # print("Extracted Author Id", author_id)
        author = get_object_or_404(Authors, row_id=author_id)
        comments = Comment.objects.filter(author=author).order_by("published")
        serializer = self.get_serializer(comments, many=True)
        return Response(serializer.data, status=200)

    def get_comment_by_fqid(self, request, comment_fqid):
        decoded_comment_fqid = unquote(comment_fqid)  
        comment_id = decoded_comment_fqid.split("/")[-1] 
        comment = Comment.objects.get(id=comment_id)
        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=200)

    
class CommentSchema(SwaggerAutoSchema):
    def  get_tags(self,operation_keys=None):
        return ["Like"]
class LikeView(viewsets.ModelViewSet):
    swagger_schema=CommentSchema
    serializer_class = LikeSerializer
    queryset = Like.objects.all().order_by('published')
    
    @action(detail=True, methods=["post"])
    def like_post(self, request, author_serial, post_serial):
        post = get_object_or_404(Post, id=post_serial)
        like, created = Like.objects.get_or_create(author=request.user, post=post)
        serializer = self.get_serializer(like)
        redirect_url = request.POST.get('next')
        return redirect(redirect_url)
    
    @action(detail=True, methods=["post"])
    def like_comment(self, request, author_serial, comment_serial):
        comment = get_object_or_404(Comment, id=comment_serial)
        like, created = Like.objects.get_or_create(author=request.user, comment=comment)
        serializer = self.get_serializer(like)
        return redirect("pages:home")
    
    def get_post_likes(self, request, author_serial, post_serial):
        post = get_object_or_404(Post, id=post_serial, author__row_id=author_serial)
        likes = Like.objects.filter(post=post)
        serializer = LikeSerializer(likes, many=True)
        return Response(serializer.data, status=200)
    
    def get_all_post_likes(self, request, post_fqid):
        decoded_post_fqid = unquote(post_fqid)  
        post_id = decoded_post_fqid.split("/")[-1]
        post = get_object_or_404(Post, id=post_id)  
        likes = Like.objects.filter(post=post)  
        serializer = LikeSerializer(likes, many=True)  
        return Response(serializer.data, status=200)

    def get_comment_likes(self, request, author_serial, post_serial, comment_fqid):
        decoded_comment_fqid = unquote(comment_fqid)
        comment_id = decoded_comment_fqid.split("/")[-1]
        comment = get_object_or_404(Comment, id=comment_id)
        likes = Like.objects.filter(comment=comment)
        serializer = LikeSerializer(likes, many=True)
        return Response(serializer.data, status=200)

    def get_author_likes(self, request, author_serial):
        author = get_object_or_404(Authors, row_id = author_serial)
        likes = Like.objects.filter(author = author)
        serializer = LikeSerializer(likes, many=True)
        return Response(serializer.data, status=200)

    def get_single_like(self, request,author_serial,like_serial):
        author = get_object_or_404(Authors, row_id = author_serial)
        like = get_object_or_404(Like, id = like_serial, author = author)
        serializer = LikeSerializer(like)
        return Response(serializer.data,status = 200)

    def get_like_by_author_fqid(self, request, author_fqid):
        decoded_author_fqid = unquote(author_fqid)  
        author = get_object_or_404(Authors, row_id=decoded_author_fqid.split("/")[-1])  
        likes = Like.objects.filter(author=author) 
        serializer = LikeSerializer(likes, many=True)
        return Response(serializer.data, status=200)
    
    def a_single_like(self,request,like_fqid):
        decoded_like_fqid = unquote(like_fqid)  
        like_uuid = decoded_like_fqid.split("/")[-1]  
        like = get_object_or_404(Like, id=like_uuid)  
        serializer = LikeSerializer(like)
        return Response(serializer.data, status=200)
    
class InboxView(APIView):
    def post(self, request, author_serial):
        
        author = get_object_or_404(Authors, row_id=author_serial)
        data_type = request.data.get("type")
        if data_type == "comment":
            return self.handle_comment(request, author)
        elif data_type == "like":
            return self.handle_like(request,author)
        elif data_type == "follow":
            return self.handle_follow(request, author_serial)
        return Response({"error": "Invalid type"}, status=400)

    def handle_comment(self, request, author):
        post_url = request.data.get("post")  
        post_id = post_url.split("/")[-1]
        post = get_object_or_404(Post, id=post_id) 
        serializer = CommentSerializer(data=request.data, context={"request": request})  
        if serializer.is_valid():
            serializer.save(author=author, post=post)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def handle_like(self, request, author): 
        object_url = request.data.get("object")  
        object_id = object_url.split("/")[-1] 
        if "/posts/" in object_url:
            liked_object = get_object_or_404(Post, id=object_id)
        elif "/commented/" in object_url:
            liked_object = get_object_or_404(Comment, id=object_id)
        author_data = request.data.get("author", {})
        author_id = author_data.get("id", "").split("/")[-1]  
        liker = get_object_or_404(Authors, row_id=author_id)  
        like, _ = Like.objects.get_or_create(
            author=liker,
            post=liked_object if isinstance(liked_object, Post) else None,
            comment=liked_object if isinstance(liked_object, Comment) else None
        )
        serializer = LikeSerializer(like)
        return Response(serializer.data, status=201)

    def handle_follow(self, request, author_serial):
        makeRequest = FollowRequestViewSet.as_view({'post': "makeRequest"})
        request._request.POST = QueryDict('', mutable=True)
        request._request.POST.update(request.data)  
        return makeRequest(request._request, author_serial)
