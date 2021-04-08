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


# endregion


# region 1. user management
def get_next_id(session, table_name):
    res = session.execute(f'select max("id") from {table_name};')
    last_id = res.one()[0]
    return 0 if last_id is None else last_id + 1


def create_user(name, email, session_key):
    session = get_cassandra_session()
    user = session.execute('insert into "et"."user"("id", "email", "sessionKey", "name") values (%s,%s,%s,%s);', (
        get_next_id(session=session, table_name='et.user'),
        email,
        session_key,
        name
    ))
    return user


def get_user(user_id=None, email=None, session_key=None):
    session = get_cassandra_session()
    db_user = None
    if None not in [user_id, email, session_key]:
        db_user = session.execute('select * from "et"."user" where "id"=%s and "email"=%s and "sessionKey"=%s;', (
            user_id,
            email,
            session_key
        )).one()
    elif user_id is not None:
        db_user = session.execute('select * from "et"."user" where "id"=%s', (user_id,)).one()
    elif email is not None:
        db_user = session.execute('select * from "et"."user" where "email"=%s', (email,)).one()
    elif session_key is not None:
        db_user = session.execute('select * from "et"."user" where "sessionKey"=%s', (session_key,)).one()
    return db_user


def update_session_key(db_user, session_key):
    session = get_cassandra_session()
    session.execute('update "et"."user" set "sessionKey" = %s where "email" = %s;', (
        session_key,
        db_user.email
    ))


def user_is_bound_to_campaign(db_user, db_campaign):
    session = get_cassandra_session()
    count = session.execute('select count(*) from "stats"."campaignParticipantStats" where "campaignId"=%s and "userId"=%s;', (
        db_campaign.id,
        db_user.id
    )).one()[0]
    return count > 0


def bind_participant_to_campaign(db_user, db_campaign):
    session = get_cassandra_session()
    if not user_is_bound_to_campaign(db_user=db_user, db_campaign=db_campaign):
        session.execute('insert into "stats"."campaignParticipantStats"("userId", "campaignId", "join_timestamp")  values (%s,%s,%s);', (
            db_user.id,
            db_campaign.id,
            utils.get_timestamp_ms()
        ))
        session.execute(f'create table if not exists "data"."{db_campaign.id}-{db_user.id}"("timestamp" bigint, "value" blob, "dataSourceId" int);')
        return True  # new binding
    return False  # old binding


# endregion


# region 2. campaign management
def create_or_update_campaign(db_user_creator, db_campaign, name, notes, configurations, start_timestamp, end_timestamp, remove_inactive_users_timeout):
    session = get_cassandra_session()
    if db_campaign is None:
        session.execute('insert into "et"."campaign"("creatorId", "name", "notes", "config_json", "start_timestamp", "end_timestamp", "remove_inactive_users_timeout") values (%s,%s,%s,%s,%s,%s,%s);', (
            db_user_creator.id,
            name,
            notes,
            configurations,
            start_timestamp,
            end_timestamp,
            remove_inactive_users_timeout
        ))
    elif db_campaign.creatorId == db_user_creator.id:
        session.execute('update "et"."campaign" set "creatorId" = %s, "name" = %s, "notes" = %s, "config_json" = %s, "start_timestamp" = %s, "end_timestamp" = %s, "remove_inactive_users_timeout" = %s where "id"=%s;', (
            db_user_creator.id,
            name,
            notes,
            configurations,
            start_timestamp,
            end_timestamp,
            remove_inactive_users_timeout,
            db_campaign.id
        ))


def get_campaign(campaign_id, db_creator_user=None):
    session = get_cassandra_session()
    if db_creator_user is None:
        db_campaign = session.execute('select * from "et"."campaign" where "id"=%s;', (campaign_id,)).one()
    else:
        db_campaign = session.execute('select * from "et"."campaign" where "id"=%s and "creatorId"=%s;', (
            campaign_id,
            db_creator_user.id
        )).one()
    return db_campaign


