from ziproto.ZiProtoFormat import ZiProtoFormat
from ziproto.ZiProtoDecoder import Decoder
import struct

class Encoder:
    def __init__(self):
        self.payload=bytearray()

    def array(self, count):
        if count <= 0xF:
            self.payload.append(ZiProtoFormat.FIXARRAY.value + count)
        elif count <= 0xFFFF:
            self.payload.append(ZiProtoFormat.ARRAY16.value)
            self.payload.extend(struct.pack('>H', count))
        elif count <= 0xFFFFFFFF:
            self.payload.append(ZiProtoFormat.ARRAY32.value)
            self.payload.extend(struct.pack('>I', count))
        else:
            raise OverflowError('array %d' % count)

    def map(self, count):
        if count <= 0xF:
            self.payload.append(ZiProtoFormat.FIXMAP.value + count)
        elif count <= 0xFFFF:
            self.payload.append(ZiProtoFormat.MAP16.value)
            self.payload.extend(struct.pack('>H', count))
        elif count <= 0xFFFFFFFF:
            self.payload.append(ZiProtoFormat.MAP32.value)
            self.payload.extend(struct.pack('>I', count))
        else:
            raise OverflowError('map %d' % count)

    def encode(self, value):
        encoded = encode(value)
        self.payload.extend(encoded)

def encode(obj):
    if obj is None:
        return struct.pack('B', ZiProtoFormat.NIL.value)
    elif obj is False:
        return struct.pack('B', ZiProtoFormat.FALSE.value)
    elif obj is True:
        return struct.pack('B', ZiProtoFormat.TRUE.value)
    elif isinstance(obj, int):
        if obj >= 0:
            if obj <= 0x7f:
                return struct.pack('b', obj)
            elif obj <= 0xFF:
                return struct.pack('>BB', ZiProtoFormat.UINT8.value, obj)
            elif obj <= 0xFFFF:
                return struct.pack('>BH', ZiProtoFormat.UINT16.value, obj)
            elif obj <= 0xFFFFFFFF:
                return struct.pack('>BI', ZiProtoFormat.UINT32.value, obj)
            elif obj <= 0xFFFFFFFFFFFFFFFF:
                return struct.pack('>BQ', ZiProtoFormat.UINT64.value, obj)
            else:
                raise OverflowError('Encode failed. %s' % obj)
        else:
            if obj >= -32:
                return struct.pack('B', 0x100 + obj)
            elif obj >= -128:
                return struct.pack('>Bb', ZiProtoFormat.INT8.value, obj)
            elif obj >= -32768:
                return struct.pack('>Bh', ZiProtoFormat.INT16.value, obj)
            elif obj >= -2147483648:
                return struct.pack('>Bi', ZiProtoFormat.INT32.value, obj)
            elif obj >= -9223372036854775808:
                return struct.pack('>Bq', ZiProtoFormat.INT64.value, obj)
            else:
                raise OverflowError('Encode failed. %s' % obj)

    elif isinstance(obj, float):
        return struct.pack('>Bd', ZiProtoFormat.FLOAT64.value, obj)

    elif isinstance(obj, str):
        utf8 = obj.encode('utf-8')
        utf8_len = len(utf8)
        if utf8_len == 0:
            return struct.pack('B', ZiProtoFormat.FIXSTR.value)
        elif utf8_len < 32:
            return struct.pack('B%ds' % utf8_len, ZiProtoFormat.FIXSTR.value+utf8_len, utf8)
        elif utf8_len <= 0xFF:
            return struct.pack('BB%ds' % utf8_len, ZiProtoFormat.STR8.value, utf8_len, utf8)
        elif utf8_len <= 0xFFFF:
            return struct.pack('>BH%ds' % utf8_len, ZiProtoFormat.STR16.value, utf8_len, utf8)
        elif utf8_len <= 0xFFFFFFFF:
            return struct.pack('>BI%ds' % utf8_len, ZiProtoFormat.STR32.value, utf8_len, utf8)
        else:
            raise OverflowError('Encode failed. %s' % obj)

    elif isinstance(obj, bytes) or isinstance(obj, bytearray):
        bin_len=len(obj)
        if bin_len == 0:
            return struct.pack('B', ZiProtoFormat.BIN8.value)
        elif bin_len <= 0xFF:
            return struct.pack('BB%ds' % bin_len, ZiProtoFormat.BIN8.value, bin_len, obj)
        elif bin_len <= 0xFFFF:
            return struct.pack('>BH%ds' % bin_len, ZiProtoFormat.BIN16.value, bin_len, obj)
        elif bin_len <= 0xFFFFFFFF:
            return struct.pack('>BI%ds' % bin_len, ZiProtoFormat.BIN32.value, bin_len, obj)
        else:
            raise OverflowError('Encode failed. %s' % obj)

    elif isinstance(obj, Decoder):
        return obj.get_bytes()

    elif isinstance(obj, dict):
        encoder = Encoder()
        encoder.map(len(obj))
        for k, v in obj.items():
            encoder.encode(k)
            encoder.encode(v)
        return encoder.payload

    elif hasattr(obj, '__iter__'):
        encoder = Encoder()
        encoder.array(len(obj))
        for x in obj:
            encoder.encode(x)
        return encoder.payload

    raise ValueError('unknown type. %s' % type(obj))
