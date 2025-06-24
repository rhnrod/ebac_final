from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('smalltalk.urls')),
]

handler404 = 'smalltalk.views.handling_404'