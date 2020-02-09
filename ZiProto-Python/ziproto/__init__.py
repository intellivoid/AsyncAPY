import ziproto.ZiProtoEncoder
import ziproto.ZiProtoDecoder

def encode(obj):
    return(ZiProtoEncoder.encode(obj))

def decode(bytes):
    return(ZiProtoDecoder.decode(bytes))
