import ast

from app.utils.decorators import database_required, user_authenticated
from django.http import HttpResponse, JsonResponse


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_tree_info(request, database):
    try:
        data = {
            "database": database.GetName(),
            "formatted_version": database.GetFormattedVersion(),
            "version": database.GetVersion(),
            "username": database.GetUserName(),
            "superuser": database.GetUserSuper(),
            "express": database.GetExpress(),
            "create_role": database.TemplateCreateRole(),
            "alter_role": database.TemplateAlterRole(),
            "drop_role": database.TemplateDropRole(),
            "create_tablespace": database.TemplateCreateTablespace(),
            "alter_tablespace": database.TemplateAlterTablespace(),
            "drop_tablespace": database.TemplateDropTablespace(),
            "create_sequence": database.TemplateCreateSequence(),
            "alter_sequence": database.TemplateAlterSequence(),
            "drop_sequence": database.TemplateDropSequence(),
            "create_function": database.TemplateCreateFunction(),
            "drop_function": database.TemplateDropFunction(),
            "create_procedure": database.TemplateCreateProcedure(),
            "drop_procedure": database.TemplateDropProcedure(),
            "create_view": database.TemplateCreateView(),
            "drop_view": database.TemplateDropView(),
            "create_table": database.TemplateCreateTable(),
            "alter_table": database.TemplateAlterTable(),
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
            "drop_index": database.TemplateDropIndex(),
            "delete": database.TemplateDelete(),
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
            data["schema"], data["object"], data["type"]
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
    try:
        tables = database.QueryTables()
        list_tables = [table["table_name"] for table in tables.Rows]
    except Exception as exc:
        data = {"password_timeout": True, "data": str(exc)}
        return JsonResponse(data=data, status=500)

    return JsonResponse(data=list_tables, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_columns(request, database):
    table = request.data["table"]

    list_columns = []

    try:
        columns = database.QueryTablesFields(table)
        for column in columns.Rows:
            column_data = {
                "column_name": column["column_name"],
                "data_type": column["data_type"],
                "data_length": column["data_length"],
                "nullable": column["nullable"],
            }
            list_columns.append(column_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_columns, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_pk(request, database):
    table = request.data["table"]

    try:
        pks = database.QueryTablesPrimaryKeys(table)
        list_pk = [pk["constraint_name"] for pk in pks.Rows]
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_pk, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_pk_columns(request, database):
    data = request.data
    pkey = data["key"]
    table = data["table"]

    try:
        pks = database.QueryTablesPrimaryKeysColumns(pkey, table)
        list_pk = [row["column_name"] for row in pks.Rows]
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_pk, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_fks(request, database):
    table = request.data["table"]

    list_fk = []

    try:
        fks = database.QueryTablesForeignKeys(table)
        for fk in fks.Rows:
            fk_data = {
                "constraint_name": fk["constraint_name"],
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

    try:
        fks = database.QueryTablesForeignKeysColumns(fkey, table)
        fk = fks.Rows.pop() if fks.Rows else {}
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=fk)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_uniques(request, database):
    table = request.data["table"]

    try:
        uniques = database.QueryTablesUniques(table)
        list_uniques = [unique["constraint_name"] for unique in uniques.Rows]
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_uniques, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_uniques_columns(request, database):
    data = request.data
    unique = data["unique"]
    table = data["table"]

    try:
        uniques = database.QueryTablesUniquesColumns(unique, table)
        list_uniques = [unique["column_name"] for unique in uniques.Rows]
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_uniques, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_indexes(request, database):
    table = request.data["table"]

    list_indexes = []

    try:
        indexes = database.QueryTablesIndexes(table)
        for index in indexes.Rows:
            index_data = {
                "index_name": index["index_name"],
                "name_raw": index["name_raw"],
                "unique": index["uniqueness"] == "Unique",
                "type": "unique" if index["uniqueness"] == "Unique" else "non-unique",
                "is_primary": index["is_primary"] == "True",
                "columns": list(ast.literal_eval(index["columns"])),
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

    try:
        indexes = database.QueryTablesIndexesColumns(index, table)
        list_indexes = [index["column_name"] for index in indexes.Rows]
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_indexes, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_tablespaces(request, database):
    list_tablespaces = []

    try:
        tablespaces = database.QueryTablespaces()
        for tablespace in tablespaces.Rows:
            tablespace_data = {"name": tablespace["tablespace_name"]}
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
            role_data = {"name": role["role_name"]}
            list_roles.append(role_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_roles, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_packages(request, database):
    schema = request.data["schema"]

    list_packages = []

    try:
        packages = database.QueryPackages(False, schema)
        for package in packages.Rows:
            package_data = {"name": package["name"], "id": package["id"]}
            list_packages.append(package_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data={"data": list_packages})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_functions(request, database):
    list_functions = []

    try:
        functions = database.QueryFunctions()
        for function in functions.Rows:
            function_data = {"name": function["name"], "id": function["id"]}
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

    return JsonResponse({"data": function_definition})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_procedures(request, database):
    list_functions = []

    try:
        functions = database.QueryProcedures()
        for function in functions.Rows:
            function_data = {"name": function["name"], "id": function["id"]}
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

    return JsonResponse({"data": procedure_definition})


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_sequences(request, database):
    list_sequences = []

    try:
        sequences = database.QuerySequences()
        for sequence in sequences.Rows:
            sequence_data = {"sequence_name": sequence["sequence_name"]}
            list_sequences.append(sequence_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_sequences, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_views(request, database):
    list_tables = []

    try:
        tables = database.QueryViews()
        for table in tables.Rows:
            table_data = {
                "name": table["table_name"],
            }
            list_tables.append(table_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_tables, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_views_columns(request, database):
    table = request.data["table"]

    list_columns = []

    try:
        columns = database.QueryViewFields(table)
        for column in columns.Rows:
            column_data = {
                "column_name": column["column_name"],
                "data_type": column["data_type"],
                "data_length": column["data_length"],
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

    return JsonResponse({"data": view_definition})


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

    try:
        template = database.TemplateSelect(schema, table).text
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
def get_types(request, database):
    schema = request.data["schema"]

    list_types = []

    try:
        types = database.QueryTypes(False, schema)
        for type_object in types.Rows:
            type_data = {
                "type_name": type_object["type_name"],
            }
            list_types.append(type_data)
    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data=list_types, safe=False)


@user_authenticated
@database_required(check_timeout=True, open_connection=True)
def get_table_definition(request, database):
    data = request.data
    columns = []

    try:
        table = data["table"]
        schema = data["schema"]

        q_definition = database.QueryTableDefinition(table, schema)

        for col in q_definition.Rows:
            column_data = {
                "name": col["column_name"],
                "data_type": col["data_type"],
                "default_value": col["column_default"],
                "nullable": col["is_nullable"] != "N",
                "is_primary": bool(col["is_primary"]),
                "comment": col["column_comment"],
            }
            columns.append(column_data)

    except Exception as exc:
        return JsonResponse(data={"data": str(exc)}, status=400)

    return JsonResponse(data={"data": columns})
