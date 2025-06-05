from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('welcome', views.welcome, name='welcome'),
    path('', views.dashboard, name='dashboard'),
    path('profile/<slug:slug>/', views.profile, name='profile'),
    path('profile/', views.profile, name='profile'),
    path('search/<slug:slug>/', views.search, name='search'),
    path('login', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register', views.register, name='register'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)