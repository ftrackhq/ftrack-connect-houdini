# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import uuid

import hou
import toolutils

# import houdini.cmds as mc
# import houdini.OpenhoudiniUI as mui
# import houdini.mel as mm
# from pymel.core.uitypes import pysideWrapInstance

from ftrack_connect.connector import base as maincon
from ftrack_connect.connector import FTAssetHandlerInstance


class Connector(maincon.Connector):
    def __init__(self):
        super(Connector, self).__init__()

    @staticmethod
    def getAssets():
        componentIds = []
        return componentIds

    @staticmethod
    def getFileName():
        return 'dummyTestScene'

    @staticmethod
    def getMainWindow():
        return None

    @staticmethod
    def importAsset(iAObj):
        iAObj.assetName = iAObj.assetType.upper() + "_" + iAObj.assetName + "_AST"
        # Check if this AssetName already exists in scene
        # iAObj.assetName = Connector.getUniqueSceneName(iAObj.assetName)

        assetHandler = FTAssetHandlerInstance.instance()
        importAsset = assetHandler.getAssetClass(iAObj.assetType)
        if importAsset:
            result = importAsset.importAsset(iAObj)
            return result
        else:
            return 'assetType not supported'

    @staticmethod
    def selectObject(applicationObject=''):
        print applicationObject
        pass

    @staticmethod
    def selectObjects(selection):
        print selection
        pass

    @staticmethod
    def removeObject(applicationObject=''):
        print applicationObject
        pass

    @staticmethod
    def changeVersion(applicationObject=None, iAObj=None):
        if iAObj.assetType in ['rig', 'light']:
            changeAsset = houdiniassets.GenericAsset()
        elif iAObj.assetType in ['geo']:
            changeAsset = houdiniassets.GeometryAsset()
        else:
            print 'assetType not supported'
            return False

        result = changeAsset.changeVersion(iAObj, applicationObject)
        return result

    @staticmethod
    def getSelectedObjects():
        selectedObjects = ['horse', 'pig', 'donkey', 'cat', 'dog']
        print selectedObjects
        return selectedObjects

    @staticmethod
    def getSelectedAssets():
        selectedObjects = ['horse', 'pig', 'donkey']
        print selectedObjects
        return selectedObjects

    @staticmethod
    def setNodeColor(applicationObject='', latest=True):
        pass

    @staticmethod
    def publishAsset(iAObj=None):
        assetHandler = FTAssetHandlerInstance.instance()
        pubAsset = assetHandler.getAssetClass(iAObj.assetType)
        if pubAsset:
            publishedComponents, message = pubAsset.publishAsset(iAObj)
            return publishedComponents, message
        else:
            return [], 'assetType not supported'

    @staticmethod
    def init_dialogs(ftrackDialogs, availableDialogs=[]):
        # Cant init dialogs in cinema mode
        if not Connector.batch():
            return
        print ftrackDialogs
        print availableDialogs
        return

    @staticmethod
    def getConnectorName():
        return 'houdini'

    @staticmethod
    def getUniqueSceneName(assetName):
        print assetName
        return assetName

    @staticmethod
    def getReferenceNode(assetLink):
        print assetLink
        pass

    @classmethod
    def registerAssets(cls):
        '''Register all the available assets'''
        import houdiniassets
        houdiniassets.registerAssetTypes()
        super(Connector, cls).registerAssets()

    @staticmethod
    def executeInThread(function, arg):
        '''Execute the given *function* with provided *args* in a separate thread
        '''
        # import houdini.utils
        # houdini.utils.executeInMainThreadWithResult(function, arg)
        pass

    # Make certain scene validations before actualy publishing
    @classmethod
    def prePublish(cls, iAObj):
        '''Pre Publish check for given *iAObj*'''
        result, message = super(Connector, cls).prePublish(iAObj)
        if not result:
            return result, message

        nodes = hou.selectedNodes()
        if len(nodes) == 0:
            if (
                'exportMode' in iAObj.options and
                iAObj.options['exportMode'] == 'Selection'
            ):
                return None, 'Nothing selected'
            if (
                'alembicExportMode' in iAObj.options and
                iAObj.options['alembicExportMode'] == 'Selection'
            ):
                return None, 'Nothing selected'

        return True, ''

    @staticmethod
    def takeScreenshot():
        '''Take a screenshot and save it in the temp folder'''
        import tempfile

        res = [1024, 768]

        filename = "%s.jpg" % (os.path.join(
            tempfile.gettempdir(), str(uuid.uuid4())))

        desktop = hou.ui.curDesktop()
        scene_view = toolutils.sceneViewer()

        if scene_view is None or scene_view.type() != hou.paneTabType.SceneViewer:
            raise hou.Error("No scene view available to flipbook")
        viewport = scene_view.curViewport()

        if viewport.camera() is not None:
            res = [viewport.camera().parm('resx').eval(),
                   viewport.camera().parm('resy').eval()]

        view = '%s.%s.world.%s' % (
            desktop.name(), scene_view.name(), viewport.name())

        executeCommand = "viewwrite -c -f 0 1 -r %s %s %s %s" % (
            res[0], res[1], view, filename)

        print executeCommand

        hou.hscript(executeCommand)
        return filename
