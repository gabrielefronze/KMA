import subprocess, threading
import time, os
from typing import List

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
        self.stdout = open(logDir+'/'+self.args[0]+".log", "w+")
        self.stderr = open(logDir+'/'+self.args[0]+".log", "w+")
        self.ready = True

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
        print(self.trigger)
        if self.trigger is None:
            print("Trigger undefined. Running once and waiting for completion.")
            self.run()
            self.ready = False
        else:
            print("Trigger defined.")
            while self.trigger():
                self.calls+=1
                print("Running call {} and waiting {} seconds.".format(self.calls, self.pollingInterval))
                self.run()
                time.sleep(self.pollingInterval)
            print("Main process ended, stopping.")
            self.ready = False

    def is_alive(self):
        try:
            print("Main process running.")
            return self.thread.is_alive()
        except:
            print("Main process ready.")
            return self.ready


def main(mainExecutable: subprocessWrapper, sideExecutables:  List[subprocessWrapper]):
    for exe in sideExecutables:
        threading.Thread(target=exe.autorun).start()
    
    if mainExecutable.runInBackground == True:
        mainExecutable.switchRunInBackground()
    mainExecutable.autorun()

    


if __name__ == "__main__":
    mainExe = subprocessWrapper("bash test_script.sh")
    sideExes = [subprocessWrapper("ls", mainExe.is_alive, 1, True)]
    
    main(mainExe, sideExes)