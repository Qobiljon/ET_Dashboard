import json
import datetime
import csv

# Django
from django.contrib.auth import logout as dj_logout
from django.contrib.auth.decorators import login_required
from django.http import StreamingHttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

# gRPC
from et_grpcs import et_service_pb2

# EasyTrack
from ET_Dashboard import models as et_models
from utils import utils


def handle_google_verification(request):
    return render(request=request, template_name='google43e44b3701ba10c8.html')


@login_required
@require_http_methods(['GET'])
def handle_index_page(request):
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is not None:
        grpc_req = et_service_pb2.RetrieveCampaignsRequestMessage(userId=grpc_user_id, email=request.user.email, myCampaignsOnly=True)
        grpc_res: et_service_pb2.RetrieveCampaignsResponseMessage = utils.stub.retrieveCampaigns(grpc_req)
        if grpc_res.doneSuccessfully:
            for campaign_id, name, notes, start_timestamp, end_timestamp, creator_email, config_json, participant_count in zip(grpc_res.campaignId, grpc_res.name, grpc_res.notes, grpc_res.startTimestamp, grpc_res.endTimestamp, grpc_res.creatorEmail, grpc_res.configJson, grpc_res.participantCount):
                et_models.Campaign.create_or_update(
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
                'campaigns': et_models.Campaign.objects.filter(requester_email=request.user.email)
            }
        )
    else:
        return redirect(to='login')


@require_http_methods(['GET', 'POST'])
def handle_login_api(request):
    if request.user.is_authenticated:
        grpc_req = et_service_pb2.DashboardLoginWithEmailRequestMessage(email=request.user.email, name=request.user.get_full_name(), dashboardKey='ETd@$#b0@rd')
        grpc_res: et_service_pb2.LoginResponseMessage = utils.stub.dashboardLoginWithEmail(grpc_req)
        if grpc_res.doneSuccessfully:
            et_models.GrpcUserIds.create_or_update(email=request.user.email, user_id=grpc_res.userId)
            return redirect(to='index')
        else:
            dj_logout(request=request)
    return render(
        request=request,
        template_name='auth_page.html',
        context={'title': 'Authentication'}
    )


@login_required
@require_http_methods(['GET', 'POST'])
def handle_logout_api(request):
    if request.user.is_authenticated:
        dj_logout(request=request)
    return redirect(to='login')


