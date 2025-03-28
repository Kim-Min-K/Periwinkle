from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from .forms import AuthorCreation, AvatarUpload, EditProfile
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import Authors, FollowRequest, Comment, Like, Post, SiteSettings, Follow
from .serializers import *
from inbox.serializers import InboxSerializer
from django.http import QueryDict
from api.viewsets import *
from api.serializers import *
from django.shortcuts import redirect, render
from django.http import HttpResponse
from .models import Post
from django.utils.dateparse import parse_datetime
from django.utils import timezone
import uuid
from uuid import UUID
import requests
from pages.views import markdown_to_html
from django.db.models import Q
from django.urls import reverse_lazy, reverse
from django.contrib.auth.views import LogoutView
from rest_framework.views import APIView
from urllib.parse import unquote
from rest_framework.test import APIRequestFactory
from inbox.models import Inbox
from api.serializers import PostSerializer, AuthorSerializer
from api.models import ExternalNode
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# I used https://www.geeksforgeeks.org/how-to-create-a-basic-api-using-django-rest-framework/ to do the api stuff
from rest_framework.response import Response
from rest_framework import viewsets, permissions
from rest_framework.decorators import action

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
            
            host = request.build_absolute_uri("/api/authors/")
            user.id = f'{host}{user.row_id}'  
            
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
    author = None
    try:
        author = get_object_or_404(Authors, row_id=row_id)
    except Http404:
        try:

            decoded_url = unquote(row_id)
            author = get_object_or_404(Authors, id=decoded_url)
        except Http404:
            raise Http404("Author not found")

    if author.is_staff:
        author = request.user

    ownProfile = request.user.is_authenticated and (request.user == author)
    if not ownProfile:
        posts = author.posts.filter(is_deleted=False, visibility="PUBLIC").order_by("-published")
    else:
        posts = author.posts.filter(is_deleted=False).order_by("-published")

    # Connections field
    friends = (FriendsViewSet.as_view({'get': 'getFriends'}))(request,author.row_id).data["authors"]
    followers = (FollowersViewSet.as_view({"get": "list"}))(request, author.row_id).data["followers"]
    followees = (FolloweesViewSet.as_view({"get": "getFollowees"}))(request, author.row_id).data["followees"]
    requesters = (FollowRequestViewSet.as_view({'get': 'getFollowRequests'}))(request, author.row_id).data["authors"]
    suggestions = (FollowRequestViewSet.as_view({'get': 'getRequestSuggestions'}))(request, author.row_id).data["authors"]
    sent_requests = (FollowRequestViewSet.as_view({'get': 'getOutGoingFollowRequests'}))(request, author.row_id).data["authors"]

    # Add row_id to followers
    for follower in followers:
        # Get row_id from id field
        follower["row_id"] = follower["id"].split("/")[-1]

    for post in posts:
        if post.contentType == "text/markdown":
            post.content = markdown_to_html(post.content)
    isFollowee = Follow.objects.filter(followee=author, follower=request.user).exists()
    isPending = FollowRequest.objects.filter(requestee=author, requester=request.user).exists()
    isFriend = (
        Follow.objects.filter(followee=author, follower=request.user).exists() and
        Follow.objects.filter(followee=request.user, follower=author).exists()
    )


    # GitHub activity // NOTE: They are public posts only 
    # Used this as reference -> can change format of the events 
    # https://docs.github.com/en/rest/activity/events?apiVersion=2022-11-28#list-public-events-for-a-user

    github_username = author.github_username                                                  # Gets username from author form
    github_url = f"https://api.github.com/users/{github_username}/events/public"              # URL for users github
    github_activity = []                                                                      # List to append all activities

    try:
        response = requests.get(github_url, headers={"Accept": "application/vnd.github.v3+json"}, timeout=5)
        print(f"GitHub API Status: {response.status_code}")                                    # API response

        if response.status_code == 200:
            events = response.json()[:5]                                                       #Limit 5 can change this later

            for event in events:                                                               #iterate through each event in the events JSON and process it based on its type
                event_type = event["type"]                                                     
                repo_name = event["repo"]["name"]                                              #repository name
                created_at = event["created_at"][:10]                                          #example format "2025-03-24T14:25:30Z"

                if event_type == "PushEvent":
                    commit_count = len(event["payload"]["commits"])
                    message = f"Pushed {commit_count} commit(s) to {repo_name}"
                elif event_type == "PullRequestEvent":
                    action = event["payload"]["action"]
                    message = f"{action.capitalize()} a pull request in {repo_name}"
                elif event_type == "IssuesEvent":
                    action = event["payload"]["action"]
                    message = f"{action.capitalize()} an issue in {repo_name}"
                else:
                    message = f"{event_type} in {repo_name}"
                github_activity.append({"message": message, "date": created_at})

    except requests.RequestException as e:
        print(f"GitHub API Error: {e}")  
        github_activity = [{"message": "Failed to fetch GitHub activity", "date": "N/A"}]



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
        "github_activity": github_activity,
    }

    return render(request, "profile.html", context)


