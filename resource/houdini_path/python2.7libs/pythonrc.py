# :copyright: Copyright (c) 2016 Postmodern Digital

import os
import hou
import logging

import ftrack

ftrack.setup()


def setFrameRangeData():

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


setFrameRangeData()

logging.getLogger().setLevel(logging.INFO)