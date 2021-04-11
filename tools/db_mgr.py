from cassandra.cluster import Cluster
from tools import settings
from tools import utils
import json


# region common part
def get_cassandra_session():
    if settings.cassandra_cluster is None:
        settings.cassandra_cluster = Cluster(contact_points=['127.0.0.1'])
        settings.cassandra_session = settings.cassandra_cluster.connect()
        print('cassandra session initialized', settings.cassandra_session)
    return settings.cassandra_session


def end():
    settings.cassandra_session.shutdown()
    settings.cassandra_cluster.shutdown()


def get_next_id(session, table_name):
    res = session.execute(f'select max("id") from {table_name};')
    last_id = res.one()[0]
    return 0 if last_id is None else last_id + 1


# endregion


# region 1. user management
def create_user(name, email, session_key):
    session = get_cassandra_session()
    next_id = get_next_id(session=session, table_name='et.user')
    session.execute('insert into "et"."user"("id", "email", "sessionKey", "name") values (%s,%s,%s,%s);', (
        next_id,
        email,
        session_key,
        name
    ))
    return session.execute('select * from "et"."user" where "id"=%s;', (next_id,)).one()


def get_user(user_id=None, email=None):
    session = get_cassandra_session()
    db_user = None
    if None not in [user_id, email]:
        db_user = session.execute('select * from "et"."user" where "id"=%s and "email"=%s allow filtering;', (
            user_id,
            email
        )).one()
    elif user_id is not None:
        db_user = session.execute('select * from "et"."user" where "id"=%s allow filtering;', (user_id,)).one()
    elif email is not None:
        db_user = session.execute('select * from "et"."user" where "email"=%s allow filtering;', (email,)).one()
    return db_user


def update_session_key(db_user, session_key):
    session = get_cassandra_session()
    session.execute('update "et"."user" set "sessionKey" = %s where "id" = %s and "email" = %s;', (
        session_key,
        db_user.id,
        db_user.email
    ))


def user_is_bound_to_campaign(db_user, db_campaign):
    session = get_cassandra_session()
    count = session.execute('select count(*) from "stats"."campaignParticipantStats" where "campaignId"=%s and "userId"=%s allow filtering;', (
        db_campaign.id,
        db_user.id
    )).one()[0]
    return count > 0


def bind_participant_to_campaign(db_user, db_campaign):
    session = get_cassandra_session()
    if not user_is_bound_to_campaign(db_user=db_user, db_campaign=db_campaign):
        session.execute('insert into "stats"."campaignParticipantStats"("userId", "campaignId", "joinTimestamp")  values (%s,%s,%s);', (
            db_user.id,
            db_campaign.id,
            utils.get_timestamp_ms()
        ))
        session.execute(f'create table if not exists "data"."cmp{db_campaign.id}_usr{db_user.id}"("dataSourceId" int, "timestamp" bigint, "value" blob, primary key ("dataSourceId", "timestamp"));')
        return True  # new binding
    return False  # old binding


# endregion


# region 2. campaign management
def create_or_update_campaign(db_creator_user, name, notes, configurations, start_timestamp, end_timestamp, db_campaign=None):
    session = get_cassandra_session()
    if db_campaign is None:
        next_id = get_next_id(session=session, table_name='et.campaign')
        session.execute('insert into "et"."campaign"("id", "creatorId", "name", "notes", "configJson", "startTimestamp", "endTimestamp") values (%s,%s,%s,%s,%s,%s,%s);', (
            next_id,
            db_creator_user.id,
            name,
            notes,
            configurations,
            start_timestamp,
            end_timestamp,
        ))
        return get_campaign(campaign_id=next_id, db_creator_user=db_creator_user)
    elif db_campaign.creatorId == db_creator_user.id:
        session.execute('update "et"."campaign" set "name" = %s, "notes" = %s, "configJson" = %s, "startTimestamp" = %s, "endTimestamp" = %s where "creatorId"=%s and "id"=%s;', (
            name,
            notes,
            configurations,
            start_timestamp,
            end_timestamp,
            db_creator_user.id,
            db_campaign.id
        ))
        return db_campaign


def get_campaign(campaign_id, db_creator_user=None):
    session = get_cassandra_session()
    if db_creator_user is None:
        db_campaign = session.execute('select * from "et"."campaign" where "id"=%s allow filtering;', (campaign_id,)).one()
    else:
        db_campaign = session.execute('select * from "et"."campaign" where "id"=%s and "creatorId"=%s allow filtering;', (
            campaign_id,
            db_creator_user.id
        )).one()
    return db_campaign


