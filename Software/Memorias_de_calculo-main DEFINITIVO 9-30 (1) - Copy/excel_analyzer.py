import pandas as pd
import os

def analyze_excel(file_path):
    try:
        xls = pd.ExcelFile(file_path)
        print(f"--- Analyzing {os.path.basename(file_path)} ---")
        for sheet_name in xls.sheet_names:
            print(f"  Sheet: {sheet_name}")
            try:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                print(f"    Headers: {list(df.columns)}")
            except Exception as e:
                print(f"    Could not read sheet: {e}")
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")

print("Analyzing Excel files...")
analyze_excel("c:\\Users\\ereyes25052\\Desktop\\Programación\\Memorias_de_calculo-main 9-10\\Límites de deflexión.xlsx")
print("\n" + "="*50 + "\n")
analyze_excel("c:\\Users\\ereyes25052\\Desktop\\Programación\\Memorias_de_calculo-main 9-10\\Límites de deflexión (Actualizado).xlsx")
