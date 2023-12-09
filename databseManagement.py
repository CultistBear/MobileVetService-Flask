import pymysql
import pymysql.cursors
from constants import RDS_ENDPOINT, DATABASE_NAME, DB_USERNAME, DB_PASSWORD

class DB:
    def __init__(self):
        self.connect()

    def connect(self):
        try:
            self.conn = pymysql.connect(
                host=RDS_ENDPOINT,
                user=DB_USERNAME,
                password=DB_PASSWORD,
                database=DATABASE_NAME,
                cursorclass=pymysql.cursors.DictCursor,
            )
        except pymysql.Error as e:
            print("Error connecting to the database:", e)

    def query(self, sql):
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()
            result = cursor.fetchall()
            cursor.close()
            return result
        except (pymysql.Error, AttributeError) as e:
            print("Error executing query:", e)
            try:
                self.connect() 
                cursor = self.conn.cursor()
                cursor.execute(sql)
                self.conn.commit()
                result = cursor.fetchall()
                cursor.close()
                return result
            except pymysql.Error as e:
                print("Error reconnecting to the database:", e)
                return None