def delete_campaign(db_campaign):
    session = get_cassandra_session()
    session.execute(f'delete from "et"."campaign" where "creatorId"=%s and "id"=%s;', (db_campaign.creatorId, db_campaign.id,))


def get_campaigns(db_creator_user=None):
    session = get_cassandra_session()
    if db_creator_user is None:
        db_campaigns = session.execute('select * from "et"."campaign";').all()
    else:
        db_campaigns = session.execute('select * from "et"."campaign" where "creatorId"=%s allow filtering;', (db_creator_user.id,)).all()
    return db_campaigns


def get_campaign_participants(db_campaign):
    session = get_cassandra_session()
    db_participants = []
    for row in session.execute('select "userId" from "stats"."campaignParticipantStats" where "campaignId"=%s allow filtering;', (db_campaign.id,)).all():
        db_participants += [get_user(user_id=row.userId)]
    return db_participants


def get_campaign_participants_count(db_campaign):
    session = get_cassandra_session()
    return len(session.execute('select "userId" from "stats"."campaignParticipantStats" where "campaignId"=%s allow filtering;', (db_campaign.id,)).all())


# endregion


# region 3. data source management
def create_data_source(db_creator_user, name, icon_name):
    session = get_cassandra_session()
    next_id = get_next_id(session=session, table_name='et.dataSource')
    session.execute('insert into "et"."dataSource"("id", "creatorId", "name", "iconName") values (%s,%s,%s,%s);', (
        next_id,
        db_creator_user.id,
        name,
        icon_name
    ))
    return get_data_source(data_source_id=next_id)


def get_data_source(data_source_name=None, data_source_id=None):
    session = get_cassandra_session()
    db_data_source = None
    if None not in [data_source_id, data_source_name]:
        db_data_source = session.execute('select * from "et"."dataSource" where "id"=%s and "name"=%s allow filtering;', (
            data_source_id,
            data_source_name,
        )).one()
    elif data_source_id is not None:
        db_data_source = session.execute('select * from "et"."dataSource" where "id"=%s allow filtering;', (data_source_id,)).one()
    elif data_source_name is not None:
        db_data_source = session.execute('select * from "et"."dataSource" where "name"=%s allow filtering;', (data_source_name,)).one()
    return db_data_source


def get_all_data_sources():
    session = get_cassandra_session()
    return session.execute('select * from "et"."dataSource";').all()


def get_campaign_data_sources(db_campaign):
    db_data_sources = []
    config_jsons = json.loads(s=db_campaign.configJson)
    for config_json in config_jsons:
        db_data_source = get_data_source(data_source_id=config_json['data_source_id'])
        if db_data_source is not None:
            db_data_sources += [db_data_source]
    return db_data_sources


# endregion


# region 4. data management
def store_data_record(db_user, db_campaign, db_data_source, timestamp, value):
    session = get_cassandra_session()
    session.execute(f'insert into "data"."cmp{db_campaign.id}_usr{db_user.id}"("dataSourceId", "timestamp", "value") values (%s,%s,%s);', (
        db_data_source.id,
        timestamp,
        value
    ))


def store_data_records(db_user, db_campaign, timestamp_list, data_source_id_list, value_list):
    data_sources: dict = {}
    for timestamp, data_source_id, value in zip(timestamp_list, data_source_id_list, value_list):
        if data_source_id not in data_sources:
            db_data_source = get_data_source(data_source_id=data_source_id)
            if db_data_source is None:
                continue
            data_sources[data_source_id] = db_data_source
        if data_sources[data_source_id] is not None:
            store_data_record(
                db_user=db_user,
                db_campaign=db_campaign,
                db_data_source=data_sources[data_source_id],
                timestamp=timestamp,
                value=value
            )


def get_next_k_data_records(db_user, db_campaign, from_timestamp, db_data_source, k):
    session = get_cassandra_session()
    k_records = session.execute(f'select * from "data"."cmp{db_campaign.id}_usr{db_user.id}" where "timestamp">=%s and "dataSourceId"=%s order by "timestamp" asc limit {k} allow filtering;', (
        from_timestamp,
        db_data_source.id
    )).all()
    return k_records


