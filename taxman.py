import ConfigParser
import itunes
import os.path

if not os.path.isfile('taxman.cfg') : exit('Config file (taxman.cfg) missing, please create it')

config = ConfigParser.ConfigParser()
config.read('taxman.cfg')

data = itunes.grab(config.get('iTunes', 'username'), config.get('iTunes', 'password'))
if data : print itunes.parse(data)