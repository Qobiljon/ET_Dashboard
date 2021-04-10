import plotly.graph_objects as go
from json import JSONDecodeError
from tools import settings
import datetime
import zipfile
import plotly
import json
import os
import re

# Django
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as dj_logout
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import JsonResponse

# EasyTrack
from ET_Dashboard.models import EnhancedDataSource
from tools import db_mgr as db
from tools import utils


def handle_google_verification(request):
    return render(request=request, template_name='google43e44b3701ba10c8.html')


@require_http_methods(['GET', 'POST'])
def handle_login_api(request):
    if request.user.is_authenticated:
        db_user = db.get_user(email=request.user.email)
        if db_user is None:
            print('new user : ', end='')
            session_key = utils.md5(value=f'{request.user.email}{utils.now_us()}')
            db_user = db.create_user(name=request.user.get_full_name(), email=request.user.email, session_key=session_key)
            if db_user is None:
                dj_logout(request=request)
            else:
                return redirect(to='campaigns-list')
        else:
            return redirect(to='campaigns-list')
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
    db_user = db.get_user(email=request.user.email)
    if db_user is not None:
        my_campaigns = []
        for db_campaign in db.get_campaigns(db_creator_user=db_user):
            my_campaigns += [{
                'id': db_campaign.id,
                'name': db_campaign.name,
                'notes': db_campaign.notes,
                'participants': db.get_campaign_participants_count(db_campaign=db_campaign)
            }]
        print('%s opened the main page' % request.user.email)
        my_campaigns.sort(key=lambda x: x['id'])
        return render(
            request=request,
            template_name='page_campaigns.html',
            context={
                'title': "%s's campaigns" % request.user.get_full_name(),
                'my_campaigns': my_campaigns,
            }
        )
    else:
        dj_logout(request=request)
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_participants_list(request):
    db_user = db.get_user(email=request.user.email)
    if db_user is not None:
        if 'id' in request.GET and str(request.GET['id']).isdigit():
            db_campaign = db.get_campaign(campaign_id=int(request.GET['id']), db_creator_user=db_user)
            if db_campaign is not None:
                # campaign dashboard page
                participants = []
                for participant in db.get_campaign_participants(db_campaign=db_campaign):
                    participants += [{
                        'id': participant.id,
                        'name': participant.name,
                        'email': participant.email,
                        'day_no': utils.calculate_day_number(join_timestamp=db.get_participant_join_timestamp(db_user=participant, db_campaign=db_campaign)),
                        'amount_of_data': db.get_participants_amount_of_data(db_user=participant, db_campaign=db_campaign),
                        'last_heartbeat_time': utils.timestamp_to_readable_string(timestamp_ms=db.get_participant_heartbeat_timestamp(db_user=participant, db_campaign=db_campaign)),
                        'last_sync_time': utils.timestamp_to_readable_string(timestamp_ms=db.get_participant_last_sync_timestamp(db_user=participant, db_campaign=db_campaign)),
                    }]
                participants.sort(key=lambda x: x['id'])
                return render(
                    request=request,
                    template_name='page_campaign_participants.html',
                    context={
                        'title': "%s's participants" % db_campaign.name,
                        'campaign': db_campaign,
                        'participants': participants
                    }
                )
            else:
                return redirect(to='campaigns-list')
        else:
            return redirect(to='campaigns-list')
    else:
        dj_logout(request=request)
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_participants_data_list(request):
    db_user = db.get_user(email=request.user.email)
    if db_user is not None:
        if 'campaign_id' in request.GET and str(request.GET['campaign_id']).isdigit():
            db_campaign = db.get_campaign(campaign_id=request.GET['campaign_id'], db_creator_user=db_user)
            if db_campaign is not None:
                campaign_data_source_configs = {}
                for data_source in json.loads(s=db_campaign.configJson):
                    campaign_data_source_configs[data_source['data_source_id']] = data_source['config_json']
                if 'participant_id' in request.GET and utils.is_numeric(request.GET['participant_id']):
                    db_participant_user = db.get_user(user_id=request.GET['participant_id'])
                    if db_participant_user is not None and db.user_is_bound_to_campaign(db_user=db_participant_user, db_campaign=db_campaign):
                        data_sources = []
                        for db_data_source, amount_of_data, last_sync_time in db.get_participants_per_data_source_stats(db_user=db_participant_user, db_campaign=db_campaign):
                            data_sources += [{
                                'id': db_data_source.id,
                                'name': db_data_source.name,
                                'icon_name': db_data_source.iconName,
                                'config_json': campaign_data_source_configs[db_data_source.id],
                                'amount_of_data': amount_of_data,
                                'last_sync_time': utils.timestamp_to_readable_string(timestamp_ms=last_sync_time)
                            }]
                        data_sources.sort(key=lambda x: x['name'])
                        return render(
                            request=request,
                            template_name='page_participant_data_sources_stats.html',
                            context={
                                'title': f'Data submitted by {db_participant_user.name}, {db_participant_user.email} (ID = {db_participant_user.id})',
                                'campaign': db_campaign,
                                'participant': db_participant_user,
                                'data_sources': data_sources
                            }
                        )
                    else:
                        return redirect(to='campaigns-list')
                else:
                    return redirect(to='campaigns-list')
            else:
                return redirect(to='campaigns-list')
        else:
            return redirect(to='campaigns-list')
    else:
        dj_logout(request=request)
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_raw_samples_list(request):
    db_user = db.get_user(email=request.user.email)
    if db_user is not None:
        if 'campaign_id' in request.GET and str(request.GET['campaign_id']).isdigit():
            db_campaign = db.get_campaign(campaign_id=request.GET['campaign_id'], db_creator_user=db_user)
            if db_campaign is not None:
                if 'email' in request.GET:
                    db_participant_user = db.get_user(email=request.GET['email'])
                    if db_participant_user is not None and db.user_is_bound_to_campaign(db_user=db_participant_user, db_campaign=db_campaign):
                        if 'from_timestamp' in request.GET and 'data_source_id' in request.GET and utils.is_numeric(request.GET['from_timestamp']) and utils.is_numeric(request.GET['data_source_id']):
                            from_timestamp = int(request.GET['from_timestamp'])
                            db_data_source = db.get_data_source(data_source_id=int(request.GET['data_source_id']))
                            if db_data_source is not None:
                                records = []
                                for row, record in enumerate(db.get_filtered_data_records(db_user=db_participant_user, db_campaign=db_campaign, db_data_source=db_data_source, from_timestamp=from_timestamp)):
                                    value_len = len(record.value)
                                    if value_len > 5 * 1024:  # 5KB (e.g., binary files)
                                        value = f'[ {value_len:,} byte data record ]'
                                    else:
                                        try:
                                            value = str(record.value, encoding='utf-8')
                                        except UnicodeDecodeError:
                                            value = f'[ {value_len:,} byte data record ]'
                                    records += [{
                                        'row': row + 1,
                                        'timestamp': utils.timestamp_to_readable_string(timestamp_ms=record.timestamp),
                                        'value': value
                                    }]
                                    from_timestamp = record.timestamp
                                return render(
                                    request=request,
                                    template_name='page_raw_data_view.html',
                                    context={
                                        'title': db_data_source.name,
                                        'records': records,
                                        'from_timestamp': from_timestamp
                                    }
                                )
                            else:
                                return redirect(to='campaigns-list')
                        else:
                            return redirect(to='campaigns-list')
                    else:
                        return redirect(to='campaigns-list')
                else:
                    return redirect(to='campaigns-list')
            else:
                return redirect(to='campaigns-list')
        else:
            return redirect(to='campaigns-list')
    else:
        dj_logout(request=request)
        return redirect(to='login')


