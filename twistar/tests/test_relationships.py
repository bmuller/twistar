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
        self.image = yield Image(name="Picasso_dream").save()
        self.article = yield Article(name="My_new_article").save()
        self.sound = yield Sound(name="Jazz").save()
        self.catalogentry1 = yield Catalogentry(name="CoolJazz",resource_id=self.sound.id,resource_type='sound').save()
        self.catalogentry2 = yield Catalogentry(name="An_article",resource_id=self.article.id,resource_type='article').save()
        self.catalogentry3 = yield Catalogentry(name="Another_article",resource_id=self.article.id,resource_type='article').save()
        self.catalogentry4 = yield Catalogentry(name="Some_catalogued_image",resource_id=self.image.id,resource_type='image').save()
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
    def test_poly_get_belongsto_catalogentry_to_sound_resource(self):
        catalogentry = yield Catalogentry.find(where=["name = ?", 'CoolJazz'], limit=1)
        resource = yield catalogentry.resource.get()
        self.assertEqual(resource.name, 'Jazz')


    @inlineCallbacks
    def test_poly_get_belongsto_catalogentries_to_article_resource(self):
        catalogentries = yield Catalogentry.find(where=["resource_type = ?", 'article'])
        self.assertEqual(len(catalogentries), 2)

        for catalogentry in catalogentries:
            resource = yield catalogentry.resource.get()
            self.assertEqual(resource.name, 'My_new_article')


    @inlineCallbacks
    def test_poly_get_belongsto_all_catalogentries_and_check_names(self):
        catalogentries = yield Catalogentry.find()
        self.assertEqual(len(catalogentries), 4)

        for catalogentry in catalogentries:
            resource = yield catalogentry.resource.get()
            if catalogentry.name == 'CoolJazz':
                self.assertEqual(resource.name, 'Jazz')
            elif catalogentry.name == 'Some_catalogued_image':
                self.assertEqual(resource.name, 'Picasso_dream')
            else:
                self.assertEqual(resource.name, 'My_new_article')


    @inlineCallbacks
    def test_poly_get_hasmany_article_resource_catalogentries(self):
        my_new_article = yield Article.find(where=["name = ?", 'My_new_article'], limit=1)
        articles = yield my_new_article.resource.get()
        self.assertEqual(len(articles), 2)


    @inlineCallbacks
    def test_poly_get_hasmany_sound_resource_catalogentry(self):
        sound = yield self.sound.resource.get()
        self.assertEqual(len(sound), 1)
        self.assertEqual(sound[0].name, 'CoolJazz')


    @inlineCallbacks
    def test_poly_get_hasone_image_resource_catalogentry(self):
        image = yield self.image.resource.get()
        self.assertEqual(image.name, 'Some_catalogued_image')


    @inlineCallbacks
    def test_poly_set_hasone(self):
        catalogentry = yield Catalogentry(name="Fuffy").save()
        yield self.image.resource.set(catalogentry)
        yield catalogentry.refresh()
        self.assertEqual(catalogentry.resource_id, self.image.id)
        self.assertEqual(catalogentry.resource_type, 'image')


    @inlineCallbacks
    def test_poly_set_hasmany(self):
        # Generate some catalog entries...
        entries = [self.catalogentry1]

        for _ in range(3):
            entry = yield Catalogentry(name="another catalog entry").save()
            entries.append(entry)
        entryids = [int(entry.id) for entry in entries]

        yield self.sound.resource.set(entries)
        results = yield self.sound.resource.get()
        self.assertEqual(len(results), 4)
        resultids = [int(entry.id) for entry in results]
        entryids.sort()
        resultids.sort()
        self.assertEqual(entryids, resultids)

        # now try resetting
        entries = []
        for _ in range(3):
            entry = yield Catalogentry(name="another catalog entry").save()
            entries.append(entry)
        entryids = [entry.id for entry in entries]
        
        yield self.sound.resource.set(entries)
        results = yield self.sound.resource.get()
        resultids = [entry.id for entry in results]
        self.assertEqual(entryids, resultids)        


    @inlineCallbacks
    def test_poly_clear_has_many(self):
        catentries = yield self.article.resource.get()
        for _ in range(3):
            catentry = yield Catalogentry(name="another catalog entry").save()
            catentries.append(catentry)

        yield self.article.resource.set(catentries)

        arresources = yield self.article.resource.get()
        self.assertEqual(len(arresources), 5)

        yield self.article.resource.clear()
        
        arresources = yield self.article.resource.get()
        self.assertEqual(arresources, [])

