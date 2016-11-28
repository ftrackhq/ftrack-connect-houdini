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

        if (
            iAObj.componentName == 'alembic' or
            iAObj.filePath.endswith('abc')
        ):
            resultingNode = hou.node('/obj').createNode(
                'alembicarchive', iAObj.assetName)
            resultingNode.parm('buildSubnet').set(False)
            resultingNode.parm('fileName').set(iAObj.filePath)
            hou.hscript(
                "opparm -C {0} buildHierarchy (1)".format(
                    resultingNode.path()))
            self.addFTab(resultingNode)
            self.setFTab(resultingNode, iAObj)

        # TODO: Add import Bgeo
        # elif 'bgeo' in iAObj.componentName:
        #     geoNode = hou.node('/obj').createNode('geo')
        #     fileSop = geoNode.children()[0]
        #     fileSop.parm('file').set(iAObj.filePath)

        elif iAObj.componentName == 'houdiniPublishScene':
            # Load Houdini Published Scene

            self.importAssetBool = False
            hou.hipFile.load(iAObj.filePath)

        elif iAObj.componentName == 'houdiniNodes':
            # Import Published Houdini Nodes

            resultingNode = hou.node('/obj').createNode(
                'subnet', iAObj.assetName)
            resultingNode.loadChildrenFromFile(iAObj.filePath)
            resultingNode.setSelected(1)
            self.addFTab(resultingNode)
            self.setFTab(resultingNode, iAObj)

        else:
            self.importAssetBool = False
            hou.hipFile.load(iAObj.filePath)

        return 'Imported ' + iAObj.assetType + ' asset'

    def publishAsset(self, iAObj=None):
        '''Publish the asset defined by the provided *iAObj*.'''

        panelComInstance = panelcom.PanelComInstance.instance()

        if hasattr(iAObj, 'customComponentName'):
            componentName = iAObj.customComponentName
        else:
            componentName = 'houdiniNodes'

        publishedComponents = []

        temporaryPath = HelpFunctions.temporaryFile(suffix='.hip')

        publishedComponents.append(
            FTComponent(
                componentname=componentName,
                path=temporaryPath
            )
        )

        if 'exportMode' in iAObj.options and (
                iAObj.options['exportMode'] == 'Selection') and (
                    componentName == 'houdiniNodes'):
            ''' Publish Selected Nodes'''
            selectednodes = hou.selectedNodes()
            selectednodes[0].parent().saveChildrenToFile(
                selectednodes, [], temporaryPath)

            panelComInstance.emitPublishProgressStep()

        elif componentName == 'houdiniPublishScene' and (
                iAObj.options['exportMode'] == 'Selection'):
            # Publisdh Main Scene in selection mode
            hou.copyNodesToClipboard(hou.selectedNodes())

            command = "hou.pasteNodesFromClipboard(hou.node('/obj'));\
            hou.hipFile.save('%s')" % (temporaryPath)

            cmd = '%s -c "%s"' % (os.path.join(
                os.getenv('HFS'), 'bin', 'hython'), command)
            os.system(cmd)

        elif componentName == 'houdiniPublishScene':
            # Publisdh Main Scene
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
        iAObjCopy.options['exportMode'] = 'All'
        iAObjCopy.customComponentName = 'houdiniPublishScene'
        return iAObjCopy

    def changeVersion(self, iAObj=None, applicationObject=None):
        for n in hou.node('/').allSubChildren():
            if n.name().startswith(applicationObject):
                if iAObj.componentName == 'alembic':
                    n.parm('fileName').set(
                        HelpFunctions.safeString(iAObj.filePath))
                    hou.hscript(
                        "opparm -C {0} buildHierarchy (1)".format(
                            n.path()))
                    self.setFTab(n, iAObj)
                    return True
                elif iAObj.componentName == 'houdiniNodes':
                    results = n.glob('*')
                    for del_n in results:
                        del_n.destroy()
                    n.loadChildrenFromFile(iAObj.filePath)
                    n.setSelected(1)
                    self.setFTab(n, iAObj)
                    return True


