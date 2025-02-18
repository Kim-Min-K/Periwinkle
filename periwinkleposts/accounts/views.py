from django.shortcuts import render, redirect, get_object_or_404
from .forms import AuthorCreation, AvatarUpload
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import Authors, FollowRequest
from .serializers import authorSerializer
from django.http import QueryDict
from api.follow_views import getFriends, getFollowers, getFollowRequests\
 ,getSuggestions, acceptFollowRequest, declineFollowRequest, followRequest, getFollowees, getSentRequests
from django.http import HttpResponseRedirect
from django.urls import reverse
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
    if request.method == 'POST':
        form = AvatarUpload(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
    else:
        form = AvatarUpload()
    return render(request, 'avatar.html', {'form': form})

def registerView(request):
    if request.method == "POST":

        # Add a "host" field in the post request and set it to our server's / proxy's host name
        print(" RegisterView/request.POST : "+str(request.POST))
        ordinary_dict = dict(request.POST.dict())
        ordinary_dict["host"]=request.build_absolute_uri("/api/")
        query_dict = QueryDict('', mutable=True)
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
    followers = getFollowers(request, author.row_id.hex).data["followers"]
    requesters = getFollowRequests(request, author.row_id.hex).data["requesters"]
    suggestions = getSuggestions(request, author.row_id.hex).data["suggestions"]
    followees = getFollowees(request, author.row_id.hex).data["followees"]
    sent_requests = getSentRequests(request, author.row_id.hex).data["sent_requests"]

    context = {
        "author": author,
        "ownProfile": ownProfile,
        "friends": friends,
        "followers":followers,
        "requesters": requesters,
        "suggestions": suggestions,
        "followees": followees,
        "sent_requests": sent_requests,
        "follower_count":len(followers),
        "followee_count": len(followees)
    }

    return render(request, "profile.html", context)

def acceptRequest(request, author_serial, fqid):
    requester = Authors.objects.get(id=fqid)
    requestee = Authors.objects.get(row_id=uuid.UUID(hex=author_serial))
    follow_request = get_object_or_404(
        FollowRequest,
        requester=requester,
        requestee=requestee
    )
    response = acceptFollowRequest(request, follow_request.id)
    return redirect("accounts:profile", username=requestee.username)

def declineRequest(request, author_serial, fqid):
    requester = Authors.objects.get(id=fqid)
    requestee = Authors.objects.get(row_id=uuid.UUID(hex=author_serial))
    follow_request = get_object_or_404(
        FollowRequest,
        requester=requester,
        requestee=requestee
    )
    response = declineFollowRequest(request, follow_request.id)
    print(response)
    return redirect("accounts:profile", username=requestee.username)

def sendFollowRequest(request, fqid):
    requestee = Authors.objects.get(id=fqid)
    requester = Authors.objects.get(id=request.user.id)
    requestee_serializer = authorSerializer(requestee)
    serializer = authorSerializer(requester)
    response = requests.post(request.build_absolute_uri(f"/api/authors/{requestee.row_id.hex}/inbox"), headers={"Content-Type": "application/json"}, json={"actor": serializer.data})
    return redirect("accounts:profile", username=request.user.username)

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
    

