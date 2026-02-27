#
# test_session
#
#   Copyright (c) 2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import datetime
import os
import tempfile
import unittest.mock

import werkzeug.http

from ayame import session
from base import AyameTestCase


class SessionTestCase(AyameTestCase):

    def test_load(self):
        with unittest.mock.patch.dict(self.app.config):
            self.app.config['ayame.session.store'] = store = unittest.mock.Mock(spec=session.SessionStore)

            store.reset_mock()
            self.app.config['ayame.session.gc'] = 0.0
            session.load(self.app, {})
            store.gc.assert_not_called()
            store.load.assert_called_once()

            store.reset_mock()
            self.app.config['ayame.session.gc'] = 1.0
            session.load(self.app, {})
            store.gc.assert_called_once()
            store.load.assert_called_once()

    def test_save(self):
        with unittest.mock.patch.dict(self.app.config):
            self.app.config['ayame.session.store'] = store = unittest.mock.Mock(spec=session.SessionStore)
            store.save.return_value = 'sid'

            store.reset_mock()
            self.app.config['ayame.session.sliding'] = False
            sess = session.Session()
            self.assertIsNone(session.save(self.app, sess))

            store.reset_mock()
            self.app.config['ayame.session.sliding'] = True
            sess = session.Session()
            self.assertEqual(session.save(self.app, sess), ('Set-Cookie', 'session_id=sid; HttpOnly; Path=/'))

            store.reset_mock()
            self.app.config['ayame.session.sliding'] = True
            sess = session.Session()
            sess['a'] = 1
            self.assertEqual(session.save(self.app, sess), ('Set-Cookie', 'session_id=sid; HttpOnly; Path=/'))

            store.reset_mock()
            self.app.config['ayame.session.sliding'] = True
            sess = session.Session()
            sess.clear()
            expires = werkzeug.http.http_date(0)
            self.assertEqual(session.save(self.app, sess), ('Set-Cookie', f'session_id=; Expires={expires}; Max-Age=0; HttpOnly; Path=/'))

    def test_max_age(self):
        with unittest.mock.patch.dict(self.app.config):
            for max_age in (datetime.timedelta(seconds=0), 0, 0.0, None):
                with self.subTest(max_age=max_age):
                    self.app.config['ayame.session.max_age'] = max_age
                    self.assertIsNone(session.max_age(self.app))

            for max_age in (-datetime.timedelta(seconds=60), -60, -60.0):
                with self.subTest(max_age=max_age):
                    self.app.config['ayame.session.max_age'] = max_age
                    v = session.max_age(self.app)
                    self.assertIsNone(session.max_age(self.app))

            for max_age in (datetime.timedelta(seconds=60), 60, 60.0):
                with self.subTest(max_age=max_age):
                    self.app.config['ayame.session.max_age'] = max_age
                    v = session.max_age(self.app)
                    self.assertIsInstance(v, int)
                    self.assertEqual(v, 60)

        jst = datetime.timezone(datetime.timedelta(hours=9), 'JST')
        with unittest.mock.patch.dict(self.app.config):
            for expires in ('', 0, 0.0, None):
                with self.subTest(expires=expires):
                    self.app.config['ayame.session.expires'] = expires
                    self.assertIsNone(session.max_age(self.app))

            now = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=60)
            for expires in (now.ctime(), now.isoformat(), now, now.replace(tzinfo=None), now.astimezone(jst), int(now.timestamp()), now.timestamp(), None):
                with self.subTest(expires=expires):
                    self.app.config['ayame.session.expires'] = expires
                    self.assertIsNone(session.max_age(self.app))

            now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=3)
            for expires in (now.ctime(), now, now.replace(tzinfo=None), now.astimezone(jst), int(now.timestamp()), now.timestamp()):
                with self.subTest(expires=expires):
                    self.app.config['ayame.session.expires'] = expires
                    v = session.max_age(self.app)
                    self.assertIsInstance(v, int)
                    self.assertGreater(v, 60)

    def test_session(self):
        sess = session.Session({'a': 1})
        self.assertEqual(sess.sid, '')
        self.assertFalse(sess.modified)
        self.assertEqual(str(sess), "<Session {'a': 1}>")

        x = sess.copy()
        self.assertIsNot(x, sess)
        self.assertEqual(x, sess)
        self.assertEqual(x.sid, '')
        self.assertFalse(x.modified)
        self.assertEqual(str(x), "<Session {'a': 1}>")
        x.sid = ''
        x.modified = True
        self.assertEqual(x, sess)

        sess.sid = 'sid'
        sess['b'] = 2
        self.assertEqual(sess.sid, 'sid')
        self.assertTrue(sess.modified)
        self.assertEqual(str(sess), "<Session* {'a': 1, 'b': 2}>")

        x = sess.copy()
        self.assertIsNot(x, sess)
        self.assertEqual(x, sess)
        self.assertEqual(x.sid, 'sid')
        self.assertTrue(x.modified)
        self.assertEqual(str(x), "<Session* {'a': 1, 'b': 2}>")
        x.sid = ''
        x.modified = False
        self.assertEqual(x, sess)

    def test_session_store(self):
        class SessionStore(session.SessionStore):
            def load(self, value):
                return super().load(value)

            def save(self, sess):
                return super().save(sess)

            def drop(self, sess):
                super().drop(sess)

            def gc(self):
                super().gc()

        with self.assertRaises(TypeError):
            session.SessionStore()

        store = SessionStore()
        with self.assertRaises(NotImplementedError):
            store.load(None)
        with self.assertRaises(NotImplementedError):
            store.save(session.Session())
        self.assertIsNone(store.drop(session.Session()))
        self.assertIsNone(store.gc())


