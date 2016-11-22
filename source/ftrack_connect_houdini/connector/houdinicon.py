# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import uuid
import urlparse

import hou
import toolutils

import _alembic_hom_extensions as abc

from ftrack_connect.connector import base as maincon
from ftrack_connect.connector import FTAssetHandlerInstance, HelpFunctions


class Connector(maincon.Connector):
    def __init__(self):
        super(Connector, self).__init__()

    @staticmethod
    def bakeAnim(
            node, frameRange, bakeParms=[],
            parentNode=hou.node('/obj'), byChop=False):

        position = node.position()

        # bake anim to keyframe by chop
        if byChop:
            tempChopnet = hou.node('/obj').createNode('chopnet')
            objectChop = tempChopnet.createNode('object')
            [objectChop.parm(k).set(v) for k, v in zip(
                [
                    'targetpath', 'compute',
                    'samplerate', 'start', 'end', 'units'],
                [
                    node.path(), 'fullxform', hou.fps(),
                    frameRange[0], frameRange[1], 'frames'])]

        trsParms = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']

        if node.type().name() == 'cam':
            bakedNode = parentNode.createNode(
                'cam', node_name=node.name() + "_bake")

            [bakedNode.parm('resx').set(node.parm('resx').eval()),
                bakedNode.parm('resy').set(node.parm('resy').eval())]
            bakedNode.setPosition(
                hou.Vector2((position[0] + 1, position[1] - 1)))

        elif not node.type().name() == 'cam':
            bakedNode = hou.copyNodesTo([node], parentNode)[0]
            bakedNode.setInput(0, None)
            [[bakedNode.parm(parmName).deleteAllKeyframes(),
                bakedNode.parm(parmName).set(0)] for parmName in bakeParms]
            bakedNode.setName('animation:' + node.name(), unique_name=True)
            bakedNode.parm("keeppos").set(0)
            bakedNode.movePreTransformIntoParmTransform()
            bakedNode.setPosition(
                hou.Vector2((position[0] + 1, position[1] + 1)))

        for frame in xrange(int(frameRange[0]), int(frameRange[1]) + 1):
            time = (frame - 1) / hou.fps()

            tsrMatrix = node.worldTransformAtTime(time)
            for parm, value in zip(
                trsParms, (list(tsrMatrix.extractTranslates('srt')) + list(
                    tsrMatrix.extractRotates(
                        transform_order='srt', rotate_order='xyz')) + list(
                    tsrMatrix.extractScales(transform_order='srt')))):
                if parm in bakeParms:
                    if not byChop:
                        bakedNode.parm(parm).setKeyframe(
                            hou.Keyframe(value, time))
                    else:
                        bakedNode.parm(parm).setKeyframe(
                            hou.Keyframe(objectChop.track(
                                parm).evalAtFrame(frame), time))

            if bakeParms != []:
                for parm, value in zip(
                    bakeParms, [node.parm(p).evalAtFrame(
                        frame) for p in bakeParms]):
                    if parm not in trsParms:
                        bakedNode.parm(parm).setKeyframe(
                            hou.Keyframe(value, time))

        if byChop:
            tempChopnet.destroy()

        return bakedNode

    @staticmethod
    def importCamFromAbc(
            filepath, importAsBakedCam=False, scaleFactor=1, resolution=[]):
        camXformPath = abc.alembicGetObjectPathListForMenu(filepath)[2]
        camShapePath = abc.alembicGetObjectPathListForMenu(filepath)[4]

        # sampleTime = hou.frame()/hou.fps()
        trsName = camShapePath.split('/')[-2]
        shapeName = camShapePath.split('/')[-1]

        abcXform = hou.node('/obj/').createNode('alembicxform', trsName)
        abcXform.parm('fileName').set(filepath)
        abcXform.parm('frame').setExpression('$FF')
        abcXform.parm('fps').deleteAllKeyframes()
        abcXform.parm('fps').setExpression('$FPS')
        abcXform.parm('objectPath').set(camXformPath)
        cam = abcXform.createNode('cam', shapeName)
        cam.setInput(0, abcXform.indirectInputs()[0])

        focalPyExps = '__import__("_alembic_hom_extensions")\
        .alembicGetCameraDict(hou.parent().parm("fileName").eval(),\
         "%s", hou.frame()/hou.fps()).get("focal")' % camShapePath
        aperturePyExps = '__import__("_alembic_hom_extensions")\
        .alembicGetCameraDict(hou.parent().parm("fileName").eval(),\
         "%s", hou.frame()/hou.fps()).get("aperture") \
        *max(1, (hou.pwd().parm("resx").eval()/hou.pwd().parm("resy")\
        .eval()*hou.pwd().parm("aspect").eval())*3./4) ' % camShapePath
        cam.parm('focal').setExpression(
            focalPyExps, language=hou.exprLanguage.Python)
        cam.parm('aperture').setExpression(
            aperturePyExps, language=hou.exprLanguage.Python)

        if not importAsBakedCam:
            return abcXform
        else:
            if scaleFactor != 1:
                nullScale = abcXform.createInputNode(0, 'null')
                nullScale.parm('scale').set(scaleFactor)
            bakedCam = Connector.bakeAnim(
                cam,
                [hou.playbar.playbackRange()[0],
                    hou.playbar.playbackRange()[1]], bakeParms=[
                        'tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz',
                        'focal', 'aperture', 'resx', 'resy'], byChop=True)
            if scaleFactor != 1:
                nullScale.destroy()
            if resolution != []:
                for parmName in ['resx', 'resy']:
                    bakedCam.parm(parmName).deleteAllKeyframes()
                for parmName, res in zip(['resx', 'resy'], resolution):
                    bakedCam.parm(parmName).set(res)
                for parmName in ['resx', 'resy']:
                    bakedCam.parm(parmName).lock(True)
            abcXform.destroy()
            bakedCam.setName(trsName, unique_name=True)
            return {'status':True, 'message':'Cam imported ' + bakedCam.name(), 'output':bakedCam}

    @staticmethod
    def setTimeLine():
        '''Set time line to FS , FE environment values'''
        import ftrack
        start_frame = float(os.getenv('FS'))
        end_frame = float(os.getenv('FE'))
        shot_id = os.getenv('FTRACK_SHOTID')
        shot = ftrack.Shot(id=shot_id)
        handles = float(shot.get('handles'))
        fps = shot.get('fps')

        print 'setting timeline to %s %s ' % (start_frame, end_frame)

        # add handles to start and end frame
        hsf = start_frame - handles
        hef = end_frame + handles

        hou.setFps(fps)
        hou.setFrame(hsf)

        try:
            if start_frame != end_frame:
                hou.hscript("tset {0} {1}".format(hsf / fps,
                            hef / fps))
                hou.playbar.setPlaybackRange(hsf, hef)
        except IndexError:
            pass

    @staticmethod
    def getAssets():
        '''Return the available assets in scene, return the *componentId(s)*'''
        componentIds = []

        for n in hou.node('/').allSubChildren():
            if n.parmTemplateGroup().findFolder('ftrack'):
                valueftrackId = n.parm('componentId').eval()
                if valueftrackId != '':
                    if 'ftrack://' in valueftrackId:
                        url = urlparse.urlparse(valueftrackId)
                        valueftrackId = url.netloc
                        componentIds.append((valueftrackId, n.name()))

        # print componentIds
        return componentIds

    @staticmethod
    def getFileName():
        '''Return the *current scene* name'''
        return hou.hipFile.path()

    @staticmethod
    def getMainWindow():
        return None

    @staticmethod
    def importAsset(iAObj):
        iAObj.assetName = "%s_%s_AST" % (
            iAObj.assetType.upper(),
            iAObj.assetName)
        # Check if this AssetName already exists in scene
        # Need to Done!
        assetHandler = FTAssetHandlerInstance.instance()
        importAsset = assetHandler.getAssetClass(iAObj.assetType)
        if importAsset:
            result = importAsset.importAsset(iAObj)
            return result
        else:
            return 'assetType not supported'

    @staticmethod
    def selectObject(applicationObject=''):
        for n in hou.node('/').allSubChildren():
            if n.name() == applicationObject:
                n.setSelected(1, True)

    @staticmethod
    def selectObjects(selection):
        '''Return the selected nodes'''
        return hou.selectedNodes()

    @staticmethod
    def removeObject(applicationObject=''):
        for n in hou.node('/').allSubChildren():
            if n.name() == applicationObject:
                n.destroy()

    @staticmethod
    def changeVersion(applicationObject=None, iAObj=None):
        assetHandler = FTAssetHandlerInstance.instance()
        changeAsset = assetHandler.getAssetClass(iAObj.assetType)
        if changeAsset:
            result = changeAsset.changeVersion(
                iAObj, applicationObject
            )
            return result
        else:
            print 'assetType not supported'
            return False

    @staticmethod
    def getSelectedObjects():
        return hou.selectedNodes()

    @staticmethod
    def getSelectedAssets():
        selection = hou.selectedNodes()
        selectedObjects = []
        for node in selection:
            try:
                node.parm('componentId').eval()
                selectedObjects.append(node.name())
            except:
                pass
        return selectedObjects

    @staticmethod
    def setNodeColor(applicationObject='', latest=True):
        latestColor = hou.Color(hou.Vector3(0.07, 0.63, 0.29))
        oldColor = hou.Color(hou.Vector3(0.89, 0.39, 0.08))
        for n in hou.node('/').allSubChildren():
            if n.name() == applicationObject:
                if latest:
                    n.setColor(latestColor)
                else:
                    n.setColor(oldColor)

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
        assetName = assetName
        for n in hou.node('/').allSubChildren():
            if n.name().startswith(
                    HelpFunctions.safeString(assetName)):
                if n:
                    i = 0
                    while n:
                        uniqueAssetName = assetName + str(i)
                        if n.name().startswith(
                                HelpFunctions.safeString(uniqueAssetName)):
                            i = i + 1
                    return uniqueAssetName
                else:
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
        function(arg)

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

        if scene_view is None or (
                scene_view.type() != hou.paneTabType.SceneViewer):
            raise hou.Error("No scene view available to flipbook")
        viewport = scene_view.curViewport()

        if viewport.camera() is not None:
            res = [viewport.camera().parm('resx').eval(),
                   viewport.camera().parm('resy').eval()]

        view = '%s.%s.world.%s' % (
            desktop.name(), scene_view.name(), viewport.name())

        executeCommand = "viewwrite -c -f 0 1 -r %s %s %s %s" % (
            res[0], res[1], view, filename)

        hou.hscript(executeCommand)
        return filename
