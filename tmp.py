parameter_dict = {
            1: 'Label',
            2: 'Scan direction',
            3: 'Efficiency (%)',
            4: 'Short-circuit current density (mA/cm²)',
            5: 'Open circuit voltage (V)',
            6: 'Fill factor',
            7: 'Maximum power (W)',
            8: 'Voltage at MPP (V)',
            9: 'Current density at MPP (mA/cm²)',
            10: 'Series resistance, Rs (ohm)',
            11: 'Shunt resistance, Rsh (ohm)',
            12: 'Active area, (cm²)',
            13: 'Light intensity (W/m²)',
            14: 'Distance to light source (mm)',
            15: 'Device order',
        }
keys_to_exclude = [12, 13, 14, 15]
keys_to_exclude.extend([1,2])
counter = 0
for i, value in parameter_dict.items():
    if i in keys_to_exclude:
        continue
    print(i, value)
    counter+=1
print(counter)