def get_filtered_data_records(db_user, db_campaign, db_data_source, from_timestamp, till_timestamp=None):
    session = get_cassandra_session()
    if till_timestamp:
        data_records = session.execute(f'select * from "data"."cmp{db_campaign.id}_usr{db_user.id}" where "dataSourceId"=%s and "timestamp">=%s and "timestamp"<%s order by "timestamp" asc allow filtering;', (
            db_data_source.id,
            from_timestamp,
            till_timestamp
        )).all()
    else:
        data_records = session.execute(f'select * from "data"."cmp{db_campaign.id}_usr{db_user.id}" where "dataSourceId"=%s and "timestamp">=%s order by "timestamp" asc limit 500 allow filtering;', (
            db_data_source.id,
            from_timestamp
        )).all()
    return data_records


def dump_data(db_campaign, db_user):
    session = get_cassandra_session()

    file_path = utils.get_download_file_path(f'cmp{db_campaign.id}_usr{db_user.id}.bin.tmp')
    session.execute(f'copy (select "id", "timestamp", "value", "dataSourceId" from "data"."cmp{db_campaign.id}_usr{db_user.id}" allow filtering) to %s with binary;', (file_path,))

    session.close()
    return file_path


# endregion


# region 5. communication management
def create_direct_message(db_source_user, db_target_user, subject, content):
    session = get_cassandra_session()
    next_id = get_next_id(session=session, table_name='et.directMessage')
    session.execute('insert into "et"."directMessage"("id", "sourceUserId", "targetUserId", "timestamp", "subject", "content")  values (%s,%s,%s,%s,%s);', (
        next_id,
        db_source_user.id,
        db_target_user.id,
        utils.get_timestamp_ms(),
        subject,
        content
    ))
    return session.execute('select * from "et"."directMessage" where "id"=%s;', (next_id,)).one()


def get_unread_direct_messages(db_user):
    session = get_cassandra_session()
    db_direct_messages = session.execute('select * from "et"."directMessage" where "targetUserId"=%s and "read"=FALSE allow filtering;', (db_user.id,)).all()
    session.execute('update "et"."directMessage" set "read"=TRUE where targetUserId=%s;', (db_user.id,))
    return db_direct_messages


def create_notification(db_target_user, db_campaign, timestamp, subject, content):
    session = get_cassandra_session()
    next_id = get_next_id(session=session, table_name='et.notification')
    session.execute('insert into "et"."notification"("id", "targetUserId", "campaignId", "timestamp", "subject", "content") values (%s,%s,%s,%s,%s)', (
        next_id,
        db_target_user.id,
        db_campaign.id,
        timestamp,
        subject,
        content
    ))
    return session.execute('select * from "et"."notification" where "id"=%s;', (next_id,)).one()


def get_unread_notifications(db_user):
    session = get_cassandra_session()
    db_notifications = session.execute('select * from "et"."notification" where "targetUserId"=%s and "read"=FALSE allow filtering;', (db_user.id,)).all()
    session.execute('update "et"."notification" set "read"=TRUE where "targetUserId"=%s;', (db_user.id,))
    return db_notifications


# endregion


# region 6. statistics
def get_participant_join_timestamp(db_user, db_campaign):
    session = get_cassandra_session()
    res = session.execute('select "joinTimestamp" from "stats"."campaignParticipantStats" where "userId"=%s and "campaignId"=%s allow filtering;', (
        db_user.id,
        db_campaign.id
    )).one()
    return None if res is None else res.joinTimestamp


def get_participant_last_sync_timestamp(db_user, db_campaign):
    session = get_cassandra_session()
    res = session.execute('select max("syncTimestamp") from "stats"."perDataSourceStats" where "campaignId"=%s and "userId"=%s allow filtering;', (
        db_campaign.id,
        db_user.id,
    )).one()[0]
    return 0 if res is None else res


def get_participant_heartbeat_timestamp(db_user, db_campaign):
    session = get_cassandra_session()
    res = session.execute('select "lastHeartbeatTimestamp" from "stats"."campaignParticipantStats" where "userId" = %s and "campaignId" = %s allow filtering;', (
        db_user.id,
        db_campaign.id
    )).one()
    return 0 if res is None else res.lastHeartbeatTimestamp


