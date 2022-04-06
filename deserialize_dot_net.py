import struct
import copy
import logging

LOG = logging.getLogger()

SEPARATOR = '/'


class UnhandledData(Exception):
    pass


class Deserializer:
    def __init__(self, data, pos=0):
        self.data = data
        self.pos = pos
        self.idmap = {}
        self.meta = {}
        self.seen = set()
        self.printhex(10)

    def get(self, name):
        obj = next(_ for _ in self.idmap.values()
                   if isinstance(_, dict) and _.get('__cname__') == name)
        return DictQuery(obj)

    def parse(self):
        ret = []
        while True:
            _type = self.data[self.pos]
            try:
                if _type == 1:  # Ref object
                    ret.append(self.parse_refobj())
                elif _type == 4:  # Runtime Obj
                    ret.append(self.parse_class())
                elif _type == 5:  # Class 
                    ret.append(self.parse_class())
                elif _type == 7:  # Generic Array
                    ret.append(self.parse_generic_array())
                elif _type == 10:  # NullValue
                    self.pos += 1
                elif _type == 15:  # Array of primitives
                    ret.append(self.parse_primarr())
                elif _type == 11:  # END
                    LOG.debug(f"Found end")
                    break
                else:
                    LOG.error(f"Stopping on {_type}")
                    break
            except UnhandledData:
                break
            finally:
                # self.printhex(40)
                pass
        self._finalize()
        return ret

    def _finalize(self):
        for _id in self.idmap:
            self._fix_deferred_id(_id)

    def _fix_deferred_id(self, _id):
        if _id not in self.seen:
            self.seen.add(_id)
            if isinstance(self.idmap[_id], list):
                for _idx, _val in enumerate(self.idmap[_id]):
                    if isinstance(_val, (list, tuple)) and _val[-1] == 'deferred':
                        self._fix_deferred_id(_val[0])
                        self.idmap[_id][_idx] = self.idmap[_val[0]]
            self._fix_deferred_dict(self.idmap[_id])

    def _fix_deferred_dict(self, item):
        if not isinstance(item, dict):
            return
        for key, ref in item.items():
            if key.startswith('__'):
                continue
            if key == 'deferred':
                continue
            if key == 'value' and isinstance(ref, list):
                for _idx, _val in enumerate(ref):
                    if isinstance(_val, (list, tuple)) and _val[-1] == 'deferred':
                        self._fix_deferred_id(_val[0])
                        ref[_idx] = self.idmap[_val[0]]
                continue
            self._fix_deferred_dict(ref)
        if 'deferred' in item:
            self._fix_deferred_id(item['deferred'])
            item['value'] = self.idmap[item['deferred']]
            del item['deferred']

    def read_byte(self, peek=False):
        ret = self.data[self.pos]
        if not peek:
            self.pos += 1
        return ret

    def read_str(self):
        size = 0
        shift = 0
        origpos = self.pos
        while True:
            _siz = self.data[self.pos]
            self.pos += 1
            size = size + ((0x7f & _siz) << shift)
            shift += 7
            if _siz < 128:
                break
        ret = self.data[self.pos: self.pos + size].decode('utf8')
        self.pos += size
        return ret

    def read_u32(self):
        res = struct.unpack('<L', self.data[self.pos:self.pos + 4])
        self.pos += 4
        return res[0]

    def read_i32(self):
        res = struct.unpack('<l', self.data[self.pos:self.pos + 4])
        self.pos += 4
        return res[0]

    def read_u64(self):
        res = struct.unpack('<Q', self.data[self.pos:self.pos + 8])
        self.pos += 8
        return res[0]

    def read_i64(self):
        res = struct.unpack('<q', self.data[self.pos:self.pos + 8])
        self.pos += 8
        return res[0]

    def read_float(self):
        res = struct.unpack('<f', self.data[self.pos:self.pos + 4])
        self.pos += 4
        return res[0]

    def read_double(self):
        res = struct.unpack('<d', self.data[self.pos:self.pos + 8])
        self.pos += 8
        return res[0]

    def printhex(self, *args):
        if len(args) == 1:
            start = self.pos
            end = self.pos + args[0]
        else:
            start, end = args
        while start < end:
            new_end = min(end, start + 16)
            _hex = [f"{_x:02x}" for _x in self.data[start:new_end]]
            _hex += [f"  " for _x in range(new_end, start + 16)]
            _str = [f"{chr(_x) if 31 < _x < 127 else '.'}" for _x in self.data[start:new_end]]
            _str += [" " for _x in range(new_end, start + 16)]
            LOG.debug(f"{start:08x}    " + " ".join(_hex) + "    " + "".join(_str))
            start += 16

    def parse_class(self):
        orig_pos = self.pos
        elem_type = self.read_byte()
        if elem_type not in (4, 5):
            LOG.error(f"Unsupported data type: {elem_type}")
            raise UnhandledData
        _id = self.read_u32()
        cname = self.read_str()
        count = self.read_u32()
        LOG.debug(f"{cname}({_id}) @ {orig_pos:04x} Count: {count}")
        cls_idx = []
        cls = {}
        while count:
            field = self.read_str()
            cls_idx.append(field)
            count -= 1
        for name in cls_idx:
            cls[name] = {'type': self.read_byte()}
        for name in cls_idx:
            type_tag = cls[name]['type']
            cls[name]['code'] = self.get_type_spec(type_tag)
        self.printhex(30)
        cls['__cname__'] = cname
        cls['__fields__'] = cls_idx
        self.meta[_id] = cls
        if elem_type == 5:
            # only classes have assembly id
            assemblyid = self.read_u32()
        self.printhex(orig_pos, self.pos)
        self.idmap[_id] = self.get_class_values(_id)
        return self.idmap[_id]

    def parse_refobj(self):
        orig_pos = self.pos
        if self.data[self.pos] != 1:
            LOG.error(f"Unsupported data type: {self.data[self.pos]}")
            raise UnhandledData
        self.pos += 1
        _id = self.read_u32()
        metaid = self.read_u32()
        self.idmap[_id] = self.get_class_values(metaid)
        return self.idmap[_id]

    def parse_primarr(self):
        orig_pos = self.pos
        if self.data[self.pos] != 15:
            LOG.error(f"Unsupported data type: {self.data[self.pos]}")
            raise UnhandledData
        self.pos += 1
        _id = self.read_u32()
        count = self.read_u32()
        _type = self.read_byte()
        ret = []
        while count:
            ret.append(self.get_prim_value(_type))
            count -= 1
        self.idmap[_id] = ret
        return self.idmap[_id]

    def parse_generic_array(self):
        orig_pos = self.pos
        if self.data[self.pos] != 7:
            LOG.error(f"Unsupported data type: {self.data[self.pos]}")
            raise UnhandledData
        self.pos += 1
        _id = self.read_u32()
        array_type = self.read_byte()
        dimensions = self.read_u32()
        if array_type != 0 or dimensions != 1:
            LOG.error("Multidimensional arrays not supported")
            raise UnhandledData
        elems_per_dim = []
        for i in range(0, dimensions):
            elems_per_dim.append(self.read_u32())
        type_tag = self.read_byte()
        type_spec = self.get_type_spec(type_tag)
        ret = []
        while len(ret) < elems_per_dim[0]:
            res = self.get_single_value(type_tag, type_spec, "unknown")
            if isinstance(res[1], list):
                ret += [[res[0], _x] for _x in res[1]]
            else:
                ret += [res]
        self.idmap[_id] = ret
        return self.idmap[_id]

    def parse_runtime_obj(self):
        LOG.error("parse_runtime_obj unsupported")
        raise UnhandledData
        orig_pos = self.pos
        if self.data[self.pos] != 4:
            LOG.error(f"Unsupported data type: {data[self.pos]}")
            raise UnhandledData
        self.pos += 1
        _id = self.read_u32()
        cname = self.read_str()
        count = self.read_u32()
        LOG.debug(f"{cname}({_id}) @@ {orig_pos:04x} Count: {count}")
        cls_idx = []
        cls = {}
        while count:
            field = self.read_str()
            cls_idx.append(field)
            count -= 1

    def get_type_spec(self, type_tag):
        if type_tag == 0:  # primitive
            return self.read_byte()
        elif type_tag == 1:  # string
            return None
        elif type_tag == 3:  # runtimeobj
            return self.read_str()
        elif type_tag == 4:  # generic (nested class/array)
            # class-name, id
            return self.read_str(), self.read_u32()
        elif type_tag == 7:  # primitive array
            return self.read_byte()
        else:
            LOG.error(f"Can't handle type '{type_tag}'")
            raise UnhandledData

    def get_prim_value(self, primtype):
        if primtype == 1:  # bool
            return self.read_byte()
        elif primtype == 6:  # Double
            return self.read_double()
        elif primtype == 8:  # int32
            return self.read_i32()
        elif primtype == 9:  # int64
            return self.read_i64()
        elif primtype == 11:  # float
            return self.read_float()
        else:
            LOG.error(f"Can't handle prim type '{primtype}'")
            raise UnhandledData

    def get_single_value(self, type_tag, type_spec, name):
        if type_tag == 0:  # primitive
            return None, self.get_prim_value(type_spec)
        elif type_tag == 1:  # string
            if self.data[self.pos] != 6:
                LOG.error(f"Could not parse string for {name}")
                raise UnhandledData
            self.pos += 1
            _id = self.read_u32()
            return _id, self.read_str()
        elif type_tag in (3, 4, 7):
            elem = self.data[self.pos]
            if elem == 1:  # reference of object
                origpos = self.pos
                LOG.debug(f"(1) {name} - {self.pos:02x}")
                self.printhex(origpos, self.pos)
                return None, self.parse_refobj()
            elif elem == 4:  # runtime
                origpos = self.pos
                LOG.debug(f"(5) {name} - {origpos:02x}")
                self.printhex(origpos, self.pos + 48)
                return None, self.parse_class()
            elif elem == 5:  # class
                origpos = self.pos
                LOG.debug(f"(5) {name} - {origpos:02x}")
                self.printhex(origpos, self.pos + 48)
                return None, self.parse_class()
            elif elem == 9:  # object ref
                self.pos += 1
                _id = self.read_u32()
                if _id in self.idmap:
                    LOG.debug(f"Found object reference: {self.idmap[_id]} for {name}")
                else:
                    LOG.debug(f"Found deferred object reference '{_id}' for {name}")
                return _id, "deferred"
            elif elem == 10:  # NullValue
                self.pos += 1
                return None, None
            elif elem == 13:  # array of null
                self.pos += 1
                count = self.read_byte()
                return None, [None for _ in range(0, count)]
            else:
                LOG.error(f"Unknown element type {elem} for {name}")
                raise UnhandledData
        else:
            LOG.error(f"Couldn't handle type {type_tag} for {name}")
            raise UnhandledData

    def get_class_values(self, metaid):
        if metaid not in self.meta:
            LOG.error(f"Couldn't find meta-id {metaid}")
            raise UnhandledData
        cls = copy.deepcopy(self.meta[metaid])
        cls_idx = cls.pop('__fields__')
        start = self.pos
        for name in cls_idx:
            _type = cls[name]['type']
            LOG.debug(f"{name} -- {_type}")
            _id, value = self.get_single_value(_type, cls[name]['code'], name)
            if value == 'deferred':
                cls[name]['deferred'] = _id
            else:
                cls[name]['value'] = value
        return cls


class DictQuery(dict):
    # from https://www.haykranen.nl/2016/02/13/handling-complex-nested-dicts-in-python/
    def get(self, path, default=None):
        keys = path.split(SEPARATOR)
        val = None

        for key in keys:
            if val:
                if isinstance(val, list):
                    val = [v.get(key, default) if v else None for v in val]
                else:
                    val = val.get(key, default)
            else:
                val = dict.get(self, key, default)

            if not val:
                break

        return val
