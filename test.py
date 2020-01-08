#! /usr/bin/env python3

from satellite import verbose, logDir, setLogDir

if __name__ == "__main__":
    print(logDir)
    logDir = "pippo"
    setLogDir()
    print(logDir)