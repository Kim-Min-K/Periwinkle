from django.shortcuts import render

def homeView(request):
    user = request.user
    context = {
        "username": user.username,
        "github_username": user.github_username,
    }
    return render(request, "home.html", context)
