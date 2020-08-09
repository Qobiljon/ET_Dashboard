import json
import datetime
import csv
from json import JSONDecodeError

# Django
from django.contrib.auth import logout as dj_logout
from django.contrib.auth.decorators import login_required
from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

# gRPC
from et_grpcs import et_service_pb2

# EasyTrack
from ET_Dashboard import models as et_models
from utils import utils


def handle_google_verification(request):
    return render(request=request, template_name='google43e44b3701ba10c8.html')


@require_http_methods(['GET', 'POST'])
def handle_login_api(request):
    if request.user.is_authenticated:
        grpc_req = et_service_pb2.DashboardLoginWithEmailRequestMessage(email=request.user.email, name=request.user.get_full_name(), dashboardKey='ETd@$#b0@rd')
        grpc_res = utils.stub.dashboardLoginWithEmail(grpc_req)
        if grpc_res.doneSuccessfully:
            et_models.GrpcUserIds.create_or_update(email=request.user.email, user_id=grpc_res.userId)
            print('%s logged in' % request.user.email)
            return redirect(to='campaigns-list')
        else:
            dj_logout(request=request)
    return render(
        request=request,
        template_name='1. authentication.html',
        context={'title': 'Authentication'}
    )


@login_required
@require_http_methods(['GET', 'POST'])
def handle_logout_api(request):
    dj_logout(request=request)
    return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_campaigns_list(request):
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is not None:
        load_unread_notifications(grpc_user_id=grpc_user_id, email=request.user.email)
        grpc_req = et_service_pb2.RetrieveCampaignsRequestMessage(userId=grpc_user_id, email=request.user.email, myCampaignsOnly=True)
        grpc_res = utils.stub.retrieveCampaigns(grpc_req)
        if grpc_res.doneSuccessfully:
            for campaign_id, name, notes, start_timestamp, end_timestamp, remove_inactive_users_timeout, creator_email, config_json, participant_count in zip(grpc_res.campaignId, grpc_res.name, grpc_res.notes, grpc_res.startTimestamp, grpc_res.endTimestamp, grpc_res.removeInactiveUsersTimeout, grpc_res.creatorEmail, grpc_res.configJson, grpc_res.participantCount):
                et_models.Campaign.create_or_update(
                    campaign_id=campaign_id,
                    requester_email=request.user.email,
                    name=name,
                    notes=notes,
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp,
                    remove_inactive_users_timeout=remove_inactive_users_timeout,
                    creator_email=creator_email,
                    config_json=config_json,
                    participant_count=participant_count
                )
            print('%s opened the main page' % request.user.email)
        campaigns = et_models.Campaign.objects.filter(requester_email=request.user.email).order_by('name')
        notifications = {}
        for campaign in campaigns:
            notifications[campaign.campaign_id] = et_models.Notifications.objects.filter(campaign_id=campaign.campaign_id).order_by('-timestamp')
        return render(
            request=request,
            template_name='2. campaigns_list.html',
            context={
                'title': "%s's campaigns" % request.user.get_full_name(),
                'campaigns': campaigns,
                'notifications': notifications
            }
        )
    else:
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_participants_list(request):
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is None:
        return redirect(to='login')
    campaign = None
    if 'id' in request.GET and str(request.GET['id']).isdigit() and et_models.Campaign.objects.filter(campaign_id=request.GET['id'], requester_email=request.user.email).exists():
        campaign = et_models.Campaign.objects.get(campaign_id=int(request.GET['id']), requester_email=request.user.email)
    if campaign is None:
        return redirect(to='campaigns-list')
    else:
        # campaign dashboard page
        grpc_req = et_service_pb2.RetrieveParticipantsRequestMessage(
            userId=grpc_user_id,
            email=request.user.email,
            campaignId=campaign.campaign_id
        )
        grpc_res = utils.stub.retrieveParticipants(grpc_req)
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
                    sub_grpc_res = utils.stub.retrieveParticipantStatistics(sub_grpc_req)
                    success |= sub_grpc_res.doneSuccessfully
                    if sub_grpc_res.doneSuccessfully:
                        et_models.Participant.create_or_update(
                            email=email,
                            campaign=campaign,
                            full_name=name,
                            day_no=utils.calculate_day_number(join_timestamp=sub_grpc_res.campaignJoinTimestamp),
                            amount_of_data=sub_grpc_res.amountOfSubmittedDataSamples,
                            last_heartbeat_time=utils.timestamp_to_readable_string(sub_grpc_res.lastHeartbeatTimestamp),
                            last_sync_time=utils.timestamp_to_readable_string(sub_grpc_res.lastSyncTimestamp),
                            data_source_ids=sub_grpc_res.dataSourceId,
                            per_data_source_amount_of_data=sub_grpc_res.perDataSourceAmountOfData,
                            per_data_source_last_sync_time=[utils.timestamp_to_readable_string(timestamp_ms=timestamp_ms) for timestamp_ms in sub_grpc_res.perDataSourceLastSyncTimestamp]
                        )
                if success:
                    return render(
                        request=request,
                        template_name='3. participants_list.html',
                        context={
                            'title': "%s's participants" % campaign.name,
                            'campaign': campaign,
                            'participants': et_models.Participant.objects.filter(campaign=campaign).order_by('full_name')
                        }
                    )
        return redirect(to='campaigns-list')


