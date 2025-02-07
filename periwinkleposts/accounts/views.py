from django.shortcuts import render, redirect
from .forms import AuthorCreation
from django.contrib.auth import authenticate, login
from django.contrib import messages

def loginView(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('accounts:profile') 
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def registerView(request):
    if request.method == 'POST':
        form = AuthorCreation(request.POST)
        if form.is_valid():
            form.save()
            return redirect('accounts:login') 
    else:
        form = AuthorCreation()
    return render(request, 'register.html', {'form': form})
    # TODO: add not matching password and existing user and existing github handling 
    
def profileView(request):
    user = request.user  
    context = {
        "username": user.username,
        "github_username": user.github_username, 
    }
    return render(request, "profile.html", context)