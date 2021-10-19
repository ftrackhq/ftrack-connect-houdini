# :coding: utf-8
# :copyright: Copyright (c) 2016 Postmodern Digital

import getpass
import sys
import logging
import os
import platform
import functools

import ftrack_api


cwd = os.path.dirname(__file__)
sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))

logger = logging.getLogger('ftrack_connect_houdini.hook')

def on_discover_houdini_integration(session, event):
    sys.path.append(sources)

    from ftrack_connect_houdini import __version__ as integration_version

    data = {
        'integration': {
            'name': 'ftrack-connect-houdini',
            'version': integration_version
        }
    }

    # Make sure app supports python 2
    app_path = event['data']['application']['path']

    if platform.system() == 'Windows':
        if os.path.exists(os.path.join(app_path, 'python37')):
            logger.debug('Not discovering non-py2k Houdini build ("{0}").'.format(
                app_path))
            data['integration']['disable'] = True
    elif platform.system() == 'Darwin':
        # Check that Python framework link points to a certain target
        link_path = os.path.join(app_path, '../Frameworks/Python.framework/Versions/Current')
        value = os.readlink(link_path)
        if value.split('.')[0] != '2':
            logger.debug('Not discovering non-py2k Houdini build ("{0}",'
                ' linked interpreter: {1}).'.format(app_path, value))
            data['integration']['disable'] = True
    elif platform.system() == 'Linux':
        # Check if python 2.7 library exists
        app_path = os.path.dirname(os.path.dirname(app_path))
        lib_path = os.path.join(app_path, 'python/lib/python2.7')
        if not os.path.exists(lib_path):
            logger.debug('Not discovering non-py2k Houdini build ("{0}").'.format(
                app_path))
            data['integration']['disable'] = True

    return data

def on_launch_houdini_integration(session, event):
    hou_base_data = on_discover_houdini_integration(session, event)

    ftrack_connect_houdini_resource_path = os.path.abspath(os.path.join(cwd, '..',  'resource'))
    houdini_connect_plugins = os.path.join( ftrack_connect_houdini_resource_path, 'houdini_path')

    # In HOUDINI_PATH, & is a special character meaning the default path
    # see : http://www.sidefx.com/docs/houdini/basics/config_env.html


    hou_base_data['integration']['env'] = {
        'PYTHONPATH.prepend': os.path.pathsep.join([houdini_connect_plugins, sources]),
        'HOUDINI_PATH': os.path.pathsep.join([houdini_connect_plugins, '&']),
        'QT_PREFERRED_BINDING':  os.pathsep.join(['PySide2', 'PySide']),
        'LOGNAME.set': session._api_user,
        'FTRACK_APIKEY.set': session._api_key
    }

    selection = event['data'].get('context', {}).get('selection', [])
    
    if selection:
        task = session.get('Context', selection[0]['entityId'])
        hou_base_data['integration']['env']['FTRACK_TASKID.set'] =  task['id']
        hou_base_data['integration']['env']['FTRACK_SHOTID.set'] =  task['parent']['id']
        hou_base_data['integration']['env']['FS.set'] = task['parent']['custom_attributes'].get('fstart', '1.0')
        hou_base_data['integration']['env']['FE.set'] = task['parent']['custom_attributes'].get('fend', '100.0')

        
    return hou_base_data

def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return


    handle_discovery_event = functools.partial(
        on_discover_houdini_integration,
        session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover'
        ' and data.application.identifier=houdini*',
        handle_discovery_event
    )

    handle_launch_event = functools.partial(
        on_launch_houdini_integration,
        session
    )    

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch'
        ' and data.application.identifier=houdini*',
        handle_launch_event
    )
    