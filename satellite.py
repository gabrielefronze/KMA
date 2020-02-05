#! /usr/bin/env python3

import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

import subprocess, threading, time, os, argparse
from datetime import datetime
from typing import List
from argparse import RawTextHelpFormatter

logDir="./var/log/satellite/"
def setLogDir(path):
    if not path[-1]=='/':
        path = path + '/'
    global logDir
    logDir = path
    try:
        os.stat(logDir)
    except:
        os.makedirs(logDir)
def getLogDir():
    return logDir

verbose=False

mainThreadEnded = threading.Event()

class subprocessWrapper:
    def __init__(self, executableString, trigger=None, pollingInterval=1, runInBackground=False, customName=None):
        self.args = executableString
        self.process = None
        self.trigger = trigger
        self.pollingInterval = pollingInterval
        self.runInBackground = runInBackground
        self.thread = None
        self.calls = 0
        if self.runInBackground:
            if not customName:
                self.stdout = open(getLogDir()+self.args[0].replace('/','_')+".satellite.log", "w")
                self.stderr = open(getLogDir()+self.args[0].replace('/','_')+".satellite.err", "w")
            else:
                self.stdout = open(getLogDir()+customName+".satellite.log", "w")
                self.stderr = open(getLogDir()+customName+".satellite.err", "w")
        else:
            self.stdout = sys.stdout
            self.stderr = sys.stderr
        self.ready = True

    def __del__(self):
        if self.runInBackground:
            self.stderr.close()
            self.stdout.close()

    def switchRunInBackground(self):
        self.runInBackground = not self.runInBackground

    def run(self):
        if verbose:
            print("Process launched: {}".format(' '.join(self.args)))
        self.process = subprocess.run(self.args, \
                                        stdout=self.stdout, \
                                        stderr=self.stderr, \
                                        errors=True, \
                                        check=True, \
                                        shell=True)
        self.ready = False

    def runOnTop(self):
        if verbose:
            print("Launching main process.")
        self.process = subprocess.run(self.args, errors=True, check=True, shell=True)
        self.ready = False

    def runOnBg(self):
        if self.trigger is None:
            if verbose:
                print("Trigger undefined. Running once and waiting for completion.")
            self.run()
            self.ready = False
        else:
            if verbose:
                print("Trigger defined.")
            while self.trigger():
                self.calls+=1
                self.stdout.write("+++ call {} {}+++\n".format(self.calls, datetime.now().strftime("%m/%d/%Y, %H:%M:%S")))
                self.stdout.flush()
                self.stderr.write("+++ call {} {}+++\n".format(self.calls, datetime.now().strftime("%m/%d/%Y, %H:%M:%S")))
                self.stderr.flush()
                if verbose:
                    print("Running call {} and waiting {} seconds.".format(self.calls, self.pollingInterval))
                self.run()
                mainThreadEnded.wait(timeout=self.pollingInterval)
            if verbose:
                print("Main process ended, stopping.")
            self.ready = False

    def is_alive(self):
        try:
            return self.thread.is_alive() or self.ready
        except:
            return self.ready


def main(mainExecutable, sideExecutables):
    threads = []
    for exe in sideExecutables:
        threads.append(threading.Thread(target=exe.runOnBg))
        threads[-1].start()
    
    if verbose:
        if mainExecutable.runInBackground == True:
            mainExecutable.switchRunInBackground()
        mainExecutable.runOnBg()
    else:
        mainExecutable.runOnTop()

    mainThreadEnded.set()

    

def makeWrapper(x, trigger = None, customName = None):
    if ' @ ' in x:
        y=x.split(' @ ')
        print("Command '{}' to be run every {} seconds.".format(y[0],y[1]))
        if customName:
            return subprocessWrapper(y[0].lstrip().rstrip(), trigger, int(y[1].lstrip().rstrip()), True, customName = customName)
        else:
            return subprocessWrapper(y[0].lstrip().rstrip(), trigger, int(y[1].lstrip().rstrip()), True)
    else:
        if trigger:
            print("Command '{}' to be run every second.".format(x))
        else:
            print("Command '{}' to be run as main process.".format(x))

        if customName:
            return subprocessWrapper(x, trigger, 1, True, customName = customName)
        else:
            return subprocessWrapper(x, trigger, 1, True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='satellite is a command wrapper able to maintain satellite processes as long as the main process is alive.', formatter_class=RawTextHelpFormatter)

    parser.add_argument("-s", "--satellites", type=str, help="Provide comma separed launch commands for the satellite processes as strings.\n\Optional: add polling interval in seconds after ' @ '.\n\n\te.g. -s ls <-- run ls every second\n\te.g. -s 'ls @ 5,pwd' <-- run ls every 5 seconds and pwd every second\n\te.g. -s 'ls @ 5, pwd @ 10' <-- run ls every 5 seconds and pwd every 10 seconds\n\n")

    parser.add_argument("-l", "--logdir", type=str, help="Optional logdir. Default '{}'.\n\n".format(logDir))

    parser.add_argument("-v", "--verbose", action='store_true', help="Enable verbose output.\n\n")

    parser.add_argument("main", type=str, help="Provide the main process launch command as a string (surrounded by '').\n\n\te.g. python satellite.py sleep 10\n\te.g. python satellite.py ./test_script.sh\n\n")

    args = parser.parse_args()

    if args.logdir is not None:
        logDir = args.logdir

    if args.verbose is not None:
        verbose=args.verbose

    setLogDir('./')

    mainExe = subprocessWrapper(args.main)

    if args.satellites:
        sideExes = map(lambda x: makeWrapper(x, mainExe.is_alive), args.satellites.split(','))
        main(mainExe, sideExes)
    else:
        main(mainExe, [])