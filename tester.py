import os
from read_iv import ReadData


def do_smth():
    print(ReadData.raw_data)
    print("")


some_data = {}

some_data["key1"] = (1, 2, 3)
some_data["key1"] = (4, 5)
some_data["key2"] = ("hello")
print(some_data)
# class Parental:
#     def __init__(self, x_value: float, y_value: float, str_value: str, new_value=None):
#         self.x = x_value
#         self.y = y_value
#         self.str_value = str_value
#         self.new_value = self.function_1(new_value)
#
#     def function_1(self, some_value):
#         return self.x + some_value
#
#
# class Child(Parental):
#     def __init__(self, str_value: str, new_value=None):
#         super().__init__(str_value, new_value)
#         self.str_value = str_value
#     # def print_1(self):
#     #     print(new_value)
#
#
# Parental(1.3, 4.3, 'Hello', 5)
# # f = Child('Wow', True)
# print(Child)