@login_required
@require_http_methods(['GET'])
def handle_participants_data_list(request):
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is None:
        return redirect(to='login')
    target_campaign = None
    target_participant = None
    if 'campaign_id' in request.GET and str(request.GET['campaign_id']).isdigit() and et_models.Campaign.objects.filter(campaign_id=request.GET['campaign_id'], requester_email=request.user.email).exists():
        target_campaign = et_models.Campaign.objects.get(campaign_id=request.GET['campaign_id'], requester_email=request.user.email)
    if target_campaign is not None and 'email' in request.GET and et_models.Participant.objects.filter(email=request.GET['email'], campaign__campaign_id=request.GET['campaign_id']).exists():
        target_participant = et_models.Participant.objects.get(email=request.GET['email'], campaign=target_campaign)
    if target_campaign is None or target_participant is None:
        return redirect(to='campaigns-list')
    else:
        grpc_req = et_service_pb2.RetrieveParticipantStatisticsRequestMessage(
            userId=grpc_user_id,
            email=request.user.email,
            targetEmail=target_participant.email,
            targetCampaignId=target_campaign.campaign_id
        )
        grpc_res = utils.stub.retrieveParticipantStatistics(grpc_req)
        if grpc_res.doneSuccessfully:
            et_models.Participant.create_or_update(
                email=target_participant.email,
                campaign=target_campaign,
                full_name=target_participant.full_name,
                day_no=utils.calculate_day_number(join_timestamp=grpc_res.campaignJoinTimestamp),
                amount_of_data=grpc_res.amountOfSubmittedDataSamples,
                last_heartbeat_time=utils.timestamp_to_readable_string(grpc_res.lastHeartbeatTimestamp),
                last_sync_time=utils.timestamp_to_readable_string(grpc_res.lastSyncTimestamp),
                data_source_ids=grpc_res.dataSourceId,
                per_data_source_amount_of_data=grpc_res.perDataSourceAmountOfData,
                per_data_source_last_sync_time=[utils.timestamp_to_readable_string(timestamp_ms=timestamp_ms) for timestamp_ms in grpc_res.perDataSourceLastSyncTimestamp]
            )
        # participant's data list (data sources)
        target_campaign = et_models.Campaign.objects.get(campaign_id=request.GET['campaign_id'], requester_email=request.user.email)
        trg_participant = et_models.Participant.objects.get(email=request.GET['email'], campaign=target_campaign)
        return render(
            request=request,
            template_name='4. participants_data_list.html',
            context={
                'title': "%s's data" % trg_participant.full_name,
                'campaign': target_campaign,
                'participant': trg_participant,
                'data_sources': et_models.DataSource.participants_data_sources_details(campaign=target_campaign, trg_participant=trg_participant)
            }
        )


