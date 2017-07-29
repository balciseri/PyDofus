#!/usr/bin/python3
# -*- coding: utf-8 -*-

import zlib, tempfile, io
from ._binarystream import _BinaryStream
from collections import OrderedDict

class InvalidELEFile(Exception):
    def __init__(self, message):
        super(InvalidELEFile, self).__init__(message)
        self.message = message

class ELE:
    def __init__(self, stream):
        self._stream = stream

    def read(self):
        ele_uncompressed = tempfile.TemporaryFile()
        ele_uncompressed.write(zlib.decompress(self._stream.read()))
        ele_uncompressed.seek(0)

        raw = _BinaryStream(ele_uncompressed, True)

        ele = Element(raw)
        ele.read()

        ele_uncompressed.close()

        return ele.get_dict()


class Element:
    def __init__(self, raw):
        self._raw = raw
        self.file_version = 0
        self.elements_count = 0
        self._elements_map = OrderedDict()
        self._elements_index = OrderedDict()
        self._jpg_map = OrderedDict()

    def read(self):
        header = self._raw.read_char()
        if header != 69:
            raise InvalidELEFile("Unknown file format")
        self.file_version = self._raw.read_char()
        self.elements_count = self._raw.read_uint32()

        skip_len = 0
        for i in range(0, self.elements_count):
            if self.file_version >= 9:
                skip_len = self._raw.read_uint16()
            ed_id = self._raw.read_int32()
            if self.file_version <= 8:
                self._elements_index[ed_id] = self._raw.position()
                self._read_element(ed_id)
            else:
                self._elements_index[ed_id] = self._raw.position()
                self._raw.position(self._raw.position() + (skip_len - 4))
        if self.file_version >= 8:
            gfx_count = self._raw.read_int32()
            for i in range(0, gfx_count):
                gfx_id = self._raw.read_int32()
                self._jpg_map[gfx_id] = True
        for key in self._elements_index.keys():
            self._read_element(key)

    def get_dict(self):
        ret = OrderedDict()
        ret['file_version'] = self.file_version
        ret['elements_count'] = self.elements_count
        ret['elements_map'] = OrderedDict((key, value.get_dict()) for key, value
                                          in self._elements_map.items())
        return ret

    def _read_element(self, ele_id):
        self._raw.position(self._elements_index[ele_id])
        ele_type = self._raw.read_char()
        gfx_ele_data = _GraphicalElementFactory.get_graphical_element_data(
            ele_id, ele_type)
        if not gfx_ele_data:
            return None
        gfx_ele_data.read(self._raw, self.file_version)
        self._elements_map[ele_id] = gfx_ele_data
        return gfx_ele_data


class _GraphicalElementFactory:
    @classmethod
    def get_graphical_element_data(cls, ele_id, ele_type):
        if ele_type == 0:
            return _NormalGraphicalElementData(ele_id, ele_type)
        elif ele_type == 1:
            return _BoundingBoxGraphicalElementData(ele_id, ele_type)
        elif ele_type == 2:
            return _AnimatedGraphicalElementData(ele_id, ele_type)
        elif ele_type == 3:
            return _EntityGraphicalElementData(ele_id, ele_type)
        elif ele_type == 4:
            return _ParticlesGraphicalElementData(ele_id, ele_type)
        elif ele_type == 5:
            return _BlendedGraphicalElementData(ele_id, ele_type)
        else:
            return None


class _GraphicalElementData:
    def __init__(self, id, type):
        self.id = id
        self.type = type

    def get_dict(self):
        ret = OrderedDict()
        ret['id'] = self.id
        ret['type'] = self.type
        return ret


