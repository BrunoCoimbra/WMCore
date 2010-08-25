#!/usr/bin/env python
"""
Base handler for taskEnd.
"""
__all__ = []
__revision__ = "$Id: TaskEndHandler.py,v 1.4 2009/07/08 17:28:08 delgadop Exp $"
__version__ = "$Revision: 1.4 $"

from WMCore.WMFactory import WMFactory

from TQComp.Constants import taskStates
#from TQComp.Constants import reportUrlDir, uploadRoot

from traceback import extract_tb
import sys

import threading

class TaskEndHandler(object):
    """
    Handler for pilot's taskEnd message.
    """
   
    def __init__(self, params = None):
        """
        Constructor. The params argument can be used as a dict for any
        parameter (if needed). Basic things can be obtained from currentThread.

        The required params are as follow:
           uploadBaseUrl, specBasePath
        """
#        required = ["uploadBaseUrl", "specBasePath"]
        required = []
        for param in required:
            if not param in params:
                messg = "GetTaskHandler object requires params['%s']" % param
                # TODO: What number?
                numb = 0
                raise WMException(messg, numb)

#        self.uploadBaseUrl = params["uploadBaseUrl"]
#        self.specBasePath = params["specBasePath"]
        myThread = threading.currentThread()
        factory = WMFactory("default", \
                  "TQComp.Database."+myThread.dialect)
        self.queries = factory.loadObject("Queries")
        self.logger = myThread.logger
    
    
    # this we overload from the base handler
    def __call__(self, event, payload):
        """
        Handles the event with payload.
        """
        # load queries for backend.
        myThread = threading.currentThread()
   
        # Now handle the message
        fields = {}
        if event in ['taskEnd']:
   
            self.logger.debug('TaskEndHandler:TaskEnd:payload: %s' % payload)
            
            try:
                myThread.transaction.begin()

                # Extract the task attributes
                # Here we should check that all arguments are given correctly...
                pilotId = payload['pilotId']
                taskId = payload['taskId']
                status = payload['exitStatus']
                possibleStatus = ('Done', 'Failed')
                if not (status in possibleStatus):
                    fields = {'Error': 'exitStatus should be one of %s' % \
                                       (possibleStatus)}
                    self.logger.warning("Incorrect exitStatus: %s" % status)
                    myThread.transaction.rollback()
                    return {'msgType': result, 'payload': fields}
              
                # Retrieve the task spec (check the task is in this pilot)
                res = self.queries.getTasksWithFilter({'id': taskId}, \
                                          fields = ['spec', 'pilot'])
                self.logger.debug("Res: %s" % res)
                if (not res) or (res[0][1] != pilotId):
                    result = 'Error'
                    if (not res):
                        fields = {'Error': 'No task with id %s' % (taskId)}
                    else:
                        fields = {'Error': 'Task %s not in pilot %s' % \
                                           (taskId, pilotId)}
                    myThread.transaction.rollback()
                    return {'msgType': result, 'payload': fields}
             
                specFile = res[0][0]

                # Mark the task as Done/Failed in the DB
#                vars = {'state': taskStates['Done'], 'pilot': None}
#                vars = {'state': taskStates['Done']}
                vars = {'state': taskStates[status]}
                self.queries.updateOneTask(taskId, vars)
#                self.logger.debug("Task updated as Done.")
                self.logger.debug("Task updated as %s." % status)
              
                # Give the result back
                fields['TaskId'] = taskId
#                fields['Info'] = 'Task updated as Done.'
                fields['Info'] = 'Task updated as %s.' % status
#                # TODO: By now, store report in the same dir as spec (like PA)
#                reportUrl = self.__buildReportUrl(specFile)
#                fields['ReportUrl'] = reportUrl 
                result = 'TaskEndACK'
      
                # Commit
                myThread.transaction.commit()
              
            except:
                type, val, tb = sys.exc_info()
                myThread.transaction.rollback()
                messg = 'Error in TaskEnd, due to: %s - %s '% (type, val)
                self.logger.warning(messg + "Trace: %s"% extract_tb(tb,limit=5))
                result = 'Error'
                fields = {'Error': messg}
              
            return {'msgType': result, 'payload': fields}
   
        else:
            # unexpected message, scream?
            pass
    

#    def __buildReportUrl(self, thefile):
#        # TODO: maybe need to change the file name/location for error reports?
#        path = thefile.replace(self.specBasePath, reportUrlDir+'/')
#        path = path.replace(thefile.split('/')[-1], 'FrameworkJobReport.xml')
#        return self.uploadBaseUrl+'/'+uploadRoot+'/'+path
        
