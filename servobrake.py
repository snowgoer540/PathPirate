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
from subprocess import call as CALL
from subprocess import Popen, PIPE
import os
import json

class ServoBrake:

    def __init__(self):
        # set up the main window
        self.main = tk.Tk()
        self.main.title("PathPirate Servo Brake Release Tool v1.0")
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
        self.exit_button = tk.Button(self.button_frame, text='EXIT', command=self.exit_path_pirate, height=2, padx=5)
        self.exit_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # set up output text boxes
        self.machine_info = tk.Text(self.version_frame, padx=5, height=1, bg='black', fg='yellow', highlightthickness=0, bd=0)
        self.machine_info.pack(fill=tk.BOTH, expand=True)
        self.machine_info.tag_configure('red', foreground='red')
        self.current_version_info = tk.Text(self.version_frame, padx=5, height=1, bg='black', fg='yellow', highlightthickness=0, bd=0)
        self.current_version_info.pack(fill=tk.BOTH, expand=True)
        self.current_version_info.tag_configure('red', foreground='red')
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

        os.chdir(self.halcmd_folder)

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
    def release_brake(self, event=None):
        self.console.insert(tk.END, '\nRELEASING SERVO BRAKE', 'yellow')
        try:
            if self.board:
                CALL([self.halcmd, 'unlinkp', 'hm2_{}.0.pwmgen.00.enable'.format(self.board)])
                CALL([self.halcmd, 'setp', 'hm2_{}.0.pwmgen.00.enable'.format(self.board), 'true'])
            CALL([self.halcmd, 'unlinkp', 'hm2_{}.0.gpio.{}.out'.format(self.board, self.gpio)])
            CALL([self.halcmd, 'setp', 'hm2_{}.0.gpio.{}.out'.format(self.board, self.gpio), 'true'])
        except Exception as e:
            self.console.insert(tk.END, '\nThe following system error has occured:\n{}\n'.format(e), 'red')
            self.release_brake_button['state'] = 'disabled'
            return
        self.console.insert(tk.END, ' - servo must be re-engaged before program may be exited.\n', 'cyan')
        self.release_brake_button['state'] = 'disabled'
        self.exit_button['state'] = 'disabled'
        self.engage_brake_button['state'] = 'normal'
        self.console.see(tk.END)

    # Engage the servo brake (de-energize the coil)
    # Brake is gpio.023 on EMCV1.5 machines
    def engage_brake(self, event=None):
        self.console.insert(tk.END, '\nENGAGING SERVO BRAKE\n', 'orange')
        self.exit_button['state'] = 'normal'
        self.engage_brake_button['state'] = 'disabled'
        try:
            CALL([self.halcmd, 'setp', 'hm2_{}.0.gpio.{}.out'.format(self.board, self.gpio), 'false'])
            CALL([self.halcmd, 'linkps', 'hm2_{}.0.gpio.{}.out'.format(self.board, self.gpio), '{}-axis-brake-release'.format(self.brake_axis)])
            if self.board:
                CALL([self.halcmd, 'setp', 'hm2_{}.0.pwmgen.00.enable'.format(self.board), 'false'])
                CALL([self.halcmd, 'linkps', 'hm2_{}.0.pwmgen.00.enable'.format(self.board), 'estop'])
        except Exception as e:
            self.console.insert(tk.END, 'The following system error has occured:\n{}\n'.format(e), 'red')
            return
        self.console.insert(tk.END, ' - servo ready for auto-tuning process.\n', 'cyan')
        self.release_brake_button['state'] = 'normal'
        self.console.see(tk.END)

    # Get the latest version number and machine model
    def get_version(self, event=None):
        if not os.path.exists(self.tmc):
            self.current_version_info.insert(tk.END, 'ERROR: ~/tmc does not exist, is PathPilot installed?\n', 'red')
            return
        if not os.path.exists(self.halcmd_folder):
            self.current_version_info.insert(tk.END, 'ERROR: ~/tmc/bin does not exist, is PathPilot installed?\n', 'red')
            return
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
            self.current_version_info.insert(tk.END, 'ERROR: {} is missing! Unable to proceed!\n'.format(self.version_file), 'red')
            return
        with open(self.version_file, 'r') as json_file:
            version_data = json.load(json_file)
        self.current_ver = version_data['version']
        if not self.current_ver.split('-')[0] in ['v2.9.2', 'v2.9.3', 'v2.9.4', 'v2.9.5', 'v2.9.6', 'v2.10.0']:
            self.current_version_info.insert(tk.END, 'ERROR: PathPirate is not compatible with version {}! Unable to proceed!\n'.format(self.current_ver), 'red')
            return
        self.minorVer = int(self.current_ver.split('.')[1])
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
        if self.machine in ['1100-3', '15L Slant-PRO']:
            if self.machine == '1100-3':
                hal_file = self.mill_hal
            else:
                hal_file = self.lathe_hal
            with open(hal_file, 'r') as file:
                text = file.read()
                if not 'PathPirate' in text:
                    self.machine_info.insert(tk.END, 'Machine Model is {}. No servos or PathPirate config mods present. Unable to proceed.\n'.format(self.machine), 'red')
                    return
            self.machine_info.insert(tk.END, 'Machine Model is: {}\n'.format(self.machine))
            self.gpio = '024'
        elif self.machine in ['770M+', '770MX', '1100M+', '1100MX']:
            self.machine_info.insert(tk.END, 'Machine Model is: {}\n'.format(self.machine))
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
        estop_state, running = self.path_pilot_state()
        if not running:
            error = tkMessageBox.showinfo('ERROR', 'PathPilot is not running.\n\nRestart this program after starting PathPilot.')
            return
        if estop_state.strip() != 'FALSE':
            try_again = tkMessageBox.askokcancel('ERROR', 'Machine must be in E-STOP state.\n\nE-STOP the machine and press OK to try again.')
            if try_again:
                 estop_state, running = self.path_pilot_state()
                 if estop_state.strip() != 'FALSE':
                     try_again = tkMessageBox.showinfo('ERROR', 'Machine must be in E-STOP state.\n\nE-STOP the machine and restart this program.')
                     return
        warning_message = '''
MANUALLY CONTROLLING THE SERVO BRAKE CAN BE EXTREMELY DANGEROUS!

ENSURE THAT THE SERVO MOTOR IS UNDER THE CONTROL OF THE TEKNIC
AUTO-TUNE SOFTWARE BEFORE PROCEEDING.

THE USE OF CRIBBING PLACED IN THE APPROPRIATE MANNER/POSITION
IS RECOMMENDED TO PREVENT THE AXIS FROM FREE FALLING.

ENSURE YOU UNDERSTAND THE RISKS AND TAKE THE PROPER STEPS TO MITIGATE THEM.     

THE AUTHOR OF THIS SOFTWARE ACCEPTS NO RESPONSIBLITY WHATSOEVER FOR
ANY DAMAGES OR INJURIES INCURRED FROM THE USE OF THIS SOFTWARE.'''
        warning = tkMessageBox.askokcancel('WARNING', warning_message)
        if warning:
            self.release_brake_button['state'] = 'normal'
            self.console.insert(tk.END, warning_message, 'bold')
            self.console.insert(tk.END, '\n\nUSER AGREED\n', 'bold_green')
        else:
            self.console.insert(tk.END, warning_message, 'bold')
            self.console.insert(tk.END, '\n\nUSER DECLINED\n', 'bold_red')
            return

        command = Popen([self.halcmd, 'getp', 'hm2_5i25.0.gpio.001.out'], stdout=PIPE, stderr=PIPE)
        out, error = command.communicate()
        if out and not error:
            self.board = '5i25'
            return
        command = Popen([self.halcmd, 'getp', 'hm2_7i92.0.gpio.001.out'], stdout=PIPE, stderr=PIPE)
        out, error = command.communicate()
        if out and not error:
            self.board = '7i92'
            return
        command = Popen([self.halcmd, 'getp', 'hm2_7i92T.0.gpio.001.out'], stdout=PIPE, stderr=PIPE)
        out, error = command.communicate()
        if out and not error:
            self.board = '7i92T'
            return

    def path_pilot_state(self):
        state = Popen([self.halcmd, 'gets', 'estop'], stdout=PIPE, stderr=PIPE)
        estop_state, running = state.communicate()
        return estop_state, running

    # Exits PathPirate and checks if the user would like to reboot automatically
    def exit_path_pirate(self, event=None):
        exit = tkMessageBox.askokcancel('EXIT', 'Are you sure?')
        if exit:
            self.main.destroy()
        else:
            pass

    def exit_pass(self, event=None):
        pass

if __name__ == '__main__':
    app = ServoBrake()