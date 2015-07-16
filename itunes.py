import mechanize
import cookielib
from bs4 import BeautifulSoup
import re

from dateutil.parser import parse as parseDate
from datetime import *

DEFAULT = datetime(2000, 01, 01)

def get(username, password, dates) :
	# Browser
	br = mechanize.Browser(factory=mechanize.RobustFactory())

	# Cookie Jar
	cj = cookielib.LWPCookieJar()
	br.set_cookiejar(cj)

	# Browser options
	br.set_handle_equiv(True)
	br.set_handle_redirect(True)
	br.set_handle_referer(True)
	br.set_handle_robots(False)

	# Follows refresh 0 but not hangs on refresh > 0
	br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

	# Want debugging messages?
	#br.set_debug_http(True)
	#br.set_debug_redirects(True)
	#br.set_debug_responses(True)

	# User-Agent (this is cheating, ok?)
	br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

	print('Opening iTunes Connect...')
	r = br.open('https://itunesconnect.apple.com/WebObjects/iTunesConnect.woa')

	print('Logging in...')

	# Select the "appleConnectForm"
	br.select_form(name="appleConnectForm")

	# enter user name and password
	br.form['theAccountName'] = username
	br.form['theAccountPW'] = password
	br.submit()

	print('Going to report page...')

	# open the link to payments and reports
	r = br.open('https://itunesconnect.apple.com/WebObjects/iTunesConnect.woa/da/jumpTo?page=paymentsAndFinancialReports')

	# Select the first (index zero) form
	br.select_form(nr=0)

	# submit using the hidden Payments input (this is normally done via js, but works this way too)
	r = br.submit(label='Payments')

	# grab the html
	html = r.read()

	return html

def strip_whitespace(s) :
	# replace any whitespace with a single space, strip removes any whitespace around the string
	return re.sub('[\t\n\r ]+', ' ', s).strip()

def parse(html, dates) :
	# parse the html using beautiful soup
	soup = BeautifulSoup(html)

	# finds all earnings divs, they're hidden when viewing the page but always present in the html
	months = soup.find_all('div', { 'class' : 'earnings-container'} )

	output = dict()

	for month in months :

		# grabs the summary bit at the top
		summary = strip_whitespace(month.find('div', { 'class' : 'earnings-top' }).text)
		# break the summary into three lines (using the year as an anchor)
		summary = re.sub(' (20\d\d) ', '\g<0>\n', summary)

		# parse out the report date, it uses the month name so some fancier parsing is required
		dateText = summary.splitlines()[0]
		dateText = re.sub('Earned ', '', dateText)
		date = parseDate(dateText)

		# with that we can now skip this month if it's not in the list of dates
		# the dates are stored as tuples, so we need to make a new tuple here to compare
		dateTuple = (date.strftime('%Y'), date.strftime('%m'))
		if dateTuple not in dates :
			#print date.strftime('skipping %Y-%m, was not in list of requested months')
			continue

		# add tabs after summary labels
		summary = re.sub('Earned ', 'Earned\t', summary)
		summary = re.sub('Paid On ', 'Paid On\t', summary)
		# add a Sum label before the sum
		summary = re.sub('\n(\d+)', '\nSum\t\g<1>', summary)

		# parse out the tables (each row (currency) is strangely a table)
		tables = month.find_all('table', { 'class' : 'earnings-matrix payments earned' })

		text = ''

		for table in tables :
			for tr in table.find_all('tr') :
				cols = []
				for td in tr.find_all('td') :
					inner = td.text

					# if the row is the header, we replace it with a hand spaced one
					if inner == "Currency" :
						cols = ['Currency    Beginning   Earned      Pre-Tax     Withholding Input       Adjustments Post-Tax    FX Rate     Payment\n', '            Balance                 Subtotal    Tax         Tax                     Subtotal']
						break

					cols.append(strip_whitespace(inner).ljust(12))
				text += ''.join(cols).strip() + '\n'

		text += '\n' + summary

		print date.strftime('iTunes found data for %Y-%m')
		output[date.strftime('%Y-%m')] = text

	return output
