import filesystem

# Remove the first character ('/') from path.
#
# @FIXME: Should check that the first character is actually / so that if it is called twice on the same string it does not take two characters off the front.
def preparePath(path):
        return path[1:]
