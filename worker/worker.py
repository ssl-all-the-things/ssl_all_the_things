#!/usr/bin/env python

import threading
import sys,os,getopt
import urllib2
import ConfigParser
import datetime
import time
import signal
import subprocess
import math
import uuid
import json
import copy
from subprocess import Popen, PIPE, STDOUT


class IPv4address(object):
    __version = 4
    __oct_a   = None
    __oct_b   = None
    __oct_c   = None
    __oct_d   = None
    __slash   = None
    __lastIP  = None

    def __init__(self, *args):
        if len(args) == 1:
            self.__set_ipv4(args[0])
        elif len(args) == 4:
            self.__oct_a = args[0]
            self.__oct_b = args[1]
            self.__oct_c = args[2]
            self.__oct_d = args[3]
        elif len(args) == 5:
            self.__oct_a = args[0]
            self.__oct_b = args[1]
            self.__oct_c = args[2]
            self.__oct_d = args[3]
            self.__slash = args[4]
            self.__lastIP = self.get_ipv4_last()

    def __set_ipv4(self, ipv4):
        try:
            self.__oct_a = ipv4.split(".")[0]
            self.__oct_b = ipv4.split(".")[1]
            self.__oct_c = ipv4.split(".")[2]
            self.__oct_d = ipv4.split(".")[3]
        except:
            raise

    def __add__(self, other):
        if not isinstance(other, int):
            return NotImplemented

        oct_a = self.__oct_a
        oct_b = self.__oct_b
        oct_c = self.__oct_c
        oct_d = self.__oct_d

        # Count IP address upwards
        for i in xrange(other):
            if oct_d < 255:
                oct_d += 1
            elif oct_c < 255:
                oct_c += 1
                oct_d = 0
            elif oct_b < 255:
                oct_b += 1
                oct_c = 0
                oct_d = 0
            elif oct_a < 255:
                oct_a += 1
                oct_b = 0
                oct_c = 0
                oct_d = 0

        return IPv4address(oct_a, oct_b, oct_c, oct_d)

    def __sub__(self, other):
        if not isinstance(other, int):
            return NotImplemented

    def __gt__(self, other):
        if other == None:
            return False
        o_dict = other.get_ipv4_dict()
        if self.__oct_a > o_dict['oct_a']:
            return True
        elif self.__oct_a < o_dict['oct_a']:
            return False
        else:
            if self.__oct_b > o_dict['oct_b']:
                return True
            elif self.__oct_b < o_dict['oct_b']:
                return False
            else:
                if self.__oct_c > o_dict['oct_c']:
                    return True
                elif self.__oct_c < o_dict['oct_c']:
                    return False
                else:
                    if self.__oct_d > o_dict['oct_d']:
                        return True
                    elif self.__oct_d < o_dict['oct_d']:
                        return False
                    else:
                        # Equal
                        return False

    def __ge__(self, other):
        if other == None:
            return False
        o_dict = other.get_ipv4_dict()
        if self.__oct_a > o_dict['oct_a']:
            return True
        elif self.__oct_a < o_dict['oct_a']:
            return False
        else:
            if self.__oct_b > o_dict['oct_b']:
                return True
            elif self.__oct_b < o_dict['oct_b']:
                return False
            else:
                if self.__oct_c > o_dict['oct_c']:
                    return True
                elif self.__oct_c < o_dict['oct_c']:
                    return False
                else:
                    if self.__oct_d > o_dict['oct_d']:
                        return True
                    elif self.__oct_d < o_dict['oct_d']:
                        return False
                    else:
                        # Equal
                        return True

    def __lt__(self, other):
        if other == None:
            return False
        o_dict = other.get_ipv4_dict()
        if self.__oct_a > o_dict['oct_a']:
            return False
        elif self.__oct_a < o_dict['oct_a']:
            return True
        else:
            if self.__oct_b > o_dict['oct_b']:
                return False
            elif self.__oct_b < o_dict['oct_b']:
                return True
            else:
                if self.__oct_c > o_dict['oct_c']:
                    return False
                elif self.__oct_c < o_dict['oct_c']:
                    return True
                else:
                    if self.__oct_d > o_dict['oct_d']:
                        return False
                    elif self.__oct_d < o_dict['oct_d']:
                        return True
                    else:
                        # Equal
                        return False

    def __le__(self, other):
        if other == None:
            return False
        o_dict = other.get_ipv4_dict()
        if self.__oct_a > o_dict['oct_a']:
            return False
        elif self.__oct_a < o_dict['oct_a']:
            return True
        else:
            if self.__oct_b > o_dict['oct_b']:
                return False
            elif self.__oct_b < o_dict['oct_b']:
                return True
            else:
                if self.__oct_c > o_dict['oct_c']:
                    return False
                elif self.__oct_c < o_dict['oct_c']:
                    return True
                else:
                    if self.__oct_d > o_dict['oct_d']:
                        return False
                    elif self.__oct_d < o_dict['oct_d']:
                        return True
                    else:
                        # Equal
                        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        if other == None:
            return False

        o_dict = other.get_ipv4_dict()
        if other.get_version() == self.__version and \
            o_dict['oct_a'] == self.__oct_a and \
            o_dict['oct_b'] == self.__oct_b and \
            o_dict['oct_c'] == self.__oct_c and \
            o_dict['oct_d'] == self.__oct_d:
            return True
        else:
            return False

    def get_version(self):
        return self.__version

    def get_ipv4(self):
        return "".join([str(self.__oct_a), ".", str(self.__oct_b), ".",
                        str(self.__oct_c), ".", str(self.__oct_d)])

    def get_ipv4_extended(self):
        if self.__slash == None:
            return self.get_ipv4()
        else:
            return self.get_ipv4() + "/" + str(self.__slash)

    def get_ipv4_dict(self):
        res = {}
        res['oct_a']   = self.__oct_a
        res['oct_b']   = self.__oct_b
        res['oct_c']   = self.__oct_c
        res['oct_d']   = self.__oct_d
        res['slash']   = self.__slash
        res['version'] = self.__version
        return res

    def get_ipv4_last(self):
        if self.__slash == None:
            return None

        # Cached answer?
        if self.__lastIP != None:
            return self.__lastIP

        oct_a = self.__oct_a
        oct_b = self.__oct_b
        oct_c = self.__oct_c
        oct_d = self.__oct_d

        rounds = 32 - self.__slash
        for i in xrange(rounds):
            if i < 8:
                oct_d += 2**(i % 8)
            elif i < 16:
                oct_c += 2**(i % 8)
            elif i < 24:
                oct_b += 2**(i % 8)
            else:
                oct_a += 2**(i % 8)

        return IPv4address(oct_a, oct_b, oct_c, oct_d)


