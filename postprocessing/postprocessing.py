#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb
import sys, os
import re
import time,datetime
from time import strptime
from datetime import datetime
import ConfigParser
import M2Crypto
from M2Crypto import X509, EVP, RSA, ASN1
import multiprocessing
from multiprocessing import Process, Pool
import hashlib


def __m2CryptoUTC2datetime(m2CryptoUTC):
    """Convert M2Crypto UTC time string as returned by get_not_before/
       get_not_after methods into datetime type"""

    datetimeRE = "([a-zA-Z]{3} {1,2}\d{1,2} \d{2}:\d{2}:\d{2} \d{4}).*"
    sM2CryptoUTC = None

    try:
        # Convert into string
        sM2CryptoUTC = str(m2CryptoUTC)

        # Check for expected format - string may have trailing GMT - ignore
        sTime = re.findall(datetimeRE, sM2CryptoUTC)[0]

        # Convert into a tuple
        lTime = strptime(sTime, "%b %d %H:%M:%S %Y")[0:6]

        return datetime(lTime[0], lTime[1], lTime[2],
                lTime[3], lTime[4], lTime[5])

    except Exception, e:
        msg = "Error parsing M2Crypto UTC"
        if sM2CryptoUTC is not None:
            msg += ": " + sM2CryptoUTC

        raise


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

        self.load_tables()

    def create_meta_cert(self):
        q = "CREATE TABLE meta_cert(" \
            "cert_id INT NOT NULL,"\
            "signer_cert_id INT,"\
            "version INT,"\
            "subject_dn VARCHAR(500),"\
            "issuer_dn VARCHAR(500),"\
            "serial_nr VARCHAR(100),"\
            "ca BOOLEAN,"\
            "not_before DATETIME,"\
            "not_after DATETIME,"\
            "digest VARCHAR(64),"\
            "pubkey LONGTEXT,"\
            "pubkey_length INT,"\
            "replica INT,"\
            "PRIMARY KEY (cert_id)"\
            ")"

        cur = self.db.cursor()
        try:
            cur.execute(q)
        except:
            print "Failed to add a new table"
            raise

    def create_meta_cert_san(self):
        q = "CREATE TABLE meta_cert_san(" \
            "cert_id INT NOT NULL,"\
            "san_type VARCHAR(30),"\
            "san_value VARCHAR(512),"\
            "digest VARCHAR(64),"\
            "order_num INT,"\
            "PRIMARY KEY (cert_id, digest)"\
            ")"

        cur = self.db.cursor()
        try:
            cur.execute(q)
        except:
            print "Failed to add a new table"
            raise

    def create_meta_cert_ext(self):
        q = "CREATE TABLE meta_cert_ext(" \
            "cert_id INT NOT NULL,"\
            "ext_name VARCHAR(25),"\
            "ext_value LONGTEXT,"\
            "digest VARCHAR(64),"\
            "order_num INT,"\
            "PRIMARY KEY (cert_id, digest)"\
            ")"

        cur = self.db.cursor()
        try:
            cur.execute(q)
        except:
            print "Failed to add a new table"
            raise

    def load_tables(self):
        has_meta_cert = False
        has_meta_cert_san = False
        has_meta_cert_ext = False

        cur = self.db.cursor()
        cur.execute("SHOW TABLES")
        row = cur.fetchone()
        while row:
            if row[0] == "meta_cert":
                has_meta_cert = True

            if row[0] == "meta_cert_san":
                has_meta_cert_san = True

            if row[0] == "meta_cert_ext":
                has_meta_cert_ext = True

            try:
                row = cur.fetchone()
            except:
                row = None
                pass

        if not has_meta_cert:
            print "Creating \"meta_cert\"";
            self.create_meta_cert()
        if not has_meta_cert_san:
            print "Creating \"meta_cert_san\"";
            self.create_meta_cert_san()
        if not has_meta_cert_ext:
            print "Creating \"meta_cert_ext\"";
            self.create_meta_cert_ext()

    def load_configuration(self):
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


def quotify(s):
    return "\"" + s + "\""



def insert_meta_cert(pp, x509, cert_id):
    try:
        not_before = __m2CryptoUTC2datetime(x509.get_not_before())
    except:
        not_before = "NULL"

    try:
        not_after  = __m2CryptoUTC2datetime(x509.get_not_after())
    except:
        not_after = "NULL"

    try:
        q = "INSERT INTO meta_cert "\
                       "(cert_id, version,"\
                        "subject_dn, issuer_dn, serial_nr, ca, "\
                        "not_before, not_after, "\
                        "digest, "\
                        "pubkey, pubkey_length, replica) "\
                "VALUES (%d, %d,"\
                        "%s, %s, %s, %d,"\
                        "%s, %s,"\
                        "%s,"\
                        "%s, %d, NULL)" % \
                       (cert_id, x509.get_version(), \
                        quotify(MySQLdb.escape_string(str(x509.get_subject()))), quotify(MySQLdb.escape_string(str(x509.get_issuer()))), quotify(MySQLdb.escape_string(str(x509.get_serial_number()))), x509.check_ca(),\
                        quotify(str(not_before)), quotify(str(not_after)),\
                        quotify(x509.get_fingerprint('sha1')),\
                        quotify(MySQLdb.escape_string(x509.get_pubkey().get_rsa().as_pem())), len(x509.get_pubkey().get_rsa())\
                       )
    except:
        print "Error (insert_meta_cert): Conversion error in INSERT statement."
        return

    try:
        cur = pp.db.cursor()
        cur.execute(q)
        pp.db.commit()
    except MySQLdb.Error, e:
        errnum = e.args[0]
        # Skip/ignore the duplicate error, error
        if errnum == 1062:
            pass
        else:
            print "Error (insert_meta_cert): Unable to execute or commit(): %d: %s" % (e.args[0], e.args[1])
