# -*- coding: utf-8 -*-
import logging
from cStringIO import StringIO

import transaction
from zope import event
from zope.interface import implements

from DateTime import DateTime
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from OFS.Image import Image

from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.requestmethod import postonly
from Acquisition import aq_get
from Acquisition import aq_inner
from Acquisition import aq_parent
from zExceptions import BadRequest
from ZODB.POSException import ConflictError

from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.permissions import ManageUsers
from Products.CMFCore.permissions import SetOwnProperties
from Products.CMFCore.permissions import SetOwnPassword
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.MembershipTool import MembershipTool as BaseTool

from Products.PlonePAS.events import UserLoggedInEvent
from Products.PlonePAS.events import UserInitialLoginInEvent
from Products.PlonePAS.events import UserLoggedOutEvent
from Products.PlonePAS.interfaces import membership
from Products.PlonePAS.utils import cleanId
from Products.PlonePAS.utils import scale_image

default_portrait = 'defaultUser.png'
logger = logging.getLogger('PlonePAS')
memberareaCreationFlag = True

#from eisoo.memberattachedinfo.events import MemberAreaCreatedEvent
#from eisoo.operation.events import AddloginlogsEvent


def getMemberareaCreationFlag(self):
    return True

def get_enable_user_folders(self):
    return True
#    security.declarePublic('createMemberarea')
def createMemberarea(self, member_id=None, minimal=None):
        """
        Create a member area for 'member_id' or the authenticated
        user, but don't assume that member_id is url-safe.
        """
        if not self.getMemberareaCreationFlag():
            return None
        catalog = getToolByName(self, 'portal_catalog')
        membership = getToolByName(self, 'portal_membership')
        members = self.getMembersFolder()

        if not member_id:
            # member_id is optional (see CMFCore.interfaces.portal_membership:
            #     Create a member area for 'member_id' or authenticated user.)
            member = membership.getAuthenticatedMember()
            member_id = member.getId()

        if hasattr(members, 'aq_explicit'):
            members = members.aq_explicit

        if members is None:
            # no members area
            logger.debug('createMemberarea: members area does not exist.')
            return

        safe_member_id = cleanId(member_id)
        if hasattr(members, safe_member_id):
            # has already this member
            logger.debug(
                'createMemberarea: member area '
                'for %r already exists.' % safe_member_id)
            return

        if not safe_member_id:
            # Could be one of two things:
            # - A Emergency User
            # - cleanId made a empty string out of member_id
            logger.debug(
                'createMemberarea: empty member id '
                '(%r, %r), skipping member area creation.' % (
                member_id, safe_member_id))
            return

        # Create member area without security checks
        typesTool = getToolByName(members, 'portal_types')
#        fti = typesTool.getTypeInfo(self.memberarea_type)
        menufolder_type = "my315ok.wechat.content.menufolder"
        menu_type = "my315ok.wechat.content.menu"
        import pdb
        pdb.set_trace()
        fti = typesTool.getTypeInfo(menufolder_type)        
        member_folder = fti._constructInstance(members, safe_member_id)
        fti = typesTool.getTypeInfo(menu_type)         
        menu  = fti._constructInstance(member_folder, 'top1')
        menu.title = u"plone论坛"
        menu.menu_type = "view"
        menu.istopmenu = "1"
        menu.key = 1
        menu.url ="http://plone.315ok.org/"
        menu  = fti._constructInstance(member_folder, 'top2')
        menu.title = u"plone论坛"        
        menu.menu_type = "view"
        menu.istopmenu = "1"
        menu.key = 1
        menu.url ="http://plone.315ok.org/" 
        menu  = fti._constructInstance(member_folder, 'top3')
        menu.title = u"菜单"        
        menu.menu_type = "view"
        menu.istopmenu = "1"
        menu.key = 1
        menu.url ="http://plone.315ok.org/"
        submenu  = fti._constructInstance(menu, 'top3_1')
        menu.title = u"plone论坛"        
        submenu.menu_type = "view"
        submenu.istopmenu = "0"
        submenu.key = 1
        submenu.url ="http://plone.315ok.org/"                       

        # Get the user object from acl_users
        acl_users = getToolByName(self, "acl_users")
        user = acl_users.getUserById(member_id)
        if user is not None:
            user = user.__of__(acl_users)
        else:
            user = getSecurityManager().getUser()
            # check that we do not do something wrong
            if user.getId() != member_id:
                raise NotImplementedError(
                        'cannot get user for member area creation')

        member_object = self.getMemberById(member_id)

        ## Modify member folder
        member_folder = self.getHomeFolder(member_id)
        # Grant Ownership and Owner role to Member
        member_folder.changeOwnership(user)
        member_folder.__ac_local_roles__ = None
        member_folder.manage_setLocalRoles(member_id, ['Owner'])
        # We use ATCT now use the mutators
        fullname = member_object.getProperty('fullname')
        member_folder.setTitle(fullname or member_id)
        member_folder.reindexObject()

        ## Hook to allow doing other things after memberarea creation.
        notify_script = getattr(member_folder, 'notifyMemberAreaCreated', None)
        if notify_script is not None:
            notify_script()
            
def loginUser(self, REQUEST=None):
        """ Handle a login for the current user.

        This method takes care of all the standard work that needs to be
        done when a user logs in:
        - clear the copy/cut/paste clipboard
        - PAS credentials update
        - sending a logged-in event
        - storing the login time
        - create the member area if it does not exist
        """
        user=getSecurityManager().getUser()

        if user is None:
            return

        res = self.setLoginTimes()