def acceptRequest(request, author_serial, requester_serial):
    response = (FollowRequestViewSet.as_view({'post': 'acceptFollowRequest'}))(request, author_serial, requester_serial)
    if response.status_code != 200:
        raise Exception(response.data)
    return redirect("accounts:profile", row_id=request.user.row_id)


def declineRequest(request, author_serial, requester_serial):
    response = (FollowRequestViewSet.as_view({'post': 'declineFollowRequest'}))(request, author_serial, requester_serial)
    if response.status_code != 200:
        raise Exception(response.data)
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

    serializer = ActionSerializer(action_type="follow", actor=requester, object=requestee)

    follow_request = serializer.to_representation()

    print(follow_request)
    
    if requester.host == requestee.host:
        # Create a new request object with POST data
        factory = APIRequestFactory()
        new_request = factory.post("", follow_request, format="json")  # Empty URL since ViewSet is called directly
        new_request.user = request.user  # Ensure authentication info is retained
        
        # Call the ViewSet action properly
        response = FollowRequestViewSet.as_view({'post': 'makeRequest'})(new_request, requestee.row_id)

        if response.status_code != 200:
            raise Exception(response.json().get("message"))
        return redirect("accounts:profile", row_id=requester.row_id)
    else:
        url = f"{requestee.host}authors/{author_serial}/inbox/"

        try:
            response = requests.post(url, json=follow_request)
            if response.status_code not in [400, 200, 201]:  # Check for success statuses
                raise Exception(response.json().get("message", "Failed to send follow request"))
            Follow.objects.create(followee=requestee, follower=requester)

        except requests.RequestException as e:
            raise Exception(f"Error connecting to {requestee.host}: {str(e)}")

        return redirect("accounts:profile", row_id=requester.row_id)


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
            inbox_instance = InboxView()
            post_data = PostSerializer(post, context={'request': request}).data
            inbox_instance.save_item(post.author.id, "post", post_data)

            # Add to other inboxes
        #     if visibility.upper() == "PUBLIC":
        #         # Send to Every Author
        #         for author in Authors.objects.all():
        #             Inbox.objects.create(
        #                 author=author,
        #                 type="post",
        #                 content=serialized_post
        #             )
        #     elif visibility.upper() == "UNLISTED":
        #         # Send to Followers
        #         for follower in request.user.followers.all():
        #             Inbox.objects.create(
        #                 author=follower.follower, 
        #                 type="post",
        #                 content=serialized_post
        #             )
        #     elif visibility.upper() == "FRIENDS":
        #         # Send to Friends
        #         for potential_friend in Authors.objects.exclude(row_id=request.user.row_id):
        #             if is_friend(request.user, potential_friend):
        #                 Inbox.objects.create(
        #                     author=potential_friend,
        #                     type="post",
        #                     content=serialized_post
        #                 )

        #     return redirect("pages:home")
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

