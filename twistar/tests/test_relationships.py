from twisted.trial import unittest
from twisted.enterprise import adbapi
from twisted.internet.defer import inlineCallbacks

from twistar.exceptions import ReferenceNotSavedError

from utils import *

class RelationshipTest(unittest.TestCase):    
    @inlineCallbacks
    def setUp(self):
        yield initDB(self)
        self.user = yield User(first_name="First", last_name="Last", age=10).save()
        self.avatar = yield Avatar(name="an avatar name", user_id=self.user.id).save()
        self.picture = yield Picture(name="a pic", size=10, user_id=self.user.id).save()
        self.favcolor = yield FavoriteColor(name="blue").save()
        self.dog = yield Dog(name="Pluto").save()
        self.mother = yield Mother(name="Marge").save()
        self.father = yield Father(name="Homer").save()
        self.child1 = yield Child(name="Bart",parent_id=self.father.id,parent_type='father').save()
        self.child2 = yield Child(name="Lisa",parent_id=self.mother.id,parent_type='mother').save()
        self.child3 = yield Child(name="Maggie",parent_id=self.mother.id,parent_type='mother').save()
        self.child4 = yield Child(name="Dixie",parent_id=self.dog.id,parent_type='dog').save()
        self.config = Registry.getConfig()


    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB(self)            


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
        user = yield User(first_name="new one").save()
        picture = Picture(name="a pic")
        self.assertRaises(ReferenceNotSavedError, getattr, picture, 'user')


    @inlineCallbacks
    def test_clear_belongs_to(self):
        picture = yield Picture(name="a pic", size=10, user_id=self.user.id).save()
        yield picture.user.clear()
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
        picids = [pic.id for pic in pics]
        self.assertEqual(ids, picids)


    @inlineCallbacks
    def test_has_many_get_with_args(self):
        # First, make a few pics
        ids = [self.picture.id]
        for _ in range(3):
            pic = yield Picture(user_id=self.user.id).save()
            ids.append(pic.id)
            
        pics = yield self.user.pictures.get(where=['name = ?','a pic'])
        self.assertEqual(len(pics),1)
        self.assertEqual(pics[0].name,'a pic')


    @inlineCallbacks
    def test_set_has_many(self):
        # First, make a few pics
        pics = [self.picture]
        for _ in range(3):
            pic = yield Picture(name="a pic").save()
            pics.append(pic)
        picids = [int(pic.id) for pic in pics]

        yield self.user.pictures.set(pics)
        results = yield self.user.pictures.get()
        resultids = [int(pic.id) for pic in results]
        picids.sort()
        resultids.sort()
        self.assertEqual(picids, resultids)

        # now try resetting
        pics = []
        for _ in range(3):
            pic = yield Picture(name="a pic").save()
            pics.append(pic)
        picids = [pic.id for pic in pics]
        
        yield self.user.pictures.set(pics)
        results = yield self.user.pictures.get()
        resultids = [pic.id for pic in results]
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

        allpics = Picture.all()
        self.assertEqual(userpics, [])
        

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
        colorids = [color.id for color in colors]
        yield FavoriteColor(name="green").save()

        args = {'user_id': self.user.id, 'favorite_color_id': colors[0].id}
        yield self.config.insert('favorite_colors_users', args)
        args = {'user_id': self.user.id, 'favorite_color_id': colors[1].id}
        yield self.config.insert('favorite_colors_users', args)
        
        newcolors = yield self.user.favorite_colors.get()
        newcolorids = [color.id for color in newcolors]        
        self.assertEqual(newcolorids, colorids)


    @inlineCallbacks
    def test_habtm_get_with_args(self):
        color = yield FavoriteColor(name="red").save()
        colors = [self.favcolor, color]
        colorids = [color.id for color in colors]

        args = {'user_id': self.user.id, 'favorite_color_id': colors[0].id}
        yield self.config.insert('favorite_colors_users', args)
        args = {'user_id': self.user.id, 'favorite_color_id': colors[1].id}
        yield self.config.insert('favorite_colors_users', args)
        
        newcolor = yield self.user.favorite_colors.get(where=['name = ?','red'], limit=1)
        self.assertEqual(newcolor.id, color.id)


    @inlineCallbacks
    def test_set_habtm(self):
        user = yield User().save()
        color = yield FavoriteColor(name="red").save()
        colors = [self.favcolor, color]
        colorids = [color.id for color in colors]

        yield user.favorite_colors.set(colors)
        newcolors = yield user.favorite_colors.get()
        newcolorids = [color.id for color in newcolors]        
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
    def test_set_habtm_blank(self):
        user = yield User().save()
        color = yield FavoriteColor(name="red").save()
        colors = [self.favcolor, color]
        colorids = [color.id for color in colors]

        yield user.favorite_colors.set(colors)
        # now blank out
        yield user.favorite_colors.set([])
        newcolors = yield user.favorite_colors.get()
        self.assertEqual(len(newcolors), 0)

    @inlineCallbacks
    def test_get_poly_belongsto_bart_parent(self):
        child = yield Child.find(where=["name = ?", 'Bart'], limit=1)
        parent = yield child.parent.get()
        self.assertEqual(parent.name, 'Homer')

    @inlineCallbacks
    def test_get_poly_belongsto_lisa_maggie_parent(self):
        children = yield Child.find(where=["parent_type = ?", 'mother'])
        self.assertEqual(len(children), 2)

        for child in children:
            parent = yield child.parent.get()
            self.assertEqual(parent.name, 'Marge')

    @inlineCallbacks
    def test_get_poly_belongsto_all_child_and_check_names(self):
        children = yield Child.find()
        self.assertEqual(len(children), 4)

        for child in children:
            parent = yield child.parent.get()
            if child.name == 'Bart':
                self.assertEqual(parent.name, 'Homer')
            elif child.name == 'Dixie':
                self.assertEqual(parent.name, 'Pluto')
            else:
                self.assertEqual(parent.name, 'Marge')

    @inlineCallbacks
    def test_get_poly_hasmany_marge_sons(self):
        marge = yield Mother.find(where=["name = ?", 'Marge'], limit=1)
        sons = yield marge.parent.get()
        self.assertEqual(len(sons), 2)

    @inlineCallbacks
    def test_get_poly_hasmany_homer_son(self):
        son = yield self.father.parent.get()
        self.assertEqual(len(son), 1)
        self.assertEqual(son[0].name, 'Bart')

    @inlineCallbacks
    def test_get_poly_hasone_dog_son(self):
        son = yield self.dog.parent.get()
        self.assertEqual(son.name, 'Dixie')

