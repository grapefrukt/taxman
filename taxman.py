import ConfigParser
import itunes
import googleplay
import os.path

if not os.path.isfile('taxman.cfg') : exit('Config file (taxman.cfg) missing, please create it')

config = ConfigParser.ConfigParser()
config.read('taxman.cfg')

#data = itunes.grab(config.get('iTunes', 'username'), config.get('iTunes', 'password'))
#if data : print itunes.parse(data)

if not os.path.isfile('gsutil/gsutil.py') : googleplay.setup()

data = googleplay.get(config.get('Google Play', 'bucket_id'))
if data : print googleplay.parse(data)