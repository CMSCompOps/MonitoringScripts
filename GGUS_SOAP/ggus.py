import logging
from suds.client import Client
from suds.transport.http import HttpAuthenticated
from suds import WebFault

logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.DEBUG)
client = Client('https://train-ars.ggus.eu/arsys/WSDL/public/train-ars/GGUS')
print client

class Ticket:
	def __init__(self, site_name, subject, description):
		self.site_name = site_name
		self.subject = subject
		self.description = description

	def create(self):
		person = client.factory.create('AuthenticationInfo')
		person.userName = '********'
		person.password = '********'
		client.set_options(soapheaders=person) 

		result = client.service.TicketCreate(
			#https://wiki.egi.eu/wiki/GGUS:SOAP_Interface_FAQ
			#Mandatory fields
			GHD_Submitter_Mail='email@email.com',
			GHD_Loginname='YOUR DN',
			GHD_Last_Login='user',
			GHD_Last_Modifier='user',
			GHD_Short_Description=self.subject,
			GHD_Description=self.description,	
			GHD_Origin_ID='',
			GHD_Origin_SG='CMSSST',
			#Optional fields
			GHD_Affected_Site=self.site_name,
			GHD_Affected_VO='cms',
			GHD_Responsible_Unit='TPM',
			GHD_Status='new',
			GHD_Name='NAME SURNAME',
			GHD_Priority='urgent',
			GHD_Type_Of_Problem='CMS_Facilities',
		)