import os
import hou
import ftrack
import tempfile

from ftrack_connect.ui.widget.import_asset import FtrackImportAssetDialog
from ftrack_connect.ui.widget.asset_manager import FtrackAssetManagerDialog


from ftrack_connect_houdini.connector import Connector
from ftrack_connect_houdini.ui.info import FtrackHoudiniInfoDialog
from ftrack_connect_houdini.ui.publisher import PublishAssetDialog
from ftrack_connect_houdini.ui.tasks import FtrackTasksDialog

connector = Connector()
connector.registerAssets()

currentEntity = ftrack.Task(
    os.getenv('FTRACK_TASKID',
              os.getenv('FTRACK_SHOTID')
              )
)


def writePypanel(pan_name, pan_start):

    xml = """<?xml version="1.0" encoding="UTF-8"?>
<pythonPanelDocument>
  <interface name="{0}" label="{0}" icon="MISC_python" help_url="">
    <script><![CDATA[

import ftrack_startup

def createInterface():

    info_view = ftrack_startup.{1}()

    return info_view]]></script>
    <help><![CDATA[]]></help>
  </interface>
</pythonPanelDocument>"""

    xml = xml.format(pan_name, pan_start)

    path = os.path.join(tempfile.gettempdir(), '%s.pypanel' % pan_name)
    if os.path.exists(path):
        pass
    else:
        f = open(path, 'w')
        f.write(xml)
        f.close()
    return path


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
    connector = Connector()
    dialog = FtrackAssetManagerDialog(connector=connector)

    return dialog


def showPublishDialog():

    dialog = PublishAssetDialog(
        currentEntity=currentEntity, connector=connector)

    return dialog
