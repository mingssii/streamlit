import pandas as pd

a_df = pd.read_csv("aiml_data.csv", encoding="latin1", index_col=0)
b_df = pd.read_csv("Cited_by.csv", encoding="latin1", index_col=0)
c_df = pd.read_csv("subject_area.csv", encoding="latin1", index_col=0)

# 1. แปลง Subject_area_code ใน a.csv ให้อยู่ในรูปแบบที่จับคู่กับ Subject_area_code ใน c.csv ได้
a_df["Subject_area_code"] = a_df["Subject_area_code"].str.rstrip('#').str.split('#')

# 2. แปลงข้อมูลใน b.csv ให้สามารถนำไป merge กับ a.csv ได้
b_df.rename(columns={'paperID': 'Id'}, inplace=True)

# 3. นำข้อมูลจาก b.csv ไป merge กับ a.csv โดยใช้ Id
merged_ab = pd.merge(a_df, b_df, on='Id', how='left')

# 4. แปลง Subject_area_code ใน a.csv ให้ขยายเป็นแถวที่แตกออกตาม Subject_area_code
expanded = merged_ab.explode('Subject_area_code')

# แปลง Subject_area_code ใน a_df เป็นชนิดข้อมูล string
a_df['Subject_area_code'] = a_df['Subject_area_code'].astype(str)

# แปลง Subject_area_code ใน c_df เป็นชนิดข้อมูล string
c_df['Subject_area_code'] = c_df['Subject_area_code'].astype(str)

# 5. นำข้อมูลจาก c.csv มา merge เพื่อให้ได้ชื่อเต็มของ Subject Area
final = pd.merge(expanded, c_df, how='left', left_on='Subject_area_code', right_on='Subject_area_code')
final['Subject_area_abbrev'] = final['Subject_area_abbrev_y']  # ใช้ข้อมูลจาก `_y`
final = final.drop(columns=['Subject_area_abbrev_x', 'Subject_area_abbrev_y'])
final['Ref_amount'] = final['Ref_amount'].fillna(0).astype(int)
final['Cited'] = final['Cited'].fillna(0).astype(int)
# 6. ผลลัพธ์สุดท้ายที่รวมข้อมูลทั้งหมด
final.to_csv("Cited.csv", index=False, encoding="utf-8")