import certifi
import ssl
from pymongo import MongoClient

uri = "mongodb+srv://emekaokservices:EmekaOkServices@ac-4w8zl2n.hpzmd6k.mongodb.net/test?retryWrites=true&w=majority&tls=true"
client = MongoClient(uri, tlsCAFile=certifi.where(), tlsVersion=ssl.PROTOCOL_TLSv1_2)

print(client.server_info())
