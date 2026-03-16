import ast

from app.models.main import Connection
from app.utils.crypto import pg_scram_sha256
from app.utils.decorators import database_required, user_authenticated
from django.http import HttpResponse, JsonResponse


@user_authenticated
@database_required(check_timeout=True, open_connection=True, prefer_database="postgres")
def get_tree_info(request, database):
    try:

        data = {
            "database": database.GetName(),
            "version": database.GetVersion(),
            "major_version": database.major_version,
            #'superuser': database.GetUserSuper(),
            "templates": {
                "drop_role": database.TemplateDropRole(),
                "create_tablespace": database.TemplateCreateTablespace(),
                "alter_tablespace": database.TemplateAlterTablespace(),
                "drop_tablespace": database.TemplateDropTablespace(),
                "create_database": database.TemplateCreateDatabase(),
                "alter_database": database.TemplateAlterDatabase(),
                "drop_database": database.TemplateDropDatabase(),
                "create_schema": database.TemplateCreateSchema(),
                "alter_schema": database.TemplateAlterSchema(),
                "drop_schema": database.TemplateDropSchema(),
                "create_sequence": database.TemplateCreateSequence(),
                "alter_sequence": database.TemplateAlterSequence(),
                "drop_sequence": database.TemplateDropSequence(),
                "create_function": database.TemplateCreateFunction(),
                "alter_function": database.TemplateAlterFunction(),
                "drop_function": database.TemplateDropFunction(),
                "create_procedure": database.TemplateCreateProcedure(),
                "alter_procedure": database.TemplateAlterProcedure(),
                "drop_procedure": database.TemplateDropProcedure(),
                "create_triggerfunction": database.TemplateCreateTriggerFunction(),
                "alter_triggerfunction": database.TemplateAlterTriggerFunction(),
                "drop_triggerfunction": database.TemplateDropTriggerFunction(),
                "create_eventtriggerfunction": database.TemplateCreateEventTriggerFunction(),
                "alter_eventtriggerfunction": database.TemplateAlterEventTriggerFunction(),
                "drop_eventtriggerfunction": database.TemplateDropEventTriggerFunction(),
                "create_aggregate": database.TemplateCreateAggregate(),
                "alter_aggregate": database.TemplateAlterAggregate(),
                "drop_aggregate": database.TemplateDropAggregate(),
                "create_view": database.TemplateCreateView(),
                "alter_view": database.TemplateAlterView(),
                "drop_view": database.TemplateDropView(),
                "create_mview": database.TemplateCreateMaterializedView(),
                "refresh_mview": database.TemplateRefreshMaterializedView(),
                "alter_mview": database.TemplateAlterMaterializedView(),
                "drop_mview": database.TemplateDropMaterializedView(),
                "drop_table": database.TemplateDropTable(),
                "create_column": database.TemplateCreateColumn(),
                "alter_column": database.TemplateAlterColumn(),
                "drop_column": database.TemplateDropColumn(),
                "create_primarykey": database.TemplateCreatePrimaryKey(),
                "drop_primarykey": database.TemplateDropPrimaryKey(),
                "create_unique": database.TemplateCreateUnique(),
                "drop_unique": database.TemplateDropUnique(),
                "create_foreignkey": database.TemplateCreateForeignKey(),
                "drop_foreignkey": database.TemplateDropForeignKey(),
                "create_index": database.TemplateCreateIndex(),
                "alter_index": database.TemplateAlterIndex(),
                "cluster_index": database.TemplateClusterIndex(),
                "reindex": database.TemplateReindex(),
                "drop_index": database.TemplateDropIndex(),
                "create_check": database.TemplateCreateCheck(),
                "drop_check": database.TemplateDropCheck(),
                "create_exclude": database.TemplateCreateExclude(),
                "drop_exclude": database.TemplateDropExclude(),
                "create_rule": database.TemplateCreateRule(),
                "alter_rule": database.TemplateAlterRule(),
                "drop_rule": database.TemplateDropRule(),
                "create_trigger": database.TemplateCreateTrigger(),
                "create_view_trigger": database.TemplateCreateViewTrigger(),
                "alter_trigger": database.TemplateAlterTrigger(),
                "enable_trigger": database.TemplateEnableTrigger(),
                "disable_trigger": database.TemplateDisableTrigger(),
                "drop_trigger": database.TemplateDropTrigger(),
                "create_eventtrigger": database.TemplateCreateEventTrigger(),
                "alter_eventtrigger": database.TemplateAlterEventTrigger(),
                "enable_eventtrigger": database.TemplateEnableEventTrigger(),
                "disable_eventtrigger": database.TemplateDisableEventTrigger(),
                "drop_eventtrigger": database.TemplateDropEventTrigger(),
                "create_inherited": database.TemplateCreateInherited(),
                "noinherit_partition": database.TemplateNoInheritPartition(),
                "create_partition": database.TemplateCreatePartition(),
                "detach_partition": database.TemplateDetachPartition(),
                "drop_partition": database.TemplateDropPartition(),
                "vacuum": database.TemplateVacuum(),
                "vacuum_table": database.TemplateVacuumTable(),
                "analyze": database.TemplateAnalyze(),
                "analyze_table": database.TemplateAnalyzeTable(),
                "delete": database.TemplateDelete(),
                "truncate": database.TemplateTruncate(),
                "create_physicalreplicationslot": database.TemplateCreatePhysicalReplicationSlot(),
                "drop_physicalreplicationslot": database.TemplateDropPhysicalReplicationSlot(),
                "create_logicalreplicationslot": database.TemplateCreateLogicalReplicationSlot(),
                "drop_logicalreplicationslot": database.TemplateDropLogicalReplicationSlot(),
                "create_publication": database.TemplateCreatePublication(),
                "alter_publication": database.TemplateAlterPublication(),
                "drop_publication": database.TemplateDropPublication(),
                "add_pubtable": database.TemplateAddPublicationTable(),
                "drop_pubtable": database.TemplateDropPublicationTable(),
                "create_subscription": database.TemplateCreateSubscription(),
                "alter_subscription": database.TemplateAlterSubscription(),
                "drop_subscription": database.TemplateDropSubscription(),
                "create_fdw": database.TemplateCreateForeignDataWrapper(),
                "alter_fdw": database.TemplateAlterForeignDataWrapper(),
                "drop_fdw": database.TemplateDropForeignDataWrapper(),
                "create_foreign_server": database.TemplateCreateForeignServer(),
                "alter_foreign_server": database.TemplateAlterForeignServer(),
                "import_foreign_schema": database.TemplateImportForeignSchema(),
                "drop_foreign_server": database.TemplateDropForeignServer(),
                "create_foreign_table": database.TemplateCreateForeignTable(),
                "alter_foreign_table": database.TemplateAlterForeignTable(),
                "drop_foreign_table": database.TemplateDropForeignTable(),
                "create_foreign_column": database.TemplateCreateForeignColumn(),
                "alter_foreign_column": database.TemplateAlterForeignColumn(),
                "drop_foreign_column": database.TemplateDropForeignColumn(),
                "create_user_mapping": database.TemplateCreateUserMapping(),
                "alter_user_mapping": database.TemplateAlterUserMapping(),
                "drop_user_mapping": database.TemplateDropUserMapping(),
                "create_type": database.TemplateCreateType(),
                "alter_type": database.TemplateAlterType(),
                "drop_type": database.TemplateDropType(),
                "create_domain": database.TemplateCreateDomain(),
                "alter_domain": database.TemplateAlterDomain(),
                "drop_domain": database.TemplateDropDomain(),
                "create_statistics": database.TemplateCreateStatistics(),
                "alter_statistics": database.TemplateAlterStatistics(),
                "drop_statistics": database.TemplateDropStatistics(),
            },
            "feature_flags": {
                "has_replication_slots": database.has_replication_slots,
                "has_extensions": database.has_extensions,
                "has_fdw": database.has_fdw,
                "has_event_triggers": database.has_event_triggers,
                "has_logical_replication": database.has_logical_replication,
            },
        }
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=data)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_database_objects(request, database):
    unsupported_versions = ["1.0", "1.1", "1.2", "1.3"]
    version_filter = (
        lambda extension: extension[0] == "pg_cron"
        and extension[2] not in unsupported_versions
    )
    has_pg_cron = False
    database.GetVersion() # this is needed to trigger database.update_feature_flags, in case it is new database
    try:
        current_schema = "public"
        schema = database.QueryCurrentSchema().Rows
        if schema:
            [current_schema] = schema[0]
        if database.has_extensions:
            extensions = database.QueryExtensions().Rows
            has_pg_cron = len(list(filter(version_filter, extensions))) > 0
        data = {
            "has_pg_cron": has_pg_cron,
            "current_schema": current_schema,
        }
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=data)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_properties(request, database):
    data = request.data["data"]

    list_properties = []
    ddl = ""

    try:
        properties = database.GetProperties(
            data["schema"], data["table"], data["object"], data["type"]
        )
        for property_object in properties.Rows:
            list_properties.append(
                [property_object["Property"], property_object["Value"]]
            )
        ddl = database.GetDDL(
            data["schema"], data["table"], data["object"], data["type"]
        )
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data={"properties": list_properties, "ddl": ddl})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_tables(request, database):
    schema = request.data["schema"]

    list_tables = []

    try:
        tables = database.QueryTables(False, schema)
        for table in tables.Rows:
            table_data = {
                "name": table["table_name"],
                "oid": table["oid"],
                "name_raw": table["name_raw"],
            }
            list_tables.append(table_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_tables, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_columns(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]

    list_columns = []

    try:
        columns = database.QueryTablesFields(table, False, schema)
        for column in columns.Rows:
            column_data = {
                "column_name": column["column_name"],
                "name_raw": column["name_raw"],
                "data_type": column["data_type"],
                "data_length": column["data_length"],
                "nullable": column["nullable"],
                "position": column["position"],
            }
            list_columns.append(column_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_columns, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_table_definition(request, v_database):
    data = request.data
    columns = []
    try:
        table = data["table"]
        schema = data["schema"]

        q_primaries = v_database.QueryTablePKColumns(table, schema)
        pk_column_names = [x[0] for x in q_primaries.Rows]
        q_definition = v_database.QueryTableDefinition(table, schema)
        for col in q_definition.Rows:
            column_data = {
                "name": col["column_name"],
                "data_type": col["data_type"],
                "default_value": col["column_default"],
                "nullable": col["is_nullable"] != "NO",
                "is_primary": col["column_name"] in pk_column_names,
                "comment": col["comment"],
            }
            columns.append(column_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data={"data": columns})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_pk(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]

    list_pk = []

    try:
        pks = database.QueryTablesPrimaryKeys(table, False, schema)
        for pk in pks.Rows:
            pk_data = {
                "constraint_name": pk["constraint_name"],
                "oid": pk["oid"],
                "name_raw": pk["name_raw"],
            }
            list_pk.append(pk_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_pk, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_pk_columns(request, database):
    data = request.data
    pkey = data["key"]
    table = data["table"]
    schema = data["schema"]

    try:
        pks = database.QueryTablesPrimaryKeysColumns(pkey, table, False, schema)
        list_pk = [pk["column_name"] for pk in pks.Rows]
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_pk, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_fks(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]

    list_fk = []

    try:
        fks = database.QueryTablesForeignKeys(table, False, schema)
        for fk in fks.Rows:
            fk_data = {
                "constraint_name": fk["constraint_name"],
                "oid": fk["oid"],
                "name_raw": fk["name_raw"],
                "column_name": fk["column_name"],
                "table_name": fk["table_name"],
                "table_schema": fk["table_schema"],
                "r_constraint_name": fk["r_constraint_name"],
                "r_table_name": fk["r_table_name"],
                "r_table_schema": fk["r_table_schema"],
                "r_column_name": fk["r_column_name"],
                "on_update": fk["update_rule"],
                "on_delete": fk["delete_rule"],
            }
            list_fk.append(fk_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_fk, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_fks_columns(request, database):
    data = request.data
    fkey = data["fkey"]
    table = data["table"]
    schema = data["schema"]

    list_fk = []

    try:
        fks = database.QueryTablesForeignKeysColumns(fkey, table, False, schema)
        for fk in fks.Rows:
            fk_data = {
                "r_table_name": fk["r_table_name"],
                "delete_rule": fk["delete_rule"],
                "update_rule": fk["update_rule"],
                "column_name": fk["column_name"],
                "r_column_name": fk["r_column_name"],
            }
            list_fk.append(fk_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_fk, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_uniques(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]

    list_uniques = []

    try:
        uniques = database.QueryTablesUniques(table, False, schema)
        for unique in uniques.Rows:
            v_unique_data = {
                "constraint_name": unique["constraint_name"],
                "oid": unique["oid"],
                "name_raw": unique["name_raw"],
            }
            list_uniques.append(v_unique_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_uniques, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_uniques_columns(request, database):
    data = request.data
    unique = data["unique"]
    table = data["table"]
    schema = data["schema"]

    try:
        uniques = database.QueryTablesUniquesColumns(unique, table, False, schema)
        list_uniques = [unique["column_name"] for unique in uniques.Rows]
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_uniques, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_indexes(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]

    list_indexes = []

    try:
        indexes = database.QueryTablesIndexes(table, False, schema)
        for index in indexes.Rows:
            index_data = {
                "index_name": index["index_name"],
                "name_raw": index["name_raw"],
                "unique": index["uniqueness"] == "Unique",
                "type": "unique" if index["uniqueness"] == "Unique" else "non-unique",
                "oid": index["oid"],
                "is_primary": index["is_primary"] == "True",
                "columns": list(ast.literal_eval(index["columns"])),
                "method": index["method"],
                "predicate": index["constraint"],
            }
            list_indexes.append(index_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_indexes, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_indexes_columns(request, database):
    data = request.data
    index = data["index"]
    table = data["table"]
    schema = data["schema"]

    try:
        indexes = database.QueryTablesIndexesColumns(index, table, False, schema)
        list_indexes = [index["column_name"] for index in indexes.Rows]
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_indexes, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_checks(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]

    list_checks = []

    try:
        checks = database.QueryTablesChecks(table, False, schema)
        for check in checks.Rows:
            check_data = {
                "constraint_name": check["constraint_name"],
                "name_raw": check["name_raw"],
                "constraint_source": check["constraint_source"],
                "oid": check["oid"],
            }
            list_checks.append(check_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_checks, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_excludes(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]

    list_excludes = []

    try:
        excludes = database.QueryTablesExcludes(table, False, schema)
        for exclude in excludes.Rows:
            exclude_data = {
                "constraint_name": exclude["constraint_name"],
                "name_raw": exclude["name_raw"],
                "attributes": exclude["attributes"],
                "operations": exclude["operations"],
                "oid": exclude["oid"],
            }
            list_excludes.append(exclude_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_excludes, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_rules(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]

    list_rules = []

    try:
        rules = database.QueryTablesRules(table, False, schema)
        for rule in rules.Rows:
            rule_data = {
                "rule_name": rule["rule_name"],
                "oid": rule["oid"],
                "name_raw": rule["name_raw"],
            }
            list_rules.append(rule_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_rules, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_rule_definition(request, database):
    data = request.data
    rule = data["rule"]
    table = data["table"]
    schema = data["schema"]

    try:
        rule_definition = database.GetRuleDefinition(rule, table, schema)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data={"data": rule_definition})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_triggers(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]

    list_triggers = []

    try:
        triggers = database.QueryTablesTriggers(table, False, schema)
        for trigger in triggers.Rows:
            trigger_data = {
                "trigger_name": trigger["trigger_name"],
                "name_raw": trigger["name_raw"],
                "enabled": trigger["trigger_enabled"],
                "trigger_function": trigger["trigger_function"],
                "id": trigger["id"],
                "function_oid": trigger["function_oid"],
                "oid": trigger["oid"],
            }
            list_triggers.append(trigger_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_triggers, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_eventtriggers(request, database):
    list_triggers = []

    try:
        triggers = database.QueryEventTriggers()
        for trigger in triggers.Rows:
            trigger_data = {
                "name": trigger["trigger_name"],
                "name_raw": trigger["name_raw"],
                "enabled": trigger["trigger_enabled"],
                "event": trigger["event_name"],
                "function": trigger["trigger_function"],
                "id": trigger["id"],
                "function_oid": trigger["function_oid"],
                "oid": trigger["oid"],
            }
            list_triggers.append(trigger_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_triggers, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_inheriteds(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]

    try:
        partitions = database.QueryTablesInheriteds(table, False, schema)
        list_partitions = [
            f'{partition["child_schema"]}.{partition["child_table"]}'
            for partition in partitions.Rows
        ]
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_partitions, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_partitions(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]

    try:
        partitions = database.QueryTablesPartitions(table, False, schema)
        list_partitions = [partition["child_table"] for partition in partitions.Rows]
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_partitions, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_statistics(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]

    list_statistics = []

    try:
        statistics = database.QueryTablesStatistics(table, False, schema)
        for statistic in statistics.Rows:
            statistic_data = {
                "statistic_name": statistic["statistic_name"],
                "name_raw": statistic["name_raw"],
                "schema_name": statistic["schema_name"],
                "oid": statistic["oid"],
            }
            list_statistics.append(statistic_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_statistics, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_statistics_columns(request, database):
    data = request.data
    statistics = data["statistics"]
    schema = data["schema"]

    list_columns = []

    try:
        columns = database.QueryStatisticsFields(statistics, False, schema)
        for column in columns.Rows:
            column_data = {"column_name": column["column_name"]}
            list_columns.append(column_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_columns, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_views(request, database):
    schema = request.data["schema"]

    list_tables = []

    try:
        tables = database.QueryViews(False, schema)
        for table in tables.Rows:
            table_data = {
                "name": table["table_name"],
                "oid": table["oid"],
                "name_raw": table["name_raw"],
            }
            list_tables.append(table_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_tables, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_views_columns(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]

    list_columns = []

    try:
        columns = database.QueryViewFields(table, False, schema)
        for column in columns.Rows:
            column_data = {
                "column_name": column["column_name"],
                "name_raw": column["name_raw"],
                "data_type": column["data_type"],
            }
            list_columns.append(column_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_columns, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_view_definition(request, database):
    data = request.data
    view = data["view"]
    schema = data["schema"]

    try:
        view_definition = database.GetViewDefinition(view, schema)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data={"data": view_definition})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_mviews(request, database):
    schema = request.data["schema"]

    list_tables = []

    try:
        tables = database.QueryMaterializedViews(False, schema)
        for table in tables.Rows:
            table_data = {
                "name": table["table_name"],
                "oid": table["oid"],
                "name_raw": table["name_raw"],
            }
            list_tables.append(table_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_tables, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_mviews_columns(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]

    list_columns = []

    try:
        columns = database.QueryMaterializedViewFields(table, False, schema)
        for column in columns.Rows:
            column_data = {
                "column_name": column["column_name"],
                "name_raw": column["name_raw"],
                "data_type": column["data_type"],
            }
            list_columns.append(column_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_columns, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_mview_definition(request, database):
    data = request.data
    view = data["view"]
    schema = data["schema"]

    try:
        mview_definition = database.GetMaterializedViewDefinition(view, schema)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data={"data": mview_definition})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_schemas(request, database):
    schemas_list = []
    system_schemas = {"information_schema", "pg_catalog"}
    try:
        schemas = database.QuerySchemas()
        for schema in schemas.Rows:
            if not request.user.userdetails.show_system_catalogs and schema["schema_name"] in system_schemas:
                continue
            schema_data = {
                "name": schema["schema_name"],
                "oid": schema["oid"],
                "name_raw": schema["name_raw"],
            }
            schemas_list.append(schema_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=500)
    return JsonResponse(data=schemas_list, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True, prefer_database="postgres")
def get_databases(request, database):
    list_databases = []

    try:
        conn_object = Connection.objects.get(id=database.conn_id)
        databases = database.QueryDatabases()
        for database_object in databases.Rows:
            database_data = {
                "name": database_object["database_name"],
                "name_raw": database_object["name_raw"],
                "oid": database_object["oid"],
                "pinned": database_object["database_name"]
                in conn_object.pinned_databases,
            }
            list_databases.append(database_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_databases, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_tablespaces(request, database):
    list_tablespaces = []

    try:
        tablespaces = database.QueryTablespaces()
        for tablespace in tablespaces.Rows:
            tablespace_data = {
                "name": tablespace["tablespace_name"],
                "oid": tablespace["oid"],
            }
            list_tablespaces.append(tablespace_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)
    return JsonResponse(data=list_tablespaces, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_roles(request, database):
    list_roles = []
    try:
        roles = database.QueryRoles()
        for role in roles.Rows:
            role_data = {
                "name": role["role_name"],
                "oid": role["oid"],
                "name_raw": role["name_raw"],
            }
            list_roles.append(role_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)
    return JsonResponse(data={"data": list_roles})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_role_details(request, database):
    role_oid = request.data["oid"]

    try:
        role = database.QueryRoleDetails(role_oid)
        if not role.Rows:
            return JsonResponse(
                {"data": f"Role with oid '{role_oid}' does not exist."}, status=400
            )

        rolerow = role.Rows[0]

        role_details = {
            "name": rolerow["role_name"],
            "name_raw": rolerow["name_raw"],
            "rolsuper": rolerow["rolsuper"],
            "rolinherit": rolerow["rolinherit"],
            "rolcanlogin": rolerow["rolcanlogin"],
            "rolcreaterole": rolerow["rolcreaterole"],
            "rolcreatedb": rolerow["rolcreatedb"],
            "rolbypassrls": rolerow["rolbypassrls"],
            "rolreplication": rolerow["rolreplication"],
            "rolconnlimit": rolerow["rolconnlimit"],
            "rolpassword": rolerow["rolpassword"],
            "rolvaliduntil": (
                None
                if rolerow["rolvaliduntil"] == "infinity"
                else rolerow["rolvaliduntil"]
            ),
            "members": rolerow["members"],
            "member_of": rolerow["member_of"],
        }

    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=role_details)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_functions(request, database):
    schema = request.data["schema"]

    list_functions = []

    try:
        functions = database.QueryFunctions(False, schema)
        for function in functions.Rows:
            function_data = {
                "name": function["name"],
                "name_raw": function["name_raw"],
                "id": function["id"],
                "function_oid": function["function_oid"],
            }
            list_functions.append(function_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_functions, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_function_fields(request, database):
    data = request.data
    function = data["function"]
    schema = data["schema"]

    list_fields = []

    try:
        fields = database.QueryFunctionFields(function, schema)
        for field in fields.Rows:
            field_data = {"name": field["name"], "type": field["type"]}
            list_fields.append(field_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_fields, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_function_definition(request, database):
    function = request.data["function"]

    try:
        function_definition = database.GetFunctionDefinition(function)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data={"data": function_definition})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_function_debug(request, database):
    function = request.data["function"]

    try:
        response_data = database.GetFunctionDebug(function)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data={"data": response_data})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_procedures(request, database):
    schema = request.data["schema"]

    list_functions = []

    try:
        functions = database.QueryProcedures(False, schema)
        for function in functions.Rows:
            function_data = {
                "name": function["name"],
                "id": function["id"],
                "function_oid": function["function_oid"],
            }
            list_functions.append(function_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_functions, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_procedure_fields(request, database):
    data = request.data
    function = data["procedure"]
    schema = data["schema"]

    list_fields = []

    try:
        fields = database.QueryProcedureFields(function, schema)
        for field in fields.Rows:
            field_data = {"name": field["name"], "type": field["type"]}
            list_fields.append(field_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_fields, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_procedure_definition(request, database):
    function = request.data["procedure"]

    try:
        procedure_definition = database.GetProcedureDefinition(function)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data={"data": procedure_definition})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_procedure_debug(request, database):
    function = request.data["procedure"]

    try:
        response_data = database.GetProcedureDebug(function)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data={"data": response_data})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_triggerfunctions(request, database):
    schema = request.data["schema"]

    list_functions = []

    try:
        functions = database.QueryTriggerFunctions(False, schema)
        for function in functions.Rows:
            function_data = {
                "name": function["name"],
                "id": function["id"],
                "function_oid": function["function_oid"],
            }
            list_functions.append(function_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_functions, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_triggerfunction_definition(request, database):
    function = request.data["function"]

    try:
        trigger_function_definition = database.GetTriggerFunctionDefinition(function)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data={"data": trigger_function_definition})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_eventtriggerfunctions(request, database):
    schema = request.data["schema"]

    list_functions = []

    try:
        functions = database.QueryEventTriggerFunctions(False, schema)
        for function in functions.Rows:
            function_data = {
                "name": function["name"],
                "id": function["id"],
                "function_oid": function["function_oid"],
            }
            list_functions.append(function_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_functions, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_eventtriggerfunction_definition(request, database):
    function = request.data["function"]

    try:
        function_definition = database.GetEventTriggerFunctionDefinition(function)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data={"data": function_definition})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_aggregates(request, database):
    schema = request.data["schema"]

    list_aggregates = []

    try:
        aggregates = database.QueryAggregates(False, schema)
        for aggregate in aggregates.Rows:
            aggregate_data = {
                "name": aggregate["name"],
                "id": aggregate["id"],
                "oid": aggregate["oid"],
            }
            list_aggregates.append(aggregate_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_aggregates, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_sequences(request, database):
    schema = request.data["schema"]

    list_sequences = []

    try:
        sequences = database.QuerySequences(False, schema)
        for sequence in sequences.Rows:
            sequence_data = {
                "sequence_name": sequence["sequence_name"],
                "name_raw": sequence["name_raw"],
                "oid": sequence["oid"],
            }
            list_sequences.append(sequence_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_sequences, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_extensions(request, database):
    list_extensions = []

    try:
        extensions = database.QueryExtensions()
        for extension in extensions.Rows:
            extension_data = {
                "name": extension["extension_name"],
                "name_raw": extension["name_raw"],
                "oid": extension["oid"],
            }
            list_extensions.append(extension_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_extensions, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_available_extensions(request, database):
    available_extensions = database.QueryAvailableExtensionsVersions()

    list_ext = []

    for extension in available_extensions.Rows:
        extension_data = {
            "name": extension["name"],
            "versions": extension["versions"],
            "comment": extension["comment"],
            "required_schema": extension["required_schema"],
        }
        list_ext.append(extension_data)
    return JsonResponse({"available_extensions": list_ext})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_extension_details(request, database):
    data = request.data

    extension = database.QueryExtensionByName(data.get("ext_name"))

    if not extension.Rows:
        return JsonResponse(
            {"data": f"Extension '{data.get('ext_name')}' does not exist."}, status=400
        )

    [extension_detail] = extension.Rows

    return JsonResponse(data=dict(extension_detail))


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def execute_query(request, database):
    data = request.data
    try:
        database.Execute(data.get("query"))
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)
    return JsonResponse({"status": "success"})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_physicalreplicationslots(request, database):
    list_repslots = []

    try:
        repslots = database.QueryPhysicalReplicationSlots()
        for repslot in repslots.Rows:
            repslot_data = {"name": repslot["slot_name"]}
            list_repslots.append(repslot_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)
    return JsonResponse(data=list_repslots, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_logicalreplicationslots(request, database):
    list_repslots = []

    try:
        repslots = database.QueryLogicalReplicationSlots()
        for repslot in repslots.Rows:
            repslot_data = {"name": repslot["slot_name"]}
            list_repslots.append(repslot_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)
    return JsonResponse(data=list_repslots, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_publications(request, database):
    list_pubs = []

    try:
        pubs = database.QueryPublications()
        for pub in pubs.Rows:
            pub_data = {
                "name": pub["pubname"],
                "name_raw": pub["name_raw"],
                "alltables": pub["puballtables"],
                "insert": pub["pubinsert"],
                "update": pub["pubupdate"],
                "delete": pub["pubdelete"],
                "truncate": pub["pubtruncate"],
                "oid": pub["oid"],
            }
            list_pubs.append(pub_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_pubs, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_publication_tables(request, database):
    pub = request.data["pub"]

    list_tables = []

    try:
        tables = database.QueryPublicationTables(pub)
        for table in tables.Rows:
            table_data = {"name": table["table_name"]}
            list_tables.append(table_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_tables, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_subscriptions(request, database):
    list_subs = []

    try:
        subs = database.QuerySubscriptions()
        for sub in subs.Rows:
            sub_data = {
                "name": sub["subname"],
                "name_raw": sub["name_raw"],
                "enabled": sub["subenabled"],
                "conn_info": sub["subconninfo"],
                "publications": sub["subpublications"],
                "oid": sub["oid"],
            }
            list_subs.append(sub_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_subs, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_subscription_tables(request, database):
    sub = request.data["sub"]

    list_tables = []

    try:
        tables = database.QuerySubscriptionTables(sub)
        for table in tables.Rows:
            table_data = {"name": table["table_name"]}
            list_tables.append(table_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_tables, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_foreign_data_wrappers(request, database):
    list_fdws = []

    try:
        fdws = database.QueryForeignDataWrappers()
        for fdw in fdws.Rows:
            fdw_data = {"name": fdw["fdwname"], "oid": fdw["oid"]}
            list_fdws.append(fdw_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_fdws, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_foreign_servers(request, database):
    fdw = request.data["fdw"]

    list_servers = []

    try:
        servers = database.QueryForeignServers(fdw)
        for server in servers.Rows:
            server_data = {
                "name": server["srvname"],
                "name_raw": server["name_raw"],
                "type": server["srvtype"],
                "version": server["srvversion"],
                "options": server["srvoptions"],
                "oid": server["oid"],
            }
            list_servers.append(server_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_servers, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_user_mappings(request, database):
    foreign_server = request.data["foreign_server"]

    list_mappings = []

    try:
        mappings = database.QueryUserMappings(foreign_server)
        for mapping in mappings.Rows:
            mapping_data = {
                "name": mapping["rolname"],
                "name_raw": mapping["name_raw"],
                "options": mapping["umoptions"],
                "foreign_server": foreign_server,
            }
            list_mappings.append(mapping_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_mappings, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_foreign_tables(request, database):
    schema = request.data["schema"]

    list_tables = []

    try:
        tables = database.QueryForeignTables(False, schema)
        for table in tables.Rows:
            table_data = {
                "name": table["table_name"],
                "oid": table["oid"],
                "name_raw": table["name_raw"],
            }
            list_tables.append(table_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_tables, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_foreign_columns(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]

    list_columns = []

    try:
        columns = database.QueryForeignTablesFields(table, False, schema)
        for column in columns.Rows:
            column_data = {
                "column_name": column["column_name"],
                "data_type": column["data_type"],
                "data_length": column["data_length"],
                "nullable": column["nullable"],
                "options": column["attfdwoptions"],
                "table_options": column["ftoptions"],
                "server": column["srvname"],
                "fdw": column["fdwname"],
            }
            list_columns.append(column_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_columns, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_types(request, database):
    schema = request.data["schema"]

    list_types = []

    try:
        types = database.QueryTypes(False, schema)
        for type_object in types.Rows:
            type_data = {
                "type_name": type_object["type_name"],
                "name_raw": type_object["name_raw"],
                "oid": type_object["oid"],
            }
            list_types.append(type_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_types, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_domains(request, database):
    schema = request.data["schema"]

    list_domains = []

    try:
        domains = database.QueryDomains(False, schema)
        for domain in domains.Rows:
            domain_data = {
                "domain_name": domain["domain_name"],
                "oid": domain["oid"],
                "name_raw": domain["name_raw"],
            }
            list_domains.append(domain_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_domains, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_inheriteds_parents(request, database):
    schema = request.data["schema"]

    list_tables = []
    try:
        tables = database.QueryTablesInheritedsParents(False, schema)
        for table in tables.Rows:
            table_data = {
                "name": f'{table["table_schema"]}.{table["table_name"]}',
                "name_raw": f'{table["table_schema_raw"]}.{table["name_raw"]}',
            }
            list_tables.append(table_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_tables, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_inheriteds_children(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]

    list_tables = []

    try:
        tables = database.QueryTablesInheritedsChildren(table, schema)
        for table in tables.Rows:
            table_data = {
                "name": table["table_name"],
                "oid": table["oid"],
                "name_raw": table["name_raw"],
            }
            list_tables.append(table_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_tables, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_partitions_parents(request, database):
    schema = request.data["schema"]

    list_tables = []
    try:
        tables = database.QueryTablesPartitionsParents(False, schema)
        for table in tables.Rows:
            table_data = {
                "name": table["table_name"],
                "name_raw": f'{table["table_schema_raw"]}.{table["name_raw"]}',
            }
            list_tables.append(table_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_tables, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_partitions_children(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]

    list_tables = []

    try:
        tables = database.QueryTablesPartitionsChildren(table, schema)
        for table in tables.Rows:
            table_data = {
                "name": table["table_name"],
                "oid": table["oid"],
                "name_raw": table["name_raw"],
            }
            list_tables.append(table_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_tables, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def kill_backend(request, database):
    pid = request.data["pid"]

    try:
        database.Terminate(pid)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return HttpResponse(status=204)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def template_select(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]
    kind = data["kind"]

    try:
        template = database.TemplateSelect(schema, table, kind).text
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data={"template": template})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def template_insert(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]

    try:
        template = database.TemplateInsert(schema, table).text
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data={"template": template})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def template_update(request, database):
    data = request.data
    table = data["table"]
    schema = data["schema"]

    try:
        template = database.TemplateUpdate(schema, table).text
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data={"template": template})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def template_select_function(request, database):
    data = request.data
    function = data["function"]
    functionid = data["functionid"]
    schema = data["schema"]

    try:
        template = database.TemplateSelectFunction(schema, function, functionid).text
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data={"template": template})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def template_call_procedure(request, database):
    data = request.data
    procedure = data["procedure"]
    procedureid = data["procedureid"]
    schema = data["schema"]

    try:
        template = database.TemplateCallProcedure(schema, procedure, procedureid).text
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data={"template": template})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_version(request, database):
    try:
        response_data = {"version": database.major_version}
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=response_data)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def change_role_password(request, database):
    data = request.data

    password = data["password"]

    hashed_password = pg_scram_sha256(password)

    try:
        database.ChangeRolePassword(data["role"], hashed_password)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse({"status": "success"})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_object_description(request, database):
    data = request.data
    oid = data["oid"]
    object_type = data["object_type"]
    position = data["position"]

    try:
        object_description = database.GetObjectDescription(object_type, oid, position)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data={"data": object_description})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_server_log(request, database):
    data = request.data
    log_format = data.get("log_format")
    log_offset = data.get("log_offset")
    log_offset_step = 10000

    try:
        log_formats = database.ExecuteScalar("show log_destination")

        if log_format not in log_formats:
            log_format = ""

        current_file_size = database.ExecuteScalar(
            f"SELECT size from pg_stat_file(pg_current_logfile('{log_format}'))"
        )

        if log_offset and log_offset < current_file_size:
            try:
                logs_data = database.Query(
                    f"SELECT pg_read_file(pg_current_logfile('{log_format}'), {log_offset}, {log_offset_step})"
                )
            except Exception:
                log_offset_step += 1
                logs_data = database.Query(
                    f"SELECT pg_read_file(pg_current_logfile('{log_format}'), {log_offset}, {log_offset_step})"
                )
            next_offset = min(log_offset + log_offset_step, current_file_size)
        else:
            log_offset = current_file_size
            logs_data = database.Query(
                f"SELECT pg_read_file(pg_current_logfile('{log_format}'))"
            )
            next_offset = current_file_size

        logs = logs_data.Rows[0]["pg_read_file"]
        current_logfile_data = database.Query(
            f"SELECT pg_current_logfile('{log_format}')"
        )
        current_logfile = current_logfile_data.Rows[0]["pg_current_logfile"]
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)
    return JsonResponse(
        data={
            "logs": logs,
            "current_logfile": current_logfile,
            "log_offset": next_offset,
        }
    )


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_log_formats(request, database):
    try:
        data = database.ExecuteScalar("show log_destination")
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)
    return JsonResponse(data={"formats": data})
