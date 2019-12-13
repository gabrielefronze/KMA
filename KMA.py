#!/usr/bin/python

import subprocess, threading
import time, os
from datetime import datetime
from typing import List
import argparse

logDir="./var/log/KMA"
try:
    os.stat(logDir)
except:
    os.makedirs(logDir)  

class subprocessWrapper:
    def __init__(self, executableString, trigger=None, pollingInterval=1, runInBackground=False):
        self.args = executableString.split()
        self.process = None
        self.trigger = trigger
        self.pollingInterval = pollingInterval
        self.runInBackground = runInBackground
        self.thread = None
        self.calls = 0
        self.stdout = open(logDir+'/'+self.args[0]+".log", "w")
        self.stderr = open(logDir+'/'+self.args[0]+".err", "w")
        self.ready = True

    def __del__(self):
        self.stderr.close()
        self.stdout.close()

    def switchRunInBackground(self):
        self.runInBackground = not self.runInBackground
    
    def run(self):
        print("Process launched: {}".format(' '.join(self.args)))
        self.process = subprocess.run(self.args, \
                                       stdout=self.stdout, \
                                       stderr=self.stderr, errors=True, \
                                       check=True, shell=self.runInBackground)
        self.ready = False

    def runOnTop(self):
        print("Launching main process.")
        self.process = subprocess.run(self.args)

    def autorun(self):
        if self.trigger is None:
            print("Trigger undefined. Running once and waiting for completion.")
            self.run()
            self.ready = False
        else:
            print("Trigger defined.")
            while self.trigger():
                self.calls+=1
                self.stdout.write("+++ call {} {}+++\n".format(self.calls, datetime.now().strftime("%m/%d/%Y, %H:%M:%S")))
                self.stdout.flush()
                self.stderr.write("+++ call {} {}+++\n".format(self.calls, datetime.now().strftime("%m/%d/%Y, %H:%M:%S")))
                self.stderr.flush()
                print("Running call {} and waiting {} seconds.".format(self.calls, self.pollingInterval))
                self.run()
                time.sleep(self.pollingInterval)
            print("Main process ended, stopping.")
            self.ready = False

    def is_alive(self):
        try:
            return self.thread.is_alive() or self.ready
        except:
            return self.ready


def main(mainExecutable: subprocessWrapper, sideExecutables:  List[subprocessWrapper]):
    for exe in sideExecutables:
        threading.Thread(target=exe.autorun).start()
    
    if mainExecutable.runInBackground == True:
        mainExecutable.switchRunInBackground()
    mainExecutable.autorun()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='KMA is a command wrapper able to maintain satellite processes as long as the main process is alive.')
    parser.add_argument("--m", required=True, type=str, help="Provide the main process launch command as a string (surrounded by '').")
    parser.add_argument("--s", type=str, help="Provide comma separed launch commands for the satellite processes.")

    args = parser.parse_args()

    print(args)

    mainExe = subprocessWrapper(args.m)
    sideExes = map(lambda x: subprocessWrapper(x, mainExe.is_alive, 1, True), args.s.split(','))
    
    main(mainExe, sideExes)