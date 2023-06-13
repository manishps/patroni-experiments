import psycopg2
from threading import Thread
from typing import Union
import time
from datetime import datetime

class DataGenerator():
    """
    A class that writes data to the database at regular
    intervals to test
    :param 
    """
    def __init__(self, freq=1.0, table_name="dummy"):
        self.conn = psycopg2.connect(
                    database="postgres",
                        host="10.51.140.91",
                        user="postgres",
                        password="password",
                        port="5433")
        self.table_name = table_name
        self.create_table(self.table_name)
        self.writing_thread: Union[Thread, None] = None
        self.is_writing = False
        self.freq = freq
    
    def create_table(self, table_name):
        """
        Creates a table to write data into with the given
        name
        """
        with self.conn.cursor() as cur:
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                time TIMESTAMP NOT NULL
            )
            """)
        self.conn.commit()
    
    def writing_job(self):
        while self.is_writing:
            with self.conn.cursor() as cur:
                now = datetime.utcnow()
                now = str(now)
                cur.execute(f"""
                INSERT INTO {self.table_name} 
                    (time)
                VALUES 
                    ('{now}')
                """)
            self.conn.commit()
            time.sleep(self.freq)
                
    
    def start_writing(self):
        self.is_writing = True
        self.writing_thread = Thread(target=self.writing_job)
        self.writing_thread.start()
    
    def stop_writing(self):
        self.is_writing = False
        if self.writing_thread:
            self.writing_thread.join()
            self.writing_thread = None


if __name__ == "__main__":
    dg = DataGenerator(freq=0.1)
    dg.start_writing()
    time.sleep(10)
    dg.stop_writing()
