#-*- coding: UTF-8  -*-
import unittest2 as unittest
from wechat.policy.testing import INTEGRATION_TESTING

from Products.CMFCore.utils import getToolByName

class TestSetup(unittest.TestCase):
    
    layer = INTEGRATION_TESTING
    
    def test_portal_title(self):
        portal = self.layer['portal']
        self.assertEqual("Wechat管理平台", portal.getProperty('title'))
    
    def test_portal_description(self):
        portal = self.layer['portal']
        self.assertEqual("Wechat管理平台", portal.getProperty('description'))
   


    def test_Dexterity_membrane_installed(self):
        portal = self.layer['portal']
        portal_types = getToolByName(portal, 'portal_types')
        
        self.assertTrue("dexterity.membrane.member" in portal_types)
        self.assertTrue("dexterity.membrane.memberfolder" in portal_types)        
    
    def test_wechat_installed(self):
        portal = self.layer['portal']
        portal_types = getToolByName(portal, 'portal_types')
        
        self.assertTrue('collective.conference.conference' in portal_types)
        self.assertTrue('collective.conference.session' in portal_types)        
    
  
    def test_add_portal_member_permission(self):
        portal = self.layer['portal']
        
        self.assertTrue('Add portal member' in
                [r['name'] for r in 
                    portal.permissionsOfRole('Anonymous')
                    if r['selected']])

