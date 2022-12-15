

class ReadData:
    def __init__(self, path_file):
        self.path_file = path_file

    def read_file(self):
        with open(self.path_file):
            for