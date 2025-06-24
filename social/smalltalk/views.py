from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.db import transaction
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
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                storage = messages.get_messages(request)
                list(storage)
                messages.error(request, 'Este nome de usuário já está em uso.')
                return redirect('register')
            
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                storage = messages.get_messages(request)
                list(storage)
                messages.error(request, 'Este email já está em uso.')
                return redirect('register')

            try:
                with transaction.atomic():
                    user = User.objects.create_user(username=username, email=email, password=password)
                    login(request, user)
                    return redirect('dashboard')
            except Exception as e:
                storage = messages.get_messages(request)
                list(storage)
                print(e)
                messages.error(request, 'Erro ao criar usuário. Por favor, tente novamente.')
                return redirect('register')
        else:
            storage = messages.get_messages(request)
            list(storage)
            messages.error(request, 'As senhas devem ser iguais.')
            return redirect('register')

    context = {
        'hide_header': True,
        'subscribe': True,
        'password_pattern': r'(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}',
        'username_pattern': r'^[a-z]\w+$'
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
            storage = messages.get_messages(request)
            list(storage)
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
                mentions = re.findall(r'@\w+', post.content)

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

    profiles = Profile.objects.all().exclude(user=request.user)
    public_profiles = profiles.filter(is_public=True)
    public_profiles_users = [profile.user for profile in public_profiles]

    logged_user = get_object_or_404(Profile, user__username=request.user.username)
    logged_follows_user = [follow.user for follow in logged_user.follows.exclude(user__id=logged_user.user.id)]
    logged_follows = logged_user.follows.exclude(user__id=logged_user.user.id)
    not_known_users = list(profiles.exclude(user__in=logged_follows_user))
    random.shuffle(not_known_users)

    not_known_users = not_known_users[:4]

    seguindo = logged_user.follows.all()
    usuarios_seguidos = [perfil.user for perfil in seguindo] + [request.user]

    posts = Post.objects.filter(
        Q(user__in=usuarios_seguidos) | Q(shares__in=usuarios_seguidos)
    ).distinct()

    displayable_posts = posts.filter(
        Q(user__in=public_profiles_users) |
        Q(user__in=logged_follows_user) |
        Q(user=request.user) |
        Q(shares=request.user, user__in=logged_follows_user)
    ).distinct()
    
    shared_posts = [post for post in posts if request.user in post.shares.all()]
    shared_follows = [post.user for post in shared_posts]
    shared_posts_count = len([post for post in posts if request.user in post.shares.all()])

    context = {
        'super_user_date': super_user_date + " dias" if super_user_date != 1 else super_user_date + " dia",
        'profiles': profiles,
        'public_profiles': public_profiles,
        'public_profiles_users': public_profiles_users,
        'profile_data': request.user,
        'user': request.user,
        'logged_user': logged_user,
        'logged_follows': logged_follows,
        'logged_follows_user': logged_follows_user,
        'not_known_users': not_known_users,
        'posts': posts,
        'displayable_posts': displayable_posts,
        'shared_posts': shared_posts,
        'shared_follows': shared_follows,
        'shared_posts_count': shared_posts_count,
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

    user_profile = get_object_or_404(Profile, user__username=slug)
    profiles = Profile.objects.all().exclude(user=request.user)

    public_profiles = profiles.filter(is_public=True)
    public_profiles_users = [profile.user for profile in public_profiles]

    logged_user = get_object_or_404(Profile, user__username=request.user.username)
    logged_follows = logged_user.follows.exclude(user__id=logged_user.user.id)
    logged_follows_user = [follow.user for follow in logged_user.follows.exclude(user__id=logged_user.user.id)]
    not_known_users = list(profiles.exclude(user__in=logged_follows_user))
    random.shuffle(not_known_users)

    not_known_users = not_known_users[:4]
    
    seguindo = logged_user.follows.all()
    usuarios_seguidos = [perfil.user for perfil in seguindo] + [request.user]
    third_follows = user_profile.follows.all()
    third_follows_users = [perfil.user for perfil in third_follows.exclude(user__id=user_profile.user.id)]

    posts = Post.objects.filter(
        Q(user=request.user) | Q(shares__in=usuarios_seguidos)
    ).distinct()

    displayable_posts = posts.filter(
        Q(user=request.user) |
        Q(shares=request.user, user__in=public_profiles_users) |
        Q(shares=request.user, user__in=logged_follows_user)
    ).distinct()

    profile_posts = Post.objects.filter(
        Q(user__username=slug) |
        Q(shares=user_profile.user, user__in=third_follows_users)
        ).distinct().order_by('-created_at')
    shared_posts = [post.user for post in posts if request.user in post.shares.all()]
    shared_posts_count = len([post for post in posts if request.user in post.shares.all()])

    pic_form = ProfilePicForm(request.POST or None, request.FILES or None, instance=request.user.profile)

    search_form = SearchForm(request.POST or None)

    if request.method == 'POST' and 'search' in request.POST:
        if search_form.is_valid():
            termo = search_form.cleaned_data['query']
            return redirect(f"{reverse('search')}?q={termo}")
        
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
            storage = messages.get_messages(request)
            list(storage)
            messages.success(request, "Imagem atualizada com sucesso!")
            return redirect('profile', slug=slug)
        else:
            storage = messages.get_messages(request)
            list(storage)
            messages.error(request, "Erro ao atualizar a imagem. Verifique o arquivo enviado.")

    context = {
        'profiles': profiles,
        'user': request.user,
        'slug': slug,
        'follows': user_profile.follows.exclude(user__id=user_profile.user.id),
        'logged_follows': logged_user.follows.exclude(user__id=logged_user.user.id),
        'logged_follows_user': [follow.user for follow in logged_user.follows.exclude(user__id=logged_user.user.id)],
        'followers': user_profile.followed_by.exclude(user__id=user_profile.user.id),
        'logged_user': logged_user,
        'third_follows': third_follows,
        'third_follows_users': third_follows_users,
        'profile_data': user_profile,
        'profile_posts': profile_posts,
        'public_profiles': public_profiles,
        'public_profiles_users': public_profiles_users,
        'super_user_date': super_user_date,
        'follow_you': logged_user.followed_by.all().exclude(id=logged_user.user.id),
        'subscribe': True,
        'aguardando': False,
        'not_known_users': not_known_users,
        'posts': posts,
        'displayable_posts': displayable_posts,
        'shared_posts': shared_posts,
        'shared_posts_count': shared_posts_count,
        'tags': Tag.objects.annotate(mentions=Count('post')).order_by('-mentions'),
        'filtered_tags': Tag.objects.annotate(mentions=Count('post'))
                            .filter(mentions__gt=0)
                            .order_by('-mentions')[:10],
        'pic_form': pic_form,
        'search_form': search_form
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

    logged_user = get_object_or_404(Profile, user__username=request.user.username)
    logged_follows = logged_user.follows.exclude(user__id=logged_user.user.id)
    logged_follows_user = [follow.user for follow in logged_user.follows.exclude(user__id=logged_user.user.id)]
    not_known_users = list(profiles.exclude(user__in=logged_follows_user))
    random.shuffle(not_known_users)

    not_known_users = not_known_users[:4]

    search_form = SearchForm(request.POST or None)

    if request.method == 'POST' and 'search' in request.POST:
        if search_form.is_valid():
            termo = search_form.cleaned_data['query']
            return redirect(f"{reverse('search')}?q={termo}")

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
        'not_known_users': not_known_users,
        'super_user_date': super_user_date,
        'follow_you': logged_user.followed_by.all().exclude(id=logged_user.user.id),
        'subscribe': True,
        'aguardando': False,
        'posts': posts,
        'tags': Tag.objects.annotate(mentions=Count('post')).order_by('-mentions'),
        'filtered_tags': Tag.objects.annotate(mentions=Count('post'))
                            .filter(mentions__gt=0)
                            .order_by('-mentions')[:10],
        'search_form': search_form
    }
    return render(request, 'smalltalk/pages/whoswho.html', context)

@login_required
def delete_post(request, post_id=None):
    if User.objects.get(username=request.user.username) == Post.objects.get(id=post_id).user:
        post = get_object_or_404(Post, id=post_id)
        post.delete()
        return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def config(request):
    user = request.user
    profile = user.profile

    profiles = Profile.objects.all().exclude(user=request.user)
    logged_user = get_object_or_404(Profile, user__username=request.user.username)
    logged_follows = logged_user.follows.exclude(user__id=logged_user.user.id)
    logged_follows_user = [follow.user for follow in logged_user.follows.exclude(user__id=logged_user.user.id)]
    not_known_users = list(profiles.exclude(user__in=logged_follows_user))
    random.shuffle(not_known_users)

    not_known_users = not_known_users[:4]


    # Formulário de imagem
    pic_form = ProfilePicForm(request.POST or None, request.FILES or None, instance=profile)

    search_form = SearchForm(request.POST or None)

    if request.method == 'POST' and 'search' in request.POST:
        if search_form.is_valid():
            termo = search_form.cleaned_data['query']
            return redirect(f"{reverse('search')}?q={termo}")

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

        storage = messages.get_messages(request)
        list(storage)
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
        'not_known_users': not_known_users,
        'profiles': profiles,
        'logged_user': get_object_or_404(Profile, user__username=user.username),
        'form': ProfileForm(instance=profile),
        'pic_form': pic_form,
        'search_form': search_form
    }
    return render(request, 'smalltalk/pages/config.html', context)

@login_required
def search(request, slug=None):
    termo = request.GET.get('q', '')
    termo_mention = f'@{termo}'
    termo_tag = f'#{termo}'


    profiles = Profile.objects.all().exclude(user=request.user)
    logged_user = get_object_or_404(Profile, user__username=request.user.username)
    logged_follows_user = [follow.user for follow in logged_user.follows.exclude(user__id=logged_user.user.id)]
    public_profiles = profiles.filter(is_public=True)
    public_profiles_users = [profile.user for profile in public_profiles]

    logged_user = get_object_or_404(Profile, user__username=request.user.username)
    logged_follows = logged_user.follows.exclude(user__id=logged_user.user.id)
    logged_follows_user = [follow.user for follow in logged_user.follows.exclude(user__id=logged_user.user.id)]
    not_known_users = list(profiles.exclude(user__in=logged_follows_user))
    random.shuffle(not_known_users)

    not_known_users = not_known_users[:4]
    

    public_posts = Post.objects.filter(
        Q(user__in=logged_follows_user) |
        Q(user__in=public_profiles_users)
        ).order_by('-created_at')
    
    resultados = public_posts.filter(
        Q(content__icontains=termo) |
        Q(content__icontains=termo_mention) |
        Q(content__icontains=termo_tag)
        ).order_by('-created_at')
    
    resultados_perfis = profiles.filter(user__username__icontains=termo)[:3]

    search_form = SearchForm(request.POST or None)

    if request.method == 'POST' and 'search' in request.POST:
        if search_form.is_valid():
            termo = search_form.cleaned_data['query']
            return redirect(f"{reverse('search')}?q={termo}")
        
    return render(request, 'smalltalk/pages/search.html', {
        'termo': termo,
        'resultados': resultados,
        'resultados_perfis': resultados_perfis,
        'search_form': search_form,
        'profiles': profiles,
        'logged_user': logged_user,
        'not_known_users': not_known_users,
        'follow_you': logged_user.followed_by.all().exclude(id=logged_user.user.id),
        'logged_follows': logged_user.follows.exclude(user__id=logged_user.user.id),
        'logged_follows_user': logged_follows_user,
        'public_profiles': public_profiles,
        'public_profiles_users': public_profiles_users,
        'public_posts': public_posts
    }) 

def handling_404(request, exception=None):
    status=404

    search_form = SearchForm(request.POST or None)

    if request.method == 'POST' and 'search' in request.POST:
        if search_form.is_valid():
            termo = search_form.cleaned_data['query']
            return redirect(f"{reverse('search')}?q={termo}")



    return render(request, 'smalltalk/pages/404.html', {
        'status': status,
        'search_form': search_form,
    })
def logout_view(request):
    logout(request)
    storage = messages.get_messages(request)
    list(storage)
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