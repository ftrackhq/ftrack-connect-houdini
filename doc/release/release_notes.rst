..
    :copyright: Copyright (c) 2016 Postmodern Digital

.. _release/release_notes:

*************
Release Notes
*************

.. release:: Upcoming

    .. change:: change

        Update pyside signal signature for pyside2 compatiblity.

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
    :date: 2016-14-11

    .. change:: new

        Initial release of ftrack connect Houdini plug-in.
