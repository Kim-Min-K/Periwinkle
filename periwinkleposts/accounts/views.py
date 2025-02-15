from django.shortcuts import render, redirect, get_object_or_404
from .forms import AuthorCreation
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import Authors
from .serializers import authorSerializer
from django.http import QueryDict

def loginView(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("accounts:home")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "login.html")


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
    # TODO: add not matching password and existing user and existing github handling


def profileView(request, username):
    author = get_object_or_404(Authors, username=username)
    ownProfile = request.user.is_authenticated and (request.user == author)

    context = {
        "author": author,
        "ownProfile": ownProfile,
    }
    return render(request, "profile.html", context)


def homePageView(request):
    user = request.user
    context = {
        "username": user.username,
        "github_username": user.github_username,
    }
    return render(request, "home.html", context)


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
