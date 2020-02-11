"""ET_Dashboard URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from ET_Dashboard import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('google43e44b3701ba10c8.html', views.handle_google_verification),
    path('google-auth/', include('social_django.urls', namespace='social')),

    path('', views.handle_index, name='index'),
    path('login/', views.handle_login, name='login'),
    path('register/', views.handle_register, name='register'),
    path('logout/', views.handle_logout, name='logout'),
    path('campaign/', views.handle_campaign, name='campaign'),
    path('new_campaign/', views.handle_create_campaign, name='create_campaign'),
]
