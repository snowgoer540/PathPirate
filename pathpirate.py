'''
pathpirate is a script that provides automated configuration changes to
Tormach's PathPilot.

Copyright (C) 2023, 2024, 2025 Gregory D Carl

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
        self.main.title("PathPirate Configurator v1.11 for Tormach's PathPilot v2.9.2 - v2.14.0")
        self.versionList = ['v2.9.2', 'v2.9.3', 'v2.9.4', 'v2.9.5', 'v2.9.6',
                            'v2.10.0', 'v2.10.1',
                            'v2.12.0', 'v2.12.1', 'v2.12.2', 'v2.12.3', 'v2.12.5',
                            'v2.13.0', 'v2.14.0']
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
        self.encoderHal = os.path.join(self.tmc, 'configs/tormach_mill/series3_encoder.hal')
        self.currentLatheIni = os.path.join(self.tmc, 'configs/tormach_lathe/tormach_lathe_base.ini')
        self.currentLatheHal = os.path.join(self.tmc, 'configs/tormach_lathe/tormach_lathe_mesa.hal')
        self.currentRapidTurnHal = os.path.join(self.tmc, 'configs/tormach_lathe/tormach_mill_mesa_rapidturn.hal')
        self.consoleHal1 = os.path.join(self.tmc, 'configs/common/operator_console_controls_3axis.hal')
        self.consoleHal2 = os.path.join(self.tmc, 'configs/common/operator_console_controls_4axis.hal')
        self.cm770_1 = os.path.join(self.tmc, 'configs/tormach_mill/tormach_770_specific.ini')
        self.cm770_2 = os.path.join(self.tmc, 'configs/tormach_mill/tormach_770_7i92_specific.ini')
        self.cm770_3 = os.path.join(self.tmc, 'configs/tormach_lathe/tormach_770_rapidturn_specific.ini')
        self.cm770_4 = os.path.join(self.tmc, 'configs/tormach_lathe/tormach_770_7i92_rapidturn_specific.ini')
        self.cm1100_1 = os.path.join(self.tmc, 'configs/tormach_mill/tormach_1100-3_specific.ini')
        self.cm1100_2 = os.path.join(self.tmc, 'configs/tormach_mill/tormach_1100-3_7i92_specific.ini')
        self.cm1100_3 = os.path.join(self.tmc, 'configs/tormach_lathe/tormach_1100-3_rapidturn_specific.ini')
        self.cm1100_4 = os.path.join(self.tmc, 'configs/tormach_lathe/tormach_1100-3_7i92_rapidturn_specific.ini')
        self.plasmaControls = os.path.join(self.tmc, 'python/images/primary_plasma_controls.glade')
        self.latheControls = os.path.join(self.tmc, 'python/images/primary_lathe_controls.glade')
        self.millControls = os.path.join(self.tmc, 'python/images/primary_mill_controls.glade')
        self.uiCommon = os.path.join(self.tmc, 'python/ui_common.py')
        self.uiLathe = os.path.join(self.tmc, 'python/tormach_lathe_ui.py')
        self.tooltips = os.path.join(self.tmc, 'python/res/tooltips.json')
        self.velImage = os.path.join(self.tmc, 'python/images/MAXVEL_100.jpg')
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
        self.rapidImage = os.path.join(self.pathPirateDir, 'files/rapid_slider/RAPID_100.jpg')
        self.halshowPath = os.path.join(self.pathPirateDir, 'files/halshow/halshow.tcl')
        self.cbuttonPath = os.path.join(self.pathPirateDir, 'files/halshow/cbutton.tcl')
        self.cp770_1 = os.path.join(self.pathPirateDir, 'files/configs/pathpirate_cpm_hsh_770_specific.ini')
        self.cp770_2 = os.path.join(self.pathPirateDir, 'files/configs/pathpirate_cpm_hsh_770_7i92_specific.ini')
        self.cp770_3 = os.path.join(self.pathPirateDir, 'files/configs/pathpirate_cpm_hsh_770_rapidturn_specific.ini')
        self.cp770_4 = os.path.join(self.pathPirateDir, 'files/configs/pathpirate_cpm_hsh_770_7i92_rapidturn_specific.ini')
        self.cp770Encoder_1 = os.path.join(self.pathPirateDir, 'files/configs/pathpirate_encoder_770_specific.ini')
        self.cp770Encoder_2 = os.path.join(self.pathPirateDir, 'files/configs/pathpirate_encoder_770_7i92_specific.ini')
        self.cp1100_1 = os.path.join(self.pathPirateDir, 'files/configs/pathpirate_cpm_hsh_1100-3_specific.ini')
        self.cp1100_2 = os.path.join(self.pathPirateDir, 'files/configs/pathpirate_cpm_hsh_1100-3_7i92_specific.ini')
        self.cp1100_3 = os.path.join(self.pathPirateDir, 'files/configs/pathpirate_cpm_hsh_1100-3_rapidturn_specific.ini')
        self.cp1100_4 = os.path.join(self.pathPirateDir, 'files/configs/pathpirate_cpm_hsh_1100-3_7i92_rapidturn_specific.ini')
        self.cp1100Encoder_1 = os.path.join(self.pathPirateDir, 'files/configs/pathpirate_encoder_1100-3_specific.ini')
        self.cp1100Encoder_2 = os.path.join(self.pathPirateDir, 'files/configs/pathpirate_encoder_1100-3_7i92_specific.ini')

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
            list = [self.uiCommon, self.consoleHal1, self.consoleHal2, self.tooltips, self.velImage, self.rapidImage]
        else:
            list = [self.uiCommon, self.consoleHal1, self.consoleHal2, self.tooltips, self.plasmaControls, self.latheControls, self.millControls]
        for file in list:
            if not os.path.exists(file):
                self.console.insert(tk.END, 'The following required file is missing: ', 'red')
                self.console.insert(tk.END, '{}\n'.format(file), 'pink')
                missing = True
        if missing:
            self.console.insert(tk.END, '\nAborting...\n', 'red')
            self.console.see(tk.END)
            return
        for modFile in [self.uiCommon, self.consoleHal1, self.consoleHal2, self.tooltips]:
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
            with open (self.velImage, 'rb') as originalImage:
                original = originalImage.read()
            with open (self.rapidImage, 'rb') as modImage:
                modified = modImage.read()
            if original == modified:
                self.console.insert(tk.END, 'Image file was previously replaced\n\n')
            else:
                tempFile = '{}.bak'.format(self.velImage)
                if not os.path.exists(tempFile):
                    copy(self.velImage, tempFile)
                copy(self.rapidImage, self.velImage)
                self.console.insert(tk.END, 'Image file copied to: ')
                self.console.insert(tk.END, '{}\n'.format(self.velImage), 'pink')
                change = True
        else:
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
        checkFiles = [self.currentMillIni, self.cm770_1, self.cm770_2, self.cm1100_1, self.cm1100_2, self.newMill7i92Bit, self.newMill7i92tBin, self.newMillBit]
        for file in checkFiles:
            if not os.path.exists(file):
                self.console.insert(tk.END, 'The following required file is missing: ', 'red')
                self.console.insert(tk.END, '{}\n'.format(file), 'pink')
                missing = True
        if missing:
            self.console.insert(tk.END, '\nAborting...\n', 'red')
            self.console.see(tk.END)
            return
        backupFiles = [self.currentMillIni, self.cm770_1, self.cm770_2, self.cm1100_1, self.cm1100_2]
        for file in backupFiles:
            tempFile = '{}.bak'.format(file)
            if not os.path.exists(tempFile):
                copy(file, tempFile)
        with open(self.currentMillIni, 'r+') as file:
            text = file.read()
            if 'HALFILE = series3_encoder.hal' in text:
                self.console.insert(tk.END, 'The necessary modifications are already present in the following file: ')
                self.console.insert(tk.END, '{}\n'.format(self.currentMillIni), 'pink')
            else:
                for line in text.splitlines():
                    if 'HALFILE = tormach_mill_mesa.hal' in line:
                        text = text.replace(line, 'HALFILE = tormach_mill_mesa.hal\nHALFILE = series3_encoder.hal')
                        file.seek(0)
                        file.truncate()
                        file.write(text)
                        change = True
                        self.console.insert(tk.END, 'The following file has been successfully modified: ')
                        self.console.insert(tk.END, '{}\n'.format(self.currentMillIni), 'pink')
        with open(self.encoderHal,'w') as file:
            text = ('#####################################################################\n')
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
        with open(self.cm1100_1, 'r+') as file:
            text = file.read()
            if not 'PathPirate' in text:
                copy(self.cp770Encoder_1, self.cm770_1)
                copy(self.cp770Encoder_2, self.cm770_2)
                copy(self.cp1100Encoder_1, self.cm1100_1)
                copy(self.cp1100Encoder_2, self.cm1100_2)
                change = True
                self.console.insert(tk.END, 'The following files has been successfully modified:\n')
                self.console.insert(tk.END, '{}\n'.format(self.cm770_1), 'pink')
                self.console.insert(tk.END, '{}\n'.format(self.cm770_2), 'pink')
                self.console.insert(tk.END, '{}\n'.format(self.cm1100_1), 'pink')
                self.console.insert(tk.END, '{}\n'.format(self.cm1100_2), 'pink')
            else:
                self.console.insert(tk.END, 'The necessary modifications are already present in the following files:\n')
                self.console.insert(tk.END, '{}\n'.format(self.cm770_1), 'pink')
                self.console.insert(tk.END, '{}\n'.format(self.cm770_2), 'pink')
                self.console.insert(tk.END, '{}\n'.format(self.cm1100_1), 'pink')
                self.console.insert(tk.END, '{}\n'.format(self.cm1100_2), 'pink')
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
        if self.machine in ['770', '1100-3']:
            self.addServosMill()
        else:
            self.addServosLathe()

    # Adds ClearPath Servos to a mill (that is using a Mesa 7i85s card)
    def addServosMill(self, event=None):
        self.console.insert(tk.END, '\n-----------------------\nADDING CLEARPATH SERVOS\n-----------------------\n', 'yellow')
        missing = False
        checkFiles = [self.currentMillHal, self.currentRapidTurnHal, self.clearPathMillHal, self.clearPathRapidTurnHal, self.newMill7i92Bit, self.newMill7i92tBin, self.newMillBit, self.uiLathe, self.cp1100_1, self.cp1100_2, self.cp1100_3, self.cp1100_4, self.cm1100_1, self.cm1100_2, self.cm1100_3, self.cm1100_4, self.cp770_1, self.cp770_2, self.cp770_3, self.cp770_4, self.cm770_1, self.cm770_2, self.cm770_3, self.cm770_4]
        for file in checkFiles:
            if not os.path.exists(file):
                self.console.insert(tk.END, 'The following required file is missing: ', 'red')
                self.console.insert(tk.END, '{}\n'.format(file), 'pink')
                missing = True
        if missing:
            self.console.insert(tk.END, '\nAborting...\n', 'red')
            self.console.see(tk.END)
            return
        backupFiles = [self.currentMillHal, self.currentRapidTurnHal, self.cm770_1, self.cm770_2, self.cm770_3, self.cm770_4, self.cm1100_1, self.cm1100_2, self.cm1100_3, self.cm1100_4]
        for file in backupFiles:
            tempFile = '{}.bak'.format(file)
            if not os.path.exists(tempFile):
                copy(file, tempFile)
        copy(self.cp770_1, self.cm770_1)
        copy(self.cp770_2, self.cm770_2)
        copy(self.cp770_3, self.cm770_3)
        copy(self.cp770_4, self.cm770_4)
        copy(self.cp1100_1, self.cm1100_1)
        copy(self.cp1100_2, self.cm1100_2)
        copy(self.cp1100_3, self.cm1100_3)
        copy(self.cp1100_4, self.cm1100_4)
        copy(self.clearPathMillHal, self.currentMillHal)
        copy(self.clearPathRapidTurnHal, self.currentRapidTurnHal)
        if not os.path.exists(self.encoderHal):
            with open(self.encoderHal,'w') as _:
                pass
        #in PP v2.9.x, the Y axis servo was not polled for fault conditions. This fixes that.
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
        self.console.insert(tk.END, '{}\n'.format(self.currentMillHal), 'pink')
        self.console.insert(tk.END, '{}\n'.format(self.currentRapidTurnHal), 'pink')
        self.console.insert(tk.END, '{}\n'.format(self.cm770_1), 'pink')
        self.console.insert(tk.END, '{}\n'.format(self.cm770_2), 'pink')
        self.console.insert(tk.END, '{}\n'.format(self.cm770_3), 'pink')
        self.console.insert(tk.END, '{}\n'.format(self.cm770_4), 'pink')
        self.console.insert(tk.END, '{}\n'.format(self.cm1100_1), 'pink')
        self.console.insert(tk.END, '{}\n'.format(self.cm1100_2), 'pink')
        self.console.insert(tk.END, '{}\n'.format(self.cm1100_3), 'pink')
        self.console.insert(tk.END, '{}\n'.format(self.cm1100_4), 'pink')
        for file in [self.newMillBit, self.newMill7i92Bit, self.newMill7i92tBin]:
            copy(file, self.mesaPath)
        self.console.insert(tk.END, '\nThe necessary firmwares have been copied to:\n')
        self.console.insert(tk.END, '{}\n'.format(self.mesaPath), 'pink')
        self.restartRequired = True
        self.console.insert(tk.END, '\nA RESTART IS REQUIRED FOR CHANGES TO TAKE EFFECT!\n', 'white')
        self.console.insert(tk.END, 'You will be prompted to restart upon exiting PathPirate\n', 'white')
        self.console.see(tk.END)

    # Adds ClearPath Servos to a lathe (that is using a Mesa 7i85s card)
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
        tempFile = '{}.bak'.format(self.uiLathe)
        if not os.path.exists(tempFile):
            copy(self.uiLathe, tempFile)
        with open(self.uiLathe, 'r+') as file:
            text = file.read()
            if 'PathPirate' in text:
                self.console.insert(tk.END, 'The necessary modifications are already present in the following file: ')
                self.console.insert(tk.END, '{}\n'.format(self.uiLathe), 'pink')
            else:
                text = text.replace('max_maxvel = 100.0', 'max_maxvel = 300.0#Changed by PathPirate')
                text = text.replace('max_maxvel = max_maxvel * 1.2', '#max_maxvel = max_maxvel * 1.2#Changed by PathPirate')
                file.seek(0)
                file.truncate()
                file.write(text)
                self.console.insert(tk.END, 'The following file has been successfully modified: ')
                self.console.insert(tk.END, '{}\n'.format(self.uiLathe), 'pink')
        self.console.insert(tk.END, 'The following files have been successfully modified:\n')
        self.console.insert(tk.END, '{}\n'.format(self.currentLatheIni), 'pink')
        self.console.insert(tk.END, '{}\n\n'.format(self.currentLatheHal), 'pink')
        for file in [self.newLatheBin]:
            copy(file, self.mesaPath)
        self.console.insert(tk.END, '\nThe necessary firmwares have been copied to:\n')
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
            changedFilesList = [self.uiCommon, self.uiLathe, self.consoleHal1, self.consoleHal2, self.velImage, self.currentMillIni, self.currentMillHal, self.cm1100_1, self.cm1100_2, self.cm1100_3, self.cm1100_4, self.cm770_1, self.cm770_2, self.cm770_3, self.cm770_4, self.currentRapidTurnHal, self.currentLatheHal, self.currentLatheIni, self.tooltips, self.plasmaControls, self.latheControls, self.millControls]
            for file in changedFilesList:
                tempFile = '{}.bak'.format(file)
                if os.path.exists(tempFile):
                    change = True
                    copy(tempFile, file)
                    os.remove(tempFile)
            for file in [self.encoderHal, self.pathPirateMillFirmware, self.pathPirateMill7i92Firmware, self.pathPirateMill7i92tFirmware, self.pathPirateLatheFirmware]:
                if os.path.exists(file):
                    os.remove(file)
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
        if not self.currentVer in self.versionList:
            self.currentVersionInfo.insert(tk.END, 'ERROR: PathPirate is not compatible with version {}! Unable to proceed!\n'.format(self.currentVer), 'red')
            self.console.insert(tk.END, '\nThe following versions are currently supported: {}\n'.format(', '.join(self.versionList)), 'yellow')
            return
        self.minorVer = int(self.currentVer.split('.')[1])
        self.currentVersionInfo.insert(tk.END, 'Current Version of PathPilot is: {}\n'.format(self.currentVer))
        self.versionFolder = 'v2.9.x' if self.currentVer in ['v2.9.2', 'v2.9.3', 'v2.9.4', 'v2.9.5', 'v2.9.6'] else self.currentVer
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
        # currently the 1100-3 and 7700 are supported, 15L Slant-PRO is in development
        if self.machine in ['770', '1100-3']:
            self.clearPathMillHal = os.path.join(self.pathPirateDir, 'files/configs/{}/pathpirate_cpm_hsh_mill.hal'.format(self.versionFolder))
            self.clearPathRapidTurnHal = os.path.join(self.pathPirateDir, \
            'files/configs/{}/pathpirate_cpm_hsh_rapidturn.hal'.format(self.versionFolder, self.machine))
            self.machineInfo.insert(tk.END, 'Machine Model is: {}\n'.format(self.machine))
        elif self.machine == '15L Slant-PRO':
            self.clearPathLatheHal = os.path.join(self.pathPirateDir, 'files/configs/{}/pathpirate_cpm_hsh_lathe.hal'.format(self.versionFolder))
            self.clearPathLatheIni = os.path.join(self.pathPirateDir, 'files/configs/{}/pathpirate_cpm_hsh_lathe.ini'.format(self.versionFolder))
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