class _NormalGraphicalElementData(_GraphicalElementData):
    def __init__(self, id, type):
        super(_NormalGraphicalElementData, self).__init__(id, type)
        self.gfx_id = 0
        self.height = 0
        self.horizontal_symetry = False
        self.origin = OrderedDict()
        self.size = OrderedDict()

    def read(self, raw, file_version):
        self.gfx_id = raw.read_int32()
        self.height = raw.read_char()
        self.horizontal_symetry = raw.read_bool()
        self.origin['x'] = raw.read_int16()
        self.origin['y'] = raw.read_int16()
        self.size['x'] = raw.read_int16()
        self.size['y'] = raw.read_int16()

    def get_dict(self):
        ret = super(_NormalGraphicalElementData, self).get_dict()
        ret['gfx_id'] = self.gfx_id
        ret['height'] = self.height
        ret['horizontal_symetry'] = self.horizontal_symetry
        ret['origin'] = OrderedDict()
        ret['origin']['x'] = self.origin['x']
        ret['origin']['y'] = self.origin['y']
        ret['size'] = OrderedDict()
        ret['size']['x'] = self.size['x']
        ret['size']['y'] = self.size['y']
        return ret


class _BoundingBoxGraphicalElementData(_NormalGraphicalElementData):
    def __init__(self, id, type):
        super(_BoundingBoxGraphicalElementData, self).__init__(id, type)


class _AnimatedGraphicalElementData(_NormalGraphicalElementData):
    def __init__(self, id, type):
        super(_AnimatedGraphicalElementData, self).__init__(id, type)
        self.min_delay = 0
        self.max_delay = 0

    def read(self, raw, file_version):
        super(_AnimatedGraphicalElementData, self).read(raw, file_version)
        if file_version >= 4:
            self.min_delay = raw.read_int32()
            self.max_delay = raw.read_int32()

    def get_dict(self):
        ret = super(_AnimatedGraphicalElementData, self).get_dict()
        ret['min_delay'] = self.min_delay
        ret['max_delay'] = self.max_delay
        return ret


class _EntityGraphicalElementData(_GraphicalElementData):
    def __init__(self, id, type):
        super(_EntityGraphicalElementData, self).__init__(id, type)
        self.entity_look = ""
        self.horizontal_symetry = False
        self.play_animation = False
        self.play_anim_static = False
        self.min_delay = 0
        self.max_delay = 0

    def read(self, raw, file_version):
        look_length = raw.read_int32()
        self.entity_look = raw.read_string_bytes(look_length).decode('utf-8')
        self.horizontal_symetry = raw.read_bool()
        if file_version >= 7:
            self.play_animation = raw.read_bool()
        if file_version >= 6:
            self.play_anim_static = raw.read_bool()
        if file_version >= 5:
            self.min_delay = raw.read_int32()
            self.max_delay = raw.read_int32()

    def get_dict(self):
        ret = super(_EntityGraphicalElementData, self).get_dict()
        ret['entity_look'] = self.entity_look
        ret['horizontal_symetry'] = self.horizontal_symetry
        ret['play_animation'] = self.play_animation
        ret['play_anim_static'] = self.play_anim_static
        ret['min_delay'] = self.min_delay
        ret['max_delay'] = self.max_delay
        return ret


class _ParticlesGraphicalElementData(_GraphicalElementData):
    def __init__(self, id, type):
        super(_ParticlesGraphicalElementData, self).__init__(id, type)
        self.script_id = 0

    def read(self, raw, file_version):
        self.script_id = raw.read_int16()

    def get_dict(self):
        ret = super(_ParticlesGraphicalElementData, self).get_dict()
        ret['script_id'] = self.script_id
        return ret


class _BlendedGraphicalElementData(_NormalGraphicalElementData):
    def __init__(self, id, type):
        super(_BlendedGraphicalElementData, self).__init__(id, type)
        self.blend_mode = ""

    def read(self, raw, file_version):
        super(_BlendedGraphicalElementData, self).read(raw, file_version)
        mode_length = raw.read_int32()
        self.blend_mode = raw.read_string_bytes(mode_length).decode('utf-8')

    def get_dict(self):
        ret = super(_BlendedGraphicalElementData, self).get_dict()
        ret['blend_mode'] = self.blend_mode
        return ret