@login_required
@require_http_methods(['GET', 'POST'])
def handle_campaign_editor(request):
    db_user = db.get_user(email=request.user.email)
    if db_user is not None:
        if request.method == 'GET':
            # request to open the campaign editor
            db_data_sources = db.get_all_data_sources()
            if 'edit' in request.GET and 'campaign_id' in request.GET and str(request.GET['campaign_id']).isdigit():
                # edit an existing campaign
                db_campaign = db.get_campaign(campaign_id=int(request.GET['campaign_id']), db_creator_user=db_user)
                if db_campaign is not None:
                    campaign_db_data_sources = []
                    campaign_data_source_configs = {}
                    for campaign_data_source in json.loads(s=db_campaign.configJson):
                        db_data_source = db.get_data_source(data_source_id=campaign_data_source['data_source_id'])
                        campaign_db_data_sources += [db_data_source]
                        campaign_data_source_configs[db_data_source.id] = campaign_data_source['config_json']
                    campaign_data_sources = []
                    for db_data_source in db_data_sources:
                        selected = db_data_source in campaign_db_data_sources
                        campaign_data_sources += [{
                            'name': db_data_source.name,
                            'icon_name': db_data_source.iconName,
                            'selected': selected,
                            'config_json': campaign_data_source_configs[db_data_source.id] if selected else None
                        }]
                    campaign_data_sources.sort(key=lambda key: key['name'])
                    return render(
                        request=request,
                        template_name='page_campaign_editor.html',
                        context={
                            'edit_mode': True,
                            'title': '"%s" Campaign Editor' % db_campaign.name,
                            'campaign': db_campaign,
                            'campaign_start_time': utils.timestamp_to_web_string(timestamp_ms=db_campaign['start_timestamp']),
                            'campaign_end_time': utils.timestamp_to_web_string(timestamp_ms=db_campaign['end_timestamp']),
                            'data_sources': campaign_data_sources
                        }
                    )
                else:
                    return redirect(to='campaigns-list')
            else:
                # edit for a new campaign
                campaign_data_sources = []
                for db_data_source in db_data_sources:
                    campaign_data_sources += [{
                        'name': db_data_source.name,
                        'icon_name': db_data_source.iconName
                    }]
                campaign_data_sources.sort(key=lambda key: key['name'])
                return render(
                    request=request,
                    template_name='page_campaign_editor.html',
                    context={
                        'title': 'New campaign',
                        'data_sources': campaign_data_sources,
                    }
                )
        elif request.method == 'POST':
            def prepare_campaign_params():
                def is_date_time(string):
                    return re.search(pattern=r'^\d{4}-\d{1,2}-\d{1,2}T\d{1,2}:\d{1,2}$', string=string) is not None

                def get_campaign_data_sources_as_list():
                    # parse data sources from POST request
                    _campaign_data_sources = []
                    for _data_source in request.POST:
                        if str(_data_source).startswith("config_json_"):
                            _data_source_name = str(_data_source)[12:]
                            if 'icon_name_%s' % _data_source_name in request.POST and 'config_json_%s' % _data_source_name in request.POST:
                                _data_source_icon_name = request.POST['icon_name_%s' % _data_source_name]
                                if len(_data_source_icon_name) > 0:
                                    try:  # validate JSON format
                                        _data_source_config_json = json.loads(s=request.POST['config_json_%s' % _data_source_name])
                                        _campaign_data_sources += [{
                                            'name': _data_source_name,
                                            'icon_name': _data_source_icon_name,
                                            'config_json': _data_source_config_json
                                        }]
                                    except JSONDecodeError:
                                        return None

                    # bind the data sources and attach data source ids
                    for _index, _data_source in enumerate(_campaign_data_sources):
                        _id = db.get_data_source(data_source_name=_data_source['name']).id
                        if _id is None:  # create a new data source
                            _id = db.create_data_source(db_creator_user=db_user, name=_data_source['name'], icon_name=_data_source['icon_name'])
                        _campaign_data_sources[_index]['data_source_id'] = _id
                    return _campaign_data_sources

                if 'name' in request.POST and 'notes' in request.POST and 'startTime' in request.POST and 'endTime' and 'remove_inactive_users_timeout' in request.POST:
                    _campaign_name = str(request.POST['name'])
                    if utils.is_numeric(request.POST['remove_inactive_users_timeout']) and is_date_time(request.POST['startTime']) and is_date_time(request.POST['endTime']):
                        return {
                            'name': _campaign_name,
                            'notes': str(request.POST['notes']),
                            'configurations': json.dumps(get_campaign_data_sources_as_list()),
                            'start_timestamp': utils.datetime_to_timestamp_ms(value=datetime.datetime.strptime(request.POST['startTime'], "%Y-%m-%dT%H:%M")),
                            'end_timestamp': utils.datetime_to_timestamp_ms(value=datetime.datetime.strptime(request.POST['endTime'], "%Y-%m-%dT%H:%M")),
                            'remove_inactive_users_timeout': int(request.POST['remove_inactive_users_timeout']) if int(request.POST['remove_inactive_users_timeout']) > 0 else -1
                        }
                    else:
                        return None
                else:
                    return None

            if 'campaign_id' in request.POST and utils.is_numeric(request.POST['campaign_id']):
                db_campaign = db.get_campaign(campaign_id=int(request.POST['campaign_id']))
                if db_campaign is None:
                    # request to create a new campaign
                    campaign_params = prepare_campaign_params()
                    if campaign_params is not None:
                        db.create_or_update_campaign(
                            db_user_creator=db_user,
                            name=campaign_params['name'],
                            notes=campaign_params['notes'],
                            configurations=campaign_params['configurations'],
                            start_timestamp=campaign_params['start_timestamp'],
                            end_timestamp=campaign_params['end_timestamp']
                        )
                        return redirect(to='campaigns-list')
                    else:
                        return redirect(to='campaigns-list')
                elif db_campaign['creator_id'] == db_user['id']:
                    # request to edit an existing campaign
                    campaign_params = prepare_campaign_params()
                    if campaign_params is not None:
                        db.create_or_update_campaign(
                            db_user_creator=db_user,
                            name=campaign_params['name'],
                            notes=campaign_params['notes'],
                            configurations=campaign_params['configurations'],
                            start_timestamp=campaign_params['start_timestamp'],
                            end_timestamp=campaign_params['end_timestamp'],
                            db_campaign=db_campaign
                        )
                        return redirect(to='campaigns-list')
                    else:
                        return redirect(to='campaigns-list')
                else:
                    return redirect(to='campaigns-list')
            else:
                return redirect(to='campaigns-list')
        else:
            return redirect(to='campaigns-list')
    else:
        dj_logout(request=request)
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_easytrack_monitor(request):
    db_user = db.get_user(email=request.user.email)
    if db_user is not None:
        if 'campaign_id' in request.GET and utils.is_numeric(request.GET['campaign_id']):
            db_campaign = db.get_campaign(campaign_id=int(request.GET['campaign_id']))
            db_campaign_data_sources = db.get_campaign_data_sources(db_campaign=db_campaign)
            db_campaign_participant_users = db.get_campaign_participants(db_campaign=db_campaign)
            if db_campaign is not None:
                from_datetime = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                till_datetime = from_datetime + datetime.timedelta(hours=24)

                if 'plot_date' in request.GET:
                    plot_date_str = str(request.GET['plot_date'])
                    if re.search(r'\d{4}-\d{1,2}-\d{1,2}', plot_date_str) is not None:
                        year, month, day = plot_date_str.split('-')
                        from_datetime = datetime.datetime(year=int(year), month=int(month), day=int(day), hour=0, minute=0, second=0, microsecond=0)
                        till_datetime = from_datetime + datetime.timedelta(hours=24)

                till_timestamp = utils.datetime_to_timestamp_ms(till_datetime)
                from_timestamp = utils.datetime_to_timestamp_ms(from_datetime)
                window = 3600000  # 1 hour jump

                if 'participant_id' in request.GET and utils.is_numeric(request.GET['participant_id']):
                    db_participant_user = db.get_user(user_id=request.GET['participant_id'])
                    if db_participant_user is not None and db.user_is_bound_to_campaign(db_user=db_participant_user, db_campaign=db_campaign):
                        plot_participant = db_participant_user
                    else:
                        plot_participant = {'id': 'all'}
                else:
                    plot_participant = {'id': 'all'}

                if 'data_source_name' in request.GET:
                    data_source_name = request.GET['data_source_name']
                    db_data_source = db.get_data_source(data_source_name=data_source_name)
                    if data_source_name == 'all':
                        hourly_stats = {}
                        # region compute hourly stats
                        for db_participant_user in (db_campaign_participant_users if plot_participant.id == 'all' else [plot_participant]):
                            for db_data_source in db_campaign_data_sources:
                                _from_timestamp = from_timestamp
                                _till_timestamp = _from_timestamp + window
                                while _from_timestamp < till_timestamp:
                                    hour = utils.get_timestamp_hour(timestamp_ms=_from_timestamp)
                                    amount = db.get_filtered_amount_of_data(
                                        db_campaign=db_campaign,
                                        db_user=db_participant_user,
                                        from_timestamp=_from_timestamp,
                                        till_timestamp=_till_timestamp,
                                        db_data_source=db_data_source
                                    )
                                    if hour in hourly_stats:
                                        hourly_stats[hour] += amount
                                    else:
                                        hourly_stats[hour] = amount
                                    _from_timestamp += window
                                    _till_timestamp += window
                        # endregion

                        plot_data_source = {'name': 'all campaign data sources combined'}
                        # region plot hourly stats
                        x = []
                        y = []
                        max_amount = 10
                        hours = list(hourly_stats.keys())
                        hours.sort()
                        for hour in hours:
                            amount = hourly_stats[hour]
                            if hour < 13:
                                hour = f'{hour} {"pm" if hour == 12 else "am"}'
                            else:
                                hour = f'{hour % 12} pm'
                            x += [hour]
                            y += [amount]
                            max_amount = max(max_amount, amount)
                        fig = go.Figure([go.Bar(x=x, y=y)])
                        fig.update_yaxes(range=[0, max_amount])
                        plot_str = plotly.offline.plot(fig, auto_open=False, output_type="div")
                        plot_data_source['plot'] = plot_str
                        # endregion

                        return render(
                            request=request,
                            template_name='easytrack_monitor.html',
                            context={
                                'title': 'EasyTracker',
                                'campaign': db_campaign,
                                'plot_date': f'{from_datetime.year}-{from_datetime.month:02}-{from_datetime.day:02}',

                                'participants': db_campaign_participant_users,
                                'plot_participant': plot_participant,

                                'all_data_sources': db_campaign_data_sources,
                                'plot_data_source': plot_data_source
                            }
                        )
                    elif db_data_source is not None:
                        hourly_stats = {}
                        # region compute hourly stats
                        for db_participant_user in (db_campaign_participant_users if plot_participant.id == 'all' else [plot_participant]):
                            _from_timestamp = from_timestamp
                            _till_timestamp = _from_timestamp + window
                            while _from_timestamp < till_timestamp:
                                hour = utils.get_timestamp_hour(timestamp_ms=_from_timestamp)
                                amount = db.get_filtered_amount_of_data(
                                    db_campaign=db_campaign,
                                    db_user=db_participant_user,
                                    from_timestamp=_from_timestamp,
                                    till_timestamp=_till_timestamp,
                                    db_data_source=db_data_source
                                )
                                if hour in hourly_stats:
                                    hourly_stats[hour] += amount
                                else:
                                    hourly_stats[hour] = amount
                                _from_timestamp += window
                                _till_timestamp += window
                        # endregion

                        plot_data_source = EnhancedDataSource(db_data_source=db_data_source)
                        # region plot hourly stats
                        x = []
                        y = []
                        max_amount = 10
                        hours = list(hourly_stats.keys())
                        hours.sort()
                        for hour in hours:
                            amount = hourly_stats[hour]
                            if hour < 13:
                                hour = f'{hour} {"pm" if hour == 12 else "am"}'
                            else:
                                hour = f'{hour % 12} pm'
                            x += [hour]
                            y += [amount]
                            max_amount = max(max_amount, amount)
                        fig = go.Figure([go.Bar(x=x, y=y)])
                        fig.update_yaxes(range=[0, max_amount])
                        plot_str = plotly.offline.plot(fig, auto_open=False, output_type="div")
                        plot_data_source.attach_plot(plot_str=plot_str)
                        # endregion

                        return render(
                            request=request,
                            template_name='easytrack_monitor.html',
                            context={
                                'title': 'EasyTracker',
                                'campaign': db_campaign,
                                'plot_date': f'{from_datetime.year}-{from_datetime.month:02}-{from_datetime.day:02}',

                                'participants': db_campaign_participant_users,
                                'plot_participant': plot_participant,

                                'all_data_sources': db_campaign_data_sources,
                                'plot_data_source': plot_data_source
                            }
                        )
                    else:
                        return redirect(to='campaigns-list')
                else:
                    return redirect(to='campaigns-list')
            else:
                return redirect(to='campaigns-list')
        else:
            return redirect(to='campaigns-list')
    else:
        dj_logout(request=request)
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_dataset_info(request):
    db_user = db.get_user(email=request.user.email)
    if db_user is not None:
        if 'campaign_id' in request.GET and utils.is_numeric(request.GET['campaign_id']):
            db_campaign = db.get_campaign(campaign_id=int(request.GET['campaign_id']))
            if db_campaign is not None:
                campaign_data_sources = list(json.loads(s=db_campaign.configJson))
                campaign_data_sources.sort(key=lambda x: x['name'])
                db_participants = list(db.get_campaign_participants(db_campaign=db_campaign))
                db_participants.sort(key=lambda db_participant: db_participant.id)
                return render(
                    request=request,
                    template_name='page_dataset_configs.html',
                    context={
                        'data_sources': campaign_data_sources,
                        'participants': db_participants
                    }
                )
            else:
                return redirect(to='campaigns-list')
        else:
            return redirect(to='campaigns-list')
    else:
        dj_logout(request=request)
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_delete_campaign_api(request):
    db_user = db.get_user(email=request.user.email)
    if db_user is not None:
        if 'campaign_id' in request.GET and utils.is_numeric(request.GET['campaign_id']):
            db_campaign = db.get_campaign(campaign_id=int(request.GET['campaign_id']))
            if db_campaign is not None:
                db.delete_campaign(db_campaign=db_campaign)
                return redirect(to='campaigns-list')
            else:
                return redirect(to='campaigns-list')
        else:
            return redirect(to='campaigns-list')
    else:
        dj_logout(request=request)
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_download_data_api(request):
    db_user = db.get_user(email=request.user.email)
    if db_user is not None:
        if 'campaign_id' in request.GET and utils.is_numeric(request.GET['campaign_id']):
            db_campaign = db.get_campaign(campaign_id=int(request.GET['campaign_id']))
            if db_campaign is not None:
                if 'participant_id' in request.GET and utils.is_numeric(request.GET['participant_id']):
                    db_participant_user = db.get_user(user_id=request.GET['participant_id'])
                    if db_participant_user is not None:
                        # dump db data
                        dump_file_path = db.dump_data(db_campaign=db_campaign, db_user=db_participant_user)
                        with open(dump_file_path, 'rb') as r:
                            dump_content = bytes(r.read())
                        os.remove(dump_file_path)

                        # archive the dump content
                        now = datetime.datetime.now()
                        file_name = f'et data {db_participant_user.email} {now.month}-{now.day}-{now.year} {now.hour}-{now.minute}.zip'
                        file_path = utils.get_download_file_path(file_name=file_name)
                        fp = zipfile.ZipFile(file_path, 'w', zipfile.ZIP_STORED)
                        with open(os.path.join(settings.STATIC_DIR, 'restoring_postgres_data.txt'), 'r') as r:
                            fp.writestr('!README.txt', r.read())
                        fp.writestr('!info.txt', f'campaign_id : {db_campaign.id}')
                        fp.writestr(f'{db_participant_user.email}.bin', dump_content)
                        fp.close()
                        with open(file_path, 'rb') as r:
                            content = r.read()
                        os.remove(file_path)

                        res = HttpResponse(content=content, content_type='application/x-binary')
                        res['Content-Disposition'] = f'attachment; filename={file_name}'
                        return res
                    else:
                        return redirect(to='campaigns-list')
                else:
                    return redirect(to='campaigns-list')
            else:
                return redirect(to='campaigns-list')
        else:
            return redirect(to='campaigns-list')
    else:
        dj_logout(request=request)
        return redirect(to='login')


