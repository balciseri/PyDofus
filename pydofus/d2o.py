#!/usr/bin/python3
# -*- coding: utf-8 -*-

from ._binarystream import _BinaryStream
from collections import OrderedDict

# Exceptions


class InvalidD2OFile(Exception):
    def __init__(self, message):
        super(InvalidD2OFile, self).__init__(message)
        self.message = message

# Class itself


class D2OReader:
    """Read D2O files"""
    def __init__(self, stream):
        """Init the class with the informations about files in the D2P"""
        # Attributes
        self._stream = stream

        self._stream_start_index = 7
        self._classes = OrderedDict()
        self._counter = 0

        # Load the D2O
        D2O_file_binary = _BinaryStream(self._stream, True)
        self._D2O_file_binary = D2O_file_binary

        string_header = D2O_file_binary.read_bytes(3)
        base_offset = 0
        if string_header != b'D2O':
            self._stream.seek(0)
            string_header = D2O_file_binary.read_string()
            if string_header != "AKSF":
                raise InvalidD2OFile("Malformated game data file.")
            D2O_file_binary.read_short()
            base_offset = D2O_file_binary.read_int32()
            self._stream.seek(base_offset, 1)
            self._stream_start_index = self._stream.position + 7
            string_header = D2O_file_binary.read_bytes(3)
            if string_header != b'D2O':
                raise InvalidD2OFile("Malformated game data file.")

        offset = D2O_file_binary.read_int32()
        self._stream.seek(base_offset + offset)
        index_number = D2O_file_binary.read_int32()
        index = 0
        index_dict = OrderedDict()

        while index < index_number:
            index_id = D2O_file_binary.read_int32()
            offset = D2O_file_binary.read_int32()
            index_dict[index_id] = base_offset + offset
            self._counter += 1
            index = index + 8

        class_number = D2O_file_binary.read_int32()
        class_index = 0

        while class_index < class_number:
            class_id = D2O_file_binary.read_int32()
            self._read_class_definition(class_id, D2O_file_binary)
            class_index += 1

        if D2O_file_binary.bytes_available():
            self._game_data_processor = _GameDataProcess(D2O_file_binary)

    def get_objects(self):
        if not self._counter:
            return None
        counter = self._counter
        classes = self._classes
        D2O_file_binary = self._D2O_file_binary
        D2O_file_binary.position(self._stream_start_index)
        objects = list()
        i = 0
        while i < counter:
            objects.append(
                classes[D2O_file_binary.read_int32()].read(D2O_file_binary))
            i += 1
        return objects

    def get_class_definition(self, object_id):
        return self._classes[object_id]

    def _read_class_definition(self, class_id, D2O_file_binary):
        class_name = D2O_file_binary.read_string()
        class_pkg = D2O_file_binary.read_string()
        class_def = _GameDataClassDefinition(class_pkg, class_name, self)
        field_number = D2O_file_binary.read_int32()
        field_index = 0

        while field_index < field_number:
            field = D2O_file_binary.read_string()
            class_def.add_field(field, D2O_file_binary)
            field_index += 1

        self._classes[class_id] = class_def


class _GameDataClassDefinition:
    def __init__(self, class_pkg, class_name, d2o_reader):
        self._class = class_pkg.decode('utf-8') + '.' + \
            class_name.decode('utf-8')
        self._fields = list()
        self._d2o_reader = d2o_reader

    def fields(self):
        return self._fields

    def read(self, D2O_file_binary):
        obj = OrderedDict()
        for field in self._fields:
            obj[field.name] = field.read_data(D2O_file_binary)
        return obj

    def add_field(self, name, D2O_file_binary):
        field = _GameDataField(name, self._d2o_reader)
        field.read_type(D2O_file_binary)
        self._fields.append(field)


class _GameDataField:
    def __init__(self, name, d2o_reader):
        self.name = name.decode('utf-8')
        self._inner_read_methods = list()
        self._inner_type_names = list()
        self._d2o_reader = d2o_reader

    def read_type(self, D2O_file_binary):
        read_id = D2O_file_binary.read_int32()
        self.read_data = self._get_read_method(read_id, D2O_file_binary)

    def _get_read_method(self, read_id, D2O_file_binary):
        if read_id == -1:
            return self._read_integer
        elif read_id == -2:
            return self._read_boolean
        elif read_id == -3:
            return self._read_string
        elif read_id == -4:
            return self._read_number
        elif read_id == -5:
            return self._read_i18n
        elif read_id == -6:
            return self._read_unsigned_integer
        elif read_id == -99:
            self._inner_type_names.append(D2O_file_binary.read_string())
            self._inner_read_methods = [self._get_read_method(
                D2O_file_binary.read_int32(),
                D2O_file_binary)] + self._inner_read_methods
            return self._read_vector
        else:
            if read_id > 0:
                return self._read_object
            raise Exception("Unknown type \'" + read_id + "\'.")

    def _read_integer(self, D2O_file_binary, vec_index=0):
        return D2O_file_binary.read_int32()

    def _read_boolean(self, D2O_file_binary, vec_index=0):
        return D2O_file_binary.read_bool()

    def _read_string(self, D2O_file_binary, vec_index=0):
        string = D2O_file_binary.read_string()
        if string == 'null':
            string = None
        return string.decode('utf-8')

    def _read_number(self, D2O_file_binary, vec_index=0):
        return D2O_file_binary.read_double()

    def _read_i18n(self, D2O_file_binary, vec_index=0):
        return D2O_file_binary.read_int32()

    def _read_unsigned_integer(self, D2O_file_binary, vec_index=0):
        return D2O_file_binary.read_uint32()

    def _read_vector(self, D2O_file_binary, vec_index=0):
        vector_size = D2O_file_binary.read_int32()
        vector = list()
        i = 0
        while i < vector_size:
            vector.append(self._inner_read_methods[vec_index](D2O_file_binary,
                                                              vec_index + 1))
            i += 1
        return vector

    def _read_object(self, D2O_file_binary, vec_index=0):
        object_id = D2O_file_binary.read_int32()
        if object_id == -1431655766:
            return None
        obj = self._d2o_reader.get_class_definition(object_id)
        return obj.read(D2O_file_binary)


class _GameDataProcess:
    def __init__(self, D2O_file_binary):
        self._stream = D2O_file_binary
        self._sort_index = OrderedDict()
        self._queryable_field = list()
        self._search_field_index = OrderedDict()
        self._search_field_type = OrderedDict()
        self._search_field_count = OrderedDict()
        self._parse_stream()

    def _parse_stream(self):
        length = self._stream.read_int32()
        off = self._stream.position() + length + 4
        while length:
            available = self._stream.bytes_available()
            string = self._stream.read_string()
            self._queryable_field.append(string)
            self._search_field_index[string] = self._stream.read_int32() + off
            self._search_field_type[string] = self._stream.read_int32()
            self._search_field_count[string] = self._stream.read_int32()
            length = length - (available - self._stream.bytes_available())
