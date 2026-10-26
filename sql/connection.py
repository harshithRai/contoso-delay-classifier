"""Entra token authentication; requires `az login` and Microsoft ODBC Driver 18."""
import os
import struct
import pyodbc
from azure.identity import AzureCliCredential

def connect():
    server=os.environ['SQL_SERVER'];database=os.environ.get('SQL_DATABASE','contoso')
    if not server.endswith('.database.windows.net'): raise ValueError('Use the SQL server FQDN.')
    token=AzureCliCredential().get_token('https://database.windows.net/.default').token.encode('utf-16-le')
    packed=struct.pack(f'<I{len(token)}s',len(token),token)
    return pyodbc.connect(f'Driver={{ODBC Driver 18 for SQL Server}};Server=tcp:{server},1433;Database={database};Encrypt=yes;TrustServerCertificate=no;',attrs_before={1256:packed})
