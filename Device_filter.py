from icecream import ic


class DeviceDetector:
    """
    Class to detect and filter devices and/or pixels.
    """

    def __init__(self, data_dict):
        self.smu_ones = None
        self.data = data_dict

    def detector(self):
        self.smu_ones = []
        for device, specs in self.data.items():
            for spec, value in specs.items():
                if spec == 'measurement device' and value == 'SMU':
                    self.smu_ones.append(device)
        self.smu_case()

    def smu_case(self):
        if not self.smu_ones:
            return
        else:
            pass
