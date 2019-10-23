from appstoreconnect import Api

def get(config, dates) :		
	api = Api(config['key_id'], config['key_file'], config['issuer_id'])
	api.download_finance_reports(filters={'vendorNumber': config['vendor_id'], 'reportDate': '2019-06'}, save_to='finance.csv')
	
