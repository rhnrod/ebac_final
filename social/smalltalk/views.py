from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.urls import reverse

from .models import Profile, User, Post, Tag
from .forms import PostForm, ProfileForm, ProfilePicForm, SearchForm
from .censor import PALAVRAS_PROIBIDAS, CARACTERES_SUBSTITUTIVOS

from datetime import date
import random
import re

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
        'username_pattern': r'^[a-zA-Z]\w+$'
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

def censurar_palavras(texto, palavras_proibidas, substitutos):
    def substituir(match):
        palavra = match.group()
        return ''.join(random.choices(substitutos, k=len(palavra)))

    for palavra in palavras_proibidas:
        # Expressão regular com bordas de palavra, case insensitive
        regex = re.compile(rf'\b{re.escape(palavra)}\b', re.IGNORECASE)
        texto = regex.sub(substituir, texto)
    
    return texto

@login_required
def dashboard(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        search_form = SearchForm(request.POST)

        # Se o search_form foi submetido e é válido
        if search_form.is_valid() and 'search' in request.POST:
            termo = search_form.cleaned_data['query']
            return redirect(f"{reverse('search')}?q={termo}")

        if form.is_valid() and 'posts' in request.POST:
            action = request.POST['posts']

            if action == 'create':
                post = form.save(commit=False)
                post.user = request.user

                # Extrai hashtags
                hashtags = re.findall(r'#\w+', post.content)

                # Remove o símbolo '#' do texto
                for tag in hashtags:
                    post.content = post.content.replace(tag, tag[1:])

                # Censura palavras proibidas no conteúdo
                post.content = censurar_palavras(
                    post.content,
                    palavras_proibidas=PALAVRAS_PROIBIDAS,
                    substitutos=CARACTERES_SUBSTITUTIVOS
                )

                post.save()

                for tag_name in hashtags:
                    tag_text = tag_name[1:].lower()
                    if tag_text not in [p.lower() for p in PALAVRAS_PROIBIDAS]:
                        tag_obj, _ = Tag.objects.get_or_create(name=tag_text)
                        post.tags.add(tag_obj)

        return redirect('dashboard')

    else:
        form = PostForm()
        search_form = SearchForm()

    # Dados do dashboard
    data_atual = date.today()
    data_base = date(2025, 5, 27)
    super_user_date = str((data_atual - data_base).days)

    logged_user = get_object_or_404(Profile, user__username=request.user.username)
    profiles = Profile.objects.all().exclude(user=request.user)

    seguindo = logged_user.follows.all()
    usuarios_seguidos = [perfil.user for perfil in seguindo] + [request.user]

    posts = Post.objects.filter(
        Q(user__in=usuarios_seguidos) | Q(shares__in=usuarios_seguidos)
    ).distinct()
    shared_posts = len([post for post in posts if request.user in post.shares.all()])

    context = {
        'super_user_date': super_user_date + " dias" if super_user_date != 1 else super_user_date + " dia",
        'profiles': profiles,
        'profile_data': request.user,
        'user': request.user,
        'logged_user': logged_user,
        'logged_follows': logged_user.follows.exclude(user__id=logged_user.user.id),
        'posts': posts,
        'shared_posts': shared_posts,
        'tags': Tag.objects.annotate(mentions=Count('post')).order_by('-mentions'),
        'filtered_tags': Tag.objects.annotate(mentions=Count('post'))
                            .filter(mentions__gt=0)
                            .order_by('-mentions')[:10],
        'form': form,
        'search_form': search_form,  # inclui o search_form no contexto
    }

    return render(request, 'smalltalk/pages/dashboard.html', context)

@login_required
def post_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
    else:  
        post.likes.add(request.user)
    
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if post.shares.filter(id=request.user.id).exists():
        post.shares.remove(request.user)
    else:  
        post.shares.add(request.user)
    
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def profile(request, slug=None):
    data_atual = date.today()
    data_base = date(2025, 5, 27)
    super_user_days = (data_atual - data_base).days
    super_user_date = f"{super_user_days} {'dia' if super_user_days == 1 else 'dias'}"

    if slug is None:
        return redirect('profile', slug=request.user.username)

    posts = Post.objects.filter(user__username=slug)
    user_profile = get_object_or_404(Profile, user__username=slug)
    logged_user = get_object_or_404(Profile, user__username=request.user.username)
    profiles = Profile.objects.all().exclude(user=request.user)

    pic_form = ProfilePicForm(request.POST or None, request.FILES or None, instance=request.user.profile)

    if request.method == 'POST':
        if 'follow' in request.POST:
            action = request.POST['follow']
            if action == 'follow':
                logged_user.follows.add(user_profile)
            elif action == 'unfollow':
                logged_user.follows.remove(user_profile)
            logged_user.save()
            return redirect('profile', slug=slug)

        # Se não for follow/unfollow, assume que é upload de imagem
        if pic_form.is_valid():
            pic_form.save()
            messages.success(request, "Imagem atualizada com sucesso!")
            return redirect('profile', slug=slug)
        else:
            messages.error(request, "Erro ao atualizar a imagem. Verifique o arquivo enviado.")

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
        'posts': posts,
        'tags': Tag.objects.annotate(mentions=Count('post')).order_by('-mentions'),
        'filtered_tags': Tag.objects.annotate(mentions=Count('post'))
                            .filter(mentions__gt=0)
                            .order_by('-mentions')[:10],
        'pic_form': pic_form,
    }
    return render(request, 'smalltalk/pages/profile.html', context)



