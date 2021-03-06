# coding: utf-8
import os
import sys
from io import BytesIO
from PIL import Image, ImageFile, ImageOps
from django.conf import settings
from django.core.files.base import ContentFile

try:
    from sorl.thumbnail import ImageField
except ImportError:
    from django.db.models import ImageField


DEFAULT_SIZE = getattr(settings, 'DJANGORESIZED_DEFAULT_SIZE', [1920, 1080])
DEFAULT_QUALITY = getattr(settings, 'DJANGORESIZED_DEFAULT_QUALITY', 0)
DEFAULT_KEEP_META = getattr(settings, 'DJANGORESIZED_DEFAULT_KEEP_META', True)

alphabet = {'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
            'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
            'й': 'j', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
            'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
            'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch',
            'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'i', 'ь': '', 'э': 'e', 'ю': 'yu',
            'я': 'ya'}


class ResizedImageFieldFile(ImageField.attr_class):

    def save(self, name, content, save=True):
        content.file.seek(0)
        img = Image.open(content.file)
        
        name = ''.join(alphabet.get(w.encode('utf-8'), w) for w in name.lower())

        if not self.field.keep_meta:
            image_without_exif = Image.new(img.mode, img.size)
            image_without_exif.putdata(img.getdata())
            image_without_exif.format = img.format
            img = image_without_exif

        if self.field.crop:
            thumb = ImageOps.fit(
                img,
                self.field.size,
                Image.ANTIALIAS,
                centering=self.get_centring()
            )
        else:
            img.thumbnail(
                self.field.size,
                Image.ANTIALIAS,
            )
            thumb = img

        ImageFile.MAXBLOCK = max(ImageFile.MAXBLOCK, thumb.size[0] * thumb.size[1])
        new_content = BytesIO()
        thumb.save(new_content, format=img.format, quality=self.field.quality, **img.info)
        new_content = ContentFile(new_content.getvalue())

        super(ResizedImageFieldFile, self).save(name, new_content, save)

    def get_centring(self):
        vertical = {
            'top': 0,
            'middle': 0.5,
            'bottom': 1,
        }
        horizontal = {
            'left': 0,
            'center': 0.5,
            'right': 1,
        }
        return [
            vertical[self.field.crop[0]],
            horizontal[self.field.crop[1]],
        ]


class ResizedImageField(ImageField):

    attr_class = ResizedImageFieldFile

    def __init__(self, verbose_name=None, name=None, **kwargs):
        # migrate from 0.2.x
        depricated = ('max_width', 'max_height', 'use_thumbnail_aspect_ratio', 'background_color')
        for argname in depricated:
            if argname in kwargs:
                sys.stderr.write('Error: Keyword argument %s is deprecated for ResizedImageField, see README https://github.com/un1t/django-resized\n' % argname)
                del kwargs[argname]

        self.size = kwargs.pop('size', DEFAULT_SIZE)
        self.crop = kwargs.pop('crop', None)
        self.quality = kwargs.pop('quality', DEFAULT_QUALITY)
        self.keep_meta = kwargs.pop('keep_meta', DEFAULT_KEEP_META)
        super(ResizedImageField, self).__init__(verbose_name, name, **kwargs)


try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    rules = [
        (
            (ResizedImageField,),
            [],
            {
            },
        )
    ]
    add_introspection_rules(rules, ["^django_resized\.forms\.ResizedImageField"])
