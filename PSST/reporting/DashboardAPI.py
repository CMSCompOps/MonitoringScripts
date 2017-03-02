"""
This is the Dashboard API Module for the Worker Node
"""
from __future__ import absolute_import
from __future__ import print_function

import apmon
import time, sys, os, datetime
import traceback
import socket
from types import DictType, StringType, ListType

from WMExceptions import PSST_JOB_EXIT_CODES

#
# Methods for manipulating the apmon instance
#

# Config attributes
apmonUseUrl = False

# Internal attributes
apmonInstance = None
apmonInit = False

# Monalisa configuration
#apmonUrlList = ["http://lxgate35.cern.ch:40808/ApMonConf?app=dashboard", \
#                "http://monalisa.cacr.caltech.edu:40808/ApMonConf?app=dashboard"]
#apmonConf = {"dashb-ai-584.cern.ch:8884": {"sys_monitoring" : 0, \
#                                    "general_info"   : 0, \
#                                    "job_monitoring" : 0} }
apmonConf = {"cms-jobmon.cern.ch:8884": {"sys_monitoring" : 0, \
									"general_info"   : 0, \
									"job_monitoring" : 0} }


apmonLoggingLevel = apmon.Logger.ERROR

#
# Method to create a single apmon instance at a time
#
def getApmonInstance():
	global apmonInstance
	global apmonInit
	if apmonInstance is None and not apmonInit :
		apmonInit = True
		if apmonUseUrl :
			apm = None
			#print "Creating ApMon with dynamic configuration/url"
			try :
				apm = apmon.ApMon(apmonUrlList, apmonLoggingLevel);
			except Exception as e :
				pass
			if apm is not None and not apm.initializedOK():
				#print "Setting ApMon to static configuration"
				try :
					apm.setDestinations(apmonConf)
				except Exception as e :
					apm = None
			apmonInstance = apm
		if apmonInstance is None :
			#print "Creating ApMon with static configuration"
			try :
				apmonInstance = apmon.ApMon(apmonConf, apmonLoggingLevel)
			except Exception as e :
				pass
	return apmonInstance 

#
# Method to free the apmon instance
#
def apmonFree() :
	global apmonInstance
	global apmonInit
	if apmonInstance is not None :
		time.sleep(1)
		try :
			apmonInstance.free()
		except Exception as e :
			pass
		apmonInstance = None
	apmonInit = False

#
# Method to send params to Monalisa service
#
def apmonSend(taskid, jobid, params) :
	apm = getApmonInstance()
	if apm is not None :
		if not isinstance(params, DictType) and not isinstance(params, ListType) :
			params = {"unknown" : "0"}
		if not isinstance(taskid, StringType) :
			taskid = "unknown"
		if not isinstance(jobid, StringType) :
			jobid = "unknown"
		try :
			apm.sendParameters(taskid, jobid, params)
		except Exception as e:
			pass

#
# Common method for writing debug information in a file
#
def logger(msg) :
	msg = str(msg)
	if not msg.endswith("\n") :
		msg += "\n"
	try :
		fh = open("report.log", "a")
		fh.write(msg)
		fh.close
	except Exception as e :
		pass

#
# Context handling for CLI
#

# Format envvar, context var name, context var default value
contextConf = {"MonitorID"    : ("MonitorID", "unknown"), 
			   "MonitorJobID" : ("MonitorJobID", "unknown") }

#
# Method to return the context
#
def getContext(overload={}) :
	if not isinstance(overload, DictType) :
		overload = {}
	context = {}
	for paramName in contextConf.keys() :
		paramValue = None
		if paramName in overload :
			paramValue = overload[paramName]
		if paramValue is None :    
			envVar = contextConf[paramName][0] 
			paramValue = os.getenv(envVar)
		if paramValue is None :
			defaultValue = contextConf[paramName][1]
			paramValue = defaultValue
		context[paramName] = paramValue
	return context

