# from test1 import Test1
#
#
# class Test2(Test1):
#     def __init__(self, some_value2=5):
#         super().__init__()
#         self.some_value = some_value2
#         self.test_a = None
#         self.do_stuff2()
#
#     # @staticmethod
#     def do_stuff2(self):
#         print('var test', Test1.test_var)
#         print('str test', Test1.test_str)
#         print('list test', Test1.test_list)
#         print('var2 test', self.test_var2)
#
# # Test1()
# Test2()
from test1 import Daddy, GrandPa
from instruments import logger


class Child(Daddy):
    def __init__(self, string=None):
        self.string = string
        super().__init__()
        print(self.string)
        self.do_like_kid()

    @logger(GrandPa.log_dict)
    def do_like_kid(self):
        # self.var1 = self.var1 + 1
        print('Child says', self.var1)
        print('Child also believe in', self.dad_var1)


# GrandPa('hello')
# Daddy('hello')
Child('hello')
print(GrandPa.log_dict)

