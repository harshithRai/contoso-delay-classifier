"""Entra token authentication, with strict TLS for native ODBC or Python TDS."""
import os
import struct
from azure.identity import AzureCliCredential

def connect():
    server=os.environ['SQL_SERVER'];database=os.environ.get('SQL_DATABASE','contoso')
    if not server.endswith('.database.windows.net'): raise ValueError('Use the SQL server FQDN.')
    credential=AzureCliCredential()
    try:
        import pyodbc
        has_odbc='ODBC Driver 18 for SQL Server' in pyodbc.drivers()
    except (ImportError,OSError):
        has_odbc=False
    if has_odbc:
        token=credential.get_token('https://database.windows.net/.default').token.encode('utf-16-le')
        packed=struct.pack(f'<I{len(token)}s',len(token),token)
        return pyodbc.connect(f'Driver={{ODBC Driver 18 for SQL Server}};Server=tcp:{server},1433;Database={database};Encrypt=yes;TrustServerCertificate=no;',attrs_before={1256:packed})
    import certifi
    import pytds
    return pytds.connect(server=server,database=database,port=1433,cafile=certifi.where(),validate_host=True,enc_login_only=False,access_token_callable=lambda:credential.get_token('https://database.windows.net/.default').token,login_timeout=60,timeout=90)