@csrf_exempt
@require_http_methods(['POST'])
def handle_db_mgmt_api(request):
    # for db_campaign in db.get_campaigns():
    #     max_count = db.get_campaign_participants_count(db_campaign=db_campaign)
    #     count = 1
    #     for db_participant in db.get_campaign_participants(db_campaign=db_campaign):
    #         print(f'{db_campaign.id}-{db_participant["id"]} ({count} / {max_count})')
    #         db.rescue_data_table(db_campaign=db_campaign, db_participant=db_participant)
    return JsonResponse(data={'rescued': True})


@login_required
@require_http_methods(['GET'])
def handle_download_dataset_api(request):
    db_user = db.get_user(email=request.user.email)
    if db_user is not None:
        if 'campaign_id' in request.GET and utils.is_numeric(request.GET['campaign_id']):
            db_campaign = db.get_campaign(campaign_id=int(request.GET['campaign_id']))
            if db_campaign is not None:
                # archive
                now = datetime.datetime.now()
                file_name = f'et data campaign {db_campaign.id} {now.month}-{now.day}-{now.year} {now.hour}-{now.minute}.zip'
                file_path = utils.get_download_file_path(file_name=file_name)
                fp = zipfile.ZipFile(file_path, 'w', zipfile.ZIP_STORED)
                with open(os.path.join(settings.STATIC_DIR, 'restoring_postgres_data.txt'), 'r') as r:
                    fp.writestr('!README.txt', r.read())
                fp.writestr('!info.txt', f'campaign_id : {db_campaign.id}')

                for db_participant_user in db.get_campaign_participants(db_campaign=db_campaign):
                    # dump db data
                    dump_file_path = db.dump_data(db_campaign=db_campaign, db_user=db_participant_user)
                    with open(dump_file_path, 'rb') as r:
                        dump_content = bytes(r.read())
                    os.remove(dump_file_path)
                    # archive the dump content
                    fp.writestr(f'{db_participant_user.email}.bin', dump_content)
                fp.close()
                with open(file_path, 'rb') as r:
                    content = r.read()
                os.remove(file_path)

                res = HttpResponse(content=content, content_type='application/x-binary')
                res['Content-Disposition'] = f'attachment; filename={file_name}'
                return res
            else:
                return redirect(to='campaigns-list')
        else:
            return redirect(to='campaigns-list')
    else:
        dj_logout(request=request)
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_notifications_list(request):
    return None


