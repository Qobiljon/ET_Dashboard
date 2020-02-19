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

    path('login/', views.handle_login_api, name='login'),
    path('logout/', views.handle_logout_api, name='logout'),

    path('', views.handle_campaigns_list, name='campaigns-list'),
    path('campaign/', views.handle_participants_list, name='participants-list'),
    path('participant/', views.handle_participants_data_list, name='participant'),
    path('data/', views.handle_raw_samples_list, name='view_data'),
    path('edit/', views.handle_campaign_editor, name='campaign-editor'),

    path('download_campaign/', views.handle_download_campaign_api, name='get-configs'),
    path('delete/', views.handle_delete_campaign_api, name='delete-campaign'),
    path('download_data/', views.handle_download_data_api, name='download_data'),
]
