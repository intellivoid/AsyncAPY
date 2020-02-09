# ZiProto

ZiProto is used to serialize data, ZiProto is designed with the intention to be
used for transferring data instead of using something like JSON which can use
up more bandwidth when you don't intend to have the data shown to the public
or end-user

## Setup
```bash
python setup.py install
```

## Usage

To encode data, this can be done simply
```python
>> import ziproto
>> ziproto.encode({"foo": "bar", "fruits": ['apple', 'banana']})
bytearray(b'\x82\xa6fruits\x92\xa5apple\xa6banana\xa3foo\xa3bar')
```

The same can be said when it comes to decoding
```python
>> import ziproto
>> Data = ziproto.encode({"foo": "bar", "fruits": ['apple', 'banana']})
>> ziproto.decode(Data)
{'foo': 'bar', 'fruits': ['apple', 'banana']}
```

To determine what type of variable you are dealing with, you could use the decoder
```python
>> import ziproto
>> from ziproto.ZiProtoDecoder import Decoder

>> Data = ziproto.encode({"foo": "bar", "fruits": ['apple', 'banana']})
>> SuperDecoder = Decoder(Data)
>> print(SuperDecoder.get_type())
ValueType.MAP
```

---

## License
Copyright *2018 Zi Xing Narrakas*

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "**AS IS**" **BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND**, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