@csrf_exempt
@require_http_methods(['POST'])
def huno_json_total_ema_score(request):
    if not utils.param_check(request.POST, ['campaign_id', 'participant_id', 'data_source_id', 'from_timestamp', 'till_timestamp']):
        return JsonResponse(data={'success': False, 'err_msg': 'huno, check your param types'})

    db_campaign = db.get_campaign(campaign_id=int(request.POST['campaign_id']))
    db_participant = db.get_user(user_id=int(request.POST['participant_id']))
    db_data_source = db.get_data_source(data_source_id=int(request.POST['data_source_id']))
    from_ts = int(request.POST['from_timestamp'])
    till_ts = int(request.POST['till_timestamp'])

    if None in [db_campaign, db_participant, db_data_source, from_ts, till_ts]:
        return JsonResponse(data={'success': False, 'err_msg': 'huno, values for some params are invalid, pls recheck'})

    res = {'success': True, 'scores': {}}
    for ema in db.get_filtered_data_records(db_campaign=db_campaign, from_timestamp=from_ts, till_timestamp=till_ts, db_user=db_participant, db_data_source=db_data_source):
        cells = str(bytes(ema['value']), encoding='utf8').split(' ')
        res['scores'][int(cells[0])] = sum([int(x) for x in cells[1:]])

    return JsonResponse(data=res)


