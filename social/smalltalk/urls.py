from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('welcome', views.welcome, name='welcome'),
    path('', views.dashboard, name='dashboard'),
    path('profile/<slug:slug>/', views.profile, name='profile'),
    path('profile/', views.profile, name='profile'),
    path('whoswho/<slug:slug>/', views.whoswho, name='whoswho'),
    path('whoswho/', views.whoswho, name='whoswho'),
    path('search', views.search, name='search'),
    path('login', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register', views.register, name='register'),
    path('delete_post/<int:post_id>', views.delete_post, name='delete_post'),
    path('post_like/<int:post_id>', views.post_like, name='post_like'),
    path('post_share/<int:post_id>', views.post_share, name='post_share'),
    path('config', views.config, name='config'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)