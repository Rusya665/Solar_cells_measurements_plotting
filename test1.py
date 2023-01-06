# class Test1:
#     test_var = 12
#     test_str = 12
#     test_list = []
#
#     def __init__(self, some_value=5):
#         self.some_value = some_value
#         self.test_var2 = 5
#         # self.test_var2 = self.var_do()
#         self.do_stuff()
#
#     def do_stuff(self):
#         self.test_var2 = 6
#         self.test_var = 1
#         self.test_str = 1
#         self.test_list.append(1)
from instruments import logger


class GrandPa:
    log_dict = {}

    def __init__(self, string: str):
        if not string.endswith('/'):
            string = string + '/'
        self.string = string
        self.var1 = 4
        print('The var1 is', self.var1)
        self.do_smth()

    @logger(log_dict)
    def do_smth(self):
        self.var1 = self.var1 + 1
        print('GrandPa says', self.var1)
        return self.var1


class Daddy(GrandPa):

    def __init__(self):
        self.dad_var1 = 42
        super().__init__(string=self.string, )
        # self.string = string
        for h in range(3):
            h += 1
            self.do_like_dad()

    @logger(GrandPa.log_dict)
    def do_like_dad(self, g=10):
        self.dad_var1 = self.dad_var1 + 2
        self.var1 = self.var1 + 1
        print('Daddy says', self.var1)
        print(f'Daddy prints {self.string}')
        return self.dad_var1, self.var1, g



