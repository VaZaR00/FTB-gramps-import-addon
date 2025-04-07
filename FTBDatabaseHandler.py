import os
import sqlite3
import traceback
from ftb_shared import *

FTB_DIR_NAME = "myheritage"
FTB_DB_DIR_NAME = "database"
FTB_DB_FORMAT = '.ftb'

class FTBDatabaseHandler:
    def __init__(self, dbPath):
        self.dbPath = dbPath
        self.cursor, self.dbConnection = self.connect_to_database()

    def connect_to_database(self):
        self.dbPath = self.find_ftb_file(self.dbPath)
        if not self.dbPath: raise FileNotFoundError
        conn = sqlite3.connect(self.dbPath, check_same_thread=False)
        conn.text_factory = lambda b: b.decode(errors = 'ignore')
        cursor = conn.cursor()
        return cursor, conn

    def find_ftb_file(self, root_folder: str):
        # if not (FTB_DIR_NAME in root_folder.lower()): return None
        for dirpath, dirnames, filenames in os.walk(root_folder):
            if os.path.basename(dirpath).lower() == FTB_DB_DIR_NAME:
                for filename in filenames:
                    if filename.endswith(FTB_DB_FORMAT):
                        return os.path.join(dirpath, filename)
        return None

    def fetchDbDataDto(self, key, dtoClass, oneRow=True, query=None, keysStr=None, hasCondition=True):
        if query is None:
            query = dtoClass.query(keysStr, hasCondition)
            
        try:
            if key:
                key = toIter(key)
                self.cursor.execute(query, key)
            else:
                self.cursor.execute(query)

            if oneRow:
                rows = self.cursor.fetchone()
            else:
                rows = self.cursor.fetchall()
            
            if rows:
                if oneRow:
                    objects = dtoClass(*rows)
                else:
                    objects = [dtoClass(*row) for row in rows]
                return objects
            else:
                return None

        except sqlite3.Error as e:
            print(f"Error while executing query: {e}, {traceback.format_exc()}")
            return None

    def fetchDbData(self, params: list = list('*'), table_name: str = 'N', key: str = None) -> list:
        columns = ", ".join(params)
        if key:
            key = str(key)
            query = f"SELECT {columns} FROM {table_name} WHERE id = %s"
            self.cursor.execute(query, (key,))
        else:
            query = f"SELECT {columns} FROM {table_name}"
            self.cursor.execute(query)
        
        results = self.cursor.fetchall()
        
        return results

    def fetchQuery(self, query, all=False):
        self.cursor.execute(query)
        if all:
            return self.cursor.fetchall()
        else:
            return self.cursor.fetchone()