def get_participants_amount_of_data(db_user, db_campaign):
    cur = get_cassandra_session()
    amount_of_samples = cur.execute(f'select sum("amountOfSamples") from "stats"."perDataSourceStats" where "campaignId"=%s and "userId"=%s allow filtering;', (
        db_campaign.id,
        db_user.id,
    )).one()[0]
    return 0 if amount_of_samples is None else amount_of_samples


def get_participants_per_data_source_stats(db_user, db_campaign):
    cur = get_cassandra_session()
    db_data_sources = get_campaign_data_sources(db_campaign=db_campaign)
    res_stats = []
    for db_data_source in db_data_sources:
        res = cur.execute(f'select "amountOfSamples" from "stats"."perDataSourceStats" where "campaignId"=%s and "userId"=%s and "dataSourceId"=%s allow filtering;', (
            db_campaign.id,
            db_user.id,
            db_data_source.id,
        )).one()
        amount_of_samples = 0 if res is None or res.amountOfSamples is None else res.amountOfSamples
        res = cur.execute(f'select "syncTimestamp" from "stats"."perDataSourceStats" where "campaignId"=%s and "userId"=%s and "dataSourceId"=%s allow filtering;', (
            db_campaign.id,
            db_user.id,
            db_data_source.id,
        )).one()
        sync_timestamp = 0 if res is None or res.syncTimestamp is None else res.syncTimestamp
        res_stats += [(
            db_data_source,
            amount_of_samples,
            sync_timestamp
        )]
    return res_stats


def update_user_heartbeat_timestamp(db_user, db_campaign):
    session = get_cassandra_session()
    session.execute('update "stats"."campaignParticipantStats" set "lastHeartbeatTimestamp" = %s where "userId" = %s and "campaignId" = %s;', (
        utils.get_timestamp_ms(),
        db_user.id,
        db_campaign.id
    ))


def remove_participant_from_campaign(db_user, db_campaign):
    session = get_cassandra_session()
    session.execute('delete from "stats"."campaignParticipantStats" where "userId" = %s and "campaignId" = %s;', (
        db_user.id,
        db_campaign.id
    ))


def get_participants_data_source_sync_timestamps(db_user, db_campaign, db_data_source):
    session = get_cassandra_session()
    res = session.execute(f'select "syncTimestamp" from "stats"."perDataSourceStats" where "campaignId"=%s and "userId"=%s and "dataSourceId"=%s allow filtering;', (
        db_campaign.id,
        db_user.id,
        db_data_source.id,
    ))
    return 0 if res is None else res.syncTimestamp


def get_filtered_amount_of_data(db_campaign, from_timestamp=0, till_timestamp=9999999999999, db_user=None, db_data_source=None):
    session = get_cassandra_session()
    amount = 0

    if db_user is None:
        # all users
        if db_data_source is None:
            # all data sources
            for db_participant_user in get_campaign_participants(db_campaign=db_campaign):
                amount += session.execute(f'select count(*) from "data"."{db_campaign.id}-{db_participant_user.id}" where "timestamp">=%s and "timestamp"<%s allow filtering;', (
                    from_timestamp,
                    till_timestamp
                )).one()[0]
        else:
            # single data source
            for db_participant_user in get_campaign_participants(db_campaign=db_campaign):
                amount += session.execute(f'select count(*) from "data"."{db_campaign.id}-{db_participant_user.id}" where "dataSourceId"=%s and "timestamp">=%s and "timestamp"<%s allow filtering;', (
                    db_data_source.id,
                    from_timestamp,
                    till_timestamp
                )).one()[0]
    else:
        # single user
        if db_data_source is None:
            # all data sources
            amount += session.execute(f'select count(*) from "data"."cmp{db_campaign.id}_usr{db_user.id}" where "timestamp">=%s and "timestamp"<%s;', (
                from_timestamp,
                till_timestamp
            )).one()[0]
        else:
            # single data source
            # f'select count(*) as "amount" from "data"."cmp{db_campaign.id}_usr{db_user.id}" where "dataSourceId"={db_data_source["id"]} and "timestamp">={from_timestamp} and "timestamp"<{till_timestamp};'
            amount += session.execute(f'select count(*) from "data"."cmp{db_campaign.id}_usr{db_user.id}" where "dataSourceId"=%s and "timestamp">=%s and "timestamp"<%s allow filtering;', (
                db_data_source.id,
                from_timestamp,
                till_timestamp
            )).one()[0]
    return amount

# endregion
