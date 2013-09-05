#!/usr/bin/env python

from jnius import autoclass

PythonActivity = autoclass('org.renpy.android.PythonActivity')
Context = autoclass('android.content.Context')

class AudioAccess(object):

    __slots__ = ["audio_manager"]

    def __init__(self):
        self.audio_manager = PythonActivity.mActivity.getSystemService(Context.AUDIO_SERVICE)

    def is_music_active(self):
        return self.audio_manager.isMusicActive()
