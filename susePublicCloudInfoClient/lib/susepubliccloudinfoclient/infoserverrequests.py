#!/usr/bin/python
#
# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of susePublicCloudInfoClient
#
# susePublicCloudInfoClient is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# susePublicCloudInfoClient is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with susePublicCloudInfoClient. If not, see
# <http://www.gnu.org/licenses/>.
#

import json
import re
import requests
import sys
import urllib
import xml.etree.ElementTree as ET


def __apply_filters(superset, filters):
    # map operators to filter functions
    filter_operations = {
        '=': __filter_exact,
        '~': __filter_substring,
        '>': __filter_greater_than,
        '<': __filter_less_than
    }
    # prepopulate the result set with all the items
    result_set = superset
    # run through the filters, allowing each to reduce the result set...
    for a_filter in filters:
        result_set = filter_operations[a_filter['operator']](
            result_set,
            a_filter['attr'],
            a_filter['value']
        )
    return result_set


def __filter_exact(items, attr, value):
    """select from items list where the attribute is an exact match to 'value'"""
    # start with an empty result set
    filtered_items = []
    # iterate over the list of items
    for item in items:
        # append the current item to the result set if matching
        if item[attr] == value:
            filtered_items.append(item)
    # return the filtered list
    return filtered_items


def __filter_substring(items, attr, value):
    """select from items list where 'value' is a substring of the attribute"""
    # start with an empty result set
    filtered_items = []
    # iterate over the list of items
    for item in items:
        # append the current item to the result set if matching
        if value in item[attr]:
            filtered_items.append(item)
    # return the filtered list
    return filtered_items


def __filter_less_than(items, attr, value):
    """select from items list where the attribute is less than 'value' as integers"""
    # start with an empty result set
    filtered_items = []
    # iterate over the list of items
    for item in items:
        # append the current item to the result set if matching
        if int(item[attr]) < int(value):
            filtered_items.append(item)
    # return the filtered list
    return filtered_items


def __filter_greater_than(items, attr, value):
    """select from items list where the attribute is greater than 'value' as integers"""
    # start with an empty result set
    filtered_items = []
    # iterate over the list of items
    for item in items:
        # append the current item to the result set if matching
        if int(item[attr]) > int(value):
            filtered_items.append(item)
    # return the filtered list
    return filtered_items


def __form_url(
        framework,
        info_type,
        result_format='xml',
        region='all',
        image_state=None,
        server_type=None,
        apply_filters=None):
    """Form the URL for the request"""
    url_components = []
    url_components.append(__get_base_url())
    url_components.append(__get_api_version())
    url_components.append(framework)
    if region == 'all':
        region = None
    if region:
        url_components.append(urllib.quote(region))
    url_components.append(info_type)
    doc_type = image_state or server_type
    server_format = __select_server_format(result_format, apply_filters)
    if doc_type:
        url_components.append(doc_type)
    url_components[-1] = url_components[-1] + '.' + server_format
    url = '/'
    return url.join(url_components)


def __get_api_version():
    """Return the API version to use"""
    return 'v1'


def __get_base_url():
    """Return the base url for the information service"""
    return 'https://susepubliccloudinfo.suse.com'


def __get_data(url):
    """Make the request and return the data or None in case of failure"""
    response = requests.get(url)
    assert response.text, "No data was returned by the server!"
    return response.text


def __inflect(plural):
    inflections = {'images': 'image', 'servers': 'server'}
    return inflections[plural]


def __parse_command_arg_filter(command_arg_filter=None):
    """Break down the --filter argument into a list of filters"""
    valid_filters = {
        'id': '^(?P<attr>id)(?P<operator>[=])(?P<value>.+)$',
        'replacementid': '^(?P<attr>replacementid)(?P<operator>[=])(?P<value>.+)$',
        'ip': '^(?P<attr>ip)(?P<operator>[=])(?P<value>\d+\.\d+\.\d+.\d+)$',
        'name': '^(?P<attr>name)(?P<operator>[~])(?P<value>.+)$',
        'replacementname': '(?P<attr>replacementname)(?P<operator>[~])(?P<value>.+)$',
        'publishedon': '(?P<attr>publishedon)(?P<operator>[<=>])(?P<value>\d+)$',
        'deprecatedon': '(?P<attr>deprecatedon)(?P<operator>[<=>])(?P<value>\d+)$',
        'deletedon': '(?P<attr>deletedon)(?P<operator>[<=>])(?P<value>\d+)$'
    }
    # start with empty result set
    filters = []
    # split the argument into a comma-separated list if supplied...
    if command_arg_filter:
        for phrase in command_arg_filter.split(','):
            # compare each comma-separated 'phrase' against the valid filters
            # defined by regular expressions
            for attr, regex in valid_filters.iteritems():
                match = re.match(regex, phrase)
                if match:
                    filters.append(match.groupdict())
                    break
            else:
                # if we can't break out with a valid filter, warn the user
                __warn("Invalid filter phrase '%s' will be ignored." % phrase)
    # return any valid filters we found
    return filters


def __parse_server_response_data(server_response_data, info_type):
    return json.loads(server_response_data)[info_type]


def __reformat(items, info_type, result_format):
    if result_format == 'json':
        return json.dumps({info_type: items})
    # default to XML output (until we have a plain formatter)
    else:
        # elif result_format == 'xml':
        root = ET.Element(info_type)
        for item in items:
            ET.SubElement(root, __inflect(info_type), item)
        return ET.tostring(root, 'UTF-8', 'xml')


def __select_server_format(result_format, apply_filters=False):
    if apply_filters:
        return 'json'
    elif result_format == 'plain':
        return 'xml'
    else:
        return result_format


def __warn(str, out=sys.stdout):
    out.write("Warning: %s" % str)


def __process(url, info_type, command_arg_filter, result_format):
    # where the magic happens
    """given a URL, the type of information, maybe some filters, and an expected format, do the right thing"""
    server_response_data = __get_data(url)
    if command_arg_filter:
        filters = __parse_command_arg_filter(command_arg_filter)
        superset = __parse_server_response_data(server_response_data, info_type)
        filtered_items = __apply_filters(superset, filters)
        return __reformat(filtered_items, info_type, result_format)
    else:
        return server_response_data


def get_image_data(
        framework,
        image_state,
        result_format='plain',
        region='all',
        command_arg_filter=None):
    """Return the requested image information"""
    info_type = 'images'
    url = __form_url(
        framework,
        info_type,
        result_format,
        region,
        image_state,
        apply_filters=command_arg_filter
    )
    return __process(url, info_type, command_arg_filter, result_format)


def get_server_data(
        framework,
        server_type,
        result_format='plain',
        region='all',
        command_arg_filter=None):
    """Return the requested server information"""
    info_type = 'servers'
    url = __form_url(
        framework,
        info_type,
        result_format,
        region,
        server_type=server_type,
        apply_filters=command_arg_filter
    )
    return __process(url, info_type, command_arg_filter, result_format)