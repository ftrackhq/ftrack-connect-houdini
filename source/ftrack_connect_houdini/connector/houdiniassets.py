import houdinicon
import hou
import ftrack

import os
import copy

from ftrack_connect.connector import (
    FTAssetHandlerInstance,
    HelpFunctions,
    FTAssetType,
    FTComponent
)

from ftrack_connect.connector import panelcom

class GenericAsset(FTAssetType):
    def __init__(self):
        super(GenericAsset, self).__init__()
        self.importAssetBool = False
        self.referenceAssetBool = False

    def importAsset(self, iAObj=None):

        if 'alembic' in iAObj.componentName:
            resultingNode = hou.node('/obj').createNode(
                'alembicarchive', iAObj.assetName)
            resultingNode.parm('buildSubnet').set(False)
            resultingNode.parm('fileName').set(iAObj.filePath)
            hou.hscript(
                "opparm -C {0} buildHierarchy (1)".format(
                    resultingNode.path()))
        elif 'bgeo' in iAObj.componentName:
            geoNode = hou.node('/obj').createNode('geo')
            fileSop = geoNode.children()[0]
            fileSop.parm('file').set(iAObj.filePath)

        else:
            self.importAssetBool = False
            hou.hipFile.load(iAObj.filePath)

        self.addFTab(resultingNode)
        self.setFTab(resultingNode, iAObj)

        return 'Imported ' + iAObj.assetType + ' asset'

    def publishAsset(self, iAObj=None):
        '''Publish the asset defined by the provided *iAObj*.'''

        publishedComponents = []

        panelComInstance = panelcom.PanelComInstance.instance()

        if hasattr(iAObj, 'customComponentName'):
            componentName = iAObj.customComponentName
        else:
            componentName = 'houdiniBinary'

        publishedComponents = []

        temporaryPath = HelpFunctions.temporaryFile(suffix='.hip')

        publishedComponents.append(
            FTComponent(
                componentname=componentName, path=temporaryPath))

        if 'exportMode' in iAObj.options and (
                iAObj.options['exportMode'] == 'Selection'):
            pass
        else:
            hou.hipFile.save(temporaryPath)

        panelComInstance.emitPublishProgressStep()

        return publishedComponents, 'Published ' + iAObj.assetType + ' asset'

    def addFTab(self, resultingNode):
        parm_group = resultingNode.parmTemplateGroup()
        parm_folder = hou.FolderParmTemplate('folder', 'ftrack')
        alembic_folder = parm_group.findFolder('Alembic Loading Parameters')

        components = [
            'componentId', 'componentName', 'assetVersionId',
            'assetVersion', 'assetName', 'assetType', 'assetId'
        ]

        for comp in components:
            parm_folder.addParmTemplate(
                hou.StringParmTemplate(comp, comp, 1, ''))
        if alembic_folder:
            parm_group.insertAfter(alembic_folder, parm_folder)
        else:
            parm_group.append(parm_folder)
        resultingNode.setParmTemplateGroup(parm_group)

    def setFTab(self, resultingNode, iAObj):
        componentId = ftrack.Component(
            iAObj.componentId).getEntityRef()
        assetVersionId = ftrack.AssetVersion(
            iAObj.assetVersionId).getEntityRef()

        components = {
            'componentId': HelpFunctions.safeString(componentId),
            'componentName': HelpFunctions.safeString(iAObj.componentName),
            'assetVersionId': HelpFunctions.safeString(assetVersionId),
            'assetVersion': HelpFunctions.safeString(iAObj.assetVersion),
            'assetName': HelpFunctions.safeString(iAObj.assetName),
            'assetType': HelpFunctions.safeString(iAObj.assetType),
            'assetId': HelpFunctions.safeString(iAObj.assetId)
        }

        for comp in components:
            resultingNode.parm(comp).set(components[comp])

    def getSceneSettingsObj(self, iAObj):
        iAObjCopy = copy.copy(iAObj)
        # iAObjCopy.options['houdiniShaders'] = True
        iAObjCopy.options['exportMode'] = 'All'
        iAObjCopy.customComponentName = 'houdiniScene'
        return iAObjCopy

    def changeVersion(self, iAObj=None, applicationObject=None):
        for n in hou.node('/').allSubChildren():
            if n.name().startswith(applicationObject):
                print iAObj.filePath
                n.parm('fileName').set(
                    HelpFunctions.safeString(iAObj.filePath))
                hou.hscript(
                    "opparm -C {0} buildHierarchy (1)".format(
                        n.path()))
                self.setFTab(n, iAObj)
                return True


