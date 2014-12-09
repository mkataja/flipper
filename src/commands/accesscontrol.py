'''
Created on 9.12.2014

@author: Matias
'''

def has_admin_access(nickmask):
    # TODO: Better authentication
    return nickmask.user == "otus"
