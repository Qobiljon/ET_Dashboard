import json
import datetime
import csv
from json import JSONDecodeError

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
    dj_logout(request=request)
    return redirect(to='login')


@login_required
@require_http_methods(['GET', 'POST'])
def handle_create_or_modify_campaign(request):
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is not None:
        if request.method == 'POST':
            config_json = []
            # first validate the user input JSON configurations
            all_data_sources = et_models.DataSource.all_data_sources_no_details(user_id=None, email=None, use_grpc=False)
            for elem in all_data_sources:
                if elem.name in request.POST:
                    try:
                        json.loads(s=request.POST['config_json_%s' % elem.name])
                    except JSONDecodeError:
                        referer = request.META.get('HTTP_REFERER')
                        if referer:
                            return redirect(to=referer)
                        else:
                            return redirect(to='index')
            for elem in all_data_sources:
                if elem.name in request.POST:
                    grpc_req = et_service_pb2.BindDataSourceRequestMessage(
                        userId=grpc_user_id,
                        email=request.user.email,
                        name=elem.name,
                        iconName=elem.icon_name
                    )
                    grpc_res: et_service_pb2.BindDataSourceResponseMessage = utils.stub.bindDataSource(grpc_req)
                    config_json += [{'name': elem.name, 'data_source_id': grpc_res.dataSourceId, 'icon_name': elem.icon_name, 'config_json': request.POST['config_json_%s' % elem.name]}]
            grpc_req = et_service_pb2.RegisterCampaignRequestMessage(
                userId=grpc_user_id,
                email=request.user.email,
                campaignId=int(request.POST['campaign_id']),
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
                    template_name='campaign_editor_page.html',
                    context={
                        'error': True,
                        'title': 'New campaign',
                        'android': et_models.DataSource.android_sensors,
                        'tizen': et_models.DataSource.tizen_sensors,
                        'others': et_models.DataSource.others
                    }
                )
        elif request.method == 'GET':
            data_source_dict = et_models.DataSource.all_data_sources_no_details(user_id=grpc_user_id, email=request.user.email, map_with_name=True)
            if 'edit' in request.GET and 'campaign_id' in request.GET and str(request.GET['campaign_id']).isdigit() and et_models.Campaign.objects.filter(campaign_id=int(request.GET['campaign_id']), creator_email=request.user.email).exists():
                campaign = et_models.Campaign.objects.get(campaign_id=int(request.GET['campaign_id']), creator_email=request.user.email)
                for config_json in json.loads(s=campaign.config_json):
                    data_source_dict[config_json['name']].selected = True
                    data_source_dict[config_json['name']].name = config_json['name']
                    data_source_dict[config_json['name']].icon_name = config_json['icon_name']
                    data_source_dict[config_json['name']].config_json = config_json['config_json']
                data_source_list = []
                for name in data_source_dict:
                    data_source_list += [data_source_dict[name]]
                data_source_list.sort(key=lambda key: key.name)
                return render(
                    request=request,
                    template_name='campaign_editor_page.html',
                    context={
                        'edit_mode': True,
                        'title': '"%s" Campaign Editor' % campaign.name,
                        'campaign': campaign,
                        'data_sources': data_source_list
                    }
                )
            else:
                data_source_list = []
                for name in data_source_dict:
                    data_source_list += [data_source_dict[name]]
                data_source_list.sort(key=lambda key: key.name)
                return render(
                    request=request,
                    template_name='campaign_editor_page.html',
                    context={
                        'title': 'New campaign',
                        'data_sources': data_source_list,
                    }
                )
        else:
            return redirect(to='index')
    else:
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_delete_campaign(request):
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is not None:
        if 'campaign_id' in request.GET and str(request.GET['campaign_id']).isdigit() and et_models.Campaign.objects.filter(campaign_id=int(request.GET['campaign_id'])).exists():
            campaign_id = int(request.GET['campaign_id'])
            grpc_req = et_service_pb2.DeleteCampaignRequestMessage(
                userId=grpc_user_id,
                email=request.user.email,
                campaignId=campaign_id
            )
            grpc_res: et_service_pb2.DefaultResponseMessage = utils.stub.deleteCampaign(grpc_req)
            if grpc_res.doneSuccessfully:
                et_models.Campaign.objects.get(campaign_id=campaign_id).delete()
            return redirect(to='index')
        else:
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return redirect(to=referer)
            else:
                return redirect(to='index')
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
        trg_participant = et_models.Participant.objects.get(email=request.GET['email'], campaign=campaign)
        data_sources = et_models.DataSource.participants_data_sources_details(campaign=campaign, trg_participant=trg_participant)
        return render(
            request=request,
            template_name='participant_details.html',
            context={
                'title': "%s's data" % trg_participant.full_name,
                'campaign': campaign,
                'participant': trg_participant,
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
                if not data_available:
                    print(from_time)

        res = StreamingHttpResponse(
            streaming_content=(row for row in load_next_100rows(pseudo_buffer=et_models.Echo())),
            content_type='text/csv'
        )
        res['Content-Disposition'] = 'attachment; filename="{0}-{1}.csv"'.format(email, utils.timestamp_to_readable_string(utils.timestamp_now_ms()).replace('/', '-'))
        return res
