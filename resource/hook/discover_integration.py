# :coding: utf-8
# :copyright: Copyright (c) 2016 Postmodern Digital

import getpass
import sys
import pprint
import logging
import os
import functools

import ftrack_api



def on_discover_houdini_integration(session, event):

    cwd = os.path.dirname(__file__)
    sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))
    ftrack_connect_houdini_resource_path = os.path.abspath(os.path.join(cwd, '..',  'resource'))
    houdini_connect_plugins = os.path.join(
        ftrack_connect_houdini_resource_path, 'houdini_path'
    )
    sys.path.insert(0, sources)

    entity = event['data']['context']['selection'][0]

    task = session.get('Context', entity['entityId'])

    from ftrack_connect_houdini import __version__ as integration_version

    # In HOUDINI_PATH, & is a special character meaning the default path
    # see : http://www.sidefx.com/docs/houdini/basics/config_env.html

    data = {
        'integration': {
            'name': 'ftrack-connect-houdini',
            'version': integration_version,
            'env': {
                'PYTHONPATH.prepend': os.path.pathsep.join([houdini_connect_plugins,sources]),
                'HOUDINI_PATH': os.path.pathsep.join([houdini_connect_plugins, '&']),
                'QT_PREFERRED_BINDING':  os.pathsep.join(['PySide2', 'PySide']),
                'FTRACK_TASKID.set': task['id'],
                'FTRACK_SHOTID.set': task['parent']['id'],
                'LOGNAME.set': session._api_user,
                'FTRACK_APIKEY.set': session._api_key,
                'FS.set': task['parent']['custom_attributes'].get('fstart', '1.0'),
                'FE.set': task['parent']['custom_attributes'].get('fend', '100.0')
            }
        }
    }
    return data



def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return


    handle_event = functools.partial(
        on_discover_houdini_integration,
        session
    )
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch'
        ' and data.application.identifier=houdini*',
        handle_event
    )
    
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover'
        ' and data.application.identifier=houdini*',
        handle_event
    )