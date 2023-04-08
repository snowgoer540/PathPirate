'''
pathpirate is a script that provides automated configuration changes to
Tormach's PathPilot.

Copyright (C) 2023  Gregory D Carl

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
'''

import sys
if sys.version_info[0] > 2:
    import tkinter as tk
    import tkinter.filedialog as tkFileDialog
    import tkinter.simpledialog as tkSimpleDialog
    import tkinter.messagebox as tkMessageBox
else:
    import Tkinter as tk
    import tkFileDialog
    import tkSimpleDialog
    import tkMessageBox
from subprocess import Popen, check_output, STDOUT
from shutil import copy
import socket
import os
import json
import difflib
import threading

class PathPirate:

    def __init__(self):
        # set up the main window
        self.main = tk.Tk()
        self.main.title("PathPirate Configurator v1.0 for Tormach's PathPilot")
        winWidth = 1000
        winHeight = 700
        screenWidth = self.main.winfo_screenwidth()
        screenHeight = self.main.winfo_screenheight()
        xCoord = int((screenWidth/2) - (winWidth/2))
        yCoord = int((screenHeight/2) - (winHeight/2))
        self.main.geometry('{}x{}+{}+{}'.format(winWidth, winHeight, xCoord, yCoord))
        self.main.attributes('-zoomed', True)
        # self.main.attributes('-topmost',True) This doesnt work to keep this window on top of PathPilot. This is just here to remind me of that.
        self.main.protocol('WM_DELETE_WINDOW', self.exitPathPirate)

        # add frames to window
        self.buttonFrame = tk.Frame(self.main)
        self.buttonFrame.pack(anchor=tk.NW, fill=tk.X)
        self.versionFrame = tk.Frame(self.main)
        self.versionFrame.pack(anchor=tk.NW, fill=tk.X)
        self.consoleFrame = tk.Frame(self.main)
        self.consoleFrame.pack(anchor=tk.NW, fill=tk.BOTH, expand=True)

        # set up buttons
        self.b0 = tk.Button(self.buttonFrame, text='GET DIRECTORY\nTO COMPARE', command=self.getDirectory, height=2, padx=5)
        self.b0.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.b0['state'] = 'disabled'
        self.b1 = tk.Button(self.buttonFrame, text='COMPARE\nINI', command=lambda:self.compare('INI'), height=2, padx=5)
        self.b1.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.b1['state'] = 'disabled'
        self.b2 = tk.Button(self.buttonFrame, text='COMPARE\nHAL', command=lambda:self.compare('HAL'), height=2, padx=5)
        self.b2.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.b2['state'] = 'disabled'
        self.b3 = tk.Button(self.buttonFrame, text='ADD\nHALSHOW', command=self.addHalshow, height=2, padx=5)
        self.b3.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.b3['state'] = 'disabled'
        self.b4 = tk.Button(self.buttonFrame, text='MAX VEL\nTO RAPID', command=self.convertSlider, height=2, padx=5)
        self.b4.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.b4['state'] = 'disabled'
        self.b5 = tk.Button(self.buttonFrame, text='ADD\nENCODER', command=self.addEncoder, height=2, padx=5)
        self.b5.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.b6 = tk.Button(self.buttonFrame, text='ADD\nSERVOS', command=self.addServos, height=2, padx=5)
        self.b6.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.b7 = tk.Button(self.buttonFrame, text='REVERT\nALL', command=self.revertAll, height=2, padx=5)
        self.b7.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.b8 = tk.Button(self.buttonFrame, text='EXIT', command=self.exitPathPirate, height=2, padx=5)
        self.b8.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # set up output text boxes
        self.machineInfo = tk.Text(self.versionFrame, padx=5, height=1, bg='black', fg='yellow', highlightthickness=0, bd=0)
        self.machineInfo.pack(fill=tk.BOTH, expand=True)
        self.currentVersionInfo = tk.Text(self.versionFrame, padx=5, height=1, bg='black', fg='yellow', highlightthickness=0, bd=0)
        self.currentVersionInfo.pack(fill=tk.BOTH, expand=True)
        self.previousVersionInfo = tk.Text(self.versionFrame, padx=5, height=1, bg='black', fg='orange', highlightthickness=0, bd=0)
        self.previousVersionInfo.pack(fill=tk.BOTH, expand=True)
        self.console = tk.Text(self.consoleFrame, padx=5, bg='black', fg='orange', highlightthickness=0)
        self.console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.console.tag_configure('yellow', foreground='yellow')
        self.console.tag_configure('green', foreground='green')
        self.console.tag_configure('orange', foreground='orange')
        self.console.tag_configure('red', foreground='red')
        self.console.tag_configure('cyan', foreground='cyan')
        self.console.tag_configure('white', foreground='white')
        self.console.tag_configure('pink', foreground='pink')
        self.previousVersionInfo.tag_configure('cyan', foreground='cyan')
        self.previousVersionInfo.tag_configure('red', foreground='red')
        self.machineInfo.tag_configure('red', foreground='red')

        # add scroll bar to console text box
        self.scrollBar = tk.Scrollbar(self.consoleFrame, command=self.console.yview, width=15)
        self.scrollBar.pack(side=tk.LEFT, fill=tk.Y)
        self.console['yscrollcommand']=self.scrollBar.set

        # prevent typing in all text boxes
        self.machineInfo.bind('<Key>', lambda e: 'break')
        self.currentVersionInfo.bind('<Key>', lambda e: 'break')
        self.previousVersionInfo.bind('<Key>', lambda e: 'break')
        self.console.bind('<Key>', lambda e: 'break')

        # prevent mouse wheel scrolling in Info text boxes (linux separates scroll up and scroll down)
        self.machineInfo.bind('<Button-4>', lambda e: 'break')
        self.machineInfo.bind('<Button-5>', lambda e: 'break')
        self.currentVersionInfo.bind('<Button-4>', lambda e: 'break')
        self.currentVersionInfo.bind('<Button-5>', lambda e: 'break')
        self.previousVersionInfo.bind('<Button-4>', lambda e: 'break')
        self.previousVersionInfo.bind('<Button-5>', lambda e: 'break')

        # allow right click to cut, and copy
        self.console.bind('<Button-3>', self.rightClick)

        # call a filedialog with bad option intentionally so there is an instance to
        # be able to set the options to hide hidden directories by default
        # discussed here: https://code.activestate.com/lists/python-tkinter-discuss/3723
        try:
            try:
                self.main.tk.call('tk_getOpenFile', '-foobarbaz')
            except tk.TclError:
                pass
            self.main.tk.call('set', '::tk::dialog::file::showHiddenBtn', '1')
            self.main.tk.call('set', '::tk::dialog::file::showHiddenVar', '0')
        except:
            pass

        # set up necessary paths
        self.pathPirateDir = os.path.realpath(os.path.dirname(__file__))
        self.newBin = os.path.join(self.pathPirateDir, 'files/5i25_t2_7i85s_dpll.bit')
        self.rapidPath = os.path.join(self.pathPirateDir, 'files/MAXVEL_100.jpg')
        self.halshowPath = os.path.join(self.pathPirateDir, 'files/halshow.tcl')
        self.cbuttonPath = os.path.join(self.pathPirateDir, 'files/cbutton.tcl')
        self.newTooltips = os.path.join(self.pathPirateDir, 'files/pathpirate_tooltips.json')
        self.home = os.getenv('HOME')
        self.tmc = os.path.join(self.home, 'tmc')
        self.sourcePath = os.path.join(self.tmc, 'tcl/bin')
        self.scriptFile = os.path.join(self.tmc, 'bin/halshow')
        self.currentIni = os.path.join(self.tmc, 'configs/tormach_mill/tormach_mill_base.ini')
        self.currentHal = os.path.join(self.tmc, 'configs/tormach_mill/tormach_mill_mesa.hal')
        self.hal1 = os.path.join(self.tmc, 'configs/common/operator_console_controls_3axis.hal')
        self.hal2 = os.path.join(self.tmc, 'configs/common/operator_console_controls_4axis.hal')
        self.uiCommon = os.path.join(self.tmc, 'python/ui_common.py')
        self.tooltips = os.path.join(self.tmc, 'python/res/tooltips.json')
        self.velPath = os.path.join(self.tmc, 'python/images/MAXVEL_100.jpg')
        self.mesaFlash = os.path.join(self.tmc, 'bin/mesaflash')
        self.mesaPath = os.path.join(self.tmc, 'mesa')
        self.newMesaFirmware = os.path.join(self.mesaPath, '5i25_t2_7i85s_dpll.bit')
        self.oldMesaFirmware = os.path.join(self.mesaPath, 'tormach_mill3.bit')

        # set restart flag false
        self.restartRequired = False
        self.powerCycleRequired = False

        # get current version and machine info
        self.getVersion()

        # call the main window loop
        self.main.mainloop()

    # Allows a user to right click to cut or copy in the console text box
    def rightClick(self, event=None):
        menu = tk.Menu(self.main, tearoff=0)
        menu.add_command(label='Cut', command=lambda: self.console.event_generate('<<Cut>>'))
        menu.add_command(label='Copy', command=lambda: self.console.event_generate('<<Copy>>'))
        menu.tk_popup(event.x_root, event.y_root)

    # Shows the directory chooser for picking previous and current directories
    def getDirectory(self, event=None):
        self.b1['state'] = 'disabled'
        self.b2['state'] = 'disabled'
        self.old = tkFileDialog.askdirectory(
                initialdir=self.home,
                mustexist=True,
                title='Select Directory of Version to Compare (v2.X.X)')
        if not self.old:
            self.previousVersionInfo.delete(1.0, tk.END)
            self.previousVersionInfo.insert(tk.END, 'Directory selection is required', 'red')
            return
        test = self.old.split('/')
        if not 'v2' in test[len(test)-1]:
            self.previousVersionInfo.delete(1.0, tk.END)
            self.previousVersionInfo.insert(tk.END, 'Incorrect directory choice. Base directory must be chosen (v2.X.X)', 'red')
            return
        for self.previousVer in test:
            if 'v2' in self.previousVer:
                self.previousVersionInfo.delete(1.0, tk.END)
                self.previousVersionInfo.insert(tk.END, '{} will be compared against {}'.format(self.currentVer, self.previousVer))
            if self.previousVer == self.currentVer:
                self.previousVersionInfo.insert(tk.END, '; backup files will be used if present')
        self.b1['state'] = 'normal'
        self.b2['state'] = 'normal'

    # Compares between chosen configuration files
    def compare(self, extension, event=None):
        oldMod = False
        missing = False
        self.console.insert(tk.END, '\n------------------\nCOMPARING {} FILE\n------------------\n'.format(extension.upper()), 'yellow')
        if extension == 'HAL':
            newFile = self.currentHal
            if os.path.exists(os.path.join(self.old, 'configs/tormach_mill/tormach_mill_mesa.hal.bak')):
                oldMod = True
                oldFile = os.path.join(self.old, 'configs/tormach_mill/tormach_mill_mesa.hal.bak')
            else:
                oldFile = os.path.join(self.old, 'configs/tormach_mill/tormach_mill_mesa.hal')
        if extension == 'INI':
            newFile = self.currentIni
            if os.path.exists(os.path.join(self.old, 'configs/tormach_mill/tormach_mill_base.ini.bak')):
                oldMod = True
                oldFile = os.path.join(self.old, 'configs/tormach_mill/tormach_mill_base.ini.bak')
            else:
                oldFile = os.path.join(self.old, 'configs/tormach_mill/tormach_mill_base.ini')
        if oldMod:
            self.console.insert(tk.END, 'PREVIOUS ({}) - MODIFIED {} FILE DETECTED\n'.format(self.previousVer, extension))
            self.console.insert(tk.END, 'Using backup {} file to compare against current version\n\n'.format(extension))
            self.console.see(tk.END)
        for file in [oldFile, newFile]:
            if not os.path.exists(file):
                self.console.insert(tk.END, 'The following required file is missing: ', 'red')
                self.console.insert(tk.END, '{}\n'.format(file), 'pink')
                missing = True
        if missing:
            self.console.insert(tk.END, '\nAborting...\n', 'red')
            self.console.see(tk.END)
            return
        with open(oldFile, 'r') as previousFile, open(newFile, 'r') as currentFile:
            previousFile = previousFile.read()
            currentFile = currentFile.read()
        if 'PathPirate' in currentFile:
            self.console.insert(tk.END, 'CURRENT VERISON ({}) - MODIFIED {} FILE DETECTED\n\n'.format(self.currentVer, extension))
            self.console.see(tk.END)
        if previousFile == currentFile:
            self.console.insert(tk.END, 'No changes present (the files are the same)\n')
            self.console.see(tk.END)
            return
        self.console.insert(tk.END, 'The following changes exist between {} files:\n'.format(extension))
        previousFile = previousFile.strip().splitlines()
        currentFile = currentFile.strip().splitlines()
        # credit for help on this: https://stackoverflow.com/a/19128062
        for line in difflib.unified_diff(previousFile, currentFile, lineterm='', n=0):
            if line.startswith('---') or line.startswith('+++'):
                continue
            elif line.startswith('@@'):
                self.console.insert(tk.END, '\n')
            else:
                if '+' in line:
                    self.console.insert(tk.END, '{}: {}\n'.format(self.currentVer, line[1:]), 'green')
                elif '-' in line:
                    self.console.insert(tk.END, '{}: {}\n'.format(self.previousVer, line[1:]), 'red')
        self.console.see(tk.END)

    # Adds halshow back to PathPilot so it can be called with 'ADMIN HALSHOW' via MDI
    def addHalshow(self, event=None):
        internet = self.internetStatus()
        self.console.insert(tk.END, '\n--------------\nADDING HALSHOW\n--------------\n', 'yellow')
        # check if ~/tmc/tcl/bin exists (it shouldn't) and if it doesnt, create it
        if not os.path.lexists(self.sourcePath):
            os.mkdir(self.sourcePath)
        # attempt to grab latest halshow.tcl and cbutton.tcl from the linuxCNC master repository
        if internet:
            self.console.insert(tk.END, 'Internet connection found\n')
            self.console.insert(tk.END, 'Attempting to download latest files from LinuxCNC master github repository\n')
            self.console.insert(tk.END, '(Any previous versions will be automatically overwritten without warning)\n')
            try:
                # check for wget
                test = check_output(['wget', '--version'], stderr=STDOUT)
                # attempt to download files from github
                output = check_output('wget --quiet -O {}/halshow.tcl https://raw.github.com/LinuxCNC/linuxcnc/master/tcl/bin/halshow.tcl'.format(self.sourcePath), shell=True, stderr=STDOUT)
                output1 = check_output('wget --quiet -O {}/cbutton.tcl https://raw.github.com/LinuxCNC/linuxcnc/master/tcl/bin/cbutton.tcl'.format(self.sourcePath), shell=True, stderr=STDOUT)
            except Exception as e:
                self.console.insert(tk.END, 'The following error occurred while attempting to download Halshow files from LinuxCN master github repository:\n\n{}\n\n'.format(e), 'red')
                self.console.insert(tk.END, 'There may be an internet issue, or wget may not be installed\n\n', 'red')
                self.console.insert(tk.END, 'wget can be installed by entering "sudo apt-get install wget" in a terminal window\n\n', 'cyan')
                self.console.insert(tk.END, 'Attempting to copy local files instead...\n\n')
                success = self.addHalshowCopy()
                if not success:
                    return
        # no internet - just copy the local version
        else:
            self.console.insert(tk.END, 'No internet connection found\n')
            success = self.addHalshowCopy()
            if not success:
                return
        # overwrite the current halshow launch script as the source path will never exist on an end user's PC, no need to back this up
        if os.path.exists(self.scriptFile):
            tempFile = '{}.bak'.format(self.scriptFile)
            if not os.path.exists(tempFile):
                copy(self.scriptFile, tempFile)
            with open(self.scriptFile,'w') as script:
                script.write('#!/usr/bin/tclsh8.6\n')
                script.write('source ~/tmc/tcl/bin/halshow.tcl')
        else:
            self.console.insert(tk.END, 'The following required file is missing: ', 'red')
            self.console.insert(tk.END, '{}\n'.format(self.scriptFile), 'pink')
            self.console.see(tk.END)
            return
        self.console.insert(tk.END, '\nhalshow.tcl and cbutton.tcl were successfully placed in: ')
        self.console.insert(tk.END, '{}\n'.format(self.sourcePath), 'pink')
        self.console.insert(tk.END, 'The following script was successfully updated: ')
        self.console.insert(tk.END, '{}\n\n'.format(self.scriptFile), 'pink')
        self.console.insert(tk.END, 'HALSHOW can be launched via the following MDI command: ')
        self.console.insert(tk.END, 'ADMIN HALSHOW\n', 'cyan')
        self.console.see(tk.END)

    # Copy local hlashow files if no internet, or download from internet fails
    def addHalshowCopy(self):
            self.console.insert(tk.END, 'Copying local files\n')
            missing = False
            for file in [self.halshowPath, self.cbuttonPath]:
                if not os.path.exists(file):
                    self.console.insert(tk.END, 'The following required file is missing: ', 'red')
                    self.console.insert(tk.END, '{}\n'.format(file), 'pink')
                    missing = True
            if missing:
                self.console.insert(tk.END, '\nAborting...\n', 'red')
                self.console.see(tk.END)
                return False
            for file in [self.halshowPath, self.cbuttonPath]:
                copy(file, self.sourcePath)
            self.console.see(tk.END)
            return True

    # Checks to see if the computer has an active internet connection
    def internetStatus(self):
        try:
            s = socket.create_connection(('www.google.com', 80))
            if s is not None:
                s.close
            return True
        except:
            return False

    # Converts the MAX VEL slider to RAPID since having a MAX VEL slider makes no sense
    def convertSlider(self, event=None):
        self.console.insert(tk.END, '\n---------------------------------------\nCONVERTING SLIDER FROM MAX VEL TO RAPID\n---------------------------------------\n', 'yellow')
        missing = False
        change = False
        for file in [self.uiCommon, self.hal1, self.hal2, self.velPath, self.rapidPath, self.tooltips]:
            if not os.path.exists(file):
                self.console.insert(tk.END, 'The following required file is missing: ', 'red')
                self.console.insert(tk.END, '{}\n'.format(file), 'pink')
                missing = True
        if missing:
            self.console.insert(tk.END, '\nAborting...\n', 'red')
            self.console.see(tk.END)
            return
        for modFile in [self.uiCommon, self.hal1, self.hal2, self.tooltips]:
            tempFile = '{}.bak'.format(modFile)
            if not os.path.exists(tempFile):
                copy(modFile, tempFile)
                if modFile == self.tooltips:
                    copy(self.newTooltips, self.tooltips)
                    self.console.insert(tk.END, 'The following file has been successfully modified: ')
                    self.console.insert(tk.END, '{}\n'.format(modFile), 'pink')
                    continue
            with open(modFile, 'r+') as file:
                text = file.read()
                if 'PathPirate' in text:
                    self.console.insert(tk.END, 'The necessary modifications are already present in the following file: ')
                    self.console.insert(tk.END, '{}\n'.format(modFile), 'pink')
                    continue
                if modFile == self.uiCommon:
                    text = text.replace('lcnc_apply_function=lambda value: self.command.maxvel(value * self.maxvel_lin / 100, value * self.maxvel_ang / 100)),', \
                    'lcnc_apply_function=lambda value: self.command.rapidrate(value / 100)), #Changed by PathPirate')
                else:
                    text = text.replace('setp tormach-console.0.rapid-override-scale 960', \
                    '#setp tormach-console.0.rapid-override-scale 960 #Changed by PathPirate')
                file.seek(0)
                file.truncate()
                file.write(text)
                self.console.insert(tk.END, 'The following file has been successfully modified: ')
                self.console.insert(tk.END, '{}\n'.format(modFile), 'pink')
                change = True
        with open (self.velPath, 'rb') as originalImage:
            original = originalImage.read()
        with open (self.rapidPath, 'rb') as modImage:
            modified = modImage.read()
        if original == modified:
            self.console.insert(tk.END, 'Image file was previously replaced\n\n')
        else:
            tempFile = '{}.bak'.format(self.velPath)
            if not os.path.exists(tempFile):
                copy(self.velPath, tempFile)
            copy(self.rapidPath, self.velPath)
            self.console.insert(tk.END, 'Image file copied to: ')
            self.console.insert(tk.END, '{}\n'.format(self.velPath), 'pink')
            change = True
        if change:
            self.restartRequired = True
            self.console.insert(tk.END, '\nA RESTART IS REQUIRED FOR CHANGES TO TAKE EFFECT!\n', 'white')
        self.console.see(tk.END)

    # Added to center the tkSimpleDialog.askinteger box. Help from: https://stackoverflow.com/a/69904742 (and the tkSimpleDialog source code)
    def askinteger(self, title, prompt, **kwargs):
        def change_geometry():
            w = kwargs['parent'].winfo_children()[-1]
            if isinstance(w, tkSimpleDialog.Dialog):
                w.withdraw()
                w.transient(kwargs['parent'])
                minwidth = w.winfo_reqwidth()
                minheight = w.winfo_reqheight()
                maxwidth = w.winfo_vrootwidth()
                maxheight = w.winfo_vrootheight()
                x = kwargs['parent'].winfo_rootx() + (kwargs['parent'].winfo_width() - minwidth) // 2
                y = kwargs['parent'].winfo_rooty() + (kwargs['parent'].winfo_height() - minheight) // 2
                vrootx = w.winfo_vrootx()
                vrooty = w.winfo_vrooty()
                x = min(x, vrootx + maxwidth - minwidth)
                x = max(x, vrootx)
                y = min(y, vrooty + maxheight - minheight)
                y = max(y, vrooty)
                w.geometry('+{}+{}'.format(x, y))
                w.deiconify()
        if 'parent' in kwargs:
            kwargs['parent'].after(10, change_geometry)
        return tkSimpleDialog.askinteger(title, prompt, **kwargs)

    # Adds an encoder to an 1100-3 machine (that is using a Mesa 7i85s card)
    def addEncoder(self, event=None):
        change = False
        missing = False
        mesa = False
        self.console.insert(tk.END, '\n--------------\nADDING ENCODER\n--------------\n', 'yellow')
        # initialvalue is set to -1440 as a perk of being the author :)
        scale = self.askinteger(title='ENCODER SCALE', prompt='Enter the encoder scale:', initialvalue='-1440', parent=self.main)
        if scale is None:
            self.console.insert(tk.END, 'Encoder scale is required\n', 'red')
            self.console.see(tk.END)
            return
        for file in [self.currentHal, self.currentIni, self.newBin]:
            if not os.path.exists(file):
                self.console.insert(tk.END, 'The following required file is missing: ', 'red')
                self.console.insert(tk.END, '{}\n'.format(file), 'pink')
                missing = True
        if missing:
            self.console.insert(tk.END, '\nAborting...\n', 'red')
            self.console.see(tk.END)
            return
        with open(self.currentHal, 'r+') as file:
            text = file.read()
            if '#The following encoder lines were added by PathPirate' in text:
                if 'setp hm2_5i25.0.encoder.00.scale {}'.format(scale) in text:
                    self.console.insert(tk.END, 'The necessary modifications are already present in the following file: ')
                    self.console.insert(tk.END, '{}\n'.format(self.currentHal), 'pink')
                else:
                    for line in text.splitlines():
                        if 'setp hm2_5i25.0.encoder.00.scale' in line:
                            text = text.replace(line, 'setp hm2_5i25.0.encoder.00.scale {}'.format(scale))
                            file.seek(0)
                            file.truncate()
                            file.write(text)
                            change = True
                            self.console.insert(tk.END, 'The following file has been modified to change the encoder scale: '.format(self.currentHal))
                            self.console.insert(tk.END, '{}\n'.format(self.currentHal), 'pink')
            else:
                tempFile = '{}.bak'.format(self.currentHal)
                if not os.path.exists(tempFile):
                    copy(self.currentHal, tempFile)
                text += ('\n#####################################################################\n')
                text += ('#The following encoder lines were added by PathPirate\n\n')
                text += ('unlinkp motion.spindle-speed-in\n')
                text += ('net spindle-position hm2_5i25.0.encoder.00.position => motion.spindle-revs\n')
                text += ('net spindle-velocity hm2_5i25.0.encoder.00.velocity => motion.spindle-speed-in\n')
                text += ('net spindle-index-enable hm2_5i25.0.encoder.00.index-enable <=> motion.spindle-index-enable\n')
                text += ('setp hm2_5i25.0.encoder.00.scale {}'.format(scale))
                file.seek(0)
                file.truncate()
                file.write(text)
                change = True
                self.console.insert(tk.END, 'The following file has been successfully modified: ')
                self.console.insert(tk.END, '{}\n'.format(self.currentHal), 'pink')
        tempFile = '{}.bak'.format(self.currentIni)
        if not os.path.exists(tempFile):
            copy(self.currentIni, tempFile)
        with open(self.currentIni, 'r+') as file:
            text = file.read()
            if not '#Encoder added by PathPirate' in text:
                text = text.replace('DRIVER_PARAMS="config= num_encoders=2 num_pwmgens=1 num_3pwmgens=0 num_stepgens=5 "', \
                'DRIVER_PARAMS="config= num_encoders=4 num_pwmgens=1 num_3pwmgens=0 num_stepgens=5 "')
                text = text.replace('BITFILE0=mesa/tormach_mill3.bit', \
                'BITFILE0=mesa/5i25_t2_7i85s_dpll.bit')
                text += ('#Encoder added by PathPirate')
                file.seek(0)
                file.truncate()
                file.write(text)
                change = True
                self.console.insert(tk.END, 'The following file has been successfully modified: ')
                self.console.insert(tk.END, '{}\n'.format(self.currentIni), 'pink')
            else:
                self.console.insert(tk.END, 'The necessary modifications are already present in the following file: ')
                self.console.insert(tk.END, '{}\n'.format(self.currentIni), 'pink')
        if not os.path.exists(os.path.join(self.mesaPath, '5i25_t2_7i85s_dpll.bit')):
            copy(self.newBin, self.mesaPath)
            change = True
            mesa = True
            self.console.insert(tk.END, '5i25_t2_7i85s_dpll.bit has been copied to: ')
            self.console.insert(tk.END, '{}\n'.format(self.mesaPath), 'pink')
        else:
            self.console.insert(tk.END, '5i25_t2_7i85s_dpll.bit already exists in :')
            self.console.insert(tk.END, '{}\n'.format(self.mesaPath), 'pink')
        if change:
            self.restartRequired = True
            self.console.insert(tk.END, '\nA RESTART IS REQUIRED FOR CHANGES TO TAKE EFFECT!\n', 'white')
        self.console.see(tk.END)
        if mesa:
            self.verifyThread(self.newMesaFirmware)

    # Adds ClearPath Servos to an 1100-3 machine (that is using a Mesa 7i85s card)
    def addServos(self, event=None):
        self.console.insert(tk.END, '\n-----------------------\nADDING CLEARPATH SERVOS\n-----------------------\n', 'yellow')
        hostmotSection = False
        trajSection = False
        xySection = False
        zSection = False
        putSmoothing = False
        missing = False
        change = False
        mesa = False
        encoder = True
        for file in [self.currentHal, self.currentIni, self.newBin, self.mesaPath]:
            if not os.path.exists(file):
                self.console.insert(tk.END, 'The following required file is missing: ', 'red')
                self.console.insert(tk.END, '{}\n'.format(file), 'pink')
                missing = True
        if missing:
            self.console.insert(tk.END, '\nAborting...\n', 'red')
            self.console.see(tk.END)
            return
        tempFile = '{}.bak'.format(self.currentIni)
        if not os.path.exists(tempFile):
            copy(self.currentIni, tempFile)
        with open(self.currentIni, 'r') as file:
            text=file.read()
        if '#Encoder added by PathPirate' in text:
            encoder = True
        if not '#Servos added by PathPirate' in text:
            with open(tempFile, 'r') as inFile:
                with open (self.currentIni, 'w') as outFile:
                    for line in inFile:
                        if line.startswith('[HOSTMOT2]'):
                            hostmotSection = True
                        elif line.startswith('[TRAJ]'):
                            trajSection = True
                        elif line.startswith('[AXIS_0]') or line.startswith('[AXIS_1]'):
                            xySection = True
                            putSmoothing = True
                        elif line.startswith('[AXIS_2]'):
                            zSection = True
                            putSmoothing = True
                        elif hostmotSection:
                            line = line.replace('DRIVER_PARAMS="config= num_encoders=2 num_pwmgens=1 num_3pwmgens=0 num_stepgens=5 "', \
                            'DRIVER_PARAMS="config= num_encoders=4 num_pwmgens=1 num_3pwmgens=0 num_stepgens=5 "')
                            line = line.replace('BITFILE0=mesa/tormach_mill3.bit', \
                            'BITFILE0=mesa/5i25_t2_7i85s_dpll.bit')
                            if line.startswith('['):
                                hostmotSection = False
                        elif trajSection:
                            line = line.replace('MAX_VELOCITY = 3.0', 'MAX_VELOCITY = 8.043')
                            if line.startswith('['):
                                trajSection = False
                        elif xySection:
                            line = line.replace('# 110 in/min', '# 300 in/min')
                            line = line.replace('MAX_VELOCITY = 1.833', 'MAX_VELOCITY = 5.00')
                            line = line.replace('MAX_ACCELERATION = 15.0', 'MAX_ACCELERATION = 30.0')
                            line = line.replace('STEPGEN_MAX_VEL = 2.2', 'STEPGEN_MAX_VEL = 6.0')
                            line = line.replace('STEPGEN_MAXACCEL = 37.5', 'STEPGEN_MAXACCEL = 75')
                            line = line.replace('MAX_JOG_VELOCITY_UPS = 1.833', 'MAX_JOG_VELOCITY_UPS = 3.333')
                            line = line.replace('# nanoseconds', '#nanosecs .. for ClearPath')
                            line = line.replace('DIRSETUP = 10000', 'DIRSETUP = 2000')
                            line = line.replace('DIRHOLD = 10000', 'DIRHOLD = 2000')
                            line = line.replace('STEPLEN = 8000', 'STEPLEN = 2000')
                            line = line.replace('STEPSPACE  = 5000', 'STEPSPACE  = 2000')
                            line = line.replace('SCALE = 10000.0', 'SCALE = 16000.0')
                            if 'HOME_SEQUENCE' in line and putSmoothing:
                                    line += '\nSMOOTHING_WINDOW = 0.0056\n'
                                    putSmoothing = False
                            if line.startswith('['):
                                xySection = False
                            elif zSection:
                                line = line.replace('# 90 in/min', '# 230 in/min')
                                line = line.replace('MAX_VELOCITY = 1.500', 'MAX_VELOCITY = 3.8333')
                                line = line.replace('MAX_ACCELERATION = 15.0', 'MAX_ACCELERATION = 19.167')
                                line = line.replace('STEPGEN_MAX_VEL = 1.8', 'STEPGEN_MAX_VEL = 4.600')
                                line = line.replace('STEPGEN_MAXACCEL = 37.5', 'STEPGEN_MAXACCEL = 47.9175')
                                line = line.replace('MAX_JOG_VELOCITY_UPS = 1.5', 'MAX_JOG_VELOCITY_UPS = 3.0')
                                line = line.replace('# nanoseconds', '#nanosecs .. for ClearPath')
                                line = line.replace('DIRSETUP = 10000', 'DIRSETUP = 2000')
                                line = line.replace('DIRHOLD = 10000', 'DIRHOLD = 2000')
                                line = line.replace('STEPLEN = 8000', 'STEPLEN = 2000')
                                line = line.replace('STEPSPACE  = 5000', 'STEPSPACE  = 2000')
                                line = line.replace('SCALE = -10000.0', 'SCALE = -16000.0')
                                if 'HOME_SEQUENCE' in line and putSmoothing:
                                        line += '\nSMOOTHING_WINDOW = 0.0056\n'
                                        putSmoothing = False
                                if line.startswith('['):
                                    zSection = False
                        outFile.write(line)
                    if encoder:
                        outFile.write('#Encoder added by PathPirate\n')
                    outFile.write('#Servos added by PathPirate\n')
                change = True
                self.console.insert(tk.END, 'The following file has been successfully modified: ')
                self.console.insert(tk.END, '{}\n'.format(self.currentIni), 'pink')
        else:
            self.console.insert(tk.END, 'The necessary modifications are already present in the following file: ')
            self.console.insert(tk.END, '{}\n'.format(self.currentIni), 'pink')
        tempFile = '{}.bak'.format(self.currentHal)
        if not os.path.exists(tempFile):
            copy(self.currentHal, tempFile)
        with open(self.currentHal, 'r+') as file:
            text = file.read()
            if not '#The following ClearPath servo lines were added by PathPirate' in text:
                text = text.replace('loadrt not names=prog-not-idle,axis3-not-homing,x-homing-not2', \
                'loadrt not names=prog-not-idle,axis3-not-homing,x-homing-not2,x-fault-not,y-fault-not #Changed by PathPirate')
                text += ('\n#####################################################################\n')
                text += ('#The following ClearPath servo lines were added by PathPirate\n\n')
                text += ('addf x-fault-not servo-thread\n')
                text += ('addf y-fault-not servo-thread\n')
                text += ('net x_fault_not hm2_[HOSTMOT2](BOARD).0.encoder.02.input-a x-fault-not.in\n')
                text += ('net x_fault x-fault-not.out axis.0.amp-fault-in\n')
                text += ('net y_fault_not hm2_[HOSTMOT2](BOARD).0.encoder.02.input-b y-fault-not.in\n')
                text += ('net y_fault y-fault-not.out axis.1.amp-fault-in\n')
                text += ('net z_fault hm2_[HOSTMOT2](BOARD).0.encoder.02.input-index axis.2.amp-fault-in\n')
                file.seek(0)
                file.truncate()
                file.write(text)
                change = True
                self.console.insert(tk.END, 'The following file has been successfully modified: ')
                self.console.insert(tk.END, '{}\n'.format(self.currentHal), 'pink')
            else:
                self.console.insert(tk.END, 'The necessary modifications are already present in the following file: ')
                self.console.insert(tk.END, '{}\n'.format(self.currentHal), 'pink')
        if not os.path.exists(os.path.join(self.mesaPath, '5i25_t2_7i85s_dpll.bit')):
            copy(self.newBin, self.mesaPath)
            change = True
            mesa = True
            self.console.insert(tk.END, '5i25_t2_7i85s_dpll.bit has been copied to: ')
            self.console.insert(tk.END, '{}\n'.format(self.mesaPath), 'pink')
        else:
            self.console.insert(tk.END, '5i25_t2_7i85s_dpll.bit already exists in :')
            self.console.insert(tk.END, '{}\n'.format(self.mesaPath), 'pink')
        if change:
            self.restartRequired = True
            self.console.insert(tk.END, '\nA RESTART IS REQUIRED FOR CHANGES TO TAKE EFFECT!\n', 'white')
        self.console.see(tk.END)
        if mesa:
            self.verifyThread(self.newMesaFirmware)

    # Revert any changes PathPirate may have made by restoring backup files/deleting new files
    def revertAll(self, event=None):
        self.console.insert(tk.END, '\n---------------------\nREVERTING ALL CHANGES\n---------------------\n', 'yellow')
        change = False
        halshow = False
        mesa = False
        halshowPath = os.path.join(self.sourcePath, 'halshow.tcl')
        cbuttonPath = os.path.join(self.sourcePath, 'cbutton.tcl')
        try:
            for file in [self.uiCommon, self.hal1, self.hal2, self.velPath, self.currentHal, self.currentIni, self.tooltips]:
                tempFile = '{}.bak'.format(file)
                if os.path.exists(tempFile):
                    change = True
                    copy(tempFile, file)
                    os.remove(tempFile)
            if os.path.exists(self.newMesaFirmware):
                change = True
                mesa = True
                os.remove(self.newMesaFirmware)
            for file in [halshowPath, cbuttonPath]:
                if os.path.exists(file):
                    halshow = True
                    os.remove(file)
            tempFile = '{}.bak'.format(self.scriptFile)
            if os.path.exists(tempFile):
                halshow = True
                copy(tempFile, self.scriptFile)
                os.remove(tempFile)
            if os.path.exists(self.sourcePath):
                halshow = True
                os.rmdir(self.sourcePath)
            if halshow and not change:
                self.console.insert(tk.END, 'Halshow changes have been removed\n')
            elif change:
                self.restartRequired = True
                self.console.insert(tk.END, 'All changes to {} have been undone\n\n'.format(self.currentVer))
                self.console.insert(tk.END, 'A RESTART IS REQUIRED FOR CHANGES TO TAKE EFFECT!\n', 'white')
            else:
                self.console.insert(tk.END, 'There were no configuration changes in {} to revert\n'.format(self.currentVer))
            self.console.see(tk.END)
            if mesa:
                self.verifyThread(self.oldMesaFirmware)
        except Exception as e:
            self.console.insert(tk.END, 'The following system error has occured:\n\n{}\n'.format(e), 'red')
            self.console.see(tk.END)
            return

    # Get the latest version number and machine model
    def getVersion(self, event=None):
        machineFile = os.path.join(self.home, 'machine.json')
        if os.path.exists(machineFile):
            with open(machineFile, 'r') as jsonFile:
                machineData = json.load(jsonFile)
            machine = machineData['mdl']
            if machine != '1100-3':
                self.b5.pack_forget()
                self.b6.pack_forget()
                self.machineInfo.insert(tk.END, 'Machine Model is: {}. ADD ENCODER and ADD SERVOS buttons have been hidden'.format(machine))
            else:
                self.machineInfo.insert(tk.END, 'Machine Model is: {}\n'.format(machine))
        else:
            self.machineInfo.insert(tk.END, 'ERROR: {} is missing! Unable to proceed!\n'.format(machineFile), 'red')
            return
        if not os.path.exists(self.tmc):
            self.currentVersionInfo.insert(tk.END, 'ERROR: ~/tmc does not exist, is PathPilot installed?\n', 'red')
            return
        versionFile = os.path.join(self.tmc, 'version.json')
        if os.path.exists(versionFile):
            with open(versionFile, 'r') as jsonFile:
                versionData = json.load(jsonFile)
            self.currentVer = versionData['version']
            self.currentVersionInfo.insert(tk.END, 'Current Version of PathPilot is: {}\n'.format(self.currentVer))
        else:
            self.currentVersionInfo.insert(tk.END, 'ERROR: {} is missing! Unable to proceed!\n'.format(versionFile), 'red')
            return
        self.previousVersionInfo.insert(tk.END, 'To use the COMPARE feature, click GET DIRECTORY TO COMPARE to select the directory of the version to compare the current version against', 'cyan')
        self.b0['state'] = 'normal'
        self.b3['state'] = 'normal'
        self.b4['state'] = 'normal'

    # Starts the firmware verification process on its own thread, otherwise it halts updates to the textbox
    def verifyThread(self, firmwareFile):
        self.console.insert(tk.END, '\nVerifying Mesa firmware...PLEASE WAIT\n', 'cyan')
        self.console.see(tk.END)
        t1 = threading.Thread(target=self.verifyFirmware, args=(firmwareFile,))
        t1.start()

    # Starts the firmware flash process on its own thread, otherwise it halts updates to the textbox
    def flashThread(self, firmwareFile):
        self.console.insert(tk.END, '\nFlashing Mesa firmware...PLEASE WAIT\n', 'cyan')
        self.console.see(tk.END)
        t2 = threading.Thread(target=self.flashFirmware, args=(firmwareFile,))
        t2.start()

    # Verify the firmware matches what is flashed to the card
    def verifyFirmware(self, firmwareFile):
        try:
            # check to see if mesaflash is installed
            test = check_output([self.mesaFlash], stderr=STDOUT)
            # verify firmware
            verify = ['sudo', self.mesaFlash, '--device', '5i25', '--verify', firmwareFile]
            output = Popen(verify)
            result = output.wait()
            if result == 0:
                self.console.insert(tk.END, 'Firmware matches, no flash required\n', 'orange')
                self.console.see(tk.END)
                return
            else:
                self.console.insert(tk.END, 'Firmware flash required!\n', 'yellow')
                self.console.see(tk.END)
        except Exception as e:
            self.console.insert(tk.END, '\nFIRMWARE VERIFICATION WAS UNSUCCESSFUL\n', 'red')
            self.console.insert(tk.END, '\nThe following error occured while verifying the firmware:\n\n{}\n'.format(e), 'red')
            self.console.see(tk.END)
            return
        self.flashThread(firmwareFile)

    # Flash the firmware to the card
    def flashFirmware(self, firmwareFile):
        try:
            flash = ['sudo', self.mesaFlash, '--device', '5i25', '--write', firmwareFile]
            output = Popen(flash)
            reply = output.wait()
            self.console.insert(tk.END, 'Firmware flash successful!\n\n', 'green')
            self.console.insert(tk.END, '\nA POWER CYCLE IS REQUIRED FOR CHANGES TO TAKE EFFECT!\n', 'white')
            self.powerCycleRequired = True
            self.console.see(tk.END)
        except Exception as e:
            self.console.insert(tk.END, '\nFIRMWARE FLASH WAS UNSUCCESSFUL\n', 'red')
            self.console.insert(tk.END, '\nThe following error occured while flashing the firmware:\n\n{}\n'.format(e), 'red')
            self.console.see(tk.END)

    # Exits PathPirate and checks if the user would like to reboot automatically
    def exitPathPirate(self, event=None):
        if self.powerCycleRequired:
            powerCycle = tkMessageBox.askquestion('POWER CYCLE REQUIRED', 'Would you like to power cycle the PC now?', icon='question', type='yesnocancel')
            if powerCycle == 'yes':
                os.system('sudo shutdown -H now')
            elif restart == 'no':
                self.main.destroy()
            else:
                pass
        elif self.restartRequired:
            restart = tkMessageBox.askquestion('RESTART REQUIRED', 'Would you like to restart the PC now?\n\nDISREGARD THE PATHPILOT POWER CYCLE SCREEN\n\nCOMPUTER WILL RESTART AUTOMATICALLY', icon='question', type='yesnocancel')
            if restart == 'yes':
                os.system('sudo reboot')
            elif restart == 'no':
                self.main.destroy()
            else:
                pass
        else:
            exit = tkMessageBox.askokcancel('EXIT PATHPIRATE', 'No restart is required\n\nWould you like to exit?')
            if exit == True:
                self.main.destroy()
            else:
                pass

if __name__ == '__main__':
    app = PathPirate()
