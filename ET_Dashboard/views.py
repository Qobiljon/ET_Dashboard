from django.contrib.auth import authenticate as dj_auth, login as dj_login, logout as dj_logout
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from ET_Dashboard.models import Campaigns


@require_http_methods(['GET'])
def handle_index(request):
    if request.user.is_authenticated:
        return render(
            request=request,
            template_name='dashboard_page.html',
            context={
                'title': 'My Campaigns',
                'campaigns': Campaigns.objects.filter(creatorEmail=request.user.email)
            }
        )
    else:
        return redirect(to='login')


@require_http_methods(['GET', 'POST'])
def handle_authenticate(request):
    if request.method == 'POST':
        if 'email' in request.POST and 'password' in request.POST:
            user = dj_auth(request=request, username=request.POST['email'], password=request.POST['password'])
            dj_login(request=request, user=user)
        if request.user.is_authenticated:
            return redirect(to='index')
        else:
            return redirect(to='authenticate')
    else:
        return render(
            request=request,
            template_name='auth_page.html',
            context={'title': 'Authentication'}
        )


@require_http_methods(['POST'])
def handle_register(request):
    if request.user.is_authenticated:
        return redirect('index')
    elif 'email' in request.POST and 'password' in request.POST and 're_password' in request.POST and \
            request.POST['password'] == request.POST['re_password'] and not User.objects.filter(email=request.POST['email']).exists():
        User.objects.create_user(username=request.POST['email'], email=request.POST['email'], password=request.POST['password'])
        return redirect(to='index')
    else:
        return redirect(to='login')


@require_http_methods(['GET'])
def handle_logout(request):
    if request.user.is_authenticated:
        dj_logout(request=request)
    return redirect(to='login')


@require_http_methods(['GET'])
def handle_campaign(request):
    if not request.user.is_authenticated:
        return redirect(to='login')
    if 'id' not in request.GET or not Campaigns.objects.filter(id=request.GET['id']).exists():
        return redirect(to='index')
    else:
        campaign = Campaigns.objects.get(id=request.GET['id'])
        return render(
            request=request,
            template_name='campaign_details.html',
            context={
                'title': campaign.title,
                'campaign': campaign
            }
        )
