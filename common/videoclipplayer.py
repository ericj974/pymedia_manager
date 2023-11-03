import logging
import threading
import time
from enum import Enum
from pathlib import Path
from queue import Queue, Full

import numpy as np
from PyQt5.QtGui import QMovie
from moviepy.editor import VideoFileClip
from moviepy.tools import cvsecs
from moviepy.video.VideoClip import VideoClip

queue_length = 3

logger = logging.getLogger(__name__)


class VideoClipPlayer(object):
    """ This class loads a video file that can be played. It can
    be passed a callback function to which decoded video frames should be passed.
    """

    def __init__(self, path: Path = None, videorenderfunc=None, frame_changed_callback=None):
        """
        Constructor.

        Parameters
        ----------
        path : Path, optional
            The path to the mediafile to be loaded (default: None)
        videorenderfunc : callable (default: None)
            Callback function that takes care of the actual
            Rendering of the videoframe.\
            The specified renderfunc should be able to accept the following
            arguments:
                - frame (numpy.ndarray): the videoframe to be rendered
        play_audio : bool, optional
            Whether audio of the clip should be played.
        """

        # The clip
        self.clip: VideoClip = None
        # Create an internal timer
        self.clock: ClipTimer = ClipTimer()
        # filepath that has been loaded
        self.path: Path = None
        # Clip properties
        self.fps = None
        self.duration = None
        self.play_audio: bool = False
        # Player status
        self.status = PlayerState.UNINITIALIZED
        self.loop_count = 0
        # Last played frame
        self.last_frame_no = 0

        # Audio
        self.audio_format: dict = None
        self.audio_queue: Queue = None
        self.audio_frame_handler: threading.Thread = None

        # Rendering
        self.__video_frame_render_callback = None
        # Main rendering loop.
        self.render_loop = None

        # Load a video file if specified, but allow users to do this later
        # by initializing all variables to None
        if path:
            if not self.open_media(path, play_audio=False):
                self.reset()

        # Set callback function if set
        self.set_video_frame_render_callback(videorenderfunc)
        self.frame_changed_callback = frame_changed_callback

        # Shall we loop ?
        self._loop = False
        # Current video frame as a numpy array
        self.__current_video_frame = None

    @property
    def frame_interval(self):
        """ Duration in seconds of a single frame. """
        return self.clock.frame_interval

    @property
    def current_frame_no(self):
        """ Current frame_no of video. """
        return self.clock.current_frame

    @property
    def current_videoframe(self):
        """ Representation of current video frame as a numpy array. """
        return self.__current_video_frame

    @property
    def current_playtime(self):
        """ Clocks current runtime in seconds. """
        return self.clock.time

    @property
    def loop(self):
        """ Indicates whether the playback should loop. """
        return self._loop

    @loop.setter
    def loop(self, value):
        """ Indicates whether the playback should loop.

        Parameters
        ----------
        value : bool
            True if playback should loop, False if not.

        """
        if not type(value) == bool:
            raise TypeError("can only be True or False")
        self._loop = value

    def currentFrameNumber(self):
        if self.clip:
            return self.current_frame_no
        else:
            return -1

    def frame_count(self):
        return int(self.fps * self.duration)

    def state(self):
        return self.status

    def is_valid(self):
        return self.clip is not None

    def reset(self):
        """ Resets the player and discards loaded data. """
        self.clip = None
        self.path = None

        self.fps = None
        self.duration = None

        self.status = PlayerState.UNINITIALIZED
        self.clock.reset()

        self.loop_count = 0

    def open_media(self, path: Path, play_audio: bool = False, **kwargs):
        """ Loads a media file to decode.

        If an audio stream is detected, its parameters will be stored in a
        dictionary in the variable `audioformat`. This contains the fields

        :nbytes: the number of bytes in the stream (2 is 16-bit sound).
        :nchannels: the channels (2 for stereo, 1 for mono)
        :fps: the frames per sec/sampling rate of the sound (e.g. 44100 KhZ).
        :buffersize: the audioframes per buffer.

        If play_audio was set to False, or the video does not have an audiotrack,
        `audioformat` will be None.

        Parameters
        ----------
        path : Path
            The path to the media file to load.
        play_audio : bool, optional
            Indicates whether the audio of a movie should be played.

        Raises
        ------
        IOError
            When the file could not be found or loaded.
        """
        if path and path.is_file():
            self.clip = VideoFileClip(str(path), audio=play_audio, **kwargs)
            # Workaround when rotation in metadata, see https://github.com/Zulko/moviepy/issues/586
            if self.clip.rotation == 90:
                self.clip = self.clip.resize(self.clip.size[::-1])
                self.clip.rotation = 0

            self.path = path

            ## Timing variables
            # Clip duration
            self.duration = self.clip.duration
            self.clock.max_duration = self.clip.duration
            logger.debug("Video clip duration: {}s".format(self.duration))

            # Frames per second of clip
            self.fps = self.clip.fps
            self.clock.fps = self.clip.fps
            logger.debug("Video clip FPS: {}".format(self.fps))

            if play_audio and self.clip.audio:
                buffersize = int(self.frame_interval * self.clip.audio.fps)
                self.audio_format = {
                    'nbytes': 2,
                    'nchannels': self.clip.audio.nchannels,
                    'fps': self.clip.audio.fps,
                    'buffersize': buffersize
                }
                logger.debug("Audio loaded: \n{}".format(self.audio_format))
                logger.debug("Creating audio buffer of length: "
                             " {}".format(queue_length))
                self.audio_queue = Queue(queue_length)
            else:
                self.audio_format = None

            logger.debug('Loaded {0}'.format(path))
            self.status = PlayerState.STOPPED
            return True
        else:
            raise IOError("File not found: {0}".format(path))

    def load_clip(self, clip: VideoClip = None, play_audio=False):
        """ Loads a clip to decode.

        If an audiostream is detected, its parameters will be stored in a
        dictionary in the variable `audioformat`. This contains the fields

        :nbytes: the number of bytes in the stream (2 is 16-bit sound).
        :nchannels: the channels (2 for stereo, 1 for mono)
        :fps: the frames per sec/sampling rate of the sound (e.g. 44100 KhZ).
        :buffersize: the audioframes per buffer.

        If play_audio was set to False, or the video does not have an audiotrack,
        `audioformat` will be None.

        Parameters
        ----------
        clip : VideoClip
            The path to the media file to load.
        play_audio : bool, optional
            Indicates whether the audio of a movie should be played.

        Raises
        ------
        IOError
            When the file could not be found or loaded.
        """
        if clip is not None:
            self.clip = clip
            self.path = None

            ## Timing variables
            # Clip duration
            self.duration = self.clip.duration
            self.clock.max_duration = self.clip.duration
            logger.debug("Video clip duration: {}s".format(self.duration))

            # Frames per second of clip
            self.fps = self.clip.fps
            self.clock.fps = self.clip.fps
            logger.debug("Video clip FPS: {}".format(self.fps))

            if play_audio and self.clip.audio:
                buffersize = int(self.frame_interval * self.clip.audio.fps)
                self.audio_format = {
                    'nbytes': 2,
                    'nchannels': self.clip.audio.nchannels,
                    'fps': self.clip.audio.fps,
                    'buffersize': buffersize
                }
                logger.debug("Audio loaded: \n{}".format(self.audio_format))
                logger.debug("Creating audio buffer of length: "
                             " {}".format(queue_length))
                self.audio_queue = Queue(queue_length)
            else:
                self.audio_format = None

            logger.debug('Loaded clip')
            self.status = PlayerState.STOPPED
            return True
        return False

    def set_video_frame_render_callback(self, func):
        """ Sets the function to call when a new frame is available.
        This function is passed the frame (in the form of a numpy.ndarray) and
        should take care of the rendering.

        Parameters
        ----------
        func : callable
            The function to pass the new frame to once it becomes available.
        """

        # Check if renderfunc is indeed a function
        if not func is None and not callable(func):
            raise TypeError("The object passed for set_video_frame_render_callback is not a function")
        self.__video_frame_render_callback = func

    def start(self):
        return self.play()

    def play(self):
        """ Start the playback of the video.
        The playback loop is run in a separate thread, so this function returns
        immediately. This allows one to implement things such as event handling
        loops (e.g. check for key presses) elsewhere.
        """
        ### First do some status checks

        # Make sure a file is loaded
        if self.status == PlayerState.UNINITIALIZED or self.clip is None:
            raise RuntimeError("Player uninitialized or no file loaded")

        # Check if playback has already finished (rewind needs to be called first)
        if self.status == PlayerState.EOS:
            logger.debug("End of stream has already been reached")
            return

        # Check if playback hasn't already been started (and thus if play()
        # has not been called before from another thread for instance)
        if self.status in [PlayerState.PLAYING, PlayerState.PAUSED]:
            logger.warning("Video already started")
            return

        # Start the general playing loop
        if self.status == PlayerState.STOPPED:
            self.status = PlayerState.PLAYING

        self.last_frame_no = 0

        if not hasattr(self, "renderloop") or not self.render_loop.is_alive():
            if self.audio_format:
                # Chop the total stream into separate audio chunks that are the
                # length of a video frame (this way the index of each chunk
                # corresponds to the video frame it belongs to.)
                self.__calculate_audio_frames()
                # Start audio handling thread. This thread places audioframes
                # into a sound buffer, until this buffer is full.
                self.audio_frame_handler = threading.Thread(
                    target=self.__audio_render_thread)
                self.audio_frame_handler.start()

            # Start main rendering loop.
            self.render_loop = threading.Thread(target=self.__render)
            self.render_loop.start()
        else:
            logger.warning("Rendering thread already running!")

    def pause(self):
        """ Pauses or resumes the video and/or audio stream. """

        # Change playback status only if current status is PLAYING or PAUSED
        # (and not READY).
        logger.debug("Pausing playback")
        if self.status == PlayerState.PAUSED:
            # Recalculate audio stream position to make sure it is not out of
            # sync with the video
            self.__calculate_audio_frames()
            self.status = PlayerState.PLAYING
            self.clock.pause()
        elif self.status == PlayerState.PLAYING:
            self.status = PlayerState.PAUSED
            self.clock.pause()

    def stop(self):
        """ Stops the video stream and resets the clock. """
        logger.debug("Stopping playback")
        # Stop the clock
        self.clock.stop()
        # Set player status to ready
        self.status = PlayerState.STOPPED

    def seek(self, value: float):
        """ Seek to the specified time.

        Parameters
        ----------
        value : float
            The time to seek to. Can be any of the following formats:

            >>> 15.4 -> 15.4 # seconds
            >>> (1,21.5) -> 81.5 # (min,sec)
            >>> (1,1,2) -> 3662 # (hr, min, sec)
            >>> '01:01:33.5' -> 3693.5  #(hr,min,sec)
            >>> '01:01:33.045' -> 3693.045
            >>> '01:01:33,5' #comma works too
        """
        # Pause the stream
        self.pause()
        # Make sure the movie starts at 1s as 0s gives trouble.
        self.clock.time = max(0.5, value)
        logger.debug("Seeking to {} seconds; frame {}".format(self.clock.time,
                                                              self.clock.current_frame))
        if self.audio_format:
            self.__calculate_audio_frames()
        # Resume the stream
        self.pause()

    def rewind(self):
        """ Rewinds the video to the beginning.
        Convenience function simply calling seek(0). """
        self.seek(0.5)

    def __calculate_audio_frames(self):
        """ Aligns audio with video.
        This should be called for instance after a seeking operation or resuming
        from a pause. """

        if self.audio_format is None:
            return
        start_frame = self.clock.current_frame
        totalsize = int(self.clip.audio.fps * self.clip.audio.duration)
        self.audio_times = list(range(0, totalsize,
                                      self.audio_format['buffersize'])) + [totalsize]
        # Remove audio segments up to the starting frame
        del (self.audio_times[0:start_frame])

    def __render(self):
        """ Main render loop.

        Checks clock if new video and audio frames need to be rendered.
        If so, it passes the frames to functions that take care
        of rendering these frames. """

        # Render first frame
        self.__render_video_frame()

        # Start video clock with start of this thread
        self.clock.start()

        logger.debug("Started rendering loop.")
        # Main rendering loop
        while self.status in [PlayerState.PLAYING, PlayerState.PAUSED]:
            current_frame_no = self.clock.current_frame

            # Check if end of clip has been reached
            if self.clock.time >= self.duration:
                logger.debug("End of stream reached at {}".format(self.clock.time))
                if self.loop:
                    logger.debug("Looping: restarting stream")
                    # Seek to the start
                    self.rewind()
                    self.loop_count += 1
                else:
                    # End of stream has been reached
                    self.status = PlayerState.EOS
                    break

            if self.last_frame_no != current_frame_no:
                # A new frame is available. Get it from te stream
                self.__render_video_frame()

            self.last_frame_no = current_frame_no

            # Sleeping is a good idea to give the other threads some breathing
            # space to do their work.
            try:
                time.sleep(1. / self.fps)
            except:
                time.sleep(1. / 20)

        # Stop the clock.
        self.clock.stop()
        logger.debug("Rendering stopped.")

    def render_video_frame(self):
        self.__render_video_frame()

    def __render_video_frame(self):
        """ Retrieves a new video frame from the stream.

        Sets the frame as the __current_video_frame and passes it on to
        __videorenderfunc() if it is set. """
        if self.clip:
            try:
                new_video_frame = self.clip.get_frame(self.clock.time)
            except:
                return
        else:
            return
        # Pass it to the callback function if this is set
        if callable(self.__video_frame_render_callback):
            self.__video_frame_render_callback(new_video_frame)
        # Set current_frame to current frame (...)
        self.__current_video_frame = new_video_frame

    def __audio_render_thread(self):
        """ Thread that takes care of the audio rendering. Do not call directly,
        but only as the target of a thread. """
        new_audio_frame = None
        logger.debug("Started audio rendering thread.")

        while self.status in [PlayerState.PLAYING, PlayerState.PAUSED]:
            # Retrieve audio chunk
            if self.status == PlayerState.PLAYING:
                if new_audio_frame is None:
                    # Get a new frame from the audio stream, skip to the next one
                    # if the current one gives a problem
                    try:
                        start = self.audio_times.pop(0)
                        stop = self.audio_times[0]
                    except IndexError:
                        logger.debug("Audio times could not be obtained")
                        time.sleep(0.02)
                        continue

                    # Get the frame numbers to extract from the audio stream.
                    chunk = (1.0 / self.audio_format['fps']) * np.arange(start, stop)

                    try:
                        # Extract the frames from the audio stream. Does not always,
                        # succeed (e.g. with bad streams missing frames), so make
                        # sure this doesn't crash the whole program.
                        new_audio_frame = self.clip.audio.to_soundarray(
                            tt=chunk,
                            buffersize=self.frame_interval * self.clip.audio.fps,
                            quantize=True
                        )
                    except OSError as e:
                        logger.warning("Sound decoding error: {}".format(e))
                        new_audio_frame = None
                # Put audio frame in buffer/queue for sound renderer to pick up. If
                # the queue is full, try again after a timeout (this allows to check
                # if the status is still PLAYING after a pause.)
                if not new_audio_frame is None:
                    try:
                        self.audio_queue.put(new_audio_frame, timeout=.05)
                        new_audio_frame = None
                    except Full:
                        pass

            time.sleep(0.005)

        logger.debug("Stopped audio rendering thread.")

    def __repr__(self):
        """ Create a string representation for when print() is called. """
        return f"Decoder [file loaded: {self.path.name}]"


