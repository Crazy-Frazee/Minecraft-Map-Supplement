# -*- coding: utf-8 -*-

# WOOSTER VERSION 1.0.1
#   Enhancements:
#       * Thonny compatibility for GUI features
#       * Fix order of pixels from getPixels to reflect the book

#ORIGINAL COMMENT from JES media.py BELOW

#
# Media Wrappers for "Introduction to Media Computation"
# Started: Mark Guzdial, 2 July 2002
# Revisions:
# 18 June 2003: (ellie)
#    Added (blocking)play(AtRate)InRange methods to Sound class
#      and global sound functions
#    Changed getSampleValue, setSampleValue to give the appearance
#      of 1-based indexing
#    Added getLeftSampleValue and getRightSampleValue to Sound class
# 14 May 2003: Fixed discrepancy between getMediaPath and setMediaFolder (AdamW)
# 8 Nov: Fixed getSamplingRate (MarkG)
# 1 Nov: Fixed printing pixel
# 31 Oct: Fixed pickAColor (MarkG)
# 30 Oct: Added raises, fixed error messages. Added repaint (MarkG)
# 10 Oct: Coerced value to integer in Sound.setSampleValue   (MarkR)
# 2 Oct:  Corrected calls in setSampleValueAt  (MarkG):
# 30 Aug: Made commands more consistent and add type-checking (MarkG)
# 2 Aug: Changed to getSampleValueAt and setSampleValueAt (MarkG)
# 1 Dec 2005: made max makeEmptySound size 600
#             made max makeEmptyPicture dimensions 10000x10000
#             fixed the off-by-one error in makeEmptyPicture
# 14 June 2007: (Pam Cutter, Kalamazoo College)
#              Fixed off-by-one error in copyInto.  Now allows copying
#       of same-sized picture, starting at top-left corner
#
# 6 July 2007: (Pam Cutter/Alyce Brady, Kalamazoo College)
#              Added flexibility to make an empty picture of a specified color.  Added
#                  additional, 3-parameter constructor to Picture and SimplePicture classes to support this.
#              Modified copyInto so that it will copy as much of the source picture as will fit
#              Added crop and copyInto methods to Picture class to support these.
#
# 8 July 2007: (Pam Cutter/ Alyce Brady, Kalamazoo College)
#              Changed all  _class_ comparisons to use isinstance instead so that
#                   they will work with subclasses as well (e.g., subclasses of Picture
#                   are still pictures)
#              Added getSampleValue, setSampleValue functions with same functionality, but
#                   more intuitive names, as the getSample, setSample function, respectively.
#              Added global getDuration function to return the number of seconds in a sound
#
# 10 July 2007: (Pam Cutter, Kalamazoo College)
#              Added a global duplicateSound function
# 11 July 2007: (Pam Cutter, Kalamazoo College)
#              Added global addTextWithStyle function to allow users to add text to images
#                  with different font styles.
#
# 17 July 2007: (Pam Cutter, Kalamazoo College)
#              Added 7global addOval, addOvalFilled, addArc and addArcFilled functions.
#              Added global getNumSamples function as more meaningful name for getLength of a sound.
#
# 19 July 2007: (Pam Cutter, Kalamazoo College)
#              Modified the SoundExplorer class to be consistent with sounds in JES
#                  starting at sample index 1.
#              Modified the PictueExplorer class to initially show color values from
#            pixel 1,1, instead of 0,0.
#
# 1 Nov 2007: Added __add__ and __sub__ to Color class (BrianO)
# 29 Apr 2008: Changed makeEmptySound to take an integer number of samples
#          Added optional second argument to makeEmptySound for sampleRate
# 6 June 2008: Added a check for forward slash in a directory path in makeMovieFromInitialFile
#       This check should work with os.altsep, but it does not work with Jython 2.2.
#       This should be fixed again at a later date.
# 27 June 2008: Added optional input to setMediaFolder and setMediaPath.
#       Added showMediaFolder and showMediaPath methods.
# 11 July 2007: Removed showMediaFolder and showMediaPath for no-arg version of getMediaPath/getMediaFolder.
#       Added generic explore method. 
# 15 July 2007: Added no-arg option for setLibPath

# TODO:
## Fix HSV/RGB conversions -- getting a divide by zero error when max=min

import sys
import os
import math
import tempfile
import numbers
import threading
import collections
import time
import traceback

try:
    #Use Qt for everything
    #Attempt to use PyQt5
    import PyQt5.QtGui as QtGui
    import PyQt5.QtCore as QtCore
    import PyQt5.QtWidgets as QtWidgets
    import PyQt5.QtMultimedia as QtMultimedia #This is for sound/video
    Qt_VERSION = 5
except ImportError:
    #Use Qt4 for everything
    import PyQt4.QtGui as QtGui
    QtWidgets = QtGui
    import PyQt4.QtCore as QtCore
    import PyQt4.QtMultimedia as QtMultimedia #This is for sound/video
    Qt_VERSION = 4
    #Don't Use PIL for images
    #except one case
    import PIL

import wave #This is for reading sound file metadata

# Create an PyQt application object.
#If we're running in Canopy, there already is one
root = QtWidgets.QApplication.instance()
if root is None:
    #We're not running in Canopy
    #Need to launch a new application
    root = QtWidgets.QApplication(sys.argv)
#import tkinter
#from tkinter import filedialog
#from tkinter.colorchooser import askcolor
#import threading
#import org.python.core.PyString as String
#root = tkinter.Tk()
#root.withdraw()

#roots = []

# Support a media shortcut

#mediaFolder = JESConfig.getMediaPath()
#if ( mediaFolder == "" ):
mediaFolder = os.getcwd() + os.sep
#Before the user sets a folder, it should default to the current working directory
mediaFolderSet = False
# Store last pickAFile() opening
lastFilePath = None
#Use the last file path when picking a file/folder?
useLastFilePath = True

true = 1
false = 0

#List of things to keep around
keepAround = []

#Check supported image types
suppTypes = QtGui.QImageReader.supportedImageFormats()
supportedImageTypes = set([])
for typ in suppTypes:
    supportedImageTypes.add(str(typ)[2:-1])

#Is the type of this file supported?
def isSupportedImageFormat(fname):
    inddot = fname.rfind(".")
    if inddot == -1:
        tstr = fname
    else:
        tstr = fname[inddot+1:]
    return tstr.lower() in supportedImageTypes

#Error reporting structure
#Lets us refactor error reporting by changing only one line of code!
def reportErrorToUser(errType, msg):
    #Create the exception object
    error = errType(msg)
    #First, print a nice friendly error message to the user
    #To do that, we need the current stack
    stack_sum = list(traceback.format_stack())
    #Reverse the stack, so we can process it from bottom to top
    stack_sum.reverse()
    #Stages:
    #1: in media.py, don't report errors
    #2: outside media.py but inside user code, do report errors
    #3: above user code (e.g. in Canopy code), don't report errors
    stage = 1
    #List to include stage 2 frames
    ok_frames = []
    for frame in stack_sum:
        #Transition criterion from stage 1 to stage 2
        if stage == 1 and '%smedia.py'%os.sep not in frame:
            stage = 2
        if stage == 2:
            #Transition criterion from stage 2 to stage 3
            if '<module>' in frame:
                stage = 3
                #Make it clear that this is referring to the Command Prompt
                linebreak_index = frame.find("\n")
                frame = "  Thing you typed in the Command Prompt" +\
                    frame[linebreak_index:]
            ok_frames.append(frame)
    #We want to display the frames in the correct order, so we reverse again.
    ok_frames.reverse()
    #Print the nice message
    print("An error occurred. You are about to get a scary Python traceback.")
    print("But first, here's some info in English to help you out.")
    print()
    print("The error message is:\n  %s"%msg)
    print()
    print("The error type is:\n  %s"%type(error).__name__)
    print()
    print("The following are the primary places you should look "
        "for the mistake:")
    print()
    for frame in ok_frames:
        print(frame)
    #Pause for a second so the user can think about what they've done
    sleep(1)
    #Raise the exception
    raise error

#Shortcut for ValueError reporting
def repValError(msg):
    reportErrorToUser(ValueError, msg)

#Shortcut for TypeError reporting
def repTypeError(msg):
    reportErrorToUser(TypeError, msg)

#Done
def setMediaPath(file=None):
    """
        Takes a directory as input. JES then will look for files in that
        directory unless given a full path, i.e. one that starts with "c:\".
        You can leave out the directory. If you do, JES will open up a file
        chooser to let you select a directory.

        :param file: The directory you want to set as the media folder (optional)
    """
    global mediaFolder
    global mediaFolderSet
    if(file == None):
        mediaFolder = pickAFolder()
    else:   
        mediaFolder = file
    #mediaFolder = getMediaPath()
    mediaFolderSet = True
    return mediaFolder

def getMediaPath( filename = "" ):
    """
        This function builds the whole path to the file you specify, as long as
        you've already used setMediaFolder() or setMediaPath() to pick out the
        place where you keep your media. If no filename is given, only the
        MediaPath will be returned. (Same as getMediaFolder)

        :param filename: the name of the file you want (optional)
        :return: the complete path to the file specified
    """
    if filename == "":
        return mediaFolder
    return mediaFolder + os.sep + filename
    #return FileChooser.getMediaPath( filename )

#Done
def setMediaFolder(directory=None):
    """
        Takes a directory as input. JES then will look for files in that
        directory unless given a full path, i.e. one that starts with "c:\".
        You can leave out the directory. If you do, JES will open up a file
        chooser to let you select a directory.

        :param directory: The directory you want to set as the media folder. (optional)
    """
    return setMediaPath(directory)

#New
#If you've set a media folder in the past and you want to instead
#start using your working directory again, you can "un-set" it here
def unsetMediaFolder():
    global mediaFolderSet
    mediaFolderSet = False

#New
#Should we use the last file's path for the next file choice?
def rememberLastFilePath(toggle=True):
    global useLastFilePath
    useLastFilePath = toggle

#Done
def setTestMediaFolder():
    global mediaFolder
    mediaFolder = os.getcwd() + os.sep

#Done
def getMediaFolder( filename = "" ):
    """
        This function builds the whole path to the file you specify, as long as
        you've already used setMediaFolder() or setMediaPath() to pick out the
        place where you keep your media. If no filename is given, only the
        MediaFolder will be returned.

        :param filename: the name of the file you want (optional)
        :return: the complete path to the file specified
    """
    return getMediaPath(filename)

#Done
def showMediaFolder():
    global mediaFolder
    global mediaFolderSet
    if mediaFolderSet:
        print("The media path is currently: ",mediaFolder)
    else:
        print("The media path is not currently set; your working directory is: ",os.getcwd())

#Done
def getShortPath(path):
    """
        Takes a file path as input and returns the short version of that path.

        :param path: a path to a file, as a string
        :return: a shorter, non-absolute version of that path
    """
    dirs = path.split(os.sep)
    if len(dirs) < 1:
        return "."
    elif len(dirs) == 1:
        return dirs[0]
    else:
        return (dirs[len(dirs) - 2] + os.sep + dirs[len(dirs) - 1])

#Done
def setLibPath(directory=None):
    """
        Allows you to add a directory where JES can look for modules that you
        want to be able to import.

        :param directory: a string path to a directory. (optional)
    """
    if(directory == None):
        directory = pickAFolder()
    if(os.path.isdir(directory)):
        sys.path.append(directory)
    else:
        #print("Note: There is no directory at ",directory)
        #raise ValueError
        repValError("Note: There is no directory at "+str(directory))
    return directory

#This is not actually a media function
#Instead, it prints lists better
def betterPrint(val):
    print(recursive_str(val))

#Recursively call str on all components of val
#If val is not a sequence type, it's just str
#No need to call directly
#This is called by betterPrint
def recursive_str(val):
    if isinstance(val, collections.abc.Sequence) and not isinstance(val, str):
        #It's a sequence; recurse!
        return str(type(val)(map(str, val)))
    else:
        return str(val)

#Like time.sleep, but continues to play sounds
def sleep(secs):
    cur_time = time.time()
    while time.time() - cur_time < secs:
        QtWidgets.QApplication.processEvents()

#Sample class
#A Sample knows its value, its position, and the Sound it's from
class Sample:
    #Constructor
    #Takes a Sound and a position
    #Finds the value
    def __init__(self, sound, pos):
        self.sound = sound
        self.pos = pos
        self.value = sound.getSampleValue(pos)
    
    #Convert to a printable string
    def __str__(self):
        return 'Sample at ' + str(self.pos) + ' with value ' + str(self.value)
    
    #Get the Sample's value
    def getValue(self):
        return self.value
    
    #Set the Sample's value
    def setValue(self, newVal):
        #Update the Sound
        self.sound.setSampleValueRaw(self.pos, newVal)
        #Update the Sample's internal value
        self.value = newVal
    
    #Get the Sound object
    def getSound(self):
        return self.sound
    
    #Get the position
    def getIndex(self):
        return self.pos

