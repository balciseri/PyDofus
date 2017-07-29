PyDofus Tools
=============

Python 3 scripts to pack/unpack Dofus files

- [x] **d2i**
- [x] **d2p**
- [x] **d2o** (unpack only)
- [x] **dlm**
- [x] **dx**
- [x] **ele** (unpack only)
- [x] **swl**

Usage
-----

###d2i

```Shell
$ python d2i_unpack.py file.d2i
# file output: file.json
```

```Shell
$ python d2i_pack.py file.json
# file output: file.d2i
```

###d2p

```Shell
$ python d2p_unpack.py
# (all files in input folder)
# folder output: ./output/{all files}.d2p
```

```Shell
$ python d2p_pack.py file.d2p
# require original file in input folder and unpacked file in output folder
# file output: ./output/~generated/file.d2p
```

###d2o

```Shell
$ python d2o_unpack.py
# (all files in input folder)
# folder output: ./output/{all files}.json
```

###dlm

```Shell
$ python dlm_unpack.py file.dlm
# file output: file.json
```

```Shell
$ python dlm_pack.py file.json
# file output: file.dlm
```

###dx

```Shell
$ python dx_unpack.py file.dx
# file output: file.swf
```

```Shell
$ python dx_pack.py file.swf
# file output: file.dx
```

###ele

```Shell
$ python ele_unpack.py elements.ele
# file output: elements.json
```

###swl

```Shell
$ python swl_unpack.py file.swl
# file output: file.swf and file.json
```

```Shell
$ python swl_pack.py file.swf
# require file.json
# file output: file.swl
```

Authors
-------

**Marvin Roger** ([marvinroger](https://github.com/marvinroger)) : based on his work  
**Yann Guineau** ([LuaxY](https://github.com/LuaxY)) : automated scripts for pack/unpack dofus files  
**[nowis13](https://github.com/nowis13)** : add d2o and ele unpack support
