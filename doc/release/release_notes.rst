..
    :copyright: Copyright (c) 2016 Postmodern Digital

.. _release/release_notes:

*************
Release Notes
*************

.. release:: 0.4.0
    :date: 2021-09-08

    .. change:: changed
        :tags: Hook

            Update hook for application-launcher.


    .. change:: changed
        :tags: Setup

            Provide dependency to ftrack-connector-legacy module.


.. warning::

    From this version the support for ftrack-connect 1.X is dropped, and
    only ftrack-conenct 2.0 will be supported up to the integration EOL.


.. release:: 0.3.1
    :date: 2020-11-16

    .. change:: fixed
        :tags: Internal

        Houdini fails to load due to certificate error under linux.

    .. change:: changed
        :tags: Setup

        Update pip command to install dependencie to generic main call.     


.. release:: 0.3.0
    :date: 2020-09-15

    .. change:: changed
        :tags: Internal

        Add file logger.

    .. change:: changed
        :tags: Internal

        Update pyside signal signature for pyside2 compability.

    .. change:: new
        :tags: Internal

        FBX export on publish.

    .. change:: new
        :tags: Internal

        FBX import.

    .. change:: fixed
        :tags: Internal

        Thumbnail save failed on windows publish.

    .. change:: changed
        :tags: fix

        Have plug-in load proceed if there is an exception setting up frame range and fps.

    .. change:: changed
        :tags: fix

        Hip can now be imported on Windows with paths having backlash (\) elements.

    .. change:: new
        :tags: Internal

        New Import,Merge & Open import options.


.. release:: 0.2.3
    :date: 2019-12-10

    .. change:: fix

        Fix QStringListModel compatibility for PySide2 5.9+.

    .. change: changed
        tags: Setup

        Update QtExt to latest vesion.

    .. change:: changed
        :tags: Setup

        Pip compatibility for version 19.3.0 or higher

.. release:: 0.2.2
    :date: 2019-01-29

    .. change:: changed
        :tags: Internal

        Convert code to standalone ftrack-connect plugin.

.. release:: 0.1.2
    :date: 2016-11-30

    .. change:: changed

        Add Support for Cache Asset (HoudiniScene/HoudiniNodes/Alembic Mode)
        Cache - it is a *.bgeo or *.vdb sequence publisher from Houdini

    .. change:: changed

        Add Camera Aperture, Resolution and other type.

    .. change:: fixed

        Check what type of Node selected in some type of Publish.

    .. change:: fixed
        :tags: Connector

        Camera not asset publish hierarchy animation.


.. release:: 0.1.1
    :date: 2016-11-28

    .. change:: new

        Add Support for Publish Scene (All/ Selected Mode)

    .. change:: new

        Add Support for Publish Geometry Asset (HoudiniScene/HoudiniNodes/Alembic Mode)

    .. change:: new

        Add Support for Camera Asset (HoudiniScene/HoudiniNodes/Alembic Mode)

    .. change:: fixed
        :tags: Ui

        Replace PySide module with QtExt.

    .. change:: fixed
        :tags: Connector

        Houdini doesn't starts when no handles attribute exists in shot.

    .. change:: fixed
        :tags: Connector

        Add new style of startup Frames set. If handles exists it set handles as Global parameter and with play-bar you can see actual frame range and handles is extended.

.. release:: 0.1.0
    :date: 2016-11-14

    .. change:: new

        Initial release of ftrack connect Houdini plug-in.