@login_required
@require_http_methods(['GET'])
def handle_raw_samples_list(request):
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is None:
        return redirect(to='login')
    target_campaign = None
    target_participant = None
    if 'campaign_id' in request.GET and str(request.GET['campaign_id']).isdigit() and et_models.Campaign.objects.filter(campaign_id=request.GET['campaign_id'], requester_email=request.user.email).exists():
        target_campaign = et_models.Campaign.objects.get(campaign_id=request.GET['campaign_id'], requester_email=request.user.email)
    if target_campaign is not None and 'email' in request.GET and et_models.Participant.objects.filter(email=request.GET['email'], campaign=target_campaign).exists():
        target_participant = et_models.Participant.objects.get(email=request.GET['email'], campaign=target_campaign)
    if target_campaign is None or target_participant is None or 'data_source_id' not in request.GET or not str(request.GET['data_source_id']).isdigit() or 'from_time' not in request.GET \
            or not (len(request.GET['from_time']) > 1 and str(request.GET['from_time'][1:]).isdigit()):
        return redirect(to='campaigns-list')
    else:
        from_time = int(request.GET['from_time'])
        data_source_id = int(request.GET['data_source_id'])
        grpc_req = et_service_pb2.Retrieve100DataRecordsRequestMessage(
            userId=grpc_user_id,
            email=request.user.email,
            targetEmail=target_participant.email,
            targetCampaignId=target_campaign.campaign_id,
            targetDataSourceId=data_source_id,
            fromTimestamp=from_time
        )
        grpc_res = utils.stub.retrieve100DataRecords(grpc_req)
        if grpc_res.doneSuccessfully:
            records = []
            for timestamp, value in zip(grpc_res.timestamp, grpc_res.value):
                records += [et_models.Record(timestamp_ms=timestamp, value=value)]
                from_time = timestamp
            data_source_name = None
            for data_source in json.loads(s=et_models.Campaign.objects.get(requester_email=request.user.email, campaign_id=target_campaign.campaign_id).config_json):
                if data_source['data_source_id'] == data_source_id:
                    data_source_name = data_source['name']
                    break
            return render(
                request=request,
                template_name='5. raw_samples_list.html',
                context={
                    'title': data_source_name,
                    'records': records,
                    'from_time': from_time
                }
            )
        else:
            return redirect(to='campaigns-list')


@login_required
@require_http_methods(['GET', 'POST'])
def handle_campaign_editor(request):
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is not None:
        if request.method == 'POST':
            config_json = []
            # first validate the user input JSON configurations
            data_sources = []
            for elem in request.POST:
                if str(elem).startswith("config_json_"):
                    _name = str(elem)[12:]
                    _icon_name = request.POST['icon_name_%s' % _name]
                    _config_json = request.POST['config_json_%s' % _name]
                    data_sources += [et_models.DataSource(
                        data_source_id=-1,
                        name=_name,
                        icon_name=_icon_name,
                        amount_of_data=-1,
                        config_json=_config_json,
                        last_sync_time=None
                    )]
            for elem in data_sources:
                try:
                    json.loads(s=elem.config_json)
                except JSONDecodeError:
                    referer = request.META.get('HTTP_REFERER')
                    if referer:
                        return redirect(to=referer)
                    else:
                        return redirect(to='campaigns-list')
            for elem in data_sources:
                grpc_req = et_service_pb2.BindDataSourceRequestMessage(
                    userId=grpc_user_id,
                    email=request.user.email,
                    name=elem.name,
                    iconName=elem.icon_name
                )
                grpc_res = utils.stub.bindDataSource(grpc_req)
                config_json += [{'name': elem.name, 'data_source_id': grpc_res.dataSourceId, 'icon_name': elem.icon_name, 'config_json': elem.config_json}]
            grpc_req = et_service_pb2.RegisterCampaignRequestMessage(
                userId=grpc_user_id,
                email=request.user.email,
                campaignId=int(request.POST['campaign_id']),
                name=request.POST['name'],
                notes=request.POST['notes'],
                startTimestamp=utils.datetime_to_timestamp_ms(value=datetime.datetime.strptime(request.POST['startTime'], "%Y-%m-%dT%H:%M")),
                endTimestamp=utils.datetime_to_timestamp_ms(value=datetime.datetime.strptime(request.POST['endTime'], "%Y-%m-%dT%H:%M")),
                removeInactiveUsersTimeout=int(request.POST['remove_inactive_users_timeout']) if int(request.POST['remove_inactive_users_timeout']) > 0 else -1,
                configJson=json.dumps(obj=config_json)
            )
            grpc_res = utils.stub.registerCampaign(grpc_req)
            if grpc_res.doneSuccessfully:
                return redirect(to='campaigns-list')
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
            return redirect(to='campaigns-list')
    else:
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_delete_campaign_api(request):
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is not None:
        if 'campaign_id' in request.GET and str(request.GET['campaign_id']).isdigit() and et_models.Campaign.objects.filter(campaign_id=int(request.GET['campaign_id'])).exists():
            campaign_id = int(request.GET['campaign_id'])
            grpc_req = et_service_pb2.DeleteCampaignRequestMessage(
                userId=grpc_user_id,
                email=request.user.email,
                campaignId=campaign_id
            )
            grpc_res = utils.stub.deleteCampaign(grpc_req)
            if grpc_res.doneSuccessfully:
                et_models.Campaign.objects.get(campaign_id=campaign_id).delete()
            return redirect(to='campaigns-list')
        else:
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return redirect(to=referer)
            else:
                return redirect(to='campaigns-list')
    else:
        return redirect(to='login')


