from django.shortcuts import render, redirect
from django.db.models import Q
from datetime import date
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile, User, Post

def welcome(request):
    context = {
        'hide_header': True,
        'subscribe': True
    }
    return render(request, 'smalltalk/pages/welcome.html', context)

def register(request):
    if request.user.is_authenticated:
        return redirect(request.GET.get('next') or 'dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')

        if password == confirm_password:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'As senhas devem ser iguais.')
            return redirect('register')

    context = {
        'hide_header': True,
        'subscribe': True,
        'password_pattern': r'(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}',
        'username_pattern': r'^[a-zA-Z0-9_-]+$'
    }
    return render(request, 'smalltalk/pages/register.html', context)

def login_view(request, slug=None):
    if request.user.is_authenticated:
        return redirect(request.GET.get('next') or 'dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
            return redirect('login')
    else:
        context = {
        'hide_header': True,
        'subscribe': True,
        }
        return render(request, 'smalltalk/pages/login.html', context)
@login_required
def dashboard(request):
    data_atual = date.today()
    data_base = date(2025, 5, 27)
    super_user_date = str((data_atual - data_base).days)

    logged_user = get_object_or_404(Profile, user__username=request.user.username)
    profiles = Profile.objects.all().exclude(user=request.user)

    seguindo = logged_user.follows.all()
    usuarios_seguidos = [perfil.user for perfil in seguindo] + [request.user]

    posts = Post.objects.filter(user__in=usuarios_seguidos).order_by('-created_at')

    context = {
        'super_user_date': super_user_date + " dias" if super_user_date != 1 else super_user_date + " dia",
        'profiles': profiles,
        'user': request.user,
        'logged_user': logged_user,
        'posts': posts
    }

    return render(request, 'smalltalk/pages/dashboard.html', context)


from django.shortcuts import get_object_or_404

@login_required
def profile(request, slug=None):
    data_atual = date.today()
    data_base = date(2025, 5, 27)
    super_user_days = (data_atual - data_base).days
    super_user_date = f"{super_user_days} {'dia' if super_user_days == 1 else 'dias'}"
    posts = Post.objects.filter(user__username=slug).order_by('-created_at')

    if slug is None:
        return redirect('profile', slug=request.user.username)

    # Busca o Profile com base no slug (username do User)
    user_profile = get_object_or_404(Profile, user__username=slug)
    logged_user = get_object_or_404(Profile, user__username=request.user.username)
    profiles = Profile.objects.all().exclude(user=request.user)

    if request.method == 'POST':
        action = request.POST['follow']

        if action == 'follow':
            logged_user.follows.add(user_profile)
        elif action == 'unfollow':
            logged_user.follows.remove(user_profile)
        logged_user.save()

    context = {
        'profiles': profiles,
        'user': request.user,
        'slug': slug,
        'follows': user_profile.follows.exclude(user__id=user_profile.user.id),
        'logged_follows': logged_user.follows.exclude(user__id=logged_user.user.id),
        'followers': user_profile.followed_by.exclude(user__id=user_profile.user.id),
        'logged_user': logged_user,
        'profile_data': user_profile,
        'super_user_date': super_user_date,
        'follow_you': logged_user.followed_by.all().exclude(id=logged_user.user.id),
        'subscribe': True,
        'aguardando': False,
        'posts': posts
    }
    return render(request, 'smalltalk/pages/profile.html', context)


@login_required
def search(request, slug=None):
    user = User.objects.exclude(username=request.user.username)
    profiles = Profile.objects.exclude(first_name=request.user.first_name)
    context = {
        'search_term' : slug,
        'profiles' : [user, profiles]
    }
    return render(request, 'smalltalk/pages/search.html', context)

def logout_view(request):
    logout(request)
    return redirect('login')