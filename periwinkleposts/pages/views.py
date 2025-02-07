from django.shortcuts import render

def homeView(request):
    context = {
        'username': 'JohnDoe',  
    }
    return render(request, 'home.html', context)