@login_required
def whoswho(request, slug=None):
    data_atual = date.today()
    data_base = date(2025, 5, 27)
    super_user_days = (data_atual - data_base).days
    super_user_date = f"{super_user_days} {'dia' if super_user_days == 1 else 'dias'}"
    posts = Post.objects.filter(user__username=slug)

    if slug is None:
        return redirect('whoswho', slug=request.user.username)

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
        'posts': posts,
        'tags': Tag.objects.annotate(mentions=Count('post')).order_by('-mentions'),
        'filtered_tags': Tag.objects.annotate(mentions=Count('post'))
                            .filter(mentions__gt=0)
                            .order_by('-mentions')[:10],
    }
    return render(request, 'smalltalk/pages/whoswho.html', context)

@login_required
def delete_post(request, post_id=None):
    if User.objects.get(username=request.user.username) == Post.objects.get(id=post_id).user:
        post = get_object_or_404(Post, id=post_id)
        post.delete()
        return redirect('dashboard')

@login_required
def config(request):
    user = request.user
    profile = user.profile

    # Formulário de imagem
    pic_form = ProfilePicForm(request.POST or None, request.FILES or None, instance=profile)

    if request.method == 'POST':
        # Atualiza dados básicos do usuário
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        description = request.POST.get('description', '').strip()
        location = request.POST.get('location', '').strip()
        is_public = request.POST.get('is_public') == 'on'

        if username:
            user.username = username
        user.save()

        if first_name:
            profile.first_name = first_name
        if description:
            profile.description = description
        if location:
            profile.location = location
        profile.is_public = is_public  # mesmo que esteja off, salva False

        # Se o form de imagem for válido, salva as imagens
        if pic_form.is_valid():
            pic_form.save()

        profile.save()

        messages.success(request, 'Dados atualizados com sucesso!')
        return redirect('profile')

    context = {
        'password_pattern': r'(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}',
        'username_pattern': r'^[a-z][a-z0-9_]+$',
        'first_name_pattern': r'^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s]+$',
        'location_pattern': r'^[A-Za-zÀ-ÿ\s]+$',
        'config_username': user.username,
        'config_first_name': profile.first_name or '',
        'config_description': profile.description or '',
        'config_location': profile.location or '',
        'config_is_public': profile.is_public,
        'logged_user': get_object_or_404(Profile, user__username=user.username),
        'form': ProfileForm(instance=profile),
        'pic_form': pic_form,
    }
    return render(request, 'smalltalk/pages/config.html', context)


@login_required
def search(request, slug=None):
    termo = request.GET.get('q', '')
    resultados = Post.objects.filter(content__icontains=termo)

    return render(request, 'smalltalk/pages/search.html', {
        'termo': termo,
        'resultados': resultados,
    }) 

def logout_view(request):
    logout(request)
    return redirect('login')

def updatePics(request):
    path = request.path

    if request.method == 'POST':
        form = ProfilePicForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            if 'config' in path:
                return redirect('config')
            return redirect('profile')
    if 'config' in path:
        return redirect('config')
    return redirect('profile')