def delete_campaign(db_campaign):
    session = get_cassandra_session()
    session.execute(f'delete from "et"."campaign" where id=%s;', (db_campaign.id,))


def get_campaigns(db_creator_user=None):
    session = get_cassandra_session()
    if db_creator_user is None:
        db_campaigns = session.execute('select * from "et"."campaign";').all()
    else:
        db_campaigns = session.execute('select * from "et"."campaign" where "creatorId"=%s;', (db_creator_user.id,)).all()
    return db_campaigns


def get_campaign_participants(db_campaign):
    session = get_cassandra_session()
    db_participants = session.execute('select * from "et"."user" where "id" in (select "userId" from "stats"."campaignParticipantStats" where "campaignId"=%s);', (db_campaign.id,)).all()
    return db_participants


def get_campaign_participants_count(db_campaign):
    session = get_cassandra_session()
    participants_count = session.execute('select count(*) from "et"."user" where "id" in (select "userId" from "stats"."campaignParticipantStats" where "campaignId"=%s);', (db_campaign.id,)).one()[0]
    return participants_count


# endregion


# region 3. data source management
def store_data_source(db_creator_user, name, icon_name):
    session = get_cassandra_session()
    session.execute('insert into "et"."data_source"("creatorId", "name", "icon_name") values (%s,%s,%s);', (
        db_creator_user.id,
        name,
        icon_name
    ))


def get_data_source(data_source_name=None, data_source_id=None):
    session = get_cassandra_session()
    db_data_source = None
    if None not in [data_source_id, data_source_name]:
        db_data_source = session.execute('select * from "et"."data_source" where "id"=%s and "name"=%s;', (
            data_source_id,
            data_source_name,
        )).one()
    elif data_source_id is not None:
        db_data_source = session.execute('select * from "et"."data_source" where "id"=%s;', (
            data_source_id,
        )).one()
    elif data_source_name is not None:
        db_data_source = session.execute('select * from "et"."data_source" where "name"=%s;', (
            data_source_name,
        )).one()
    return db_data_source


