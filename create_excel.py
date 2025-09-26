import pandas as pd

# داده نمونه
data = {
    "name": ["علی رضایی", "سارا محمدی"],
    "numbers": ["02112345678,09121234567", "02187654321,09129876543"],
    "address": ["تهران، خیابان ولیعصر", "شیراز، بلوار مطهری"],
    "label": ["دوست", "همکار"]
}

# ایجاد DataFrame
df = pd.DataFrame(data)

# ذخیره به فایل Excel
df.to_excel("contacts_sample.xlsx", index=False)

print("فایل contacts_sample.xlsx ساخته شد ✅")