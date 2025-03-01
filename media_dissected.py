# File_Deleted's heavily trimmed version of media.py - for personal use; lacks any proper licenses or any of dat legal stuff

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

# a LOOOOOOOOT of stuff was cut out here

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

# LOT of stuff cut out here

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

# some stuff cut out here

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

# LOOOOOOOOT of stuff cut out here