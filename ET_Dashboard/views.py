from django.contrib.auth import logout as dj_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

# gRPC
import grpc
from et_grpcs import et_service_pb2
from et_grpcs import et_service_pb2_grpc

from ET_Dashboard.models import PresetDataSources, GrpcUserIds, Campaign

import json
import datetime

from utils.utils import datetime_to_timestamp_ms

GRPC_HOST = '165.246.43.162:50051'


def handle_google_verification(request):
    return render(request=request, template_name='google43e44b3701ba10c8.html')


@login_required
def handle_index_page(request):
    grpc_user_id = GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is not None:
        channel = grpc.insecure_channel(GRPC_HOST)
        stub = et_service_pb2_grpc.ETServiceStub(channel)
        grpc_req = et_service_pb2.RetrieveCampaignsRequestMessage(userId=grpc_user_id, email=request.user.email, myCampaignsOnly=True)
        grpc_res: et_service_pb2.RetrieveCampaignsResponseMessage = stub.retrieveCampaigns(grpc_req)
        channel.close()
        if grpc_res.doneSuccessfully:
            for campaign_id, name, notes, start_timestamp, end_timestamp, creator_email, config_json, participant_count in zip(grpc_res.campaignId, grpc_res.name, grpc_res.notes, grpc_res.startTimestamp, grpc_res.endTimestamp, grpc_res.creatorEmail, grpc_res.configJson, grpc_res.participantCount):
                Campaign.create_or_update(
                    campaign_id=campaign_id,
                    requester_email=request.user.email,
                    name=name,
                    notes=notes,
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp,
                    creator_email=creator_email,
                    config_json=config_json,
                    participant_count=participant_count
                )
        return render(
            request=request,
            template_name='campaigns_page.html',
            context={
                'title': 'My Campaigns',
                'campaigns': Campaign.objects.filter(requester_email=request.user.email)
            }
        )
    else:
        return redirect(to='login')


@require_http_methods(['GET', 'POST'])
def handle_login_api(request):
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


@login_required
def handle_logout_api(request):
    if request.user.is_authenticated:
        dj_logout(request=request)
    return redirect(to='login')


@login_required
@require_http_methods(['GET', 'POST'])
def handle_create_campaign(request):
    grpc_user_id = GrpcUserIds.get_id(email=request.user.email)
    if request.user.is_authenticated and grpc_user_id is not None:
        if request.method == 'POST':
            channel = grpc.insecure_channel(GRPC_HOST)
            stub = et_service_pb2_grpc.ETServiceStub(channel)
            config_json = {}
            counter = 0
            for elem in PresetDataSources.all_preset_data_sources():
                if elem['name'] in request.POST:
                    grpc_req = et_service_pb2.BindDataSourceRequestMessage(
                        userId=grpc_user_id,
                        email=request.user.email,
                        name=elem['name']
                    )
                    grpc_res: et_service_pb2.BindDataSourceResponseMessage = stub.bindDataSource(grpc_req)
                    data_source = {'name': elem['name'], 'data_source_id': grpc_res.dataSourceId}
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
            grpc_req = et_service_pb2.RegisterCampaignRequestMessage(
                userId=grpc_user_id,
                email=request.user.email,
                name=request.POST['name'],
                notes=request.POST['notes'],
                startTimestamp=datetime_to_timestamp_ms(value=datetime.datetime.strptime(request.POST['startTime'], "%Y-%m-%dT%H:%M")),
                endTimestamp=datetime_to_timestamp_ms(value=datetime.datetime.strptime(request.POST['endTime'], "%Y-%m-%dT%H:%M")),
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
                        'title': 'New campaign',
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
                    'title': 'New campaign',
                    'android': PresetDataSources.android_sensors,
                    'tizen': PresetDataSources.tizen_sensors,
                    'others': PresetDataSources.others
                }
            )
    else:
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_campaign_details_page(request):
    grpc_user_id = GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is None:
        return redirect(to='login')
    elif 'id' not in request.GET or not str(request.GET['id']).isdigit() or not Campaign.objects.filter(campaign_id=request.GET['id'], requester_email=request.user.email).exists():
        return redirect(to='index')
    else:
        # campaign dashboard page
        campaign = Campaign.objects.get(campaign_id=request.GET['id'], requester_email=request.user.email)
        channel = grpc.insecure_channel(GRPC_HOST)
        stub = et_service_pb2_grpc.ETServiceStub(channel)
        grpc_req = et_service_pb2.RetrieveParticipantsRequestMessage(
            userId=grpc_user_id,
            email=request.user.email,
            campaignId=campaign.campaign_id
        )
        grpc_res: et_service_pb2.RetrieveParticipantsResponseMessage = stub.retrieveParticipants(grpc_req)
        channel.close()
        if grpc_res.doneSuccessfully:
            return render(
                request=request,
                template_name='campaign_details.html',
                context={
                    'title': '"%s" Dashboard' % campaign.name,
                    'campaign': campaign
                }
            )
        else:
            return redirect(to='index')
