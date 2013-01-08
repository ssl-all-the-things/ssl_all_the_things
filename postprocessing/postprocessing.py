#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb
import sys, os
import M2Crypto
import ConfigParser
from M2Crypto import X509, EVP, RSA, ASN1
import multiprocessing as mp

class PostProcessing(object):
    db = None

    def __init__(self, conffile='postprocessing.conf'):
        self.conffile = conffile
        try:
            self.load_configuration()
        except:
            print "Error: Could not initialize PostProcessing() because of a configuration file failure"
            sys.exit(1)

        try:
            self.load_database()
        except:
            print "Error: Could not load database"
            sys.exit(1)

    def load_configuration(self):
        print 'load %s' % self.conffile
        try:
            if not os.path.exists(self.conffile):
                print "Could not open the configuration file \"%s\"" % self.conffile
                raise
        except:
            raise

        config = ConfigParser.RawConfigParser()
        try:
            config.read(self.conffile)
        except:
            print "Error in configuration file: Syntax error. Please fix the configuration file to be a proper .ini style config file"
            raise

        try:
            self.username = config.get('settings', 'username').strip()
            self.password = config.get('settings', 'password').strip()
            self.database = config.get('settings', 'database').strip()
            self.hostname = config.get('settings', 'hostname').strip()
            self.unixsock = config.get('settings', 'unixsock').strip()
        except:
            print "Something was missing from the config file"

    def load_database(self):
        try:
            self.db = MySQLdb.connect(host = self.hostname,
                                      unix_socket = self.unixsock,
                                      user = self.username,
                                      passwd = self.password,
                                      db = self.database)
        except:
            raise


#def is_a_ca():
#    # do stuff
#        return result


#if __name__=='__main__':
#    pool = mp.Pool()
#    results=pool.map(NOT_leakSomeMemory, range(50000000))


foo = PostProcessing()
#cur = foo.db.cursor()
cur = foo.db.cursor(cursorclass=MySQLdb.cursors.SSCursor)
cur.execute("select * from work_certificate")

total_count = 0
ca_count = 0
eec_count = 0



# Fetch!
row = cur.fetchone()
while row:
    if (total_count % 1000000) == 0:
        sys.stdout.write('.')
        sys.stdout.flush()

    # load cert
    try:
        x509 = X509.load_cert_string(row[3])
        if x509.check_ca():
            ca_count += 1
        else:
            eec_count += 1
    except:
        pass

#    #print x509.as_text()
#    try:
#        subjectAltName = x509.get_ext('subjectAltName').get_value()
#
#        for san in subjectAltName.split(", "):
#            print san.split(":")[0], san.split(":")[1]
#    except:
#        pass

    total_count += 1
    try:
        row = cur.fetchone()
        continue
    except:
        pass
        break


print "CA : %d / %d" % (ca_count, total_count)
print "EEC: %d / %d" % (eec_count, total_count)


if foo.db:
    foo.db.close()

