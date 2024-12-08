import pandas as pd

# อ่านไฟล์ CSV
x = pd.read_csv("raw_data/affiliation_count.csv", encoding="utf-8")
y = pd.read_csv("raw_data/affiliation_count(extra).csv", encoding="utf-8")

# กรองข้อมูลที่มีคำว่า "Chulalongkorn" และ count น้อยกว่า 100
filtered = x[(x['Affiliation'].str.contains("Chulalongkorn", case=True)) & (x['count'] < 100)]

# รวมค่า count ของข้อมูลที่กรองไว้
total_count_to_add = filtered['count'].sum()

# อัปเดตค่า count ของ "Chulalongkorn University" (ที่มีค่า count > 10000)
x.loc[(x['Affiliation'] == "Chulalongkorn University") & (x['count'] > 10000), 'count'] += total_count_to_add

# ลบแถวที่กรองไว้
x = x[~((x['Affiliation'].str.contains("Chulalongkorn", case=True)) & (x['count'] < 100))]

# Merge ข้อมูลโดยเชื่อม x[affiliation] กับ y[organization]
merged = x.merge(y, left_on='Affiliation', right_on='Organization', how='left')

# เพิ่มค่า count จาก collabcount
merged['count'] = merged['count'] + merged['CollabCount'].fillna(0)
merged['count'] = merged['count'].astype(int)

# เก็บเฉพาะคอลัมน์ที่ต้องการใน x
x_updated = merged[['Affiliation','Country','count']]

# บันทึกผลลัพธ์กลับไปเป็นไฟล์ใหม่ (ถ้าต้องการ)
x_updated.to_csv("updated_affiliation_count.csv", index=False, encoding="utf-8")