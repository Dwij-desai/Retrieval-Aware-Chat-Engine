import pandas as pd

# Update the filename below if the unzipped excel file has a slightly different name
record_set_df = pd.read_excel("Online_Retail.xlsx")
print(record_set_df.head(20))