class FileSystemSessionTestCase(AyameTestCase):

    def setUp(self):
        self.session_dir = tempfile.TemporaryDirectory(prefix='ayame-')
        self.store = session.FileSystemSessionStore(self.session_dir.name)

    def tearDown(self):
        self.session_dir.cleanup()

    def ls(self):
        return os.listdir(self.store.path)

    def test_basic(self):
        for sid, m in (
            (None, False),
            ('', False),
            ('_', True),
        ):
            with self.subTest(value=repr(sid)):
                sess = self.store.load(sid)
                self.assertEqual(sess, {})
                self.assertNotEqual(sess.sid, sid)
                self.assertEqual(sess.modified, m)

        # save (modified == False)
        sess = self.store.load(None)
        self.assertTrue(self.store.save(sess))
        self.assertEqual(len(self.ls()), 0)
        # save (modified == True)
        sess = self.store.load(None)
        sid = sess.sid
        data = {'fs': True}
        sess.update(data)
        sess = self.store.load(self.store.save(sess))
        self.assertEqual(sess, data)
        self.assertEqual(sess.sid, sid)
        self.assertFalse(sess.modified)
        self.assertEqual(len(self.ls()), 1)

        # error on load
        with unittest.mock.patch.object(session, 'open', side_effect=OSError):
            sess = self.store.load(sid)
            self.assertEqual(sess, {})
            self.assertNotEqual(sess.sid, sid)
            self.assertTrue(sess.modified)
        # error on save
        sess = self.store.load(None)
        sess['fs'] = object()
        with self.assertRaises(TypeError):
            self.store.save(sess)
        self.assertEqual(len(self.ls()), 1)

    def test_drop(self):
        sess = self.store.load(None)
        self.store.drop(sess)
        self.assertEqual(len(self.ls()), 0)

        sess = self.store.load(None)
        sess['fs'] = True
        self.assertTrue(self.store.save(sess))
        self.assertEqual(len(self.ls()), 1)
        self.store.drop(sess)
        self.assertEqual(len(self.ls()), 0)

    def test_gc(self):
        # session file
        sess = self.store.load(None)
        sess['fs'] = True
        self.assertTrue(self.store.save(sess))
        self.assertEqual(len(self.ls()), 1)
        # temporary session file
        with open(os.path.join(self.store.path, f'{self.store._prefix}{self.__module__}'), 'w') as fp:
            fp.flush()
        self.assertEqual(len(self.ls()), 2)
        # directory
        os.mkdir(os.path.join(self.store.path, 'dir'))
        self.assertEqual(len(self.ls()), 3)

        self.store.max_age = datetime.timedelta(days=7).total_seconds()
        self.store.gc()
        self.assertEqual(len(self.ls()), 3)

        with unittest.mock.patch('os.remove', side_effect=OSError):
            self.store.max_age = -1
            self.store.gc()
            self.assertEqual(len(self.ls()), 3)

        with unittest.mock.patch('os.scandir', side_effect=OSError):
            self.store.max_age = -1
            self.store.gc()
            self.assertEqual(len(self.ls()), 3)

        self.store.max_age = -1
        self.store.gc()
        self.assertEqual(len(self.ls()), 2)
