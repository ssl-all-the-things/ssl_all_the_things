''' initiate django shizzle '''
from django.core.management import setup_environ
import server.settings

setup_environ(server.settings)

from django.db import models
from server.work.models import Certificate

import M2Crypto
import pprint

json = {}
json['ext'] = {}

certs = Certificate.objects.all()[:5]
for x509 in certs:
	# http://www.heikkitoivonen.net/m2crypto/api/M2Crypto.X509-module.html
	cert = M2Crypto.X509.load_cert_string(str(x509.pem))
	#cert = M2Crypto.X509.load_cert('tumblr.pem')

	# http://www.heikkitoivonen.net/m2crypto/api/M2Crypto.X509.X509-class.html
	json['issuer'] = cert.get_issuer().as_text()
	json['subject'] = cert.get_subject().as_text()

	# http://www.heikkitoivonen.net/m2crypto/api/M2Crypto.X509.X509-class.html#get_fingerprint
	json['fingerprint'] = cert.get_fingerprint()

	# http://www.heikkitoivonen.net/m2crypto/api/M2Crypto.RSA.RSA_pub-class.html
	json['pub_key_len'] = cert.get_pubkey().get_rsa().__len__()
	json['pub_key'] = cert.get_pubkey().get_rsa().as_pem()

	# http://www.heikkitoivonen.net/m2crypto/api/M2Crypto.ASN1.ASN1_UTCTIME-class.html
	json['not_before'] = cert.get_not_before().get_datetime()
	json['not_after'] = cert.get_not_after().get_datetime()

	# http://www.heikkitoivonen.net/m2crypto/api/M2Crypto.X509.X509_Extension-class.html
	count = cert.get_ext_count()
	for i in range(0, count):
		json['ext'][cert.get_ext_at(i).get_name()] = cert.get_ext_at(i).get_value()

	pprint.pprint(json)