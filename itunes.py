import os
import subprocess
import re

def get(username, token, dates) :
			
	def itc(command) :
		try :
			cmd = 'python itc-reporter/reporter.py -u {0} {1} -T "{2}"'.format(username, command, token)
			print cmd
			output = subprocess.check_output(cmd)
		except subprocess.CalledProcessError as exception :
			print("Status : FAIL", exception.returncode, exception.output)
			return ''
		else :
			return output
			
	def itc_a(command) : 
		return itc('-a {0} {1}'.format(account_nr, command))
	
	def itc_v(command, args) : 
		return itc_a('{0} {1} {2}'.format(command, vendor_nr, args))
	
	result = itc("getAccounts Sales")
	account_nr = re.search(r'(\d+)\r', result).group(1)

	result = itc_a("getVendorsAndRegions")
	regions = re.findall(r'^(\w+)(?=:Financial)', result, re.MULTILINE)
	vendor_nr = re.search(r'(?!vendor )\d+(?=:)', result).group(0)
	
	print vendor_nr
	print regions
	
	for region in regions :
		print itc_v("getFinancialReport", '{0} 2017 01'.format(region))