@csrf_exempt
@require_http_methods(['POST'])
def huno_json_hr(request):
    if not utils.param_check(request.POST, ['campaign_id', 'participant_id', 'data_source_id', 'from_timestamp', 'till_timestamp']):
        return JsonResponse(data={'success': False, 'err_msg': 'huno, check your param types'})

    db_campaign = db.get_campaign(campaign_id=int(request.POST['campaign_id']))
    db_participant = db.get_user(user_id=int(request.POST['participant_id']))
    db_data_source = db.get_data_source(data_source_id=int(request.POST['data_source_id']))
    from_ts = int(request.POST['from_timestamp'])
    till_ts = int(request.POST['till_timestamp'])

    if None in [db_campaign, db_participant, db_data_source, from_ts, till_ts]:
        return JsonResponse(data={'success': False, 'err_msg': 'huno, values for some params are invalid, pls recheck'})

    hrs = []
    for hr in db.get_filtered_data_records(db_campaign=db_campaign, from_timestamp=from_ts, till_timestamp=till_ts, db_user=db_participant, db_data_source=db_data_source):
        cells = str(bytes(hr['value']), encoding='utf8').split(' ')
        hrs += [int(cells[1])]
    res = {'success': True, 'hr': 'n/a' if len(hrs) == 0 else sum(hrs) / len(hrs)}

    return JsonResponse(data=res)