def reportToDashboard(site_name=None, target_ce=None, exitCode=None, grid_status=None, task=None, job=None):
	taskName = task
	# taskName = "PSST_" + site_name + "_"+ str(int(time.time())) 
	# job = 1
	retry = exitCode + 1
	jobId = ("%d_https://glidein.cern.ch/%d/%s_%d" % (int(job), int(job), taskName.replace("_", ":"), retry))

	#meta info
	report1 = {
		"MessageType": "TaskMeta",
		"application": "",
		"nevtJob": "NotAvailable",
		"tool": "glideinwms",
		"JSToolVersion": "0.0.1",
		"GridName": "/DC=ch/DC=cern/OU=Organic Units/OU=Users/CN=rmaciula/CN=780070/CN=Rokas Maciulaitis",
		"scheduler": "GLIDEIN",
		"taskType": "PSST",
		"TaskName": taskName,
		"JobName": "taskMeta",
		"datasetFull": "",
		"CMSUser": "rmaciula"
	}

	#Job meta information (Sent when a job is created):
	report2 = {
		"MessageType": "JobMeta",
		"taskId": taskName,
		"jobId": jobId,
		"schedule": "BossAir",
		"TaskType": "PSST",
		"JobType": "PSST",
		"NEventsToProcess": "",
	}

	# #Job status updated to submitted (Sent when a job is successfully submitted):
	# report3 = {
	# 	"MessageType": "JobStatus",
	# 	"jobId": jobId,
	# 	"taskId": taskName,
	# 	"StatusValue": "submitted",
	# 	"StatusValueReason": "Job was successfuly submitted",
	# 	"StatusEnterTime": time.time(),
	# 	"StatusDestination": site_name,
	# }

	# #Job status update to running (Sent when the job starts in the WN):
	# report4 = {
	# 	"MessageType": "JobStatus",
	# 	"MessageTS": time.time(),
	# 	"taskId": taskName,
	# 	"jobId": jobId,
	# 	"StatusValue": "running",
	# 	"StatusEnterTime": time.time(),
	# 	"StatusValueReason": "Job started execution in the WN",
	# 	"StatusDestination": site_name,
	# }

	# #Job start message (Sent when the job starts in the WN):
	# report5 = {
	# 	"MessageType": "jobRuntime-jobStart",
	# 	"MessageTS": time.time(),
	# 	"taskId": taskName,
	# 	"jobId": jobId,
	# 	"StatusEnterTime": time.time(),
	# }

	# #job complete message (Sent when a job completes execution normally):
	# report6 = {
	# 	"MessageType": "jobRuntime-jobEnd",
	# 	"MessageTS": time.time(),
	# 	"taskId": taskName,
	# 	"jobId": jobId,
	# 	"JobExitReason": "Job completed execution in the WN",
	# 	"StatusEnterTime": time.time(),
	# }

	#Job status updated to succeeded (Sent when a job finishes execution and didn't have any error)
	report7 = {
		"MessageType": "JobStatus",
		"jobId": jobId,
		"taskId": taskName,
		"JobExitCode": exitCode,
		"StatusValue": grid_status,
		"StatusEnterTime": time.time(),
		"StatusDestination": site_name,
		"WNHostName": socket.gethostname(),
		"TargetCE": target_ce,
		"JobExitReason": PSST_JOB_EXIT_CODES[exitCode],
	}
	#meta info
	# params = {
	# 	"datasetFull": "None", 
	# 	"exe": "",
	# 	"ApplicationVersion": "",
	# 	"scheduler": "GLIDEIN",
	# 	"resubmitter": "rmaciula",
	# 	"tool": "glideinwms",
	# 	"vo": "cms",
	# 	"tool_ui": os.environ.get("HOSTNAME",""),
	# 	"jobId": "1",
	# 	"JSToolVersion": "0.0.1",
	# 	"user": "rmaciula",
	# 	"taskId": taskName,
	# 	"taskType": "integration",
	# 	"CMSuser": "rmaciula",
	# 	"sid": "https://glidein.cern.ch/%d/%s" % (job, taskName.replace("_", ":")),
	# 	"GridName": "/DC=ch/DC=cern/OU=Organic Units/OU=Users/CN=rmaciula/CN=780070/CN=Rokas Maciulaitis",
	# 	"SubmissionType": "glideinwms",
	# }

	# params2 = {
	# 	"TargetSE": "", 
	# 	"ApplicationVersion": "", 
	# 	"localId": "", 
	# 	"resubmitter": "rmaciula", 
	# 	"tool": "glideinwms", 
	# 	"scheduler": "GLIDEIN", 
	# 	"broker": "", 
	# 	"jobId": ("%d_https://glidein.cern.ch/%d/%s_%d" % (job, job, taskName.replace("_", ":"), retry)),
	# 	"tool_ui": os.environ.get("HOSTNAME",""), 
	# 	"StatusValue": "pending", 
	# 	"JSToolVersion": "0.0.1", 
	# 	"user": "rmaciula", 
	# 	"taskId": taskName, 
	# 	"taskType": "integration", 
	# 	"CMSUser": "rmaciula", 
	# 	"bossId": job, 
	# 	"vo": "cms", 
	# 	"datasetFull": "",
	# 	"exe": "cmsRun", 
	# 	"sid": "https://glidein.cern.ch/%d/%s" % (job, taskName.replace("_", ":")), 
	# 	"GridName": "/DC=ch/DC=cern/OU=Organic Units/OU=Users/CN=rmaciula/CN=780070/CN=Rokas Maciulaitis", 
	# 	"SubmissionType": "glideinwms"
	# }

	# #Dashboard early startup params: 
	# params3 = {
	# 	"MonitorID": taskName, 
	# 	"MonitorJobID": ("%d_https://glidein.cern.ch/%d/%s_%d" % (job, job, taskName.replace("_", ":"), retry)),
	# 	"SyncCE": "ceprod07.grid.hep.ph.ic.ac.uk", 
	# 	"OverflowFlag": 0, 
	# 	"SyncSite": "T2_UK_London_IC", 
	# 	"SyncGridJobId": "https://glidein.cern.ch/%d/%s" % (job, taskName.replace("_", ":")), 
	# 	"WNHostName": "wg57.grid.hep.ph.ic.ac.uk"
	# }

	# #Dashboard startup parameters: 
	# params4 = {
	# 	"MonitorID": taskName,
	# 	"MonitorJobID": ("%d_https://glidein.cern.ch/%d/%s_%d" % (job, job, taskName.replace("_", ":"), retry)),
	# 	"WNHostName": "wg57.grid.hep.ph.ic.ac.uk", 
	# 	"ExeStart": ""
	# }

	# #Dashboard end parameters: 
	# params5 = {
	# 	"MonitorID": taskName, 
	# 	"CRABUserReadMB": 0, 
	# 	"MonitorJobID": ("%d_https://glidein.cern.ch/%d/%s_%d" % (job, job, taskName.replace("_", ":"), retry)),
	# 	"CrabCpuPercentage": 0,
	# 	"CRABUserWriteMB": 0, 
	# 	"CrabUserCpuTime": 0, 
	# 	"NEventsProcessed": 0, 
	# 	"ExeTime": 4805,
	# 	"JobExitCode": exitCode, 
	# 	"CRABUserPeakRss": 0, 
	# 	"ExeExitCode": 0,
	# 	"StatusValue": "succeeded",
	# 	"StatusValueReason": "Job has completed successfully",
	# 	"StatusDestination": "T2_UK_London_IC"
	# }

	# params6 = {
	# 	'MonitorID': taskName, 
	# 	'MonitorJobID': ("%d_https://glidein.cern.ch/%d/%s_%d" % (job, job, taskName.replace("_", ":"), retry)), 
	# 	'StatusValue': 'Done'
	# }
	print("Dashboard parameters: %s" % str(report1))
	apmonSend(report1["TaskName"], report1["JobName"], report1)
	print("Dashboard parameters: %s" % str(report2))
	apmonSend(report2["taskId"], report2["jobId"], report2)
	# print("Dashboard parameters: %s" % str(report3))
	# apmonSend(report3["taskId"], report3["jobId"], report3)
	# time.sleep(3)
	# print("Dashboard parameters: %s" % str(report4))
	# apmonSend(report4["taskId"], report4["jobId"], report4)
	# time.sleep(3)
	# print("Dashboard parameters: %s" % str(report5))
	# apmonSend(report5["taskId"], report5["jobId"], report5)
	# time.sleep(3)
	# print("Dashboard parameters: %s" % str(report6))
	# apmonSend(report6["taskId"], report6["jobId"], report6)
	# time.sleep(3)
	print("Dashboard parameters: %s" % str(report7))
	apmonSend(report7["taskId"], report7["jobId"], report7)

	apmonFree()
	return exitCode

if __name__ == "__main__":
	reportToDashboard(sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6])
