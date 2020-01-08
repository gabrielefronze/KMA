#! /usr/bin/env python3

import argparse
import satellite

print("1: "+satellite.logDir)
satellite.setLogDir("./testlog")
print("2: "+satellite.logDir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This is a process wrapper wich adds a myproxy retrieval satellite by default.')
    parser.add_argument("main", type=str, help="Provide the main process launch command as a string (surrounded by quotes).")
    parser.add_argument("--name", "-n", type=str, help="Provide a custom name for the pipeline process wrapper.")
    parser.add_argument("--passw", "-p", type=str, help="Provide the myproxy password.", required=True)
    parser.add_argument("--voms", "-m", type=str, help="Provide the VOMS handle to add VOMS extensions to your certificate.")

    args = parser.parse_args()

    if args.name:
        mainExe = satellite.makeWrapper(args.main, customName = "pipeline")
    else:
        mainExe = satellite.makeWrapper(args.main, customName = args.name)

    if args.voms:
        sideExes = [satellite.makeWrapper("echo {} | myproxy-logon -d -S --voms {} -t 1 @ 3400".format(args.passw, args.voms), mainExe.is_alive, customName = "myproxy-logon")]
    else:
        sideExes = [satellite.makeWrapper("echo {} | myproxy-logon -d -S -t 1 @ 3400".format(args.passw), mainExe.is_alive, customName = "myproxy-logon")]

    satellite.main(mainExe, sideExes)
    
    