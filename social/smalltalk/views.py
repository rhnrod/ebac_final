from django.shortcuts import render

def welcome(request):
    context = {
        'hide_header': True
    }
    return render(request, 'welcome.html', context)

def login(request, slug=None):
    context = {
        'is_new_account': slug == 'new',
        'hide_header': True
    }
    return render(request, 'login.html', context)

def dashboard(request):
    return render(request, 'dashboard.html', {})

def profile(request, slug=None):
    context = {
        'profile' : slug
    }
    return render(request, 'profile.html', context)

def search(request, slug=None):
    context = {
        'search_term' : slug
    }
    return render(request, 'search.html', context)