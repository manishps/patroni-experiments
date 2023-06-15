from threading import Thread
from typing import Union
import time
from datetime import datetime
import json
import psycopg2

class DataGenerator():
    """
    A class that writes data to the database at regular
    intervals to test
    :param freq=0.1: How often to write data (s)
    :param rate=1.0: How many MiB to write per second
    :table_name="dummy": Name of the table to store data in
    """
    def __init__(self, freq=0.1, rate=1.0, table_name="dummy"):
        with open("../.config/.HOST_4", "r") as fin:
            self.proxy_host = fin.readline()
        self.conn = self.block_for_writable_connection(initial=True)
        self.table_name = table_name
        self.create_table()
        self.writing_thread: Union[Thread, None] = None
        self.is_starting = False
        self.end_seconds: Union[float, None] = None
        self.freq = freq
        self.rate = rate
        self.payload = self.make_payload()
    
    def make_payload(self):
        """
        This function looks at the frequency and rate, and will
        construct a JSON object (in local directory) of the necessary
        size to ensure that we are transmitting rate MiB data / s
        :returns: a json.dumps object which can be written during DB
        calls to obtain the desired rate
        """
        size = int(self.freq * self.rate)
        dictionary = {
            "a": "b" * size * int(1e6)
        }
        json_object = json.dumps(dictionary, indent=4)
        with open("payload.json", "w") as outfile:
            outfile.write(json_object)
        return json_object
    
    def block_for_writable_connection(self, initial=False):
        """
        """
        DELAY = 0.1
        if not initial and self.conn:
            self.conn.close()
        conn = None
        while conn == None:
            try:
                conn = psycopg2.connect(
                                database="postgres",
                                host=self.proxy_host,
                                user="postgres",
                                password="password",
                                port="5000")
            except:
                pass
            if conn == None:
                time.sleep(DELAY)
            if conn and conn.readonly:
                conn.close()
                conn = None
                time.sleep(DELAY)
        return conn
    
    def reset(self):
        """
        Drops existing table and recreates it
        """
        with self.conn.cursor() as cur:
            cur.execute(f"""
            DROP TABLE IF EXISTS {self.table_name};
            """)
        self.create_table()
    
    def create_table(self):
        """
        Creates a table to write data into with the given
        name
        """
        with self.conn.cursor() as cur:
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id SERIAL PRIMARY KEY,
                time TIMESTAMP NOT NULL,
                payload JSON
            );
            """)
        self.conn.commit()
    
    def writing_job(self):
        """
        The function run in the background to write at a constant rate
        """
        began_end_at: Union[datetime, None] = None
        while self.is_starting or self.end_seconds != None:
            start_time = datetime.now()
            try:
                with self.conn.cursor() as cur:
                    now = datetime.utcnow()
                    now = str(now)
                    cur.execute(f"""
                    INSERT INTO {self.table_name} 
                        (time, payload)
                    VALUES 
                        ('{now}', '{self.payload}')
                    """)
                self.conn.commit()
                if self.end_seconds != None:
                    if began_end_at == None:
                        began_end_at = datetime.now()
                    else:
                        time_finishing = (datetime.now() - began_end_at).total_seconds()
                        if time_finishing > self.end_seconds:
                            self.end_seconds = None
            except Exception:
                self.conn = self.block_for_writable_connection()
            end_time = datetime.now()
            buffer_time = self.freq - (end_time - start_time).total_seconds()
            if buffer_time > 0:
                time.sleep(buffer_time)
                
    
    def start_writing(self):
        """
        Starts the background data writing job
        """
        self.is_starting = True
        self.writing_thread = Thread(target=self.writing_job)
        self.writing_thread.start()
    
    def stop_writing(self):
        """
        Stops the background data writing job
        """
        self.is_starting = False
        self.end_seconds = None
        if self.writing_thread:
            self.writing_thread.join()
            self.writing_thread = None
    
    def write_for_x_seconds_then_stop(self, x: float):
        self.is_starting = None
        self.end_seconds = x
        if self.writing_thread:
            self.writing_thread.join()
            self.writing_thread = None


if __name__ == "__main__":
    dg = DataGenerator(freq=0.5, rate=1.0)
    dg.reset()
    dg.start_writing()
    time.sleep(10)
    dg.stop_writing()
