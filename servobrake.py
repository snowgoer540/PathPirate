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
    import tkinter.messagebox as tkMessageBox
else:
    import Tkinter as tk
    import tkMessageBox
from subprocess import Popen, PIPE
import os
import json
import time

class ServoBrake:

    def __init__(self):
        # set up the main window
        self.main = tk.Tk()
        self.main.title("PathPirate Servo Brake Release Tool v1.9 for Tormach's PathPilot v2.9.2 - v2.12.5")
        self.versionList = ['v2.9.2', 'v2.9.3', 'v2.9.4', 'v2.9.5', 'v2.9.6',
                            'v2.10.0', 'v2.10.1',
                            'v2.12.0', 'v2.12.1', 'v2.12.2', 'v2.12.3', 'v2.12.5']
        win_width = 1000
        win_height = 700
        screen_width = self.main.winfo_screenwidth()
        screen_height = self.main.winfo_screenheight()
        x_coord = int((screen_width/2) - (win_width/2))
        y_coord = int((screen_height/2) - (win_height/2))
        self.main.geometry('{}x{}+{}+{}'.format(win_width, win_height, x_coord, y_coord))
        self.main.attributes('-zoomed', True)
        self.main.attributes('-topmost',True)
        self.main.protocol('WM_DELETE_WINDOW', self.exit_pass)
        #changes the default line wrap length of message boxes  (Credit: https://stackoverflow.com/a/62307975)
        self.main.option_add("*Dialog.msg.wrapLength", "14i")

        # add frames to window
        self.button_frame = tk.Frame(self.main)
        self.button_frame.pack(anchor=tk.NW, fill=tk.X)
        self.version_frame = tk.Frame(self.main)
        self.version_frame.pack(anchor=tk.NW, fill=tk.X)
        self.console_frame = tk.Frame(self.main)
        self.console_frame.pack(anchor=tk.NW, fill=tk.BOTH, expand=True)

        # set up buttons
        self.release_brake_button = tk.Button(self.button_frame, text='RELEASE\nBRAKE', command=self.release_brake, height=2, padx=5)
        self.release_brake_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.release_brake_button['state'] = 'disabled'
        self.engage_brake_button = tk.Button(self.button_frame, text='ENGAGE\nBRAKE', command=self.engage_brake, height=2, padx=5)
        self.engage_brake_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.engage_brake_button['state'] = 'disabled'
        self.exit_button = tk.Button(self.button_frame, text='EXIT', command=self.exit_servo_brake, height=2, padx=5)
        self.exit_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # set up output text boxes
        self.machine_info = tk.Text(self.version_frame, padx=5, height=1, bg='black', fg='yellow', highlightthickness=0, bd=0)
        self.machine_info.pack(fill=tk.BOTH, expand=True)
        self.machine_info.tag_configure('red', foreground='red')
        self.current_version_info = tk.Text(self.version_frame, padx=5, height=1, bg='black', fg='yellow', highlightthickness=0, bd=0)
        self.current_version_info.pack(fill=tk.BOTH, expand=True)
        self.current_version_info.tag_configure('red', foreground='red')
        self.board_info = tk.Text(self.version_frame, padx=5, height=1, bg='black', fg='yellow', highlightthickness=0, bd=0)
        self.board_info.pack(fill=tk.BOTH, expand=True)
        self.board_info.tag_configure('red', foreground='red')
        self.console = tk.Text(self.console_frame, padx=5, bg='black', fg='orange', highlightthickness=0)
        self.console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.console.tag_configure('yellow', foreground='yellow')
        self.console.tag_configure('green', foreground='green')
        self.console.tag_configure('orange', foreground='orange')
        self.console.tag_configure('red', foreground='red')
        self.console.tag_configure('cyan', foreground='cyan')
        self.console.tag_configure('white', foreground='white')
        self.console.tag_configure('bold', font='Helvetica 12 bold', foreground='white')
        self.console.tag_configure('bold_green', font='Helvetica 12 bold', foreground='green')
        self.console.tag_configure('bold_red', font='Helvetica 12 bold', foreground='red')

        # add scroll bar to console text box
        self.scroll_bar = tk.Scrollbar(self.console_frame, command=self.console.yview, width=15)
        self.scroll_bar.pack(side=tk.LEFT, fill=tk.Y)
        self.console['yscrollcommand']=self.scroll_bar.set

        # prevent typing in all text boxes
        self.machine_info.bind('<Key>', lambda e: 'break')
        self.current_version_info.bind('<Key>', lambda e: 'break')
        self.console.bind('<Key>', lambda e: 'break')

        # prevent mouse wheel scrolling in Info text boxes (linux separates scroll up and scroll down)
        self.machine_info.bind('<Button-4>', lambda e: 'break')
        self.machine_info.bind('<Button-5>', lambda e: 'break')
        self.current_version_info.bind('<Button-4>', lambda e: 'break')
        self.current_version_info.bind('<Button-5>', lambda e: 'break')

        # allow right click to cut, and copy
        self.console.bind('<Button-3>', self.right_click)

        # set up necessary paths
        self.home = os.getenv('HOME')
        self.machine_file = os.path.join(self.home, 'pathpilot.json')
        self.tmc = os.path.join(self.home, 'tmc')
        self.halcmd_folder = os.path.join(self.home, 'tmc/bin')
        self.halcmd = os.path.join(self.halcmd_folder, 'halcmd')
        self.version_file = os.path.join(self.tmc, 'version.json')
        self.mill_hal = os.path.join(self.tmc, 'configs/tormach_mill/tormach_mill_mesa.hal')
        self.lathe_hal = os.path.join(self.tmc, 'configs/tormach_lathe/tormach_lathe_mesa.hal')

        self.board = ''

        # get current version and machine info
        self.get_version()

        # call the main window loop
        self.main.mainloop()

    # Allows a user to right click to cut or copy in the console text box
    def right_click(self, event=None):
        menu = tk.Menu(self.main, tearoff=0)
        menu.add_command(label='Cut', command=lambda: self.console.event_generate('<<Cut>>'))
        menu.add_command(label='Copy', command=lambda: self.console.event_generate('<<Copy>>'))
        menu.tk_popup(event.x_root, event.y_root)

    # Release the servo brake (energize the coil)
    # Brake is gpio.023 on EMCV1.5 machines
    def release_brake(self):
        self.console.insert(tk.END, '\nRELEASE BRAKE CLICKED', 'orange')
        self.console.insert(tk.END, '\nChecking E-STOP status...........................................', 'yellow')
        out, err = self.send_commands(self.halcmd, 'gets', self.estop_signal)
        if out.strip() != 'FALSE':
            self.console.insert(tk.END, 'FAILED\n', 'red')
            tkMessageBox.showinfo('ERROR', 'PathPilot has been RESET.\n\nPathPilot must be in E-STOP state (RESET blinking).')
            self.console.insert(tk.END, 'PathPilot must be in E-STOP state (RESET blinking), unable to proceed.\n', 'cyan')
            self.console.see(tk.END)
            return
        self.console.insert(tk.END, 'OK\n', 'green')

        self.console.insert(tk.END, 'Checking machine status..........................................', 'yellow')
        out, err = self.send_commands(self.halcmd, 'getp', 'tormach.machine-ok')
        if out.strip() != 'TRUE':
            self.console.insert(tk.END, 'FAILED\n', 'red')
            tkMessageBox.showinfo('ERROR', 'Machine must be powered ON.\n\nFollow these steps:\n1. Reset physical E-STOP.\n2. Press green button.\n3. Do not click RESET in PathPirate.\n4. Press OK to try again.')
            self.console.insert(tk.END, 'Machine must be powered ON, unable to proceed.\n', 'cyan')
            self.console.see(tk.END)
            return
        self.console.insert(tk.END, 'OK\n', 'green')

        timeout = 5
        interval = 0.5
        elapsed = 0
        self.console.update_idletasks()
        self.console.insert(tk.END, 'Ensuring servo brake output is off.', 'yellow')
        while elapsed < timeout:
            out, err = self.send_commands(self.halcmd, 'getp', 'hm2_{}.0.gpio.{}.out'.format(self.board, self.gpio))
            if out.strip() == 'FALSE':
                self.console.insert(tk.END, '.............................OK\n', 'green')
                break
            time.sleep(interval)
            elapsed += interval
            self.console.insert(tk.END, '...', 'yellow')
            self.console.update_idletasks()
        else:
            self.console.insert(tk.END, 'FAILED\n', 'red')
            self.console.update_idletasks()
            tkMessageBox.showinfo('ERROR', 'Servo brake output pin did turn off within 5 seconds. Unable to proceed.\nPress E-STOP and wait a full 10 seconds before powering the machine on.\nThen restart this program to try again.\n')
            self.console.insert(tk.END, '\nServo brake output pin did turn off within 5 seconds. Unable to proceed.\n', 'red')
            self.console.insert(tk.END, 'Press E-STOP and wait a full 10 seconds before powering the machine on.\n', 'red')
            self.console.insert(tk.END, 'Then restart this program to try again.\n', 'red')
            self.console.see(tk.END)
            self.console.update_idletasks()
            return



        if self.board != 'EMC1':
            self.console.insert(tk.END, 'Unlinking machine board servo relay control pin..................', 'yellow')
            out, err = self.send_commands(self.halcmd, 'unlinkp', 'hm2_{}.0.pwmgen.00.enable'.format(self.board))
            if err.strip() != '':
                self.release_brake_button['state'] = 'disabled'
                self.console.insert(tk.END, '\n{}\n'.format(err), 'red')
                self.console.insert(tk.END, 'FAILED\n', 'red')
                self.console.insert(tk.END, 'Machine board servo relay control pin not found, unable to proceed.\n', 'cyan')
                self.console.see(tk.END)
                return
            self.console.insert(tk.END, 'OK\n', 'green')
            self.console.insert(tk.END, "Energzing machine board's servo brake relay to close contacts....", 'yellow')
            out, err = self.send_commands(self.halcmd, 'setp', 'hm2_{}.0.pwmgen.00.enable'.format(self.board), 'true')
            self.console.insert(tk.END, 'OK\n', 'green')

        self.console.insert(tk.END, 'Unlinking PathPirate servo brake coil relay pin..................', 'yellow')
        out, err = self.send_commands(self.halcmd, 'unlinkp', 'hm2_{}.0.gpio.{}.out'.format(self.board, self.gpio))
        if err.strip() != '':
            self.release_brake_button['state'] = 'disabled'
            self.console.insert(tk.END, 'FAILED\n', 'red')
            self.console.insert(tk.END, '\n{}\n'.format(err), 'red')
            self.console.insert(tk.END, 'PathPirate servo brake coil relay pin not found, unable to proceed.\n', 'cyan')
            self.console.see(tk.END)
            return
        self.console.insert(tk.END, 'OK\n', 'green')

        self.console.insert(tk.END, '\nENERGIZING THE SERVO BRAKE COIL TO RELEASE THE BRAKE.............', 'orange')
        out, err = self.send_commands(self.halcmd, 'setp', 'hm2_{}.0.gpio.{}.out'.format(self.board, self.gpio), 'true')

        self.console.insert(tk.END, 'OK\n', 'green')
        self.console.insert(tk.END, '\nBRAKE SUCCESSFULLY RELEASED\n', 'bold_green')
        self.console.insert(tk.END, '\nServo brake must be re-engaged before program may be exited.\n', 'cyan')
        self.console.insert(tk.END, '{} Axis ready for auto-tuning process.\n'.format(self.brake_axis.upper()), 'cyan')
        self.release_brake_button['state'] = 'disabled'
        self.exit_button['state'] = 'disabled'
        self.engage_brake_button['state'] = 'normal'
        self.console.see(tk.END)

    # Engage the servo brake (de-energize the coil)
    # Brake is gpio.023 on EMCV1.5 machines
    def engage_brake(self):
        self.console.insert(tk.END, '\nENGAGE BRAKE CLICKED', 'orange')
        self.console.insert(tk.END, '\nChecking E-STOP status...........................................', 'yellow')
        out, err = self.send_commands(self.halcmd, 'gets', self.estop_signal)
        if out.strip() != 'FALSE':
            self.console.insert(tk.END, 'FAILED\n', 'red')
            tkMessageBox.showinfo('ERROR', 'PathPilot has been RESET.\n\nPathPilot must be in E-STOP state (RESET blinking).')
            self.console.insert(tk.END, 'PathPilot must be in E-STOP state (RESET blinking), unable to proceed.\n', 'cyan')
            self.console.see(tk.END)
            return
        self.console.insert(tk.END, 'OK\n', 'green')

        self.console.insert(tk.END, 'Checking machine status..........................................', 'yellow')
        out, err = self.send_commands(self.halcmd, 'getp', 'tormach.machine-ok')
        if out.strip() != 'TRUE':
            tkMessageBox.showinfo('ERROR', 'Machine must be powered ON.\n\nFollow these steps:\n1. Reset physical E-STOP.\n2. Press green button.\n3. Do not click RESET in PathPirate.\n4. Press OK to try again.')
            self.console.insert(tk.END, 'Machine must be powered ON, unable to proceed.\n', 'cyan')
            self.console.see(tk.END)
            return
        self.console.insert(tk.END, 'OK\n', 'green')

        self.exit_button['state'] = 'normal'
        self.engage_brake_button['state'] = 'disabled'
        self.console.insert(tk.END, '\nDENERGIZING THE COIL TO ENGAGE THE BRAKE.........................', 'orange')
        out, err = self.send_commands(self.halcmd, 'setp', 'hm2_{}.0.gpio.{}.out'.format(self.board, self.gpio), 'false')
        if err.strip() != '':
            self.console.insert(tk.END, 'FAILED\n', 'red')
            self.console.insert(tk.END, '\n{}\n'.format(err), 'red')
            self.console.insert(tk.END, 'PathPirate servo brake coil relay pin not found, unable to proceed.\n', 'cyan')
            self.console.see(tk.END)
            return
        self.console.insert(tk.END, 'OK\n', 'green')
        self.console.insert(tk.END, '\n\nBRAKE SUCCESSFUL APPLIED\n\n', 'bold_green')

        self.console.insert(tk.END, 'Linking PathPirate servo brake coil relay pin....................', 'yellow')
        out, err = self.send_commands(self.halcmd, 'linkps', 'hm2_{}.0.gpio.{}.out'.format(self.board, self.gpio), '{}-axis-brake-release'.format(self.brake_axis))
        if err.strip() != '':
            self.console.insert(tk.END, 'FAILED\n', 'red')
            self.console.insert(tk.END, '\n{}\n'.format(err), 'red')
            self.console.insert(tk.END, 'Link unsuccessful, unable to proceed.\n', 'cyan')
            self.console.see(tk.END)
            return
        self.console.insert(tk.END, 'OK\n', 'green')

        if self.board != 'EMC1':
            self.console.insert(tk.END, "Denergzing machine board's servo brake relay to close contacts...", 'yellow')
            out, err = self.send_commands(self.halcmd, 'setp', 'hm2_{}.0.pwmgen.00.enable'.format(self.board), 'false')
            if err.strip() != '':
                self.console.insert(tk.END, 'FAILED\n', 'red')
                self.console.insert(tk.END, '\n{}\n'.format(err), 'red')
                self.console.insert(tk.END, 'Pin not found, unable to proceed.\n', 'cyan')
                self.console.see(tk.END)
                return
            self.console.insert(tk.END, 'OK\n', 'green')
            self.console.insert(tk.END, 'Linking machine board servo relay control pin....................', 'yellow')
            out, err = self.send_commands(self.halcmd, 'linkps', 'hm2_{}.0.pwmgen.00.enable'.format(self.board), self.estop_signal)
            if err.strip() != '':
                self.console.insert(tk.END, 'FAILED\n', 'red')
                self.console.insert(tk.END, '\n{}\n'.format(err), 'red')
                self.console.insert(tk.END, 'Link unsuccessful, unable to proceed.\n', 'cyan')
                self.console.see(tk.END)
                return
            self.console.insert(tk.END, 'OK\n', 'green')

        self.release_brake_button['state'] = 'normal'
        self.console.see(tk.END)

    # Get the latest version number and machine model
    def get_version(self):
        if not os.path.exists(self.tmc):
            self.current_version_info.insert(tk.END, 'ERROR: ~/tmc does not exist, is PathPilot installed?\n', 'red')
            return
        if not os.path.exists(self.halcmd_folder):
            self.current_version_info.insert(tk.END, 'ERROR: ~/tmc/bin does not exist, is PathPilot installed?\n', 'red')
            return
        os.chdir(self.halcmd_folder)
        if not os.path.exists(self.halcmd):
            self.current_version_info.insert(tk.END, 'ERROR: ~/tmc/bin/halcmd does not exist, is PathPilot installed?\n', 'red')
            return
        if not os.path.exists(self.version_file):
            self.current_version_info.insert(tk.END, 'ERROR: {} is missing! Unable to proceed!\n'.format(self.version_file), 'red')
            return
        if not os.path.exists(self.machine_file):
            self.machine_info.insert(tk.END, 'ERROR: {} is missing! Unable to proceed!\n'.format(self.machine_file), 'red')
            return
        if not os.path.exists(self.mill_hal):
            self.current_version_info.insert(tk.END, 'ERROR: {} is missing! Unable to proceed!\n'.format(self.mill_hal), 'red')
            return
        with open(self.version_file, 'r') as json_file:
            version_data = json.load(json_file)
        self.current_ver = version_data['version']
        if not self.current_ver.split('-')[0] in self.versionList:
            self.current_version_info.insert(tk.END, 'ERROR: PathPirate is not compatible with version {}! Unable to proceed!\n'.format(self.current_ver), 'red')
            self.console.insert(tk.END, '\nThe following versions are currently supported: {}\n'.format(', '.join(self.versionList)), 'yellow')
            return
        self.minor_ver = int(self.current_ver.split('.')[1])
        if self.minor_ver > 10:
            self.estop_signal = 'not-estop-signal'
        else:
            self.estop_signal = 'estop'
        self.current_version_info.insert(tk.END, 'Current Version of PathPilot is: {}\n'.format(self.current_ver))
        with open(self.machine_file, 'r') as json_file:
            machine_data = json.load(json_file)
        try:
            self.machine_class = machine_data['machine']['class']
            self.machine = machine_data['machine']['model']
            self.rapid_turn = machine_data['machine']['rapidturn']
        except:
            self.machine_info.insert(tk.END, 'ERROR: Missing data in: {}! Unable to proceed!\n'.format(self.machine_file), 'red')
            return
        if self.machine in ['770', '1100-3', '15L Slant-PRO']:
            if self.machine in ['770', '1100-3']:
                hal_file = self.mill_hal
            else:
                hal_file = self.lathe_hal
            with open(hal_file, 'r') as file:
                text = file.read()
                if not 'PathPirate' in text:
                    self.machine_info.insert(tk.END, 'Machine Model is {}. No servos or PathPirate config mods present. Unable to proceed.'.format(self.machine), 'red')
                    return
            self.machine_info.insert(tk.END, 'Machine Model is: {}'.format(self.machine))
            self.gpio = '024'
        elif self.machine in ['770M+', '770MX', '1100M+', '1100MX']:
            self.machine_info.insert(tk.END, 'Machine Model is: {}'.format(self.machine))
            self.gpio = '023'
        else:
            self.machine_info.insert(tk.END, 'Machine Model {} is unsupported. Unable to proceed.\n'.format(self.machine), 'red')
            return
        if self.machine_class == 'lathe' or self.rapid_turn:
            self.brake_axis = 'x'
        elif self.machine_class == 'mill' and not self.rapid_turn:
            self.brake_axis = 'z'
        #keeps the upcoming dialogs on top
        self.main.lower()
        out, err = self.send_commands(self.halcmd, 'gets', self.estop_signal)
        if err.strip() != '':
            tkMessageBox.showinfo('ERROR', 'PathPilot is not running.\n\nRestart this program after starting PathPilot.')
            return
        if out.strip() == 'TRUE':
            try_again = tkMessageBox.askokcancel('ERROR', 'PathPilot must be in E-STOP state (RESET blinking).\n\nE-STOP the machine and press OK to try again.')
            if not try_again:
                return
            out, err = self.send_commands(self.halcmd, 'gets', self.estop_signal)
            if out.strip() != 'FALSE':
                try_again = tkMessageBox.showinfo('ERROR', 'PathPilot must be in E-STOP state (RESET blinking).\n\nE-STOP the machine and restart this program to try again.')
                return
        out, err = self.send_commands(self.halcmd, 'getp', 'tormach.machine-ok')
        if out.strip() != 'TRUE':
            try_again = tkMessageBox.askokcancel('ERROR', 'Machine must be powered ON.\n\nFollow these steps:\n1. Reset physical E-STOP.\n2. Press green button.\n3. Do not click RESET in PathPirate.\n4. Press OK to try again.')
            if not try_again:
                return
            out, err = self.send_commands(self.halcmd, 'getp', 'tormach.machine-ok')
            if out.strip() != 'TRUE':
                try_again = tkMessageBox.showinfo('ERROR', 'Machine must be powered ON.\n\nFollow these steps:\n1. Reset physical E-STOP.\n2. Press green button.\n3. Do not click RESET in PathPirate.\n4. Restart this program to try again.')
                return
        # check for board type
        for board in ['5i25', '7i92', '7i92T', 'EMC1']:
            out, err = self.send_commands(self.halcmd, 'getp', 'hm2_{}.0.gpio.001.out'.format(board))
            if out.strip() != '':
                self.board = board
                self.board_info.insert(tk.END, 'Machine Board is: {}'.format(self.board))
                break
        if self.board == '':
            self.board_info.insert(tk.END, 'ERROR: Unable to determine machine board type! Unable to proceed!', 'red')
            return
        warning_message = '''
MANUALLY CONTROLLING THE SERVO BRAKE CAN BE EXTREMELY DANGEROUS!

ENSURE THAT THE SERVO MOTOR IS UNDER THE CONTROL OF THE TEKNIC
AUTO-TUNE SOFTWARE BEFORE RELEASING THE SERVO BRAKE.

THE USE OF CRIBBING PLACED IN THE APPROPRIATE MANNER/POSITION
IS RECOMMENDED TO PREVENT THE Z AXIS FROM FREE FALLING.

ENSURE YOU UNDERSTAND THE RISKS AND TAKE THE PROPER STEPS TO MITIGATE THEM.

THE AUTHOR OF THIS SOFTWARE ACCEPTS NO RESPONSIBLITY WHATSOEVER FOR
ANY DAMAGES OR INJURIES INCURRED FROM THE USE OF THIS SOFTWARE.

BY CLICKING "OK" YOU AGREE.'''
        warning = tkMessageBox.askokcancel('END USER WARNING AGREEMENT', warning_message)
        if not warning:
            self.console.insert(tk.END, warning_message, 'bold')
            self.console.insert(tk.END, '\n\nUSER DECLINED\n', 'bold_red')
            return
        self.release_brake_button['state'] = 'normal'
        self.console.insert(tk.END, warning_message, 'bold')
        self.console.insert(tk.END, '\n\nUSER AGREED\n', 'bold_green')

    def send_commands(self, *args):
        state = Popen(args, stdout=PIPE, stderr=PIPE)
        out, err = state.communicate()
        return out, err

    # Exit the program
    def exit_servo_brake(self):
        exit = tkMessageBox.askokcancel('EXIT', 'Are you sure?')
        if not exit:
            return
        self.main.destroy()

    def exit_pass(self):
        pass

if __name__ == '__main__':
    app = ServoBrake()