def view_post(request, author_id, post_id):
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
            inbox_instance = InboxView()
            inbox_instance.save_item(request.user.id, "comment", serializer.data)
            # for node in ExternalNode.objects.all():
            #     inbox_url = f"{node.nodeURL}/api/authors/{post.author.row_id}/inbox/"
            #     try:
            #         response = requests.post(
            #             inbox_url,
            #             json={
            #                 'type':'comment',
            #                 **serializer.data
            #             },
            #             timeout = 5
            #         )
            #     except Exception as e:
            #         print(f"Failed to send comment to {inbox_url}: {e}")
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
        inbox_instance = InboxView()
        inbox_instance.save_item(post.author.id, "like", serializer.data)
        redirect_url = request.POST.get('next')
        return redirect(redirect_url)
    
    @action(detail=True, methods=["post"])
    def like_comment(self, request, author_serial, comment_serial):
        comment = get_object_or_404(Comment, id=comment_serial)
        like, created = Like.objects.get_or_create(author=request.user, comment=comment)
        serializer = self.get_serializer(like)
        Inbox.objects.create(
            author=comment.author,
            type="like",
            content=serializer.data
        )
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
    
    def get(self, request, author_serial):
        author = get_object_or_404(Authors, row_id=author_serial)
        inbox_items = Inbox.objects.filter(author=author).order_by('-received')
        serializer = InboxSerializer(inbox_items, many=True)
        return Response(serializer.data, status=200)

    @swagger_auto_schema(
        operation_description="Accepts different types of requests, such as followers or posts.",
        tags=["Remote"],
    )
    def post(self, request, author_serial):
        author = get_object_or_404(Authors, row_id=author_serial)
        data_type = request.data.get("type")
        if data_type == "comment":
            return self.handle_comment(request, author)
        elif data_type == "like":
            return self.handle_like(request,author)
        elif data_type == "follow":
            return self.handle_follow(request, author_serial)
        elif data_type == 'post':
            return self.handle_post(request, author)
        return Response({"error": "Invalid type"}, status=400)

    def handle_comment(self, request, author):
        post_url = request.data.get("post")  
        post_id = post_url.split("/")[-1]
        post = get_object_or_404(Post, id=post_id) 
        author_data = request.data.get('author',{})
        author_id = author_data.get("id", "").split("/")[-1]
        commenter = get_object_or_404(Authors, row_id=author_id)
        serializer = CommentSerializer(data=request.data, context={"request": request})  
        if serializer.is_valid():
            serializer.save(author=commenter, post=post)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def handle_post(self,request,local_author):
        # get ot create the author
        remote_author_data = request.data.get("author", {})
        if not remote_author_data:
            return Response({"error": "No author data provided"}, status=400)
        remote_author = remote_author = self.get_or_create_author_from_data(remote_author_data)
        if not remote_author:
            return Response({"error": "Failed to create or retrieve remote author"}, status=400)
        new_post = self.create_inbox_post(request, remote_author)
        if not new_post:
            return Response({"error": "Failed to create Post"}, status=400)
        serializer = PostSerializer(new_post, context={'request': request})
        return Response(serializer.data, status=201)

    def create_inbox_post(self, request, author):
        try:
            post_id = request.data.get('id', '').split("/")[-1]
            title = request.data.get('title', '')
            description = request.data.get('description', '')
            contentType = request.data.get('contentType', 'text/plain')
            content = request.data.get('content', '')
            visibility = request.data.get('visibility', 'PUBLIC')
            page = request.data.get('page', '')

            published_str = request.data.get('published', '')
            published_dt = parse_datetime(published_str) if published_str else timezone.now()

            post_obj, created = Post.objects.update_or_create(
                id=post_id,
                defaults={
                    'title': title,
                    'description': description,
                    'content': content,
                    'contentType': contentType,
                    'visibility': visibility,
                    'author': author,
                    'page': page,
                    'published': published_dt,
                }
            )
            print(f"Post created: {created}, ID: {post_obj.id}")
            return post_obj
        except Exception as e:
            print(f"Error creating/updating post: {e}")
            return None

    def get_or_create_author_from_data(self,remote_author_data):
        try:
            remote_author_id = remote_author_data.get("id", "")
            remote_row_id = remote_author_data.get("row_id") or remote_author_id.split("/")[-1]
            host = remote_author_data.get("host", "")
            display_name = remote_author_data.get("displayName") or remote_author_data.get("username") or "unknown"
            github = remote_author_data.get("github", "")
            avatar_url = remote_author_data.get("profileImage", None)
            full_id = remote_author_id or f"{host}authors/{remote_row_id}"
            author, created = Authors.objects.get_or_create(
                id=full_id,
                defaults={
                    "row_id": UUID(remote_row_id),
                    "host": host,
                    "username": display_name,
                    "displayName": display_name,
                    "github_username": github,
                    "avatar_url": avatar_url,
                    "local": False,
                    "is_approved": True,  
                }
            )
            return author
        except Exception as e:
            print(f"[get_or_create_author_from_data] Error creating author from data: {e}")
            return None


    def handle_like(self, request, author): 
        object_url = request.data.get("object")  
        object_id = object_url.split("/")[-1] 
        if "/posts/" in object_url:
            liked_object = get_object_or_404(Post, id=object_id)
            receiver = liked_object.author
        elif "/commented/" in object_url:
            liked_object = get_object_or_404(Comment, id=object_id)
            receiver = liked_object.author
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

    def save_item(self, author, data_type, content):
        author = get_object_or_404(Authors, id=author)
        Inbox.objects.create(
                author=author, 
                type=data_type,
                content=content
            )
        for author in Authors.objects.all():
            host = author.host

            inbox_url = f"{host}authors/{author.row_id}/inbox/"
            print(inbox_url)
            try:
                response = requests.post(
                    inbox_url,
                    json=content,
                    timeout = 5
                )
            except Exception as e:
                print(f"Failed to send post to {inbox_url}: {e}")