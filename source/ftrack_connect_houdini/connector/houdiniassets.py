import hou

import ftrack

import os
import copy
import subprocess

from ftrack_connect.connector import (
    FTAssetHandlerInstance,
    HelpFunctions,
    FTAssetType,
    FTComponent
)

from ftrack_connect.connector import panelcom


class GenericAsset(FTAssetType):
    FBX_EXPORT_OPTIONS = """
                <row name="ASCII">
                    <option type="checkbox" name="fbxASCII" value="True"/>
                </row>
                <row name="SDK Version" accepts="houdini">
                    <option type="combo" name="fbxSDKVersion">
                            <optionitem name="FBX | FBX201600 {FBX | FBX201600}"/>
                            <optionitem name="FBX | FBX201400 {FBX | FBX201400}"/>
                            <optionitem name="FBX | FBX201300 {FBX | FBX201300}"/>
                            <optionitem name="FBX | FBX201200 {FBX | FBX201200}"/>
                            <optionitem name="FBX | FBX201100 {FBX | FBX201100}"/>
                            <optionitem name="FBX 6.0 | FBX201000 {FBX 6.0 | FBX201000}"/>
                            <optionitem name="FBX 6.0 | FBX200900 {FBX 6.0 | FBX200900}"/>
                            <optionitem name="FBX 6.0 | FBX200611 {FBX 6.0 | FBX200611}"/>
                    </option>
                </row>
                <row name="Vertex Cache Format" accepts="houdini">
                    <option type="combo" name="fbxVCF">
                            <optionitem name="Maya Compatible (MC) {mayaformat}"/>
                            <optionitem name="3DS Max Compatible (PC2) {maxformat}"/>
                    </option>
                </row>
                <row name="Export Invisible Objects" accepts="houdini">
                    <option type="combo" name="fbxEIO">
                            <optionitem name="As hidden null nodes {nullnodes}"/>
                            <optionitem name="As hidden full nodes {fullnodes}"/>
                            <optionitem name="As visible full nodes {visiblenodes}"/>
                            <optionitem name="Don't export {nonodes}"/>
                    </option>
                </row>
                <row name="Axis system" accepts="houdini">
                    <option type="combo" name="fbxAS">
                            <optionitem name="Y Up (Right-handed) {yupright}"/>
                            <optionitem name="Y Up (Left-handed) {yupleft}"/>
                            <optionitem name="Z Up (Right-handed) {zupright}"/>
                            <optionitem name="Current (Y up Right-handed) {currentup}"/>
                    </option>
                </row>
                <row name="Conversion Level of Detail">
                    <option type="float" name="fbxCLOD" value="1.0"/>
                </row>
                <row name="Detect Constant Point Count Dynamic Objects">
                    <option type="checkbox" name="fbxDCPCDO" value="True"/>
                </row>
                <row name="Convert NURBS and Beizer Surface to Polygons">
                    <option type="checkbox" name="fbxCNABSTP" value="False"/>
                </row>
                <row name="Conserve Memory at the Expense of Export Time">
                    <option type="checkbox" name="fbxCMATEOET" value="False"/>
                </row>
                <row name="Force Blend Shape Export">
                    <option type="checkbox" name="fbxFBSE" value="False"/>
                </row>
                <row name="Force Skin Deform Export">
                    <option type="checkbox" name="fbxFSDE" value="False"/>
                </row>
                <row name="Export End Effectors">
                    <option type="checkbox" name="fbxEEE" value="True"/>
                </row>

    """

    def __init__(self):
        super(GenericAsset, self).__init__()

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
            resultingNode.moveToGoodPosition()
            self.addFTab(resultingNode)
            self.setFTab(resultingNode, iAObj)

        elif (
                iAObj.componentName == 'houdiniPublishScene' or
                iAObj.componentName == 'houdiniNodes' or
                iAObj.filePath.endswith('.hip')
        ):
            if (
                    'importMode'in iAObj.options and
                    iAObj.options['importMode'] == 'Import'
            ):
                # Import Houdini Published Nodes/Scene
                resultingNode = hou.node('/obj').createNode(
                    'subnet', iAObj.assetName)
                resultingNode.loadChildrenFromFile(iAObj.filePath.replace('\\', '/'))
                resultingNode.setSelected(1)
                resultingNode.moveToGoodPosition()
                self.addFTab(resultingNode)
                self.setFTab(resultingNode, iAObj)

            elif (
                    'importMode' in iAObj.options and
                    iAObj.options['importMode'] == 'Merge'
            ):
                if iAObj.options['overwriteOnConflict']:
                    hou.hipFile.merge(iAObj.filePath.replace('\\', '/'), overwrite_on_conflict=True)
                else:
                    hou.hipFile.merge(iAObj.filePath.replace('\\', '/'))
            else:
                # Load Houdini Published Nodes/Scene
                hou.hipFile.load(iAObj.filePath.replace('\\', '/'))

        elif (
                iAObj.componentName == 'fbx' or
                iAObj.filePath.endswith('fbx')
        ):
            hou.hipFile.importFBX(iAObj.filePath)

        else:
            print 'Do not know how to import component {} (path: {})'.format(iAObj.componentName, iAObj.filePath)

        return 'Imported ' + iAObj.assetType + ' asset'

    def publishAsset(self, iAObj=None):
        '''Publish the asset defined by the provided *iAObj*.'''

        panelComInstance = panelcom.PanelComInstance.instance()

        if hasattr(iAObj, 'customComponentName'):
            componentName = iAObj.customComponentName
        else:
            componentName = 'houdiniNodes'

        publishedComponents = []

        # handle houdini scene
        if (
                componentName == 'houdiniPublishScene'
        ):
            temporaryPath = HelpFunctions.temporaryFile(suffix='.hip')

            if iAObj.options['exportMode'] == 'Selection':
                # Publish Main Scene in selection mode
                hou.copyNodesToClipboard(hou.selectedNodes())

                command = "hou.pasteNodesFromClipboard(hou.node('/obj'));\
                hou.hipFile.save('%s')" % (temporaryPath.replace('\\', '\\\\'))

                cmd = '%s -c "%s"' % (os.path.join(
                    os.getenv('HFS'), 'bin', 'hython'), command)

                #os.system(cmd)
                result = subprocess.Popen(cmd)
                result.communicate()
                if result.returncode != 0:
                    raise Exception('Houdini selected nodes scene export failed!')
            else:
                hou.hipFile.save(temporaryPath)

            publishedComponents.append(
                FTComponent(
                    componentname=componentName,
                    path=temporaryPath
                )
            )

            panelComInstance.emitPublishProgressStep()

        # handle houdini nodes
        if (
                componentName == 'houdiniNodes'
        ):
            temporaryPath = HelpFunctions.temporaryFile(suffix='.hip')

            if iAObj.options['exportMode'] == 'Selection':
                ''' Publish Selected Nodes'''
                selectednodes = hou.selectedNodes()
                selectednodes[0].parent().saveChildrenToFile(
                    selectednodes, [], temporaryPath)
            else:
                ''' Publish All Nodes'''
                rootnode = hou.node('/obj')
                rootnode.saveChildrenToFile(rootnode.children(), [], temporaryPath)

            publishedComponents.append(
                FTComponent(
                    componentname=componentName,
                    path=temporaryPath
                )
            )

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

    @staticmethod
    def importOptions():
        xml = """
        <tab name="Options">
            <row name="Import mode">
                <option type="radio" name="importMode">
                    <optionitem name="Import" value="True"/>
                    <optionitem name="Merge"/>
                    <optionitem name="Open"/>
                </option>
            </row>
            <row name="Merge - overwrite on conflict" accepts="houdini">
                <option type="checkbox" name="overwriteOnConflict" value="True"/>
            </row>
        </tab>
        """
        return xml

    @staticmethod
    def parseComboBoxNameValue(name):
        return name[name.rfind("{") + 1:name.rfind("}")]


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
                iAObj.options['fbx'],
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
                    abcRopnet.parm('f%d' % (i + 1)).deleteAllKeyframes()
                    abcRopnet.parm('f%d' % (i + 1)).set(iAObj.options[x])
            else:
                abcRopnet.parm('trange').set(0)

            abcRopnet.parm('filename').set(temporaryPath)
            abcRopnet.parm('root').set(selectednodes[0].parent().path())
            abcRopnet.parm('objects').set(objects)
            abcRopnet.parm('format').set('hdf5')
            try:
                abcRopnet.render()
            finally:
                ropNet.destroy()

            panelComInstance.emitPublishProgressStep()

        if iAObj.options.get('fbx'):
            ''' Export FBX'''
            temporaryPath = HelpFunctions.temporaryFile(suffix='.fbx')

            publishedComponents.append(
                FTComponent(
                    componentname='fbx',
                    path=temporaryPath
                )
            )

            objPath = hou.node('/obj')

            # Selection Objects Set
            if iAObj.options.get('fbxExportMode') == 'Selection':
                selectednodes = hou.selectedNodes()
                objects = ' '.join([x.path() for x in selectednodes])
            else:
                selectednodes = objPath.glob('*')
                objects = '*'

            # Create Rop Net
            ropNet = objPath.createNode('ropnet')
            fbxRopnet = ropNet.createNode('filmboxfbx')

            fbxRopnet.parm('sopoutput').set(temporaryPath)
            fbxRopnet.parm('startnode').set(selectednodes[0].parent().path())
            fbxRopnet.parm('exportkind').set(iAObj.options.get('fbxASCII'))
            fbxRopnet.parm('sdkversion').set(GenericAsset.parseComboBoxNameValue(iAObj.options.get('fbxSDKVersion')))
            fbxRopnet.parm('vcformat').set(GenericAsset.parseComboBoxNameValue(iAObj.options.get('fbxVCF')))
            fbxRopnet.parm('invisobj').set(GenericAsset.parseComboBoxNameValue(iAObj.options.get('fbxEIO')))
            fbxRopnet.parm('polylod').set(iAObj.options.get('fbxCLOD'))
            fbxRopnet.parm('detectconstpointobjs').set(iAObj.options.get('fbxDCPCDO'))
            fbxRopnet.parm('convertsurfaces').set(iAObj.options.get('fbxCNABSTP'))
            fbxRopnet.parm('conservemem').set(iAObj.options.get('fbxCMATEOET'))
            fbxRopnet.parm('forceblendshape').set(iAObj.options.get('fbxFBSE'))
            fbxRopnet.parm('forceskindeform').set(iAObj.options.get('fbxFSDE'))
            try:
                fbxRopnet.parm('axissystem').set(GenericAsset.parseComboBoxNameValue(iAObj.options.get('fbxAS')))
                fbxRopnet.parm('exportendeffectors').set(iAObj.options.get('fbxEEE'))
            except:
                pass  # No supported in older versions
            try:
                fbxRopnet.render()
            finally:
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
            <row name="Houdini nodes" accepts="houdini">
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
                <option type="checkbox" name="alembicAnimation" value="False"/>
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
        <tab name="FBX options">
            <row name="Publish FBX">
                <option type="checkbox" name="fbx" value="True"/>
            </row>
            {2}
            <row name="FBX Selection Mode" accepts="houdini">
                <option type="radio" name="fbxExportMode">
                        <optionitem name="All"/>
                        <optionitem name="Selection" value="True"/>
                </option>
            </row>
        </tab>
        """
        s = os.getenv('FS')
        e = os.getenv('FE')
        xml = xml.format(s, e, GenericAsset.FBX_EXPORT_OPTIONS)
        return xml


class CameraAsset(GenericAsset):
    def __init__(self):
        super(CameraAsset, self).__init__()

    def bakeCamAnim(self, node, frameRange):
        ''' Bake camera to World Space '''
        if 'cam' in node.type().name():
            bkNd = hou.node('/obj').createNode(
                'cam', '%s_bake' % node.name())

            for x in ['resx', 'resy']:
                bkNd.parm(x).set(node.parm(x).eval())

        for frame in xrange(int(frameRange[0]), (int(frameRange[1]) + 1)):
            time = (frame - 1) / hou.fps()
            tsrMtx = node.worldTransformAtTime(time).explode()

            for parm in tsrMtx:
                if 'shear' not in parm:
                    for x, p in enumerate(bkNd.parmTuple(parm[0])):
                        p.setKeyframe(hou.Keyframe(tsrMtx[parm][x], time))

        return bkNd

    def importAsset(self, iAObj=None):

        if iAObj.componentName == 'alembic':
            resultingNode = hou.node('/obj').createNode(
                'alembicarchive', iAObj.assetName)
            resultingNode.parm('buildSubnet').set(False)
            resultingNode.parm('fileName').set(iAObj.filePath)
            hou.hscript(
                "opparm -C {0} buildHierarchy (1)".format(
                    resultingNode.path()))

            resCam = ''
            for nd in resultingNode.glob('*'):
                if 'cam' in nd.type().name():
                    resCam = self.bakeCamAnim(nd,
                                              [os.getenv('FS'),
                                               os.getenv('FE')])

            GenericAsset.addFTab(self, resCam)
            GenericAsset.setFTab(self, resCam, iAObj)
            resultingNode.destroy()
            resCam.setName(iAObj.assetName)
            resCam.moveToGoodPosition()

            return 'Imported ' + iAObj.assetType + ' asset'

        else:
            result = GenericAsset.importAsset(self, iAObj)

            return result

    def changeVersion(self, iAObj=None, applicationObject=None):
        '''Change the version of the asset defined in *iAObj*
        and *applicationObject*
        '''
        for n in hou.node('/').allSubChildren():
            if n.name().startswith(applicationObject):
                if iAObj.componentName == 'alembic':
                    iAObjCopy = copy.copy(iAObj)
                    iAObjCopy.assetName = n.name()
                    n.destroy()
                    self.importAsset(iAObjCopy)
                    return True
                else:
                    return GenericAsset.changeVersion(
                        self, iAObj, applicationObject)

    def publishAsset(self, iAObj=None):
        '''Publish the asset defined by the provided *iAObj*.'''

        publishedComponents = []

        totalSteps = self.getTotalSteps(
            steps=[
                iAObj.options['houdiniNodes'],
                iAObj.options['alembic'],
                iAObj.options['fbx'],
                iAObj.options['houdiniPublishScene']
            ]
        )
        panelComInstance = panelcom.PanelComInstance.instance()
        panelComInstance.setTotalExportSteps(totalSteps)

        objPath = hou.node('/obj')
        cam = hou.selectedNodes()[0]

        bcam = self.bakeCamAnim(cam,
                                [iAObj.options['frameStart'],
                                 iAObj.options['frameEnd']])

        if iAObj.options['houdiniNodes']:
            temporaryPath = HelpFunctions.temporaryFile(suffix='.hip')

            publishedComponents.append(
                FTComponent(
                    componentname='houdiniNodes',
                    path=temporaryPath
                )
            )
            bcam.parent().saveChildrenToFile(
                [bcam], [], temporaryPath)

            panelComInstance.emitPublishProgressStep()

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

            # Create Rop Net
            ropNet = objPath.createNode('ropnet')

            abcRopnet = ropNet.createNode('alembic')

            if iAObj.options.get('alembicAnimation'):
                # Check Alembic for animation option
                abcRopnet.parm('trange').set(1)
                for i, x in enumerate(
                        ['frameStart', 'frameEnd', 'alembicEval']):
                    abcRopnet.parm('f%d' % (i + 1)).deleteAllKeyframes()
                    abcRopnet.parm('f%d' % (i + 1)).set(iAObj.options[x])
            else:
                abcRopnet.parm('trange').set(0)

            abcRopnet.parm('filename').set(temporaryPath)
            abcRopnet.parm('root').set(bcam.parent().path())
            abcRopnet.parm('objects').set(bcam.path())
            abcRopnet.parm('format').set('hdf5')
            abcRopnet.render()
            ropNet.destroy()

            panelComInstance.emitPublishProgressStep()

        if iAObj.options.get('fbx'):
            ''' Export FBX'''
            temporaryPath = HelpFunctions.temporaryFile(suffix='.fbx')

            publishedComponents.append(
                FTComponent(
                    componentname='fbx',
                    path=temporaryPath
                )
            )

            objPath = hou.node('/obj')

            # Selection Objects Set
            if iAObj.options.get('fbxExportMode') == 'Selection':
                selectednodes = hou.selectedNodes()
                objects = ' '.join([x.path() for x in selectednodes])
            else:
                selectednodes = objPath.glob('*')
                objects = '*'

            # Create Rop Net
            ropNet = objPath.createNode('ropnet')
            fbxRopnet = ropNet.createNode('filmboxfbx')

            fbxRopnet.parm('sopoutput').set(temporaryPath)
            fbxRopnet.parm('startnode').set(selectednodes[0].parent().path())
            fbxRopnet.parm('exportkind').set(iAObj.options.get('fbxASCII'))
            fbxRopnet.parm('sdkversion').set(GenericAsset.parseComboBoxNameValue(iAObj.options.get('fbxSDKVersion')))
            fbxRopnet.parm('vcformat').set(GenericAsset.parseComboBoxNameValue(iAObj.options.get('fbxVCF')))
            fbxRopnet.parm('invisobj').set(GenericAsset.parseComboBoxNameValue(iAObj.options.get('fbxEIO')))
            fbxRopnet.parm('polylod').set(iAObj.options.get('fbxCLOD'))
            fbxRopnet.parm('detectconstpointobjs').set(iAObj.options.get('fbxDCPCDO'))
            fbxRopnet.parm('convertsurfaces').set(iAObj.options.get('fbxCNABSTP'))
            fbxRopnet.parm('conservemem').set(iAObj.options.get('fbxCMATEOET'))
            fbxRopnet.parm('forceblendshape').set(iAObj.options.get('fbxFBSE'))
            fbxRopnet.parm('forceskindeform').set(iAObj.options.get('fbxFSDE'))
            try:
                fbxRopnet.parm('axissystem').set(GenericAsset.parseComboBoxNameValue(iAObj.options.get('fbxAS')))
                fbxRopnet.parm('exportendeffectors').set(iAObj.options.get('fbxEEE'))
            except:
                pass  # No supported in older versions
            try:
                fbxRopnet.render()
            finally:
                ropNet.destroy()

            panelComInstance.emitPublishProgressStep()
        bcam.destroy()

        return publishedComponents, 'Published CameraAsset asset'

    @staticmethod
    def exportOptions():
        xml = """
        <tab name="Options">
            <row name="Frame range">
                <option type="string" name="frameStart" value="{0}"/>
                <option type="string" name="frameEnd" value="{1}"/>
            </row>
            <row name="Attach scene to asset" accepts="houdini">
                <option type="checkbox" name="houdiniPublishScene" value="False"/>
            </row>
            <row name="Houdini binary" accepts="houdini">
                <option type="checkbox" name="houdiniNodes" value="False"/>
            </row>
            <row name="Export" accepts="houdini">
                <option type="radio" name="exportMode">
                        <optionitem name="Selection" value="True"/>
                </option>
            </row>
        </tab>
        <tab name="Alembic options">
            <row name="Publish Alembic">
                <option type="checkbox" name="alembic" value="True"/>
            </row>
            <row name="Include animation">
                <option type="checkbox" name="alembicAnimation" value="False"/>
            </row>
            <row name="Frame range">
                <option type="string" name="frameStart" value="{0}"/>
                <option type="string" name="frameEnd" value="{1}"/>
            </row>
            <row name="Evaluate every">
                <option type="float" name="alembicEval" value="1.0"/>
            </row>
        </tab>
        <tab name="FBX options">
            <row name="Publish FBX">
                <option type="checkbox" name="fbx" value="True"/>
            </row>
            {2}
        </tab>
        """
        s = os.getenv('FS')
        e = os.getenv('FE')
        xml = xml.format(s, e, GenericAsset.FBX_EXPORT_OPTIONS)
        return xml


def registerAssetTypes():
    assetHandler = FTAssetHandlerInstance.instance()
    assetHandler.registerAssetType(name='scene', cls=SceneAsset)
    assetHandler.registerAssetType(name='geo', cls=GeometryAsset)
    assetHandler.registerAssetType(name='cam', cls=CameraAsset)