@csrf_exempt
@require_http_methods(['POST'])
def huno_json_sleep(request):
    return JsonResponse(data={'success': False, 'err_msg': 'not implemented'})


@csrf_exempt
@require_http_methods(['POST'])
def huno_json_steps(request):
    if not utils.param_check(request.POST, ['campaign_id', 'participant_id', 'data_source_id', 'from_timestamp', 'till_timestamp']):
        return JsonResponse(data={'success': False, 'err_msg': 'huno, check your param types'})

    db_campaign = db.get_campaign(campaign_id=int(request.POST['campaign_id']))
    db_participant = db.get_user(user_id=int(request.POST['participant_id']))
    db_data_source = db.get_data_source(data_source_id=int(request.POST['data_source_id']))
    from_ts = int(request.POST['from_timestamp'])
    till_ts = int(request.POST['till_timestamp'])

    if None in [db_campaign, db_participant, db_data_source, from_ts, till_ts]:
        return JsonResponse(data={'success': False, 'err_msg': 'huno, values for some params are invalid, pls recheck'})

    res = {'success': True, 'amount': db.get_filtered_amount_of_data(db_campaign=db_campaign, from_timestamp=from_ts, till_timestamp=till_ts, db_user=db_participant, db_data_source=db_data_source)}
    return JsonResponse(data=res)


