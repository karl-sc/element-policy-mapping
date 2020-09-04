#!/usr/bin/env python
PROGRAM_NAME = "cg-list-element-mgmt-policies"
PROGRAM_DESCRIPTION = """
CloudGenix script to Create a CSV listing of all IONS and their associated management policies
---------------------------------------

usage: cg-list-element-mgmt-policies.py [-h] [--token "MYTOKEN"]
                                  [--authtokenfile "MYTOKENFILE.TXT"]
                                  [--csvfile csvfile]

By default we write to the file 'element-policy-mapping.csv' if none is specified

Example:

cg-list-element-mgmt-policies.py --csvfile element-policy-mapping
    Uses either the ENV variable or interactive login and prints the report to site-report.csv

"""
from cloudgenix import API, jd
import cloudgenix_idname 
import os
import sys
import argparse
import csv

CLIARGS = {}
cgx_session = API()              #Instantiate a new CG API Session for AUTH

def parse_arguments():
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=PROGRAM_DESCRIPTION
            )
    parser.add_argument('--token', '-t', metavar='"MYTOKEN"', type=str, 
                    help='specify an authtoken to use for CloudGenix authentication')
    parser.add_argument('--authtokenfile', '-f', metavar='"MYTOKENFILE.TXT"', type=str, 
                    help='a file containing the authtoken')
    parser.add_argument('--csvfile', '-c', metavar='csvfile', type=str, 
                    help='the CSV Filename to write', default="element-policy-mapping.csv", required=False)
    args = parser.parse_args()
    CLIARGS.update(vars(args)) ##ASSIGN ARGUMENTS to our DICT
    print(CLIARGS)

def authenticate():
    print("AUTHENTICATING...")
    user_email = None
    user_password = None
    
    ##First attempt to use an AuthTOKEN if defined
    if CLIARGS['token']:                    #Check if AuthToken is in the CLI ARG
        CLOUDGENIX_AUTH_TOKEN = CLIARGS['token']
        print("    ","Authenticating using Auth-Token in from CLI ARGS")
    elif CLIARGS['authtokenfile']:          #Next: Check if an AuthToken file is used
        tokenfile = open(CLIARGS['authtokenfile'])
        CLOUDGENIX_AUTH_TOKEN = tokenfile.read().strip()
        print("    ","Authenticating using Auth-token from file",CLIARGS['authtokenfile'])
    elif "X_AUTH_TOKEN" in os.environ:              #Next: Check if an AuthToken is defined in the OS as X_AUTH_TOKEN
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('X_AUTH_TOKEN')
        print("    ","Authenticating using environment variable X_AUTH_TOKEN")
    elif "AUTH_TOKEN" in os.environ:                #Next: Check if an AuthToken is defined in the OS as AUTH_TOKEN
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
        print("    ","Authenticating using environment variable AUTH_TOKEN")
    else:                                           #Next: If we are not using an AUTH TOKEN, set it to NULL        
        CLOUDGENIX_AUTH_TOKEN = None
        print("    ","Authenticating using interactive login")
    ##ATTEMPT AUTHENTICATION
    if CLOUDGENIX_AUTH_TOKEN:
        cgx_session.interactive.use_token(CLOUDGENIX_AUTH_TOKEN)
        if cgx_session.tenant_id is None:
            print("    ","ERROR: AUTH_TOKEN login failure, please check token.")
            sys.exit()
    else:
        while cgx_session.tenant_id is None:
            cgx_session.interactive.login(user_email, user_password)
            # clear after one failed login, force relogin.
            if not cgx_session.tenant_id:
                user_email = None
                user_password = None            
    print("    ","SUCCESS: Authentication Complete")

def go():
    name_to_id = cloudgenix_idname.generate_id_name_map(cgx_session)

    ####CODE GOES BELOW HERE#########
    resp = cgx_session.get.tenants()
    if resp.cgx_status:
        tenant_name = resp.cgx_content.get("name", None)
        print("======== TENANT NAME",tenant_name,"========")
    else:
        logout()
        print("ERROR: API Call failure when enumerating TENANT Name! Exiting!")
        print(resp.cgx_status)
        sys.exit((vars(resp)))

    csvfilename = CLIARGS['csvfile']
    
    counter = 0
    with open(csvfilename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        resp = cgx_session.get.elements()
        if resp.cgx_status:
            element_list = resp.cgx_content.get("items", None)    

            csvwriter.writerow( [ "ION-Name", "ION-Interface", "Rule-Name", "Rule-Status", "Rule-Prefix", "Rule-App", "Rule-Action"])
            for element in element_list:       
                result = cgx_session.get.element_extensions(element['site_id'], element['id'])
                if result.cgx_status:
                    extension_list = result.cgx_content.get("items", None)
                    for extension in extension_list:
                        if ( "namespace" in extension.keys() and extension['namespace'] == "devicemanagement/interface"):
                            rule_device = name_to_id[element['id']]
                            rule_interface = name_to_id[extension['entity_id']]
                            rule_name = extension['name']
                            if (extension['disabled'] == False):
                                rule_status = "Enabled"
                            else:
                                rule_status = "Disabled"

                            for rule in extension['conf']['rules']:
                                rule_prefix = rule['prefix']
                                rule_app = rule['app']
                                rule_action = rule['action']
                                counter += 1
                                csvwriter.writerow( [ rule_device, rule_interface, rule_name, rule_status, rule_prefix, rule_app, rule_action
                                    ] ) 
        else:
            logout()
            print("ERROR: API Call failure when enumerating SITES in tenant! Exiting!")
            sys.exit((jd(resp)))

    print("Wrote to CSV File:", csvfilename, " - ", counter, 'rows')
    ####CODE GOES ABOVE HERE#########
  
def logout():
    print("Logging out")
    cgx_session.get.logout()

if __name__ == "__main__":
    parse_arguments()
    authenticate()
    go()
    logout()
