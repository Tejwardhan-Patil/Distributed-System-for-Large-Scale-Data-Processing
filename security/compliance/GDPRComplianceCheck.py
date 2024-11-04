import json
import os
import logging
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
import sqlite3

# Logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GDPRComplianceCheck")

# Database setup (SQLite)
db_file = "compliance.db"
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# GDPR Settings (replace with environment variables or secure store)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
DATA_RETENTION_DAYS = 365  # Personal data retention policy
CONSENT_REQUIRED_FOR_PROCESSING = True
USER_DATA_ACCESS_ENABLED = True

fernet = Fernet(ENCRYPTION_KEY)

# GDPR Compliance Checks

class GDPRCompliance:
    def __init__(self):
        self.create_compliance_tables()

    def create_compliance_tables(self):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_data (
                user_id INTEGER PRIMARY KEY,
                data TEXT,
                consent BOOLEAN,
                created_at DATE,
                encrypted BOOLEAN
            )
        ''')
        conn.commit()

    def store_user_data(self, user_id, data, consent):
        encrypted_data = fernet.encrypt(data.encode()) if consent else None
        created_at = datetime.now()
        cursor.execute('''
            INSERT INTO user_data (user_id, data, consent, created_at, encrypted) VALUES (?, ?, ?, ?, ?)
        ''', (user_id, encrypted_data, consent, created_at, True))
        conn.commit()
        logger.info(f"User data stored for user_id {user_id} with consent {consent}")

    def check_data_retention_policy(self):
        expired_date = datetime.now() - timedelta(days=DATA_RETENTION_DAYS)
        cursor.execute('''
            DELETE FROM user_data WHERE created_at < ? AND consent = 0
        ''', (expired_date,))
        conn.commit()
        logger.info(f"Data older than {DATA_RETENTION_DAYS} days has been removed")

    def check_consent_before_processing(self, user_id):
        cursor.execute('''
            SELECT consent FROM user_data WHERE user_id = ?
        ''', (user_id,))
        consent = cursor.fetchone()
        if consent and consent[0]:
            logger.info(f"Consent for processing exists for user_id {user_id}")
            return True
        logger.warning(f"No consent for processing for user_id {user_id}")
        return False

    def handle_data_access_request(self, user_id):
        if not USER_DATA_ACCESS_ENABLED:
            logger.error("User data access is currently disabled.")
            return

        cursor.execute('''
            SELECT data, encrypted FROM user_data WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()

        if result:
            data, encrypted = result
            decrypted_data = fernet.decrypt(data).decode() if encrypted else data
            logger.info(f"Access request fulfilled for user_id {user_id}. Data: {decrypted_data}")
            return decrypted_data
        logger.warning(f"No data found for user_id {user_id}")
        return None

    def handle_data_erasure_request(self, user_id):
        cursor.execute('''
            DELETE FROM user_data WHERE user_id = ?
        ''', (user_id,))
        conn.commit()
        logger.info(f"Data erasure request fulfilled for user_id {user_id}")

    def anonymize_data(self):
        cursor.execute('''
            SELECT user_id, data FROM user_data WHERE consent = 1
        ''')
        rows = cursor.fetchall()

        for row in rows:
            user_id, data = row
            anonymized_data = self.anonymize_user_data(data)
            cursor.execute('''
                UPDATE user_data SET data = ? WHERE user_id = ?
            ''', (anonymized_data, user_id))
        conn.commit()
        logger.info("User data anonymized for all consented records")

    def anonymize_user_data(self, data):
        # Replace PII with random or masked values
        anonymized = data.replace("Paul", "User123").replace("123456789", "XXXXXXX")
        return anonymized

    def check_encryption(self, user_id):
        cursor.execute('''
            SELECT encrypted FROM user_data WHERE user_id = ?
        ''', (user_id,))
        encrypted = cursor.fetchone()
        if encrypted and encrypted[0]:
            logger.info(f"Data for user_id {user_id} is encrypted")
            return True
        logger.warning(f"Data for user_id {user_id} is not encrypted")
        return False

# Instantiate GDPRCompliance class
gdpr_compliance = GDPRCompliance()

# Usage
def run_gdpr_checks():
    # Insert some user data (user_id, data, consent)
    gdpr_compliance.store_user_data(1, "Paul, SSN: 123456789", True)
    
    # Check if consent is present before processing data
    gdpr_compliance.check_consent_before_processing(1)
    
    # Handle data access request (GDPR Article 15)
    gdpr_compliance.handle_data_access_request(1)
    
    # Handle data erasure request (GDPR Article 17)
    gdpr_compliance.handle_data_erasure_request(1)
    
    # Ensure data retention policies are met
    gdpr_compliance.check_data_retention_policy()
    
    # Anonymize data to comply with GDPR
    gdpr_compliance.anonymize_data()
    
    # Verify if data is encrypted
    gdpr_compliance.check_encryption(1)

if __name__ == "__main__":
    run_gdpr_checks()