@csrf_exempt
@require_http_methods(['POST'])
def huno_json_total_reward(request):
    if not utils.param_check(request.POST, ['campaign_id', 'participant_id', 'data_source_id']):
        return JsonResponse(data={'success': False, 'err_msg': 'huno, check your param types'})

    db_campaign = db.get_campaign(campaign_id=int(request.POST['campaign_id']))
    db_participant = db.get_user(user_id=int(request.POST['participant_id']))
    db_data_source = db.get_data_source(data_source_id=int(request.POST['data_source_id']))

    if None in [db_campaign, db_participant, db_data_source]:
        return JsonResponse(data={'success': False, 'err_msg': 'huno, values for some params are invalid, pls recheck'})

    res = {'success': True, 'reward': db.get_filtered_amount_of_data(db_campaign=db_campaign, db_user=db_participant, db_data_source=db_data_source) * 250}
    return JsonResponse(data=res)


@csrf_exempt
@require_http_methods(['POST'])
def huno_json_ema_resp_rate(request):
    return JsonResponse(data={'success': False, 'err_msg': 'not implemented'})


@csrf_exempt
@require_http_methods(['POST'])
def huno_json_participant_stats(request):
    if not utils.param_check(request.POST, ['campaign_id', 'participant_id']):
        return JsonResponse(data={'success': False, 'err_msg': 'huno, check your param types'})

    db_campaign = db.get_campaign(campaign_id=int(request.POST['campaign_id']))
    db_participant = db.get_user(user_id=int(request.POST['participant_id']))

    if None in [db_campaign, db_participant]:
        return JsonResponse(data={'success': False, 'err_msg': 'huno, values for some params are invalid, pls recheck'})

    stats = db.get_participants_per_data_source_stats(db_user=db_participant, db_campaign=db_campaign)
    amount_of_samples = {}
    sync_timestamps = {}
    for _db_data_source, _amount_of_samples, _sync_timestamp in stats:
        amount_of_samples[_db_data_source.id] = _amount_of_samples
        sync_timestamps[_db_data_source.id] = _sync_timestamp

    return JsonResponse(data={
        'success': True,
        'participation_days': utils.calculate_day_number(join_timestamp=db.get_participant_join_timestamp(db_user=db_participant, db_campaign=db_campaign)),
        'total_amount': sum([amount_of_samples[x] for x in amount_of_samples]),
        'last_sync_ts': max([sync_timestamps[x] for x in sync_timestamps]),
        'per_data_source_amount': {x: amount_of_samples[x] for x in amount_of_samples},
        'per_data_source_last_sync_ts': {x: sync_timestamps[x] for x in sync_timestamps}
    })
