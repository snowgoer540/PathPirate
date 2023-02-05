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
from subprocess import Popen, PIPE, check_output, STDOUT
from shutil import copy
import socket
import os
import json
import difflib


class PathPirate:

    def __init__(self):
        # set up window
        self.main = tk.Tk()
        self.main.title('PathPirate Configurator v1.0 for Tormach Milling Machines')
        winWidth = 1000
        winHeight = 1000
        screenWidth = self.main.winfo_screenwidth()
        screenHeight = self.main.winfo_screenheight()
        xCoord = int((screenWidth/2) - (winWidth/2))
        yCoord = int((screenHeight/2) - (winHeight/2))
        self.main.geometry('{}x{}+{}+{}'.format(winWidth, winHeight, xCoord, yCoord))
        # self.main.attributes('-topmost',True)
        self.main.protocol('WM_DELETE_WINDOW', self.exitPathPirate)

        # add frames to window
        self.buttonFrame = tk.Frame(self.main)
        self.buttonFrame.pack(anchor=tk.NW, fill=tk.X)
        self.versionFrame = tk.Frame(self.main)
        self.versionFrame.pack(anchor=tk.NW, fill=tk.X)
        self.consoleFrame = tk.Frame(self.main)
        self.consoleFrame.pack(anchor=tk.NW, fill=tk.BOTH, expand=True)

        # set up buttons
        self.b0 = tk.Button(self.buttonFrame, text='PREVIOUS\nVERSION', command=self.openFile, height=2, padx=5)
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
        self.previousVersionInfo = tk.Text(self.versionFrame, padx=5, height=1, bg='black', fg='yellow', highlightthickness=0, bd=0)
        self.previousVersionInfo.pack(fill=tk.BOTH, expand=True)
        self.console = tk.Text(self.consoleFrame, padx=5, bg='black', fg='orange', highlightthickness=0)
        self.console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.console.tag_configure('green', foreground='green')
        self.console.tag_configure('orange', foreground='orange')
        self.console.tag_configure('red', foreground='red')
        self.console.tag_configure('cyan', foreground='cyan')
        self.console.tag_configure('white', foreground='white')
        self.previousVersionInfo.tag_configure('cyan', foreground='cyan')

        # add scroll bar to console
        self.scrollBar = tk.Scrollbar(self.consoleFrame, command=self.console.yview, width=15)
        self.scrollBar.pack(side=tk.LEFT, fill=tk.Y)
        self.console['yscrollcommand']=self.scrollBar.set

        # prevent typing in text boxes
        self.machineInfo.bind('<Key>', lambda e: 'break')
        self.currentVersionInfo.bind('<Key>', lambda e: 'break')
        self.previousVersionInfo.bind('<Key>', lambda e: 'break')
        self.console.bind('<Key>', lambda e: 'break')

        # prevent mouse wheel scrolling
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
        self.currentDir = os.path.realpath(os.path.dirname(__file__))
        self.newBin = os.path.join(self.currentDir, 'files/5i25_t2_7i85s_dpll.bit')
        self.rapidPath = os.path.join(self.currentDir, 'files/MAXVEL_100.jpg')
        self.halshowPath = os.path.join(self.currentDir, 'files/halshow.tcl')
        self.cbuttonPath = os.path.join(self.currentDir, 'files/cbutton.tcl')
        self.home = os.getenv('HOME')
        self.tmc = os.path.join(self.home, 'tmc')
        self.sourcePath = os.path.join(self.tmc, 'tcl/bin')
        self.scriptFile = os.path.join(self.tmc, 'bin/halshow')
        self.currentIni = os.path.join(self.tmc, 'configs/tormach_mill/tormach_mill_base.ini')
        self.currentHal = os.path.join(self.tmc, 'configs/tormach_mill/tormach_mill_mesa.hal')
        self.mesaPath = os.path.join(self.tmc, 'mesa')
        self.mesaFlash = os.path.join(self.tmc, 'bin/mesaflash')
        self.mesaNewFirmware = os.path.join(self.mesaPath, '5i25_t2_7i85s_dpll.bit')
        self.mesaOldFirmware = os.path.join(self.mesaPath, 'tormach_mill3.bit')
        self.uiCommon = os.path.join(self.tmc, 'python/ui_common.py')
        self.hal1 = os.path.join(self.tmc, 'configs/common/operator_console_controls_3axis.hal')
        self.hal2 = os.path.join(self.tmc, 'configs/common/operator_console_controls_4axis.hal')
        self.velPath = os.path.join(self.tmc, 'python/images/MAXVEL_100.jpg')

        # set restart flag false
        self.restartRequired = False

        # get current version and machine info
        self.getVersion()

        # call the main window loop
        self.main.mainloop()

    # Allows a user to right click to copy paste in the console text box
    def rightClick(self, event=None):
        menu = tk.Menu(self.main, tearoff=0)
        menu.add_command(label='Cut', command=lambda: self.console.event_generate('<<Cut>>'))
        menu.add_command(label='Copy', command=lambda: self.console.event_generate('<<Copy>>'))
        menu.tk_popup(event.x_root, event.y_root)

    # Shows the directory chooser for picking previous and current directories
    def openFile(self, event=None):
        self.b1['state'] = 'disabled'
        self.b2['state'] = 'disabled'
        self.old = tkFileDialog.askdirectory(
                initialdir=self.home,
                mustexist=True,
                title='Select PREVIOUS Version Folder (v2.X.X)')
        if not self.old:
            self.previousVersionInfo.delete(1.0, tk.END)
            self.previousVersionInfo.insert(tk.END, 'PREVIOUS directory selection is required')
            return
        test = self.old.split('/')
        if not 'v2' in test[len(test)-1]:
            self.previousVersionInfo.delete(1.0, tk.END)
            self.previousVersionInfo.insert(tk.END, 'Incorrect directory choice. Base directory must be chosen (v2.X.X)')
            return
        for self.previous in test:
            if 'v2' in self.previous:
                self.previousVersionInfo.delete(1.0, tk.END)
                self.previousVersionInfo.insert(tk.END, 'Previous Version of PathPilot is: {}'.format(self.previous))
        self.b1['state'] = 'normal'
        self.b2['state'] = 'normal'

    # Compares between chosen configuration files
    def compare(self, extension, event=None):
        oldMod = False
        missing = False
        self.console.insert(tk.END, '\n------------------\nCOMPARING {} FILE\n------------------\n'.format(extension.upper()))
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
            self.console.insert(tk.END, 'PREVIOUS ({}) - MODIFIED {} FILE DETECTED\n'.format(self.previous, extension))
            self.console.insert(tk.END, 'Using backup {} file to compare against current version\n\n'.format(extension))
            self.console.see(tk.END)
        for file in [oldFile, newFile]:
            if not os.path.exists(file):
                self.console.insert(tk.END, 'The following required file is missing: {}\n'.format(file))
                missing = True
        if missing:
            self.console.insert(tk.END, '\nAborting...\n', 'red')
            self.console.see(tk.END)
            return
        with open(oldFile, 'r') as previous, open(newFile, 'r') as current:
            previous = previous.read()
            current = current.read()
        if 'PathPirate' in current:
            self.console.insert(tk.END, 'CURRENT ({}) - MODIFIED {} FILE DETECTED\n\n'.format(self.current, extension))
            # self.console.insert(tk.END, 'Using compare on unmodified config files may make changes more apparent\n\n')
            self.console.see(tk.END)
        if previous == current:
            self.console.insert(tk.END, 'No changes present (the files are the same)\n')
            self.console.see(tk.END)
            return
        self.console.insert(tk.END, 'The following changes exist between {} files:\n'.format(extension))
        previous = previous.strip().splitlines()
        current = current.strip().splitlines()
        # credit for help on this: https://stackoverflow.com/a/19128062
        for line in difflib.unified_diff(previous, current, lineterm='', n=0):
            if line.startswith('---') or line.startswith('+++'):
                continue
            elif line.startswith('@@'):
                self.console.insert(tk.END, '\n')
            else:
                if '+' in line:
                    self.console.insert(tk.END, '{}: {}\n'.format(self.current, line[1:]), 'green')
                elif '-' in line:
                    self.console.insert(tk.END, '{}: {}\n'.format(self.previous, line[1:]), 'red')
        self.console.see(tk.END)

    # Adds halshow back to PathPilot so it can be called with 'ADMIN HALSHOW' via MDI
    def addHalshow(self, event=None):
        internet = self.internetStatus()
        self.console.insert(tk.END, '\n--------------\nADDING HALSHOW\n--------------\n')
        # check if ~/tmc/tcl/bin exists (it shouldn't) and if it doesnt, create it
        if not os.path.lexists(self.sourcePath):
            os.mkdir(self.sourcePath)
        # attempt to grab latest halshow.tcl and cbutton.tcl from the linuxCNC master repository
        if internet:
            self.console.insert(tk.END, 'Internet connection found - Attempting to pull latest files from LinuxCNC master repository\n')
            self.console.insert(tk.END, '(Previous versions will be overwritten)\n\n')
            try:
                # check for wget
                test = check_output(['wget', '--version'], stderr=STDOUT)
                # attempt to pull files from github
                output = check_output('wget --quiet -O {}/halshow.tcl https://raw.github.com/LinuxCNC/linuxcnc/master/tcl/bin/halshow.tcl'.format(self.sourcePath), shell=True, stderr=STDOUT)
                output1 = check_output('wget --quiet -O {}/cbutton.tcl https://raw.github.com/LinuxCNC/linuxcnc/master/tcl/bin/cbutton.tcl'.format(self.sourcePath), shell=True, stderr=STDOUT)
            except Exception as e:
                self.console.insert(tk.END, 'The following error occurred while attempting to pull Halshow files from github repository:\n\n{}\n\n'.format(e), 'red')
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
            self.console.insert(tk.END, 'The following required file is missing: {}\n'.format(self.scriptFile))
            self.console.see(tk.END)
            return
        self.console.insert(tk.END, '\nhalshow.tcl and cbutton.tcl were successfully placed in: {}\n'.format(self.sourcePath))
        self.console.insert(tk.END, '{} script was successfuly updated\n\n'.format(self.scriptFile))
        self.console.insert(tk.END, 'HALSHOW can be launched via the following MDI command:\nADMIN HALSHOW\n')
        self.console.see(tk.END)

    # Helper function to copy local files if no internet, or internet pull fails
    def addHalshowCopy(self):
            self.console.insert(tk.END, 'Copying local files\n')
            missing = False
            for file in [self.halshowPath, self.cbuttonPath]:
                if not os.path.exists(file):
                    self.console.insert(tk.END, 'The following required file is missing: {}\n'.format(file), 'red')
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
        self.console.insert(tk.END, '\n---------------------------------------\nCONVERTING SLIDER FROM MAX VEL TO RAPID\n---------------------------------------\n')
        missing = False
        change = False
        for file in [self.uiCommon, self.hal1, self.hal2, self.velPath, self.rapidPath]:
            if not os.path.exists(file):
                self.console.insert(tk.END, 'The following required file is missing: {}\n'.format(file), 'red')
                missing = True
        if missing:
            self.console.insert(tk.END, '\nAborting...\n', 'red')
            self.console.see(tk.END)
            return
        for modFile in [self.uiCommon, self.hal1, self.hal2]:
            tempFile = '{}.bak'.format(modFile)
            if not os.path.exists(tempFile):
                copy(modFile, tempFile)
            with open(modFile, 'r+') as file:
                text = file.read()
                if 'PathPirate' in text:
                    self.console.insert(tk.END, 'Modifications to {} are already present\n'.format(modFile))
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
                self.console.insert(tk.END, '{} has been modified\n'.format(modFile))
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
            self.console.insert(tk.END, 'Image file copied to: {}\n'.format(self.velPath))
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
        self.console.insert(tk.END, '\n---------------\nADDING ENCODER\n---------------\n')
        scale = self.askinteger(title='ENCODER SCALE', prompt='Enter the encoder scale:', initialvalue='-1440', parent=self.main)
        if scale is None:
            self.console.insert(tk.END, 'Encoder scale is required\n')
            self.console.see(tk.END)
            return
        for file in [self.currentHal, self.currentIni, self.newBin]:
            if not os.path.exists(file):
                self.console.insert(tk.END, 'The following required file is missing: {}\n'.format(file), 'red')
                missing = True
        if missing:
            self.console.insert(tk.END, '\nAborting...\n', 'red')
            self.console.see(tk.END)
            return
        with open(self.currentHal, 'r+') as file:
            text = file.read()
            if '#The following encoder lines were added by PathPirate' in text:
                if 'setp hm2_5i25.0.encoder.00.scale {}'.format(scale) in text:
                    self.console.insert(tk.END, 'Modifications to {} are already present\n'.format(self.currentHal))
                else:
                    for line in text.splitlines():
                        if 'setp hm2_5i25.0.encoder.00.scale' in line:
                            text = text.replace(line, 'setp hm2_5i25.0.encoder.00.scale {}'.format(scale))
                            file.seek(0)
                            file.truncate()
                            file.write(text)
                            change = True
                            self.console.insert(tk.END, '{} has been modified\n'.format(self.currentHal))
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
                self.console.insert(tk.END, '{} has been modified\n'.format(self.currentHal))
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
                self.console.insert(tk.END, '{} has been modified\n'.format(self.currentIni))
            else:
                self.console.insert(tk.END, 'Necessary modifications to {} are already present\n'.format(self.currentIni))
        if not os.path.exists(os.path.join(self.mesaPath, '5i25_t2_7i85s_dpll.bit')):
            copy(self.newBin, self.mesaPath)
            change = True
            self.console.insert(tk.END, '{} has been copied to {}\n'.format(self.newBin, self.mesaPath))
            self.flashFirmware(self.mesaNewFirmware)
        else:
            self.console.insert(tk.END, '5i25_t2_7i85s_dpll.bit already exists in {}\n'.format(self.mesaPath))
        if change:
            self.restartRequired = True
            self.console.insert(tk.END, '\nA RESTART IS REQUIRED FOR CHANGES TO TAKE EFFECT!\n', 'white')
        self.console.see(tk.END)

    # Adds ClearPath Servos to an 1100-3 machine (that is using a Mesa 7i85s card)
    def addServos(self, event=None):
        self.console.insert(tk.END, '\n-----------------------\nADDING CLEARPATH SERVOS\n-----------------------\n')
        hostmotSection = False
        trajSection = False
        xySection = False
        zSection = False
        putSmoothing = False
        missing = False
        change = False
        for file in [self.currentHal, self.currentIni, self.newBin, self.mesaPath]:
            if not os.path.exists(file):
                self.console.insert(tk.END, 'The following required file is missing: {}\n'.format(file), 'red')
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
                    outFile.write('#Servos added by PathPirate\n')
                change = True
                self.console.insert(tk.END, '{} has been modified\n'.format(self.currentIni))
        else:
            self.console.insert(tk.END, 'Modifications to {} are already present\n'.format(self.currentIni))
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
                self.console.insert(tk.END, '{} has been modified\n'.format(self.currentHal))
            else:
                self.console.insert(tk.END, 'Modifications to {} are already present\n'.format(self.currentHal))
        if not os.path.exists(os.path.join(self.mesaPath, '5i25_t2_7i85s_dpll.bit')):
            copy(self.newBin, self.mesaPath)
            change = True
            self.console.insert(tk.END, '{} has been copied to {}\n'.format(self.newBin, self.mesaPath))
            self.flashFirmware(self.mesaNewFirmware)
        else:
            self.console.insert(tk.END, '5i25_t2_7i85s_dpll.bit already exists in {}\n'.format(self.mesaPath))
        if change:
            self.restartRequired = True
            self.console.insert(tk.END, '\nA RESTART IS REQUIRED FOR CHANGES TO TAKE EFFECT!\n', 'white')
        self.console.see(tk.END)

    # Revert any changes that have occurred by restoring backup files/deleting new files
    def revertAll(self, event=None):
        change = False
        halshow = False
        halshowPath = os.path.join(self.sourcePath, 'halshow.tcl')
        cbuttonPath = os.path.join(self.sourcePath, 'cbutton.tcl')
        try:
            for file in [self.uiCommon, self.hal1, self.hal2, self.velPath, self.currentHal, self.currentIni]:
                tempFile = '{}.bak'.format(file)
                if os.path.exists(tempFile):
                    change = True
                    copy(tempFile, file)
                    os.remove(tempFile)
            if os.path.exists(self.mesaNewFirmware):
                change = True
                os.remove(self.mesaNewFirmware)
                self.flashFirmware(self.mesaOldFirmware)
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
            if change:
                self.restartRequired = True
                self.console.insert(tk.END, '\nAll changes to {} have been undone\n'.format(self.current))
                self.console.insert(tk.END, '\nA RESTART IS REQUIRED FOR CHANGES TO TAKE EFFECT!\n', 'white')
            elif halshow:
                self.console.insert(tk.END, '\nHalshow changes were removed\n')
            else:
                self.console.insert(tk.END, '\nThere were no changes in {} to revert\n'.format(self.current))
            self.console.see(tk.END)
        except Exception as e:
            self.console.insert(tk.END, '\nThe following system error has occured:\n\n{}'.format(e), 'red')
            self.console.see(tk.END)

    # Show the user the latest version number
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
            self.machineInfo.insert(tk.END, '{} is missing! Unable to proceed!\n'.format(machineFile))
            return
        if not os.path.exists(self.tmc):
            self.currentVersionInfo.insert(tk.END, '~/tmc does not exist, is PathPilot installed?\n')
            return
        versionFile = os.path.join(self.tmc, 'version.json')
        if os.path.exists(versionFile):
            with open(versionFile, 'r') as jsonFile:
                versionData = json.load(jsonFile)
            self.current = versionData['version']
            self.currentVersionInfo.insert(tk.END, 'Current Version of PathPilot is: {}\n'.format(self.current))
        else:
            self.currentVersionInfo.insert(tk.END, '{} is missing! Unable to proceed!\n'.format(versionFile))
            return
        self.previousVersionInfo.insert(tk.END, 'To use the COMPARE feature, click PREVIOUS VERSION to select the previous version directory', 'cyan')
        self.b0['state'] = 'normal'
        self.b3['state'] = 'normal'
        self.b4['state'] = 'normal'

    def flashFirmware(self, firmwareFile):
        try:
            self.console.insert(tk.END, '\nVerifying Mesa firmware...\n', 'cyan')
            verify = ['sudo', self.mesaFlash, '--device', '5i25', '--verify', firmwareFile]
            verifyFirmware = check_output(verify)
            result = verifyFirmware.wait()
            if result == 0:
                self.console.insert(tk.END, 'Firmware matches, no flash required\n', 'cyan')
                return
            else:
                self.console.insert(tk.END, 'Firmware differs, flash required\n', 'cyan')
        except Exception as e:
            self.console.insert(tk.END, '\nFIRMWARE VERIFICATION WAS UNSUCCESSFUL\n', 'red')
            self.console.insert(tk.END, '\nThe following error occured while verifying the firmware:\n\n{}'.format(e), 'red')
            return
        try:
            self.console.insert(tk.END, '\nFlashing Mesa firmware...\n', 'cyan')
            flash = ['sudo', self.mesaFlash, '--device', '5i25', '--write', firmwareFile]
            flashFirmware = check_output(flash)
            #TODO: verify this is necessary
            while flashFirmware.poll() == None:
                time.sleep(0.2)
            result = flashFirmware.wait()
            self.console.insert(tk.END, 'Flash successful with the following message:\n\n{}'.format(result), 'cyan')
        except Exception as e:
            self.console.insert(tk.END, '\nFIRMWARE FLASH WAS UNSUCCESSFUL\n', 'red')
            self.console.insert(tk.END, '\nThe following error occured while flashing the firmware:\n\n{}'.format(e), 'red')

    def exitPathPirate(self, event=None):
        if self.restartRequired:
            restart = tkMessageBox.askquestion('REBOOT REQUIRED', 'Would you like to reboot now?', icon='question')
            if restart == 'yes':
                os.system('sudo reboot')
            else:
                self.main.destroy()
        else:
            self.main.destroy()

if __name__ == '__main__':
    app = PathPirate()
