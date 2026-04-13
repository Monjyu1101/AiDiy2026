# -*- coding: utf-8 -*-

import sys
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import core_models as models
import core_schema as schemas
from core_crud.C利用者 import authenticate_C利用者, create_C利用者
from core_router.C利用者 import update_C利用者


class C利用者パスワードテスト(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False})
        models.Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_初期データ相当の作成ではプレーンテキストを保持できる(self):
        user = create_C利用者(
            self.db,
            schemas.C利用者Create(
                利用者ID='plain',
                利用者名='plain',
                パスワード='secret',
                権限ID='1',
                利用者備考='seed',
                有効=True,
            ),
            認証情報={'利用者ID': 'system', '利用者名': 'system'},
            hash_password=False,
        )
        self.assertEqual(user.パスワード, 'secret')
        self.assertIsNotNone(authenticate_C利用者(self.db, 'plain', 'secret'))

    def test_通常作成ではハッシュ保存し認証できる(self):
        user = create_C利用者(
            self.db,
            schemas.C利用者Create(
                利用者ID='hash',
                利用者名='hash',
                パスワード='secret',
                権限ID='1',
                利用者備考='normal',
                有効=True,
            ),
            認証情報={'利用者ID': 'system', '利用者名': 'system'},
        )
        self.assertNotEqual(user.パスワード, 'secret')
        self.assertTrue(user.パスワード.startswith('$2'))
        self.assertIsNotNone(authenticate_C利用者(self.db, 'hash', 'secret'))

    def test_パスワード変更時はハッシュ保存へ切り替わる(self):
        target = create_C利用者(
            self.db,
            schemas.C利用者Create(
                利用者ID='target',
                利用者名='target',
                パスワード='initial',
                権限ID='1',
                利用者備考='seed',
                有効=True,
            ),
            認証情報={'利用者ID': 'system', '利用者名': 'system'},
            hash_password=False,
        )

        updater = models.C利用者(
            利用者ID='admin',
            利用者名='Administrator',
            パスワード='dummy',
            権限ID='1',
            利用者備考=None,
            有効=True,
            登録日時='2026-01-01 00:00:00',
            登録利用者ID='system',
            登録利用者名='system',
            登録端末ID='localhost',
            更新日時='2026-01-01 00:00:00',
            更新利用者ID='system',
            更新利用者名='system',
            更新端末ID='localhost',
        )

        response = update_C利用者(
            schemas.C利用者Update(利用者ID='target', パスワード='changed'),
            db=self.db,
            現在利用者=updater,
        )

        self.assertEqual(response.status, 'OK')
        self.db.refresh(target)
        self.assertNotEqual(target.パスワード, 'changed')
        self.assertTrue(target.パスワード.startswith('$2'))
        self.assertIsNone(authenticate_C利用者(self.db, 'target', 'initial'))
        self.assertIsNotNone(authenticate_C利用者(self.db, 'target', 'changed'))


if __name__ == '__main__':
    unittest.main()
