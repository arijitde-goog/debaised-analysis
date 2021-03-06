"""
Copyright 2020 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

https://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
"""
This module contains the function that gets called by the UI, and it
serves a purpose of a master function to all the intets.
It returns the result of the intent and also the list of suggestions.
"""

import json, pandas, enum, topk
from flask import escape
from show import show
from util import enums

def hello_http(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <http://flask.pocoo.org/docs/1.0/api/#flask.Request>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>.
    """
    request_json = request.get_json(silent=True)
    request_args = request.args

    # extracting the intent parameters from the json
    intent = request_json['intent']
    table = request_json['table']
    row_range = request_json['rowRange']
    metric = request_json['metric']
    dimensions = request_json['dimensions']
    summary_operator = request_json['summaryOperator']
    slices = request_json['slices']
    is_asc = request_json['isAsc']
    k = request_json['k']
    slices = request_json['slices']
    date = request_json['dateRange']
    time_granularity = request_json['timeGranularity']
    row_start = row_range["rowStart"]
    row_end = row_range["rowEnd"]
    row_header = row_range["header"]

    # Converting the list of list into a pandas dataframe.
    query_table = []
    for row in range(row_start-1, row_end):
        if row != row_header-1:
            query_table.append(table[row])
    query_table_dataframe = pandas.DataFrame(query_table,
                                             columns=table[row_header-1])

    # Converting the variables that contain denote the
    # date range into the desired format.
    date_column_name = None
    date_range = None
    if date != "null":
        date_column_name = date['dateCol']
        date_range = (date['dateStart'], date['dateEnd'])

    # Converting the Slices passed in the json into a
    # list of tuples (col, operator, val)
    slices_list = None
    if slices != "null":
        slices_list = []
        for item in slices:
            val = item['sliceVal']
            col = item['sliceCol']
            operator = _str_to_filter_enum(item['sliceOp'])
            slices_list.append((col, operator, val))

    if dimensions == 'null':
        dimensions = None

    if metric == 'null':
        metric = None

    summary_operator = _str_to_summary_operator_enum(summary_operator)

    suggestions = []

    if intent == 'show':
        query_table_dataframe = show(query_table_dataframe,
                                     slices=slices_list,
                                     metric=metric,
                                     dimensions=dimensions,
                                     summary_operator=summary_operator
                                    )
    elif intent == 'topk':
        query_result = topk.topk(query_table_dataframe,
                                 metric, dimensions, is_asc, k,
                                 summary_operator=summary_operator,
                                 date_column_name=date_column_name,
                                 date_range=date_range,
                                 slices=slices_list
                                )
        query_table_dataframe = query_result[0]
        suggestions = query_result[1]
    else:
        raise Exception("Intent name does not match")

    final_table = []

    # converting into a json object and returning
    final_table = query_table_dataframe.values.tolist()
    final_table.insert(0, list(query_table_dataframe.columns.values))

    json_ret = {'outputTable' : final_table, 'suggestions' : suggestions}
    json_string = json.dumps(json_ret)
    return json_string

def _str_to_filter_enum(comparator):
    """
    This function return the corresponding enum to the
    comparator passed.

    Args:
        comparator : Type-str
    Returns:
        Filter enum member
    """
    if comparator == 'Equal to':
        return enums.Filters.EQUAL_TO
    elif comparator == 'Not equal to':
        return enums.Filters.NOT_EQUAL_TO
    elif comparator == 'Less than':
        return enums.Filters.LESS_THAN
    elif comparator == 'Less than equal to':
        return enums.Filters.LESS_THAN_EQUAL_TO
    elif comparator == 'Greater than':
        return enums.Filters.GREATER_THAN
    elif comparator == 'Greater than equal to':
        return enums.Filters.GREATER_THAN_EQUAL_TO
    elif comparator == 'In':
        return enums.Filters.IN
    elif comparator == 'Not In':
        return enums.Filters.NOT_IN
    else:
        return None

def _str_to_summary_operator_enum(summary_operator):
    """
    This function return the corresponding enum to the
    summary operator passed.

    Args:
        summary_operator : Type-str
    Returns:
        SummaryOperator enum member
    """
    if summary_operator == 'SUM':
        return enums.SummaryOperators.SUM
    elif summary_operator == 'Mean':
        return enums.SummaryOperators.MEAN
    elif summary_operator == 'Count':
        return enums.SummaryOperators.COUNT
    elif summary_operator == 'Maximum':
        return enums.SummaryOperators.MAX
    elif summary_operator == 'Minimum':
        return enums.SummaryOperators.MIN
    elif summary_operator == 'Standard Deviation':
        return enums.SummaryOperators.STD
    elif summary_operator == 'Variance':
        return enums.SummaryOperators.VAR
    elif summary_operator == 'First':
        return enums.SummaryOperators.FIRST
    elif summary_operator == 'Last':
        return enums.SummaryOperators.LAST
    elif summary_operator == 'Count Distinct':
        return enums.SummaryOperators.DISTINCT
    else:
        return None
