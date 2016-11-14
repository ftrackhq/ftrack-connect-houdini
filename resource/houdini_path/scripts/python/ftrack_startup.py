# -*- coding: utf-8 -*-
# @Author: datsik
# @Date:   2016-07-13 15:08:58
# @Last Modified by:   datsik
# @Last Modified time: 2016-07-13 18:25:35


# import sys
import os
import hou
import ftrack

# import functools

from ftrack_connect.ui.widget.import_asset import FtrackImportAssetDialog
from ftrack_connect.ui.widget.asset_manager import FtrackAssetManagerDialog


from ftrack_connect_houdini.connector import Connector
from ftrack_connect_houdini.ui.info import FtrackHoudiniInfoDialog
from ftrack_connect_houdini.ui.publisher import PublishAssetDialog
from ftrack_connect_houdini.ui.tasks import FtrackTasksDialog

connector = Connector()

currentEntity = ftrack.Task(
    os.getenv('FTRACK_TASKID',
              os.getenv('FTRACK_SHOTID')
              )
)


def FtrackDialogs(panel_id):

    ftrack_id = 'Ftrack_ID'

    panel_interface = None

    try:
        for interface, value in hou.pypanel.interfaces().items():
            if interface == panel_id:
                panel_interface = value
                break
    except hou.OperationFailed:
        print 'Something Wrong with Python Pannel'

    main_tab = hou.ui.curDesktop().findPaneTab(ftrack_id)

    if main_tab:
        panel = main_tab.pane().createTab(hou.paneTabType.PythonPanel)
        panel.showToolbar(False)
        panel.setActiveInterface(panel_interface)

        print 'This is Starta'
    else:
        if panel_interface:
            hou.hscript("pane -S -m pythonpanel -o -n %s" % ftrack_id)
            panel = hou.ui.curDesktop().findPaneTab(ftrack_id)
            panel.showToolbar(False)
            panel.setActiveInterface(panel_interface)


def showInfoDialog():
    dialog = FtrackHoudiniInfoDialog(connector=connector)

    return dialog


def showTaskDialog():
    dialog = FtrackTasksDialog(connector=connector)

    return dialog


def showImportAssetDialog():
    dialog = FtrackImportAssetDialog(connector=connector)

    return dialog


def showAssetManagerDialog():
    dialog = FtrackAssetManagerDialog(connector=connector)

    return dialog


def showPublishDialog():
    connector.registerAssets()

    dialog = PublishAssetDialog(
        currentEntity=currentEntity, connector=connector)

    return dialog
