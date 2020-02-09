from ziproto import Headmap
from ziproto.ValueType import ValueType
import struct

class MapIter:
    def __init__(self, decoder_obj):
        if not decoder_obj.is_map():
            raise TypeError('is not map')
        self.bytedata = decoder_obj.bytedata

    def __iter__(self):
        head = self.bytedata[0]
        t, value = Headmap.HEAD_MAP[head]
        count, offset = value(self.bytedata[1:])
        body = self.bytedata[1+offset:]
        x = 0
        current = None
        while x<count:
            if current is None:
                current = Decoder(body)
            else:
                current = v.next()
            v = current.next()
            yield current, v
            x+=1

class Decoder:
    __slots__ = ('bytedata', 'filled')
    def __init__(self, bytedata, filled=True):
        self.bytedata = memoryview(bytedata)
        self.filled = filled

    def get_type(self):
        head = self.bytedata[0]
        t, _ = Headmap.HEAD_MAP[head]
        return t

    def get(self):
        head = self.bytedata[0]
        t, value = Headmap.HEAD_MAP[head]
        if t == ValueType.ARRAY:
            return [x.get() for x in self]
        elif t == ValueType.MAP:
            return {k.get(): v.get() for k, v in self.items()}
        else:
            x, _ = value(self.bytedata[1:])
            if t == ValueType.STR:
                return x.tobytes().decode('utf-8')
            else:
                return x

    def is_nil(self):
        head = self.bytedata[0]
        t, _ = Headmap.HEAD_MAP[head]
        if t == ValueType.NIL:
            return True
        return False

    def is_array(self):
        head = self.bytedata[0]
        t, _ = Headmap.HEAD_MAP[head]
        return t == ValueType.ARRAY

    def is_map(self):
        head = self.bytedata[0]
        t, _ = Headmap.HEAD_MAP[head]
        return t == ValueType.MAP

    def get_bool(self):
        head = self.bytedata[0]
        t, value = Headmap.HEAD_MAP[head]
        if t == ValueType.BOOL:
            x, _ = value(self.bytedata[1:])
            return x

        raise ValueError('is not bool. %s' % t)

    def get_int(self):
        head = self.bytedata[0]
        t, value = Headmap.HEAD_MAP[head]
        if t == ValueType.INT:
            x, _ = value(self.bytedata[1:])
            return x

        raise ValueError('is not int. %s' % t)

    def get_float(self):
        head = self.bytedata[0]
        t, value = Headmap.HEAD_MAP[head]
        if t == ValueType.FLOAT:
            x, _ = value(self.bytedata[1:])
            return x

        raise ValueError('is not float. %s' % t)

    def get_number(self):
        head = self.bytedata[0]
        t, value = Headmap.HEAD_MAP[head]
        if t == ValueType.INT or t == ValueType.FLOAT:
            x, _ = value(self.bytedata[1:])
            return x

        raise ValueError('is not number. %s' % t)

    def get_str(self):
        head = self.bytedata[0]
        t, value = Headmap.HEAD_MAP[head]
        if t == ValueType.STR:
            x, _ = value(self.bytedata[1:])
            return x.tobytes().decode('utf-8')

        raise ValueError('is not str. %s' % t)

    def get_bin(self):
        head = self.bytedata[0]
        t, value = Headmap.HEAD_MAP[head]
        if t == ValueType.BIN:
            x, _ = value(self.bytedata[1:])
            return x

        raise ValueError('is not bin. %s' % t)

    def __len__(self):
        head = self.bytedata[0]
        t, value = Headmap.HEAD_MAP[head]
        if t == ValueType.ARRAY or t == ValueType.MAP:
            count, _ = value(self.bytedata[1:])
            return count

        raise ValueError('is not array or map. %s' % t)

    def __getitem__(self, index):
        if isinstance(index, int):
            for i, x in enumerate(self):
                if i == index:
                    return x
        else:
            for k, v in self.items():
                if k.get() == index:
                    return v

    def __iter__(self):
        head = self.bytedata[0]
        t, value = Headmap.HEAD_MAP[head]
        if t == ValueType.ARRAY:
            count, offset = value(self.bytedata[1:])
            x = 0
            current = None
            while x<count:
                if current is None:
                    current = Decoder(self.bytedata[1+offset:])
                else:
                    current = current.next()
                yield current
                x += 1
        else:
            raise ValueError('is not array. %s' % t)

    def get_bytes(self):
        if self.filled:
            return self.bytedata

        head = self.bytedata[0]
        t, value = Headmap.HEAD_MAP[head]
        count, offset = value(self.bytedata[1:])
        if t == ValueType.ARRAY:
            x = 0
            pos = 1+offset
            body = self.bytedata[pos:]
            current = Decoder(body)
            while x<count:
                pos += len(current.get_bytes())
                current = current.next()
                x+=1
            return self.bytedata[0:pos]
        elif t == ValueType.MAP:
            x = 0
            pos = 1+offset
            body =  self.bytedata[pos:]
            current = Decoder(body)
            while x<count:
                v = current.next()
                pos += len(current.get_bytes())
                pos += len(v.get_bytes())
                current = v.next()
                x+=1
            return self.bytedata[0:pos]
        else:
            return self.bytedata[0:1+offset]

    def next(self):
        head = self.bytedata[0]
        t, value = Headmap.HEAD_MAP[head]
        count, offset = value(self.bytedata[1:])
        body = self.bytedata[1+offset:]
        if t == ValueType.ARRAY:
            x = 0
            current = Decoder(body)
            while x<count:
                current
                current = current.next()
                x+=1
            return current
        elif t == ValueType.MAP:
            x = 0
            current = Decoder(body)
            while x<count:
                v = current.next()
                current, v
                current = v.next()
                x+=1
            return current
        else:
            return Decoder(body)

    def items(self):
        return MapIter(self)

def decode(bytes):
    Decoder_proto = Decoder(bytes, True)
    return(Decoder_proto.get())