class Probe(object):
    __name = None
    __target = None
    __raw_cmdline = None
    __real_cmdline = None
    __raw_dumpdir = None
    __real_dumpdir = None

    def __init__(self, n):
        try:
            self.__name = n
        except:
            raise

    def get_name(self):
        return self.__name

    def set_cmd(self, cmd):
        self.__raw_cmdline = cmd

    def set_target(self, ip):
        self.__target = ip
        self.make_real_dumpdir(self.__raw_dumpdir)
        self.make_cmd()

    def set_raw_dumpdir(self, dir):
        self.__raw_dumpdir = dir

    def make_real_dumpdir(self, dir):
        self.__real_dumpdir = self.__raw_dumpdir + '/' + self.__target.get_ipv4().replace('.', '/')

    def make_cmd(self):
        if self.__target == None:
            return

        octed_dir = self.__target.get_ipv4().replace('.', '/')
        self.__real_cmdline = self.__raw_cmdline

        if self.__raw_cmdline.find('$DIR') >= 0:
            self.__real_cmdline = self.__real_cmdline.replace('$DIR', self.__real_dumpdir)

        if self.__raw_cmdline.find('$HOST') >= 0:
            self.__real_cmdline = self.__real_cmdline.replace('$HOST', self.__target.get_ipv4())

    def info(self):
        print self.__name
        if self.__target != None:
            print self.__target.get_ipv4_extended()
        print self.__raw_cmdline
        print self.__real_cmdline
        print self.__raw_dumpdir
        print self.__real_dumpdir

    def execute(self):
        if not os.path.exists(self.__real_dumpdir):
            os.makedirs(self.__real_dumpdir)

        self.__process = subprocess.Popen(self.__real_cmdline, shell=True, stdout=subprocess.PIPE)

    def is_finished(self):
        self.__process.poll()
        if self.__process.returncode != None:
            print self.__process.returncode
            output = self.__process.stdout.read()
            self.__process.stdout.close()
            return True

        return False


