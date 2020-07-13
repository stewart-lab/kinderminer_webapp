def insert_into_string(table_name, field_list):
    # need to know how many fields we're inserting into
    n_fields = len(field_list)
    # and generate the (%s, %s...) value string for that
    val_str = ', '.join(['%s'] * n_fields)
    # as well as the field string
    field_str = ', '.join(field_list)
    return 'INSERT INTO {0} ({1}) VALUES ({2})'.format(
        table_name, field_str, val_str)


def select_string(table_name, field_list):
    # generate the field string
    field_str = ', '.join(field_list)
    # and select it
    return 'SELECT {0} FROM {1}'.format(field_str, table_name)


def select_where_string(table_name, field_list, where_field):
    # generate the field string
    field_str = ', '.join(field_list)
    # and select it
    return 'SELECT {0} FROM {1} WHERE {2}=%s'.format(
        field_str, table_name, where_field)


def select_multiwhere_string(table_name, field_list, where_list):
    # generate the field string
    field_str = ', '.join(field_list)
    # and build the WHERE field equalities
    where_fields = ['{0}=%s'.format(f) for f in where_list]
    # and combine them with ANDs
    where_string = ' AND '.join(where_fields)
    # and select it
    return 'SELECT {0} FROM {1} WHERE {2}'.format(
        field_str, table_name, where_string)


def update_where_string(table_name, update_field, where_field):
    return 'UPDATE {0} SET {1}=%s WHERE {2}=%s'.format(
        table_name, update_field, where_field)


def delete_where_string(table_name, where_field):
    return 'DELETE FROM {0} WHERE {1}=%s'.format(table_name, where_field)
