from __future__ import absolute_import
from twisted.trial import unittest
from twisted.internet.defer import inlineCallbacks

from twistar.exceptions import ReferenceNotSavedError

from .utils import Boy, Girl, tearDownDB, initDB, Registry, Comment, Category
from .utils import User, Avatar, Picture, FavoriteColor, Nickname, Blogpost
from six.moves import range


class RelationshipTest(unittest.TestCase):
    @inlineCallbacks
    def setUp(self):
        yield initDB(self)
        self.user = yield User(first_name="First", last_name="Last", age=10).save()
        self.avatar = yield Avatar(name="an avatar name", user_id=self.user.id).save()
        self.picture = yield Picture(name="a pic", size=10, user_id=self.user.id).save()
        self.favcolor = yield FavoriteColor(name="blue").save()
        self.boy = yield Boy(name="Robert").save()
        self.girl = yield Girl(name="Susan").save()
        self.config = Registry.getConfig()


    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB(self)


    @inlineCallbacks
    def test_polymorphic_get(self):
        bob = yield Nickname(value="Bob", nicknameable_id=self.boy.id, nicknameable_type="Boy").save()
        sue = yield Nickname(value="Sue", nicknameable_id=self.girl.id, nicknameable_type="Girl").save()

        nicknames = yield self.boy.nicknames.get()
        self.assertEqual(len(nicknames), 1)
        self.assertEqual(nicknames[0], bob)
        self.assertEqual(nicknames[0].value, bob.value)

        nicknames = yield self.girl.nicknames.get()
        self.assertEqual(len(nicknames), 1)
        self.assertEqual(nicknames[0], sue)
        self.assertEqual(nicknames[0].value, sue.value)

        boy = yield bob.nicknameable.get()
        self.assertEqual(boy, self.boy)

        girl = yield sue.nicknameable.get()
        self.assertEqual(girl, self.girl)


    @inlineCallbacks
    def test_polymorphic_set(self):
        nicknameone = yield Nickname(value="Bob").save()
        nicknametwo = yield Nickname(value="Bobby").save()
        yield self.boy.nicknames.set([nicknametwo, nicknameone])

        nicknames = yield self.boy.nicknames.get()
        self.assertEqual(len(nicknames), 2)
        # since the insert is asynchronous - two may have been inserted
        # before one
        if not nicknames[0] == nicknametwo:
            self.assertEqual(nicknames[0], nicknameone)
        if not nicknames[1] == nicknameone:
            self.assertEqual(nicknames[1], nicknametwo)

        boy = yield nicknameone.nicknameable.get()
        self.assertEqual(boy, self.boy)

        nickname = yield Nickname(value="Suzzy").save()
        yield nickname.nicknameable.set(self.girl)
        nicknames = yield self.girl.nicknames.get()
        self.assertEqual(len(nicknames), 1)
        self.assertEqual(nicknames[0], nickname)
        self.assertEqual(nicknames[0].value, nickname.value)


    @inlineCallbacks
    def test_belongs_to(self):
        user = yield self.picture.user.get()
        self.assertEqual(user, self.user)


    @inlineCallbacks
    def test_set_belongs_to(self):
        user = yield User(first_name="new one").save()
        yield self.picture.user.set(user)
        self.assertEqual(user.id, self.picture.user_id)


    @inlineCallbacks
    def test_set_on_unsaved(self):
        yield User(first_name="new one").save()
        picture = Picture(name="a pic")
        self.assertRaises(ReferenceNotSavedError, getattr, picture, 'user')


    @inlineCallbacks
    def test_clear_belongs_to(self):
        picture = yield Picture(name="a pic", size=10, user_id=self.user.id).save()
        yield picture.user.clear()
        user = yield picture.user.get()
        self.assertEqual(user, None)
        yield picture.refresh()
        user = yield picture.user.get()
        self.assertEqual(user, None)


    @inlineCallbacks
    def test_has_many(self):
        # First, make a few pics
        ids = [self.picture.id]
        for _ in range(3):
            pic = yield Picture(user_id=self.user.id).save()
            ids.append(pic.id)

        pics = yield self.user.pictures.get()
        picids = [p.id for p in pics]
        self.assertEqual(ids, picids)


    @inlineCallbacks
    def test_has_many_count(self):
        # First, make a few pics
        ids = [self.picture.id]
        for _ in range(3):
            pic = yield Picture(user_id=self.user.id).save()
            ids.append(pic.id)

        totalnum = yield self.user.pictures.count()
        self.assertEqual(totalnum, 4)


    @inlineCallbacks
    def test_has_many_count_nocache(self):
        # First, count comments
        totalnum = yield self.user.comments.count()
        self.assertEqual(totalnum, 0)

        for _ in range(3):
            yield Comment(user_id=self.user.id).save()

        totalnum = yield self.user.comments.count()
        self.assertEqual(totalnum, 3)


    @inlineCallbacks
    def test_has_many_get_with_args(self):
        # First, make a few pics
        ids = [self.picture.id]
        for _ in range(3):
            pic = yield Picture(user_id=self.user.id).save()
            ids.append(pic.id)

        pics = yield self.user.pictures.get(where=['name = ?', 'a pic'])
        self.assertEqual(len(pics), 1)
        self.assertEqual(pics[0].name, 'a pic')


    @inlineCallbacks
    def test_has_many_count_with_args(self):
        # First, make a few pics
        ids = [self.picture.id]
        for _ in range(3):
            pic = yield Picture(user_id=self.user.id).save()
            ids.append(pic.id)

        picsnum = yield self.user.pictures.count(where=['name = ?', 'a pic'])
        self.assertEqual(picsnum, 1)


    @inlineCallbacks
    def test_set_has_many(self):
        # First, make a few pics
        pics = [self.picture]
        for _ in range(3):
            pic = yield Picture(name="a pic").save()
            pics.append(pic)
        picids = [int(p.id) for p in pics]

        yield self.user.pictures.set(pics)
        results = yield self.user.pictures.get()
        resultids = [int(p.id) for p in results]
        picids.sort()
        resultids.sort()
        self.assertEqual(picids, resultids)

        # now try resetting
        pics = []
        for _ in range(3):
            pic = yield Picture(name="a pic").save()
            pics.append(pic)
        picids = [p.id for p in pics]

        yield self.user.pictures.set(pics)
        results = yield self.user.pictures.get()
        resultids = [p.id for p in results]
        self.assertEqual(picids, resultids)


    @inlineCallbacks
    def test_clear_has_many(self):
        pics = [self.picture]
        for _ in range(3):
            pic = yield Picture(name="a pic").save()
            pics.append(pic)

        yield self.user.pictures.set(pics)
        yield self.user.pictures.clear()

        userpics = yield self.user.pictures.get()
        self.assertEqual(userpics, [])

        # even go so far as to refetch user
        yield User.find(self.user.id)
        userpics = yield self.user.pictures.get()
        self.assertEqual(userpics, [])

        # picture records should be updated
        pics = yield Picture.find(where=["user_id=?", self.user.id])
        self.assertEqual(pics, [])

        # but still exist
        pics = yield Picture.all()
        self.assertEqual(len(pics), 4)


    @inlineCallbacks
    def test_has_one(self):
        avatar = yield self.user.avatar.get()
        self.assertEqual(avatar, self.avatar)


    @inlineCallbacks
    def test_set_has_one(self):
        avatar = yield Avatar(name="another").save()
        yield self.user.avatar.set(avatar)
        yield avatar.refresh()
        self.assertEqual(avatar.user_id, self.user.id)


    @inlineCallbacks
    def test_habtm(self):
        color = yield FavoriteColor(name="red").save()
        colors = [self.favcolor, color]
        colorids = [c.id for c in colors]
        yield FavoriteColor(name="green").save()

        args = {'user_id': self.user.id, 'favorite_color_id': colors[0].id}
        yield self.config.insert('favorite_colors_users', args)
        args = {'user_id': self.user.id, 'favorite_color_id': colors[1].id}
        yield self.config.insert('favorite_colors_users', args)

        newcolors = yield self.user.favorite_colors.get()
        newcolorids = [c.id for c in newcolors]
        self.assertEqual(newcolorids, colorids)


    @inlineCallbacks
    def test_habtm_with_joinwhere(self):
        color = yield FavoriteColor(name="red").save()
        colors = [self.favcolor, color]
        yield FavoriteColor(name="green").save()

        args = {'user_id': self.user.id, 'favorite_color_id': colors[0].id, 'palette_id': 1}
        yield self.config.insert('favorite_colors_users', args)
        args = {'user_id': self.user.id, 'favorite_color_id': colors[1].id, 'palette_id': 2}
        yield self.config.insert('favorite_colors_users', args)

        newcolors = yield self.user.favorite_colors.get(join_where=['palette_id = ?', 2])
        newcolorids = [c.id for c in newcolors]
        self.assertEqual(newcolorids, [colors[1].id])


    @inlineCallbacks
    def test_habtm_count(self):
        color = yield FavoriteColor(name="red").save()
        colors = [self.favcolor, color]
        yield FavoriteColor(name="green").save()

        args = {'user_id': self.user.id, 'favorite_color_id': colors[0].id}
        yield self.config.insert('favorite_colors_users', args)
        args = {'user_id': self.user.id, 'favorite_color_id': colors[1].id}
        yield self.config.insert('favorite_colors_users', args)

        newcolorsnum = yield self.user.favorite_colors.count()
        self.assertEqual(newcolorsnum, 2)


    @inlineCallbacks
    def test_habtm_get_with_args(self):
        color = yield FavoriteColor(name="red").save()
        colors = [self.favcolor, color]

        args = {'user_id': self.user.id, 'favorite_color_id': colors[0].id}
        yield self.config.insert('favorite_colors_users', args)
        args = {'user_id': self.user.id, 'favorite_color_id': colors[1].id}
        yield self.config.insert('favorite_colors_users', args)

        newcolor = yield self.user.favorite_colors.get(where=['name = ?', 'red'], limit=1)
        self.assertEqual(newcolor.id, color.id)


    @inlineCallbacks
    def test_habtm_count_with_args(self):
        color = yield FavoriteColor(name="red").save()
        colors = [self.favcolor, color]

        args = {'user_id': self.user.id, 'favorite_color_id': colors[0].id}
        yield self.config.insert('favorite_colors_users', args)
        args = {'user_id': self.user.id, 'favorite_color_id': colors[1].id}
        yield self.config.insert('favorite_colors_users', args)

        newcolorsnum = yield self.user.favorite_colors.count(where=['name = ?', 'red'])
        self.assertEqual(newcolorsnum, 1)


    @inlineCallbacks
    def test_set_habtm(self):
        user = yield User().save()
        color = yield FavoriteColor(name="red").save()
        colors = [self.favcolor, color]
        colorids = [c.id for c in colors]

        yield user.favorite_colors.set(colors)
        newcolors = yield user.favorite_colors.get()
        newcolorids = [c.id for c in newcolors]
        self.assertEqual(newcolorids, colorids)


    @inlineCallbacks
    def test_clear_habtm(self):
        user = yield User().save()
        color = yield FavoriteColor(name="red").save()
        colors = [self.favcolor, color]

        yield user.favorite_colors.set(colors)
        yield user.favorite_colors.clear()
        colors = yield user.favorite_colors.get()
        self.assertEqual(colors, [])


    @inlineCallbacks
    def test_clear_jointable_on_delete_habtm(self):
        user = yield User().save()
        color = yield FavoriteColor(name="red").save()
        colors = [self.favcolor, color]

        yield user.favorite_colors.set(colors)
        old_id = color.id
        yield color.delete()
        result = yield self.config.select('favorite_colors_users', where=['favorite_color_id = ?', old_id], limit=1)
        self.assertTrue(result is None)


    @inlineCallbacks
    def test_clear_jointable_on_delete_habtm_with_custom_args(self):
        join_tablename = 'posts_categories'
        post = yield Blogpost(title='headline').save()
        category = yield Category(name="personal").save()

        yield post.categories.set([category])
        cat_id = category.id
        yield category.delete()
        res = yield self.config.select(join_tablename, where=['category_id = ?', cat_id], limit=1)
        self.assertIsNone(res)


    @inlineCallbacks
    def test_set_habtm_blank(self):
        user = yield User().save()
        color = yield FavoriteColor(name="red").save()
        colors = [self.favcolor, color]

        yield user.favorite_colors.set(colors)
        # now blank out
        yield user.favorite_colors.set([])
        newcolors = yield user.favorite_colors.get()
        self.assertEqual(len(newcolors), 0)
