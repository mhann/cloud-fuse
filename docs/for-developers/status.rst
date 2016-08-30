Project Status
==============

=====================  ===========
Feature                 Working
=====================  ===========
Basic operations
----------------------------------
List directory           ✓
Read                     ✓ [#]_
Write                    ✓ [#]_
Rename                   ❌
Move                     ❌
Trashing                 ❌
OS-level trashing        ❌ 
View trash               ❌
Create Directory         ❌
Multi Level Tree         ❌
Misc
----------------------------------
ctime/mtime update       ❌
Custom permissions       ❌
Hard links               ❌
Symbolic links           ❌ [#]_
=====================  ===========

.. [#] partial writes are supported (from random offsets)
.. [#] partial reads are supported (from random offsets) and will only download needed blocks

