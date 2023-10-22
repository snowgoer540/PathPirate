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
    import tkinter.simpledialog as tkSimpleDialog
    import tkinter.messagebox as tkMessageBox
else:
    import Tkinter as tk
    import tkSimpleDialog
    import tkMessageBox
from shutil import copy
import os
import json

class PathPirate:

    def __init__(self):
        # set up the main window
        self.main = tk.Tk()
        self.main.title("PathPirate Configurator v1.1 for Tormach's PathPilot")
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
        self.addHalshowButton = tk.Button(self.buttonFrame, text='ADD\nHALSHOW', command=self.addHalshow, height=2, padx=5)
        self.addHalshowButton.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.addHalshowButton['state'] = 'disabled'
        self.maxVelButton = tk.Button(self.buttonFrame, text='MAX VEL\nTO RAPID', command=self.convertSlider, height=2, padx=5)
        self.maxVelButton.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.maxVelButton['state'] = 'disabled'
        self.addEncoderButton = tk.Button(self.buttonFrame, text='ADD\nENCODER', command=self.addEncoder, height=2, padx=5)
        self.addEncoderButton.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.addEncoderButton['state'] = 'disabled'
        self.addServosButton = tk.Button(self.buttonFrame, text='ADD\nSERVOS', command=self.addServos, height=2, padx=5)
        self.addServosButton.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.addServosButton['state'] = 'disabled'
        self.revertAllButton = tk.Button(self.buttonFrame, text='REVERT\nALL', command=self.revertAll, height=2, padx=5)
        self.revertAllButton.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.revertAllButton['state'] = 'disabled'
        self.exitButton = tk.Button(self.buttonFrame, text='EXIT', command=self.exitPathPirate, height=2, padx=5)
        self.exitButton.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # set up output text boxes
        self.machineInfo = tk.Text(self.versionFrame, padx=5, height=1, bg='black', fg='yellow', highlightthickness=0, bd=0)
        self.machineInfo.pack(fill=tk.BOTH, expand=True)
        self.machineInfo.tag_configure('red', foreground='red')
        self.currentVersionInfo = tk.Text(self.versionFrame, padx=5, height=1, bg='black', fg='yellow', highlightthickness=0, bd=0)
        self.currentVersionInfo.pack(fill=tk.BOTH, expand=True)
        self.currentVersionInfo.tag_configure('red', foreground='red')
        self.console = tk.Text(self.consoleFrame, padx=5, bg='black', fg='orange', highlightthickness=0)
        self.console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.console.tag_configure('yellow', foreground='yellow')
        self.console.tag_configure('green', foreground='green')
        self.console.tag_configure('red', foreground='red')
        self.console.tag_configure('white', foreground='white')

        # add scroll bar to console text box
        self.scrollBar = tk.Scrollbar(self.consoleFrame, command=self.console.yview, width=15)
        self.scrollBar.pack(side=tk.LEFT, fill=tk.Y)
        self.console['yscrollcommand']=self.scrollBar.set

        # prevent typing in all text boxes
        self.machineInfo.bind('<Key>', lambda e: 'break')
        self.currentVersionInfo.bind('<Key>', lambda e: 'break')
        self.console.bind('<Key>', lambda e: 'break')

        # prevent mouse wheel scrolling in Info text boxes (linux separates scroll up and scroll down)
        self.machineInfo.bind('<Button-4>', lambda e: 'break')
        self.machineInfo.bind('<Button-5>', lambda e: 'break')
        self.currentVersionInfo.bind('<Button-4>', lambda e: 'break')
        self.currentVersionInfo.bind('<Button-5>', lambda e: 'break')

        # allow right click to cut, and copy
        self.console.bind('<Button-3>', self.rightClick)

        # set restart/power cycle flags false
        self.restartRequired = False

        # set up necessary paths
        self.home = os.getenv('HOME')
        self.tmc = os.path.join(self.home, 'tmc')
        self.sourcePath = os.path.join(self.tmc, 'tcl/bin')
        self.scriptFile = os.path.join(self.tmc, 'bin/halshow')
        self.currentMillIni = os.path.join(self.tmc, 'configs/tormach_mill/tormach_mill_base.ini')
        self.currentMillHal = os.path.join(self.tmc, 'configs/tormach_mill/tormach_mill_mesa.hal')
        self.currentLatheIni = os.path.join(self.tmc, 'configs/tormach_lathe/tormach_lathe_base.ini')
        self.currentLatheHal = os.path.join(self.tmc, 'configs/tormach_lathe/tormach_lathe_mesa.hal')
        self.currentRapidTurnIni = os.path.join(self.tmc, 'configs/tormach_lathe/tormach_rapidturn_base.ini')
        self.currentRapidTurnHal = os.path.join(self.tmc, 'configs/tormach_lathe/tormach_mill_mesa_rapidturn.hal')
        self.hal1 = os.path.join(self.tmc, 'configs/common/operator_console_controls_3axis.hal')
        self.hal2 = os.path.join(self.tmc, 'configs/common/operator_console_controls_4axis.hal')
        self.plasmaControls = os.path.join(self.tmc, 'python/images/primary_plasma_controls.glade')
        self.latheControls = os.path.join(self.tmc, 'python/images/primary_lathe_controls.glade')
        self.millControls = os.path.join(self.tmc, 'python/images/primary_mill_controls.glade')
        self.uiCommon = os.path.join(self.tmc, 'python/ui_common.py')
        self.uiLathe = os.path.join(self.tmc, 'python/tormach_lathe_ui.py')
        self.tooltips = os.path.join(self.tmc, 'python/res/tooltips.json')
        self.velPath = os.path.join(self.tmc, 'python/images/MAXVEL_100.jpg')
        self.mesaFlash = os.path.join(self.tmc, 'bin/mesaflash')
        self.mesaPath = os.path.join(self.tmc, 'mesa')
        self.pathPirateMillFirmware = os.path.join(self.mesaPath, '5i25_t2_7i85s_dpll.bit')
        self.pathPirateMill7i92Firmware = os.path.join(self.mesaPath, '7i92_7i85s.bit')
        self.pathPirateMill7i92tFirmware = os.path.join(self.mesaPath, '7i92t_7i85s.bin')
        self.pathPirateLatheFirmware = os.path.join(self.mesaPath, '5i25_t2_7i85s_dpll_lathe.bit')
        self.tormachFirmware = os.path.join(self.mesaPath, 'tormach_mill3.bit')

        self.pathPirateDir = os.path.realpath(os.path.dirname(__file__))
        self.newMillBit = os.path.join(self.pathPirateDir, 'files/firmware/mill/5i25_t2_7i85s_dpll.bit')
        self.newMill7i92Bit = os.path.join(self.pathPirateDir, 'files/firmware/mill/7i92_7i85s.bit')
        self.newMill7i92tBin =os.path.join(self.pathPirateDir, 'files/firmware/mill/7i92t_7i85s.bin')
        self.newLatheBin = os.path.join(self.pathPirateDir, 'files/firmware/lathe/5i25_t2_7i85s_dpll_lathe.bit')
        self.rapidPath = os.path.join(self.pathPirateDir, 'files/rapid_slider/RAPID_100.jpg')
        self.halshowPath = os.path.join(self.pathPirateDir, 'files/halshow/halshow.tcl')
        self.cbuttonPath = os.path.join(self.pathPirateDir, 'files/halshow/cbutton.tcl')

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

    # Adds halshow back to PathPilot so it can be called with 'ADMIN HALSHOW' via MDI
    def addHalshow(self, event=None):
        self.console.insert(tk.END, '\n--------------\nADDING HALSHOW\n--------------\n', 'yellow')
        # check if ~/tmc/tcl/bin exists (it shouldn't) and if it doesnt, create it
        if not os.path.lexists(self.sourcePath):
            os.mkdir(self.sourcePath)
        missing = False
        for file in [self.scriptFile, self.halshowPath, self.cbuttonPath]:
            if not os.path.exists(file):
                self.console.insert(tk.END, 'The following required file is missing: ', 'red')
                self.console.insert(tk.END, '{}\n'.format(file), 'pink')
                missing = True
        if missing:
            self.console.insert(tk.END, '\nAborting...\n', 'red')
            self.console.see(tk.END)
            return
        for file in [self.halshowPath, self.cbuttonPath]:
            copy(file, self.sourcePath)
        tempFile = '{}.bak'.format(self.scriptFile)
        if not os.path.exists(tempFile):
            copy(self.scriptFile, tempFile)
        with open(self.scriptFile,'w') as script:
            script.write('#!/usr/bin/tclsh8.6\n')
            script.write('source ~/tmc/tcl/bin/halshow.tcl')
        self.console.insert(tk.END, '\nhalshow.tcl and cbutton.tcl were successfully placed in: ')
        self.console.insert(tk.END, '{}\n'.format(self.sourcePath), 'pink')
        self.console.insert(tk.END, 'The following script was successfully modified: ')
        self.console.insert(tk.END, '{}\n\n'.format(self.scriptFile), 'pink')
        self.console.insert(tk.END, 'HALSHOW can be launched via the following MDI command: ')
        self.console.insert(tk.END, 'ADMIN HALSHOW\n', 'cyan')
        self.console.see(tk.END)

    # Converts the MAX VEL slider to RAPID since having a MAX VEL slider makes no sense
    def convertSlider(self, event=None):
        self.console.insert(tk.END, '\n---------------------------------------\nCONVERTING SLIDER FROM MAX VEL TO RAPID\n---------------------------------------\n', 'yellow')
        missing = False
        change = False
        if self.minorVer == 9:
            list = [self.uiCommon, self.hal1, self.hal2, self.tooltips, self.velPath, self.rapidPath]
        elif self.minorVer == 10:
            list = [self.uiCommon, self.hal1, self.hal2, self.tooltips, self.plasmaControls, self.latheControls, self.millControls]
        for file in list:
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
            with open(modFile, 'r+') as file:
                text = file.read()
                if 'PathPirate' in text:
                    self.console.insert(tk.END, 'The necessary modifications are already present in the following file: ')
                    self.console.insert(tk.END, '{}\n'.format(modFile), 'pink')
                    continue
                if modFile == self.uiCommon:
                    text = text.replace('lcnc_apply_function=lambda value: self.command.maxvel(value * self.maxvel_lin / 100, value * self.maxvel_ang / 100)),', \
                    'lcnc_apply_function=lambda value: self.command.rapidrate(value / 100)), #Changed by PathPirate')
                elif modFile == self.tooltips:
                    text = text.replace('''
        "maxvel_override_100": {
            "shorttext_id" : "msg_maxvel_override_text",
            "longtext_id" : "msg_maxvel_override_tooltip",
            "long_width": 275
        },
        "maxvel_override_scale": {
            "shorttext_id" : "msg_maxvel_override_text",
            "longtext_id" : "msg_maxvel_override_tooltip",
            "long_width": 275
        },''', '')

                else:
                    text = text.replace('setp tormach-console.0.rapid-override-scale 960', \
                    '#setp tormach-console.0.rapid-override-scale 960 #Changed by PathPirate')
                file.seek(0)
                file.truncate()
                file.write(text)
                self.console.insert(tk.END, 'The following file has been successfully modified: ')
                self.console.insert(tk.END, '{}\n'.format(modFile), 'pink')
                change = True
        if self.minorVer == 9:
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
        elif self.minorVer == 10:
            for modFile in [self.plasmaControls, self.latheControls, self.millControls]:
                tempFile = '{}.bak'.format(modFile)
                if not os.path.exists(tempFile):
                    copy(modFile, tempFile)
                with open(modFile, 'r+') as file:
                    text = file.read()
                    if '<property name="text">Rapid</property>' in text:
                        self.console.insert(tk.END, 'The necessary modifications are already present in the following file: ')
                        self.console.insert(tk.END, '{}\n'.format(modFile), 'pink')
                        continue
                    text = text.replace('<property name="text">Max   Vel</property>', \
                    '<property name="text">Rapid</property>')
                    file.seek(0)
                    file.truncate()
                    file.write(text)
                    self.console.insert(tk.END, 'The following file has been successfully modified: ')
                    self.console.insert(tk.END, '{}\n'.format(modFile), 'pink')
                    change = True
        if change:
            self.restartRequired = True
            self.console.insert(tk.END, '\nA RESTART IS REQUIRED FOR CHANGES TO TAKE EFFECT!\n', 'white')
            self.console.insert(tk.END, 'You will be prompted to restart upon exiting PathPirate\n', 'white')
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

    # Adds an encoder to a mill that is using a Mesa 7i85s card.  770 has not been tested.
    # This change is not necessary for the rapidturn configs
    def addEncoder(self, event=None):
        change = False
        missing = False
        self.console.insert(tk.END, '\n--------------\nADDING ENCODER\n--------------\n', 'yellow')
        # initialvalue is set to -1440 as a perk of being the author (that's my encoder's scale) :-)
        scale = self.askinteger(title='ENCODER SCALE', prompt='Enter the encoder scale:', initialvalue='-1440', parent=self.main)
        if scale is None:
            self.console.insert(tk.END, 'Encoder scale is required\n', 'red')
            self.console.see(tk.END)
            return
        for file in [self.currentMillHal, self.currentMillIni, self.clearPathMill7i92Ini, self.current7i92MillIni, self.newMill7i92Bit, self.newMill7i92tBin, self.newMillBit]:
            if not os.path.exists(file):
                self.console.insert(tk.END, 'The following required file is missing: ', 'red')
                self.console.insert(tk.END, '{}\n'.format(file), 'pink')
                missing = True
        if missing:
            self.console.insert(tk.END, '\nAborting...\n', 'red')
            self.console.see(tk.END)
            return
        with open(self.currentMillHal, 'r+') as file:
            text = file.read()
            if '# The following encoder lines were added by PathPirate' in text:
                if 'setp hm2_5i25.0.encoder.03.scale {}'.format(scale) in text:
                    self.console.insert(tk.END, 'The necessary modifications are already present in the following file: ')
                    self.console.insert(tk.END, '{}\n'.format(self.currentMillHal), 'pink')
                else:
                    for line in text.splitlines():
                        if 'setp hm2_5i25.0.encoder.03.scale' in line:
                            text = text.replace(line, 'setp hm2_5i25.0.encoder.03.scale {}'.format(scale))
                            file.seek(0)
                            file.truncate()
                            file.write(text)
                            change = True
                            self.console.insert(tk.END, 'The following file has been modified to change the encoder scale: '.format(self.currentMillHal))
                            self.console.insert(tk.END, '{}\n'.format(self.currentMillHal), 'pink')
            else:
                tempFile = '{}.bak'.format(self.currentMillHal)
                if not os.path.exists(tempFile):
                    copy(self.currentMillHal, tempFile)
                text += ('\n#####################################################################\n')
                text += ('# The following encoder lines were added by PathPirate\n\n')
                text += ('unlinkp motion.spindle-speed-in\n')
                text += ('net spindle-position hm2_5i25.0.encoder.03.position => motion.spindle-revs\n')
                text += ('net spindle-velocity hm2_5i25.0.encoder.03.velocity => motion.spindle-speed-in\n')
                text += ('net spindle-index-enable hm2_5i25.0.encoder.03.index-enable <=> motion.spindle-index-enable\n')
                text += ('setp hm2_5i25.0.encoder.03.scale {}'.format(scale))
                file.seek(0)
                file.truncate()
                file.write(text)
                change = True
                self.console.insert(tk.END, 'The following file has been successfully modified: ')
                self.console.insert(tk.END, '{}\n'.format(self.currentMillHal), 'pink')
        for file in [self.currentMillIni, self.current7i92MillIni]:
            tempFile = '{}.bak'.format(file)
            if not os.path.exists(tempFile):
                copy(file, tempFile)
        copy(self.clearPathMill7i92Ini, self.current7i92MillIni)
        with open(self.currentMillIni, 'r+') as file:
            text = file.read()
            if not '# Encoder added by PathPirate' in text:
                text = text.replace('DRIVER_PARAMS="config= num_encoders=2 num_pwmgens=1 num_3pwmgens=0 num_stepgens=5 "', \
                'DRIVER_PARAMS="config= num_encoders=4 num_pwmgens=1 num_3pwmgens=0 num_stepgens=5 "')
                text = text.replace('BITFILE0=mesa/tormach_mill3.bit', \
                'BITFILE0=mesa/5i25_t2_7i85s_dpll.bit')
                text += ('# Encoder added by PathPirate')
                file.seek(0)
                file.truncate()
                file.write(text)
                change = True
                self.console.insert(tk.END, 'The following file has been successfully modified: ')
                self.console.insert(tk.END, '{}\n'.format(self.currentMillIni), 'pink')
            else:
                self.console.insert(tk.END, 'The necessary modifications are already present in the following file: ')
                self.console.insert(tk.END, '{}\n'.format(self.currentMillIni), 'pink')
        for file in [self.newMillBit, self.newMill7i92Bit, self.newMill7i92tBin]:
            copy(file, self.mesaPath)
        self.console.insert(tk.END, '\nThe necessary firmwares have been copied to:\n')
        self.console.insert(tk.END, '{}\n'.format(self.mesaPath), 'pink')
        if change:
            self.restartRequired = True
            self.console.insert(tk.END, '\nA RESTART IS REQUIRED FOR CHANGES TO TAKE EFFECT!\n', 'white')
            self.console.insert(tk.END, 'You will be prompted to restart upon exiting PathPirate\n', 'white')
        self.console.see(tk.END)

    def addServos(self, event=None):
        if self.machine in ['1100-3', '770']:
            self.addServosMill()
        else:
            self.addServosLathe()

    # Adds ClearPath Servos to a mill (that is using a Mesa 7i85s card)
    def addServosMill(self, event=None):
        self.console.insert(tk.END, '\n-----------------------\nADDING CLEARPATH SERVOS\n-----------------------\n', 'yellow')
        missing = False
        encoder = False
        for file in [self.currentMillHal, self.currentMillIni, self.currentRapidTurnHal, self.currentRapidTurnIni, self.clearPathMillHal, self.clearPathMillIni, self.current7i92MillIni, self.current7i92RapidTurnIni, self.clearPathRapidTurnHal, self.clearPathRapidTurnIni, self.clearPathMill7i92Ini, self.clearPath7i92RapidTurnIni, self.newMill7i92Bit, self.newMill7i92tBin, self.newMillBit, self.uiLathe]:
            if not os.path.exists(file):
                self.console.insert(tk.END, 'The following required file is missing: ', 'red')
                self.console.insert(tk.END, '{}\n'.format(file), 'pink')
                missing = True
        if missing:
            self.console.insert(tk.END, '\nAborting...\n', 'red')
            self.console.see(tk.END)
            return
        for file in [self.currentMillIni, self.current7i92MillIni, self.currentMillHal, self.currentRapidTurnIni, self.current7i92RapidTurnIni, self.currentRapidTurnHal]:
            tempFile = '{}.bak'.format(file)
            if not os.path.exists(tempFile):
                copy(file, tempFile)
        with open(self.currentMillIni, 'r') as file:
            text=file.read()
        if '# Encoder added by PathPirate' in text:
            encoder = True
        copy(self.clearPathMillIni, self.currentMillIni)
        copy(self.clearPathRapidTurnIni, self.currentRapidTurnIni)
        copy(self.clearPathMill7i92Ini, self.current7i92MillIni)
        copy(self.clearPath7i92RapidTurnIni, self.current7i92RapidTurnIni)
        with open(self.currentMillIni, 'r+') as file:
            text = file.read()
            if encoder:
                text += ('# Encoder added by PathPirate\n')
                file.seek(0)
                file.truncate()
                file.write(text)
        if encoder:
            with open(self.currentMillHal, 'r') as file:
                    for line in file:
                        if line.startswith('setp hm2_5i25.0.encoder.03.scale'):
                            scale = line.split()[2]
        copy(self.clearPathMillHal, self.currentMillHal)
        copy(self.clearPathRapidTurnHal, self.currentRapidTurnHal)
        #in PP v2.9.x, the Y axis servo was not polled for fault conditions.  This fixes that.
        #Tormach has since fixed this for v2.10
        if self.minorVer == 9:
            tempFile = '{}.bak'.format(self.uiLathe)
            if not os.path.exists(tempFile):
                copy(self.uiLathe, tempFile)
            with open(self.uiLathe, 'r+') as file:
                text = file.read()
                if 'PathPirate' in text:
                    self.console.insert(tk.END, 'The necessary modifications are already present in the following file: ')
                    self.console.insert(tk.END, '{}\n'.format(self.uiLathe), 'pink')
                else:
                    text = text.replace('self.axis_motor_poll(0)', \
                    'self.axis_motor_poll(0)\n        if self.machineconfig.in_rapidturn_mode():#Changed by PathPirate\n            self.axis_motor_poll(1)#Changed by PathPirate')
                    file.seek(0)
                    file.truncate()
                    file.write(text)
                    self.console.insert(tk.END, 'The following file has been successfully modified: ')
                    self.console.insert(tk.END, '{}\n'.format(self.uiLathe), 'pink')
        self.console.insert(tk.END, 'The following files have been successfully modified:\n')
        self.console.insert(tk.END, '{}\n'.format(self.currentMillIni), 'pink')
        self.console.insert(tk.END, '{}\n'.format(self.currentMillHal), 'pink')
        self.console.insert(tk.END, '{}\n'.format(self.currentRapidTurnIni), 'pink')
        self.console.insert(tk.END, '{}\n\n'.format(self.currentRapidTurnHal), 'pink')
        if encoder:
            with open(self.currentMillHal, 'r+') as file:
                text = file.read()
                text += ('\n#####################################################################\n')
                text += ('# The following encoder lines were added by PathPirate\n\n')
                text += ('unlinkp motion.spindle-speed-in\n')
                text += ('net spindle-position hm2_5i25.0.encoder.03.position => motion.spindle-revs\n')
                text += ('net spindle-velocity hm2_5i25.0.encoder.03.velocity => motion.spindle-speed-in\n')
                text += ('net spindle-index-enable hm2_5i25.0.encoder.03.index-enable <=> motion.spindle-index-enable\n')
                text += ('setp hm2_5i25.0.encoder.03.scale {}'.format(scale))
                file.seek(0)
                file.truncate()
                file.write(text)
                self.console.insert(tk.END, 'Previous encoder information has been added to: ')
                self.console.insert(tk.END, '{}\n'.format(self.currentMillHal), 'pink')
        for file in [self.newMillBit, self.newMill7i92Bit, self.newMill7i92tBin]:
            copy(file, self.mesaPath)
        self.console.insert(tk.END, 'The necessary firmwares have been copied to:\n')
        self.console.insert(tk.END, '{}\n'.format(self.mesaPath), 'pink')
        self.restartRequired = True
        self.console.insert(tk.END, '\nA RESTART IS REQUIRED FOR CHANGES TO TAKE EFFECT!\n', 'white')
        self.console.insert(tk.END, 'You will be prompted to restart upon exiting PathPirate\n', 'white')
        self.console.see(tk.END)

    # Adds ClearPath Servos to a mill (that is using a Mesa 7i85s card)
    def addServosLathe(self, event=None):
        self.console.insert(tk.END, '\n-----------------------\nADDING CLEARPATH SERVOS\n-----------------------\n', 'yellow')
        missing = False
        for file in [self.currentLatheHal, self.currentLatheIni, self.clearPathLatheHal, self.clearPathLatheIni, self.newLatheBin]:
            if not os.path.exists(file):
                self.console.insert(tk.END, 'The following required file is missing: ', 'red')
                self.console.insert(tk.END, '{}\n'.format(file), 'pink')
                missing = True
        if missing:
            self.console.insert(tk.END, '\nAborting...\n', 'red')
            self.console.see(tk.END)
            return
        for file in [self.currentLatheHal, self.currentLatheIni]:
            tempFile = '{}.bak'.format(file)
            if not os.path.exists(tempFile):
                copy(file, tempFile)
        copy(self.clearPathLatheIni, self.currentLatheIni)
        copy(self.clearPathLatheHal, self.currentLatheHal)
        self.console.insert(tk.END, 'The following files have been successfully modified:\n')
        self.console.insert(tk.END, '{}\n'.format(self.currentLatheIni), 'pink')
        self.console.insert(tk.END, '{}\n\n'.format(self.currentLatheHal), 'pink')
        for file in [self.newLatheBin]:
            copy(file, self.mesaPath)
        self.console.insert(tk.END, 'The necessary firmwares have been copied to:\n')
        self.console.insert(tk.END, '{}\n'.format(self.mesaPath), 'pink')
        self.restartRequired = True
        self.console.insert(tk.END, '\nA RESTART IS REQUIRED FOR CHANGES TO TAKE EFFECT!\n', 'white')
        self.console.insert(tk.END, 'You will be prompted to restart upon exiting PathPirate\n', 'white')
        self.console.see(tk.END)

    # Revert any changes PathPirate may have made by restoring backup files/deleting new files
    def revertAll(self, event=None):
        self.console.insert(tk.END, '\n---------------------\nREVERTING ALL CHANGES\n---------------------\n', 'yellow')
        change = False
        halshow = False
        halshowPath = os.path.join(self.sourcePath, 'halshow.tcl')
        cbuttonPath = os.path.join(self.sourcePath, 'cbutton.tcl')
        try:
            for file in [self.uiCommon, self.uiLathe, self.hal1, self.hal2, self.velPath, self.currentMillHal, self.currentMillIni, self.currentRapidTurnIni, self.currentRapidTurnHal, self.currentLatheHal, self.currentLatheIni, self.tooltips, self.plasmaControls, self.latheControls, self.millControls]:
                tempFile = '{}.bak'.format(file)
                if os.path.exists(tempFile):
                    change = True
                    copy(tempFile, file)
                    os.remove(tempFile)
            # currently only the 1100-3 is supported (770 would go here too)
            if self.machine in ['1100-3']:
                for file in [self.current7i92MillIni, self.current7i92RapidTurnIni]:
                    tempFile = '{}.bak'.format(file)
                    if os.path.exists(tempFile):
                        change = True
                        copy(tempFile, file)
                        os.remove(tempFile)
            for firmware in [self.pathPirateMillFirmware, self.pathPirateMill7i92Firmware, self.pathPirateMill7i92tFirmware, self.pathPirateLatheFirmware]:
                if os.path.exists(firmware):
                    os.remove(firmware)
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
                self.console.insert(tk.END, 'You will be prompted to restart upon exiting PathPirate\n', 'white')
            else:
                self.console.insert(tk.END, 'There were no configuration changes in {} to revert\n'.format(self.currentVer))
            self.console.see(tk.END)
        except Exception as e:
            self.console.insert(tk.END, 'The following system error has occured:\n\n{}\n'.format(e), 'red')
            self.console.see(tk.END)
            return

    # Get the latest version number and machine model
    def getVersion(self, event=None):
        if not os.path.exists(self.tmc):
            self.currentVersionInfo.insert(tk.END, 'ERROR: ~/tmc does not exist, is PathPilot installed?\n', 'red')
            return
        versionFile = os.path.join(self.tmc, 'version.json')
        if not os.path.exists(versionFile):
            self.currentVersionInfo.insert(tk.END, 'ERROR: {} is missing! Unable to proceed!\n'.format(versionFile), 'red')
            return
        with open(versionFile, 'r') as jsonFile:
            versionData = json.load(jsonFile)
        self.currentVer = versionData['version']
        if not self.currentVer.split('-')[0] in ['v2.9.2', 'v2.9.3', 'v2.9.4', 'v2.9.5', 'v2.9.6', 'v2.10.0']:
            self.currentVersionInfo.insert(tk.END, 'ERROR: PathPirate is not compatible with version {}! Unable to proceed!\n'.format(self.currentVer), 'red')
            return
        self.minorVer = int(self.currentVer.split('.')[1])
        self.currentVersionInfo.insert(tk.END, 'Current Version of PathPilot is: {}\n'.format(self.currentVer))
        machineFile = os.path.join(self.home, 'pathpilot.json')
        if not os.path.exists(machineFile):
            self.machineInfo.insert(tk.END, 'ERROR: {} is missing! Unable to proceed!\n'.format(machineFile), 'red')
            return
        with open(machineFile, 'r') as jsonFile:
            machineData = json.load(jsonFile)
        try:
            self.machine = machineData['machine']['model']
        except:
            self.machineInfo.insert(tk.END, 'ERROR: Unable to extract machine model from: {}! Unable to proceed!\n'.format(machineFile), 'red')
            return
        # machine options: 1100-3, 770, 15L Slant-PRO
        # currently only the 1100-3 is supported (770 would go here too), 15L Slant-PRO is in development
        if self.machine in ['1100-3']:
            self.current7i92MillIni = os.path.join(self.tmc, 'configs/tormach_mill/tormach_{}_7i92_specific.ini'.format(self.machine))
            self.current7i92RapidTurnIni = os.path.join(self.tmc, \
            'configs/tormach_lathe/tormach_{}_7i92_rapidturn_specific.ini'.format(self.machine))
            self.clearPathMillHal = os.path.join(self.pathPirateDir, 'files/configs/pathpirate_cpm_hsh_mill.hal')
            self.clearPathMillIni = os.path.join(self.pathPirateDir, 'files/configs/pathpirate_cpm_hsh_mill.ini')
            self.clearPathMill7i92Ini = os.path.join(self.pathPirateDir, \
            'files/configs/pathpirate_cpm_hsh_{}_7i92_specific.ini'.format(self.machine))
            self.clearPathRapidTurnHal = os.path.join(self.pathPirateDir, \
            'files/configs/pathpirate_cpm_hsh_rapidturn_{}.hal'.format(self.machine))
            self.clearPathRapidTurnIni = os.path.join(self.pathPirateDir, \
            'files/configs/pathpirate_cpm_hsh_rapidturn_{}.ini'.format(self.machine))
            self.clearPath7i92RapidTurnIni = os.path.join(self.pathPirateDir, \
            'files/configs/pathpirate_cpm_hsh_{}_7i92_rapidturn_specific.ini'.format(self.machine))
            self.machineInfo.insert(tk.END, 'Machine Model is: {}\n'.format(self.machine))
        elif self.machine == '15L Slant-PRO':
            self.clearPathLatheHal = os.path.join(self.pathPirateDir, 'files/configs/pathpirate_cpm_hsh_lathe.hal')
            self.clearPathLatheIni = os.path.join(self.pathPirateDir, 'files/configs/pathpirate_cpm_hsh_lathe.ini')
            self.addEncoderButton.pack_forget()
            self.machineInfo.insert(tk.END, 'Machine Model is: {}. ADD ENCODER button has been hidden.\n'.format(self.machine))
        else:
            self.addEncoderButton.pack_forget()
            self.addServosButton.pack_forget()
            self.machineInfo.insert(tk.END, 'Machine Model is: {}. ADD ENCODER and ADD SERVOS buttons have been hidden.'.format(self.machine))
        self.addHalshowButton['state'] = 'normal'
        self.maxVelButton['state'] = 'normal'
        self.addEncoderButton['state'] = 'normal'
        self.addServosButton['state'] = 'normal'
        self.revertAllButton['state'] = 'normal'

    # Exits PathPirate and checks if the user would like to reboot automatically
    def exitPathPirate(self, event=None):
        if self.restartRequired:
            restart = tkMessageBox.askquestion('RESTART REQUIRED', 'Would you like to restart the PC now?\n\nDISREGARD THE PROCEEDING PATHPILOT POWER CYCLE SCREEN\n\nCOMPUTER WILL RESTART AUTOMATICALLY', icon='question', type='yesnocancel')
            if restart == 'yes':
                os.system('sudo reboot')
            elif restart == 'no':
                self.main.destroy()
            else:
                pass
        else:
            exit = tkMessageBox.askokcancel('EXIT', 'Are you sure?')
            if exit == True:
                self.main.destroy()
            else:
                pass

if __name__ == '__main__':
    app = PathPirate()