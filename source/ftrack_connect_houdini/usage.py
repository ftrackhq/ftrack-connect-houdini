# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import ftrack_connect_houdini
import ftrack_connector_legacy.usage


def send_event(event_name, metadata=None):
    '''Send usage information to server.'''

    if metadata is None:
        metadata = {
            'ftrack_connect_houdini_version': ftrack_connect_houdini.__version__
        }

    ftrack_connector_legacy.usage.send_event(
        event_name, metadata
    )
