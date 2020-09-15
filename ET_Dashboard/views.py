from json import JSONDecodeError
from utils import settings
import datetime
import zipfile
import json
import os

# Django
from django.contrib.auth import logout as dj_logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
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
    channel, stub = utils.get_grpc_channel_stub()
    if request.user.is_authenticated:
        grpc_req = et_service_pb2.LoginDashboard.Request(email=request.user.email, name=request.user.get_full_name(), dashboardKey='ETd@$#b0@rd')
        grpc_res = stub.loginDashboard(grpc_req)
        if grpc_res.success:
            et_models.GrpcUserIds.create_or_update(email=request.user.email, user_id=grpc_res.userId)
            print('%s logged in' % request.user.email)
            channel.close()
            return redirect(to='campaigns-list')
        else:
            dj_logout(request=request)
    channel.close()
    return render(
        request=request,
        template_name='page_authentication.html',
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
    channel, stub = utils.get_grpc_channel_stub()
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is not None:
        load_unread_notifications(grpc_user_id=grpc_user_id, email=request.user.email)
        grpc_req = et_service_pb2.RetrieveCampaigns.Request(userId=grpc_user_id, email=request.user.email, myCampaignsOnly=True)
        grpc_res = stub.retrieveCampaigns(grpc_req)
        if grpc_res.success:
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
        channel.close()
        return render(
            request=request,
            template_name='page_campaigns.html',
            context={
                'title': "%s's campaigns" % request.user.get_full_name(),
                'campaigns': campaigns,
                'notifications': notifications
            }
        )
    else:
        channel.close()
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_participants_list(request):
    channel, stub = utils.get_grpc_channel_stub()
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
        grpc_req = et_service_pb2.RetrieveParticipants.Request(
            userId=grpc_user_id,
            email=request.user.email,
            campaignId=campaign.campaign_id
        )
        grpc_res = stub.retrieveParticipants(grpc_req)
        if grpc_res.success:
            success = len(grpc_res.name) == 0
            for grpc_id, name, email in zip(grpc_res.userId, grpc_res.name, grpc_res.email):
                sub_grpc_req = et_service_pb2.RetrieveParticipantStats.Request(
                    userId=grpc_user_id,
                    email=request.user.email,
                    targetEmail=email,
                    targetCampaignId=campaign.campaign_id
                )
                sub_grpc_res = stub.retrieveParticipantStats(sub_grpc_req)
                success |= sub_grpc_res.success
                if sub_grpc_res.success:
                    et_models.Participant.create_or_update(
                        grpc_id=grpc_id,
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
                channel.close()
                return render(
                    request=request,
                    template_name='page_campaign_participants.html',
                    context={
                        'title': "%s's participants" % campaign.name,
                        'campaign': campaign,
                        'participants': et_models.Participant.objects.filter(campaign=campaign).order_by('full_name')
                    }
                )
        channel.close()
        return redirect(to='campaigns-list')


@login_required
@require_http_methods(['GET'])
def handle_participants_data_list(request):
    channel, stub = utils.get_grpc_channel_stub()
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
        grpc_req = et_service_pb2.RetrieveParticipantStats.Request(
            userId=grpc_user_id,
            email=request.user.email,
            targetEmail=target_participant.email,
            targetCampaignId=target_campaign.campaign_id
        )
        grpc_res = stub.retrieveParticipantStats(grpc_req)
        if grpc_res.success:
            et_models.Participant.create_or_update(
                grpc_id=target_participant.grpc_id,
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
        channel.close()
        return render(
            request=request,
            template_name='page_participant_data_sources_stats.html',
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
    channel, stub = utils.get_grpc_channel_stub()
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is None:
        return redirect(to='login')
    target_campaign = None
    target_participant = None
    if 'campaign_id' in request.GET and str(request.GET['campaign_id']).isdigit() and et_models.Campaign.objects.filter(campaign_id=request.GET['campaign_id'], requester_email=request.user.email).exists():
        target_campaign = et_models.Campaign.objects.get(campaign_id=request.GET['campaign_id'], requester_email=request.user.email)
    if target_campaign is not None and 'email' in request.GET and et_models.Participant.objects.filter(email=request.GET['email'], campaign=target_campaign).exists():
        target_participant = et_models.Participant.objects.get(email=request.GET['email'], campaign=target_campaign)
    if target_campaign is None or target_participant is None or 'data_source_id' not in request.GET or not str(request.GET['data_source_id']).isdigit() or 'from_id' not in request.GET or not str(request.GET['from_id']).replace('-', '').isdigit():
        return redirect(to='campaigns-list')
    else:
        from_record_id = int(request.GET['from_id'])
        data_source_id = int(request.GET['data_source_id'])
        grpc_req = et_service_pb2.RetrieveKNextDataRecords.Request(
            userId=grpc_user_id,
            email=request.user.email,
            targetEmail=target_participant.email,
            targetCampaignId=target_campaign.campaign_id,
            targetDataSourceId=data_source_id,
            fromRecordId=from_record_id,
            k=100,
        )
        grpc_res = stub.retrieveKNextDataRecords(grpc_req)
        if grpc_res.success:
            records = []
            for record_id, timestamp, value in zip(grpc_res.id, grpc_res.timestamp, grpc_res.value):
                records += [et_models.Record(record_id=record_id, timestamp_ms=timestamp, value=value)]
                from_record_id = max(from_record_id, record_id)
            data_source_name = None
            for data_source in json.loads(s=et_models.Campaign.objects.get(requester_email=request.user.email, campaign_id=target_campaign.campaign_id).config_json):
                if data_source['data_source_id'] == data_source_id:
                    data_source_name = data_source['name']
                    break
            channel.close()
            return render(
                request=request,
                template_name='page_raw_data_view.html',
                context={
                    'title': data_source_name,
                    'records': records,
                    'from_id': from_record_id
                }
            )
        else:
            channel.close()
            return redirect(to='campaigns-list')


@login_required
@require_http_methods(['GET', 'POST'])
def handle_campaign_editor(request):
    channel, stub = utils.get_grpc_channel_stub()
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
                        channel.close()
                        return redirect(to=referer)
                    else:
                        channel.close()
                        return redirect(to='campaigns-list')
            for elem in data_sources:
                grpc_req = et_service_pb2.BindDataSource.Request(
                    userId=grpc_user_id,
                    email=request.user.email,
                    name=elem.name,
                    iconName=elem.icon_name
                )
                grpc_res = stub.bindDataSource(grpc_req)
                config_json += [{'name': elem.name, 'data_source_id': grpc_res.dataSourceId, 'icon_name': elem.icon_name, 'config_json': elem.config_json}]
            grpc_req = et_service_pb2.RegisterCampaign.Request(
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
            grpc_res = stub.registerCampaign(grpc_req)
            if grpc_res.success:
                channel.close()
                return redirect(to='campaigns-list')
            else:
                channel.close()
                return render(
                    request=request,
                    template_name='page_campaign_editor.html',
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
                    template_name='page_campaign_editor.html',
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
                channel.close()
                return render(
                    request=request,
                    template_name='page_campaign_editor.html',
                    context={
                        'title': 'New campaign',
                        'data_sources': data_source_list,
                    }
                )
        else:
            channel.close()
            return redirect(to='campaigns-list')
    else:
        channel.close()
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_delete_campaign_api(request):
    channel, stub = utils.get_grpc_channel_stub()
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is not None:
        if 'campaign_id' in request.GET and str(request.GET['campaign_id']).isdigit() and et_models.Campaign.objects.filter(campaign_id=int(request.GET['campaign_id'])).exists():
            campaign_id = int(request.GET['campaign_id'])
            grpc_req = et_service_pb2.DeleteCampaign.Request(
                userId=grpc_user_id,
                email=request.user.email,
                campaignId=campaign_id
            )
            grpc_res = stub.deleteCampaign(grpc_req)
            if grpc_res.success:
                et_models.Campaign.objects.get(campaign_id=campaign_id).delete()
            channel.close()
            return redirect(to='campaigns-list')
        else:
            referer = request.META.get('HTTP_REFERER')
            if referer:
                channel.close()
                return redirect(to=referer)
            else:
                channel.close()
                return redirect(to='campaigns-list')
    else:
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_dataset_info(request):
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
        return render(
            request=request,
            template_name='page_dataset_configs.html',
            context={
                'data_sources': data_sources,
                'participants': et_models.Participant.objects.filter(campaign=campaign).order_by('full_name')
            }
        )


@login_required
@require_http_methods(['GET'])
def handle_download_data_api(request):
    channel, stub = utils.get_grpc_channel_stub()
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is None:
        channel.close()
        return redirect(to='login')
    elif 'campaign_id' not in request.GET or not str(request.GET['campaign_id']).isdigit() or not et_models.Campaign.objects.filter(campaign_id=request.GET['campaign_id'], requester_email=request.user.email).exists() or 'email' not in request.GET:
        channel.close()
        return redirect(to='campaigns-list')
    else:
        campaign_id = int(request.GET['campaign_id'])
        email = request.user.email
        target_email = request.GET['email']

        grpc_req = et_service_pb2.DownloadDumpfile.Request(
            userId=grpc_user_id,
            email=email,
            campaignId=campaign_id,
            targetEmail=target_email
        )
        grpc_res = stub.downloadDumpfile(grpc_req)
        if grpc_res.success:
            now = datetime.datetime.now()
            file_name = f'et data {target_email} {now.month}-{now.day}-{now.year} {now.hour}-{now.minute}.bin'
            res = HttpResponse(grpc_res.dump, content_type='application/x-binary')
            res['Content-Disposition'] = f'attachment; filename={file_name}'
        else:
            res = redirect(to='campaigns-list')
        channel.close()
        return res


@login_required
@require_http_methods(['GET'])
def handle_download_dataset_api(request):
    channel, stub = utils.get_grpc_channel_stub()
    # return render(request=request, template_name='page_coming_soon.html')
    grpc_user_id = et_models.GrpcUserIds.get_id(email=request.user.email)
    if grpc_user_id is None:
        channel.close()
        return redirect(to='login')
    elif 'campaign_id' not in request.GET or not str(request.GET['campaign_id']).isdigit() or not et_models.Campaign.objects.filter(campaign_id=request.GET['campaign_id'], requester_email=request.user.email).exists():
        channel.close()
        return redirect(to='campaigns-list')
    else:
        campaign_id = int(request.GET['campaign_id'])
        email = request.user.email

        grpc_req = et_service_pb2.RetrieveParticipants.Request(
            userId=grpc_user_id,
            email=email,
            campaignId=campaign_id
        )
        grpc_res = stub.retrieveParticipants(grpc_req)
        if grpc_res.success:
            now = datetime.datetime.now()
            file_name = f'et data {now.month}-{now.day}-{now.year} {now.hour}-{now.minute}.zip'
            file_path = utils.get_download_file_path(file_name=file_name)
            fp = zipfile.ZipFile(file_path, 'w', zipfile.ZIP_STORED)
            with open(os.path.join(settings.STATIC_DIR, 'restoring_postgres_data.txt'), 'r') as r:
                fp.writestr('!README.txt', r.read())
            fp.writestr('!info.txt', f'campaign_id : {campaign_id}')

            for email in grpc_res.email:
                sub_grpc_req = et_service_pb2.DownloadDumpfile.Request(
                    userId=grpc_user_id,
                    email=email,
                    campaignId=campaign_id,
                    targetEmail=email
                )
                sub_grpc_res = stub.downloadDumpfile(sub_grpc_req)
                if sub_grpc_res.success:
                    fp.writestr(f'{email}.bin', sub_grpc_res.dump)
            fp.close()
            with open(file_path, 'rb') as r:
                content = r.read()
            os.remove(file_path)

            res = HttpResponse(content, content_type='application/zip')
            res['Content-Disposition'] = f'attachment; filename={file_name}'
        else:
            res = redirect(to='campaigns-list')
        channel.close()
        return res


@login_required
@require_http_methods(['GET'])
def handle_notifications_list(request):
    return None


def load_unread_notifications(grpc_user_id, email):
    channel, stub = utils.get_grpc_channel_stub()
    grpc_req = et_service_pb2.RetrieveUnreadNotifications.Request(userId=grpc_user_id, email=email)
    grpc_res = stub.retrieveUnreadNotifications(grpc_req)
    if grpc_res.success:
        for notification_id, campaign_id, timestamp, subject, content in zip(grpc_res.notificationId, grpc_res.campaignId, grpc_res.timestamp, grpc_res.subject, grpc_res.content):
            et_models.Notifications.objects.create(notification_id=notification_id, campaign_id=campaign_id, timestamp=timestamp, subject=subject, content=content).save()
