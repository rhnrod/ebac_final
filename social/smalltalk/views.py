from django.shortcuts import render
from datetime import datetime, date


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
    data_atual = date.today()
    data_base = date(2025, 5, 27)
    super_user_date = str((data_atual - data_base).days)

    context = {
        'super_user_date': super_user_date + " dias" if super_user_date != 1 else super_user_date + " dia"
    }

    return render(request, 'dashboard.html', context)

def profile(request, slug=None):
    data_atual = date.today()
    data_base = date(2025, 5, 27)
    super_user_date = str((data_atual - data_base).days)

    context = {
        'profile' : slug,
        'super_user_date': super_user_date + " dias" if super_user_date != 1 else super_user_date + " dia"
    }
    return render(request, 'profile.html', context)

def search(request, slug=None):
    context = {
        'search_term' : slug
    }
    return render(request, 'search.html', context)