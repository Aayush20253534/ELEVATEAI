import sqlite3

conn = sqlite3.connect("Database_4.db")
cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS DATA_LOGIN(
    ID INTEGER PRIMARY KEY,
    EMAIL TEXT NOT NULL,
    LINKEDIN_ID TEXT NOT NULL,
    PASSWORD TEXT NOT NULL
)
""")

users = [
(1, "shreyaanshjain01@gmail.com", "https://www.linkedin.com/in/shreyaansh-jain-01", "Pillu_jain"),
(2, "shreyjain02@gmail.com", "https://www.linkedin.com/in/shrey-jain-02", "Shrey_jain"),
(3, "shreya03@gmail.com", "https://www.linkedin.com/in/shreya-03", "Shreya@3"),
(4, "aditya04@gmail.com", "https://www.linkedin.com/in/aditya-ranjan-04", "Aditya@4"),
(5, "mahikaverma05@gmail.com", "https://www.linkedin.com/in/mahika-verma-05", "Milee_verma"),
(6, "Aayushkumar06@gmail.com", "https://www.linkedin.com/in/aayaush-kumar-06", "Kumar_aayush"),
(7, "abhisheksingh07@gmail.com", "https://www.linkedin.com/in/abhishek-singh-07", "Abhi_07"),
(8, "soumyaasingh08@gmail.com", "https://www.linkedin.com/in/soumyaa-singh-08", "Soumyaa_08"),
(9, "kritikasingh09@gmail.com", "https://www.linkedin.com/in/kritika-singh-09", "Sheesh_kritika"),
(10, "dhruvagrawaal10@gmail.com", "https://www.linkedin.com/in/dhruv-agrawaal-10", "Dhruv_10"),
(11, "bhavyaadigra11@gmail.com", "https://www.linkedin.com/in/bhavyaa-digra-11", "Bhavyaa_11"),
(12, "ankitasahu12@gmail.com", "https://www.linkedin.com/in/ankita-sahu-12", "Ankita_12"),
(13, "pallavi13@gmail.com", "https://www.linkedin.com/in/pallavi-13", "Pallavi_13"),
(14, "amaanarif14@gmail.com", "https://www.linkedin.com/in/arif-amaan-14", "Ammy_exists"),
(15, "deepakkumar15@gmail.com", "https://www.linkedin.com/in/deepak-kumaar-15", "Deepak_15"),
(16, "yashsharma16@gmail.com", "https://www.linkedin.com/in/sharma-yash-16", "Sharma_16"),
(17, "harshranjan17@gmail.com", "https://www.linkedin.com/in/harsh-ranjan-17", "HR_17"),
(18, "vanshikayadvendu18@gmail.com", "https://www.linkedin.com/in/vanshihka-yadvendu-18", "Vaani_18"),
(19, "devmanitripathi19@gmail.com", "https://www.linkedin.com/in/dev-mani-tripathi-19", "DM_tripathi"),
(20, "anaranyosarkaar20@gmail.com", "https://www.linkedin.com/in/sarkaar-anaranyo-20", "Anaromous_20")
]


cursor.executemany(
"INSERT INTO DATA_LOGIN (ID, EMAIL, LINKEDIN_ID, PASSWORD) VALUES (?, ?, ?, ?)",
users
)


conn.commit()

print("Database uploaded successfully")

conn.close()