class ClipTimerState(Enum):
    # Timer status
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"


class PlayerState(Enum):
    # Player status
    UNINITIALIZED = 9  # No video file loaded
    PAUSED = QMovie.Paused  # Playback is paused
    PLAYING = QMovie.Running  # Player is playing
    EOS = 4  # End of stream has been reached
    STOPPED = 33  # Clock has been stopped and is reset


class ClipTimer(object):
    """ Timer serves as a video clock that is used to determine which frame needs to be
    displayed at a specified time. the clock runs in its own separate thread.
    Say you have an instance of Timer called ``clock``. The time can be polled by
    checking

    >> clock.time

    and the current frame can be determined by checking

    >> clock.current_frame.

    """

    def __init__(self, fps=None, max_duration=None):
        """ Constructor.

        Parameters
        ----------
        fps : float, optional
            The frames per second of the video for which this timer is created.
        max_duration : float, optional
            The maximum time in seconds the timer should run for.
        """
        self.status = ClipTimerState.PAUSED
        self.max_duration = max_duration
        self.fps = fps
        self.reset()

        self.interval_start = -1
        self.previous_intervals = []
        self.current_interval_duration = 0.0

    def reset(self):
        """ Reset the clock to 0."""
        self.previous_intervals = []
        self.current_interval_duration = 0.0

    def pause(self):
        """ Pauses the clock to continue running later.
        Saves the duration of the current interval in the previous_intervals
        list."""
        if self.status == ClipTimerState.RUNNING:
            self.status = ClipTimerState.PAUSED
            self.previous_intervals.append(time.time() - self.interval_start)
            self.current_interval_duration = 0.0
        elif self.status == ClipTimerState.PAUSED:
            self.interval_start = time.time()
            self.status = ClipTimerState.RUNNING

    def start(self):
        """ Starts the clock from 0.
        Uses a separate thread to handle the timing functionalities. """
        if not hasattr(self, "thread") or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.__run)
            self.status = ClipTimerState.RUNNING
            self.reset()
            self.thread.start()
        else:
            print("Clock already running!")

    def __run(self):
        """ Internal function that is run in a separate thread. Do not call
        directly. """
        self.interval_start = time.time()
        while self.status != ClipTimerState.STOPPED:
            if self.status == ClipTimerState.RUNNING:
                self.current_interval_duration = time.time() - self.interval_start

            # If max_duration is set, stop the clock if it is reached
            if self.max_duration and self.time > self.max_duration:
                self.status == ClipTimerState.STOPPED

            # One refresh per millisecond seems enough
            time.sleep(0.001)

    def stop(self):
        """ Stops the clock and resets the internal timers. """
        self.status = ClipTimerState.STOPPED
        self.reset()

    @property
    def time(self):
        """ The current time of the clock. """
        return sum(self.previous_intervals) + self.current_interval_duration

    @time.setter
    def time(self, value):
        """ Sets the time of the clock. Useful for seeking.

        Parameters
        ----------
        value : str or int
            The time to seek to. Can be any of the following formats:

            >>> 15.4 -> 15.4 # seconds
            >>> (1,21.5) -> 81.5 # (min,sec)
            >>> (1,1,2) -> 3662 # (hr, min, sec)
            >>> '01:01:33.5' -> 3693.5  #(hr,min,sec)
            >>> '01:01:33.045' -> 3693.045
            >>> '01:01:33,5' #comma works too
        """
        seconds = cvsecs(value)
        self.reset()
        self.previous_intervals.append(seconds)

    @property
    def current_frame(self):
        """ The current frame number that should be displayed."""
        if not self.__fps:
            raise RuntimeError("fps not set so current frame number cannot be"
                               " calculated")
        else:
            return int(self.__fps * self.time)

    @property
    def frame_interval(self):
        """ The duration of a single frame in seconds. """
        if not self.__fps:
            raise RuntimeError("fps not set so current frame interval cannot be"
                               " calculated")
        else:
            return 1.0 / self.__fps

    @property
    def fps(self):
        """ Returns the frames per second indication that is currently set. """
        return self.__fps

    @fps.setter
    def fps(self, value):
        """ Sets the frames per second of the current movie the clock is used for.

        Parameters
        ----------
        value : float
            The fps value.
        """
        if not value is None:
            if not type(value) == float:
                raise ValueError("fps needs to be specified as a float")
            if value < 1.0:
                raise ValueError("fps needs to be greater than 1.0")
        self.__fps = value

    @property
    def max_duration(self):
        """ Returns the max duration the clock should run for.
        (Usually the duration of the videoclip) """
        return self.__max_duration

    @max_duration.setter
    def max_duration(self, value):
        """ Sets the value of max duration

        Parameters
        ----------
        value : float
            The value for max_duration

        Raises
        ------
        TypeError
            If max_duration is not a number.
        ValueError
            If max_duration is smaller than 0.
        """
        if not value is None:
            if not type(value) in [np.float64, float, int]:
                raise TypeError("max_duration needs to be specified as a number")
            if value < 1.0:
                raise ValueError("max_duration needs to be greater than 1.0")
            value = float(value)
        self.__max_duration = value

    def __repr__(self):
        """ Creates a string representation for the print function."""
        if self.__fps:
            return "Clock [current time: {0}, fps: {1}, current_frame: {2}]".format(
                self.time, self.__fps, self.current_frame)
        else:
            return "Clock [current time: {0}]".format(self.time)
