# 2025-06-27 - [BUG] DuckDB Crash During WAL Replay with Large Chunks
**Priority**: High

**Root Cause**: DuckDB crashes during WAL replay when processing extremely large code chunks (105KB+) in `StringStats::Update`. The crash occurs at memory address `0x00000000000000a7` during string statistics calculation.

**Key Evidence**:
- Crash in `duckdb::StringStats::Update` during WAL replay
- Two 105,653-character chunks containing entire `DuckDBProvider` class
- Segmentation fault (`EXC_BAD_ACCESS`) on macOS Intel x86_64
- Memory access violation in DuckDB's string processing during INSERT replay

**Resolution**: Recent chunking improvements should prevent oversized chunks that trigger this DuckDB internal bug.

# History

## 2025-06-27
**ANALYSIS COMPLETE**: Identified root cause as extremely large string chunks (105KB+) causing memory corruption in DuckDB's `StringStats::Update` during WAL replay. The chunking logic created abnormally large chunks by including entire class definitions. Recent fixes to chunking size limits should prevent this issue from recurring.

**Crash Report**:

Below is a crash report of chunkhound:
```
-------------------------------------
Translated Report (Full Report Below)
-------------------------------------

Process:               Python [28566]
Path:                  /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python
Identifier:            org.python.python
Version:               3.13.5 (3.13.5)
Code Type:             X86-64 (Native)
Parent Process:        uv [28565]
Responsible:           iTerm2 [3722]
User ID:               501

Date/Time:             2025-06-27 12:35:35.9371 +0300
OS Version:            macOS 15.3 (24D60)
Report Version:        12
Bridge OS Version:     9.3 (22P3051)
Anonymous UUID:        581AD0EC-17E0-E19D-40A9-E16410889E58

Sleep/Wake UUID:       202100F2-F243-49AF-8F12-3AE2847C0E92

Time Awake Since Boot: 350000 seconds
Time Since Wake:       3084 seconds

System Integrity Protection: enabled

Crashed Thread:        0  Dispatch queue: com.apple.main-thread

Exception Type:        EXC_BAD_ACCESS (SIGSEGV)
Exception Codes:       KERN_INVALID_ADDRESS at 0x00000000000000a7
Exception Codes:       0x0000000000000001, 0x00000000000000a7

Termination Reason:    Namespace SIGNAL, Code 11 Segmentation fault: 11
Terminating Process:   exc handler [28566]

VM Region Info: 0xa7 is not in any region.  Bytes before following region: 4305792857
      REGION TYPE                    START - END         [ VSIZE] PRT/MAX SHRMOD  REGION DETAIL
      UNUSED SPACE AT START
--->  
      __TEXT                      100a53000-100a55000    [    8K] r-x/r-x SM=COW  /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python

Thread 0 Crashed::  Dispatch queue: com.apple.main-thread
0   libsystem_platform.dylib      	    0x7ff80834d4c9 _platform_memmove$VARIANT$Haswell + 169
1   duckdb.cpython-313-darwin.so  	       0x10883ee0b duckdb::StringStats::Update(duckdb::BaseStatistics&, duckdb::string_t const&) + 91
2   duckdb.cpython-313-darwin.so  	       0x108777bc2 duckdb::UncompressedStringStorage::StringAppendBase(duckdb::BufferHandle&, duckdb::ColumnSegment&, duckdb::SegmentStatistics&, duckdb::UnifiedVectorFormat&, unsigned long long, unsigned long long) + 658
3   duckdb.cpython-313-darwin.so  	       0x1088562f6 duckdb::ColumnData::AppendData(duckdb::BaseStatistics&, duckdb::ColumnAppendState&, duckdb::UnifiedVectorFormat&, unsigned long long) + 54
4   duckdb.cpython-313-darwin.so  	       0x10888ead2 duckdb::StandardColumnData::AppendData(duckdb::BaseStatistics&, duckdb::ColumnAppendState&, duckdb::UnifiedVectorFormat&, unsigned long long) + 34
5   duckdb.cpython-313-darwin.so  	       0x108855756 duckdb::ColumnData::Append(duckdb::BaseStatistics&, duckdb::ColumnAppendState&, duckdb::Vector&, unsigned long long) + 86
6   duckdb.cpython-313-darwin.so  	       0x108883dda duckdb::RowGroupCollection::Append(duckdb::DataChunk&, duckdb::TableAppendState&) + 426
7   duckdb.cpython-313-darwin.so  	       0x10871e6fe duckdb::LocalStorage::Append(duckdb::LocalAppendState&, duckdb::DataChunk&) + 174
8   duckdb.cpython-313-darwin.so  	       0x10871f0d7 duckdb::DataTable::LocalWALAppend(duckdb::TableCatalogEntry&, duckdb::ClientContext&, duckdb::DataChunk&, duckdb::vector<duckdb::unique_ptr<duckdb::BoundConstraint, std::__1::default_delete<duckdb::BoundConstraint>, true>, true> const&) + 119
9   duckdb.cpython-313-darwin.so  	       0x1087446af duckdb::WriteAheadLogDeserializer::ReplayInsert() + 191
10  duckdb.cpython-313-darwin.so  	       0x1087416e9 duckdb::WriteAheadLogDeserializer::ReplayEntry() + 153
11  duckdb.cpython-313-darwin.so  	       0x108740a8f duckdb::WriteAheadLog::ReplayInternal(duckdb::AttachedDatabase&, duckdb::unique_ptr<duckdb::FileHandle, std::__1::default_delete<duckdb::FileHandle>, true>) + 1103
12  duckdb.cpython-313-darwin.so  	       0x10872c83b duckdb::WriteAheadLog::Replay(duckdb::FileSystem&, duckdb::AttachedDatabase&, std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&) + 91
13  duckdb.cpython-313-darwin.so  	       0x10872b25c duckdb::SingleFileStorageManager::LoadDatabase(duckdb::StorageOptions) + 732
14  duckdb.cpython-313-darwin.so  	       0x10839b580 duckdb::DatabaseInstance::CreateMainDatabase() + 656
15  duckdb.cpython-313-darwin.so  	       0x10839cb6e duckdb::DatabaseInstance::Initialize(char const*, duckdb::DBConfig*) + 1774
16  duckdb.cpython-313-darwin.so  	       0x10839ddce duckdb::DuckDB::DuckDB(char const*, duckdb::DBConfig*) + 46
17  duckdb.cpython-313-darwin.so  	       0x1083a1df6 duckdb::DBInstanceCache::CreateInstanceInternal(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, duckdb::DBConfig&, bool, std::__1::function<void (duckdb::DuckDB&)> const&) + 854
18  duckdb.cpython-313-darwin.so  	       0x1083a2337 duckdb::DBInstanceCache::GetOrCreateInstance(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, duckdb::DBConfig&, bool, std::__1::function<void (duckdb::DuckDB&)> const&) + 167
19  duckdb.cpython-313-darwin.so  	       0x108992ffa duckdb::DuckDBPyConnection::Connect(pybind11::object const&, bool, pybind11::dict const&) + 2954
20  duckdb.cpython-313-darwin.so  	       0x1089206ed void pybind11::cpp_function::initialize<duckdb::shared_ptr<duckdb::DuckDBPyConnection, true> (*&)(pybind11::object const&, bool, pybind11::dict const&), duckdb::shared_ptr<duckdb::DuckDBPyConnection, true>, pybind11::object const&, bool, pybind11::dict const&, pybind11::name, pybind11::scope, pybind11::sibling, char [142], pybind11::arg_v, pybind11::arg_v, pybind11::arg_v>(duckdb::shared_ptr<duckdb::DuckDBPyConnection, true> (*&)(pybind11::object const&, bool, pybind11::dict const&), duckdb::shared_ptr<duckdb::DuckDBPyConnection, true> (*)(pybind11::object const&, bool, pybind11::dict const&), pybind11::name const&, pybind11::scope const&, pybind11::sibling const&, char const (&) [142], pybind11::arg_v const&, pybind11::arg_v const&, pybind11::arg_v const&)::'lambda'(pybind11::detail::function_call&)::operator()(pybind11::detail::function_call&) const + 93
21  duckdb.cpython-313-darwin.so  	       0x108920684 void pybind11::cpp_function::initialize<duckdb::shared_ptr<duckdb::DuckDBPyConnection, true> (*&)(pybind11::object const&, bool, pybind11::dict const&), duckdb::shared_ptr<duckdb::DuckDBPyConnection, true>, pybind11::object const&, bool, pybind11::dict const&, pybind11::name, pybind11::scope, pybind11::sibling, char [142], pybind11::arg_v, pybind11::arg_v, pybind11::arg_v>(duckdb::shared_ptr<duckdb::DuckDBPyConnection, true> (*&)(pybind11::object const&, bool, pybind11::dict const&), duckdb::shared_ptr<duckdb::DuckDBPyConnection, true> (*)(pybind11::object const&, bool, pybind11::dict const&), pybind11::name const&, pybind11::scope const&, pybind11::sibling const&, char const (&) [142], pybind11::arg_v const&, pybind11::arg_v const&, pybind11::arg_v const&)::'lambda'(pybind11::detail::function_call&)::__invoke(pybind11::detail::function_call&) + 20
22  duckdb.cpython-313-darwin.so  	       0x1088ccf7a pybind11::cpp_function::dispatcher(_object*, _object*, _object*) + 5178
23  Python                        	       0x100ff81c6 cfunction_call + 70
24  Python                        	       0x100f9ab1f _PyObject_MakeTpCall + 127
25  Python                        	       0x1010cdc14 _PyEval_EvalFrameDefault + 6465
26  Python                        	       0x100fb6d7b gen_send_ex2 + 201
27  Python                        	       0x100fb6bda gen_send_ex + 28
28  Python                        	       0x100fb7e87 async_gen_asend_send + 129
29  Python                        	       0x1010d07d0 _PyEval_EvalFrameDefault + 17661
30  Python                        	       0x100fb6d7b gen_send_ex2 + 201
31  _asyncio.cpython-313-darwin.so	       0x100f1d0be task_step_impl + 470
32  _asyncio.cpython-313-darwin.so	       0x100f1ce83 task_step + 53
33  Python                        	       0x100f9ab1f _PyObject_MakeTpCall + 127
34  Python                        	       0x1010fd4c1 context_run + 134
35  Python                        	       0x100ff799b cfunction_vectorcall_FASTCALL_KEYWORDS + 94
36  Python                        	       0x1010d1f75 _PyEval_EvalFrameDefault + 23714
37  Python                        	       0x1010cc106 PyEval_EvalCode + 208
38  Python                        	       0x1010c6a26 builtin_exec + 482
39  Python                        	       0x100ff799b cfunction_vectorcall_FASTCALL_KEYWORDS + 94
40  Python                        	       0x1010d1f75 _PyEval_EvalFrameDefault + 23714
41  Python                        	       0x100f9d3de object_vacall + 313
42  Python                        	       0x100f9d229 PyObject_CallMethodObjArgs + 233
43  Python                        	       0x10111bf20 PyImport_ImportModuleLevelObject + 3600
44  Python                        	       0x1010cc952 _PyEval_EvalFrameDefault + 1663
45  Python                        	       0x1010cc106 PyEval_EvalCode + 208
46  Python                        	       0x101142b8e run_eval_code_obj + 97
47  Python                        	       0x10114252e run_mod + 154
48  Python                        	       0x101140b63 pyrun_file + 141
49  Python                        	       0x10113ff72 _PyRun_SimpleFileObject + 272
50  Python                        	       0x10113fba7 _PyRun_AnyFileObject + 66
51  Python                        	       0x101168a87 pymain_run_file_obj + 187
52  Python                        	       0x101168771 pymain_run_file + 94
53  Python                        	       0x1011678ce Py_RunMain + 1268
54  Python                        	       0x101167f93 pymain_main + 371
55  Python                        	       0x101168046 Py_BytesMain + 42
56  dyld                          	    0x7ff807f8a2cd start + 1805


Thread 0 crashed with X86 Thread State (64-bit):
  rax: 0x00007ff7bf4a89b8  rbx: 0x00000000000000a7  rcx: 0x0000000046a64a80  rdx: 0x0000000000000000
  rdi: 0x00007ff7bf4a89b8  rsi: 0x00000000000000a7  rbp: 0x00007ff7bf4a8970  rsp: 0x00007ff7bf4a8970
   r8: 0x0000000000000000   r9: 0x0000000000000001  r10: 0x8000000000000000  r11: 0x00007ff7bf4a8911
  r12: 0x0000000000000008  r13: 0x0000000000000008  r14: 0x0000000046a64a80  r15: 0x0000600002706430
  rip: 0x00007ff80834d4c9  rfl: 0x0000000000010246  cr2: 0x00000000000000a7
  
Logical CPU:     6
Error Code:      0x00000004 (no mapping for user data read)
Trap Number:     14

Thread 0 instruction stream:
  fa 10 76 56 c5 f8 10 4c-16 f0 48 83 ea 20 76 2a  ..vV...L..H.. v*
  c5 fc 10 06 c5 fc 11 07-48 83 c6 20 48 83 c7 20  ........H.. H.. 
  48 83 ea 20 72 14 c5 fc-10 06 c5 fc 11 07 48 83  H.. r.........H.
  c6 20 48 83 c7 20 48 83-ea 20 48 83 c2 10 7e 0c  . H.. H.. H...~.
  c5 f8 10 06 c5 f8 11 07-c5 f8 57 c0 c5 f8 11 0c  ..........W.....
  17 c5 f0 57 c9 5d c5 f8-77 c3 48 83 ea 08 72 10  ...W.]..w.H...r.
 [48]8b 0e 4c 8b 04 16 48-89 0f 4c 89 04 17 5d c3  H..L...H..L...].	<==
  48 83 c2 08 74 25 4d 31-c0 42 8a 0c 06 42 88 0c  H...t%M1.B...B..
  07 48 83 ea 01 74 14 42-8a 4c 06 01 42 88 4c 07  .H...t.B.L..B.L.
  01 49 83 c0 02 48 83 ea-01 75 de 5d c3 66 2e 0f  .I...H...u.].f..
  1f 84 00 00 00 00 00 c5-fc 10 06 48 83 c7 20 48  ...........H.. H
  83 e7 e0 48 89 f9 48 29-c1 48 01 ce 48 29 ca c5  ...H..H).H..H)..

Binary Images:
       0x100a53000 -        0x100a54fff org.python.python (3.13.5) <1417dcb1-7110-3c7a-a8b6-42973367b2cb> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python
       0x100f39000 -        0x1012d9fff org.python.python (3.13.5, (c) 2001-2024 Python Software Foundation.) <559fd0d5-2586-3f23-b1d2-7915b9afd925> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/Python
       0x100e91000 -        0x100e94fff _heapq.cpython-313-darwin.so (*) <1c358892-a0a2-3387-8105-4b87155a4d52> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_heapq.cpython-313-darwin.so
       0x100eac000 -        0x100eb9fff _socket.cpython-313-darwin.so (*) <486ae512-ed92-3aaa-a070-f04b527ebb74> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_socket.cpython-313-darwin.so
       0x100ec0000 -        0x100ecafff math.cpython-313-darwin.so (*) <8f73010c-e2e4-36fb-8087-473ee989c779> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/math.cpython-313-darwin.so
       0x100ea2000 -        0x100ea6fff select.cpython-313-darwin.so (*) <ee322bbe-d06a-3f3b-943c-671ce8884c3e> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/select.cpython-313-darwin.so
       0x100ede000 -        0x100ee5fff array.cpython-313-darwin.so (*) <e6ec34ee-7ad2-3cb7-a322-b38cb81e59a1> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/array.cpython-313-darwin.so
       0x100e98000 -        0x100e9afff fcntl.cpython-313-darwin.so (*) <e875663a-f32b-3209-9bda-db47838099b2> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/fcntl.cpython-313-darwin.so
       0x100ed0000 -        0x100ed2fff _posixsubprocess.cpython-313-darwin.so (*) <274ab92d-75d4-3e53-8b79-0ad4f7d6b5a9> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_posixsubprocess.cpython-313-darwin.so
       0x10158a000 -        0x1015a2fff _ssl.cpython-313-darwin.so (*) <c8f88493-511e-38a9-970e-4d38ce738ab5> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_ssl.cpython-313-darwin.so
       0x10168d000 -        0x101723fff libssl.3.dylib (*) <923b61c9-6f46-30ca-961a-15b34787e890> /usr/local/Cellar/openssl@3/3.5.0/lib/libssl.3.dylib
       0x101c41000 -        0x101f9cfff libcrypto.3.dylib (*) <0eba9848-291f-3fba-8637-ef70f57bf15f> /usr/local/Cellar/openssl@3/3.5.0/lib/libcrypto.3.dylib
       0x100ef7000 -        0x100efcfff _struct.cpython-313-darwin.so (*) <bf3e1a4a-2fb4-326f-803c-638234e8a022> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_struct.cpython-313-darwin.so
       0x100f02000 -        0x100f05fff binascii.cpython-313-darwin.so (*) <b6019894-dab9-380b-a7c7-fb14975e7526> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/binascii.cpython-313-darwin.so
       0x100ed7000 -        0x100ed9fff _opcode.cpython-313-darwin.so (*) <855fe1fe-055c-3fa0-b18d-fd30e702e9a0> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_opcode.cpython-313-darwin.so
       0x100e9e000 -        0x100e9efff _contextvars.cpython-313-darwin.so (*) <53885ad4-0003-3705-80b2-ff9ed66c4d44> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_contextvars.cpython-313-darwin.so
       0x100f1b000 -        0x100f23fff _asyncio.cpython-313-darwin.so (*) <96e80c35-a9ab-32ff-bf87-fc80352c233b> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_asyncio.cpython-313-darwin.so
       0x1015d3000 -        0x1015e8fff _pickle.cpython-313-darwin.so (*) <bafafa8a-6a0a-3b45-bdef-cc9fd2300cb1> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_pickle.cpython-313-darwin.so
       0x100eec000 -        0x100eedfff grp.cpython-313-darwin.so (*) <9b7de89a-0de0-3ba1-982b-881862834a6d> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/grp.cpython-313-darwin.so
       0x1015f0000 -        0x1015fefff _datetime.cpython-313-darwin.so (*) <48d86ad3-4fff-3b28-bd2c-7ca086ea286d> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_datetime.cpython-313-darwin.so
       0x10162f000 -        0x101649fff _decimal.cpython-313-darwin.so (*) <a1456820-9f54-3616-b4ac-2fabe8c85e6e> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_decimal.cpython-313-darwin.so
       0x101656000 -        0x101671fff libmpdec.4.0.1.dylib (*) <9b6249d9-bd04-359d-8de1-86912ab98227> /usr/local/Cellar/mpdecimal/4.0.1/lib/libmpdec.4.0.1.dylib
       0x100f2c000 -        0x100f32fff zlib.cpython-313-darwin.so (*) <1105bd4e-6ad2-3b30-8f3e-89e4c8d00ded> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/zlib.cpython-313-darwin.so
       0x100f0a000 -        0x100f0cfff _bz2.cpython-313-darwin.so (*) <27b58dd8-94fd-3355-9026-d404033fb299> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_bz2.cpython-313-darwin.so
       0x1015c1000 -        0x1015c6fff _lzma.cpython-313-darwin.so (*) <4831c524-9859-3ebe-a170-a19794745817> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_lzma.cpython-313-darwin.so
       0x101a64000 -        0x101a81fff liblzma.5.dylib (*) <54e14c86-cc43-3249-8f0f-dcbb13e9f869> /usr/local/Cellar/xz/5.8.1/lib/liblzma.5.dylib
       0x1015b6000 -        0x1015bbfff _json.cpython-313-darwin.so (*) <dd2cb206-e403-3d73-a5ff-f8ed8cbc5f19> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_json.cpython-313-darwin.so
       0x100ef1000 -        0x100ef3fff _bisect.cpython-313-darwin.so (*) <7b3d98fa-a6ed-323c-8179-f0fd9fbfffb7> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_bisect.cpython-313-darwin.so
       0x100f11000 -        0x100f12fff _random.cpython-313-darwin.so (*) <02aedcaa-6e12-3d38-9d63-39a2fbbfdbd6> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_random.cpython-313-darwin.so
       0x1026b5000 -        0x102b0bfff _pydantic_core.cpython-313-darwin.so (*) <6440dd98-ac0b-3e9d-88c3-e3eb4c674400> /Users/USER/Documents/*/_pydantic_core.cpython-313-darwin.so
       0x100f17000 -        0x100f17fff _uuid.cpython-313-darwin.so (*) <2d0f034d-1dcf-3a42-a8db-b85d457dd10c> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_uuid.cpython-313-darwin.so
       0x101611000 -        0x101615fff _zoneinfo.cpython-313-darwin.so (*) <c352b1f2-5d3b-35d6-be00-d4db8f9eddf2> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_zoneinfo.cpython-313-darwin.so
       0x10167a000 -        0x101681fff _hashlib.cpython-313-darwin.so (*) <528b700b-0249-32bc-8793-497b0859f1c1> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_hashlib.cpython-313-darwin.so
       0x101b88000 -        0x101b8efff _blake2.cpython-313-darwin.so (*) <5ff39a36-ad68-3f68-ac78-032474f4d0b5> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_blake2.cpython-313-darwin.so
       0x1015cc000 -        0x1015cdfff _scproxy.cpython-313-darwin.so (*) <b7fe2bf1-7412-3dc6-8c08-6747cd4b4c2b> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_scproxy.cpython-313-darwin.so
       0x102e27000 -        0x102ee6fff backend_c.cpython-313-darwin.so (*) <6642d831-e1c8-3ee4-927b-99289439a770> /Users/USER/Documents/*/backend_c.cpython-313-darwin.so
       0x102d4a000 -        0x102deffff unicodedata.cpython-313-darwin.so (*) <6765df4d-2e6b-3997-b607-e3f38e16a1d8> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/unicodedata.cpython-313-darwin.so
       0x10161a000 -        0x10161bfff _queue.cpython-313-darwin.so (*) <beccf008-2a6c-3741-8f50-6402fd0285ad> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_queue.cpython-313-darwin.so
       0x101620000 -        0x101622fff _multiprocessing.cpython-313-darwin.so (*) <2ceb90cb-9932-39c7-a0e8-ba2ed0daa58c> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_multiprocessing.cpython-313-darwin.so
       0x106b69000 -        0x1092a2fff duckdb.cpython-313-darwin.so (*) <25589936-cfa3-3ecc-9cdd-b0faed26b640> /Users/USER/Documents/*/duckdb.cpython-313-darwin.so
       0x101bd3000 -        0x101bddfff _multidict.cpython-313-darwin.so (*) <2696a910-c516-345a-afce-76199d475cc9> /Users/USER/Documents/*/_multidict.cpython-313-darwin.so
       0x101be6000 -        0x101bfafff _quoting_c.cpython-313-darwin.so (*) <5c7c053a-95e4-3162-b7d1-d970390c1aa4> /Users/USER/Documents/*/_quoting_c.cpython-313-darwin.so
       0x101c06000 -        0x101c13fff _helpers_c.cpython-313-darwin.so (*) <48a29ceb-1a4a-38a7-930f-bfd1b7ee2d6d> /Users/USER/Documents/*/_helpers_c.cpython-313-darwin.so
       0x101ba1000 -        0x101ba8fff _http_writer.cpython-313-darwin.so (*) <062d0da5-beaa-3919-baf0-ebc8f47a632c> /Users/USER/Documents/*/_http_writer.cpython-313-darwin.so
       0x103707000 -        0x103752fff _http_parser.cpython-313-darwin.so (*) <c158ab4a-805a-31d2-83d3-b39292030869> /Users/USER/Documents/*/_http_parser.cpython-313-darwin.so
       0x101c1d000 -        0x101c22fff mask.cpython-313-darwin.so (*) <177eb6a6-f1c6-36fb-842c-20f391254398> /Users/USER/Documents/*/mask.cpython-313-darwin.so
       0x102651000 -        0x102671fff reader_c.cpython-313-darwin.so (*) <09875ed8-1f3f-34be-a68e-325933cacab8> /Users/USER/Documents/*/reader_c.cpython-313-darwin.so
       0x102620000 -        0x10262efff _frozenlist.cpython-313-darwin.so (*) <74b8a47c-087a-3250-89eb-f30452d93c79> /Users/USER/Documents/*/_frozenlist.cpython-313-darwin.so
       0x10402a000 -        0x1040cefff _regex.cpython-313-darwin.so (*) <0cffe7c0-cc84-3b97-8533-f5b50482e4f0> /Users/USER/Documents/*/_regex.cpython-313-darwin.so
       0x1043a5000 -        0x104591fff _tiktoken.cpython-313-darwin.so (*) <abceeb8a-b2f4-33c3-9139-e0f28b4bd46c> /Users/USER/Documents/*/_tiktoken.cpython-313-darwin.so
       0x103fb6000 -        0x103febfff _binding.cpython-313-darwin.so (*) <b1ca786c-aba3-3163-9055-5ffa66273888> /Users/USER/Documents/*/_binding.cpython-313-darwin.so
       0x102df4000 -        0x102e06fff _ctypes.cpython-313-darwin.so (*) <5127405a-9319-35c0-bc94-ec726ecd09b4> /usr/local/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload/_ctypes.cpython-313-darwin.so
       0x104c08000 -        0x1051a6fff _binding.abi3.so (*) <c9abf2f2-fa02-3a2c-b9d7-51d908aba0e4> /Users/USER/Documents/*/_binding.abi3.so
       0x101608000 -        0x101609fff _binding.abi3.so (*) <c2bf44b6-35a5-310e-9ac2-2f647ea7dff1> /Users/USER/Documents/*/_binding.abi3.so
       0x103f6d000 -        0x103f9bfff _binding.abi3.so (*) <f30765c3-0e77-364a-90ee-f5d170842bb7> /Users/USER/Documents/*/_binding.abi3.so
       0x104663000 -        0x1047aafff _binding.abi3.so (*) <8e854ff8-2f51-34d7-87d9-eead886e6f89> /Users/USER/Documents/*/_binding.abi3.so
       0x104278000 -        0x104303fff _binding.abi3.so (*) <8d726337-5b4f-301e-aca6-ccaa3bdd0670> /Users/USER/Documents/*/_binding.abi3.so
       0x1051ad000 -        0x1054e9fff _binding.abi3.so (*) <9d6e55d4-97f8-3f49-8cb2-52cefa61723f> /Users/USER/Documents/*/_binding.abi3.so
       0x1048a9000 -        0x10499dfff _binding.abi3.so (*) <db39dac6-979e-349b-ace7-ec6d0f87e49f> /Users/USER/Documents/*/_binding.abi3.so
       0x105835000 -        0x105b73fff _binding.abi3.so (*) <5f49ff7a-f179-3ebd-bf7f-23b16c7a5c5a> /Users/USER/Documents/*/_binding.abi3.so
       0x1041e7000 -        0x104210fff _binding.abi3.so (*) <68ffd454-fef6-3788-b365-658c1c79cfad> /Users/USER/Documents/*/_binding.abi3.so
       0x1049a2000 -        0x104a4bfff _binding.abi3.so (*) <79c92d23-597b-3c6f-aab0-22b7452f9525> /Users/USER/Documents/*/_binding.abi3.so
       0x1047b0000 -        0x10481efff _binding.abi3.so (*) <a64ee39e-6de9-386f-be9a-13f5f4eb334c> /Users/USER/Documents/*/_binding.abi3.so
       0x10430c000 -        0x104353fff _yaml.cpython-313-darwin.so (*) <d7ee126d-e2a5-3f61-afa8-8a97becf0955> /Users/USER/Documents/*/_yaml.cpython-313-darwin.so
       0x101b93000 -        0x101b95fff _watchdog_fsevents.cpython-313-darwin.so (*) <9f97b064-c071-3f3a-afea-5b9f812c64a3> /Users/USER/Documents/*/_watchdog_fsevents.cpython-313-darwin.so
       0x102639000 -        0x102640fff _psutil_osx.abi3.so (*) <59f1656e-2822-3adc-8cf2-9e956022d770> /Users/USER/Documents/*/_psutil_osx.abi3.so
       0x101c32000 -        0x101c35fff _psutil_posix.abi3.so (*) <a71ebbc9-266d-3611-89f7-e2f883d97063> /Users/USER/Documents/*/_psutil_posix.abi3.so
       0x104823000 -        0x104887fff java.abi3.so (*) <db69d0df-e2f6-3a39-bc90-143ef085412c> /Users/USER/Documents/*/java.abi3.so
       0x104213000 -        0x10426bfff javascript.abi3.so (*) <5cf79c83-4aaa-3d3d-b7e8-148edbe068d6> /Users/USER/Documents/*/javascript.abi3.so
       0x1055f1000 -        0x10574afff typescript.abi3.so (*) <e6bfbb23-cf2a-3636-b6e5-72a7a96d11a6> /Users/USER/Documents/*/typescript.abi3.so
       0x104368000 -        0x10439bfff go.abi3.so (*) <f1f5a697-02fa-35b7-bd61-e5a8d6677353> /Users/USER/Documents/*/go.abi3.so
       0x105e23000 -        0x105f66fff bash.abi3.so (*) <87a02f44-c337-36c8-afcc-4d67f215178c> /Users/USER/Documents/*/bash.abi3.so
       0x102682000 -        0x1026acfff matlab.abi3.so (*) <c14cb07e-9930-3b4a-8e29-4778287e41d0> /Users/USER/Documents/*/matlab.abi3.so
       0x105f6c000 -        0x10607cfff rust.abi3.so (*) <42ae6a08-1c43-3482-a76f-dc9a31fc8481> /Users/USER/Documents/*/rust.abi3.so
       0x101c28000 -        0x101c2efff toml.abi3.so (*) <7c1fe611-6d7d-3576-862f-dcf18ce13763> /Users/USER/Documents/*/toml.abi3.so
    0x7ff80834c000 -     0x7ff808355fe7 libsystem_platform.dylib (*) <c55810b0-b8d2-3648-9009-570354c94d10> /usr/lib/system/libsystem_platform.dylib
    0x7ff807f84000 -     0x7ff80800fc7f dyld (*) <f2913392-361a-304f-b30d-486be5639e2d> /usr/lib/dyld
               0x0 - 0xffffffffffffffff ??? (*) <00000000-0000-0000-0000-000000000000> ???

External Modification Summary:
  Calls made by other processes targeting this process:
    task_for_pid: 0
    thread_create: 0
    thread_set_state: 0
  Calls made by this process:
    task_for_pid: 0
    thread_create: 0
    thread_set_state: 0
  Calls made by all processes on this machine:
    task_for_pid: 0
    thread_create: 0
    thread_set_state: 0

VM Region Summary:
ReadOnly portion of Libraries: Total=504.2M resident=0K(0%) swapped_out_or_unallocated=504.2M(100%)
Writable regions: Total=688.4M written=0K(0%) resident=0K(0%) swapped_out=0K(0%) unallocated=688.4M(100%)

                                VIRTUAL   REGION 
REGION TYPE                        SIZE    COUNT (non-coalesced) 
===========                     =======  ======= 
Kernel Alloc Once                    8K        1 
MALLOC                           624.3M       71 
MALLOC guard page                   16K        4 
MALLOC_LARGE (reserved)           12.4M        2         reserved VM address space (unallocated)
STACK GUARD                          4K        1 
Stack                             16.0M        1 
VM_ALLOCATE                       35.0M       36 
__DATA                            6370K      352 
__DATA_CONST                      22.5M      332 
__DATA_DIRTY                       436K       92 
__FONT_DATA                        2352        1 
__LINKEDIT                       202.0M       77 
__OBJC_RO                         76.9M        1 
__OBJC_RW                         2375K        2 
__TEXT                           302.2M      375 
__TPRO_CONST                       272K        2 
dyld private memory                160K        2 
shared memory                       32K        4 
===========                     =======  ======= 
TOTAL                              1.3G     1356 
TOTAL, minus reserved VM space     1.3G     1356 



-----------
Full Report
-----------

{"app_name":"Python","timestamp":"2025-06-27 12:35:36.00 +0300","app_version":"3.13.5","slice_uuid":"1417dcb1-7110-3c7a-a8b6-42973367b2cb","build_version":"3.13.5","platform":1,"bundleID":"org.python.python","share_with_app_devs":1,"is_first_party":0,"bug_type":"309","os_version":"macOS 15.3 (24D60)","roots_installed":0,"name":"Python","incident_id":"A357AD50-B0BC-47E5-98C2-CEFFD4342928"}
{
  "uptime" : 350000,
  "procRole" : "Unspecified",
  "version" : 2,
  "userID" : 501,
  "deployVersion" : 210,
  "modelCode" : "MacBookPro15,1",
  "coalitionID" : 2200,
  "osVersion" : {
    "train" : "macOS 15.3",
    "build" : "24D60",
    "releaseType" : "User"
  },
  "captureTime" : "2025-06-27 12:35:35.9371 +0300",
  "codeSigningMonitor" : 0,
  "incident" : "A357AD50-B0BC-47E5-98C2-CEFFD4342928",
  "pid" : 28566,
  "cpuType" : "X86-64",
  "roots_installed" : 0,
  "bug_type" : "309",
  "procLaunch" : "2025-06-27 12:35:34.8648 +0300",
  "procStartAbsTime" : 353801825430688,
  "procExitAbsTime" : 353802897385033,
  "procName" : "Python",
  "procPath" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/Resources\/Python.app\/Contents\/MacOS\/Python",
  "bundleInfo" : {"CFBundleShortVersionString":"3.13.5","CFBundleVersion":"3.13.5","CFBundleIdentifier":"org.python.python"},
  "storeInfo" : {"deviceIdentifierForVendor":"BAD7EE95-3251-5071-BF6A-81277CCC405D","thirdParty":true},
  "parentProc" : "uv",
  "parentPid" : 28565,
  "coalitionName" : "com.googlecode.iterm2",
  "crashReporterKey" : "581AD0EC-17E0-E19D-40A9-E16410889E58",
  "responsiblePid" : 3722,
  "responsibleProc" : "iTerm2",
  "codeSigningID" : "",
  "codeSigningTeamID" : "",
  "codeSigningValidationCategory" : 0,
  "codeSigningTrustLevel" : 4294967295,
  "bootSessionUUID" : "CBCA518C-DC50-4E57-8DBF-006E0DAD674E",
  "wakeTime" : 3084,
  "bridgeVersion" : {"build":"22P3051","train":"9.3"},
  "sleepWakeUUID" : "202100F2-F243-49AF-8F12-3AE2847C0E92",
  "sip" : "enabled",
  "vmRegionInfo" : "0xa7 is not in any region.  Bytes before following region: 4305792857\n      REGION TYPE                    START - END         [ VSIZE] PRT\/MAX SHRMOD  REGION DETAIL\n      UNUSED SPACE AT START\n--->  \n      __TEXT                      100a53000-100a55000    [    8K] r-x\/r-x SM=COW  \/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/Resources\/Python.app\/Contents\/MacOS\/Python",
  "exception" : {"codes":"0x0000000000000001, 0x00000000000000a7","rawCodes":[1,167],"type":"EXC_BAD_ACCESS","signal":"SIGSEGV","subtype":"KERN_INVALID_ADDRESS at 0x00000000000000a7"},
  "termination" : {"flags":0,"code":11,"namespace":"SIGNAL","indicator":"Segmentation fault: 11","byProc":"exc handler","byPid":28566},
  "vmregioninfo" : "0xa7 is not in any region.  Bytes before following region: 4305792857\n      REGION TYPE                    START - END         [ VSIZE] PRT\/MAX SHRMOD  REGION DETAIL\n      UNUSED SPACE AT START\n--->  \n      __TEXT                      100a53000-100a55000    [    8K] r-x\/r-x SM=COW  \/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/Resources\/Python.app\/Contents\/MacOS\/Python",
  "extMods" : {"caller":{"thread_create":0,"thread_set_state":0,"task_for_pid":0},"system":{"thread_create":0,"thread_set_state":0,"task_for_pid":0},"targeted":{"thread_create":0,"thread_set_state":0,"task_for_pid":0},"warnings":0},
  "faultingThread" : 0,
  "threads" : [{"triggered":true,"id":8565361,"instructionState":{"instructionStream":{"bytes":[250,16,118,86,197,248,16,76,22,240,72,131,234,32,118,42,197,252,16,6,197,252,17,7,72,131,198,32,72,131,199,32,72,131,234,32,114,20,197,252,16,6,197,252,17,7,72,131,198,32,72,131,199,32,72,131,234,32,72,131,194,16,126,12,197,248,16,6,197,248,17,7,197,248,87,192,197,248,17,12,23,197,240,87,201,93,197,248,119,195,72,131,234,8,114,16,72,139,14,76,139,4,22,72,137,15,76,137,4,23,93,195,72,131,194,8,116,37,77,49,192,66,138,12,6,66,136,12,7,72,131,234,1,116,20,66,138,76,6,1,66,136,76,7,1,73,131,192,2,72,131,234,1,117,222,93,195,102,46,15,31,132,0,0,0,0,0,197,252,16,6,72,131,199,32,72,131,231,224,72,137,249,72,41,193,72,1,206,72,41,202,197],"offset":96}},"threadState":{"r13":{"value":8},"rax":{"value":140702042982840},"rflags":{"value":66118},"cpu":{"value":6},"r14":{"value":1185303168},"rsi":{"value":167},"r8":{"value":0},"cr2":{"value":167},"rdx":{"value":0},"r10":{"value":9223372036854775808},"r9":{"value":1},"r15":{"value":105553157186608},"rbx":{"value":167},"trap":{"value":14,"description":"(no mapping for user data read)"},"err":{"value":4},"r11":{"value":140702042982673},"rip":{"value":140703266297033,"matchesCrashFrame":1},"rbp":{"value":140702042982768},"rsp":{"value":140702042982768},"r12":{"value":8},"rcx":{"value":1185303168},"flavor":"x86_THREAD_STATE","rdi":{"value":140702042982840}},"queue":"com.apple.main-thread","frames":[{"imageOffset":5321,"symbol":"_platform_memmove$VARIANT$Haswell","symbolLocation":169,"imageIndex":75},{"imageOffset":30236171,"symbol":"duckdb::StringStats::Update(duckdb::BaseStatistics&, duckdb::string_t const&)","symbolLocation":91,"imageIndex":39},{"imageOffset":29420482,"symbol":"duckdb::UncompressedStringStorage::StringAppendBase(duckdb::BufferHandle&, duckdb::ColumnSegment&, duckdb::SegmentStatistics&, duckdb::UnifiedVectorFormat&, unsigned long long, unsigned long long)","symbolLocation":658,"imageIndex":39},{"imageOffset":30331638,"symbol":"duckdb::ColumnData::AppendData(duckdb::BaseStatistics&, duckdb::ColumnAppendState&, duckdb::UnifiedVectorFormat&, unsigned long long)","symbolLocation":54,"imageIndex":39},{"imageOffset":30563026,"symbol":"duckdb::StandardColumnData::AppendData(duckdb::BaseStatistics&, duckdb::ColumnAppendState&, duckdb::UnifiedVectorFormat&, unsigned long long)","symbolLocation":34,"imageIndex":39},{"imageOffset":30328662,"symbol":"duckdb::ColumnData::Append(duckdb::BaseStatistics&, duckdb::ColumnAppendState&, duckdb::Vector&, unsigned long long)","symbolLocation":86,"imageIndex":39},{"imageOffset":30518746,"symbol":"duckdb::RowGroupCollection::Append(duckdb::DataChunk&, duckdb::TableAppendState&)","symbolLocation":426,"imageIndex":39},{"imageOffset":29054718,"symbol":"duckdb::LocalStorage::Append(duckdb::LocalAppendState&, duckdb::DataChunk&)","symbolLocation":174,"imageIndex":39},{"imageOffset":29057239,"symbol":"duckdb::DataTable::LocalWALAppend(duckdb::TableCatalogEntry&, duckdb::ClientContext&, duckdb::DataChunk&, duckdb::vector<duckdb::unique_ptr<duckdb::BoundConstraint, std::__1::default_delete<duckdb::BoundConstraint>, true>, true> const&)","symbolLocation":119,"imageIndex":39},{"imageOffset":29210287,"symbol":"duckdb::WriteAheadLogDeserializer::ReplayInsert()","symbolLocation":191,"imageIndex":39},{"imageOffset":29198057,"symbol":"duckdb::WriteAheadLogDeserializer::ReplayEntry()","symbolLocation":153,"imageIndex":39},{"imageOffset":29194895,"symbol":"duckdb::WriteAheadLog::ReplayInternal(duckdb::AttachedDatabase&, duckdb::unique_ptr<duckdb::FileHandle, std::__1::default_delete<duckdb::FileHandle>, true>)","symbolLocation":1103,"imageIndex":39},{"imageOffset":29112379,"symbol":"duckdb::WriteAheadLog::Replay(duckdb::FileSystem&, duckdb::AttachedDatabase&, std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&)","symbolLocation":91,"imageIndex":39},{"imageOffset":29106780,"symbol":"duckdb::SingleFileStorageManager::LoadDatabase(duckdb::StorageOptions)","symbolLocation":732,"imageIndex":39},{"imageOffset":25372032,"symbol":"duckdb::DatabaseInstance::CreateMainDatabase()","symbolLocation":656,"imageIndex":39},{"imageOffset":25377646,"symbol":"duckdb::DatabaseInstance::Initialize(char const*, duckdb::DBConfig*)","symbolLocation":1774,"imageIndex":39},{"imageOffset":25382350,"symbol":"duckdb::DuckDB::DuckDB(char const*, duckdb::DBConfig*)","symbolLocation":46,"imageIndex":39},{"imageOffset":25398774,"symbol":"duckdb::DBInstanceCache::CreateInstanceInternal(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, duckdb::DBConfig&, bool, std::__1::function<void (duckdb::DuckDB&)> const&)","symbolLocation":854,"imageIndex":39},{"imageOffset":25400119,"symbol":"duckdb::DBInstanceCache::GetOrCreateInstance(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, duckdb::DBConfig&, bool, std::__1::function<void (duckdb::DuckDB&)> const&)","symbolLocation":167,"imageIndex":39},{"imageOffset":31629306,"symbol":"duckdb::DuckDBPyConnection::Connect(pybind11::object const&, bool, pybind11::dict const&)","symbolLocation":2954,"imageIndex":39},{"imageOffset":31160045,"symbol":"void pybind11::cpp_function::initialize<duckdb::shared_ptr<duckdb::DuckDBPyConnection, true> (*&)(pybind11::object const&, bool, pybind11::dict const&), duckdb::shared_ptr<duckdb::DuckDBPyConnection, true>, pybind11::object const&, bool, pybind11::dict const&, pybind11::name, pybind11::scope, pybind11::sibling, char [142], pybind11::arg_v, pybind11::arg_v, pybind11::arg_v>(duckdb::shared_ptr<duckdb::DuckDBPyConnection, true> (*&)(pybind11::object const&, bool, pybind11::dict const&), duckdb::shared_ptr<duckdb::DuckDBPyConnection, true> (*)(pybind11::object const&, bool, pybind11::dict const&), pybind11::name const&, pybind11::scope const&, pybind11::sibling const&, char const (&) [142], pybind11::arg_v const&, pybind11::arg_v const&, pybind11::arg_v const&)::'lambda'(pybind11::detail::function_call&)::operator()(pybind11::detail::function_call&) const","symbolLocation":93,"imageIndex":39},{"imageOffset":31159940,"symbol":"void pybind11::cpp_function::initialize<duckdb::shared_ptr<duckdb::DuckDBPyConnection, true> (*&)(pybind11::object const&, bool, pybind11::dict const&), duckdb::shared_ptr<duckdb::DuckDBPyConnection, true>, pybind11::object const&, bool, pybind11::dict const&, pybind11::name, pybind11::scope, pybind11::sibling, char [142], pybind11::arg_v, pybind11::arg_v, pybind11::arg_v>(duckdb::shared_ptr<duckdb::DuckDBPyConnection, true> (*&)(pybind11::object const&, bool, pybind11::dict const&), duckdb::shared_ptr<duckdb::DuckDBPyConnection, true> (*)(pybind11::object const&, bool, pybind11::dict const&), pybind11::name const&, pybind11::scope const&, pybind11::sibling const&, char const (&) [142], pybind11::arg_v const&, pybind11::arg_v const&, pybind11::arg_v const&)::'lambda'(pybind11::detail::function_call&)::__invoke(pybind11::detail::function_call&)","symbolLocation":20,"imageIndex":39},{"imageOffset":30818170,"symbol":"pybind11::cpp_function::dispatcher(_object*, _object*, _object*)","symbolLocation":5178,"imageIndex":39},{"imageOffset":782790,"symbol":"cfunction_call","symbolLocation":70,"imageIndex":1},{"imageOffset":400159,"symbol":"_PyObject_MakeTpCall","symbolLocation":127,"imageIndex":1},{"imageOffset":1657876,"symbol":"_PyEval_EvalFrameDefault","symbolLocation":6465,"imageIndex":1},{"imageOffset":515451,"symbol":"gen_send_ex2","symbolLocation":201,"imageIndex":1},{"imageOffset":515034,"symbol":"gen_send_ex","symbolLocation":28,"imageIndex":1},{"imageOffset":519815,"symbol":"async_gen_asend_send","symbolLocation":129,"imageIndex":1},{"imageOffset":1669072,"symbol":"_PyEval_EvalFrameDefault","symbolLocation":17661,"imageIndex":1},{"imageOffset":515451,"symbol":"gen_send_ex2","symbolLocation":201,"imageIndex":1},{"imageOffset":8382,"symbol":"task_step_impl","symbolLocation":470,"imageIndex":16},{"imageOffset":7811,"symbol":"task_step","symbolLocation":53,"imageIndex":16},{"imageOffset":400159,"symbol":"_PyObject_MakeTpCall","symbolLocation":127,"imageIndex":1},{"imageOffset":1852609,"symbol":"context_run","symbolLocation":134,"imageIndex":1},{"imageOffset":780699,"symbol":"cfunction_vectorcall_FASTCALL_KEYWORDS","symbolLocation":94,"imageIndex":1},{"imageOffset":1675125,"symbol":"_PyEval_EvalFrameDefault","symbolLocation":23714,"imageIndex":1},{"imageOffset":1650950,"symbol":"PyEval_EvalCode","symbolLocation":208,"imageIndex":1},{"imageOffset":1628710,"symbol":"builtin_exec","symbolLocation":482,"imageIndex":1},{"imageOffset":780699,"symbol":"cfunction_vectorcall_FASTCALL_KEYWORDS","symbolLocation":94,"imageIndex":1},{"imageOffset":1675125,"symbol":"_PyEval_EvalFrameDefault","symbolLocation":23714,"imageIndex":1},{"imageOffset":410590,"symbol":"object_vacall","symbolLocation":313,"imageIndex":1},{"imageOffset":410153,"symbol":"PyObject_CallMethodObjArgs","symbolLocation":233,"imageIndex":1},{"imageOffset":1978144,"symbol":"PyImport_ImportModuleLevelObject","symbolLocation":3600,"imageIndex":1},{"imageOffset":1653074,"symbol":"_PyEval_EvalFrameDefault","symbolLocation":1663,"imageIndex":1},{"imageOffset":1650950,"symbol":"PyEval_EvalCode","symbolLocation":208,"imageIndex":1},{"imageOffset":2136974,"symbol":"run_eval_code_obj","symbolLocation":97,"imageIndex":1},{"imageOffset":2135342,"symbol":"run_mod","symbolLocation":154,"imageIndex":1},{"imageOffset":2128739,"symbol":"pyrun_file","symbolLocation":141,"imageIndex":1},{"imageOffset":2125682,"symbol":"_PyRun_SimpleFileObject","symbolLocation":272,"imageIndex":1},{"imageOffset":2124711,"symbol":"_PyRun_AnyFileObject","symbolLocation":66,"imageIndex":1},{"imageOffset":2292359,"symbol":"pymain_run_file_obj","symbolLocation":187,"imageIndex":1},{"imageOffset":2291569,"symbol":"pymain_run_file","symbolLocation":94,"imageIndex":1},{"imageOffset":2287822,"symbol":"Py_RunMain","symbolLocation":1268,"imageIndex":1},{"imageOffset":2289555,"symbol":"pymain_main","symbolLocation":371,"imageIndex":1},{"imageOffset":2289734,"symbol":"Py_BytesMain","symbolLocation":42,"imageIndex":1},{"imageOffset":25293,"symbol":"start","symbolLocation":1805,"imageIndex":76}]}],
  "usedImages" : [
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4305793024,
    "CFBundleShortVersionString" : "3.13.5",
    "CFBundleIdentifier" : "org.python.python",
    "size" : 8192,
    "uuid" : "1417dcb1-7110-3c7a-a8b6-42973367b2cb",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/Resources\/Python.app\/Contents\/MacOS\/Python",
    "name" : "Python",
    "CFBundleVersion" : "3.13.5"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4310929408,
    "CFBundleShortVersionString" : "3.13.5, (c) 2001-2024 Python Software Foundation.",
    "CFBundleIdentifier" : "org.python.python",
    "size" : 3805184,
    "uuid" : "559fd0d5-2586-3f23-b1d2-7915b9afd925",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/Python",
    "name" : "Python",
    "CFBundleVersion" : "3.13.5"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4310241280,
    "size" : 16384,
    "uuid" : "1c358892-a0a2-3387-8105-4b87155a4d52",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_heapq.cpython-313-darwin.so",
    "name" : "_heapq.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4310351872,
    "size" : 57344,
    "uuid" : "486ae512-ed92-3aaa-a070-f04b527ebb74",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_socket.cpython-313-darwin.so",
    "name" : "_socket.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4310433792,
    "size" : 45056,
    "uuid" : "8f73010c-e2e4-36fb-8087-473ee989c779",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/math.cpython-313-darwin.so",
    "name" : "math.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4310310912,
    "size" : 20480,
    "uuid" : "ee322bbe-d06a-3f3b-943c-671ce8884c3e",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/select.cpython-313-darwin.so",
    "name" : "select.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4310556672,
    "size" : 32768,
    "uuid" : "e6ec34ee-7ad2-3cb7-a322-b38cb81e59a1",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/array.cpython-313-darwin.so",
    "name" : "array.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4310269952,
    "size" : 12288,
    "uuid" : "e875663a-f32b-3209-9bda-db47838099b2",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/fcntl.cpython-313-darwin.so",
    "name" : "fcntl.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4310499328,
    "size" : 12288,
    "uuid" : "274ab92d-75d4-3e53-8b79-0ad4f7d6b5a9",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_posixsubprocess.cpython-313-darwin.so",
    "name" : "_posixsubprocess.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4317552640,
    "size" : 102400,
    "uuid" : "c8f88493-511e-38a9-970e-4d38ce738ab5",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_ssl.cpython-313-darwin.so",
    "name" : "_ssl.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4318613504,
    "size" : 618496,
    "uuid" : "923b61c9-6f46-30ca-961a-15b34787e890",
    "path" : "\/usr\/local\/Cellar\/openssl@3\/3.5.0\/lib\/libssl.3.dylib",
    "name" : "libssl.3.dylib"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4324593664,
    "size" : 3522560,
    "uuid" : "0eba9848-291f-3fba-8637-ef70f57bf15f",
    "path" : "\/usr\/local\/Cellar\/openssl@3\/3.5.0\/lib\/libcrypto.3.dylib",
    "name" : "libcrypto.3.dylib"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4310659072,
    "size" : 24576,
    "uuid" : "bf3e1a4a-2fb4-326f-803c-638234e8a022",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_struct.cpython-313-darwin.so",
    "name" : "_struct.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4310704128,
    "size" : 16384,
    "uuid" : "b6019894-dab9-380b-a7c7-fb14975e7526",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/binascii.cpython-313-darwin.so",
    "name" : "binascii.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4310528000,
    "size" : 12288,
    "uuid" : "855fe1fe-055c-3fa0-b18d-fd30e702e9a0",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_opcode.cpython-313-darwin.so",
    "name" : "_opcode.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4310294528,
    "size" : 4096,
    "uuid" : "53885ad4-0003-3705-80b2-ff9ed66c4d44",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_contextvars.cpython-313-darwin.so",
    "name" : "_contextvars.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4310806528,
    "size" : 36864,
    "uuid" : "96e80c35-a9ab-32ff-bf87-fc80352c233b",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_asyncio.cpython-313-darwin.so",
    "name" : "_asyncio.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4317851648,
    "size" : 90112,
    "uuid" : "bafafa8a-6a0a-3b45-bdef-cc9fd2300cb1",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_pickle.cpython-313-darwin.so",
    "name" : "_pickle.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4310614016,
    "size" : 8192,
    "uuid" : "9b7de89a-0de0-3ba1-982b-881862834a6d",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/grp.cpython-313-darwin.so",
    "name" : "grp.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4317970432,
    "size" : 61440,
    "uuid" : "48d86ad3-4fff-3b28-bd2c-7ca086ea286d",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_datetime.cpython-313-darwin.so",
    "name" : "_datetime.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4318228480,
    "size" : 110592,
    "uuid" : "a1456820-9f54-3616-b4ac-2fabe8c85e6e",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_decimal.cpython-313-darwin.so",
    "name" : "_decimal.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4318388224,
    "size" : 114688,
    "uuid" : "9b6249d9-bd04-359d-8de1-86912ab98227",
    "path" : "\/usr\/local\/Cellar\/mpdecimal\/4.0.1\/lib\/libmpdec.4.0.1.dylib",
    "name" : "libmpdec.4.0.1.dylib"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4310876160,
    "size" : 28672,
    "uuid" : "1105bd4e-6ad2-3b30-8f3e-89e4c8d00ded",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/zlib.cpython-313-darwin.so",
    "name" : "zlib.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4310736896,
    "size" : 12288,
    "uuid" : "27b58dd8-94fd-3355-9026-d404033fb299",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_bz2.cpython-313-darwin.so",
    "name" : "_bz2.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4317777920,
    "size" : 24576,
    "uuid" : "4831c524-9859-3ebe-a170-a19794745817",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_lzma.cpython-313-darwin.so",
    "name" : "_lzma.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4322639872,
    "size" : 122880,
    "uuid" : "54e14c86-cc43-3249-8f0f-dcbb13e9f869",
    "path" : "\/usr\/local\/Cellar\/xz\/5.8.1\/lib\/liblzma.5.dylib",
    "name" : "liblzma.5.dylib"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4317732864,
    "size" : 24576,
    "uuid" : "dd2cb206-e403-3d73-a5ff-f8ed8cbc5f19",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_json.cpython-313-darwin.so",
    "name" : "_json.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4310634496,
    "size" : 12288,
    "uuid" : "7b3d98fa-a6ed-323c-8179-f0fd9fbfffb7",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_bisect.cpython-313-darwin.so",
    "name" : "_bisect.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4310765568,
    "size" : 8192,
    "uuid" : "02aedcaa-6e12-3d38-9d63-39a2fbbfdbd6",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_random.cpython-313-darwin.so",
    "name" : "_random.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4335554560,
    "size" : 4550656,
    "uuid" : "6440dd98-ac0b-3e9d-88c3-e3eb4c674400",
    "path" : "\/Users\/USER\/Documents\/*\/_pydantic_core.cpython-313-darwin.so",
    "name" : "_pydantic_core.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4310790144,
    "size" : 4096,
    "uuid" : "2d0f034d-1dcf-3a42-a8db-b85d457dd10c",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_uuid.cpython-313-darwin.so",
    "name" : "_uuid.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4318105600,
    "size" : 20480,
    "uuid" : "c352b1f2-5d3b-35d6-be00-d4db8f9eddf2",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_zoneinfo.cpython-313-darwin.so",
    "name" : "_zoneinfo.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4318535680,
    "size" : 32768,
    "uuid" : "528b700b-0249-32bc-8793-497b0859f1c1",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_hashlib.cpython-313-darwin.so",
    "name" : "_hashlib.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4323835904,
    "size" : 28672,
    "uuid" : "5ff39a36-ad68-3f68-ac78-032474f4d0b5",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_blake2.cpython-313-darwin.so",
    "name" : "_blake2.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4317822976,
    "size" : 8192,
    "uuid" : "b7fe2bf1-7412-3dc6-8c08-6747cd4b4c2b",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_scproxy.cpython-313-darwin.so",
    "name" : "_scproxy.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4343361536,
    "size" : 786432,
    "uuid" : "6642d831-e1c8-3ee4-927b-99289439a770",
    "path" : "\/Users\/USER\/Documents\/*\/backend_c.cpython-313-darwin.so",
    "name" : "backend_c.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4342456320,
    "size" : 679936,
    "uuid" : "6765df4d-2e6b-3997-b607-e3f38e16a1d8",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/unicodedata.cpython-313-darwin.so",
    "name" : "unicodedata.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4318142464,
    "size" : 8192,
    "uuid" : "beccf008-2a6c-3741-8f50-6402fd0285ad",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_queue.cpython-313-darwin.so",
    "name" : "_queue.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4318167040,
    "size" : 12288,
    "uuid" : "2ceb90cb-9932-39c7-a0e8-ba2ed0daa58c",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_multiprocessing.cpython-313-darwin.so",
    "name" : "_multiprocessing.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4407595008,
    "size" : 41132032,
    "uuid" : "25589936-cfa3-3ecc-9cdd-b0faed26b640",
    "path" : "\/Users\/USER\/Documents\/*\/duckdb.cpython-313-darwin.so",
    "name" : "duckdb.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4324143104,
    "size" : 45056,
    "uuid" : "2696a910-c516-345a-afce-76199d475cc9",
    "path" : "\/Users\/USER\/Documents\/*\/_multidict.cpython-313-darwin.so",
    "name" : "_multidict.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4324220928,
    "size" : 86016,
    "uuid" : "5c7c053a-95e4-3162-b7d1-d970390c1aa4",
    "path" : "\/Users\/USER\/Documents\/*\/_quoting_c.cpython-313-darwin.so",
    "name" : "_quoting_c.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4324352000,
    "size" : 57344,
    "uuid" : "48a29ceb-1a4a-38a7-930f-bfd1b7ee2d6d",
    "path" : "\/Users\/USER\/Documents\/*\/_helpers_c.cpython-313-darwin.so",
    "name" : "_helpers_c.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4323938304,
    "size" : 32768,
    "uuid" : "062d0da5-beaa-3919-baf0-ebc8f47a632c",
    "path" : "\/Users\/USER\/Documents\/*\/_http_writer.cpython-313-darwin.so",
    "name" : "_http_writer.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4352667648,
    "size" : 311296,
    "uuid" : "c158ab4a-805a-31d2-83d3-b39292030869",
    "path" : "\/Users\/USER\/Documents\/*\/_http_parser.cpython-313-darwin.so",
    "name" : "_http_parser.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4324446208,
    "size" : 24576,
    "uuid" : "177eb6a6-f1c6-36fb-842c-20f391254398",
    "path" : "\/Users\/USER\/Documents\/*\/mask.cpython-313-darwin.so",
    "name" : "mask.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4335144960,
    "size" : 135168,
    "uuid" : "09875ed8-1f3f-34be-a68e-325933cacab8",
    "path" : "\/Users\/USER\/Documents\/*\/reader_c.cpython-313-darwin.so",
    "name" : "reader_c.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4334944256,
    "size" : 61440,
    "uuid" : "74b8a47c-087a-3250-89eb-f30452d93c79",
    "path" : "\/Users\/USER\/Documents\/*\/_frozenlist.cpython-313-darwin.so",
    "name" : "_frozenlist.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4362248192,
    "size" : 675840,
    "uuid" : "0cffe7c0-cc84-3b97-8533-f5b50482e4f0",
    "path" : "\/Users\/USER\/Documents\/*\/_regex.cpython-313-darwin.so",
    "name" : "_regex.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4365897728,
    "size" : 2019328,
    "uuid" : "abceeb8a-b2f4-33c3-9139-e0f28b4bd46c",
    "path" : "\/Users\/USER\/Documents\/*\/_tiktoken.cpython-313-darwin.so",
    "name" : "_tiktoken.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4361773056,
    "size" : 221184,
    "uuid" : "b1ca786c-aba3-3163-9055-5ffa66273888",
    "path" : "\/Users\/USER\/Documents\/*\/_binding.cpython-313-darwin.so",
    "name" : "_binding.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4343152640,
    "size" : 77824,
    "uuid" : "5127405a-9319-35c0-bc94-ec726ecd09b4",
    "path" : "\/usr\/local\/Cellar\/python@3.13\/3.13.5\/Frameworks\/Python.framework\/Versions\/3.13\/lib\/python3.13\/lib-dynload\/_ctypes.cpython-313-darwin.so",
    "name" : "_ctypes.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4374691840,
    "size" : 5894144,
    "uuid" : "c9abf2f2-fa02-3a2c-b9d7-51d908aba0e4",
    "path" : "\/Users\/USER\/Documents\/*\/_binding.abi3.so",
    "name" : "_binding.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4318068736,
    "size" : 8192,
    "uuid" : "c2bf44b6-35a5-310e-9ac2-2f647ea7dff1",
    "path" : "\/Users\/USER\/Documents\/*\/_binding.abi3.so",
    "name" : "_binding.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4361474048,
    "size" : 192512,
    "uuid" : "f30765c3-0e77-364a-90ee-f5d170842bb7",
    "path" : "\/Users\/USER\/Documents\/*\/_binding.abi3.so",
    "name" : "_binding.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4368773120,
    "size" : 1343488,
    "uuid" : "8e854ff8-2f51-34d7-87d9-eead886e6f89",
    "path" : "\/Users\/USER\/Documents\/*\/_binding.abi3.so",
    "name" : "_binding.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4364664832,
    "size" : 573440,
    "uuid" : "8d726337-5b4f-301e-aca6-ccaa3bdd0670",
    "path" : "\/Users\/USER\/Documents\/*\/_binding.abi3.so",
    "name" : "_binding.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4380610560,
    "size" : 3395584,
    "uuid" : "9d6e55d4-97f8-3f49-8cb2-52cefa61723f",
    "path" : "\/Users\/USER\/Documents\/*\/_binding.abi3.so",
    "name" : "_binding.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4371156992,
    "size" : 1003520,
    "uuid" : "db39dac6-979e-349b-ace7-ec6d0f87e49f",
    "path" : "\/Users\/USER\/Documents\/*\/_binding.abi3.so",
    "name" : "_binding.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4387459072,
    "size" : 3403776,
    "uuid" : "5f49ff7a-f179-3ebd-bf7f-23b16c7a5c5a",
    "path" : "\/Users\/USER\/Documents\/*\/_binding.abi3.so",
    "name" : "_binding.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4364070912,
    "size" : 172032,
    "uuid" : "68ffd454-fef6-3788-b365-658c1c79cfad",
    "path" : "\/Users\/USER\/Documents\/*\/_binding.abi3.so",
    "name" : "_binding.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4372176896,
    "size" : 696320,
    "uuid" : "79c92d23-597b-3c6f-aab0-22b7452f9525",
    "path" : "\/Users\/USER\/Documents\/*\/_binding.abi3.so",
    "name" : "_binding.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4370137088,
    "size" : 454656,
    "uuid" : "a64ee39e-6de9-386f-be9a-13f5f4eb334c",
    "path" : "\/Users\/USER\/Documents\/*\/_binding.abi3.so",
    "name" : "_binding.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4365271040,
    "size" : 294912,
    "uuid" : "d7ee126d-e2a5-3f61-afa8-8a97becf0955",
    "path" : "\/Users\/USER\/Documents\/*\/_yaml.cpython-313-darwin.so",
    "name" : "_yaml.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4323880960,
    "size" : 12288,
    "uuid" : "9f97b064-c071-3f3a-afea-5b9f812c64a3",
    "path" : "\/Users\/USER\/Documents\/*\/_watchdog_fsevents.cpython-313-darwin.so",
    "name" : "_watchdog_fsevents.cpython-313-darwin.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4335046656,
    "size" : 32768,
    "uuid" : "59f1656e-2822-3adc-8cf2-9e956022d770",
    "path" : "\/Users\/USER\/Documents\/*\/_psutil_osx.abi3.so",
    "name" : "_psutil_osx.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4324532224,
    "size" : 16384,
    "uuid" : "a71ebbc9-266d-3611-89f7-e2f883d97063",
    "path" : "\/Users\/USER\/Documents\/*\/_psutil_posix.abi3.so",
    "name" : "_psutil_posix.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4370608128,
    "size" : 413696,
    "uuid" : "db69d0df-e2f6-3a39-bc90-143ef085412c",
    "path" : "\/Users\/USER\/Documents\/*\/java.abi3.so",
    "name" : "java.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4364251136,
    "size" : 364544,
    "uuid" : "5cf79c83-4aaa-3d3d-b7e8-148edbe068d6",
    "path" : "\/Users\/USER\/Documents\/*\/javascript.abi3.so",
    "name" : "javascript.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4385083392,
    "size" : 1417216,
    "uuid" : "e6bfbb23-cf2a-3636-b6e5-72a7a96d11a6",
    "path" : "\/Users\/USER\/Documents\/*\/typescript.abi3.so",
    "name" : "typescript.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4365647872,
    "size" : 212992,
    "uuid" : "f1f5a697-02fa-35b7-bd61-e5a8d6677353",
    "path" : "\/Users\/USER\/Documents\/*\/go.abi3.so",
    "name" : "go.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4393676800,
    "size" : 1327104,
    "uuid" : "87a02f44-c337-36c8-afcc-4d67f215178c",
    "path" : "\/Users\/USER\/Documents\/*\/bash.abi3.so",
    "name" : "bash.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4335345664,
    "size" : 176128,
    "uuid" : "c14cb07e-9930-3b4a-8e29-4778287e41d0",
    "path" : "\/Users\/USER\/Documents\/*\/matlab.abi3.so",
    "name" : "matlab.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4395024384,
    "size" : 1118208,
    "uuid" : "42ae6a08-1c43-3482-a76f-dc9a31fc8481",
    "path" : "\/Users\/USER\/Documents\/*\/rust.abi3.so",
    "name" : "rust.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 4324491264,
    "size" : 28672,
    "uuid" : "7c1fe611-6d7d-3576-862f-dcf18ce13763",
    "path" : "\/Users\/USER\/Documents\/*\/toml.abi3.so",
    "name" : "toml.abi3.so"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 140703266291712,
    "size" : 40936,
    "uuid" : "c55810b0-b8d2-3648-9009-570354c94d10",
    "path" : "\/usr\/lib\/system\/libsystem_platform.dylib",
    "name" : "libsystem_platform.dylib"
  },
  {
    "source" : "P",
    "arch" : "x86_64",
    "base" : 140703262326784,
    "size" : 572544,
    "uuid" : "f2913392-361a-304f-b30d-486be5639e2d",
    "path" : "\/usr\/lib\/dyld",
    "name" : "dyld"
  },
  {
    "size" : 0,
    "source" : "A",
    "base" : 0,
    "uuid" : "00000000-0000-0000-0000-000000000000"
  }
],
  "sharedCache" : {
  "base" : 140703261577216,
  "size" : 25769803776,
  "uuid" : "c831b32d-ac59-39e3-bf9c-2a9d43d3d5a3"
},
  "vmSummary" : "ReadOnly portion of Libraries: Total=504.2M resident=0K(0%) swapped_out_or_unallocated=504.2M(100%)\nWritable regions: Total=688.4M written=0K(0%) resident=0K(0%) swapped_out=0K(0%) unallocated=688.4M(100%)\n\n                                VIRTUAL   REGION \nREGION TYPE                        SIZE    COUNT (non-coalesced) \n===========                     =======  ======= \nKernel Alloc Once                    8K        1 \nMALLOC                           624.3M       71 \nMALLOC guard page                   16K        4 \nMALLOC_LARGE (reserved)           12.4M        2         reserved VM address space (unallocated)\nSTACK GUARD                          4K        1 \nStack                             16.0M        1 \nVM_ALLOCATE                       35.0M       36 \n__DATA                            6370K      352 \n__DATA_CONST                      22.5M      332 \n__DATA_DIRTY                       436K       92 \n__FONT_DATA                        2352        1 \n__LINKEDIT                       202.0M       77 \n__OBJC_RO                         76.9M        1 \n__OBJC_RW                         2375K        2 \n__TEXT                           302.2M      375 \n__TPRO_CONST                       272K        2 \ndyld private memory                160K        2 \nshared memory                       32K        4 \n===========                     =======  ======= \nTOTAL                              1.3G     1356 \nTOTAL, minus reserved VM space     1.3G     1356 \n",
  "legacyInfo" : {
  "threadTriggered" : {
    "queue" : "com.apple.main-thread"
  }
},
  "logWritingSignature" : "5b2ebba3ce8ecb77fa9c74848ea40b773a0ae2d7",
  "trialInfo" : {
  "rollouts" : [
    {
      "rolloutId" : "6761d0c9df60af01adb250fb",
      "factorPackIds" : {

      },
      "deploymentId" : 240000009
    },
    {
      "rolloutId" : "654439cdafbf5b61207873a9",
      "factorPackIds" : {

      },
      "deploymentId" : 240000004
    }
  ],
  "experiments" : [
    {
      "treatmentId" : "f18344bb-554f-48ae-8449-e108a8813a55",
      "experimentId" : "6685b5584477001000e8c6c9",
      "deploymentId" : 400000009
    }
  ]
}
}

Model: MacBookPro15,1, BootROM 2069.80.3.0.0 (iBridge: 22.16.13051.0.0,0), 6 processors, 6-Core Intel Core i7, 2.6 GHz, 16 GB, SMC 
Graphics: Intel UHD Graphics 630, Intel UHD Graphics 630, Built-In
Display: Color LCD, 2880 x 1800 Retina, Main, MirrorOff, Online
Graphics: Radeon Pro 560X, Radeon Pro 560X, PCIe, 4 GB
Memory Module: BANK 0/ChannelA-DIMM0, 8 GB, DDR4, 2400 MHz, Micron, 8ATF1G64HZ-2G6E1
Memory Module: BANK 2/ChannelB-DIMM0, 8 GB, DDR4, 2400 MHz, Micron, 8ATF1G64HZ-2G6E1
AirPort: spairport_wireless_card_type_wifi (0x14E4, 0x7BF), wl0: Jul 26 2024 22:09:35 version 9.30.514.0.32.5.94 FWID 01-47278712
AirPort: 
Bluetooth: Version (null), 0 services, 0 devices, 0 incoming serial ports
Network Service: Wi-Fi, AirPort, en0
USB Device: USB31Bus
USB Device: T2Bus
USB Device: Touch Bar Backlight
USB Device: Touch Bar Display
USB Device: Apple Internal Keyboard / Trackpad
USB Device: Headset
USB Device: Ambient Light Sensor
USB Device: FaceTime HD Camera (Built-in)
USB Device: Apple T2 Controller
Thunderbolt Bus: MacBook Pro, Apple Inc., 47.5
Thunderbolt Bus: MacBook Pro, Apple Inc., 47.5
```
