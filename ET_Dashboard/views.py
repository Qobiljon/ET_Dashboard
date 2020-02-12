from django.contrib.auth import logout as dj_logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

# gRPC
import grpc
from et_grpcs import et_service_pb2
from et_grpcs import et_service_pb2_grpc

from ET_Dashboard.models import PresetDataSources, GrpcUserIds, Campaign

import json

GRPC_HOST = '165.246.43.162:50051'


@require_http_methods(['GET'])
def handle_index(request):
    grpc_user_id = GrpcUserIds.get_id(email=request.user.email)
    if request.user.is_authenticated and grpc_user_id is not None:
        channel = grpc.insecure_channel(GRPC_HOST)
        stub = et_service_pb2_grpc.ETServiceStub(channel)
        grpc_req = et_service_pb2.RetrieveCampaignsRequestMessage(userId=grpc_user_id, email=request.user.email, myCampaignsOnly=True)
        grpc_res: et_service_pb2.RetrieveCampaignsResponseMessage = stub.retrieveCampaigns(grpc_req)
        channel.close()
        campaigns = []
        if grpc_res.doneSuccessfully:
            for campaign_id, name, notes, creator_email, config_json, participant_count in zip(grpc_res.campaignId, grpc_res.name, grpc_res.notes, grpc_res.creatorEmail, grpc_res.configJson, grpc_res.participantCount):
                campaigns += [Campaign(campaign_id=campaign_id, name=name, notes=notes, creator_email=creator_email, config_json=config_json, participant_count=participant_count)]
        return render(
            request=request,
            template_name='campaigns_page.html',
            context={
                'title': 'My Campaigns',
                'campaigns': campaigns
            }
        )
    else:
        return redirect(to='login')


@require_http_methods(['GET', 'POST'])
def handle_login(request):
    if request.user.is_authenticated:
        channel = grpc.insecure_channel(GRPC_HOST)
        stub = et_service_pb2_grpc.ETServiceStub(channel)
        grpc_req = et_service_pb2.DashboardLoginWithEmailRequestMessage(email=request.user.email, name=request.user.get_full_name(), dashboardKey='ETd@$#b0@rd')
        grpc_res: et_service_pb2.LoginResponseMessage = stub.dashboardLoginWithEmail(grpc_req)
        channel.close()
        if grpc_res.doneSuccessfully:
            GrpcUserIds.create_or_update(email=request.user.email, user_id=grpc_res.userId)
            return redirect(to='index')
        else:
            dj_logout(request=request)
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
        user = User.objects.create_user(username=request.POST['email'], email=request.POST['email'], password=request.POST['password'])
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
    if 'id' not in request.GET:
        return redirect(to='index')
    else:
        # TODO: fill this part
        # campaigns = from gRPC
        return render(
            request=request,
            template_name='campaign_details.html',
            context={
                'title': 'Dummy',
                'campaign': 'Dummy'
            }
        )


@require_http_methods(['GET', 'POST'])
def handle_create_campaign(request):
    grpc_user_id = GrpcUserIds.get_id(email=request.user.email)
    if request.user.is_authenticated and grpc_user_id is not None:
        if request.method == 'POST':
            config_json = {}
            counter = 0
            for elem in PresetDataSources.all_preset_data_sources():
                if elem['name'] in request.POST:
                    data_source = {'name': elem['name']}
                    if 'rate_%s' % elem['name'] in request.POST:
                        data_source['rate'] = request.POST['rate_%s' % elem['name']]
                    elif 'json_%s' % elem['name'] in request.POST:
                        data_source['json'] = request.POST['json_%s' % elem['name']]
                    else:
                        return render(
                            request=request,
                            template_name='create_campaign_page.html',
                            context={
                                'error': True,
                                'android': PresetDataSources.android_sensors,
                                'tizen': PresetDataSources.tizen_sensors,
                                'others': PresetDataSources.others
                            }
                        )
                    config_json[counter] = data_source
                    counter += 1
            channel = grpc.insecure_channel(GRPC_HOST)
            stub = et_service_pb2_grpc.ETServiceStub(channel)
            grpc_req = et_service_pb2.RegisterCampaignRequestMessage(
                userId=grpc_user_id,
                email=request.user.email,
                name=request.POST['name'],
                notes=request.POST['notes'],
                configJson=json.dumps(obj=config_json)
            )
            grpc_res: et_service_pb2.RegisterCampaignResponseMessage = stub.registerCampaign(grpc_req)
            channel.close()
            if grpc_res.doneSuccessfully:
                return redirect(to='index')
            else:
                return render(
                    request=request,
                    template_name='create_campaign_page.html',
                    context={
                        'error': True,
                        'android': PresetDataSources.android_sensors,
                        'tizen': PresetDataSources.tizen_sensors,
                        'others': PresetDataSources.others
                    }
                )
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
    else:
        return redirect(to='login')


def handle_google_verification(request):
    return render(request=request, template_name='google43e44b3701ba10c8.html')