#        print q
            pass

def insert_meta_cert_san(pp, x509, cert_id):
    ### Subject Alt Names
    try:
        subjectAltName = x509.get_ext('subjectAltName').get_value()
    except:
        pass
        return

    order_num = 0
    for san in subjectAltName.split(", "):
        san_type = san.split(":")[0]
        san_value = san.split(":")[1]

        m = hashlib.sha256()
        m.update(san_type)
        m.update(san_value)
        digest = m.hexdigest()

        q = "INSERT INTO meta_cert_san "\
                       "(cert_id, san_type, san_value, order_num, digest)"\
                "VALUES (%d,      \"%s\",   \"%s\",    %d,        \"%s\")" % \
                        (cert_id, MySQLdb.escape_string(san_type),
                                            MySQLdb.escape_string(san_value),
                                                       order_num, digest)
        order_num += 1
        cur = pp.db.cursor()
        try:
            cur.execute(q)
            pp.db.commit()
        except MySQLdb.Error, e:
            errnum = e.args[0]
            # Skip/ignore the duplicate error, error
            if errnum == 1062:
                pass
            else:
                print "Error (insert_meta_cert_san): Unable to execute or commit(): %d: %s" % (e.args[0], e.args[1])
                pass


def insert_meta_cert_ext(pp, x509, cert_id):
    count = x509.get_ext_count()

    for i in range(0, count):
        ext_name = x509.get_ext_at(i).get_name()
        ext_value = x509.get_ext_at(i).get_value()

        m = hashlib.sha256()
        m.update(ext_name)
        m.update(ext_value)
        digest = m.hexdigest()

        q = "INSERT INTO meta_cert_ext "\
                       "(cert_id, ext_name, ext_value, digest, order_num) "\
                "VALUES (%d,      \"%s\",   \"%s\",    \"%s\", %d)" % \
                        (cert_id, MySQLdb.escape_string(ext_name),
                                            MySQLdb.escape_string(ext_value), digest, i)
        cur = pp.db.cursor()
        try:
            cur.execute(q)
            pp.db.commit()
        except MySQLdb.Error, e:
            errnum = e.args[0]
            # Skip/ignore the duplicate error, error
            if errnum == 1062:
                continue
            else:
                print "Error (insert_meta_cert_ext): Unable to execute or commit(): %d: %s" % (e.args[0], e.args[1])
                continue


def cert_process(rows):
    try:
        my_pp = PostProcessing()
    except:
        print "Could not connect to the database"
        return

    for row in rows:
        cert_id = row[0]
        pem = row[3]
        try:
            x509 = X509.load_cert_string(pem)
        except:
            pass
            return

        #print x509.as_text()

        try:
            insert_meta_cert(my_pp, x509, int(cert_id))
            insert_meta_cert_san(my_pp, x509, int(cert_id))
            insert_meta_cert_ext(my_pp, x509, int(cert_id))
        except:
            print "Something happened with cert_id %d" % int(cert_id)
            pass

    try:
        my_pp.db.close()
    except:
        print "Failed to close db connection"
        pass




#############################################################
if __name__ == '__main__':
    total_count = 0
    ca_count = 0
    eec_count = 0

    arraysize = 100
    debug = False
    debug = True


    # Fetch!
    if debug:
        print "Debug mode"
    else:
        print "Production mode"
        cpus = multiprocessing.cpu_count()
        print "Detected %d CPUs" % cpus
        pool = Pool(processes=cpus)              # start 4 worker processes

    postproc = PostProcessing()
    cur = postproc.db.cursor(cursorclass=MySQLdb.cursors.SSCursor)

    if debug:
        #cur.execute("SELECT * FROM work_certificate LIMIT 1000000")
        #cur.execute("SELECT * FROM work_certificate LIMIT 200")
        cur.execute("SELECT * FROM work_certificate")
    else:
        cur.execute("SELECT * FROM work_certificate")

    while True:
        try:
            rows = cur.fetchmany(arraysize)
            if not rows:
                break
        except:
            print "Couldn't fetch more records. I'm at %d" % total_count
            pass
            break

        if debug:
            cert_process(rows)
        else:
            pool.apply_async(cert_process, (rows,))

        total_count += arraysize

    try:
        cur.close()
    except:
        print "Failed to close the cursor"
        pass


print "Total certificates processed: %d" % total_count

try:
    if postproc.db:
        postproc.db.close()
except:
    print "Failed to close the database"
    pass

