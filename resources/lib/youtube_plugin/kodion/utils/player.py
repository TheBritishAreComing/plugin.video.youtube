# -*- coding: utf-8 -*-

import math
import xbmc


class YouTubePlayer(xbmc.Player):
    def __init__(self, *args, **kwargs):
        self.context = kwargs.get('context')
        self.ui = self.context.get_ui()
        self.reset()
        self.current_video_total_time = 0.0
        self.current_played_time = 0.0

    def reset(self):
        properties = ['playing', 'post_play', 'license_url', 'license_token', 'seek_time', 'play_count']
        cleared = []
        for prop in properties:
            if self.ui.get_home_window_property(prop) is not None:
                cleared.append(prop)
                self.ui.clear_home_window_property(prop)
        self.context.log_debug('Cleared home window properties: {properties}'.format(properties=str(cleared)))
        self.current_video_total_time = 0.0
        self.current_played_time = 0.0

    def post_play(self):
        is_playing = self.ui.get_home_window_property('playing')
        post_play_command = self.ui.get_home_window_property('post_play')

        if is_playing is not None:
            current_played_percent = int(math.floor((self.current_played_time / self.current_video_total_time) * 100))
            self.context.log_debug('Playback: Total time: |{total_time}| Played time: |{time}| Played percent: |{percent}|'
                                   .format(total_time=self.current_video_total_time, time=self.current_played_time,
                                           percent=current_played_percent))

            play_count = self.ui.get_home_window_property('play_count')

            if current_played_percent >= self.context.get_settings().get_play_count_min_percent():
                play_count = '1'
                self.current_played_time = 0.0
                current_played_percent = 0
            else:
                if post_play_command:
                    post_play_command = 'RunPlugin(%s)' % self.context.create_uri(['events', 'post_play'],
                                                                                  {'video_id': is_playing,
                                                                                   'refresh_only': 'true'})

            if self.context.get_settings().use_playback_history():
                self.context.get_playback_history().update(is_playing, play_count, self.current_video_total_time,
                                                           self.current_played_time, current_played_percent)

            if post_play_command is not None:
                try:
                    self.context.execute(post_play_command)
                except:
                    self.context.log_debug('Failed to execute post play events.')
                    self.ui.show_notification('Failed to execute post play events.', time_milliseconds=5000)

    def onPlayBackStarted(self):
        self.current_video_total_time = self.getTotalTime()
        while self.isPlaying():
            xbmc.sleep(500)
            if self.isPlaying():
                self.current_played_time = self.getTime()
                if self.current_video_total_time == 0.0:
                    self.current_video_total_time = self.getTotalTime()

    def onAVStarted(self):
        if self.context.get_settings().use_playback_history():
            seek_time = self.ui.get_home_window_property('seek_time')
            if seek_time and seek_time != '0.0':
                self.seekTime(float(seek_time))

    def onPlayBackStopped(self):
        self.post_play()
        self.reset()

    def onPlayBackEnded(self):
        self.post_play()
        self.reset()