@login_required
def handle_download_data_api(request):
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is None:
        return redirect(to='login')
    elif 'campaign_id' not in request.GET or not str(request.GET['campaign_id']).isdigit() or not et_models.Campaign.objects.filter(campaign_id=request.GET['campaign_id'], requester_email=request.user.email).exists() or \
            'email' not in request.GET or not et_models.Participant.objects.filter(email=request.GET['email'], campaign_id=request.GET['campaign_id']).exists() or \
            'data_source_id' not in request.GET or not str(request.GET['data_source_id']).isdigit():
        return redirect(to='campaigns-list')
    else:
        campaign_id = int(request.GET['campaign_id'])
        email = request.user.email
        data_source_id = int(request.GET['data_source_id'])

        def load_next_100rows(pseudo_buffer):
            writer = csv.writer(pseudo_buffer)
            from_time = -999999999
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
                grpc_res = utils.stub.retrieve100DataRecords(grpc_req)
                if grpc_res.doneSuccessfully:
                    for timestamp, value in zip(grpc_res.timestamp, grpc_res.value):
                        from_time = timestamp
                        yield writer.writerow([str(timestamp), value])
                data_available = grpc_res.doneSuccessfully and grpc_res.moreDataAvailable

        res = StreamingHttpResponse(
            streaming_content=(row for row in load_next_100rows(pseudo_buffer=et_models.Echo())),
            content_type='text/csv'
        )
        data_source_name = None
        for data_source in json.loads(s=et_models.Campaign.objects.get(campaign_id=campaign_id).config_json):
            if data_source['data_source_id'] == data_source_id:
                data_source_name = data_source['name']
                break
        res['Content-Disposition'] = 'attachment; filename="{0}-{1}-{2}.csv"'.format(
            request.GET['email'],
            data_source_name.replace('/', '-'),
            utils.timestamp_to_readable_string(utils.timestamp_now_ms()).replace('/', '-').replace(' ', '_')
        )
        return res


@login_required
@require_http_methods(['GET'])
def handle_download_campaign_api(request):
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is None:
        return redirect(to='login')
    elif 'campaign_id' not in request.GET or not str(request.GET['campaign_id']).isdigit() or not et_models.Campaign.objects.filter(campaign_id=request.GET['campaign_id'], requester_email=request.user.email).exists():
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(to=referer)
        else:
            return redirect(to='campaigns-list')
    else:
        campaign = et_models.Campaign.objects.get(campaign_id=int(request.GET['campaign_id']), requester_email=request.user.email)
        data_sources = json.loads(s=campaign.config_json)
        res = {}
        for data_source in data_sources:
            res[data_source['name']] = data_source['data_source_id']
        return JsonResponse(data=res)


@login_required
@require_http_methods(['GET'])
def handle_notifications_list(request):
    return None


def load_unread_notifications(grpc_user_id, email):
    grpc_req = et_service_pb2.RetrieveUnreadNotificationsRequestMessage(userId=grpc_user_id, email=email)
    grpc_res = utils.stub.retrieveUnreadNotifications(grpc_req)
    if grpc_res.doneSuccessfully:
        for notification_id, campaign_id, timestamp, subject, content in zip(grpc_res.notificationId, grpc_res.campaignId, grpc_res.timestamp, grpc_res.subject, grpc_res.content):
            et_models.Notifications.objects.create(notification_id=notification_id, campaign_id=campaign_id, timestamp=timestamp, subject=subject, content=content).save()
