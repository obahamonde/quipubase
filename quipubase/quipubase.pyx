# type: ignore
from threading import Lock as mutex
from typing import Any, ParamSpec, TypeVar

import orjson

from libcpp cimport bool
from libcpp.string cimport string

T = TypeVar("T")
P = ParamSpec("P")

cdef extern from "rocksdb/db.h" namespace "rocksdb":
    cdef cppclass DB:
        @staticmethod
        Status Open(const Options&, const string&, DB**)
        void Put(const WriteOptions&, const string&, const string&)
        Status Get(const ReadOptions&, const string&, string*)
        Status Delete(const WriteOptions&, const string&)
        Status Merge(const WriteOptions&, const string&, const string&)
        Iterator* NewIterator(const ReadOptions&)
        void Close()
        

    cdef cppclass Options:
        Options()
        bool create_if_missing

    cdef cppclass WriteOptions:
        WriteOptions()

    cdef cppclass ReadOptions:
        ReadOptions()

    cdef cppclass Status:
        bool ok()
        string ToString()

    cdef cppclass Iterator:
        void SeekToFirst()
        void Next()
        bool Valid()
        Slice key()
        Slice value()
        void Close()

    cdef cppclass Slice:
        const char* data()
        size_t size()
   

cdef class Quipu:
    cdef DB* db
    cdef Options options
    cdef WriteOptions write_options
    cdef ReadOptions read_options
    cdef Status status
    cdef string db_path
    cdef object lock

    def __cinit__(self, str db_path):
        if not db_path:
            raise ValueError("db_path must be provided")
        self.options = Options()
        self.options.create_if_missing = True
        self.write_options = WriteOptions()
        self.read_options = ReadOptions()
        self.db_path = db_path.encode()
        self.lock = mutex()
        self.open_db()

    cdef void open_db(self):
        with self.lock:
            self.status = DB.Open(self.options, self.db_path, &self.db)
            if not self.status.ok():
                raise RuntimeError(f"Failed to open database: {self.status.ToString().decode()}")

    cdef void close_db(self):
        with self.lock:
            if self.db:
                self.db.Close()
                del self.db

    def __dealloc__(self):
        self.close_db()


    def put(self, str key, bytes value):
        with self.lock:
            self.db.Put(self.write_options, key.encode(), value)

    def get(self, str key):
        cdef string value
        with self.lock:
            self.status = self.db.Get(self.read_options, key.encode(), &value)
            if not self.status.ok():
                return None
            return value
  
    def delete(self, str key):
        with self.lock:
            self.db.Delete(self.write_options, key.encode())
    

    def exists(self, str key)->bool:
        return self.get(key) is not None
  
    def count(self)->int:
        cdef int count = 0
        cdef Iterator* it = self.db.NewIterator(self.read_options)
        try:
            it.SeekToFirst()
            while it.Valid():
                count += 1
                it.Next()
        finally:
            del it
        return count


   
    def get_doc(self, str key):
        cdef bytes value
        value = self.get(key)
        if value is None:
            return None
        return orjson.loads(value)
   
    def put_doc(self, str key, dict[str,Any] value):
        if self.exists(key):
            raise ValueError(f"Object with id {key} already exists")
        self.put(key, orjson.dumps(value, option=orjson.OPT_SERIALIZE_NUMPY))
    
 
    def delete_doc(self, str key):
        if not self.exists(key):
            raise ValueError(f"Object with id {key} not found")
        self.delete(key)

    
    def scan_docs(self, int limit, int offset, bool keys_only=False):
        cdef list results = []
        cdef Iterator* it = self.db.NewIterator(ReadOptions())
        it.SeekToFirst()
        try:
            while it.Valid() and len(results) < limit:
                if offset > 0:
                    offset -= 1
                    it.Next()
                    continue
                if keys_only:
                    results.append((<bytes>it.key().data())[:it.key().size()])
                else:
                    results.append(orjson.loads((<bytes>it.value().data())[:it.value().size()]))
                it.Next()
        finally:
            del it
            return results
      
    def find_docs(self,  int limit, int offset, dict[str,Any] kwargs):
        cdef list results = []
        cdef Iterator* it = self.db.NewIterator(ReadOptions()) 
        try:
            it.SeekToFirst()
            while it.Valid() and len(results) < limit:
                if offset > 0:
                    offset -= 1
                    it.Next()
                    continue
                key = (<bytes>it.key().data())[:it.key().size()]
                value = (<bytes>it.value().data())[:it.value().size()]
                doc = orjson.loads(value)
                for k,v in kwargs.items():
                    if doc.get(k) != v:
                        break
                else:
                    results.append(doc)
                it.Next()
        finally:
            del it
            return results

    def merge_doc(self, str key, dict[str,Any] value):
        cdef bytes existing
        existing = self.get(key)
        if existing is None:
            self.put_doc(key, value)
            return
        existing_dict = orjson.loads(existing)
        existing_dict.update(value)
        self.put(key, orjson.dumps(existing_dict, option=orjson.OPT_SERIALIZE_NUMPY))