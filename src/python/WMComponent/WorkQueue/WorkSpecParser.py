#!/usr/bin/env python
"""
_Workflow_

A class that describes some work to be undertaken on some files
"""

__all__ = []
__revision__ = "$Id: WorkSpecParser.py,v 1.1 2009/05/08 15:32:32 sryu Exp $"
__version__ = "$Revision: 1.1 $"

from WMCore.WMBS.Workflow import Workflow as WMBSWorkflow
from WMCore.WMBS.Fileset import Fileset as WMBSFileset
from WMCore.WMBS.Subscription import Subscription as Subscription

class WorkSpecParser(Object):
    
    def __init__(self, url):        
        #TODO: 
        # 1. get the top level task.
        # 2. get the top level step and inpup
        # 3. generated the spec, owner, name from task
        # 4. get input file list from top level step
        # 5. generate the file set from work flow.
        self.specUrl = url
        # un pickle the object 
        
        self.wmSpec = unpickle
        pass
    
    def createWorkflow(self):
        # create work filow, 
        wmbsWorkflow = WMBSWorkflow(spec, owner, name, taskName)
        wmbsWorkflow.create()
        
        return wmbsWorkflow
        
    def createFilesset(self):
        pass
        
    def createSubscription(self):
        pass
    
    