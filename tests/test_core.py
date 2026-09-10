import unittest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import (
    get_password_hash, verify_password,
    encrypt_token, decrypt_token,
    create_access_token, decode_access_token
)
from app.core.database import Base
from app.models.user import User
from app.models.social_account import SocialAccount
from app.models.post import Post
from app.services.publisher import PublisherService

class TestCoreEngine(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()

    def test_password_hashing(self):
        plain = "MySecret123!"
        hashed = get_password_hash(plain)
        self.assertTrue(verify_password(plain, hashed))
        self.assertFalse(verify_password("WrongSecret", hashed))

    def test_token_encryption(self):
        token = "EAAFlkj234098sf098234ljksdf098"
        encrypted = encrypt_token(token)
        self.assertNotEqual(token, encrypted)
        decrypted = decrypt_token(encrypted)
        self.assertEqual(token, decrypted)

    def test_jwt_generation_and_decoding(self):
        user_id = 42
        jwt_token = create_access_token(user_id)
        decoded_id = decode_access_token(jwt_token)
        self.assertEqual(str(user_id), decoded_id)

    def test_publisher_simulation(self):
        # 1. Create a user
        user = User(email="tester@example.com", hashed_password="hashed_pwd", full_name="Tester")
        self.db.add(user)
        self.db.commit()

        # 2. Add simulated Facebook and LinkedIn accounts
        fb_acc = SocialAccount(
            user_id=user.id,
            platform="facebook",
            platform_account_id="123456789",
            account_name="Test Business Page",
            account_type="page",
            encrypted_access_token=encrypt_token("sim_fb_token_123")
        )
        li_acc = SocialAccount(
            user_id=user.id,
            platform="linkedin",
            platform_account_id="urn:li:person:test1234",
            account_name="Test Member",
            account_type="profile",
            encrypted_access_token=encrypt_token("sim_li_token_456")
        )
        self.db.add_all([fb_acc, li_acc])
        self.db.commit()

        # 3. Create a post targeted to both platforms
        post = Post(
            user_id=user.id,
            content="Hello World! Automated multi-platform post testing.",
            target_platforms="facebook,linkedin",
            status="scheduled",
            scheduled_at=datetime.now(timezone.utc)
        )
        self.db.add(post)
        self.db.commit()

        # 4. Dispatch post via PublisherService
        result = PublisherService.dispatch_post(self.db, post.id)
        
        # Verify success
        self.assertEqual(result["status"], "published")
        self.assertEqual(result["successes"], 2)
        self.assertEqual(result["failures"], 0)

        # Check updated DB record
        self.db.refresh(post)
        self.assertEqual(post.status, "published")
        self.assertEqual(len(post.dispatch_logs), 2)
        for log in post.dispatch_logs:
            self.assertEqual(log.status, "success")
            self.assertIsNotNone(log.platform_post_id)

if __name__ == "__main__":
    unittest.main()
