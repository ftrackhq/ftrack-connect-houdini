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
        if iAObj.componentName == 'alembic':
            pass
        else:
            self.importAssetBool = False
            nameSpaceStr = iAObj.options.get('nameSpaceStr', None) or iAObj.assetType.upper()
            importType = 'houdiniBinary'
            hou.hipFile.load(iAObj.filePath)

        return 'Imported ' + iAObj.assetType + ' asset'


    def publishAsset(self, iAObj=None):
        panelComInstance = panelcom.PanelComInstance.instance()

        if hasattr(iAObj, 'customComponentName'):
            componentName = iAObj.customComponentName
        else:
            componentName = 'houdiniBinary'

        # channels = True

        # if 'houdiniHistory' in iAObj.options and iAObj.options['houdiniHistory']:
        #     constructionHistory = iAObj.options['houdiniHistory']

        publishedComponents = []

        temporaryPath = HelpFunctions.temporaryFile(suffix='.hip')

        publishedComponents.append(
            FTComponent(
                componentname=componentName, path=temporaryPath))

        if 'exportMode' in iAObj.options and iAObj.options['exportMode'] == 'Selection':
            print "Fuck"
        else:
            hou.hipFile.save(temporaryPath)


        panelComInstance.emitPublishProgressStep()

        return publishedComponents, 'Published ' + iAObj.assetType + ' asset'

    def getSceneSettingsObj(self, iAObj):
        iAObjCopy = copy.copy(iAObj)
        # iAObjCopy.options['houdiniShaders'] = True
        iAObjCopy.options['exportMode'] = 'All'
        iAObjCopy.customComponentName = 'houdiniScene'
        return iAObjCopy

    def changeVersion(self, iAObj=None, applicationObject=None):
        pass


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
        <tab name="Options">
            <row name="Export" accepts="houdini">
                <option type="radio" name="exportMode">
                        <optionitem name="All" value="True"/>
                </option>
            </row>
        </tab>
        """
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

def registerAssetTypes():
    assetHandler = FTAssetHandlerInstance.instance()
    assetHandler.registerAssetType(name='geo', cls=GeometryAsset)
    # assetHandler.registerAssetType(name='cam', cls=GenericAsset)
    assetHandler.registerAssetType(name='scene', cls=SceneAsset)
