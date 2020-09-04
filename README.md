# element-policy-mapping
CloudGenix script to Create a CSV listing of all IONS and their associated management policies
---------------------------------------

usage: cg-list-element-mgmt-policies.py [-h] [--token "MYTOKEN"]
                                  [--authtokenfile "MYTOKENFILE.TXT"]
                                  [--csvfile csvfile]

By default we write to the file 'element-policy-mapping.csv' if none is specified

Example:

cg-list-element-mgmt-policies.py --csvfile element-policy-mapping
    Uses either the ENV variable or interactive login and prints the report to site-report.csv