def get_all_data_sources():
    session = get_cassandra_session()
    session.execute('select * from "et"."data_source";')
    return session


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
    session.execute(f'insert into "data"."{db_campaign.id}-{db_user.id}"("timestamp", "value", "dataSourceId") values (%s,%s,%s) on conflict do nothing returning true;', (
        timestamp,
        value,
        db_data_source.id,
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
    k_records = session.execute(f'select * from "data"."{db_campaign.id}-{db_user.id}" where "timestamp">=%s and "dataSourceId"=%s order by "timestamp" asc limit {k};', (
        from_timestamp,
        db_data_source.id
    )).all()
    return k_records


def get_filtered_data_records(db_user, db_campaign, db_data_source, from_timestamp, till_timestamp):
    session = get_cassandra_session()
    if till_timestamp > 0:
        data_records = session.execute(f'select * from "data"."{db_campaign.id}-{db_user.id}" where "dataSourceId"=%s and "timestamp">=%s and "timestamp"<%s order by "timestamp" asc;', (
            db_data_source.id,
            from_timestamp,
            till_timestamp
        )).all()
    else:
        data_records = session.execute(f'select * from "data"."{db_campaign.id}-{db_user.id}" where "dataSourceId"=%s and "timestamp">=%s order by "timestamp" asc limit 500;', (
            db_data_source.id,
            from_timestamp
        )).all()
    return data_records


def dump_data(db_campaign, db_user):
    session = get_cassandra_session()

    file_path = utils.get_download_file_path(f'{db_campaign.id}-{db_user.id}.bin.tmp')
    session.execute(f'copy (select "id", "timestamp", "value", "dataSourceId" from "data"."{db_campaign.id}-{db_user.id}") to %s with binary;', (file_path,))

    session.close()
    return file_path


# endregion


# region 5. communication management
def create_direct_message(db_source_user, db_target_user, subject, content):
    session = get_cassandra_session()
    session.execute('insert into "et"."direct_message"("src_user_id", "target_user_id", "timestamp", "subject", "content")  values (%s,%s,%s,%s,%s);', (
        db_source_user.id,
        db_target_user.id,
        utils.get_timestamp_ms(),
        subject,
        content
    ))


def get_unread_direct_messages(db_user):
    session = get_cassandra_session()
    db_direct_messages = session.execute('select * from "et"."direct_message" where "target_user_id"=%s and "read"=FALSE;', (db_user.id,))
    session.execute('update "et"."direct_message" set "read"=TRUE where trg_user_id=%s;', (db_user.id,))
    return db_direct_messages


def create_notification(db_target_user, db_campaign, timestamp, subject, content):
    session = get_cassandra_session()
    session.execute('insert into "et"."notification"("target_user_id", "campaignId", "timestamp", "subject", "content") values (%s,%s,%s,%s,%s)', (
        db_target_user.id,
        db_campaign.id,
        timestamp,
        subject,
        content
    ))


def get_unread_notifications(db_user):
    session = get_cassandra_session()
    db_notifications = session.execute('select * from "et"."notification" where "target_user_id"=%s and "read"=FALSE;', (db_user.id,))
    session.execute('update "et"."notification" set "read"=TRUE where "target_user_id"=%s;', (db_user.id,))
    return db_notifications


# endregion


# region 6. statistics
def get_participant_join_timestamp(db_user, db_campaign):
    session = get_cassandra_session()
    res = session.execute('select "join_timestamp" from "stats"."campaignParticipantStats" where "userId"=%s and "campaignId"=%s;', (
        db_user.id,
        db_campaign.id
    )).one()
    return None if res is None else res.joinTimestamp


def get_participant_last_sync_timestamp(db_user, db_campaign):
    session = get_cassandra_session()
    res = session.execute('select max("syncTimestamp") from "stats"."perDataSourceStats" where "campaignId"=%s and "userId"=%s;', (
        db_campaign.id,
        db_user.id,
    )).one()[0]
    return 0 if res is None else res


def get_participant_heartbeat_timestamp(db_user, db_campaign):
    session = get_cassandra_session()
    res = session.execute('select "lastHeartbeatTimestamp" from "stats"."campaignParticipantStats" where "userId" = %s and "campaignId" = %s;', (
        db_user.id,
        db_campaign.id
    )).one()
    return 0 if res is None else res.lastHeartbeatTimestamp


def get_participants_amount_of_data(db_user, db_campaign):
    cur = get_cassandra_session()
    amount_of_samples = cur.execute(f'select sum("amountOfSamples") from "stats"."perDataSourceStats" where "campaignId"=%s and "userId"=%s;', (
        db_campaign.id,
        db_user.id,
    )).one()[0]
    return 0 if amount_of_samples is None else amount_of_samples


def get_participants_per_data_source_stats(db_user, db_campaign):
    cur = get_cassandra_session()
    db_data_sources = get_campaign_data_sources(db_campaign=db_campaign)
    res_stats = []
    for db_data_source in db_data_sources:
        res = cur.execute(f'select "amountOfSamples" from "stats"."perDataSourceStats" where "campaignId"=%s and "userId"=%s and "dataSourceId"=%s;', (
            db_campaign.id,
            db_user.id,
            db_data_source.id,
        )).one()
        amount_of_samples = 0 if res is None else res.amountOfSamples
        res = cur.execute(f'select "syncTimestamp" from "stats"."perDataSourceStats" where "campaignId"=%s and "userId"=%s and "dataSourceId"=%s;', (
            db_campaign.id,
            db_user.id,
            db_data_source.id,
        )).one()
        sync_timestamp = 0 if res is None else res.syncTimestamp
        res_stats += [(
            db_data_source.id,
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
    res = session.execute(f'select "syncTimestamp" from "stats"."perDataSourceStats" where "campaignId"=%s and "userId"=%s and "dataSourceId"=%s;', (
        db_campaign.id,
        db_user.id,
        db_data_source.id,
    ))
    return 0 if res is None else res.syncTimestamp

# endregion
