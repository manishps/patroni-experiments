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
    :param 
    """
    def __init__(self, freq=0.1, rate=1.0, table_name="dummy"):
        self.conn = psycopg2.connect(
                        database="postgres",
                        host="10.51.140.34",
                        user="postgres",
                        password="password",
                        port="5000")
        self.table_name = table_name
        self.create_table()
        self.writing_thread: Union[Thread, None] = None
        self.is_writing = False
        self.freq = freq
        self.rate = rate
        self.payload = self.make_payload()
    
    def make_payload(self):
        """
        This function looks at the frequency and rate, and will
        construct a JSON object (in local directory) of the necessary
        size to ensure that we are transmitting rate MiB data / s
        """
        size = int(self.freq * self.rate)
        dictionary = {
            "a": "b" * size * int(1e6)
        }
        json_object = json.dumps(dictionary, indent=4)
        with open("payload.json", "w") as outfile:
            outfile.write(json_object)
        return json_object
    
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
        while self.is_writing:
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
            time.sleep(self.freq)
                
    
    def start_writing(self):
        """
        Starts the background data writing job
        """
        self.is_writing = True
        self.writing_thread = Thread(target=self.writing_job)
        self.writing_thread.start()
    
    def stop_writing(self):
        """
        Stops the background data writing job
        """
        self.is_writing = False
        if self.writing_thread:
            self.writing_thread.join()
            self.writing_thread = None


if __name__ == "__main__":
    dg = DataGenerator(freq=0.1, rate=1.0)
    dg.reset()
    dg.start_writing()
    time.sleep(10)
    dg.stop_writing()