@login_required
@require_http_methods(['GET', 'POST'])
def handle_create_campaign(request):
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if request.user.is_authenticated and grpc_user_id is not None:
        if request.method == 'POST':
            config_json = {}
            counter = 0
            for elem in et_models.PresetDataSources.all_preset_data_sources():
                if elem['name'] in request.POST:
                    grpc_req = et_service_pb2.BindDataSourceRequestMessage(
                        userId=grpc_user_id,
                        email=request.user.email,
                        name=elem['name'],
                        iconName=elem['icon']
                    )
                    grpc_res: et_service_pb2.BindDataSourceResponseMessage = utils.stub.bindDataSource(grpc_req)
                    data_source = {'name': elem['name'], 'data_source_id': grpc_res.dataSourceId, 'icon_name': grpc_res.iconName}
                    if 'delay_%s' % elem['name'] in request.POST:
                        data_source['delay'] = request.POST['delay_%s' % elem['name']]
                    elif 'json_%s' % elem['name'] in request.POST:
                        data_source['json'] = request.POST['json_%s' % elem['name']]
                    else:
                        return render(
                            request=request,
                            template_name='create_campaign_page.html',
                            context={
                                'error': True,
                                'android': et_models.PresetDataSources.android_sensors,
                                'tizen': et_models.PresetDataSources.tizen_sensors,
                                'others': et_models.PresetDataSources.others
                            }
                        )
                    config_json[counter] = data_source
                    counter += 1
            grpc_req = et_service_pb2.RegisterCampaignRequestMessage(
                userId=grpc_user_id,
                email=request.user.email,
                name=request.POST['name'],
                notes=request.POST['notes'],
                startTimestamp=utils.datetime_to_timestamp_ms(value=datetime.datetime.strptime(request.POST['startTime'], "%Y-%m-%dT%H:%M")),
                endTimestamp=utils.datetime_to_timestamp_ms(value=datetime.datetime.strptime(request.POST['endTime'], "%Y-%m-%dT%H:%M")),
                configJson=json.dumps(obj=config_json)
            )
            grpc_res: et_service_pb2.RegisterCampaignResponseMessage = utils.stub.registerCampaign(grpc_req)
            if grpc_res.doneSuccessfully:
                return redirect(to='index')
            else:
                return render(
                    request=request,
                    template_name='create_campaign_page.html',
                    context={
                        'error': True,
                        'title': 'New campaign',
                        'android': et_models.PresetDataSources.android_sensors,
                        'tizen': et_models.PresetDataSources.tizen_sensors,
                        'others': et_models.PresetDataSources.others
                    }
                )
        else:
            return render(
                request=request,
                template_name='create_campaign_page.html',
                context={
                    'title': 'New campaign',
                    'android': et_models.PresetDataSources.android_sensors,
                    'tizen': et_models.PresetDataSources.tizen_sensors,
                    'others': et_models.PresetDataSources.others
                }
            )
    else:
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_campaign_details_page(request):
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is None:
        return redirect(to='login')
    elif 'id' not in request.GET or not str(request.GET['id']).isdigit() or not et_models.Campaign.objects.filter(campaign_id=request.GET['id'], requester_email=request.user.email).exists():
        return redirect(to='index')
    else:
        # campaign dashboard page
        campaign = et_models.Campaign.objects.get(campaign_id=int(request.GET['id']), requester_email=request.user.email)
        grpc_req = et_service_pb2.RetrieveParticipantsRequestMessage(
            userId=grpc_user_id,
            email=request.user.email,
            campaignId=campaign.campaign_id
        )
        grpc_res: et_service_pb2.RetrieveParticipantsResponseMessage = utils.stub.retrieveParticipants(grpc_req)
        if grpc_res.doneSuccessfully:
            grpc_req = et_service_pb2.RetrieveParticipantsRequestMessage(
                userId=grpc_user_id,
                email=request.user.email,
                campaignId=campaign.campaign_id
            )
            grpc_res = utils.stub.retrieveParticipants(grpc_req)
            if grpc_res.doneSuccessfully:
                success = len(grpc_res.name) == 0
                for name, email in zip(grpc_res.name, grpc_res.email):
                    sub_grpc_req = et_service_pb2.RetrieveParticipantStatisticsRequestMessage(
                        userId=grpc_user_id,
                        email=request.user.email,
                        targetEmail=email,
                        targetCampaignId=campaign.campaign_id
                    )
                    sub_grpc_res: et_service_pb2.RetrieveParticipantStatisticsResponseMessage = utils.stub.retrieveParticipantStatistics(sub_grpc_req)
                    success |= sub_grpc_res.doneSuccessfully
                    if sub_grpc_res.doneSuccessfully:
                        et_models.Participant.create_or_update(
                            email=email,
                            campaign=campaign,
                            full_name=name,
                            day_no=utils.timestamp_diff_in_days(a=utils.timestamp_now_ms(), b=sub_grpc_res.campaignJoinTimestamp),
                            amount_of_data=sub_grpc_res.amountOfSubmittedDataSamples,
                            last_heartbeat_time=utils.timestamp_to_readable_string(sub_grpc_res.lastHeartbeatTimestamp),
                            last_sync_time=utils.timestamp_to_readable_string(sub_grpc_res.lastSyncTimestamp),
                            data_source_ids=sub_grpc_res.dataSourceId,
                            per_data_source_amount_of_data=sub_grpc_res.perDataSourceAmountOfData
                        )
                if success:
                    return render(
                        request=request,
                        template_name='campaign_details.html',
                        context={
                            'title': '"%s" Dashboard' % campaign.name,
                            'campaign': campaign,
                            'participants': et_models.Participant.objects.filter(campaign=campaign)
                        }
                    )
        return redirect(to='index')


@login_required
@require_http_methods(['GET'])
def handle_participant_details_page(request):
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is None:
        return redirect(to='login')
    elif 'campaign_id' not in request.GET or not str(request.GET['campaign_id']).isdigit() or not et_models.Campaign.objects.filter(campaign_id=request.GET['campaign_id'], requester_email=request.user.email).exists() or \
            'email' not in request.GET or not et_models.Participant.objects.filter(email=request.GET['email'], campaign_id=request.GET['campaign_id']).exists():
        return redirect(to='index')
    else:
        # participant details page
        campaign = et_models.Campaign.objects.get(campaign_id=request.GET['campaign_id'], requester_email=request.user.email)
        participant = et_models.Participant.objects.get(email=request.GET['email'], campaign=campaign)
        amount_of_data_map = {}
        for data_source_id, amount_of_data in zip(participant.data_source_ids.split(','), participant.per_data_source_amount_of_data.split(',')):
            amount_of_data_map[int(data_source_id)] = int(amount_of_data)
        config_json = json.loads(s=campaign.config_json)
        data_sources = []
        for index in config_json:
            data_source = config_json[index]
            data_source_id = data_source['data_source_id']
            if 'delay' in data_source:
                data_sources += [et_models.DataSource(data_source_id=data_source_id, name=data_source['name'], icon_name=data_source['icon_name'], amount_of_data=amount_of_data_map[data_source_id], delay=data_source['delay'])]
            elif 'json' in data_source:
                data_sources += [et_models.DataSource(data_source_id=data_source_id, name=data_source['name'], icon_name=data_source['icon_name'], amount_of_data=amount_of_data_map[data_source_id], json=data_source['json'])]
            else:
                raise ValueError('Bad campaign configurations, please refer to the application developer!')
        return render(
            request=request,
            template_name='participant_details.html',
            context={
                'title': "%s's data" % participant.full_name,
                'campaign': campaign,
                'participant': participant,
                'data_sources': data_sources
            }
        )


