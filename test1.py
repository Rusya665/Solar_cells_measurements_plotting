import pandas as pd
import numpy as np

def print_IV_parameters():
    # Path to the file
    file_path = r'C:/Users/runiza.TY2206042/OneDrive - O365 Turun yliopisto/IV_plotting_project/Input/scanCVivsE-R1.csv'

    # Extract data using the provided function
    V, I = ExtractIVData_PS(file_path)

    # Divide data into forward and reverse scans
    V_forward, I_forward = divideIVdata(V, I)

    # Calculate Jsc and Voc (simplified calculations)
    Jsc = abs(np.trapz(I_forward, V_forward))
    Voc = max(V_forward)

    # Print the values
    print('Jsc:', Jsc)
    print('Voc:', Voc)

def ExtractIVData_PS(path):
    df = pd.read_csv(path, engine='python', header=None, encoding='UTF-16',
                     skiprows=6, keep_default_na=True, na_filter=False, names=['V', 'I'])
    df = df[df['I'].notna()]  # Picking only the data which is not "Nan" <- dropping the last row
    V = df['V'].values.astype(float)
    I = df['I'].values.astype(float)
    return V, I

def divideIVdata(V, I):
    V_forward = []
    I_forward = []
    for i in range(1, len(V)):
        if V[i] > V[i-1]:
            if not V_forward:
                V_forward.append(V[i-1])
                I_forward.append(I[i-1])
            V_forward.append(V[i])
            I_forward.append(I[i])
    return np.array(V_forward), np.array(I_forward)

# Run the function
print_IV_parameters()
