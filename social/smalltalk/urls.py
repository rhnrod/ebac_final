
from django.urls import path
from . import views

urlpatterns = [
    path('welcome', views.welcome, name='welcome'),
    path('', views.dashboard, name='dashboard'),
    path('profile/<slug:slug>/', views.profile, name='profile'),
    path('search/<slug:slug>/', views.search, name='search'),
    path('login/', views.login, name='login'),
    path('login/<slug:slug>', views.login, name='login'),
]