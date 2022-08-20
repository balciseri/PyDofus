#!/usr/bin/python3
# -*- coding: utf-8 -*-

from ._binarystream import _BinaryStream
from collections import OrderedDict

# Exceptions


class InvalidD2PFile(Exception):
    def __init__(self, message):
        super(InvalidD2PFile, self).__init__(message)
        self.message = message

# Class itself


class D2PReader:
    """Read D2P files"""
    def __init__(self, stream, autoload=True):
        """Init the class with the informations about files in the D2P"""
        # Attributes
        self._stream = stream

        self._base_offset = None
        self._base_length = None
        self._indexes_offset = None
        self._number_indexes = None
        self._properties_offset = None
        self._number_properties = None

        self._properties = None

        self._files_position = None

        self._files = None

        self._loaded = False

        # Load the D2P
        D2P_file_binary = _BinaryStream(self._stream, True)

        bytes_header = D2P_file_binary.read_bytes(2)
        if bytes_header == b"":
            raise InvalidD2PFile("First bytes not found.")

        if bytes_header != b"\x02\x01":
            raise InvalidD2PFile("The first bytes don't match the"
                                 " SWL pattern.")

        self._stream.seek(-24, 2)  # Set position to end - 24 bytes

        self._base_offset = D2P_file_binary.read_uint32()
        self._base_length = D2P_file_binary.read_uint32()
        self._indexes_offset = D2P_file_binary.read_uint32()
        self._number_indexes = D2P_file_binary.read_uint32()
        self._properties_offset = D2P_file_binary.read_uint32()
        self._number_properties = D2P_file_binary.read_uint32()

        if ((self._base_offset == b"" or self._base_length == b"" or
             self._indexes_offset == b"" or self._number_indexes == b"" or
             self._properties_offset == b"" or
             self._number_properties == b"")):
            raise InvalidD2PFile("The file doesn't match the D2P pattern.")

        self._stream.seek(self._indexes_offset, 0)

        # Read indexes

        self._files_position = OrderedDict()

        i = 0
        while i < self._number_indexes:
            file_name = (D2P_file_binary.read_string()).decode()
            offset = D2P_file_binary.read_int32()
            length = D2P_file_binary.read_int32()
            if file_name == b"" or offset == b"" or length == b"":
                raise InvalidD2PFile("The file appears to be corrupt.")
            self._files_position[file_name] = {
                "offset": offset + self._base_offset,
                "length": length
            }

            i += 1

        self._stream.seek(self._properties_offset, 0)

        # Read properties

        self._properties = OrderedDict()

        i = 0
        while i < self._number_properties:
            try:
                property_type = (D2P_file_binary.read_string()).decode()
                property_value = (D2P_file_binary.read_string()).decode()
            except ValueError:
                property_type = (D2P_file_binary.read_string()).decode('latin-1')
                property_value = (D2P_file_binary.read_string()).decode('latin-1')
            
            if property_type == b"" or property_value == b"":
                raise InvalidD2PFile("The file appears to be corrupt.")
            self._properties[property_type] = property_value

            i += 1

        if autoload:
            self.load()

    def load(self):
        """Load the class with the actual D2P files in it"""
        # Populate _Files

        if self._loaded:
            raise Exception("D2P instance is already populated.")

        D2P_file_binary = _BinaryStream(self._stream, True)

        self._files = OrderedDict()

        for file_name, position in self._files_position.items():
            self._stream.seek(position["offset"], 0)

            self._files[file_name] = (D2P_file_binary.
                                      read_bytes(position["length"]))

        self._loaded = True

    # Accessors

    def _get_stream(self):
        return self._stream

    def _get_properties(self):
        return self._properties

    def _get_files(self):
        to_return = OrderedDict()
        for file_name, position in self._files_position.items():
            object_ = {"position": position}
            if self._files:
                object_["binary"] = self._files[file_name]
            to_return[file_name] = object_

        return to_return

    def _get_loaded(self):
        return self._loaded

    # Properties

    stream = property(_get_stream)
    properties = property(_get_properties)
    files = property(_get_files)
    loaded = property(_get_loaded)


class D2PBuilder:
    """Build D2P files"""
    def __init__(self, template, target):
        self._template = template
        self._stream = target

        self._base_offset = None
        self._base_length = None
        self._indexes_offset = None
        self._number_indexes = None
        self._properties_offset = None
        self._number_properties = None

        self._files_position = None

        self._files = None
        self._set_files(self._template.files)  # To update files and position

    def build(self):
        """Create the D2P represented by the class in the given stream."""
        if self._template is None:
            raise RuntimeError("Template must be defined to build a D2P file")

        D2P_file_build_binary = _BinaryStream(self._stream, True)

        D2P_file_build_binary.write_bytes(b"\x02\x01")

        self._base_offset = self._stream.tell()

        for file_name, specs in self._files.items():
            D2P_file_build_binary.write_bytes(specs["binary"])

        self._base_length = self._stream.tell() - self._base_offset

        self._indexes_offset = self._stream.tell()
        self._number_indexes = 0

        for file_name, position in self._files_position.items():
            D2P_file_build_binary.write_string(file_name.encode())
            D2P_file_build_binary.write_int32(position["offset"])
            D2P_file_build_binary.write_int32(position["length"])
            self._number_indexes += 1

        self._properties_offset = self._stream.tell()
        self._number_properties = 0

        for ppty_type, ppty_value in self._template._properties.items():
            D2P_file_build_binary.write_string(ppty_type.encode())
            D2P_file_build_binary.write_string(ppty_value.encode())
            self._number_properties += 1

        D2P_file_build_binary.write_uint32(self._base_offset)
        D2P_file_build_binary.write_uint32(self._base_length)
        D2P_file_build_binary.write_uint32(self._indexes_offset)
        D2P_file_build_binary.write_uint32(self._number_indexes)
        D2P_file_build_binary.write_uint32(self._properties_offset)
        D2P_file_build_binary.write_uint32(self._number_properties)

    # Mutators

    def _set_files(self, files):
        self._files = files
        self._files_position = OrderedDict()

        # Update positions
        actual_offset = 0

        for file_name, specs in self._files.items():
            self._files_position[file_name] = {
                "offset": actual_offset,
                "length": len(specs["binary"])
            }
            actual_offset += self._files_position[file_name]["length"]

    # Properties

    files = property(None, _set_files)
