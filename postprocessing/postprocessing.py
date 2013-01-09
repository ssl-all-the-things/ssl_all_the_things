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
            "fingerprint_md5 TEXT,"\
            "fingerprint_sha1 TEXT,"\
            "fingerprint_sha256 TEXT,"\
            "pubkey LONGTEXT,"\
            "pubkey_length INT,"\
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
            "san_value VARCHAR(255),"\
            "order_num INT,"\
            "PRIMARY KEY (cert_id, san_type, san_value)"\
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
            "ext_name VARCHAR(40),"\
            "ext_value VARCHAR(250),"\
            "PRIMARY KEY (cert_id, ext_name, ext_value)"\
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



def cert_process(row):
    try:
        my_pp = PostProcessing()
    except:
        print "Could not connect to the database"
        return

    cert_id = row[0]
    pem = row[3]
    try:
        x509 = X509.load_cert_string(pem)
    except:
        pass
        return

    #print x509.as_text()
    try:
        not_before = __m2CryptoUTC2datetime(x509.get_not_before())
        not_after  = __m2CryptoUTC2datetime(x509.get_not_after())

        q = "INSERT INTO meta_cert "\
                       "(cert_id, version,"\
                        "subject_dn, issuer_dn, serial_nr, ca, "\
                        "not_before, not_after, "\
                        "fingerprint_md5, fingerprint_sha1, fingerprint_sha256, "\
                        "pubkey, pubkey_length) "\
                "VALUES (\"%s\", %d,"\
                        "\"%s\", \"%s\", \"%s\", %d, "\
                        "\"%s\", \"%s\", "\
                        "\"%s\", \"%s\", \"%s\", "\
                        "\"%s\", %d)" % \
                       (cert_id, x509.get_version(), \
                        x509.get_subject(), x509.get_issuer(), str(x509.get_serial_number()), x509.check_ca(),\
                        not_before, not_after,\
                        x509.get_fingerprint('md5'), x509.get_fingerprint('sha1'), x509.get_fingerprint('sha256'),\
                        x509.get_pubkey().get_rsa().as_pem(), len(x509.get_pubkey().get_rsa())\
                       )

#        print q
        cur = my_pp.db.cursor()
        try:
            cur.execute(q)
            my_pp.db.commit()
        except:
            print "Failed to add a new record"
            pass
    except:
        pass

    ### Subject Alt Names
    try:
        subjectAltName = x509.get_ext('subjectAltName').get_value()

        order_num = 0
        for san in subjectAltName.split(", "):
            san_type = san.split(":")[0]
            san_value = san.split(":")[1]

            q = "INSERT INTO meta_cert_san "\
                           "(cert_id, san_type, san_value, order_num)"\
                    "VALUES (%d,      \"%s\",   \"%s\",    %d)" % \
                            (cert_id, san_type, san_value, order_num)
            order_num += 1
#            print q
            cur = my_pp.db.cursor()
            try:
                cur.execute(q)
                my_pp.db.commit()
            except:
                print "Failed to add a new record"
                pass
    except:
        pass


    #### Extentions
    try:
        count = x509.get_ext_count()
        for i in range(0, count):
#            print "[%s]: %s" % (x509.get_ext_at(i).get_name(), x509.get_ext_at(i).get_value())

            ext_name = x509.get_ext_at(i).get_name()
            ext_value = x509.get_ext_at(i).get_value()

            q = "INSERT INTO meta_cert_ext "\
                           "(cert_id, ext_name, ext_value)"\
                    "VALUES (%d,      \"%s\",   \"%s\")" % \
                            (cert_id, ext_name, ext_value)
#            print q
            cur = my_pp.db.cursor()
            try:
                cur.execute(q)
                my_pp.db.commit()
            except:
                print "Failed to add a new record"
                pass
    except:
        pass

    try:
        cur.close()
        my_pp.db.close()
    except:
        print "Failed to close db cursor/connection"
        pass




#############################################################
if __name__ == '__main__':
    total_count = 0
    ca_count = 0
    eec_count = 0

    debug = False
#    debug = True

    # Fetch!
    if not debug:
        cpus = multiprocessing.cpu_count()
        print "Detected %d CPUs" % cpus
        pool = Pool(processes=cpus)              # start 4 worker processes

    foo = PostProcessing()
    cur = foo.db.cursor(cursorclass=MySQLdb.cursors.SSCursor)
    cur.execute("select * from work_certificate")

    row = cur.fetchone()
    while row:
        if debug and total_count == 4:
            cur.close()
            print "Break"
            break

        print total_count

        if (total_count % 1000000) == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

        try:
            if debug:
                cert_process(row)
            else:
                pool.apply_async(cert_process, (row,))
        except:
            pass

        total_count += 1
        try:
            row = cur.fetchone()
            continue
        except:
            pass
            break
    try:
        cur.close()
    except:
        print "Failed to close the cursor"
        pass


print "Total certificates processed: %d" % total_count

try:
    if foo.db:
        foo.db.close()
except:
    print "Failed to close the database"
    pass

