
import rocksdb
class RocksDB(object):
  def __init__(self, name):
    db = rocksdb.DB(name, rocksdb.Options(create_if_missing=True))
    self.db = db
  def put(self, key:str, value:str):
    self.db.put(bytes(key,'utf8'), bytes(value, 'utf8')) 
  def get(self, key:str):
    return self.db.get(bytes(key,'utf8')).decode()
  def keys(self):
    it = self.db.iterkeys() 
    it.seek_to_first()
    for key in it:
      yield key.decode()
  def delete(self, key:str):
    self.db.delete(bytes(key, 'utf8')) 

import plyvel
class LevelDB(object):
  def __init__(self, name):
    db = plyvel.DB(name, create_if_missing=True)  
    self.db = db 
  def put(self, key:str, value:str):
    self.db.put(bytes(key,'utf8'), bytes(value, 'utf8')) 
  def get(self, key:str):
    return self.db.get(bytes(key,'utf8')).decode()
  def keys(self):
    with self.db.iterator() as it:
      for key, value in it:
        yield key.decode()
  def delete(self, key:str):
    self.db.delete(bytes(key, 'utf8')) 

import aerospike
class Aerospike(object):
  def __init__(self, name):
    config = { 'hosts': [ ('127.0.0.1', 3000) ] }
    client = aerospike.client(config).connect()
    self.name = name
    self.client = client
    self.namespace = 'hdd'
  def put(self, key:str, value:str):
    key = (self.namespace, self.name, key)
    self.client.put(key, {'value':value})
  def get(self, key:str):
    key = (self.namespace, self.name, key)
    (key, metadata, record) = self.client.get(key)
    return record.get('value')
  def keys(self):
    scan = self.client.scan(self.namespace, self.name)
    records = []
    def _result(arr):
      key, metadata, record = arr
      records.append(record.get('value'))
    scan.foreach(_result)
    for record in records:
      yield record
  def delete(self, key:str):
    key = (self.namespace, self.name, key)
    try:
      self.client.remove(key)  
      return True
    except Exception:
      return False
import redis
class Redis(object):
  def __init__(self, name):
    r = redis.StrictRedis(host='localhost', port=6379, db=0) 
    self.r = r
  def put(self, key:str, value:str):
    self.r.set(key, value)
  def get(self, key:str):
    return self.r.get(key).decode()
  def keys(self):
    for key in self.r.scan_iter('*'):
      yield key.decode()
  def delete(self, key:str):
    self.r.delete(key) 

from google.cloud import datastore
class Datastore(object):
  def __init__(self, kind):
    client = datastore.Client() 
    self.client = client
    self.kind = kind
  def put(self, key:str, value:str):
    key = self.client.key(self.kind, key)
    task = datastore.Entity(key=key)
    task['value'] = value
    self.client.put(task)
  def get(self, key:str):
    key = self.client.key(self.kind, key)
    #task = datastore.Entity(key=key)
    return self.client.get(key).get('value') 
  def delete(self, key:str):
    key = self.client.key(self.kind, key)
    self.client.delete(key)
    
  def keys(self):
    ''' kindがプライマリキーになる'''
    query = self.client.query(kind=self.kind)  
    for result in query.fetch():
      #print(result.key, result.key.name)
      if result.key.name is None:
        continue
      yield result.key.name

def as_open(type_name:str, file_name:str):
  if type_name == 'rocksdb':
    return RocksDB(file_name)
  elif type_name == 'leveldb':
    return LevelDB(file_name)
  elif type_name == 'aerospike':
    return Aerospike(file_name)
  elif type_name == 'redis':
    return Redis(file_name)
  elif type_name == 'datastore':
    return Datastore(kind=file_name)