class SceneAsset(GenericAsset):
    def __init__(self):
        super(SceneAsset, self).__init__()

    def publishAsset(self, iAObj=None):
        panelComInstance = panelcom.PanelComInstance.instance()
        panelComInstance.setTotalExportSteps(1)
        iAObj.customComponentName = 'houdiniPublishScene'
        components, message = GenericAsset.publishAsset(self, iAObj)
        return components, message

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
        """
        return xml


class GeometryAsset(GenericAsset):
    def __init__(self):
        super(GeometryAsset, self).__init__()

    def importAsset(self, iAObj=None):
        GenericAsset.importAsset(self, iAObj)

    def changeVersion(self, iAObj=None, applicationObject=None):
        '''Change the version of the asset defined in *iAObj*
        and *applicationObject*
        '''
        return GenericAsset.changeVersion(self, iAObj, applicationObject)

    def publishAsset(self, iAObj=None):
        '''Publish the asset defined by the provided *iAObj*.'''

        publishedComponents = []

        totalSteps = self.getTotalSteps(
            steps=[
                iAObj.options['houdiniNodes'],
                iAObj.options['alembic'],
                iAObj.options['houdiniPublishScene']
            ]
        )
        panelComInstance = panelcom.PanelComInstance.instance()
        panelComInstance.setTotalExportSteps(totalSteps)

        if iAObj.options['houdiniNodes']:
            houdiniComponents, message = GenericAsset.publishAsset(
                self, iAObj
            )
            publishedComponents += houdiniComponents

        if iAObj.options.get('houdiniPublishScene'):
            iAObjCopy = self.getSceneSettingsObj(iAObj)
            sceneComponents, message = GenericAsset.publishAsset(
                self, iAObjCopy
            )
            publishedComponents += sceneComponents

        if iAObj.options.get('alembic'):
            ''' Export Alembic'''
            temporaryPath = HelpFunctions.temporaryFile(suffix='.abc')

            publishedComponents.append(
                FTComponent(
                    componentname='alembic',
                    path=temporaryPath
                )
            )

            objPath = hou.node('/obj')

            # Selection Objects Set
            if iAObj.options.get('alembicExportMode') == 'Selection':
                selectednodes = hou.selectedNodes()
                objects = ' '.join([x.path() for x in selectednodes])
            else:
                selectednodes = objPath.glob('*')
                objects = '*'

            # Create Rop Net
            ropNet = objPath.createNode('ropnet')
            abcRopnet = ropNet.createNode('alembic')

            if iAObj.options.get('alembicAnimation'):
                # Check Alembic for animation option
                abcRopnet.parm('trange').set(1)
                for i, x in enumerate(
                        ['frameStart', 'frameEnd', 'alembicEval']):
                    abcRopnet.parm('f%s' % i + 1).deleteAllKeyframes()
                    abcRopnet.parm('f%s' % i + 1).set(iAObj.options[x])
            else:
                abcRopnet.parm('trange').set(0)

            abcRopnet.parm('filename').set(temporaryPath)
            abcRopnet.parm('root').set(selectednodes[0].parent().path())
            abcRopnet.parm('objects').set(objects)
            abcRopnet.parm('format').set('hdf5')
            abcRopnet.render()
            ropNet.destroy()

            panelComInstance.emitPublishProgressStep()

        return publishedComponents, 'Published GeometryAsset asset'

    @staticmethod
    def exportOptions():
        xml = """
        <tab name="Houdini Scene options" accepts="houdini">
            <row name="Attach scene to asset" accepts="houdini">
                <option type="checkbox" name="houdiniPublishScene" value="False"/>
            </row>
            <row name="Houdini binary" accepts="houdini">
                <option type="checkbox" name="houdiniNodes" value="True"/>
            </row>
            <row name="Houdini Selection Mode" accepts="houdini">
                <option type="radio" name="exportMode">
                        <optionitem name="All"/>
                        <optionitem name="Selection" value="True"/>
                </option>
            </row>
        </tab>
        <tab name="Alembic options">
            <row name="Publish Alembic">
                <option type="checkbox" name="alembic" value="True"/>
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
            <row name="Alembic Selection Mode" accepts="houdini">
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


def registerAssetTypes():
    assetHandler = FTAssetHandlerInstance.instance()
    assetHandler.registerAssetType(name='scene', cls=SceneAsset)
    assetHandler.registerAssetType(name='geo', cls=GeometryAsset)
