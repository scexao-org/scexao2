#!/usr/bin/env python
import serial
import os
import time
import sys
import subprocess
home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')
import logit #Custom logging library


def step2zaberByte(nstep):
    step = nstep        # local version of the variable
    zbytes = [int(0),int(0),int(0),int(0)]  # series of four bytes for Zaber
    if step < 0: step += 256**4
    for i in range(3,-1,-1):
        zbytes[i] = step // 256**i
        step     -= zbytes[i] * 256**i
    return zbytes
                                                     
def zaberByte2step(zb):
    nstep = 0
    for i in range(len(zb)):
        nstep += zb[i]*256**i
        if i == 3:
            if zb[3] > 127: nstep -= 256**4
        
    return nstep

def zab_cmd(cmd):
    nl = []
    instr = list(map(int, cmd.split(' ')))

    for c in instr:
        if c == 255: nl.extend([c,c])
        else:        nl.append(c)

    buf = ''.join(list(map(chr, nl)))
    return buf.encode('latin-1')

class zaber:
    def __init__(self):
        self.s = None

    def open(self, zaberchain, dev_override=None):
        if dev_override is None:
            filename = "/home/scexao/bin/devices/conf/path_zabchain_"+zaberchain+".txt"
            filep = open(filename, 'r')
            self.dev  = "/dev/serial/"
            self.dev += filep.read().rstrip('\n')
        else:
            self.dev = dev_override

        try:
            self.s = serial.Serial(self.dev, 9600, timeout=0.5)
            dummy = self.s.readlines() # flush the port
        except:
            print("Zaber chain %s not connected" %zaberchain)
            sys.exit()

    def home(self, idn, devname, log=True):
        self.command(idn, 1, 0)
        if log:
            logit.logit(devname,'Homed')

    def move(self, idn, pos, devname, log=True, delay=0.1):
        self.command(idn, 20, pos)
        time.sleep(delay)
        if log:
            logit.logit(devname,'moved_to_'+str(pos))
        
    def push(self, idn, step, devname, log=True, delay=0.1):
        self.command(idn, 21, step)
        time.sleep(delay)
        if log:
            logit.logit(devname,'moved_rel_'+str(step))
      
    def status(self, idn, devname):
        pos = self.command(idn, 60, 0)
        subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname, str(pos)])
        return pos

    def command(self, idn, cmd, arg, quiet=True):
        args = ' '.join(map(str, step2zaberByte(int(arg))))
        full_cmd = '%s %d %s' % (idn, cmd, args)
        #if not quiet:
        self.s.write(zab_cmd(full_cmd))
        for k in range(8):
            dummy = self.s.readline()
            if dummy != ''.encode():
                break
            time.sleep(0.1)
        reply=''
        if len(dummy) > 2:
            reply = zaberByte2step(dummy[2:])
        if not quiet:
            print("zaber %d = %d" % (int(idn), reply))
        return(reply)

    def close(self):
        self.s.close()