class Work(object):
    __server = 'http://localhost:8000'
    __uuid = None
    __ip_net = None
    __ip_last = None
    __in_progress = []

    def __init__(self, serv):
        self.__server = serv
        self.__uuid = str(uuid.uuid1()).replace('-','')

    def load_work(self, j):
        if j['ipv'] == 6:
            print "Error: IPv6 not yet supported. Better luck next time"
            raise

        if j['ipv'] == 4:
            self.__ip_net = IPv4address(j['oct_a'], j['oct_b'], j['oct_c'], j['oct_d'], j['slash'])

    def get_work(self):
        url = ''.join([self.__server, "?uuid=", self.__uuid])
        try:
            response = urllib2.urlopen(url)
        except:
            print "Error: failed to get work data"
            raise
        resp = response.read()
        j = json.loads(resp)
        self.load_work(j)

    def get_ip_net(self):
        return self.__ip_net

    def __get_highest(self):
        h = None
        for ip in self.__in_progress:
            if h == None:
                h = ip
            elif h < ip:
                h = ip
        return h

    def get_next_ip(self):
        if len(self.__in_progress) == 0:
            # Get IP block
            next = self.get_ip_net() + 1
        else:
            next = self.__get_highest() + 1

        if next == self.get_ip_net().get_ipv4_last():
            return None

        self.__in_progress.append(next)
        return next


class IProbeManager(object):
    probes = []
    conffile = None
    work = None

    def __init__(self, conffile="worker.conf"):
        self.conffile = conffile
        try:
            self.load_configuration()
        except:
            sys.exit(1)

    def load_configuration(self):
        #print 'load_configuration %s' % self.conffile
        try:
            if not os.path.exists(self.conffile):
                print "Could not open the configuration file \'%s\'" % self.conffile
                raise
        except:
            raise

        config = ConfigParser.RawConfigParser()

        try:
            config.read(self.conffile)
        except:
            print "Error in configuration file: Syntax error. Please fix the configuration file to be a proper .ini style config file"
            raise

        if not config.has_section('settings'):
            print "Error in configuration file: Expected section 'settings'"
            raise

        if not config.has_option('settings', 'probes'):
            print "Error in configuration file: Expected option 'probes' in section 'settings'"
            raise

        if not config.has_option('settings', 'workserver'):
            print "Error in configuration file: Expected option 'workserver' in section 'settings'"
            raise

        if not config.has_option('settings', 'dumpdir'):
            print "Error in configuration file: Expected option 'dumpdir' in section 'settings'"
            raise

        # Construct Work
        self.work = Work(config.get('settings', 'workserver'))

        # Construct and load the probes
        self.construct_probes(config.get('settings', 'probes'))
        for i in self.probes:
            if not config.has_section(i.get_name()):
                print "Error in configuration file: Expected a section for probe '%s'" % i.get_name()
                raise

            if not config.has_option(i.get_name(), 'cmd'):
                print "Error in configuration file: Expected option 'exec' in section '%s'" % i.get_name()
                raise

            i.set_cmd(config.get(i.get_name(), 'cmd'))
            i.set_raw_dumpdir(config.get('settings', 'dumpdir'))

    def construct_probes(self, probes):
        tmp_probes = [item.strip() for item in probes.split(',')]
        for item in tmp_probes:
            p = Probe(item)
            self.probes.append(p)

    def exec_probe(self, probe):
        probe.info()
        probe.execute()
        while not probe.is_finished():
            print "Busy"
            time.sleep(0.1)

    def run(self):
        self.work.get_work()

        # Work looper
        while 1:
            next = self.work.get_next_ip()
            if next == None:
                break

            for p in self.probes:
                np = copy.deepcopy(p)
                np.set_target(next)

                self.exec_probe(np)