#Sound class
#Only supports WAV for now
class Sound:
    #Constants
    SAMPLE_RATE = 22050
    NUM_CHANNELS = 1
    SAMPLE_SIZE = 16
    
    #Default audio output device
    AUDIO_DEVICE = QtMultimedia.QAudioDeviceInfo.defaultOutputDevice()
    
    #Constructor
    def __init__(self, arg1, arg2 = None):
        #arg1 can be a filename, a number of samples, or a Sound
        #arg2, if provided, is a sample rate
        #super().__init__()
        if isinstance(arg1, Sound):
            #arg1 is a Sound. Copy it.
            self.fileName = None #It doesn't duplicate this part
            # #Instead, use a temporary file, which gets changed
            # #if they save the sound
            # self.tempfile = tempfile.mkstemp(suffix = '.wav')
            #self.file = QFile(arg1.fileName)
            self.numSamples = arg1.numSamples
            self.sampleRate = arg1.sampleRate
            self.sampleSize = arg1.sampleSize
            self.numChannels = arg1.numChannels
            #Copy the raw data
            self.data = bytearray(arg1.data)
            #self.writeFile(self.tempfile[1])
            #self.file = QFile(self.tempfile[1])
        elif isinstance(arg1, str):
            #arg1 is a file name
            self.fileName = arg1
            #self.file = QFile(self.fileName)
            #Get the metadata
            wav = wave.open(self.fileName)
            self.sampleRate = wav.getframerate()
            self.sampleSize = wav.getsampwidth() * 8
            self.numChannels = wav.getnchannels()
            self.numSamples = wav.getnframes()*self.numChannels
            #Get the raw data
            self.data = bytearray(wav.readframes(self.numSamples))
            wav.close()
        elif isinstance(arg1, int):
            #arg1 is a number of samples
            self.numSamples = arg1
            # #Apparently the number of samples needs to be even or everything breaks?
            # if self.numSamples % 2 == 1:
            #     self.numSamples += 1
            if arg2 is None:
                self.sampleRate = Sound.SAMPLE_RATE
            else:
                self.sampleRate = arg2
            self.fileName = None
            self.numChannels = Sound.NUM_CHANNELS
            self.sampleSize = Sound.SAMPLE_SIZE
            #Blank data
            self.data = bytearray([0 for i in range(self.numSamples * self.sampleSize)])
            #self.file = None
            # #Use a temporary file, which gets changed
            # #if they save the sound
            # #TODO instead just send the sound data directly
            # self.tempfile = tempfile.mkstemp(suffix = '.wav')
            
        self.setUpFormat()
        #Tuples (QBuffer, QByteArray, QAudioOutput) used for playing multiple instances
        self.buffs = []
        #Cleanup lock
        self.cleanupLock = threading.Lock()
        #self.isPlaying = False
        #Set up "Samples" representation of data
        #This is clunky but "necessary" for efficiency of JES operations
        self.setUpSampleObjects()
        # #For blocking play
        # self.blockEvent = None
        if self.numChannels == 2:
            print("Warning: Your sound is stereo")
        if self.sampleRate != Sound.SAMPLE_RATE:
            print("Warning: Your sound does not have sample rate %d; it's %d"%\
                (Sound.SAMPLE_RATE, self.sampleRate))
        if self.sampleSize != Sound.SAMPLE_SIZE:
            print("Warning: Your sound does not have sample size %d; it's %d"%\
                (Sound.SAMPLE_SIZE, self.sampleSize))
    
    def setUpFormat(self):
        #Create the audio format
        self.format = QtMultimedia.QAudioFormat()
        self.format.setCodec('audio/pcm')
        self.format.setSampleRate(self.sampleRate)
        self.format.setSampleSize(self.sampleSize)
        self.format.setChannelCount(self.numChannels)
        #This is a WAV thing
        if self.sampleSize == 8:
            self.format.setSampleType(QtMultimedia.QAudioFormat.UnSignedInt)
            self.min_sample = 0
            self.max_sample = 256
        #elif self.sampleSize == 16:
        else:
            self.format.setSampleType(QtMultimedia.QAudioFormat.SignedInt)
            self.min_sample = -2**(self.sampleSize-1)
            self.max_sample = 2**(self.sampleSize-1)-1
        self.format.setByteOrder(QtMultimedia.QAudioFormat.LittleEndian)
        #print(self.sampleRate, self.sampleSize, self.numChannels)
    
    #Convert to string
    def __str__(self):
        ret = "Sound"
        fileName = self.fileName

        #if there is a file name then add that to the output
        if fileName is not None:
            ret = ret + " file: " + fileName

        #add the length in frames
        ret = ret + " number of samples: " + str(self.getLengthInFrames())

        return ret
    
    #Number of sample
    def getLengthInFrames(self):
        return self.numSamples
    
    #Get a "slice" of the raw data
    def getDataSlice(self, start, stop):
        return self.data[start * (self.sampleSize//8):stop * (self.sampleSize//8)]
    
    #Play the sound
    #Do nothing if it's already playing
    #Play from start to stop (default is the whole sound)
    def play(self, start=0, stop=0):
        #if not self.isPlaying:
        
        ##Clean up zombie processes, if somehow there are some
        #self.cleanUpResources()
        
        #Make start and stop both positive
        if start < 0:
            newStart = self.numSamples + start
        else:
            newStart = start
        if stop <= 0:
            newStop = self.numSamples + stop
        else:
            newStop = stop
                
        qba = QtCore.QByteArray(self.getDataSlice(newStart, newStop))
        buff = QtCore.QBuffer(qba)
        audioOutput = QtMultimedia.QAudioOutput(Sound.AUDIO_DEVICE, self.format)
        self.buffs.append((buff, qba, audioOutput))
        #print("Still alive")
        #worked = self.file.open(QIODevice.ReadOnly)
        #worked = self.buff.open(QIODevice.ReadOnly)
        worked = self.buffs[-1][0].open(QtCore.QIODevice.ReadOnly)
        if not worked:
            #Clean up the corrupted buffer
            del self.buffs[-1]
            raise IOError("Failed to open sound data stream")
        #print(worked)
        
        #Is it supported?
        if not Sound.AUDIO_DEVICE.isFormatSupported(self.format):
            #Clean up the corrupted buffer
            del self.buffs[-1]
            raise RuntimeError("Sound format not supported")
    
        #self.audioOutput = QAudioOutput(Sound.AUDIO_DEVICE, self.format)
        
        #worked = QObject.connect(self.audioOutput, SIGNAL('stateChanged(QAudio.State)'), self, SLOT('finishedPlaying()'))
        #worked = QObject.connect(self.audioOutput, SIGNAL('stateChanged'), self, SLOT('finishedPlaying(int)'))
        #worked = self.audioOutput.stateChanged.connect(self.finishedPlaying)
        #self.audioOutput.stateChanged.connect(self.finishedPlaying)
        self.buffs[-1][-1].stateChanged.connect(self.finishedPlaying)
        #if not worked:
        #    raise RuntimeError("Signal binding failed")
        #connect(audioOutput,SIGNAL(stateChanged(QAudio.State)),SLOT(finishedPlaying(QAudio.State)))
        #self.audioOutput.start(self.file)
        #self.audioOutput.start(self.buffs[-1][0])
        self.buffs[-1][-1].start(self.buffs[-1][0])
        QtWidgets.QApplication.processEvents()
            #self.isPlaying = True
        #return audioOutput
    
    #Plays a sound, and blocks until done
    def blockingPlay(self, start=0, stop=0):
        #thrd = threading.Thread(target = self.play())
        #thrd.start()
        #self.blockingEvent = threading.Event()
        self.play(start, stop)
        # cv = threading.Condition()
        # cv.acquire()
        # while len(self.buffs) > 0:
        #     cv.wait(0.01)
        # #cv.wait_for(lambda: len(self.buffs) == 0)
        # cv.release()
        while len(self.buffs) > 0:
            #Hang around here
            QtWidgets.QApplication.processEvents() #YES!!!!!
        #self.blockingEvent.wait()
        #self.blockingEvent = None
        #thrd.join()
        #time.sleep(2)
    
    #Is the sound currently playing?
    def isPlaying(self):
        return len(self.buffs) > 0
    
    #Stop the sound from playing (however many times it's currently playing)
    def stopPlaying(self):
        #Acquire the cleanup lock
        self.cleanupLock.acquire()
        try:
            #Clean up ALL instances of playing the sound
            buffs = list(self.buffs)
            for i in range(len(buffs)-1, -1, -1):
                self.buffs[i][-1].stop()
                self.buffs[i][0].close()
                del self.buffs[i]
        finally:
            #Release the lock
            self.cleanupLock.release()
    
    #Go through the list of playing sound resources and destroy
    #the ones that have finished playing
    def cleanUpResources(self):
        #Acquire lock; don't want multiple threads in here at once
        self.cleanupLock.acquire()
        try:
            #Clean up finished instances of playing the sound
            buffs = list(self.buffs)
            for i in range(len(buffs)-1, -1, -1):
                if buffs[i][0].atEnd():
                    #This one's done
                    self.buffs[i][0].close()
                    self.buffs[i][-1].stop()
                    del self.buffs[i]
            # if len(self.buffs) == 0 and self.blockingEvent is not None:
            #     #Wake up the block!
            #     self.blockingEvent.set()
        finally:
            QtWidgets.QApplication.processEvents()
            #Release the lock
            self.cleanupLock.release()
    
    #It was working with files, but failed with buffers (triggered too soon)
    #Workaround is to manually call the clean up method
    def finishedPlaying(self, state):
        #print("yo", state)
        #state = self.audioOutput.state()
        #Is it finished?
        if state == QtMultimedia.QAudio.IdleState:
            # self.audioOutput.stop()
            # #self.file.close()
            # self.buff.close()
            # self.isPlaying = False
            # print("It's done!")
            self.cleanUpResources()
    
    #Write this sound to the given
    def writeToFile(self, fil):
        fd = wave.open(fil, 'wb')
        fd.setnchannels(self.numChannels)
        fd.setnframes(self.numSamples)
        fd.setframerate(self.sampleRate)
        fd.setsampwidth(self.sampleSize // 8)
        fd.writeframes(self.data)
        fd.close()
    
    #Represent the sound as an image of the given dimensions
    #Used by Sound Explorer
    def getImageRep(self, width, height):
        #Find the height in the image of a given sample value
        def findY(sval):
            if self.sampleSize == 8:
                return int((-height/256)*sval + height-1)
            #elif self.sampleSize == 16:
            #    return int((-height/65536)*sval + height/2)
            else:
                return int((-height/(2**self.sampleSize))*sval + height/2)
        
        #Create an empty black picture
        #ret = makeEmptyPicture(width, height, black)
        #(Hieu) using QPixmap instead of creating a Picture object !!!!!!
        #ret = makeEmptyPicture2(width, height, black)
        ret = QtGui.QPixmap(width,height)
        ret.fill(QtGui.QColor(*black.getRGB()))
        
        #Add the waveform, adjusted for proper step size
        lastY = findY(getSampleValueAt(self, 0))
        stepSize = max(self.numSamples // width, 1)
        for i in range(stepSize, self.numSamples, stepSize):
            curY = findY(getSampleValueAt(self, i))
            addLine1(ret, i//stepSize-1, lastY, i//stepSize, curY, white)
            lastY = curY
            
        #Add the zero line
        if self.sampleSize == 8:
            addLine1(ret, 0, height-1, width-1, height-1, cyan)
        #elif self.sampleSize == 16:
        else:
            addLine1(ret, 0, height//2, width-1, height//2, cyan)
        
        return ret
    
    def setUpSampleObjects(self):
        ss = self.sampleSize // 8
        if len(self.data) % ss != 0:
            #The samples are corrupted
            raise ValueError("You have half a sample at the end. Not sure why.")
        self.samples = []
        #Convert the binary stream to integers by sample size
        #Make sure to use two's complement
        for i in range(self.numSamples):
            self.samples.append(Sample(self, i))
    
    #Get the ith sample value
    def getSampleValue(self, i):
        if self.sampleSize == 8:
            #This is easy
            val = int(self.data[i])
        #elif self.sampleSize == 16:
        else:
            #This is harder
            #val = int.from_bytes(self.data[2*i:2*i+2], 'little', signed=True)
            nbytes = self.sampleSize//8
            val = int.from_bytes(self.data[nbytes*i:nbytes*i+nbytes], 'little', signed=True)
            # val = self.data[2*i] * 256 + self.data[2*i+1]
            # if val >= 32768:
            #     #Need to make it be negative
            #     val -= 65536
        return val
    
    def getSample(self, i):
        return self.samples[i]
    
    #Get all the samples, as a list
    #DO NOT PRINT THIS!!!
    def getSamples(self):
        # ss = self.sampleSize // 8
        # if len(self.data) % ss != 0:
        #     #The samples are corrupted
        #     raise ValueError("You have half a sample at the end. Not sure why.")
        # ret = []
        # #Convert the binary stream to integers by sample size
        # #Make sure to use two's complement
        # for i in range(self.numSamples):
        #     ret.append(self.getSample(i))
        # return ret
        return self.samples
    
    #Set a sample value
    #DOES change the Sample objects
    def setSampleValue(self, pos, value):
        #Clipping
        val = value
        if val < self.min_sample:
            val = self.min_sample
        elif val > self.max_sample:
            val = self.max_sample
        # if val < -32768:
        #     val = -32768
        # elif val > 32767:
        #     val = 32767
        self.samples[pos].setValue(val)
    
    #Set the value of the sample at position pos to value
    #DO NOT CALL THIS IF YOU ARE USING Sample OBJECTS!
    #This is called by Sample to update the Sound
    #It will desync the Sample objects if you call it directly
    def setSampleValueRaw(self, pos, value):
        if self.sampleSize == 8:
            #This is easy
            self.data[pos] = value
        #elif self.sampleSize == 16:
        else:
            #This is harder
            # #First, un-two's-complement it
            # val = value
            # if val < 0:
            #     val = val + 65536
            # #Then, extract the bytes
            # hiByte = val // 256
            # loByte = val % 256
            # #Finally, set the data
            # self.data[2*pos] = hiByte
            # self.data[2*pos+1] = loByte
            nbytes = self.sampleSize//8
            val = value.to_bytes(nbytes, 'little', signed=True)
            self.data[nbytes*pos:nbytes*pos+nbytes]  = val
            #val = value.to_bytes(2, 'little', signed=True)
            #self.data[2*pos:2*pos+2]  = val
    
    #What is the sample size, in bits? 
    #the maximum amplitude (sample value) to be stored (in bits) at each sample (max value for 16 bits is 32767)
    def getSampleSize(self):
        return self.sampleSize
        
    #What is the sampling rate?
    #The rate at which samples are collected is the sample rate (# of samples/duration of sound) 
    def getSamplingRate(self):
        return self.sampleRate
    
    #DOES change the Sample objects
    #TODO: raise error for incompatible rate - only support for rate =0.5, 2 now
    def setSamplingRate(self, rate):
        self.sampleRate = int(self.sampleRate * rate)
      
    #(Hieu) Plays the specified segment of this sound at the given sample rat (only support for rate =2.0, 0.5).
    #TODO: Still don't know why the sound still keep original setting (sample rate) when it finish
    def playAtRateInRange(self, rate, start=0, stop=0, isBlocking=0):
        self.setSamplingRate(rate)
        self.setUpFormat()
        if isBlocking:
            self.blockingPlay(start, stop)
        else: 
            self.play(start, stop)
        # while(not self.isPlaying()):
        #     a = 1
        # self.setSamplingRate(1.0/rate)
        # self.setUpFormat()
    
    #Print the metadata of the sound
    def printMetadata(self):
        if self.numChannels == 2:
            print("Num Samples: %d (%d per channel)"%\
                (self.numSamples, self.numSamples//2))
        else:
            print("Num Samples: %d"%self.numSamples)
        print("Sample Rate: %d"%self.sampleRate)
        print("Sample Size: %d"%self.sampleSize)
        print("Num Channels: %d"%self.numChannels)
 
                                   
##
## Global sound functions
##
#Done
def makeSound(filename):
    """
        Takes a filename as input, reads the file, and creates a sound from it.
        Returns the sound.

        :param filename: a string path of a wav file
        :return: the sound created from the file at the given path
    """
    global mediaFolder
    if not isinstance(filename, str):
        repTypeError("makeSound(filename): argument not a string: "+str(filename))
    if not os.path.isabs(filename):
        filename = mediaFolder + filename
    if not os.path.isfile(filename):
        #print("There is no file at "+filename)
        #raise ValueError
        repValError("There is no file at "+filename)
    return Sound(filename)


# MMO (1 Dec 2005): capped size of sound to 600
# Brian O (29 Apr 2008): changed first argument to be number of samples, added optional 2nd argument of sampling rate
#Done
def makeEmptySound(numSamples, samplingRate = Sound.SAMPLE_RATE):
    """
        Takes one or two integers as input. Returns an empty Sound object with
        the given number of samples and (optionally) the given sampling rate.
        Default rate is 22050 bits/second. The resulting sound must not be longer
        than 600 seconds. Prints an error statement if numSamples or
        samplingRate are less than 0, or if (numSamples/samplingRate) > 600.

        :param numSamples: the number of samples in the sound
        :param samplingRate: the integer value representing the number of samples
                                per second (optional)
        :return: an empty sound with the given number of samples and sampling rate
    """
    if numSamples <= 0 or samplingRate <= 0:
        #print("makeEmptySound(numSamples[, samplingRate]): numSamples and samplingRate must each be greater than 0")
        #raise ValueError
        repValError("makeEmptySound(numSamples[, samplingRate]): numSamples and samplingRate must each be greater than 0")
    if (numSamples/samplingRate) > 600:
        #print("makeEmptySound(numSamples[, samplingRate]): Created sound must be less than 600 seconds")
        #raise ValueError
        repValError("makeEmptySound(numSamples[, samplingRate]): Created sound must be less than 600 seconds") 
    if not isinstance(numSamples, int):
        repTypeError("makeEmptySound(numSamples[, samplingRate]): numSamples must be an integer")  
    if not isinstance(samplingRate, int):
        repTypeError("makeEmptySound(numSamples[, samplingRate]): samplingRate must be an integer")  
    return Sound(numSamples, samplingRate)
#    if size > 600:
#        #print "makeEmptySound(size): size must be 600 seconds or less"
#        #raise ValueError
#        repValError("makeEmptySound(size): size must be 600 seconds or less")
#    return Sound(size * Sound.SAMPLE_RATE)


# Brian O (5 May 2008): Added method for creating sound by duration
#Done
def makeEmptySoundBySeconds(seconds, samplingRate = Sound.SAMPLE_RATE):
    """
        Takes a floating point number and optionally an integer as input. Returns
        an empty Sound object of the given duration and (optionally) the given
        sampling rate. Default rate is 22050 bits/second. If the given arguments
        do not multiply to an integer, the number of samples is rounded up.
        Prints an error statement if duration or samplingRate are less than 0,
        or if duration > 600

        :param seconds: the time in seconds for the duration of the sound
        :param samplingRate: the integer value representing the number of samples
                                per second of sound (optional)
        :return: an empty sound
    """
    if seconds <= 0 or samplingRate <= 0:
        #print("makeEmptySoundBySeconds(numSamples[, samplingRate]): numSamples and samplingRate must each be greater than 0")
        #raise ValueError
        repValError("makeEmptySoundBySeconds(numSamples[, samplingRate]): numSamples and samplingRate must each be greater than 0")
    if seconds > 600:
        #print("makeEmptySoundBySeconds(numSamples[, samplingRate]): Created sound must be less than 600 seconds")
        #raise ValueError
        repValError("makeEmptySoundBySeconds(numSamples[, samplingRate]): Created sound must be less than 600 seconds")
    return Sound(int(seconds * samplingRate), samplingRate)


# PamC: Added this function to duplicate a sound
#Done
def duplicateSound(sound):
    """
        Takes a sound as input and returns a new Sound object with the same
        Sample values as the original.

        :param sound: the sound you want to duplicate
        :return: a new Sound object with the same Sample values as the original
    """
    if not isinstance(sound, Sound):
        #print("duplicateSound(sound): Input is not a sound")
        #raise ValueError
        repTypeError("duplicateSound(sound): Input is not a sound")
    return Sound(sound)

#NEW
#Print the metadata of a Sound
def printSoundMetadata(sound):
    """
        Takes a sound as input and displays the number of samples, sample rate,
        sample size, and number of channels (1 or 2) of the sound.

        :param sound: A Sound, the sound you want to extract the samples from
        :return: A collection of all the samples in the sound
    """
    if not isinstance(sound, Sound):
        #print("getSamples(sound): Input is not a sound")
        #raise ValueError
        repTypeError("getSoundMetadata(sound): Input is not a sound")
    sound.printMetadata()

#Done
def getSamples(sound):
    """
        Takes a sound as input and returns the Samples in that sound.

        :param sound: A Sound, the sound you want to extract the samples from
        :return: A collection of all the samples in the sound
    """
    if not isinstance(sound, Sound):
        #print("getSamples(sound): Input is not a sound")
        #raise ValueError
        repTypeError("getSamples(sound): Input is not a sound")
    return sound.getSamples()


#Done
def play(sound):
    """
        Plays a sound provided as input.

        :param sound: the sound you want to be played
    """
    if not isinstance(sound,Sound):
        #print "play(sound): Input is not a sound"
        #raise ValueError
        repTypeError("play(sound): Input is not a sound")
    sound.play()


#DONE!!!!!!!!!
#(Note: "blocking main thread" includes infinite loop)
def blockingPlay(sound):
    """
        Plays the sound provided as input, and makes sure that no other sound
        plays at the exact same time. (Try two play's right after each other.)

        :param sound: the sound that you want to play
    """
    if not isinstance(sound,Sound):
        #print "blockingPlay(sound): Input is not a sound"
        #raise ValueError
        repTypeError("blockingPlay(sound): Input is not a sound")
    sound.blockingPlay()


# Buck Scharfnorth (27 May 2008): Added method for stopping play of a sound
#Done
def stopPlaying(sound):
    """
        Stops a sound that is currently playing.
        
        :param sound: the sound that you want to stop playing
    """
    if not isinstance(sound,Sound):
        #print "stopPlaying(sound): Input is not a sound"
        #raise ValueError
        repTypeError("stopPlaying(sound): Input is not a sound")
    sound.stopPlaying()


#(Hieu) plays a sound at a given time (2.0 is twice as fast, 0.5 is half as fast) (only for rate = 0.5, 1.0 or 2.0) 
# TODO: has not raise error for incorrect second input  
def playAtRate(sound,rate):
    if not isinstance(sound, Sound):
        #print "playAtRate(sound,rate): First input is not a sound"
        #raise ValueError
        repTypeError("playAtRate(sound,rate): First input is not a sound")
    newSound = duplicateSound(sound)
    newSound.playAtRateInRange(rate)

# def playAtRate(sound,rate):
#     #if not isinstance(sound, Sound):
#     #    #print "playAtRate(sound,rate): First input is not a sound"
#     #    #raise ValueError
#     #    repTypeError("playAtRate(sound,rate): First input is not a sound")
#     ## sound.playAtRate(rate)
#     #sound.playAtRateDur(rate,sound.getLength())
#     pass #TODO
# 
# def playAtRateDur(sound,rate,dur):
#     #if not isinstance(sound,Sound):
#     #    #print "playAtRateDur(sound,rate,dur): First input is not a sound"
#     #    #raise ValueError
#     #    repTypeError("playAtRateDur(sound,rate,dur): First input is not a sound")
#     #sound.playAtRateDur(rate,dur)
#     pass #TODO

#20June03 new functionality in JavaSound (ellie)
def playInRange(sound,start,stop):
    if not isinstance(sound, Sound):
        repTypeError("playInRange(sound,start,stop): First input is not a sound")
    elif not isinstance(start, int):
        repTypeError("playInRange(sound,start,stop): Second input is not an integer")
    elif start < 0:
        repValError("playInRange(sound,start,stop): Second input cannot be negative")
    elif start >= getNumSamples(sound):
        repValError("playInRange(sound,start,stop): Second input cannot be greater than the length of the sound, which is " + getNumSamples(sound))
    elif not isinstance(stop, int):
        repTypeError("playInRange(sound,start,stop): Third input is not an integer")
    elif stop < 0:
        repValError("playInRange(sound,start,stop): Third input cannot be negative")
    elif stop >= getNumSamples(sound):
        repValError("playInRange(sound,start,stop): Third input cannot be greater than the length of the sound, which is " + getNumSamples(sound))
    elif start > stop:
        repValError("playInRange(sound,start,stop): Second input cannot exceed third input")
    # sound.playInRange(start,stop)
    #sound.playAtRateInRange(1,start-Sound._SoundIndexOffset,stop-Sound._SoundIndexOffset)
    sound.play(start, stop)

# #20June03 new functionality in JavaSound (ellie)
#Done
def blockingPlayInRange(sound,start,stop):
    if not isinstance(sound, Sound):
        repTypeError("playInRange(sound,start,stop): First input is not a sound")
    elif not isinstance(start, int):
        repTypeError("playInRange(sound,start,stop): Second input is not an integer")
    elif start < 0:
        repValError("playInRange(sound,start,stop): Second input cannot be negative")
    elif start >= getNumSamples(sound):
        repValError("playInRange(sound,start,stop): Second input cannot be greater than the length of the sound, which is " + getNumSamples(sound))
    elif not isinstance(stop, int):
        repTypeError("playInRange(sound,start,stop): Third input is not an integer")
    elif stop < 0:
        repValError("playInRange(sound,start,stop): Third input cannot be negative")
    elif stop >= getNumSamples(sound):
        repValError("playInRange(sound,start,stop): Third input cannot be greater than the length of the sound, which is " + getNumSamples(sound))
    elif start > stop:
        repValError("playInRange(sound,start,stop): Second input cannot exceed third input")
    sound.blockingPlay(start, stop)
# 
#20June03 new functionality in JavaSound (ellie)
#(Hieu 23Jan18): 
def playAtRateInRange(sound,rate,start,stop):
        if not isinstance(sound,Sound):
                #print "playAtRateInRAnge(sound,rate,start,stop): First input is not a sound"
                #raise ValueError
            repTypeError("playAtRateInRAnge(sound,rate,start,stop): First input is not a sound")
        newSound = duplicateSound(sound)
        newSound.setSamplingRate(rate)
        newSound.play(start,stop)
        #sound.playAtRateInRange(rate,start - Sound._SoundIndexOffset,stop - Sound._SoundIndexOffset)
        #pass #TODO

# #20June03 new functionality in JavaSound (ellie)
# def blockingPlayAtRateInRange(sound,rate,start,stop):
        # if not isinstance(sound, Sound):
        #         #print "blockingPlayAtRateInRange(sound,rate,start,stop): First input is not a sound"
        #         #raise ValueError
        #     repValError("blockingPlayAtRateInRange(sound,rate,start,stop): First input is not a sound")
        # newSound = duplicateSound(sound)
        # newSound.setSamplingRate(rate)
        # newSound.blockingPlay(start,stop)
        #sound.blockingPlayAtRateInRange(rate, start - Sound._SoundIndexOffset,stop - Sound._SoundIndexOffset)
        #pass #TODO

#New
#Is the sound currently playing?
def isPlaying(sound):
    if not isinstance(sound, Sound):
        #print "getSamplingRate(sound): Input is not a sound"
        #raise ValueError
        repTypeError("isPlaying(sound): Input is not a sound")
    return sound.isPlaying()

#Done
def getSamplingRate(sound):
    """
        Takes a sound as input and returns the number representing the number of
        samples in each second for the sound.

        :param sound: the sound you want to get the sampling rate from
        :return: the integer value representing the number of samples per second
    """
    if not isinstance(sound, Sound):
        #print "getSamplingRate(sound): Input is not a sound"
        #raise ValueError
        repTypeError("getSamplingRate(sound): Input is not a sound")
    return sound.getSamplingRate()

#Done
def setSampleValueAt(sound,index,value):
    """
        Takes a sound, an index, and a value (should be between -32768 and 32767),
        and sets the value of the sample at the given index in the given sound
        to the given value.

        :param sound: the sound you want to change a sample in
        :param index: the index of the sample you want to set
        :param value: the value you want to set the sample to
    """
    if not isinstance(sound, Sound):
        repTypeError("setSampleValueAt(sound,index,value): First input is not a sound")
    if index < 0:
        repValError("You asked for the sample at index: " + str( index ) + ".  This number is less than " + str(0) + ".  Please try" + " again using an index in the range [" + str(0) + "," + str ( getLength( sound ) - 1 ) + "].")
    if index > getLength(sound) - 1:
        repValError("You are trying to access the sample at index: " + str( index ) + ", but the last valid index is at " + str( getLength( sound ) - 1 ))
    sound.setSampleValue(index, int(value))

#Done
def getSampleValueAt(sound,index):
    """
        Takes a sound and an index (an integer value), and returns the value of
        the sample (between -32768 and 32767) for that object.

        :param sound: the sound you want to get the sample from
        :param index: the index of the sample you want to get the value of
        :return: the value of sample object at that index
    """
    if not isinstance(sound,Sound):
        repTypeError("getSampleValueAt(sound,index): First input is not a sound")
    if index < 0:
        repValError("You asked for the sample at index: " + str( index ) + ".  This number is less than 0.  Please try" + " again using an index in the range [" + str(0) + "," + str ( getLength( sound ) - 1) + "].")
    if index > getLength(sound) - 1:
        repValError("You are trying to access the sample at index: " + str( index ) + ", but the last valid index is at " + str( getLength( sound ) - 1 ))
    return sound.getSampleValue(index)

#Done
def getSampleObjectAt(sound,index):
    """
        Takes a sound and an index (an integer value), and returns the Sample
        object at that index.

        :param sound: the sound you want to get the sample from
        :param index: the index of the sample you want to get
        :return: the sample object at that index
    """
    if not isinstance(sound, Sound):
        repTypeError("getSampleObjectAt(sound,index): First input is not a sound")
    if index < 0:
        repValError("You asked for the sample at index: " + str( index ) + ".  This number is less than " + str(0) + ".  Please try" + " again using an index in the range [" + str(0) + "," + str ( getLength( sound ) - 1 ) + "].")
    if index > getLength(sound) - 1:
        repValError("You are trying to access the sample at index: " + str( index ) + ", but the last valid index is at " + str( getLength( sound ) - 1 ))
    return sound.getSample(index)

#New
#Get sample size, in bits
#Usually would be 16, but this code supports 8 as well
def getSampleSize(sound):
    if not isinstance(sound, Sound):
        repTypeError("getSampleSize(sound): Input is not a sound")
    return sound.getSampleSize()

#Done
def setSample(sample, value):
    if not isinstance(sample,Sample):
        repTypeError("setSample(sample,value): First input is not a Sample")
    ss = getSampleSize(getSound(sample))
    if ss == 8:
        vmax = 255
        vmin = 0
    elif ss == 16:
        vmax = 32767
        vmin = -32768
    #Clip
    if value > vmax:
        value = vmax
    elif value < vmin:
        value = vmin
    # Need to coerce value to integer
    sample.setValue( int(value) )

# PamC: Added this function to be a better name than setSample
#Done
def setSampleValue(sample, value):
    """
        Takes a Sample object and a value (should be between -32768 and 32767),
        and sets the sample to that value.

        :param sample: the sound sample you want to change the value of
        :param value: the value you want to set the sample to
    """
    setSample(sample, value)

#Done
def getSample(sample):
    if not isinstance(sample, Sample):
        repTypeError("getSample(sample): Input is not a Sample")
    return sample.getValue()

# PamC: Added this to be a better name for getSample
#Done
def getSampleValue(sample):
    """
        Takes a Sample object and returns its value (between -32768 and 32767). 
        (Formerly getSample)

        :param sample: a sample of a sound
        :return: the integer value of that sample
    """
    return getSample(sample)

#New
def getSampleIndex(sample):
    if not isinstance(sample, Sample):
        repTypeError("getSampleIndex(sample): Input is not a Sample")
    return sample.getIndex()

#Done
def getSound(sample):
    """
        Takes a Sample object and returns the Sound that it belongs to.

        :param sample: a sample belonging to a sound
        :return: the sound the sample belongs to
    """
    if not isinstance(sample,Sample):
        repTypeError("getSound(sample): Input is not a Sample")
    return sample.getSound()

#Done
def getLength(sound):
    """
        Takes a sound as input and returns the number of samples in that sound.

        :param sound: the sound you want to find the length of (how many
                        samples it has)
        :return: the number of samples in sound
    """
    if not isinstance(sound, Sound):
        repTypeError("getLength(sound): Input is not a Sound")
    return sound.getLengthInFrames()

# PamC: Added this function as a more meaningful name for getLength
#Done
def getNumSamples(sound):
    """
        Takes a sound as input and returns the number of samples in that sound.

        :param sound: the sound you want to find the length of (how many
                        samples it has)
        :return: the number of samples in sound
    """
    return getLength(sound)

# PamC: Added this function to return the number of seconds
# in a sound
#Done
def getDuration(sound):
    """
        Takes a sound as input and returns the number of seconds that sound lasts.

        :param sound: the sound you want to find the length of (in seconds)
        :return: the number of seconds the sound lasts
    """
    if not isinstance(sound, Sound):
        repTypeError("getDuration(sound): Input is not a Sound")
    return getLength(sound) / getSamplingRate(sound)

#New
#Frequency: Hertz
#Amplitude: Max/min of the sine wave (should be between 0 and 32767)
#Dur: Length, in seconds
def pureTone(freq, amp, dur):
    if not isinstance(freq, numbers.Number):
        repTypeError("pureTone(freq, amp, dur): freq must be a number")
    elif freq < 0:
        repValError("pureTone(freq, amp, dur): freq must be nonnegative")
    if not isinstance(amp, numbers.Number):
        repTypeError("pureTone(freq, amp, dur): amp must be a number")
    elif amp < 0 or amp > 32767:
        repValError("pureTone(freq, amp, dur): amp must be between 0 and 32767 (inclusive)")
    if not isinstance(dur, numbers.Number):
        repTypeError("pureTone(freq, amp, dur): dur must be a number")
    elif dur < 0:
        repValError("pureTone(freq, amp, dur): dur must be nonnegative")
    def getVal(i):
        return int(amp*math.sin((freq*2*math.pi)*i/Sound.SAMPLE_RATE))
        
    sound = makeEmptySoundBySeconds(dur)
    for i in range(int(dur * Sound.SAMPLE_RATE)):
        setSample(getSampleObjectAt(sound, i), getVal(i))
    return sound

#Done
def writeSoundTo(sound,filename):
    """
        Takes a sound and a filename (a string) and writes the sound to that
        file as a WAV file. (Make sure that the filename ends in '.wav' if you
        want the operating system to treat it right.)
        
        :param sound: the sound you want to write out to a file
        :param filename: the path to the file you want the picture written to
    """
    global mediaFolder
    if not os.path.isabs(filename):
        filename = mediaFolder + filename
    if not isinstance(sound, Sound):
        repTypeError("writeSoundTo(sound,filename): First input is not a Sound")
    sound.writeToFile(filename)

#New
def saveSound(sound):
    fil = pickASaveFile()
    if fil == None:
        print("No file selected; nothing saved.")
        return
    #Try to get a format
    #If no format given, yell at the user
    # dotloc = fil.rfind(".")
    # if dotloc == -1:
    #     repValError("Error: No file extension provided")
    #     #raise ValueError("Error: No file extension provided")
    if len(fil) < 4 or (fil[-4:] != '.wav' and fil[-4:] != '.WAV'):
        repValError("Error: Must specify .wav extension")
    writeSoundTo(sound, fil)

##
# Globals for styled text
##
#Done
def makeStyle(fontName,emph,size):
    """
        Makes a new "empty" picture and returns it to you. The width and height 
        must be between 0 and 10000. Default color is white.
        
        :param fontName: the name of the font you want in the style
                            (sansSerif, serif, mono)
        :param emph: the type of emphasis you want in the style 
                            (italic, bold, italic + bold, plain)
        :param size: the size of the font you want in the style
        :return: the style made from the inputs
    """
    ret = QtGui.QFont()
    #ret.setStyleName(fontName)
    ret.setPointSize(size)
    #if emph == sansSerif or emph == serif or emph == mono:
    #    ret.setStyleHint(emph)
    ret.setStyleHint(fontName)
    if emph == italic:
        ret.setStyle(emph)
    elif emph == bold or emph == plain:
        ret.setWeight(emph)
    return ret

sansSerif = QtGui.QFont.SansSerif
serif = QtGui.QFont.Serif
mono = QtGui.QFont.Monospace
italic = QtGui.QFont.StyleItalic
bold = QtGui.QFont.Bold
plain = QtGui.QFont.Normal

##
## Global color functions
##

# Buck Scharfnorth (28 May 2008): if bool == 1 colors will be (value % 256)
#                 if bool == 0 colors will be truncated to 0 or 255
# updated (13 May 2009): 
# THIS GLOBAL FUNCTION CHANGES JES SETTINGS - this value overwrites
# the value in the JES options menu.
def setColorWrapAround(bool):
    #JESConfig.getInstance().setSessionWrapAround( bool )
    pass #TODO

# Buck Scharfnorth (28 May 2008): Gets the current ColorWrapAround Value
def getColorWrapAround():
    #return JESConfig.getInstance().getSessionWrapAround()
    pass #TODO

# Buck Scharfnorth (28 May 2008): Modified to no longer assume the value is 0-255
#Done
def _checkPixel(raw):
    value = int(raw)
    if getColorWrapAround():
        value = (value % 256)
    else:
        if value < 0:
            value = 0
        if value > 255:
            value = 255
    return value

# this class is solely for the purpose of
# making makeLighter makeDarker work.
# both of these functions destructively modify a color
# and a color in java is a constant value so we have to put
# this python interface here
#
# Buck Scharfnorth (28 May 2008): Modified to no longer assume the value is 0-255
# and the gray Color constructor to allow only 1 color parameter (will take 2, but ignores the second)
class Color:
    def __init__(self,r,g=None,b=None):
        if b == None:
            #In this case, r should be a tuple or Color or QColor
            if isinstance(r, Color):
                self.r = r.getRed()
                self.g = r.getGreen()
                self.b = r.getBlue()
            elif isinstance(r, QtGui.QColor):
                self.r = r.red()
                self.g = r.green()
                self.b = r.blue()
            elif isinstance(r, int):
                #This case is necessary because of how QImage.pixel() works
                cl = QtGui.QColor(r)
                self.r = cl.red()
                self.g = cl.green()
                self.b = cl.blue()
            else:
                self.r = r[0]
                self.g = r[1]
                self.b = r[2]
            #if isinstance( r, awt.Color ) or isinstance( r, Color ):
            #    self.color = r
            #else:
            #    val = _checkPixel(r)
            #    self.color = awt.Color( val, val, val )
        else:
            # self.color = awt.Color(r,g,b)
            #self.color = awt.Color( _checkPixel(r), _checkPixel(g), _checkPixel(b) )
            if not isinstance(r, numbers.Number):
                repTypeError("First color component (red) not a number")
                #raise ValueError
            if not isinstance(g, numbers.Number):
                repTypeError("Second color component (green) not a number")
                #raise ValueError
            if not isinstance(b, numbers.Number):
                repTypeError("Third color component (blue) not a number")
                #raise ValueError
            self.r = r
            self.g = g
            self.b = b
        #Fix out-of-bounds
        self.validateColor()
    
    #If any component is not in range 0 to 255, fix that
    #If any component is not an integer, fix that
    def validateColor(self):
        if self.r < 0:
            self.r = 0
        elif self.r > 255:
            self.r = 255
        if self.g < 0:
            self.g = 0
        elif self.g > 255:
            self.g = 255
        if self.b < 0:
            self.b = 0
        elif self.b > 255:
            self.b = 255
        if not isinstance(self.r, int):
            self.r = int(self.r)
        if not isinstance(self.g, int):
            self.g = int(self.g)
        if not isinstance(self.b, int):
            self.b = int(self.b)

    def __str__(self):
        return "color r="+str(self.getRed())+" g="+str(self.getGreen())+" b="+str(self.getBlue())

    def __repr__(self):
        return "Color("+str(self.getRed())+", "+str(self.getGreen())+", "+str(self.getBlue())+")"

    def __eq__(self,newcolor):
        return ((self.getRed() == newcolor.getRed()) and (self.getGreen() == newcolor.getGreen()) and (self.getBlue() == newcolor.getBlue()))

    def __ne__(self,newcolor):
        return (not self.__eq__(newcolor))

    #def __tojava__(self, javaclass):
    #    if javaclass == awt.Color:
    #        return self.color
    #    else:
    #        return self

    #Added by BrianO
    def __add__(self, other):
        r = self.getRed() + other.getRed()
        g = self.getGreen() + other.getGreen()
        b = self.getBlue() + other.getBlue()

    # if(wrapAroundPixelValues):
    #    r = r % 256
    #    g = g % 256
    #    b = b % 256

    # return Color(r,g,b)
        #return Color( _checkPixel(r), _checkPixel(g), _checkPixel(b) )
        return Color(r, g, b)

    #Added by BrianO
    def __sub__(self, other):
        r = self.getRed() - other.getRed()
        g = self.getGreen() - other.getGreen()
        b = self.getBlue() - other.getBlue()

    # if(wrapAroundPixelValues):
    #    r = r % 256
    #    g = g % 256
    #    b = b % 256

    # return Color(r,g,b)
        #return Color( _checkPixel(r), _checkPixel(g), _checkPixel(b) )
        return Color(r, g, b)

    def setRGB(self, r, g, b):
    #    # self.color = awt.Color(r,g,b)
    #    self.color = awt.Color(_checkPixel(r), _checkPixel(g), _checkPixel(b))
        if not isinstance(r, numbers.Number):
            repTypeError("First color component (red) not a number")
            #raise ValueError
        if not isinstance(g, numbers.Number):
            repTypeError("Second color component (green) not a number")
            #raise ValueError
        if not isinstance(b, numbers.Number):
            repTypeError("Third color component (blue) not a number")
            #raise ValueError
        self.r = r
        self.g = g
        self.b = b
        self.validateColor()
    

    def getRed(self):
        #return self.color.getRed()
        return self.r

    def getGreen(self):
        #return self.color.getGreen()
        return self.g

    def getBlue(self):
        #return self.color.getBlue()
        return self.b

    def distance(self, othercolor):
        r = pow((self.getRed() - othercolor.getRed()),2)
        g = pow((self.getGreen() - othercolor.getGreen()),2)
        b = pow((self.getBlue() - othercolor.getBlue()) ,2)
        return math.sqrt(r+g+b)

    def makeDarker(self):
      #return self.color.darker()
        return Color(max(int(self.getRed() * 0.7), 0), max(int(self.getGreen() * 0.7), 0), max(int(self.getBlue() * 0.7), 0))

    def makeLighter(self):
      #return self.color.brighter()
        return Color(min(int(self.getRed() / 0.7), 255), min(int(self.getGreen() / 0.7), 255), min(int(self.getBlue() / 0.7), 255))
    
    def getRGB(self):
        return (self.getRed(), self.getGreen(), self.getBlue())
    
    #Convert to QColor
    def toQColor(self):
        return QtGui.QColor(*self.getRGB())
    
    #Convert to color integer
    def toQColorInt(self):
        return self.toQColor().rgb()
        

#Done
def pickAColor():
    """
        Opens a color chooser to let the user pick a color and returns it. Takes
        no input.

        :return: the color chosen in the dialog box
    """
    ## Dorn 5/8/2009:  Edited to be thread safe since this code is executed from an
    ## interpreter JESThread and will result in an update to the main JES GUI due to 
    ## it being a modal dialog.
    #from java.lang import Runnable

    #class pickAColorRunner(Runnable):
    #color = Color(0,0,0)
    #def run(self):
    #    retValue = swing.JColorChooser().showDialog(swing.JFrame(),"Choose a color", awt.Color(0,0,0))
    #    if retValue != None:
    #        self.color = Color(retValue.getRed(),retValue.getGreen(),retValue.getBlue())

    #runner = pickAColorRunner()
    #swing.SwingUtilities.invokeAndWait(runner)
    
    #return runner.color
    #root.lift()
    #root.update()
    # root = tkinter.Tk()
    # root.withdraw()
    # #root.lift()
    # 
    # if platform() == 'Darwin':  # How Mac OS X is identified by Python
    #     system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
    # 
    # root.focus_force()
    # col = askcolor()
    # root.update()
    # root.destroy()
    col = QtWidgets.QColorDialog.getColor()
    #return Color(int(col[0][0]), int(col[0][1]), int(col[0][2]))
    return Color(col)

#NEW
#Accessors for color components
def getRedComponent(color):
    if not(isinstance(color, Color)):
        repTypeError("Input is not a color")
    return color.getRed()

def getGreenComponent(color):
    if not(isinstance(color, Color)):
        repTypeError("Input is not a color")
    return color.getGreen()

def getBlueComponent(color):
    if not(isinstance(color, Color)):
        repTypeError("Input is not a color")
    return color.getBlue()

def colorPalette():
    '''The built-in colors that you can use are:
    black
    white
    blue
    red
    green
    gray
    darkGray
    lightGray
    yellow
    orange
    pink
    magenta
    cyan
    '''
    print ('''The built-in colors that you can use are:
    black
    white
    blue
    red
    green
    gray
    darkGray
    lightGray
    yellow
    orange
    pink
    magenta
    cyan
    ''')


#Constants
black = Color(0,0,0)
white = Color(255,255,255)
blue = Color(0,0,255)
red = Color(255,0,0)
green = Color(0,255,0)
gray = Color(128,128,128)
darkGray = Color(64,64,64)
lightGray = Color(192,192,192)
yellow = Color(255,255,0)
orange = Color(255,200,0)
pink = Color(255,175,175)
magenta = Color(255,0,255)
cyan = Color(0,255,255)

#Pixel class, because JES has one
class Pixel:
    #Constructor
    def __init__(self, picture, x, y):
        self.picture = picture
        self.x = x
        self.y = y
        #self.color = Color(picture.getpixel((x,y)))
        self.color = picture.getPixelColor(x, y)
    
    #Render as string
    def __str__(self):
        return "Pixel red=%d green=%d blue=%d" % self.color.getRGB()
    
    #Get red
    def getRed(self):
        return self.color.getRed()
    
    #Get green
    def getGreen(self):
        return self.color.getGreen()
    
    #Get blue
    def getBlue(self):
        return self.color.getBlue()
    
    #Get color
    def getColor(self):
        return self.color
    
    #Set color
    def setColor(self, r, g=None, b=None):
        if g == None:
            if isinstance(r, Color):
                self.color = r
            elif isinstance(r, tuple) and len(r) == 3:
                self.color = Color(r)
            else:
                repValError("Invalid color arguments")
                #raise ValueError
        else:
            self.color = Color(r, g, b)
        self.updatePicture()
    
    #Set red
    def setRed(self, r):
        self.color = Color(r, self.color.getGreen(), self.color.getBlue())
        self.updatePicture()
    
    #Set green
    def setGreen(self, g):
        self.color = Color(self.color.getRed(), g, self.color.getBlue())
        self.updatePicture()
    
    #Set blue
    def setBlue(self, b):
        self.color = Color(self.color.getRed(), self.color.getGreen(), b)
        self.updatePicture()
    
    #Get x
    def getX(self):
        return self.x
    
    #Get y
    def getY(self):
        return self.y
    
    #Update picture
    def updatePicture(self):
        self.picture.setPixel(self.x, self.y, self.color)

#Picture class
#Mostly just a wrapper for QImages
class Picture:
    #Constructor
    def __init__(self, width = None, height = None, aColor = None):
        global keepAround
        if isinstance(width, Picture):
            #We're duplicating a picture
            self.height = width.image.height()
            self.width = width.image.width()
            self.filename = width.filename
            self.image = QtGui.QImage(width.image)
        elif isinstance(width, QtGui.QImage):
            #We're low level duplicating a picture
            self.height = width.height()
            self.width = width.width()
            self.filename = None
            self.image = width
        else:
            #We're making a blank picture
            self.filename = None
            self.height = height
            self.width = width
            if height != None:
                if isinstance(aColor, Color):
                    col = aColor.getRGB()
                elif isinstance(aColor, QtGui.QColor):
                    col = (aColor.red(), aColor.green(), aColor.blue())
                else:
                    col = aColor
                #Qt image
                self.image = QtGui.QImage(width, height, QtGui.QImage.Format_RGB32)
                if col is not None:
                    self.image.fill(QtGui.QColor(*col))
        #Set up a window for displaying it
        self.window = QtWidgets.QWidget()
        if self.filename == None:
            self.title = "Image"
            #self.window.setWindowTitle("Image")
        else:
            self.title = self.filename
            #self.window.setWindowTitle(self.filename)
        self.window.setWindowTitle(self.title)
        self.picLabel = QtWidgets.QLabel(self.window)
        #self.frame = None
        if self.height != None:
            self.window.resize(self.width, self.height)
        
        #Optimization
        self.line = None
        self.lineindex = -1
        
        #Keep a copy around forever (bad to do generally, but important for this)
        keepAround.append(self)
    
    #Match JES's printing of a picture
    def __str__(self):
        ret = "Picture, "
        if self.filename == None and self.height == None:
            return ret + "empty"
        retend = "height %d width %d" % (self.height, self.width)
        if self.filename == None:
            return ret + retend
        else:
            return ret + "filename %s %s" % (self.filename, retend)
    
    #Load a file into the Picture object
    def loadOrFail(self, filename):
        try:
            #Check if it's supported
            suppt = isSupportedImageFormat(filename)
            if not suppt and Qt_VERSION == 4:
                #print("Warning! Attempting to open unsupported file type!")
                ##Make a PNG and mess with that instead
                #First, open a PIL image
                self.pil_im = PIL.Image.open(filename)
                #Next, create a temporary PNG file
                tmpfl = tempfile.mkstemp(suffix = '.png')
                #Now, keep track of the file name to work with
                self.workfile = tmpfl[1]
                #Finally, export the PIL image as a PNG to the temp file
                self.pil_im.save(tmpfl[1])
            elif not suppt and Qt_VERSION == 5:
                print("Congratulations! You've discovered a bug in the media "
                    "module! This also means that an old bug in an external "
                    "codebase from 2017 or earlier is still not fixed...")
            else:
                #Nothing went wrong, so pil_im should be None
                self.pil_im = None
                #The "actual" file is the same as the specified file
                self.workfile = filename
            #self.image = PIL.Image.open(filename)
            #Load the QImage
            self.image = QtGui.QImage(self.workfile)
            if self.image.isNull():
                #Load failed
                #raise IOError
                reportErrorToUser(IOError, "Loading image failed")
            self.filename = filename
            self.height = self.image.height()
            self.width = self.image.width()
            self.window.resize(self.width, self.height)
            self.title = self.filename
            self.window.setWindowTitle(self.title)
        except IOError:
            raise IOError(filename + " could not be opened or was not a picture. Check that you specified the path")
    
    #Set all pixels to a color
    def setAllPixelsToAColor(self, col):
        self.image.fill(QtGui.QColor(*col.getRGB()))
    
    #Get Pixels
    def getPixels(self):
        ##Get the raw data
        #dat = self.image.getdata()
        ##Convert them all to Pixel objects
        #return [Pixel(self, 
        #On second thought, let's just mirror the Pixel class in JES
        # INCORRECTLY REVERSES THE ORDER OF THE PIXELS BASED ON THE BOOK EXAMPLES
        #return [Pixel(self, x, y) for x in range(self.width) for y in range(self.height)] 
        return [Pixel(self, x, y) for y in range(self.height) for x in range(self.width)]
    
    #Get Pixel
    def getPixel(self, x, y):
        return Pixel(self, x, y)
    
    #Get pixel color
    def getPixelColor(self, x, y):
        #return Color(self.image.pixel(x, y))
        #Making it faster
        #Get the line
        if self.lineindex == y:
            pixarray = self.line
        else:
            pixline = self.image.scanLine(y)
            pixarray = pixline.asarray(4*self.width)
            self.line = pixarray
            self.lineindex = y
        #pixline = self.image.scanLine(y)
        #pixarray = pixline.asarray(4*self.width)
        #Create a color
        return Color(pixarray[4*x+2], pixarray[4*x+1], pixarray[4*x])
    
    #Get width
    def getWidth(self):
        return self.width
    
    #Get height
    def getHeight(self):
        return self.height
    
    #Set the (x,y) pixel to Color col
    def setPixel(self, x, y, col):
        if not isinstance(col, Color):
            repTypeError("non-color passed to setPixel")
            #raise ValueError
        #self.image.putpixel((x,y), col.getRGB())
        #NOTE: There's a warning about this being a slow operation
        #self.image.setPixel(x, y, col.toQColorInt())
        #Get the line
        if self.lineindex == y:
            pixarray = self.line
        else:
            pixline = self.image.scanLine(y)
            pixarray = pixline.asarray(4*self.width)
            self.line = pixarray
            self.lineindex = y
        #pixline = self.image.scanLine(y)
        #pixarray = pixline.asarray(4*self.width)
        #Set the corresponding bytes
        pixarray[4*x] = col.getBlue() #Blue
        pixarray[4*x+1] = col.getGreen() #Green
        pixarray[4*x+2] = col.getRed() #Red
    
    #Print the picture in Canopy
    #TODO make Windows-friendly
    def printPicture(self):
        if Qt_VERSION == 5:
            print("This functionality is not supported")
            return
        #return self.image
        #Canopy prints out PIL images nicely
        #So, we'll convert to and return a PIL image
        #This is very hack-ish
        #img = QImage("/tmp/example.png")
        img = QtGui.QImage(self.image)
        #Create a temporary file
        tmpfl = tempfile.mkstemp(suffix = '.png')
        #print(tmpfl)
        #tmpfl.close()
        #img.save("/tmp/example.png", "PNG")
        #pil_im = PIL.Image.open("/tmp/example.png")
        img.save(tmpfl[1], "PNG")
        pil_im = PIL.Image.open(tmpfl[1])
        # buffer = QBuffer()
        # buffer.open(QIODevice.ReadWrite)
        # img.save(buffer, "PNG")
        # 
        # strio = io.BytesIO()
        # strio.write(buffer.data())
        # buffer.close()
        # strio.seek(0)
        #pil_im = PIL.Image.open(strio)
        return pil_im
    
    #Show the picture
    def show(self, title = None):
        #self.image.show(title)
        #root = tkinter.Tk()
        #root.withdraw()
        #second = tkinter.Toplevel()
        if title != None:
            self.window.setWindowTitle(title)
        
        pixmap = QtGui.QPixmap.fromImage(self.image)
        self.picLabel.setPixmap(pixmap)
        
        # Show window
        self.window.show()
        self.window.activateWindow()
        self.window.raise_()
        self.window.activateWindow()
        QtWidgets.QApplication.processEvents()
        
        # USE THE WINDOW TO BLOCK THE CALLING PROGRAM
        #  THIS IS NECESSARY FOR THONNY WITH THIS PARTICULAR
        #  IMPLEMENTATION.
        root.exec_()
        
        #second.geometry("%dx%d" % (self.width, self.height))
        #root.lift()
        #canvas = tkinter.Canvas(second,width=self.width,height=self.height)
        #canvas.pack()
        #try:
        #image = PIL.ImageTk.PhotoImage(self.image)
        #except TclError:
        #    #This is for debugging
        #    second.destroy()
        #    raise
            
        #canvas.create_image(0,0,image=image, anchor = 'nw')
        
        #second.update()
        #self.frame = second #Keep reference around?
        #th.start()
        #second.update()
        #second.mainloop()
        #roots.append(root) #Keep a reference around
        #return self.frame
    
    #Repaint the picture
    def repaint(self):
        pixmap = QtGui.QPixmap.fromImage(self.image)
        self.picLabel.setPixmap(pixmap)
        self.window.update()
        QtWidgets.QApplication.processEvents()
    
    #Copy the picture other into this one at position (x,y) for upper left
    def copyInto(self, other, x, y, rotation = 0):
        painter = QtGui.QPainter()
        painter.begin(self.image)
        if rotation != 0:
            painter.translate(x, y)
            painter.rotate(rotation)
            painter.translate(-x, -y)
        painter.drawImage(x, y, other.image)
        painter.end()
    
    #Draw a line on the picture 
    def addLine(self, col, x1, y1, x2, y2):
        painter = QtGui.QPainter()
        painter.begin(self.image)
        painter.setPen(QtGui.QColor(*col.getRGB()))
        painter.drawLine(x1, y1, x2, y2)
        painter.end()
    
    #Draw text on the picture
    def addText(self, col, x, y, string, font = None):
        painter = QtGui.QPainter()
        painter.begin(self.image)
        if font is not None:
            painter.setFont(font)
        painter.setPen(QtGui.QColor(*col.getRGB()))
        painter.drawText(x, y, string)
        painter.end()
    
    #Draw a rectangle on the picture
    def addRect(self, col, x, y, w, h, isFilled):
        painter = QtGui.QPainter()
        qcol = QtGui.QColor(*col.getRGB())
        painter.begin(self.image)
        painter.setPen(qcol)
        if isFilled:
            painter.fillRect(x, y, w, h, qcol)
        else:
            painter.drawRect(x, y, w, h)
        painter.end()
    
    #Draw an oval on the picture
    def addOval(self, col, x, y, w, h, isFilled):
        painter = QtGui.QPainter()
        qcol = QtGui.QColor(*col.getRGB())
        painter.begin(self.image)
        painter.setPen(qcol)
        if isFilled:
            painter.setBrush(QtGui.QBrush(qcol))
            #painter.fillRect(x, y, w, h, qcol)
        #else:
        painter.drawEllipse(x, y, w, h)
        painter.end()
    
    def addArc(self, col, x, y, w, h, start, angle, isFilled):
        painter = QtGui.QPainter()
        qcol = QtGui.QColor(*col.getRGB())
        painter.begin(self.image)
        painter.setPen(qcol)
        if isFilled:
            painter.setBrush(QtGui.QBrush(qcol))
            #*16 because these functions use 16ths of degrees
            painter.drawPie(x, y, w, h, start*16, angle*16)
        else:
            #*16 because these functions use 16ths of degrees
            painter.drawArc(x, y, w, h, start*16, angle*16)
        painter.end()
    
    #Save the picture
    #If fname is None, overwrite the file
    def writeOrFail(self, fname = None, fmt = None):
        if fname == None:
            fil = self.filename
        else:
            fil = fname
        #Check if it's supported
        suppt = (fmt == None and isSupportedImageFormat(fil)) or\
            (fmt != None and isSupportedImageFormat(fmt))
        if not suppt and Qt_VERSION == 4:
            #print("Warning! Attempting to save unsupported file type!")
            #Save as a temporary PNG first
            itWorked = self.image.save(self.workfile, 'PNG')
            if itWorked:
                #Then, open the PNG as a PIL image
                pil_im = PIL.Image.open(self.workfile)
                #Then, save the PIL image where we want
                pil_im.save(fil, fmt)
        elif not suppt and Qt_VERSION == 5:
            print("Congratulations! You've discovered a bug in the media "
                "module! This also means that an old bug in an external "
                "codebase from 2017 or earlier is still not fixed...")
        else:
            #Everything's good.  Just save the iamge
            itWorked = self.image.save(fil, fmt)
        if not itWorked:
            #print("Saving image failed")
            #raise IOError
            reportErrorToUser(IOError, "Saving image failed")

##
## Global picture functions
##
#Done
def makePicture(filename):
    """
        Takes a filename as input, reads the file, and creates a picture from it. 
        Returns the picture.
        
        :param filename: the name of the file you want to open as a picture
        :return: a picture object made from the file
    """
    '''
    Student documentation:

    The makePicture function takes a file name(with its extention) as an argument and returns a picture object containing that file.
    
    Example:
    from media.py import *

    myPicture =  makePicture("cat.jpg")

    myPicture now contains the cat.jpg picture. Please keep in mind that your file name must be inside single quotes ('') or double quotes ("").
    ------------------------------------------
    Developer documentation:
    '''
    global mediaFolder
    if not isinstance(filename, str):
        repTypeError("makePicture(filename): argument not a string: "+str(filename))
    if not os.path.isabs(filename):
        filename = mediaFolder + filename
    if not os.path.isfile(filename):
        repValError("makePicture(filename): There is no file at "+filename)
        #raise ValueError
    picture = Picture()
    picture.loadOrFail(filename)
    return picture
    #return PIL.Image.open(filename)

# MMO (1 Dec 2005): Capped width/height to max 10000 and min 1
# alexr (6 Sep 2006): fixed to work without the Python classes.
# PamC (6 July 2007): added new optional param to allow for empty pictures
# with different background colors.
#Done
def makeEmptyPicture(width, height, acolor = white):
    """
        Makes a new "empty" picture and returns it to you. The width and height 
        must be between 0 and 10000. Default color is white.
        
        :param width: the width of the empty picture
        :param height: height of the empty picture
        :param color: background color of the empty picture (optional)
        :return: a new picture object with all the pixels set to the specified color
    """
    '''
    Student documentation:

    The makeEmptyPicture function takes a width a height and a color(the default color value is white) as arguments and returns a picture object with those specifications.
    
    Example:
    from media.py import *

    myPicture =  makeEmptyPicture(300, 200, blue)

    myPicture now contains a 300 by 200 pixel blue picture. To display a list of the built-in colors call the colorPalette function.
    ------------------------------------------
    Developer documentation:
    '''
    if width > 10000 or height > 10000:
        repValError("makeEmptyPicture(width, height[, acolor]): height and width must be less than 10000 each")
        #raise ValueError
    if width <= 0 or height <= 0:
        repValError("makeEmptyPicture(width, height[, acolor]): height and width must be greater than 0 each")
        #raise ValueError
    if not isinstance(acolor, Color):
        repTypeError("makeEmptyPicture(width, height[, acolor]): acolor must be a color")
        #raise ValueError
    #if isinstance(acolor, Color):
    #    col = acolor.getRGB()
    #else:
    #    col = acolor
    picture = Picture(width, height, acolor)
    # picture.createImage(width, height)
    # picture.filename = ''
    # careful here; do we want empty strings or "None"?
    return picture
    #return PIL.Image.new('RGB', (width, height), col)

def getPixels(picture):
    """
        Takes a picture as input and returns the sequence of Pixel objects in 
        the picture.
        
        :param picture: the picture you want to get the pixels from
        :return: a list of all the pixels in the picture
    """
    '''
    Student documentation:

    The getPixels function takes a picture as argument and returns all of the pixels in that picture as a list.
    
    Example:
    from media.py import *

    myPicture =  makeEmptyPicture(300, 200, red)

    for pix in getPixels(myPicture):
        myPicture = pix.setBlue(255)

    I now have a pink picture.
    ------------------------------------------
    Developer documentation:
    '''
    if not isinstance(picture, Picture):
        repTypeError("getPixels(picture): Input is not a picture")
        #raise ValueError
    return picture.getPixels()

#Done
def getAllPixels(picture):
    return getPixels(picture)

#Done
def getWidth(picture):
    """
        Takes a picture as input and returns its length in the number of pixels 
        left-to-right in the picture.
        
        :param picture: the picture you want to get the width of
        :return: the width of the picture
    """
    '''
    Student documentation:

    The getWidth function takes a picture as argument and returns it's width.
    
    Example:
    from media.py import *

    myPicture =  makeEmptyPicture(300, 200)

    print(getWidth(myPicture))

    This prints 300.
    ------------------------------------------
    Developer documentation:
    '''
    if not isinstance(picture, Picture):
        repTypeError("getWidth(picture): Input is not a picture")
        #raise ValueError
    return picture.getWidth()

#Done
def getHeight(picture):
    """
        Takes a picture as input and returns its length in the number of pixels 
        top-to-bottom in the picture.
        
        :param picture: the picture you want to get the height of
        :return: the height of the picture
    """
    '''
    Student documentation:

    The getHeight function takes a picture as argument and returns it's height.
    
    Example:
    from media.py import *

    myPicture =  makeEmptyPicture(300, 200)

    print(getHeight(myPicture))

    This prints 200.
    ------------------------------------------
    Developer documentation:
    '''
    if not isinstance(picture,Picture):
        repTypeError("getHeight(picture): Input is not a picture")
    return picture.getHeight()

#Done
def show(picture, title=None):
    """
        Shows the picture provided as input.
        
        :param picture: the picture you want to see
        :param title: the title for window (optional)       
    """
    '''
    Student documentation:

    The show function takes a picture and a window title(the window title is optional) as arguments and makes a window with those objects.
    
    Example:
    from media.py import *

    myPicture =  makeEmptyPicture(300, 200, red)
    show(myPicture, "a black picture")

    I now have a black window with the title a black picture.
    ------------------------------------------
    Developer documentation:
    '''
    #Old Plan:
        #1. Create broken window with Tkinter
        #2. Add unshow procedure
        #3. Make it passed with stuff
        #Downside: can't close window
    #picture.setTitle(getShortPath(picture.filename))
    #if title <> None:
        #picture.setTitle(title)
    if not isinstance(picture, Picture):
        repTypeError("show(picture): Input is not a picture")
        #raise ValueError
    picture.show(title)
    #frm = picture.show(title)
    #def on_closing():
    #    print("Got here") #Debug?
    #    frm.destroy()
        
    #frm.protocol("WM_DELETE_WINDOW", on_closing)

#NEW
#This is a Canopy thing
if Qt_VERSION == 4:
    def printPicture(picture):
        if not isinstance(picture,Picture):
            repTypeError("repaint(picture): Input is not a picture")
            #raise ValueError
        return picture.printPicture()

def repaint(picture):
    """
        Repaints the picture if it has been opened in a window from 
        show(picture), otherwise a new window will be opened.
        
        :param picture: the picture you want to repaint    
    """
    #if not (isinstance(picture, World) or isinstance(picture,Picture)):
    #    print "repaint(picture): Input is not a picture or a world"
    #    raise ValueError
    #picture.repaint()
    if not isinstance(picture,Picture):
        repTypeError("repaint(picture): Input is not a picture")
        #raise ValueError
    picture.repaint()

## adding graphics to your pictures! ##
#Done
def addLine(picture, x1, y1, x2, y2, acolor=black):
    """
        Takes a picture, a starting (x, y) position (two numbers), and an ending 
        (x, y) position (two more numbers, four total), and (optionally) a color 
        as input. Adds a line from the starting point to the ending point in the 
        picture. Default color is black.

        :param picture: the picture you want to draw the arc on
        :param x1: the x position you want the line to start
        :param y1: the y position you want the line to start
        :param x2: the x position you want the line to end
        :param y2: the y position you want the line to end
        :param acolor: the color you want to draw in (optional)
    """
    '''
    Student documentation:

    The addLine function takes a picture , a first x coordinate, a first y coordinate, a second x coordinate, a second y coordinate and a color(the default color is black) as arguments and draws a line from the first coordinate to the second coordinate in the specified color.
    
    Example:
    from media.py import *

    myPicture =  makeEmptyPicture(300, 200, red)
    addLine(myPicture, 100, 0, 100, 100, blue)
    show(myPicture, "red picture with a blue line")

    I now have a red picture with a blue vertical line.
    ------------------------------------------
    Developer documentation:
    '''
    if not isinstance(picture, Picture):
        repTypeError("addLine(picture, x1, y1, x2, y2[, color]): First input is not a picture")
        #raise ValueError
    if not isinstance(acolor, Color):
        repTypeError("addLine(picture, x1, y1, x2, y2[, color]): Last input is not a color")
        #raise ValueError
    ##g = picture.getBufferedImage().createGraphics()
    ##g.setColor(acolor.color)
    ##g.drawLine(x1 - 1,y1 - 1,x2 - 1,y2 - 1)
    picture.addLine(acolor,x1,y1,x2,y2)

# Using for getImageRep
# Draw a line on the pixmap.
def addLine1(pixmap,x1,y1,x2,y2,col=black):
    if not isinstance(pixmap, QtGui.QPixmap):
        repTypeError("addLine(picture, x1, y1, x2, y2[, color]): First input is not a picture")
        #raise ValueError
    if not isinstance(col, Color):
        repTypeError("addLine(picture, x1, y1, x2, y2[, color]): Last input is not a color")
        #raise ValueError
    painter = QtGui.QPainter()
    painter.begin(pixmap)
    painter.setPen(QtGui.QColor(*col.getRGB()))
    if (x1 < 0):
        x1 = 0
    if (y1 < 0):
        y1 = 0
    if (x2 > pixmap.width()):
        x2 = pixmap.width()
    if (y2 > pixmap.height()):
        y2 = pixmap.height()      
    painter.drawLine(x1, y1, x2, y2)
    painter.end()


#Done
def addText(picture, x, y, string, acolor=black):
    """
        Takes a picture, an x position and a y position (two numbers), and some 
        text as a string, which will get drawn into the picture, in the 
        specified color. Default color is black.
        
        :param picture: the picture you want to draw the arc on
        :param x: the x-coordinate where you want to start writing the text
        :param y: he y-coordinate where you want to start writing the text
        :param string: a string containing the text you want written
        :param acolor: the color you want to draw in (optional)
    """
    '''
    Student documentation:

    The addText function takes a picture, a x coordinate, a y coordinate, the text you want to add and a color(the default color is black) as arguments and writes the text in the picture.
    
    Example:
    from media.py import *

    myPicture =  makeEmptyPicture(200, 200)
    addText(myPicture, 100, 100, "Hi")
    show(myPicture, "a white picture with a black greeting")

    I now have a white picture with a black greeting.
    ------------------------------------------
    Developer documentation:
    '''
    if not isinstance(picture, Picture):
        repTypeError("addText(picture, x, y, string[, color]): First input is not a picture")
        #raise ValueError
    if not isinstance(acolor, Color):
        repTypeError("addText(picture, x, y, string[, color]): Last input is not a color")
        #raise ValueError
    ##g = picture.getBufferedImage().getGraphics()
    ##g.setColor(acolor.color)
    ##g.drawString(string, x - 1, y - 1)
    picture.addText(acolor,x,y,string)

# PamC: Added this function to allow different font styles
#Done
def addTextWithStyle(picture, x, y, string, style, acolor=black):
    """
        Takes a picture, an x position and a y position (two numbers), and some 
        text as a string, which will get drawn into the picture, in the given 
        font style and specified color. Default color is black.
        
        :param picture: the picture you want to draw the arc on
        :param x: the x-coordinate where you want to start writing the text
        :param y: he y-coordinate where you want to start writing the text
        :param string: a string containing the text you want written
        :param style: a font created using makeStyle()
        :param acolor: the color you want to draw in (optional)
    """
    if not isinstance(picture, Picture):
        repTypeError("addTextWithStyle(picture, x, y, string, style[, color]): First input is not a picture")
    if not isinstance(style, QtGui.QFont):
        repTypeError("addTextWithStyle(picture, x, y, string, style[, color]): Input is not a style (see makeStyle)")
    if not isinstance(acolor, Color):
        repTypeError("addTextWithStyle(picture, x, y, string, style[, color]): Last input is not a color")
    picture.addText(acolor,x,y,string,style)

#Done
def addRect(picture, x,y,w,h, acolor=black):
    """
        Takes a picture, a starting (x, y) position (two numbers), a width and 
        height (two more numbers, four total), and (optionally) a color as input. 
        Adds a rectangular outline of the specified dimensions using the (x,y) 
        as the upper left corner. Default color is black.

        :param picture: the picture you want to draw the arc on
        :param x: the x-coordinate of the upper left-hand corner of the rectangle
        :param y: the y-coordinate of the upper left-hand corner of the rectangle
        :param w: the width of the rectangle
        :param h: the height of the rectangle
        :param acolor: the color you want to draw in (optional)
    """
    '''
    Student documentation:

    The addText function takes a picture, a x coordinate, a y coordinate, the width and height of your unfilled rectangle and a color(the default color is black) as arguments and draws an unfilled rectangle in the picture.
    
    Example:
    from media.py import *

    myPicture =  makeEmptyPicture(400, 400)
    addRect(myPicture, 100, 100, 200, 200, blue)
    show(myPicture, "a white picture with a blue unfilled rectangle")

    I now have a white picture with a blue unfilled rectangle.
    ------------------------------------------
    Developer documentation:
    '''
    if not isinstance(picture, Picture):
        repTypeError("addRect(picture, x, y, w, h[, color]): First input is not a picture")
        #raise ValueError
    if not isinstance(acolor, Color):
        repTypeError("addRect(picture, x, y, w, h[, color]): Last input is not a color")
        #raise ValueError
    ##g = picture.getBufferedImage().getGraphics()
    ##g.setColor(acolor.color)
    ##g.drawRect(x - 1,y - 1,w,h)
    picture.addRect(acolor,x,y,w,h,False)

#Done
def addRectFilled(picture,x,y,w,h, acolor=black):
    """
        Takes a picture, a starting (x, y) position (two numbers), a width and 
        height (two more numbers, four total), and (optionally) a color as input. 
        Adds a filled rectangle of the specified dimensions using the (x,y) as 
        the upper left corner. Default color is black.

        :param picture: the picture you want to draw the arc on
        :param x: the x-coordinate of the upper left-hand corner of the rectangle
        :param y: the y-coordinate of the upper left-hand corner of the rectangle
        :param w: the width of the rectangle
        :param h: the height of the rectangle
        :param acolor: the color you want to draw in (optional)
    """
    '''
    Student documentation:

    The addRectFilled function takes a picture, a x coordinate, a y coordinate, the width and height of your filled rectangle and a color(the default color is black) as arguments and draws a filled rectangle in the picture.
    
    Example:
    from media.py import *

    myPicture =  makeEmptyPicture(400, 400)
    addRectFilled(myPicture, 100, 100, 200, 200, red)
    show(myPicture, "a white picture with a red filled rectangle")

    I now have a white picture with a red filled rectangle.
    ------------------------------------------
    Developer documentation:
    '''
    if not isinstance(picture,Picture):
        repTypeError("addRectFilled(picture, x, y, w, h[, color]): First input is not a picture")
        #raise ValueError
    if not isinstance(acolor, Color):
        repTypeError("addRectFilled(picture, x, y, w, h[, color]): Last input is not a color")
        #raise ValueError
    ##g = picture.getBufferedImage().getGraphics()
    ##g.setColor(acolor.color)
    ##g.fillRect(x - 1,y - 1,w,h)
    picture.addRect(acolor,x,y,w,h,True)

# PamC: Added the following addOval, addOvalFilled, addArc, and addArcFilled
# functions to add more graphics to pictures.
def addOval(picture, x,y,w,h, acolor=black):
    """
        Takes a picture, a starting (x, y) position (two numbers), a width and 
        height (two more numbers, four total), and (optionally) a color as input. 
        Adds an oval outline of the given dimensions using the (x,y) as the upper 
        left corner of the bounding rectangle. Default color is black.

        :param picture: the picture you want to draw the arc on
        :param x: the x-coordinate of the upper left-hand corner of the bounding
                    rectangle of the oval
        :param y: the y-coordinate of the upper left-hand corner of the bounding
                    rectangle of the oval
        :param w: the width of the oval
        :param h: the height of the oval
        :param acolor: the color you want to draw in (optional)
    """
    '''
    Student documentation:

    The addOval function takes a picture, a x coordinate, a y coordinate, the width and height of your unfilled oval and a color(the default color is black) as arguments and draws an unfilled oval in the picture.
    
    Example:
    from media.py import *

    myPicture =  makeEmptyPicture(400, 400)
    addOval(myPicture, 100, 100, 200, 200, red)
    show(myPicture, "a white picture with a red unfilled oval")

    I now have a white picture with a red unfilled oval.
    ------------------------------------------
    Developer documentation:
    '''
    if not isinstance(picture, Picture):
        repTypeError("addOval(picture, x, y, w, h[, color]): First input is not a picture")
        #raise ValueError
    if not isinstance(acolor, Color):
        repTypeError("addOval(picture, x, y, w, h[, color]): Last input is not a color")
        #raise ValueError
    ##g = picture.getBufferedImage().getGraphics()
    ##g.setColor(acolor.color)
    ##g.drawRect(x - 1,y - 1,w,h)
    picture.addOval(acolor,x,y,w,h,False)

#Done
def addOvalFilled(picture,x,y,w,h,acolor=black):
    """
        Takes a picture, a starting (x, y) position (two numbers), a width and 
        height (two more numbers, four total), and (optionally) a color as input. 
        Adds a filled oval of the given dimensions using the (x,y) as the upper 
        left corner of the bounding rectangle. Default color is black.

        :param picture: the picture you want to draw the arc on
        :param x: the x-coordinate of the upper left-hand corner of the bounding
                    rectangle of the oval
        :param y: the y-coordinate of the upper left-hand corner of the bounding
                    rectangle of the oval
        :param w: the width of the oval
        :param h: the height of the oval
        :param acolor: the color you want to draw in (optional)
    """
    '''
    Student documentation:

    The addOvalFilled function takes a picture, a x coordinate, a y coordinate, the width and height of your filled oval and a color(the default color is black) as arguments and draws an filled oval in the picture.
    
    Example:
    from media.py import *

    myPicture =  makeEmptyPicture(400, 400)
    addOvalFilled(myPicture, 100, 100, 200, 200, pink)
    show(myPicture, "a white picture with a pink unfilled oval")

    I now have a white picture with a pink unfilled oval.
    ------------------------------------------
    Developer documentation:
    '''
    if not isinstance(picture,Picture):
        repTypeError("addOvalFilled(picture, x, y, w, h[, color]): First input is not a picture")
        #raise ValueError
    if not isinstance(acolor, Color):
        repTypeError("addOvalFilled(picture, x, y, w, h[, color]): Last input is not a color")
        #raise ValueError
    picture.addOval(acolor,x,y,w,h,True)

#Done
#Note: Uses degrees
def addArc(picture,x,y,w,h,start,angle,acolor=black):
    """
        Takes a picture, (x,y) coordinates, width, height, two integer angles, 
        and (optionally) a color as input. Adds an outline of an arc starting at 
        (x,y) at an initial angle of "start" with the given width and height. 
        The angle of the arc itself is "angle", which is relative to "start." 
        Default color is black.

        :param picture: the picture you want to draw the arc on
        :param x: the x-coordinate of the center of the arc
        :param y: the y-coordinate of the center of the arc
        :param w: the width of the arc
        :param h: the height of the arc
        :param start: the start angle of the arc in degrees
        :param angle: the angle of the arc relative to start in degrees
        :param color: the color you want to draw in (optional)a
    """
    if not isinstance(picture,Picture):
        repTypeError("addArc(picture, x, y, w, h, start, angle[, color]): First input is not a picture")
        #raise ValueError
    if not isinstance(acolor, Color):
        repTypeError("addArc(picture, x, y, w, h[, color]): Last input is not a color")
        #raise ValueError
    picture.addArc(acolor,x,y,w,h,start,angle,False)

#Note: Uses degrees
def addArcFilled(picture,x,y,w,h,start,angle,acolor=black):
    """
        Takes a picture, (x,y) coordinates, width, height, two integer angles, 
        and (optionally) a color as input. Adds a filled arc starting at (x,y) 
        at an initial angle of "start" with the given width and height. The 
        angle of the arc itself is "angle", which is relative to "start." 
        Default color is black.

        :param picture: the picture you want to draw the arc on
        :param x: the x-coordinate of the center of the arc
        :param y: the y-coordinate of the center of the arc
        :param w: the width of the arc
        :param h: the height of the arc
        :param start: the start angle of the arc in degrees
        :param angle: the angle of the arc relative to start in degrees
        :param color: the color you want to draw in (optional)
    """
    if not isinstance(picture,Picture):
        repTypeError("addArcFilled(picture, x, y, w, h[, color]): First First input is not a picture")
        #raise ValueError
    if not isinstance(acolor, Color):
        repTypeError("addArcFill(picture, x, y, w, h[, color]): Last input is not a color")
        #raise ValueError
    picture.addArc(acolor,x,y,w,h,start,angle,True)

## note the -1; in JES we think of pictures as starting at (1,1) but not
## in the Java.
##
## 29 Oct 2008: -1 changed to Picture._PictureIndexOffset
## note: Nathan Fox got rid of this offset thing
#Done
def getPixel(picture,x,y):
    """
        Takes a picture, an x position and a y position (two numbers), and 
        returns the Pixel object at that point in the picture. (Same as getPixelAt)
        
        :param picture: the picture you want to get the pixel from
        :param x: the x-coordinate of the pixel you want
        :param y: the y-coordinate of the pixel you want
        :return: the Pixel object
    """
    '''
    Student documentation:

    The getPixel function takes a picture, a x coordinate and a y coordinate as arguments and returns the pixel at that index.
    
    Example:
    from media.py import *

    myPicture =  makeEmptyPicture(200, 200)
    pix = getPixel(myPicture, 100, 100)
    print(pix)

    I now have a pix variable with the pixel at 99,99.
    ------------------------------------------
    Developer documentation:
    '''
    if not isinstance(picture, Picture):
        repTypeError("getPixel(picture,x,y): First input is not a picture")
        #raise ValueError
    # if ( x < Picture._PictureIndexOffset ) or ( x > getWidth(picture) - 1 + Picture._PictureIndexOffset ):
    #     print("getPixel(picture,x,y): x (= %s) is less than %s or bigger than the width (= %s)" % (x,Picture._PictureIndexOffset,getWidth(picture) - 1 + Picture._PictureIndexOffset)
    #     raise ValueError
    # if ( y < Picture._PictureIndexOffset ) or ( y > getHeight(picture) - 1 + Picture._PictureIndexOffset ):
    #     print "getPixel(picture,x,y): y (= %s) is less than %s or bigger than the height (= %s)" % (y,Picture._PictureIndexOffset,getHeight(picture) - 1 + Picture._PictureIndexOffset)
    #     raise ValueError
    if ( x < 0 ) or ( x > getWidth(picture) - 1 ):
        repValError("getPixel(picture,x,y): x (= %s) is less than %s or bigger than the width (= %s)" % (x, 0, getWidth(picture) - 1))
        #raise ValueError
    if ( y < 0 ) or ( y > getHeight(picture) - 1 ):
        repValError("getPixel(picture,x,y): y (= %s) is less than %s or bigger than the height (= %s)" % (y, 0, getHeight(picture) - 1))
        #raise ValueError

    #return picture.getPixel(x - Picture._PictureIndexOffset, y - Picture._PictureIndexOffset)
    return picture.getPixel(x, y)

#Added as a better name for getPixel
#Done
def getPixelAt(picture,x,y):
    """
        Takes a picture, an x position and a y position (two numbers), and 
        returns the Pixel object at that point in the picture.
        
        :param picture: the picture you want to get the pixel from
        :param x: the x-coordinate of the pixel you want
        :param y: the y-coordinate of the pixel you want
        :return: the Pixel object
    """
    return getPixel(picture,x,y)

#Done
def setRed(pixel,value):
    #value = _checkPixel(value)
    if not isinstance(pixel, Pixel):
        repTypeError("setRed(pixel,value): Input is not a pixel")
        #raise ValueError
    pixel.setRed(value)

#Done
def getRed(pixel):
    if not isinstance(pixel, Pixel):
        repTypeError("getRed(pixel): Input is not a pixel")
        #raise ValueError
    return pixel.getRed()

#Done
def setBlue(pixel,value):
    #value = _checkPixel(value)
    if not isinstance(pixel, Pixel):
        repTypeError("setBlue(pixel,value): Input is not a pixel")
        #raise ValueError
    pixel.setBlue(value)

#Done
def getBlue(pixel):
    if not isinstance(pixel,Pixel):
        repTypeError("getBlue(pixel): Input is not a pixel")
        #raise ValueError
    return pixel.getBlue()

#Done
def setGreen(pixel,value):
    #value = _checkPixel(value)
    if not isinstance(pixel, Pixel):
        repTypeError("setGreen(pixel,value): Input is not a pixel")
        #raise ValueError
    pixel.setGreen(value)

def getGreen(pixel):
    if not isinstance(pixel, Pixel):
        repTypeError("getGreen(pixel): Input is not a pixel")
        #raise ValueError
    return pixel.getGreen()

#Done
def getColor(pixel):
    if not isinstance(pixel, Pixel):
        repTypeError("getColor(pixel): Input is not a pixel")
        #raise ValueError
    return pixel.getColor()

def setColor(pixel,color):
    if not isinstance(pixel, Pixel):
        repTypeError("setColor(pixel,color): First input is not a pixel")
        #raise ValueError
    if not isinstance(color, Color):
        repTypeError("setColor(pixel,color): Second input is not a color")
        #raise ValueError
    pixel.setColor(color)

def getX(pixel):
    if not isinstance(pixel, Pixel):
        repTypeError("getX(pixel): Input is not a pixel")
        #raise ValueError
    return pixel.getX()# + Picture._PictureIndexOffset

def getY(pixel):
    if not isinstance(pixel,Pixel):
        repTypeError("getY(pixel): Input is not a pixel")
        #raise ValueError
    return pixel.getY()# + Picture._PictureIndexOffset

#Done
def distance(c1,c2):
    """
        Takes two Color objects and returns a single number representing the 
        distance between the colors. The red, green, and blue values of the 
        colors are taken as a point in (x, y, z) space, and the Cartesian 
        distance is computed.

        :param c1: the first color you want compared
        :param c2: the second color you want compared
        :return: a floating point number representing the Cartesian 
                distance between the colors
    """
    if not isinstance(c1, Color):
        repTypeError("distance(c1,c2): First input is not a color")
        #raise ValueError
    if not isinstance(c2, Color):
        repTypeError("distance(c1,c2): Second input is not a color")
        #raise ValueError
    return c1.distance(c2)

#Done
def writePictureTo(picture,filename):
    """
        Takes a picture and a file name (string) as input, then writes the 
        picture to the file as a JPEG, PNG, or BMP. (Be sure to end the 
        filename in ".jpg" or ".png" or ".bmp" for the operating system to 
        understand it well.)
        
        :param picture: the picture you want to be written out to a file
        :param filename: the path to the file you want the picture written to
    """
    global mediaFolder
    if not os.path.isabs(filename):
        filename = mediaFolder + filename
    if not isinstance(picture, Picture):
        repTypeError("writePictureTo(picture,filename): First input is not a picture")
        #raise ValueError
    picture.writeOrFail(filename)
    if not os.path.exists(filename):
        repValError("writePictureTo(picture,filename): Path is not valid")
        #raise ValueError


#New
#Call save dialog then write picture to where saved
def savePicture(picture):
    fil = pickASaveFile()
    if fil == None:
        print("No file selected; nothing saved.")
        return
    #Try to get a format
    #If no format given, yell at the user
    dotloc = fil.rfind(".")
    if dotloc == -1:
        repValError("Error: No file extension provided")
        #raise ValueError("Error: No file extension provided")
    writePictureTo(picture, fil)

# not to be confused with setColor, totally different, don't document/export
def _setColorTo(color, other):
    color.setRGB(other.getRed(), other.getGreen(), other.getBlue())
    return color

#def makeDarker(color):
    #"""This function has side effects on purpose, see p49 """
    #return _setColorTo(color, color.darker())

#Done
def makeDarker(color):
    """
        Takes a color and returns a slightly darker version of the original
        color.

        :param color: the color you want to darken
        :return: the new, darker color
    """
    if not isinstance(color,Color):
        repTypeError("makeDarker(color): Input is not a color")
        #raise ValueError("makeDarker(color): Input is not a color")
    return Color( color.makeDarker() )

#def makeLighter(color):
  #"""This function has side effects on purpose, see p49"""
  #return _setColorTo(color,color.brighter())

#Done
def makeLighter(color):
    """
        Takes a color and returns a slightly lighter version of the original 
        color. This does the same thing as makeBrighter(color).

        :param color: the color you want to lighten
        :return: the new, lighter color
    """
    if not isinstance(color,Color):
        repTypeError("makeLighter(color): Input is not a color")
        #raise ValueError("makeLighter(color): Input is not a color")
    return Color( color.makeLighter() )

#Done
def makeBrighter(color):
    """
        Takes a color and returns a slightly brighter version of the original 
        color. This does the same thing as makeLighter(color).

        :param color: the color you want to briighten
        :return: the new, brighter color
    """
    if not isinstance(color,Color):
        repTypeError("makeBrighter(color): Input is not a color")
        #raise ValueError("makeBrighter(color): Input is not a color")
    return Color( color.makeLighter() )

#Done
def makeColor(red,green=None,blue=None):
    """
        Takes three integer inputs for the red, green, and blue components (in
        order) and returns a color object. If green and blue are omitted, the
        red value is used as the intensity of a gray color. Also it works with
        only a color as input and returns a new color object with the same RGB
        values as the original.

        :param red: the amount of red you want in the color (or a Color object
                    you want to duplicate)
        :param green: the amount of green you want in the color (optional)
        :param blue: the amount of blue you want in the picture (optional)
        :return: the color made from the inputs
    """
    return Color( red, green, blue)

#Done
def setAllPixelsToAColor(picture,color):
    """
        Modifies the whole image so that every pixel in that image is the given color.
        
        :param picture: the picture to change the pixels of
        :param color: the color to set each pixel to
    """
    if not isinstance(picture, Picture):
        repTypeError("setAllPixelsToAColor(picture,color): First input is not a picture")
        #raise ValueError("setAllPixelsToAColor(picture,color): First input is not a picture")
    if not isinstance(color,Color):
        repTypeError("setAllPixelsToAColor(picture,color): Second input is not a color")
        #raise ValueError("setAllPixelsToAColor(picture,color): Second input is not a color")
    picture.setAllPixelsToAColor(color)


def copyInto(smallPicture, bigPicture, startX, startY):
    """
        Takes two pictures, a x position and a y position as input, and modifies 
        bigPicture by copying into it as much of smallPicture as will fit, 
        starting at the x,y position in the destination picture.
        
        :param smallPicture: the picture to paste into the big picture
        :param bigPicture: the picture to be modified
        :param startX: the X coordinate of where to place the small picture on
                        the big one
        :param startY: the Y coordinate of where to place the small picture on
                        the big one
    """
    #like copyInto(butterfly, jungle, 20,20)
    if not isinstance(smallPicture, Picture):
        repTypeError("copyInto(smallPicture, bigPicture, startX, startY): smallPicture must be a picture")
        #raise ValueError("copyInto(smallPicture, bigPicture, startX, startY): smallPicture must be a picture")
    if not isinstance(bigPicture, Picture):
        repTypeError("copyInto(smallPicture, bigPicture, startX, startY): bigPicture must be a picture")
        #raise ValueError
    if (startX < 0) or (startX > getWidth(bigPicture) - 1):
        repValError("copyInto(smallPicture, bigPicture, startX, startY): startX must be within the bigPicture")
        #raise ValueError
    if (startY < 0) or (startY > getHeight(bigPicture) - 1):
        repValError("copyInto(smallPicture, bigPicture, startX, startY): startY must be within the bigPicture")
        #raise ValueError
    if (startX + getWidth(smallPicture) - 1) > (getWidth(bigPicture) - 1) or \
            (startY + getHeight(smallPicture) - 1) > (getHeight(bigPicture) - 1):
        repValError("copyInto(smallPicture, bigPicture, startX, startY): smallPicture won't fit into bigPicture")
        #raise ValueError

    xOffset = startX
    yOffset = startY

    #for x in range(0, getWidth(smallPicture)):
    #    for y in range(0, getHeight(smallPicture)):
    #        bigPicture.setBasicPixel(x + xOffset, y + yOffset, smallPicture.getBasicPixel(x,y))
    bigPicture.copyInto(smallPicture, xOffset, yOffset)

    return bigPicture

def copyIntoWithCutoff(smallPicture, bigPicture, startX, startY):
    #like copyInto(butterfly, jungle, 20,20)
    if not isinstance(smallPicture, Picture):
        repTypeError("copyInto(smallPicture, bigPicture, startX, startY): smallPicture must be a picture")
        #raise ValueError("copyInto(smallPicture, bigPicture, startX, startY): smallPicture must be a picture")
    if not isinstance(bigPicture, Picture):
        repTypeError("copyInto(smallPicture, bigPicture, startX, startY): bigPicture must be a picture")
        #raise ValueError

    xOffset = startX
    yOffset = startY

    #for x in range(0, getWidth(smallPicture)):
    #    for y in range(0, getHeight(smallPicture)):
    #        bigPicture.setBasicPixel(x + xOffset, y + yOffset, smallPicture.getBasicPixel(x,y))
    bigPicture.copyInto(smallPicture, xOffset, yOffset)

    return bigPicture

# Alyce Brady's version of copyInto, with additional error-checking on the upper-left corner
# Will copy as much of the original picture into the destination picture as will fit.
#def copyInto(origPict, destPict, upperLeftX, upperLeftY):
#  if not isinstance(origPict, Picture):
#    print "copyInto(origPict, destPict, upperLeftX, upperLeftY): First parameter is not a picture"
#    raise ValueError
#  if not isinstance(destPict, Picture):
#    print "copyInto(origPict, destPict, upperLeftX, upperLeftY): Second parameter is not a picture"
#    raise ValueError
#  if upperLeftX < 1 or upperLeftX > getWidth(destPict):
#    print "copyInto(origPict, destPict, upperLeftX, upperLeftY): upperLeftX must be within the destPict"
#    raise ValueError
#  if upperLeftY < 1 or upperLeftY > getHeight(destPict):
#    print "copyInto(origPict, destPict, upperLeftX, upperLeftY): upperLeftY must be within the destPict"
#    raise ValueError
#  return origPict.copyInto(destPict, upperLeftX-1, upperLeftY-1)
#Done
def duplicatePicture(picture):
    """
        Takes a picture as input and returns a new picture object with the same 
        image as the original.
        
        :param picture: the picture that you want to duplicate
        :return: a new picture object with the same image as the original
    """
    if not isinstance(picture, Picture):
        repTypeError("duplicatePicture(picture): Input is not a picture")
        #raise ValueError
    return Picture(picture)

# Alyce Brady/ Pam Cutter: Function that crops a picture
#Was commented out
#NEW in media module
def cropPicture(picture, upperLeftX, upperLeftY, width, height):
    if not isinstance(picture, Picture):
        repTypeError("crop(picture, upperLeftX, upperLeftY, width, height): "
            "First parameter is not a picture")
    if upperLeftX < 0 or upperLeftX >= getWidth(picture):
        repValError("crop(picture, upperLeftX, upperLeftY, width, height): "
            "upperLeftX must be within the picture")
    if upperLeftY < 0 or upperLeftY >= getHeight(picture):
        repValError("cropPicture(picture, upperLeftX, upperLeftY, width, height): "
            "upperLeftY must be within the picture")
    rect = QtCore.QRect(upperLeftX, upperLeftY, width, height)
    return Picture(picture.image.copy(rect))

#NEW in media module
#Crop, but don't care if goes off edge
def cropPictureWithCutoff(picture, upperLeftX, upperLeftY, width, height):
    if not isinstance(picture, Picture):
        repTypeError("cropPictureWithCutoff(picture, upperLeftX, upperLeftY, width, height): "
            "First parameter is not a picture")
    rect = QtCore.QRect(upperLeftX, upperLeftY, width, height)
    return Picture(picture.image.copy(rect))

#NEW in media module
#Scale a picture by a given factor
#If smooth is True, will apply a smoothing filter
#Default is False for smooth
#MUCH faster than anything you can write high-level
def scalePicture(picture, factor, smooth = False):
    if not isinstance(picture, Picture):
        repTypeError("scalePicture(picture, factor): "
            "First parameter is not a picture")
    if not isinstance(factor, float) and not isinstance(factor, int):
        repTypeError("scalePicture(picture, factor): "
            "Second parameter is not a number")
    if factor <= 0:
        repValError("scalePicture(picture, factor): "
            "Second parameter must be nonnegative")
    if not isinstance(smooth, bool):
        repTypeError("scalePicture(picture, factor, smooth): "
            "smooth is not a boolean")
    if smooth:
        filt = QtCore.Qt.SmoothTransformation
    else:
        filt = QtCore.Qt.FastTransformation
    return Picture(picture.image.scaledToHeight(int(getHeight(picture) *\
        factor), filt))

##
# Input and Output interfaces
#
# Note: These calls must be done in a threadsafe manner since the JESThread will be
# executing them rather than the GUI's event dispatch thread.  See SimpleInput/Output.java
# for the threadsafe execution.
##

#  radius = SimpleInput.getNumber("Enter the radius of the cylinder")
#  SimpleOutput.showInformation("The volume of the cylinder is %.02f " % volume)

#Done
def requestNumber(message, minn=-2147483647, maxx=2147483647, dec=15):
    """
        This will allow the user to input a number with a decimal. The dialog
        will keep appearing until a valid number is entered.

        :param message: the message to display to the user in the dialog
        :return: the number as a double
    """
    #return SimpleInput.getNumber(message)
    tpl = QtWidgets.QInputDialog.getDouble(None, "Please enter a number", message,\
        decimals=dec, min=minn, max=maxx)
    if tpl[1]:
        return tpl[0]
    else:
        return None

#Done
def requestInteger(message, minn=-2147483647, maxx=2147483647, stp=1):
    """
        This will allow the user to input an integer. The dialog will keep
        appearing until a valid integer is entered.

        :param message: the message to display to the user in the dialog
        :return: the number as an integer
    """
    #return SimpleInput.getIntNumber(message)
    tpl = QtWidgets.QInputDialog.getInt(None, "Please enter an integer", message,\
        step=stp, min=minn, max=maxx)
    if tpl[1]:
        return tpl[0]
    else:
        return None

#Done
def requestIntegerInRange(message, min, max):
    """
        Opens a message dialog to the user asking for an integer between a
        minimum and maximum (inclusive). The dialog will keep appearing until
        a valid integer is entered.

        :param message: the message to display to the user in the dialog
        :param min: the smallest integer allowed
        :param max: the largest integer allowed
        :return: the number as an integer
    """
    if min >= max:
        repValError("requestIntegerInRange(message, min, max): min >= max not allowed")
        #raise ValueError

    #return SimpleInput.getIntNumber(message, min, max)
    return requestInteger(message, minn=min, maxx=max)

#Done
def requestString(message):
    """
        This will allow the user to input any string.

        :param message: the message to display to the user in the dialog
        :return: the input string
    """
    tpl = QtWidgets.QInputDialog.getText(None, "Please enter some text", message)
    if tpl[1]:
        return tpl[0]
    else:
        return None


#5/15/09 Dorn: Updated input and raw_input to read from the console
#def input(message=None):
#    im = JESInputManager()
#    return eval(im.readInput(message))

#def raw_input(message=None):
#    im = JESInputManager()
#    return im.readInput(message)
    
#Done
def showWarning(message):
    """
        Opens a message dialog to the user showing a warning.

        :param message: the message to show to the user
    """
    QtWidgets.QMessageBox.warning(None, "Warning!", message)

#Done
def showInformation(message):
    """
        Opens a message dialog to the user showing information.
        
        :param message: the message to show to the user
    """
    QtWidgets.QMessageBox.information(None, "Info", message)

#Done
def showError(message):
    """
        Opens a message dialog to the user showing an error.
        
        :param message: the message to show to the user
    """
    QtWidgets.QMessageBox.critical(None, "Error!!", message)

# 
# ##
# # Java Music Interface
# ##
# def playNote(note, duration, intensity=64):
#     #JavaMusic.playNote(note, duration, intensity)
#     pass #TODO
# 
# 
##
# General user tools
#

#Done
def pickAFile(sdir = None):
    """
        Opens a file chooser to let the user pick a file and returns the 
        complete path name as a string.

        :param sdir: the directory that holds the file (optional)
        :return: the string path to the file chosen in the dialog box
    """
    global mediaFolder
    global mediaFolderSet
    global lastFilePath
    ## Note: this needs to be done in a threadsafe manner, see FileChooser
    ## for details how this is accomplished.
    #return FileChooser.pickAFile()
    #root.update()
    #This is to prevent stupid windows from hanging around
    #root = tkinter.Tk()
    #root.withdraw()
    #root.lift()
    
    #if platform() == 'Darwin':  # How Mac OS X is identified by Python
    #    system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
    
    #root.focus_force()
    #ret = tkinter.filedialog.askopenfilename()
    #root.update()
    #root.destroy()
    if sdir is not None:
        our_dir = sdir
    elif useLastFilePath and (lastFilePath is not None):
        our_dir = lastFilePath
    elif mediaFolderSet:
        our_dir = mediaFolder
    else:
        our_dir = os.getcwd()
    ret = QtWidgets.QFileDialog.getOpenFileName(directory = our_dir)
    if Qt_VERSION == 5:
        ret = ret[0]
    if ret == '':
        ret = None
    if ret is not None:
        lastFilePath = ret[:ret.rfind(os.sep)+1]
    return ret

#New
#Done
def pickASaveFile(sdir = None):
    global mediaFolder
    global mediaFolderSet
    global lastFilePath
    ## Note: this needs to be done in a threadsafe manner, see FileChooser
    ## for details how this is accomplished.
    #return FileChooser.pickAFile()
    #root.update()
    #This is to prevent stupid windows from hanging around
    #root = tkinter.Tk()
    #root.withdraw()
    #root.lift()
    
    #if platform() == 'Darwin':  # How Mac OS X is identified by Python
    #    system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
    
    #root.focus_force()
    #ret = tkinter.filedialog.askopenfilename()
    #root.update()
    #root.destroy()
    if sdir is not None:
        our_dir = sdir
    elif useLastFilePath and (lastFilePath is not None):
        our_dir = lastFilePath
    elif mediaFolderSet:
        our_dir = mediaFolder
    else:
        our_dir = os.getcwd()
    ret = QtWidgets.QFileDialog.getSaveFileName(directory = our_dir)
    if Qt_VERSION == 5:
        ret = ret[0]
    if ret == '':
        ret = None
    if ret is not None:
        lastFilePath = ret[:ret.rfind(os.sep)+1]
    return ret

#Done
def pickAFolder(sdir = None):
    """
        Opens a file chooser to let the user pick a folder and returns the
        complete path name as a string.

        :param sdir: the directory that holds the folder (optional)
        :return: the string path to the folder chosen in the dialog box
    """
    global mediaFolder
    global mediaFolderSet
    global lastFilePath
    ## Note: this needs to be done in a threadsafe manner, see FileChooser
    ## for details how this is accomplished.
    #dir = FileChooser.pickADirectory() TODO
    #root = tkinter.Tk()
    #root.withdraw()
    #root.lift()
    
    #if platform() == 'Darwin':  # How Mac OS X is identified by Python
    #    system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
    
    #root.focus_force()
    #dirc = tkinter.filedialog.askdirectory()
    #root.update()
    #root.destroy()
    if sdir is not None:
        our_dir = sdir
    elif useLastFilePath and (lastFilePath is not None):
        our_dir = lastFilePath
    elif mediaFolderSet:
        our_dir = mediaFolder
    else:
        our_dir = os.getcwd()
    dirc = QtWidgets.QFileDialog.getExistingDirectory(directory = our_dir)
    if dirc == '':
        dirc = None
    if dirc is not None:
        lastFilePath = dirc
        return dirc + os.sep
    return None

def quit():
    sys.exit(0)

# ##
# # MediaTools interface
# #
# # TODO modify viewer.changeToBaseOne
# 
COL_BLOCK_SIZE = 20


#Need this mini-class for registering mouse clicks on picture in explorer
class ClickableLabel(QtWidgets.QLabel):
    #Need to include the explorer so we can talk to it
    def __init__(self, parent, pexplore):
        super().__init__(parent)
        self.pexplore = pexplore
        self.rubberBand = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
        self.origin = QtCore.QPoint()
    
    #Here's where the mouse click is registered
    def mousePressEvent(self, mouseEvent):
        if mouseEvent.button() == QtCore.Qt.LeftButton:
            self.dragStartPosition = mouseEvent.pos()
            self.clickPosition = mouseEvent.pos()
            self.origin = QtCore.QPoint(mouseEvent.pos())
    
    def mouseMoveEvent(self, mouseEvent):
        if not self.origin.isNull():
            self.pexplore.mouseDraged(self.dragStartPosition,mouseEvent.pos())
            self.mouseMovePos = mouseEvent.pos()
        
    def mouseReleaseEvent(self, mouseEvent):
        if mouseEvent.button() == QtCore.Qt.LeftButton:
            # Single-clicked
            if ((mouseEvent.pos() - self.dragStartPosition).manhattanLength() <\
                    QtWidgets.QApplication.instance().startDragDistance()):
                self.pexplore.imageClicked(self.clickPosition)
    
    

#Crosshair on the image explorer
class Crosshair:
    #Construct a crosshair for a given picture
    def __init__(self, pic):
        #Keep track of the picture
        self.pic = pic
        #It starts un-rendered
        self.is_rendered = False
        #It doesn't have a position initially
        self.x = None
        self.y = None
        #There are no saved pixels initially
        self.saved_pixels = []
        #Constants
        #self.COLOR = white
        self.SIZE = 7
    
    #Set the crosshair's position
    #Unrender it, move it, render it
    def setPosition(self, x, y):
        self.unrender()
        self.x = x
        self.y = y
        self.render()
    
    #Un-draw the crosshair
    def unrender(self):
        for pix in self.saved_pixels:
            #Re-draw the pixel the way it was
            self.pic.setPixel(*pix)
        #Un-save the pixels
        self.saved_pixels = []
    
    #Draw the crosshair
    def render(self):
        #+ sign SIZExSIZE, adaptive color
        w = getWidth(self.pic)
        #h = getHeight(self.pic)
        #What color is the pixel?
        pcolor = getColor(getPixel(self.pic, self.x, self.y)).getRGB()
        #Is it dark or light?
        pcolorval = pcolor[0]+pcolor[1]+pcolor[2]
        if pcolorval <= 382:
            #It's dark, so use a white crosshair
            color = white
        else:
            #It's light, so use a dark crosshair
            color = black
        for x in range(self.x-self.SIZE//2, self.x+self.SIZE//2+1):
            if x >= 0 and x < w and x != self.x:
                #Save what's currently there
                self.saved_pixels.append((x, self.y, getColor(getPixel(self.pic, x, self.y))))
                #Make it white
                self.pic.setPixel(x, self.y, color)
        for y in range(self.y-self.SIZE//2, self.y+self.SIZE//2+1):
            if y >= 0 and y < w and y != self.y:
                #Save what's currently there
                self.saved_pixels.append((self.x, y, getColor(getPixel(self.pic, self.x, y))))
                #Make it white
                self.pic.setPixel(self.x, y, color)

#Emulate the JES Picture Explorer
class PictureExplorer(QtWidgets.QWidget):
    #TODO make look nice
    #TODO box around color block #Done
    #TODO box around picture    #Done
    
    #Constructor
    #Should create window, populate with (0,0)
    #remember it globally (to avoid garbage collection issues)
    #and show it
    def __init__(self, pic):
        super().__init__()
        self.setWindowTitle("Image Explorer: " + pic.title)
        self.pic = duplicatePicture(pic)
        self.fixedPixmap = QtGui.QPixmap.fromImage(pic.image)
        self.imageSize = self.fixedPixmap.size()
        # Keeptrack of zoom rate
        self.currentZoomRate = 1

        self.drawingPic = duplicatePicture(pic)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        #self.window.setLayout(QGridLayout())
        #Starting coords
        self.coord_x = 0
        self.coord_y = 0
        
        #Tyn
        self.createMenuButtons()
        self.createFrames()
        self.createImgWindow()
        
        #Resize the window
        self.resize(pic.getWidth(), pic.getHeight() + COL_BLOCK_SIZE)
        #Remember the window
        keepAround.append(self)
        #Show the window
        self.show()
        self.activateWindow()
        self.raise_()
        self.activateWindow()
        QtWidgets.QApplication.processEvents()
    
    #Update color text and color block
    #based on self.coord_x and self.coord_y
    def updateColorStuff(self):
        #Get the color
        col = getColor(getPixel(self.drawingPic,self.coord_x,self.coord_y)).getRGB()
        #Color text
        self.rgblabel.setText("R: " + str(col[0]) + " G: " + str(col[1]) + \
            " B: " + str(col[2]))
        #Color block
        colimg = QtGui.QImage(COL_BLOCK_SIZE, COL_BLOCK_SIZE, QtGui.QImage.Format_RGB32)
        colimg.fill(QtGui.QColor(*col))
        pixmap1 = QtGui.QPixmap.fromImage(colimg)
        self.colLabel.setPixmap(pixmap1)
    
    #Update crosshair position and show it (using addLine1 method)
    #TODO something isn't working properly here
    def updateCrosshair2(self):
        drawingPixmap = QtGui.QPixmap.fromImage(self.drawingPic.image)
        #What color is the pixel?
        pcolor = getColor(getPixel(self.drawingPic, self.coord_x, self.coord_y)).getRGB()
        #Is it dark or light?
        pcolorval = pcolor[0]+pcolor[1]+pcolor[2]
        if pcolorval <= 382:
            #It's dark, so use a white crosshair
            color = white
        else:
            #It's light, so use a dark crosshair
            color = black
        #Draw the crosshair
        # color = cyan
        addLine1(drawingPixmap, self.coord_x, self.coord_y - 3, self.coord_x, self.coord_y + 3, color)
        addLine1(drawingPixmap, self.coord_x - 3, self.coord_y, self.coord_x + 3, self.coord_y, color)
        self.picLabel.setPixmap(drawingPixmap)
    
    #Update crosshair position and show it
    def updateCrosshair(self):
        #Move the crosshair
        self.crosshair.setPosition(self.coord_x, self.coord_y)
        #Redraw the picture
        pixmap2 = QtGui.QPixmap.fromImage(self.drawingPic.image)
        self.picLabel.setPixmap(pixmap2)
    
    # @pyqtSlot(int)
    # def test(self, x):
    #     print("hello " + str(x))
    
    #Position was updated via x/y boxes
    #Update color and label accordingly
    @QtCore.pyqtSlot()
    def updatedPos(self):
        #Only do this if we manually changed the numbers
        if not self.block_edit:
            #Update the current coords
            self.coord_x = self.xwidget.value()
            self.coord_y = self.ywidget.value()
            #Adjust the current coords
            self.adjustCoordinate()
            #Update the stuff that can change
            self.updateColorStuff()
            #Update the crosshair
            self.updateCrosshair2()
            #Repaint the window
            self.update()
            QtWidgets.QApplication.processEvents()
    
    #Clicked on image
    def imageClicked(self, pt):
        #Make sure we don't issue duplicate updates
        self.block_edit = True
        #Update the current coords
        self.coord_x = pt.x()
        self.coord_y = pt.y()
        #Adjust the current coords
        self.adjustCoordinate()
        #Change the spinboxes to the new coords
        self.xwidget.setValue(self.coord_x)
        self.ywidget.setValue(self.coord_y)
        #Update the stuff that can change
        self.updateColorStuff()
        #Update the crosshair
        self.updateCrosshair2()
        #Repaint the window
        self.update()
        QtWidgets.QApplication.processEvents()
        #Manual updates are safe again
        self.block_edit = False
    
    # method adjust the coordinate of the picture to be constraint in
    # Picture size
    def adjustCoordinate(self):
        if self.coord_x < 0:
            self.coord_x = 0
        if self.coord_y < 0:
            self.coord_y = 0
        if self.coord_x >= self.drawingPic.getWidth():
            self.coord_x = self.drawingPic.getWidth() - 1
        if self.coord_y >= self.drawingPic.getHeight():
            self.coord_y = self.drawingPic.getHeight() - 1
    
    #Zoom method
    def updateZoom(self, zoomRate):
        self.drawingPic.width = int(self.imageSize.width()*zoomRate)
        self.drawingPic.height = int(self.imageSize.height()*zoomRate)
        self.drawingPic.image = QtGui.QImage(self.fixedPixmap.scaled(\
            self.drawingPic.width, self.drawingPic.height,\
            QtCore.Qt.KeepAspectRatioByExpanding))
        self.pic = self.drawingPic
        self.xwidget.setRange(0, self.drawingPic.getWidth()-1)
        self.ywidget.setRange(0, self.drawingPic.getHeight()-1)
        self.picLabel.setFixedWidth(self.drawingPic.width)
        self.picLabel.setFixedHeight(self.drawingPic.height)
        self.picLabel.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        # Update coords
        self.coord_x = int(self.coord_x * 1.0 * zoomRate / self.currentZoomRate)
        self.coord_y = int(self.coord_y * 1.0 * zoomRate / self.currentZoomRate)
        self.currentZoomRate = zoomRate
        # Repaint the 
        self.updateColorStuff()
        self.updateCrosshair2()
    
    def createImgWindow(self):
        #Picture window
        self.imgFrame = QtWidgets.QFrame(self)
        layoutImg = QtWidgets.QHBoxLayout()
        self.imgFrame.setLayout(layoutImg)
        self.picLabel = ClickableLabel(self, self)
        pixmap2 = QtGui.QPixmap.fromImage(self.drawingPic.image)
        # pixmap2 = self.fixedPixmap
        self.picLabel.setFixedWidth(self.drawingPic.width)
        self.picLabel.setFixedHeight(self.drawingPic.height)
        self.picLabel.setPixmap(pixmap2)
        #Set Up Scroll Area
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidget(self.picLabel)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFixedHeight(self.pic.getHeight() + 2)
        self.scroll.setFixedWidth(max(self.pic.getWidth() + 2, 250))
        self.scroll.alignment()
        #End scroll area
        layoutImg.addWidget(self.scroll)
        self.layout.addWidget(self.imgFrame)
    
    def createFrames(self):
        #Frame for X and Y
        self.XYFrame = QtWidgets.QFrame(self)
        layoutXY = QtWidgets.QHBoxLayout()
        self.XYFrame.setLayout(layoutXY)
        self.block_edit = False
        #X
        xlabel = QtWidgets.QLabel(self.XYFrame)
        xlabel.setText("X:")
        layoutXY.addWidget(xlabel)
        self.xwidget = QtWidgets.QSpinBox(self.XYFrame)
        self.xwidget.setRange(0, self.drawingPic.getWidth()-1)
        self.xwidget.setValue(self.coord_x)
        self.xwidget.valueChanged.connect(self.updatedPos)
        layoutXY.addWidget(self.xwidget)
        #Y
        ylabel = QtWidgets.QLabel(self.XYFrame)
        ylabel.setText("Y:")
        layoutXY.addWidget(ylabel)
        self.ywidget = QtWidgets.QSpinBox(self.XYFrame)
        self.ywidget.setRange(0, self.drawingPic.getHeight()-1)
        self.ywidget.setValue(self.coord_y)
        self.ywidget.valueChanged.connect(self.updatedPos)
        layoutXY.addWidget(self.ywidget)
        self.layout.addWidget(self.XYFrame)
        
        #Frame for color stuff
        self.colFrame = QtWidgets.QFrame(self)
        layoutCol = QtWidgets.QHBoxLayout()
        self.colFrame.setLayout(layoutCol)
        #RGB text
        self.rgblabel = QtWidgets.QLabel(self.colFrame)
        #col = getColor(getPixel(pic,self.coord_x,self.coord_y)).getRGB()
        #self.rgblabel.setText("R: " + str(col[0]) + " G: " + str(col[1]) + \
        #    " B: " + str(col[2]))
        layoutCol.addWidget(self.rgblabel)
        colloclabel = QtWidgets.QLabel(self.colFrame)
        colloclabel.setText("Color at location:")
        layoutCol.addWidget(colloclabel)
        #Color block
        # colimg = QImage(COL_BLOCK_SIZE, COL_BLOCK_SIZE, QImage.Format_RGB32)
        # colimg.fill(QColor(*col)) #TODO
        widgetColBlock = QtWidgets.QScrollArea()
        widgetColBlock.setFixedHeight(COL_BLOCK_SIZE + 2)
        widgetColBlock.setFixedWidth(COL_BLOCK_SIZE + 2)
        self.colLabel = QtWidgets.QLabel(self.colFrame)
        #self.setColorBlock(*col)
        self.updateColorStuff()
        # pixmap1 = QPixmap.fromImage(colimg)
        # self.colLabel.setPixmap(pixmap1)
        widgetColBlock.setWidget(self.colLabel)
        layoutCol.addWidget(widgetColBlock)
        #layoutCol.addWidget(self.colLabel)
        self.layout.addWidget(self.colFrame)
    
    def createMenuButtons(self): 
        #Set up Zoom on menu bar
        mainMenu = QtWidgets.QMenuBar(self)
        fileMenu = mainMenu.addMenu('&Zoom')
        #Create button
        extractAction25 = QtWidgets.QAction("25%", self)
        extractAction50 = QtWidgets.QAction("50%", self)
        extractAction75 = QtWidgets.QAction("75%", self)
        extractAction100 = QtWidgets.QAction("100%", self)
        extractAction150 = QtWidgets.QAction("150%", self)
        extractAction200 = QtWidgets.QAction("200%", self)
        extractAction500 = QtWidgets.QAction("500%", self)
        #Connect button
        extractAction25.triggered.connect(self.zoom25)
        extractAction50.triggered.connect(self.zoom50)
        extractAction75.triggered.connect(self.zoom75)
        extractAction100.triggered.connect(self.zoom100)
        extractAction150.triggered.connect(self.zoom150)
        extractAction200.triggered.connect(self.zoom200)
        extractAction500.triggered.connect(self.zoom500)
        #Add button to file menu
        fileMenu.addAction(extractAction25)
        fileMenu.addAction(extractAction50)
        fileMenu.addAction(extractAction75)
        fileMenu.addAction(extractAction100)
        fileMenu.addAction(extractAction150)
        fileMenu.addAction(extractAction200)
        fileMenu.addAction(extractAction500)   
    
    def zoom25(self):
        self.updateZoom(0.25)
    def zoom50(self):
        self.updateZoom(0.5)
    def zoom75(self):
        self.updateZoom(0.75)
    def zoom100(self):
        self.updateZoom(1.0)
    def zoom150(self):
        self.updateZoom(1.5)
    def zoom200(self):
        self.updateZoom(2.0)
    def zoom500(self):
        self.updateZoom(5)
   
    # (Hieu) This function is created to be compatible with ClickableLabel class
    # Drag mouse on image
    def mouseDraged(self, startP, stopP):
        self.imageClicked(stopP)

##START OF SOUND

#Emulate the JES Sound Explorer
class SoundExplorer(QtWidgets.QWidget):
    #TODO make look nice
    #TODO selections #Done
    
    #TODO make these variable/scrollable #Done
    PIC_WIDTH = 600
    PIC_HEIGHT = 200
    EXTRA_HEIGHT = 300
    
    #Constructor
    #Should create window, populate with default values
    #remember it globally (to avoid garbage collection issues)
    #and show it
    def __init__(self, sound):
        super().__init__()
        
        self.sound = sound
        self.block_edit = False
        
        title = "Sound"
        if sound.fileName is not None:
            title = sound.fileName
        self.setWindowTitle("Sound Explorer: " + title)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.setFixedWidth(self.PIC_WIDTH + 62)
        #print(int(self.contentsMargins()))
        
        #What's selected?
        self.index = 0
        self.value = getSampleValueAt(sound, self.index)
        
        #Top row of buttons
        self.playFrame = QtWidgets.QFrame(self)
        layoutPlay = QtWidgets.QHBoxLayout()
        self.playFrame.setLayout(layoutPlay)
        self.playButton = QtWidgets.QPushButton("Play Entire Sound", self.playFrame)
        self.playButton.clicked.connect(sound.play)
        self.playBeforeButton = QtWidgets.QPushButton("Play Before", self.playFrame)
        def lpb():
            sound.play(0, self.index)
        self.playBeforeButton.clicked.connect(lpb)
        self.playAfterButton = QtWidgets.QPushButton("Play After", self.playFrame)
        def lpa():
            sound.play(self.index)
        self.playAfterButton.clicked.connect(lpa)
        self.stopButton = QtWidgets.QPushButton("Stop Playing", self.playFrame)
        self.stopButton.clicked.connect(sound.stopPlaying)
        self.playBeforeButton.setDisabled(True)
        self.playAfterButton.setDisabled(True)
        #self.stopButton.setDisabled(True)
        layoutPlay.addWidget(self.playButton)
        layoutPlay.addWidget(self.playBeforeButton)
        layoutPlay.addWidget(self.playAfterButton)
        layoutPlay.addWidget(self.stopButton)
        layout.addWidget(self.playFrame)
        
        #Second row of buttons
        #TODO selections #Done
        self.selectFrame = QtWidgets.QFrame(self)
        layoutSelect = QtWidgets.QHBoxLayout()
        self.selectFrame.setLayout(layoutSelect)
        self.startIndex = 0
        self.stopIndex = 0
        self.playSelectionButton = QtWidgets.QPushButton("Play Selection", self.selectFrame)
        self.playSelectionButton.setDisabled(True)
        def playSelect():
            sound.play(self.startIndex, self.stopIndex)
        self.playSelectionButton.clicked.connect(playSelect)    
        layoutSelect.addWidget(self.playSelectionButton)
        self.clearSelectionButton = QtWidgets.QPushButton("Clear Selection", self.selectFrame)
        self.clearSelectionButton.setDisabled(True)
        def clearSelect():
            self.picLabel.rubberBand.hide()
            self.StartIndexwidget.setText("N/A")
            self.StopIndexwidget.setText("N/A")
            self.clearSelectionButton.setDisabled(True)
            self.playSelectionButton.setDisabled(True)
        self.clearSelectionButton.clicked.connect(clearSelect)       
        layoutSelect.addWidget(self.clearSelectionButton)
        self.StartIndexlabel = QtWidgets.QLabel(self.selectFrame)
        self.StartIndexlabel.setText("Start Index:")
        layoutSelect.addWidget(self.StartIndexlabel)
        self.StartIndexwidget = QtWidgets.QLabel(self.selectFrame)
        self.StartIndexwidget.setText("N/A")
        layoutSelect.addWidget(self.StartIndexwidget)
        self.StopIndexlabel = QtWidgets.QLabel(self.selectFrame)
        self.StopIndexlabel.setText("Stop Index:")
        layoutSelect.addWidget(self.StopIndexlabel)
        self.StopIndexwidget = QtWidgets.QLabel(self.selectFrame)
        self.StopIndexwidget.setText("N/A")
        layoutSelect.addWidget(self.StopIndexwidget)
        layout.addWidget(self.selectFrame)
        
        #(Hieu): Add scrollArea
        #Sound image
        self.imgFrame = QtWidgets.QFrame(self)
        layoutImg = QtWidgets.QHBoxLayout()
        self.imgFrame.setLayout(layoutImg)
        self.picLabel = ClickableLabel(self, self)
        self.pic = sound.getImageRep(SoundExplorer.PIC_WIDTH, SoundExplorer.PIC_HEIGHT)
        # Create a variable currentPicWidth that hold the current width of sound image
        self.currentPicWidth = SoundExplorer.PIC_WIDTH
        # self.drawingPic = duplicatePicture(self.pic)
        self.drawingPic = self.pic
        # pixmap = QPixmap.fromImage(self.drawingPic.image)
        self.picLabel.setPixmap(self.drawingPic)
        self.picLabel.setFixedWidth(self.currentPicWidth)
        #Set Up Scroll Area
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidget(self.picLabel)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFixedHeight(SoundExplorer.PIC_HEIGHT + 2)
        self.scroll.setFixedWidth(SoundExplorer.PIC_WIDTH + 2)
        #End scroll area
        layoutImg.addWidget(self.scroll)
        layout.addWidget(self.imgFrame)
        
        #Index/value row
        self.indexValueFrame = QtWidgets.QFrame(self)
        layoutIV = QtWidgets.QHBoxLayout()
        self.indexValueFrame.setLayout(layoutIV)
        self.ilabel = QtWidgets.QLabel(self.indexValueFrame)
        self.ilabel.setText("Current Index:")
        layoutIV.addWidget(self.ilabel)
        self.iwidget = QtWidgets.QSpinBox(self.indexValueFrame)
        #self.iwidget.setButtonSymbols(QAbstractSpinBox.lineNoButtons) #Hide arrow
        self.iwidget.setRange(0, getLength(sound))
        self.iwidget.setValue(self.index)
        #QObject.connect(self.ywidget, SIGNAL('valueChanged(int)'), self, SLOT('updatedPos()'))
        self.iwidget.valueChanged.connect(self.updatedPos)
        layoutIV.addWidget(self.iwidget)
        self.vlabel = QtWidgets.QLabel(self.indexValueFrame)
        self.vlabel.setText("Sample Value:")
        layoutIV.addWidget(self.vlabel)
        self.vwidget = QtWidgets.QLabel(self.indexValueFrame)
        self.vwidget.setText(str(self.value))
        #QObject.connect(self.ywidget, SIGNAL('valueChanged(int)'), self, SLOT('updatedPos()'))
        #self.iwidget.valueChanged(int).connect(self.updatedPos())
        layoutIV.addWidget(self.vwidget)
        layout.addWidget(self.indexValueFrame)
        
        #Samples between pixels row
        self.sbetweenFrame = QtWidgets.QFrame(self)
        layoutSB = QtWidgets.QHBoxLayout()
        self.sbetweenFrame.setLayout(layoutSB)
        self.sblabel = QtWidgets.QLabel(self.sbetweenFrame)
        self.sblabel.setText("The number of samples between pixels:")
        layoutSB.addWidget(self.sblabel)
        #TODO make variable #Done
        self.sbwidget = QtWidgets.QLineEdit(self.sbetweenFrame)
        self.sbwidget.insert(str(getLength(sound) // self.currentPicWidth))
        self.sbwidget.setFixedWidth(120)
        self.sbwidget.returnPressed.connect(self.updatedSBW)
        # self.sbwidget = QLabel(self.sbetweenFrame)
        # self.sbwidget.setText(str(getLength(sound) // SoundExplorer.PIC_WIDTH))
        layoutSB.addWidget(self.sbwidget)
        layout.addWidget(self.sbetweenFrame)
        
        #Zoom row
        self.zoomFrame = QtWidgets.QFrame(self)
        layoutZoom = QtWidgets.QHBoxLayout()
        self.zoomFrame.setLayout(layoutZoom)
        self.isZoomIn = 0;
        self.zoomButton = QtWidgets.QPushButton("Zoom In", self.zoomFrame)
        self.zoomButton.clicked.connect(self.zoomClick)
        layoutZoom.addWidget(self.zoomButton)
        layout.addWidget(self.zoomFrame)
        
        #Resize the window
        SoundExplorer.PIC_WIDTH
        self.resize(SoundExplorer.PIC_WIDTH, SoundExplorer.PIC_HEIGHT + SoundExplorer.EXTRA_HEIGHT)
        #self.resize(self.drawingPic.getWidth(), self.drawingPic.getHeight() + SoundExplorer.EXTRA_HEIGHT)
        #Remember the window
        keepAround.append(self)
        #Show the window
        self.show()
        self.activateWindow()
        self.raise_()
        self.activateWindow()
        QtWidgets.QApplication.processEvents()
    
    #Zoom-in-out click button
    def zoomClick(self):
        if self.isZoomIn:
            self.zoomButton.setText("Zoom In")
            self.isZoomIn = 0
            self.currentPicWidth = SoundExplorer.PIC_WIDTH
            self.sbwidget.setText(str(getLength(self.sound) // self.currentPicWidth))
            self.updateSoundImage()
        else:
            self.zoomButton.setText("Zoom Out")
            self.isZoomIn = 1
            self.currentPicWidth = getLength(self.sound)
            self.sbwidget.setText("1")
            self.updateSoundImage()
    
    # #(Hieu)Scale-Image function:
    # # sampix = # of samples between pitxel
    # def scaleImg(self,sampix):
    #     sound.getImageRep(SoundExplorer.PIC_WIDTH, SoundExplorer.PIC_HEIGHT)
    
    #Update Sound Image
    def updateSoundImage(self):
        self.pic = self.sound.getImageRep(self.currentPicWidth, SoundExplorer.PIC_HEIGHT)
        self.drawingPic = self.pic
        self.picLabel.setPixmap(self.drawingPic)
        self.picLabel.setFixedWidth(self.currentPicWidth)
    
    #Sample between Pixel was updated via sbw box
    #Update things
    def updatedSBW(self):
        #Only do this if we manually changed the numbers
        if not self.block_edit:
            #New sample between Pixel value
            self.sampleBP = int(self.sbwidget.text())
            self.currentPicWidth = getLength(self.sound) // self.sampleBP
            #Update
            self.updateSoundImage()
            #Repaint the window
            self.update()
            QtWidgets.QApplication.processEvents()
    
    #Update value position and show it
    # def updateSelection(self):
    #     self.drawingPic = duplicatePicture(self.pic)
    #     #Draw the selection line
    #     x_coord = int(self.index * (SoundExplorer.PIC_WIDTH / getLength(self.sound)))
    #     addLine(self.drawingPic, x_coord, 0, x_coord, SoundExplorer.PIC_HEIGHT-1, cyan)
    #     pixmap = QPixmap.fromImage(self.drawingPic.image)
    #     self.picLabel.setPixmap(pixmap)
    
    def updateSelection(self):
        self.drawingPic = QtGui.QPixmap(self.pic)
        #Draw the selection line
        x_coord = int(self.index * (self.currentPicWidth / getLength(self.sound)))
        addLine1(self.drawingPic, x_coord, 0, x_coord, SoundExplorer.PIC_HEIGHT-1, cyan)
        self.picLabel.setPixmap(self.drawingPic)
    
    # @pyqtSlot(int)
    # def test(self, x):
    #     print("hello " + str(x))
    
    #Position was updated via index box
    #Update things
    #@pyqtSlot()
    def updatedPos(self):
        #Only do this if we manually changed the numbers
        if not self.block_edit:
            #New index
            self.index = self.iwidget.value()
            self.value = getSampleValueAt(self.sound, self.index)
            self.vwidget.setText(str(self.value))
            #Update
            self.updateSelection()
            #Repaint the window
            self.update()
            QtWidgets.QApplication.processEvents()
    
    #Clicked on image
    def imageClicked(self, pt):
        #Make sure we don't issue duplicate updates
        self.block_edit = True
        #Update the index
        self.index = int(pt.x() * (getLength(self.sound) / self.currentPicWidth))
        self.value = getSampleValueAt(self.sound, self.index)
        #Change the widgets to the new coords
        self.iwidget.setValue(self.index)
        self.vwidget.setText(str(self.value))
        #Enable Buttons
        self.playBeforeButton.setDisabled(False)
        self.playAfterButton.setDisabled(False)
        #Update the stuff that can change
        self.updateSelection()
        #Repaint the window
        self.update()
        QtWidgets.QApplication.processEvents()
        #Manual updates are safe again
        self.block_edit = False
     
    # Drag mouse on image
    def mouseDraged(self, startP, stopP):
        #Make sure we don't issue duplicate updates
        self.block_edit = True
        # Update Start & Stop Index
        self.startIndex = int(startP.x() * (getLength(self.sound) / self.currentPicWidth))
        self.stopIndex = int(stopP.x() * (getLength(self.sound) / self.currentPicWidth))
        if self.startIndex > self.stopIndex:
            self.startIndex, self.stopIndex = self.stopIndex, self.startIndex
        self.StartIndexwidget.setText(str(self.startIndex))
        self.StopIndexwidget.setText(str(self.stopIndex))
        # Enable Buttons
        self.playSelectionButton.setDisabled(False)
        self.clearSelectionButton.setDisabled(False)
        #Start select region on image
        self.picLabel.rubberBand.show()
        Qtop = QtCore.QPoint(int(startP.x()),0)
        Qbot = QtCore.QPoint(int(stopP.x()),200)
        self.picLabel.rubberBand.setGeometry(QtCore.QRect(Qtop, Qbot).normalized())
        #Repaint the window
        self.update()
        QtWidgets.QApplication.processEvents()
        #Manual updates are safe again
        self.block_edit = False

#END OF SOUND

#Open explorer tool for media (currently only pictures and sound)
#TODO: Movie
def explore(media):
    """
        Opens the explorer, which lets you examine the media.
        
        :param media: A Picture, Sound, or Movie that you want to view using
                    Media Tools.
    """
    if isinstance(media, Picture):
        openPictureTool(media)
    elif isinstance(media, Sound):
        openSoundTool(media)
    elif isinstance(media, Movie):
        openFrameSequencerTool(media)
    else:
        repValError("Exploration of this media is not supported")
        #raise ValueError

#Try to mimic functionality of JES picture explorer
#Done
def openPictureTool(picture):
    """
        Opens the Picture Tool explorer, which lets you examine the pixels of 
        an image.
        
        :param picture: the picture that you want to examine
    """
    #import PictureExplorer
    thecopy = duplicatePicture(picture)
    #Constructor has side effect of showing it
    PictureExplorer(thecopy)
# 
# #    viewer.changeToBaseOne();
#     #viewer.setTitle(getShortPath(picture.getFileName() ))
#     pass #TODO
# 
    # USE THE WINDOW TO BLOCK THE CALLING PROGRAM
        #  THIS IS NECESSARY FOR THONNY WITH THIS PARTICULAR
        #  IMPLEMENTATION.
    root.exec_()

#Done
def openFrameSequencerTool(movie):
    """
        Opens the Frame Sequencer Tool explorer, which lets you examine and
        manipulate the frames of a movie
        
        :param movie: the movie that you want to examine
    """
    FrameSequencer(movie)

    # USE THE WINDOW TO BLOCK THE CALLING PROGRAM
        #  THIS IS NECESSARY FOR THONNY WITH THIS PARTICULAR
        #  IMPLEMENTATION.
    root.exec_()

#Try to mimic functionality of JES sound explorer
def openSoundTool(sound):
    """
        Opens the Sound Tool explorer, which lets you examine the waveform of a sound.
        
        :param sound : the sound that you want to examine
    """
    #import SoundExplorer
    thecopy = duplicateSound(sound)
    #Constructor has side effect of showing it
    SoundExplorer(thecopy)

    # USE THE WINDOW TO BLOCK THE CALLING PROGRAM
        #  THIS IS NECESSARY FOR THONNY WITH THIS PARTICULAR
        #  IMPLEMENTATION.
    root.exec_()

# #Done
# def explore(someMedia):
#     if isinstance(someMedia, Picture):
#         openPictureTool(someMedia)
#     elif isinstance(someMedia, Sound):
#         openSoundTool(someMedia)
#     elif isinstance(someMedia, Movie):
#         openFrameSequencerTool(someMedia)
#     else:
#         print("explore(someMedia): Input is not a Picture, Sound, or Movie")
#         raise ValueError
#
 
# let's try the turtles...
#Can we escape from Worlds?
WORLDS_ESCAPABLE = False
def setWorldsEscapable(escapable):
    global WORLDS_ESCAPABLE
    WORLDS_ESCAPABLE = escapable

#Draw a turtle on a picture at given coordinates
def drawTurtle(pic, x, y, heading, color):
    BODY_SIZE = 16
    addOvalFilled(pic, x - BODY_SIZE // 2, y - BODY_SIZE // 2, BODY_SIZE,\
        BODY_SIZE, color)
    HEAD_SIZE = 6
    HEAD_COLOR = makeColor(0, 127, 0)
    head_x = x + int(BODY_SIZE * math.sin(math.radians(heading)) * 0.65)
    head_y = y - int(BODY_SIZE * math.cos(math.radians(heading)) * 0.65)
    addOvalFilled(pic, head_x - HEAD_SIZE // 2, head_y - HEAD_SIZE // 2,
        HEAD_SIZE, HEAD_SIZE, HEAD_COLOR)

#World class
#Just a wrapper for Picture
class World:
    def __init__(self, width = None, height = None):
        #Dimensions of the world
        if width is None:
            self.width = 640
            self.height = 480
        else:
            self.width = width
            self.height = height
        #World contains no turtles
        self.turtles = list()
        #Picture being wrapped
        self.picture = makeEmptyPicture(self.width, self.height)
        self.render = makeEmptyPicture(self.width, self.height)
        self.visible = False
        #Show the world
        self.update()
    
    #Update the view of the world
    def update(self):
        if self.visible:
            show_method = repaint
        else:
            show_method = lambda pic: show(pic, "World")
        
        #Render the turtles on the picture
        render = duplicatePicture(self.picture)
        for turtle in self.turtles:
            drawTurtle(render, turtle.getXPos(), turtle.getYPos(),\
                turtle.getHeading(), turtle.getColor())
        copyInto(render, self.render, 0, 0)
        self.visible = True
        show_method(self.render)
    
    #Show the world
    #(perhaps you closed it?)
    def show(self):
        self.visible = False
        self.update()
    
    #Add a turtle
    #Should only be called by a turtle
    def addTurtle(self, turtle):
        self.turtles.append(turtle)
        self.update()
    
    #Retrieve the list of turtles
    def getTurtleList(self):
        return self.turtles
    
    #String representation
    def __str__(self):
        return "A %d by %d world with %d turtles in it."%(self.width,\
            self.height, len(self.turtles))

#Turtles!
class Turtle:
    #Constructor
    #Requires a world
    #Can also take coordinates
    def __init__(self, world, x = None, y = None):
        self.world = world
        #Turtles in JES are apparently nameable
        self.name = None
        #Set coordinates
        if x is None:
            self.x = 320
            self.y = 240
        else:
            self.x = x
            self.y = y
        #Starts pointing north
        #Increasing is clockwise
        self.heading = 0.
        #Initial color in JES is green
        self.color = green
        #Pen starts down
        self.hasPenDown = True
        if isinstance(self.world, World):
            #Add the turtle to the world
            world.addTurtle(self)
            self.picture = self.world.picture
        else:
            self.picture = self.world
    
    #Update visuals
    def update(self):
        if isinstance(self.world, World):
            self.world.update()
    
    #Nice string representation
    def __str__(self):
        if self.name is None:
            name = "No name"
        else:
            name = self.name
        return "%s turtle at %d, %d heading %.1f."%(name, self.x, self.y,\
            self.heading)
    
    #Accessors
    def getXPos(self):
        return self.x
    
    def getYPos(self):
        return self.y
    
    def getHeading(self):
        return self.heading
    
    def getColor(self):
        return self.color
    
    #Mutators
    #Change the turtle's color
    def setColor(self, color):
        self.color = color
        #Update the turtle's color in the World
        self.update()
    
    #Set heading
    def setHeading(self, heading):
        self.heading = float(heading)
        self.heading %= 360
        #Update the turtle's color in the World
        self.update()
    
    #Turn right by specified number of degrees
    def turn(self, degrees = 90):
        self.setHeading(self.heading + degrees)       
    
    #Turn right
    def turnRight(self):
        self.turn(90)
    
    #Turn left
    def turnLeft(self):
        self.turn(-90)
    
    #Turn to face another Turtle or an (x, y) coordinate
    def turnToFace(self, x, y = None):
        #Get the coordinates
        if isinstance(x, Turtle):
            the_x = x.getXPos()
            the_y = x.getYPos()
        else:
            the_x = x
            the_y = y
        #Horizontal case
        if the_y == self.y:
            if the_x > self.x:
                self.setHeading(90)
            elif the_x < self.x:
                self.setHeading(-90)
            #If they're both equal, do nothing
        else:
            #Not vertical, use arctan
            angle = math.degrees(math.atan((the_x - self.x)/(self.y - the_y)))
            if the_y < self.y:
                self.setHeading(angle)
            else:
                self.setHeading(angle + 180)
    
    #Set the coordinates of the turtle
    def moveTo(self, x, y):
        new_x = x
        new_y = y
        #Don't leave the world, if that setting is on
        if not WORLDS_ESCAPABLE:
            new_x = max(0, new_x)
            new_y = max(0, new_y)
            new_x = min(self.world.width, new_x)
            new_y = min(self.world.height, new_y)
        #Draw a line, if the pen is down
        if self.hasPenDown:
            addLine(self.picture, self.x, self.y, new_x, new_y, self.color)
        #Move the turtle
        self.x = new_x
        self.y = new_y
        #Update the World
        self.update()
    
    #Move a given number of pixels in the given direction
    def move(self, pixels, heading):
        #Figure out x and y components of motion
        delta_x = pixels * math.sin(math.radians(heading))
        delta_y = -pixels * math.cos(math.radians(heading))
        #New coordinates
        new_x = self.x + delta_x
        new_y = self.y + delta_y
        #Move
        self.moveTo(new_x, new_y)
    
    #Move forward
    def forward(self, pixels):
        self.move(pixels, self.heading)
    
    #Move backward
    def backward(self, pixels):
        self.move(pixels, -self.heading)
    
    #Pen up
    def penUp(self):
        self.hasPenDown = False
    
    #Pen down
    def penDown(self):
        self.hasPenDown = True
    
    #Drop a picture
    def drop(self, picture):
        self.picture.copyInto(picture, self.x, self.y, self.heading)
        self.update()

#Turn the turtle right by the specified angle
def turn(turtle, degrees=90):
    if not isinstance(turtle, Turtle):
        repTypeError("turn(turtle[, degrees]): Input is not a turtle")
    if not isinstance(degrees, int) and not isinstance(degrees, float):
        repTypeError("turn(turtle[, degrees]): Second input is not a number")
    turtle.turn(degrees)

#Turn right 90 degrees
def turnRight(turtle):
    if not isinstance(turtle, Turtle):
        repTypeError("turnRight(turtle): Input is not a turtle")
    else:
        turtle.turnRight()

#Turn left 90 degrees
def turnLeft(turtle):
    if not isinstance(turtle, Turtle):
        repTypeError("turnLeft(turtle): Input is not a turtle")
    else:
        turtle.turnLeft()

#Turn to face another Turtle, or a given point (x, y)
def turnToFace(turtle, x, y=None):
    if y == None:
        if not isinstance(turtle, Turtle):
            repTypeError("turnToFace(turtle, turtle): First input is not a turtle")
        elif not isinstance(x, Turtle):
            repTypeError("turnToFace(turtle, turtle): Second input is not a turtle")
        else:
            turtle.turnToFace(x)
    else:
        if not isinstance(turtle, Turtle):
            repTypeError("turnToFace(turtle, x, y): First input is not a turtle")
        elif not isinstance(x, int) and not isinstance(x, float):
            repTypeError("turnToFace(turtle, x, y): Second input is not a number")
        elif not isinstance(y, int) and not isinstance(y, float):
            repTypeError("turnToFace(turtle, x, y): Third input is not a number")
        else:
            turtle.turnToFace(x, y)

#Move forward
def forward(turtle, pixels=100):
    if not isinstance(turtle,Turtle):
        repTypeError("forward(turtle[, pixels]): Input is not a turtle")
    if not isinstance(pixels, int) and not isinstance(pixels, float):
        repTypeError("turn(turtle[, degrees]): Second input is not a number")
    turtle.forward(pixels)

#Move backward
def backward(turtle, pixels=100):
    if not isinstance(turtle,Turtle):
        repTypeError("backward(turtle[, pixels]): Input is not a turtle")
    if not isinstance(pixels, int) and not isinstance(pixels, float):
        repTypeError("turn(turtle[, degrees]): Second input is not a number")
    turtle.backward(pixels)

#Teleport to (x, y)
def moveTo(turtle, x, y):
    if not isinstance(turtle,Turtle):
        repTypeError("moveTo(turtle, x, y): Input is not a turtle")
    if not isinstance(x, int) and not isinstance(x, float):
        repTypeError("turn(turtle[, degrees]): Second input is not a number")
    if not isinstance(y, int) and not isinstance(y, float):
        repTypeError("turn(turtle[, degrees]): Third input is not a number")
    turtle.moveTo(x, y)

#Create a new turtle on the given World/Picture
def makeTurtle(world):
    if not (isinstance(world, World) or isinstance(world, Picture)):
        repTypeError("makeTurtle(world): Input is not a world or picture")
    turtle = Turtle(world)
    return turtle

#Pen up (don't draw)
def penUp(turtle):
    if not isinstance(turtle, Turtle):
        repTypeError("penUp(turtle): Input is not a turtle")
    turtle.penUp()

#Pen down (do draw)
def penDown(turtle):
    if not isinstance(turtle, Turtle):
        repTypeError("penDown(turtle): Input is not a turtle")
    turtle.penUp()

#Drop a picture
def drop(turtle, picture):
    if not isinstance(turtle, Turtle):
        repTypeError("drop(turtle, picture): First input is not a turtle")
    if not isinstance(picture,Picture):
        repTypeError("drop(turtle, picture): Second input is not a picture")
    turtle.drop(picture)


#Retrieve the turtle's x coordinate
def getXPos(turtle):
    if not isinstance(turtle, Turtle):
        repTypeError("getXPos(turtle): Input is not a turtle")
    return turtle.getXPos()

#Retrieve the turtle's y coordinate
def getYPos(turtle):
    if not isinstance(turtle, Turtle):
        repTypeError("getYPos(turtle): Input is not a turtle")
    return turtle.getYPos()

#Retrieve the turtle's heading
def getHeading(turtle):
    if not isinstance(turtle, Turtle):
        repTypeError("getHeading(turtle): Input is not a turtle")
    return turtle.getHeading()


## world methods
def makeWorld(width=None, height=None):
    if width is not None:
        if not isinstance(width, int):
            repTypeError("makeWorld(width, height): First input is not an integer")
        if width <= 0:
            repValError("makeWorld(width, height): First input is not positive")
        if not isinstance(height, int):
            repTypeError("makeWorld(width, height): SEcond input is not an integer")
        if height <= 0:
            repValError("makeWorld(width, height): Second input is not positive")
        w = World(width, height)
    else:
        w = World()
    return w


def getTurtleList(world):
    if not isinstance(world, World):
        repTypeError("getTurtleList(world): Input is not a world")
    return world.getTurtleList()

# end of stuff imported for worlds and turtles

# used in the book
#Done
#This is dumb
def printNow(output):
    """
        Prints the specified output to the JES command area right now, without
        waiting for buffering. Helpful for debugging, if your program is
        throwing an exception!

        :param output: What we want to print
    """
    print(output)

class Movie(QtGui.QMovie):
    #TODO make the constructor accept different type of input.
    #TODO writeFramesToDirectory
    def __init__(self, frames = [], directory = None): # frames are filenames
        super().__init__()
        self.frames = frames
        self.dir = directory

    def addFrame(self, frame):
        self.frames.append(frame)
        self.dir = None

    def __len__(self):
        return len(self.frames)

    def __str__(self):
        return "Movie, frames: "+str(len(self))

    def __repr__(self):
        return "Movie, frames: "+str(len(self))

    def __getitem__(self,item):
        return self.frames[item]

    # def writeFramesToDirectory(self, directory):
    #     import FrameSequencer
    #     fs = FrameSequencer(directory)
    #     #for frameindex in range(0, self.listModel.size()):
    #         #fs.addFrame(Picture(self.listModel.get(frameindex)))
    #         #fs.play(self.fps)
    #     for frameindex in range(0, len(self.frames)):
    #         fs.addFrame(Picture(self.frames[frameindex]))
    #     self.dir = directory

    def play(self):
        MoviePlayer(self).playMovie()
        
        # USE THE WINDOW TO BLOCK THE CALLING PROGRAM
        #  THIS IS NECESSARY FOR THONNY WITH THIS PARTICULAR
        #  IMPLEMENTATION.
        root.exec_()

    # def writeQuicktime(self, destPath, framesPerSec = 16):
    #     global mediaFolder
    #     if not os.path.isabs(destPath):
    #         destPath = mediaFolder + destPath
    #     destPath = "file://"+destPath
    #     if framesPerSec <= 0:
    #         print("writeQuicktime(path[, framesPerSec]): Frame Rate must be a positive number")
    #         raise ValueError
    #     if self.frames == []: #Is movie empty?
    #         print("writeQuicktime(path[, framesPerSec]): Movie has no frames. Cannot write empty Movie")
    #         raise ValueError
    #     elif self.dir == None and len(self.frames) == 1: #Is movie only 1 frame but never written out
    #         frame = self.frames[0]
    #         self.dir = frame[:(frame.rfind(os.sep))]
    #     elif self.dir == None and len(self.frames) > 1: #Are movie frames all in the same directory? 
    #         sameDir = 1
    #         frame = self.frames[0]
    #         frame = frame.replace('/', os.sep)
    #         framesDir = frame[:(frame.rfind(os.sep))] #Parse directory of first frame
    #         thisDir = framesDir
    #         frameNum = 1
    #         while(sameDir and frameNum < len(self.frames)):
    #             frame = self.frames[frameNum]
    #             frame = frame.replace('/', os.sep) #Eliminate possibility of / vs. \ causing problems
    #             thisDir = frame[:(frame.rfind(os.sep))]
    #             frameNum = frameNum+1
    #             if(framesDir != thisDir):
    #                 sameDir = 0
    #         if(sameDir): #Loop ended because we ran out of frames
    #             self.dir = framesDir
    #         else: #Loop ended because sameDir became false
    #             print("writeQuicktime(path[, framesPerSec]): Your frames are in different directories. Call writeFramesToDirectory() first, then try again.")
    #             raise ValueError
    #     writer = MovieWriter(self.dir, framesPerSec, destPath)
    #     writer.writeQuicktime()
        
    # def writeAVI(self, destPath, framesPerSec = 16):
    #     global mediaFolder
    #     if not os.path.isabs(destPath):
    #         destPath = mediaFolder + destPath
    #     destPath = "file://"+destPath
    #     if framesPerSec <= 0:
    #         print("writeAVI(path[, framesPerSec]): Frame Rate must be a positive number")
    #         raise ValueError
    #     if self.frames == []: #Is movie empty?
    #         print("writeAVI(path[, framesPerSec]): Movie has no frames. Cannot write empty Movie")
    #         raise ValueError
    #     elif self.dir == None and len(self.frames) == 1: #Is movie only 1 frame but never written out
    #         frame = self.frames[0]
    #         self.dir = frame[:(frame.rfind(os.sep))]
    #     elif self.dir == None and len(self.frames) > 1: #Are movie frames all in the same directory? 
    #         sameDir = 1
    #         frame = self.frames[0]
    #         frame = frame.replace('/', os.sep)
    #         framesDir = frame[:(frame.rfind(os.sep))] #Parse directory of first frame
    #         thisDir = framesDir
    #         frameNum = 1
    #         while(sameDir and frameNum < len(self.frames)):
    #             frame = self.frames[frameNum]
    #             frame = frame.replace('/', os.sep)
    #             thisDir = frame[:(frame.rfind(os.sep))]
    #             frameNum = frameNum+1
    #             if(framesDir != thisDir):
    #                 sameDir = 0
    #         if(sameDir): #Loop ended because we ran out of frames
    #             self.dir = framesDir
    #         else: #Loop ended because sameDir became false
    #             print("writeAVI(path[, framesPerSec]): Your frames are in different directories. Call writeFramesToDirectory() first, then try again.")
    #             raise ValueError
    #     writer = MovieWriter(self.dir, framesPerSec, destPath)
    #     writer.writeAVI()


#Done
def playMovie(movie):
    """
        Takes a Movie object as input and plays it.

        :param movie: the movie object to be playe
    """
    if not isinstance(movie, Movie):
        repTypeError("playMovie(movie): movie is not a Movie object.")
    movie.play()
    

# #Done
# def writeQuicktime(movie, destPath, framesPerSec = 16):
#     if not (isinstance(movie, Movie)):
#         print("writeQuicktime(movie, path[, framesPerSec]): First input is not a Movie")
#         raise ValueError
#     if framesPerSec <= 0:
#         print("writeQuicktime(movie, path[, framesPerSec]): Frame rate must be a positive number")
#         raise ValueError
#     movie.writeQuicktime(destPath, framesPerSec)
# 
# #Done
# def writeAVI(movie, destPath, framesPerSec = 16):
#     if not (isinstance(movie, Movie)):
#         print("writeAVI(movie, path[, framesPerSec]): First input is not a Movie")
#         raise ValueError
#     if framesPerSec <= 0:
#         print("writeAVI(movie, path[, framesPerSec]): Frame rate must be a positive number")
#         raise ValueError
#     movie.writeAVI(destPath, framesPerSec)
# 
#Done
def makeMovie():
    """
        :return: an empty Movie object
    """
    return Movie()


#Done
def makeMovieFromInitialFile(filename):
    """
        Takes a filename as input. Returns a Movie object using the given file
        as the first frame and using sequentially named files for subsequent
        frames (i.e. frame001, frame002, etc.)

        :param filename: string path to the first frame of the movie
        :return: a Movie object using the given file as the first frame
    """
    import re
    movie = Movie()

    #filename = filename.replace(os.altsep, os.sep)
    filename = filename.replace('/',os.sep) #Hack fix because os.altsep is not defined for Windows as of Python 2.2
    sep_location = filename.rfind(os.sep)
    if(-1 == sep_location):
        filename = mediaFolder + filename

    movie.directory = filename[:(filename.rfind(os.sep))]
    movie.init_file = filename[(filename.rfind(os.sep))+1:]
    regex = re.compile('[0-9]+')
    file_regex = regex.sub('.*', movie.init_file)

    for item in os.listdir(movie.directory):
        if re.match(file_regex, item):
            movie.addFrame(movie.directory + os.sep + item)

    return movie


#Done
def addFrameToMovie(frame, movie):
    """
        Takes a filename and a Movie object as input. Adds the file as a frame
        to the end of the movie. addFrameToMovie(movie, frame) is also
        acceptable.
        
        :param frame: the filename of the frame to be added to the movie
        :param movie: the movie object for the frame to be added to
    """
    # frame = None
    # movie = None
    # if a.__class__ == Movie:
    #     movie = a
    #     frame = b
    # else:
    #     movie = b
    #     frame = a

    if not (isinstance(movie,Movie) and isinstance(frame, str)):
    # if movie.__class__ != Movie or frame.__class__ != String:
        repValError("addFrameToMovie(frame, movie): frame is not a string or movie is not a Movie objectd")

    movie.addFrame(frame)

# #Done
# def writeFramesToDirectory(movie, directory=None):
#     if not isinstance(movie, Movie):
#         print("writeFramesToDirectory(movie[, directory]): movie is not a Movie object")
#         raise ValueError
# 
#     if directory == None:
#         directory = user.home
# 
#     movie.writeFramesToDirectory(directory)
        
        
class MoviePlayer(QtWidgets.QWidget):
    PIC_WIDTH = 1000
    PIC_HEIGHT = 470
    EXTRA_HEIGHT = 520
    
    #Constructor
    #Should create window, populate with default values
    #remember it globally (to avoid garbage collection issues)
    #and show it
    def __init__(self, movie = Movie(), dictionary = None):
        super().__init__()
               
        self.dictionary = dictionary
        self.movie = movie
        self.movieList = movie.frames
        self.movie.setCacheMode(QtGui.QMovie.CacheAll)
        
        self.updateBuffer()
            
        self.framesPerSec = 16
        self.numberFrame = len(self.movieList)
        self.curentFrameNumber = self.movie.currentFrameNumber() - 1
        self.block_edit = False
               
        self.setWindowTitle("Movie Player" )
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.setFixedWidth(self.PIC_WIDTH + 62)
        self.setFixedHeight(self.EXTRA_HEIGHT)
        
        self.createFrameLabel()
        self.createMovieWindow()
        self.createButtons()
        
        #Remember the window
        keepAround.append(self)
        #Show the window
        self.show()
        self.activateWindow()
        self.raise_()
        self.activateWindow()
        QtWidgets.QApplication.processEvents()
    
    # Maybe not efficient TODO
    def updateBuffer(self): 
        self.buf = QtCore.QBuffer() #Device holding frame in format
        self.buf.open(QtCore.QIODevice.WriteOnly)    
        for i in range(len(self.movieList)):
            frame = self.movieList[i]
            image = QtGui.QImage(frame)
            image.save(self.buf, 'JPG')
        self.buf.close()
        self.movie.setDevice(self.buf)
    
    def updateStuff(self):
        self.curentFrameNumber = self.movie.currentFrameNumber()
        self.numberFrame = len(self.movieList)
        if (self.numberFrame != 0):
            self.numLabel.setText("Frame Number " + str(self.curentFrameNumber))
        else:
            self.numLabel.setText("Frame Number ")
            self.movieLabel.setText("No Movie Loaded")
         
   # Method to scale the content of image
    def fitToWindow(self):
        self.movieLabel.setScaledContents(True)
    
    # Method to jump to frame number frameNumber.
    def goToFrame(self, frameNumber):
        self.movie.jumpToFrame(frameNumber)
    
    # Method to show the next image
    def showNext(self):
        if (self.numberFrame != 0):
            self.goToFrame((self.curentFrameNumber+1)%self.numberFrame)
            self.updateStuff()
    
     # Method to show the previous image
    def showPrevious(self):
        if (self.numberFrame != 0):
            self.goToFrame((self.curentFrameNumber-1)%self.numberFrame)
            self.updateStuff()
        
    # Method to play the movie from the beginning
    # TODO param: framesPerSecond the number of frames to show per second
    def playMovie(self):
        #self.framesPerSec = framesPerSecond
        self.showAll()
        self.updateStuff()
    
    # Method to show all the image
    def showAll(self, frameRate = None):
        if frameRate != None:
            self.framesPerSec = frameRate
        startTime = 0;
        endTime = 0;
        timeToSleep = 1.0 / self.framesPerSec
        for i in range(0,self.numberFrame,1):
            startTime = time.time()
            self.goToFrame(i)
            endTime = time.time()
            sleep(timeToSleep - (endTime - startTime))
        self.updateStuff()
                
     # Method to set the frames per second to show the movie
     # param: rate the number of frames to show per second
    def updateFrameRate(self):
        if not self.block_edit:
            self.framesPerSec = self.rwidget.value()
        
    # Method to delete all the frames before the current one
    def delAllBefore(self):
        currentIndex = self.curentFrameNumber
        for i in range(0,currentIndex+1):
            # os.remove(self.movieList[0])
            del self.movieList[0]
        self.updateBuffer()
        self.updateStuff()
        # self.update()

    # Method to delete all the frames after the current one
    def delAllAfter(self):
        currentIndex = self.curentFrameNumber
        for i in range(currentIndex,self.numberFrame):
            # os.remove(self.movieList[currentIndex])
            del self.movieList[currentIndex]
        self.updateBuffer()
        self.updateStuff()
        # self.update()
        
    #  Method to write out the movie frames as a Quicktime movie
    def writeQuicktime(self):
        # MovieWriter writer = new MovieWriter(animationPanel.getFramesPerSec(),
        #                                      dir);
        # writer.writeQuicktime();
        pass #TODO

    # Method to write out the movie frames as a Quicktime movie
    def writeAVI(self):
        # MovieWriter writer = new MovieWriter(animationPanel.getFramesPerSec(),
        #                                      dir);
        # writer.writeAVI();
        pass #TODO
    
    # Method to add a picture to the movie
    # param: picture the picture to add
    def addPicture(self, picture):
        self.movie.addFrame(picture)
        self.buf.open(QtCore.QIODevice.Append)
        image = QtGui.QImage(picture)
        image.save(self.buf, 'JPG')
        self.buf.close()
        self.update()
    
    # Method to create # of Frame frame
    def createFrameLabel(self):
        self.numFrame = QtWidgets.QFrame(self)
        layoutNum = QtWidgets.QHBoxLayout()
        self.numFrame.setLayout(layoutNum)
        self.block_edit = False
        self.numLabel = QtWidgets.QLabel(self.numFrame)
        self.numLabel.setText("Frame Number ")
        self.numLabel.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignCenter)
        layoutNum.addWidget(self.numLabel)
        self.layout.addWidget(self.numFrame)
    
    # Method to create Movie window    
    def createMovieWindow(self):
        self.movieFrame = QtWidgets.QFrame(self)
        layoutMovie = QtWidgets.QHBoxLayout()
        self.movieFrame.setLayout(layoutMovie)
        self.movieLabel = QtWidgets.QLabel("No movie loaded")
        self.movieLabel.setMovie(self.movie)
        self.updateBuffer()
        self.updateStuff()
        #self.playMovie()      
        # self.fitToWindow()
        self.movieLabel.setFixedHeight(self.PIC_HEIGHT + 1)
        self.movieLabel.setAlignment(QtCore.Qt.AlignLeft)
        layoutMovie.addWidget(self.movieLabel)
        self.layout.addWidget(self.movieFrame)
    
    # Method to create Buttons in MoviePlayer
    def createButtons(self):
        #Bottom row of button
        self.playFrame = QtWidgets.QFrame(self)
        layoutPlay = QtWidgets.QHBoxLayout()
        self.playFrame.setLayout(layoutPlay)
        self.prevButton = QtWidgets.QPushButton("Prev", self.playFrame)
        self.prevButton.clicked.connect(self.showPrevious)
        self.nextButton = QtWidgets.QPushButton("Next", self.playFrame)
        self.nextButton.clicked.connect(self.showNext)
        framePerSeclabel = QtWidgets.QLabel(self.playFrame)
        framePerSeclabel.setText("Frame per Second: ")
        self.rwidget = QtWidgets.QSpinBox()
        self.rwidget.setRange(16, 30)
        self.rwidget.setSingleStep(8)
        self.rwidget.setValue(self.framesPerSec)
        self.rwidget.valueChanged.connect(self.updateFrameRate)
        self.playButton = QtWidgets.QPushButton("Play Movie", self.playFrame)
        self.playButton.clicked.connect(self.playMovie)
        self.deletePreButton = QtWidgets.QPushButton("Remove All Previous", self.playFrame)
        self.deletePreButton.clicked.connect(self.delAllBefore)
        self.deleteAfterButton = QtWidgets.QPushButton("Remove All After", self.playFrame)
        self.deleteAfterButton.clicked.connect(self.delAllAfter)
        self.QuicktimeButton = QtWidgets.QPushButton("Write QuickTime", self.playFrame)
        self.QuicktimeButton.clicked.connect(self.writeQuicktime)
        self.AVIButton = QtWidgets.QPushButton("Write AVI", self.playFrame)
        self.AVIButton.clicked.connect(self.writeAVI)
        #Add button in layout
        layoutPlay.addWidget(self.prevButton)
        layoutPlay.addWidget(self.nextButton)
        layoutPlay.addWidget(framePerSeclabel)
        layoutPlay.addWidget(self.rwidget)
        layoutPlay.addWidget(self.playButton)
        layoutPlay.addWidget(self.deletePreButton)
        layoutPlay.addWidget(self.deleteAfterButton)
        layoutPlay.addWidget(self.QuicktimeButton)
        layoutPlay.addWidget(self.AVIButton)
        self.layout.addWidget(self.playFrame)
        

class FrameSequencer(QtWidgets.QWidget):
    WIDTH = 650
    HEIGHT = 400
    
    def __init__(self, movie = Movie()):
        super().__init__()
        
        self.movie = Movie()
        self.block_edit = False
        self.frameList = Movie().frames
        
        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)
        self.setFixedWidth(self.WIDTH)
        self.setFixedHeight(self.HEIGHT)
        
        #Remember the window
        keepAround.append(self)
        #Show the window
        self.show()
        self.activateWindow()
        self.raise_()
        self.activateWindow()
        QtWidgets.QApplication.processEvents()
        
        self.createFileWindow()
        self.createButtons()
    
    def AddImgDir(self):
        path = pickAFolder()
        for afile in os.listdir(path):
            if afile.endswith(".jpg"):
                self.frameList.append(path + afile)
                if self.fileTable.rowCount() < len(self.frameList):
                    self.fileTable.setRowCount(2*self.fileTable.rowCount())
                newitem = QtWidgets.QTableWidgetItem(path + afile)
                self.fileTable.setItem(len(self.frameList) - 1, 0, newitem) 
    
    def AddImgFile(self):
        path = pickAFile()
        if path.endswith(".jpg"):
            self.frameList.append(path)
            if self.fileTable.rowCount() < len(self.frameList):
                    self.fileTable.setRowCount(2*self.fileTable.rowCount())
            newitem = QtWidgets.QTableWidgetItem(path)
            self.fileTable.setItem(len(self.frameList) - 1, 0, newitem)  
            
    def deleteSelectedItem(self):
        row = self.fileTable.currentRow()
        if row != -1 and row < len(self.frameList):
            self.fileTable.removeRow(row)
            del self.frameList[row]

    def clearItem(self):
        for item in self.frameList:
            self.fileTable.removeRow(0)
        del self.frameList[:]
        
    def play(self):
        self.movie.frames = self.frameList
        playMovie(self.movie)
        # self.clearItem()
        # self.frameList = self.movie.frames
        # self.setmydata()
    
    def moveUp(self):
        row = self.fileTable.currentRow()
        if row > 0:
            self.frameList[row], self.frameList[row - 1] = self.frameList[row - 1], self.frameList[row]
            item1 = QtWidgets.QTableWidgetItem(self.frameList[row])
            item2 = QtWidgets.QTableWidgetItem(self.frameList[row - 1] )
            self.fileTable.setItem(row, 0, item1)
            self.fileTable.setItem(row - 1, 0, item2)
            self.fileTable.selectRow(row - 1)
    
    def moveDown(self):
        row = self.fileTable.currentRow()
        if row < len(self.frameList) - 1:
            self.frameList[row], self.frameList[row + 1] = self.frameList[row + 1], self.frameList[row]
            item1 = QtWidgets.QTableWidgetItem(self.frameList[row])
            item2 = QtWidgets.QTableWidgetItem(self.frameList[row + 1] )
            self.fileTable.setItem(row, 0, item1)
            self.fileTable.setItem(row + 1, 0, item2)
            self.fileTable.selectRow(row + 1)
    
    # def updateData(self):
    #     for item in self.frameList:
    #         self.fileTable.removeRow(0)
        
    def setmydata(self):
        if self.fileTable.rowCount() < len(self.frameList):
            self.fileTable.setRowCount(len(self.frameList))
        for m, item in enumerate(self.frameList): 
            newitem = QtWidgets.QTableWidgetItem(item)
            self.fileTable.setItem(m, 0, newitem)
    
    # Method to create File window    
    def createFileWindow(self):
        self.FileFrame = QtWidgets.QFrame(self)
        layoutFile = QtWidgets.QVBoxLayout()
        self.FileFrame.setLayout(layoutFile)
        self.fileTable = QtWidgets.QTableWidget(30,2)
        self.fileTable.setSortingEnabled(False)
        self.setmydata()
        self.fileTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.fileTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.fileTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.fileTable.setShowGrid(False)
        self.fileTable.resizeColumnsToContents()
        self.fileTable.setColumnWidth(1, 0);
        self.fileTable.resizeRowsToContents()
        self.fileTable.horizontalHeader().setVisible(False)
        layoutFile.addWidget(self.fileTable)
        self.layout.addWidget(self.FileFrame)
        
    # Method to create Buttons in MoviePlayer
    def createButtons(self):
        self.buttonFrame = QtWidgets.QFrame(self)
        layoutButton = QtWidgets.QVBoxLayout()
        self.buttonFrame.setLayout(layoutButton)
        self.clearButton = QtWidgets.QPushButton("Clear image list", self.buttonFrame)
        self.clearButton.clicked.connect(self.clearItem)
        self.deleteButton = QtWidgets.QPushButton("Delete selected image from list", self.buttonFrame)
        self.deleteButton.clicked.connect(self.deleteSelectedItem)
        self.addDirButton = QtWidgets.QPushButton("Add images in directory to list", self.buttonFrame)
        self.addDirButton.clicked.connect(self.AddImgDir)
        self.addImgButton = QtWidgets.QPushButton("Add image to list", self.buttonFrame)
        self.addImgButton.clicked.connect(self.AddImgFile)
        self.playButton = QtWidgets.QPushButton("Play movie", self.buttonFrame)
        self.playButton.clicked.connect(self.play)
        self.moveUpButton = QtWidgets.QPushButton("Movie image up", self.buttonFrame)
        self.moveUpButton.clicked.connect(self.moveUp)
        self.moveDownButton = QtWidgets.QPushButton("Movie image down", self.buttonFrame)
        self.moveDownButton.clicked.connect(self.moveDown)
        self.ChangeFrameButton = QtWidgets.QPushButton("Change Frames Per Second", self.buttonFrame)
        #Add button in layout
        layoutButton.addWidget(self.clearButton)
        layoutButton.addWidget(self.deleteButton)
        layoutButton.addWidget(self.addDirButton)
        layoutButton.addWidget(self.addImgButton)
        layoutButton.addWidget(self.playButton)
        layoutButton.addWidget(self.moveUpButton)
        layoutButton.addWidget(self.moveDownButton)
        layoutButton.addWidget(self.ChangeFrameButton)
        self.layout.addWidget(self.buttonFrame)