class SceneAsset(GenericAsset):
    def __init__(self):
        super(SceneAsset, self).__init__()

    def publishAsset(self, iAObj=None):
        panelComInstance = panelcom.PanelComInstance.instance()
        panelComInstance.setTotalExportSteps(1)
        iAObj.customComponentName = 'hipScene'
        components, message = GenericAsset.publishAsset(self, iAObj)
        return components, message

    @staticmethod
    def importOptions():
        xml = """
        <tab name="Options">
            <row name="Import mode" accepts="houdini">
                <option type="radio" name="importMode">
                    <optionitem name="Import" value="True"/>
                </option>
            </row>
            <row name="Preserve References" accepts="houdini">
                <option type="checkbox" name="houdiniMerge" value="True"/>
            </row>
        </tab>
        """
        return xml

    @staticmethod
    def exportOptions():
        xml = """
        <tab name="Houdini Scene options" accepts="houdini">
            <row name="Houdini Selection Mode" accepts="houdini">
                <option type="radio" name="exportMode">
                        <optionitem name="All" value="True"/>
                        <optionitem name="Selection"/>
                </option>
            </row>
        </tab>
        <tab name="Alembic options">
            <row name="Publish Alembic">
                <option type="checkbox" name="alembic"/>
            </row>
            <row name="Include animation">
                <option type="checkbox" name="alembicAnimation"/>
            </row>
            <row name="Frame range">
                <option type="string" name="frameStart" value="{0}"/>
                <option type="string" name="frameEnd" value="{1}"/>
            </row>
            <row name="Evaluate every">
                <option type="float" name="alembicEval" value="1.0"/>
            </row>
            <row name="Alembic Selection Mode" accepts="maya">
                <option type="radio" name="alembicExportMode">
                        <optionitem name="All"/>
                        <optionitem name="Selection" value="True"/>
                </option>
            </row>
        </tab>
        """
        s = os.getenv('FS')
        e = os.getenv('FE')
        xml = xml.format(s, e)
        return xml


class GeometryAsset(GenericAsset):
    def __init__(self):
        super(GeometryAsset, self).__init__()

    def importAsset(self, iAObj=None):
        GenericAsset.importAsset(self, iAObj)

    def changeVersion(self, iAObj=None, applicationObject=None):
        return GenericAsset.changeVersion(self, iAObj, applicationObject)

    def publishAsset(self, iAObj=None):
        publishedComponents = []
        geometryComponents = GenericAsset.publishAsset(self, iAObj)
        publishedComponents += geometryComponents

        return publishedComponents, 'Published GeometryAsset asset'


# class CameraAsset(GenericAsset):
#     def __init__(self):
#         super(GeometryAsset, self).__init__()

#     def importAsset(self, iAObj=None):
#         GenericAsset.importAsset(self, iAObj)

#     def changeVersion(self, iAObj=None, applicationObject=None):
#         return GenericAsset.changeVersion(self, iAObj, applicationObject)

#     def publishAsset(self, iAObj=None):
#         publishedComponents = []
#         geometryComponents = GenericAsset.publishAsset(self, iAObj)
#         publishedComponents += geometryComponents

#         return publishedComponents, 'Published GeometryAsset asset'


def registerAssetTypes():
    assetHandler = FTAssetHandlerInstance.instance()
    assetHandler.registerAssetType(name='geo', cls=GeometryAsset)
    # assetHandler.registerAssetType(name='cam', cls=CameraAsset)
    assetHandler.registerAssetType(name='scene', cls=SceneAsset)