### MAIN ###

ipm = IProbeManager()
ipm.run()


"""

PROBE_DROP_ROOT="${PROBE_DROP_ROOT:-/tmp/drop_root}"
PROBE_DIR="${PROBE_DIR:-probe.d}"
PROBE_TIMEOUT="${PROBE_TIMEOUT:-4}"

### Helper
function number_is_octet() {
    OCTET=$1

    regex="[0-9]+"
    if [[ "$OCTET" =~ $regex ]]; then
        if [ $OCTET -lt 256 ]; then
            return 0
        fi
    fi
    echo "Error: Input is not an octet for an IP address: $OCTET"
    return 1
}

### Probe activitors
function probe_launcher() {
    PROBE_SCRIPT=$1
    THE_PROBE_TIMEOUT=$2
    PROBE_DROP_OUTPUT_DIR=$3
    IP=$4
    PORT=$5

    ### Launch Probes - Extend if there are more here
    "${PROBE_SCRIPT}" "${PROBE_DROP_OUTPUT_DIR}" "${IP}" $PORT &

    CHILD=$!
    NOW=`date "+%s"`

    while [ 1 ]; do
        kill -0 $CHILD > /dev/null 2>&1 || break

        # When timeout reached
        CURRENT=`date "+%s"`
        SPEND_TIME=$(($CURRENT-$NOW))

        if [ "${SPEND_TIME}" -gt "${THE_PROBE_TIMEOUT}" ]; then
            echo "Warning: Time out reached of ${THE_PROBE_TIMEOUT}"
            kill -15 $CHILD
            sleep 1

            # if still there, kill it 4 real
            kill -0 $CHILD > /dev/null 2>&1 && kill -9 $CHILD
            break
        fi
    done
    wait $CHILD >/dev/null 2>&1
    RC=$?
    return $RC
}


function probe_host() {
    OCTET_1=$1
    OCTET_2=$2
    OCTET_3=$3
    OCTET_4=$4

    IP="${OCTET_1}.${OCTET_2}.${OCTET_3}.${OCTET_4}"

    # Add pre-launch probes, like is there a port 443 alive
    probe_launcher "${PROBE_DIR}/probe_nc_connect.sh" "${PROBE_TIMEOUT}" "${PROBE_DROP_OUTPUT_DIR}" "${IP}" "443" || return 1


    # Make the directory for the results about this host
    PROBE_DROP_OUTPUT_DIR="${PROBE_DROP_ROOT}/${OCTET_1}/${OCTET_2}/${OCTET_3}/${OCTET_4}"

    if [ ! -d "${PROBE_DROP_OUTPUT_DIR}" ]; then
        mkdir -p "${PROBE_DROP_OUTPUT_DIR}" || exit 1
    fi


    ### Launch Probes - Extend if there are more here
    probe_launcher "${PROBE_DIR}/probe_HTTPS.sh" "${PROBE_TIMEOUT}" "${PROBE_DROP_OUTPUT_DIR}" "${IP}"
    RC=$?
    return $RC
}


### MAIN
if [ "$#" != "4" ]; then
    echo "Error: provide me an IP address split over the 4 octets, example: $0 127 0 0 1"
    exit 1
else
    number_is_octet $1 || exit 1
    number_is_octet $2 || exit 1
    number_is_octet $3 || exit 1
    number_is_octet $4 || exit 1
fi

# Engage !
probe_host $1 $2 $3 $4
RC=$?

exit $RC

"""
