from django.contrib.auth import authenticate as dj_auth
from django.contrib.auth import login as dj_login
from django.contrib.auth import logout as dj_logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from ET_Dashboard.models import Campaigns, PresetDataSources
from ET_Dashboard.models import UserToGrpcIdMap

import time
import psycopg2


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
def handle_login(request):
    if request.user.is_authenticated:
        return redirect(to='/')
    elif request.method == 'POST':
        if 'email' in request.POST and 'password' in request.POST:
            user = dj_auth(request=request, username=request.POST['email'], password=request.POST['password'])
            if user is None:
                return redirect(to='login')
            else:
                dj_login(request=request, user=user)
        if request.user.is_authenticated:
            return redirect(to='index')
        else:
            return redirect(to='login')
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
        conn = psycopg2.connect(
            host='165.246.43.97',
            database='easytrack_db',
            user='postgres',
            password='postgres'
        )
        cur = conn.cursor()
        cur.execute('select * from et_users where email=%s;', (request.POST['email'],))
        row = cur.fetchone()
        if row is None:
            timestamp_ms = int(round(time.time() * 1000))
            cur.execute(
                'insert into et_users(id_token, is_participant, name, email, last_sync_timestamp, last_heartbeat_timestamp) values (%s,%s,%s,%s,%s,%s);',
                (
                    '',
                    False,
                    request.POST['email'],
                    request.POST['email'],
                    timestamp_ms,
                    timestamp_ms
                )
            )
            conn.commit()
            user = User.objects.create_user(username=request.POST['email'], email=request.POST['email'], password=request.POST['password'])
            cur.execute('select id from et_users where email=%s;', (request.POST['email'],))
            UserToGrpcIdMap.objects.create(user=user, gRPCId=cur.fetchone()[0])
            cur.close()
            conn.close()
            return redirect(to='index')
        else:
            cur.close()
            conn.close()
            return redirect(to='login')
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


@require_http_methods(['GET', 'POST'])
def handle_create_campaign(request):
    if request.method == 'POST':
        return redirect(to='index')
    else:
        return render(
            request=request,
            template_name='create_campaign_page.html',
            context={
                'android': PresetDataSources.android_sensors,
                'tizen': PresetDataSources.tizen_sensors,
                'others': PresetDataSources.others
            }
        )