@login_required
@require_http_methods(['GET'])
def handle_view_data_page(request):
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is None:
        return redirect(to='login')
    elif 'campaign_id' not in request.GET or not str(request.GET['campaign_id']).isdigit() or not et_models.Campaign.objects.filter(campaign_id=request.GET['campaign_id'], requester_email=request.user.email).exists() or \
            'email' not in request.GET or not et_models.Participant.objects.filter(email=request.GET['email'], campaign_id=request.GET['campaign_id']).exists() or \
            'data_source_id' not in request.GET or not str(request.GET['data_source_id']).isdigit() or 'from_time' not in request.GET or not str(request.GET['from_time']).isdigit():
        return redirect(to='index')
    else:
        from_time = int(request.GET['from_time'])
        grpc_req = et_service_pb2.Retrieve100DataRecordsRequestMessage(
            userId=grpc_user_id,
            email=request.user.email,
            targetEmail=request.GET['email'],
            targetCampaignId=int(request.GET['campaign_id']),
            targetDataSourceId=int(request.GET['data_source_id']),
            fromTimestamp=from_time
        )
        grpc_res: et_service_pb2.Retrieve100DataRecordsResponseMessage = utils.stub.retrieve100DataRecords(grpc_req)
        if grpc_res.doneSuccessfully:
            records = []
            for timestamp, value in zip(grpc_res.timestamp, grpc_res.value):
                records += [et_models.Record(timestamp_ms=timestamp, value=value)]
                from_time = timestamp
            return render(
                request=request,
                template_name='view_raw_data.html',
                context={
                    'title': 'Data data samples (100 records at a time)',
                    'records': records,
                    'from_time': from_time
                }
            )
        else:
            return redirect(to='index')


@login_required
def handle_download_data_page(request):
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is None:
        return redirect(to='login')
    elif 'campaign_id' not in request.GET or not str(request.GET['campaign_id']).isdigit() or not et_models.Campaign.objects.filter(campaign_id=request.GET['campaign_id'], requester_email=request.user.email).exists() or \
            'email' not in request.GET or not et_models.Participant.objects.filter(email=request.GET['email'], campaign_id=request.GET['campaign_id']).exists() or \
            'data_source_id' not in request.GET or not str(request.GET['data_source_id']).isdigit():
        return redirect(to='index')
    else:
        campaign_id = int(request.GET['campaign_id'])
        email = request.GET['email']
        data_source_id = int(request.GET['data_source_id'])

        def load_next_100rows(pseudo_buffer):
            writer = csv.writer(pseudo_buffer)
            from_time = 0
            data_available = True
            while data_available:
                grpc_req = et_service_pb2.Retrieve100DataRecordsRequestMessage(
                    userId=grpc_user_id,
                    email=email,
                    targetEmail=request.GET['email'],
                    targetCampaignId=campaign_id,
                    targetDataSourceId=data_source_id,
                    fromTimestamp=from_time
                )
                grpc_res: et_service_pb2.Retrieve100DataRecordsResponseMessage = utils.stub.retrieve100DataRecords(grpc_req)
                if grpc_res.doneSuccessfully:
                    for timestamp, value in zip(grpc_res.timestamp, grpc_res.value):
                        from_time = timestamp
                        yield writer.writerow([str(timestamp), value])
                data_available = grpc_res.doneSuccessfully and grpc_res.moreDataAvailable

        gen = load_next_100rows(pseudo_buffer=et_models.Echo())
        res = StreamingHttpResponse(
            streaming_content=(elem for elem in gen),
            content_type='text/csv'
        )
        res['Content-Disposition'] = 'attachment; filename="email-{0}.csv"'.format(utils.timestamp_to_readable_string(utils.timestamp_now_ms()).replace('/', '-'))
        return res
