import sys

import time
from exprunner import Runner

class Viewer:
    """
    A helper function that boots up all the nodes so that 
    we can view the data
    """
    def __init__(self):
        self.runner = Runner(viewer=True)
    
    def view(self):
        try:
            self.runner.reset(clear_data=False)
            print("System live!")
        except:
            print("Shutting down")
            self.runner.stop()
        try:
            while True:
                time.sleep(0.1)
        except:
            print("Shutting down")
            self.runner.stop()

if __name__ == "__main__":
    viewer = Viewer()
    viewer.view()