#        import pdb
#        pdb.set_trace()
        if res:
            event.notify(UserInitialLoginInEvent(user))
        else:
            event.notify(UserLoggedInEvent(user))

        if REQUEST is None:
            REQUEST=getattr(self, 'REQUEST', None)
        if REQUEST is None:
            return

        # Expire the clipboard
        if REQUEST.get('__cp', None) is not None:
            REQUEST.RESPONSE.expireCookie('__cp', path='/')

        # sure only wechat site will create memberArea
        from wechat.policy.browser.interfaces import IThemeSpecific
        if IThemeSpecific.providedBy(REQUEST) and  res:
#            import pdb
#            pdb.set_trace()
            ###########################3
#            createMemberArea(self)
#        if not self.getMemberareaCreationFlag():
#            return None
            catalog = getToolByName(self, 'portal_catalog')
            membership = getToolByName(self, 'portal_membership')
            members = self.getMembersFolder()

            member_id = None
            if not member_id:
            # member_id is optional (see CMFCore.interfaces.portal_membership:
            #     Create a member area for 'member_id' or authenticated user.)
                member = membership.getAuthenticatedMember()
                member_id = member.getId()

            if hasattr(members, 'aq_explicit'):
                members = members.aq_explicit

            if members is None:
            # no members area
                logger.debug('createMemberarea: members area does not exist.')
                return

            safe_member_id = cleanId(member_id)
            if hasattr(members, safe_member_id):
            # has already this member
                logger.debug(
                'createMemberarea: member area '
                'for %r already exists.' % safe_member_id)
                return

            if not safe_member_id:
            # Could be one of two things:
            # - A Emergency User
            # - cleanId made a empty string out of member_id
                logger.debug(
                'createMemberarea: empty member id '
                '(%r, %r), skipping member area creation.' % (
                member_id, safe_member_id))
                return

        # Create member area without security checks
            typesTool = getToolByName(members, 'portal_types')
#        fti = typesTool.getTypeInfo(self.memberarea_type)
            menufolder_type = "my315ok.wechat.content.menufolder"
            menu_type = "my315ok.wechat.content.menu"
#            import pdb
#            pdb.set_trace()
            fti = typesTool.getTypeInfo(menufolder_type)        
            member_folder = fti._constructInstance(members, safe_member_id)
            fti = typesTool.getTypeInfo(menu_type)         
            menu  = fti._constructInstance(member_folder, 'top1')
            menu.title = u"plone论坛"
            menu.menu_type = "view"
            menu.istopmenu = "1"
            menu.key = 1
            menu.url ="http://plone.315ok.org/"
            menu  = fti._constructInstance(member_folder, 'top2')
            menu.title = u"plone论坛"        
            menu.menu_type = "view"
            menu.istopmenu = "1"
            menu.key = 1
            menu.url ="http://plone.315ok.org/" 
            menu  = fti._constructInstance(member_folder, 'top3')
            menu.title = u"菜单"        
            menu.menu_type = "view"
            menu.istopmenu = "1"
            menu.key = 1
            menu.url ="http://plone.315ok.org/"
            submenu  = fti._constructInstance(menu, 'top3_1')
            submenu.title = u"plone论坛"        
            submenu.menu_type = "view"
            submenu.istopmenu = "0"
            submenu.key = 1
            submenu.url ="http://plone.315ok.org/"                       

        # Get the user object from acl_users
            acl_users = getToolByName(self, "acl_users")
            user = acl_users.getUserById(member_id)
            if user is not None:
                user = user.__of__(acl_users)
            else:
                user = getSecurityManager().getUser()
            # check that we do not do something wrong
                if user.getId() != member_id:
                    raise NotImplementedError(
                        'cannot get user for member area creation')

            member_object = self.getMemberById(member_id)

        ## Modify member folder
            member_folder = self.getHomeFolder(member_id)
        # Grant Ownership and Owner role to Member
            member_folder.changeOwnership(user)
            member_folder.__ac_local_roles__ = None
            member_folder.manage_setLocalRoles(member_id, ['Owner'])
        # We use ATCT now use the mutators
            fullname = member_object.getProperty('fullname')
            member_folder.setTitle(fullname or member_id)
            member_folder.reindexObject()

        ## Hook to allow doing other things after memberarea creation.
            notify_script = getattr(member_folder, 'notifyMemberAreaCreated', None)
            if notify_script is not None:
                notify_script()            
            ######################################333
        try:
            pas = getToolByName(self, 'acl_users')
            pas.credentials_cookie_auth.login()
#            if res:
#                event.notify(MemberAreaCreatedEvent(user)) 
            #set the cookie __ac so that client can remember it
            myresponse = REQUEST.RESPONSE
            if getattr(REQUEST,"ac_persistent",None):
                cookiename = '__ac'
                cookie = myresponse.cookies.get(cookiename)
                if cookie:
                    cookievalue = cookie.pop('value')
                    new_date = DateTime()+7
                    cookie['expires'] = new_date.strftime("%a, %d-%h-%y %H:%m:%S GMT+8")
                    myresponse.setCookie(cookiename,cookievalue,**cookie)
        except AttributeError:
            # The cookie plugin may not be present
            pass
#        try:
#            event.notify(AddloginlogsEvent(user))
#        except AttributeError:
#            pass

