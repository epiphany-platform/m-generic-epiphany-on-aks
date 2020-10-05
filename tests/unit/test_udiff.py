from azepi._helpers import udiff


INPUT1 = '''
# comment1
key0:
  - name: key1  # comment2
    must-be-true: True
  # comment3
  - name: key2
    # comment4
    must-be-false: false
must-be-string: yes
must-be-literal: |
  1
  2
  3
'''

INPUT2 = '''
key0:
  - name: key1
    must-be-true: true
  - name: key2
    must-be-false: false
must-be-string: yes
must-be-literal: |
  1
  2
  3
'''

OUTPUT = '''
@@ -2 +1,0 @@
-# comment1
@@ -4,3 +3,2 @@
-  - name: key1  # comment2
-    must-be-true: True
-  # comment3
+  - name: key1
+    must-be-true: true
@@ -8 +5,0 @@
-    # comment4
'''


def test_udiff():
    assert udiff(INPUT1, INPUT2).strip() == OUTPUT.strip()
