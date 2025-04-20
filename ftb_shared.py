import gc
import re
import sys
from datetime import datetime

def remove_suffix(s: str, suffix: str) -> str:
    if s.endswith(suffix):
        return s[: -len(suffix)]
    return s

def isEmptyOrWhitespace(s) -> bool:
    return not s or s.strip() == ""

def getValFromMap(data_map, search_key, indx):
    for tupl in data_map:
        if tupl[0] == search_key:
            return tupl[indx]
    return None

def forLog(data):
    try:
        data = toIter(data)
        return data[0].hintKey()
    except:
        return "null"

def clsName(obj) -> str:
    return type(obj).__name__.lower()

def clearNones(arr):
    return [el for el in arr if el is not None]

def createCleanList(arr, func, *funcargs):
    """Create list from array without duplicates and Nones"""
    res = []
    for obj in arr:
        new = func(obj, *funcargs)
        if new and not (new in res):
            res.append(new)
    
    return res

def toArr(s):
    if not isinstance(s, (list, tuple)):
        return [s]
    return s

def getFromListByKey(arr, key, default=-1, returnIndex=0, findIndex=0, returnAll=False):
    for el in arr:
        if el[findIndex] == key:
            if returnAll:
                return el
            return el[returnIndex]

    return default

def classSortVal(clsname):
    values = {
        "person": 0,
        "family": 1,
        "event": 2,
        "media": 3
    }
    return values.get(clsname, ord(clsname[0]))

def sortObjectsHandles(objs):
    order = ["person", "family", "event", "media"]
    priority = {name: i for i, name in enumerate(order)}

    return sorted(objs, key=lambda obj: priority.get(obj.__class__.__name__, ord(obj.__class__.__name__[0])))

def toIter(v, cls=tuple):
    if isinstance(v, cls):
        return v
    else: 
        return cls((v, ))

def ifIter(v):
    if isinstance(v, (tuple, list, dict)):
        if v: return v[0]
    else: 
        return v

def tolwr(s):
    if isinstance(s, str):
        return s.lower()
    else: return s

def foo(*args, **kwargs): pass

def getGetter(c):
    custom = {}
    return custom.get(c, "g" + c[1:])

def setObjectAttributes(obj, **kwargs):
    changed = False
    for key, val in kwargs.items():
        if key and val:
            oldVal = getattr(obj, getGetter(key), foo)()
            if oldVal != val:
                changed = True
                getattr(obj, key, foo)(val)

    return changed

def tryGetHandle(obj):
    try: return obj.get_handle()
    except: return None

def tryGetGrampsID(obj):
    try: return obj.get_gramps_id()
    except: return None

def format_timestamp(ts):
    if ts > 10**10:  
        ts /= 1000  
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

def get_obj_size(obj):
    marked = {id(obj)}
    obj_q = [obj]
    sz = 0

    while obj_q:
        sz += sum(map(sys.getsizeof, obj_q))

        # Lookup all the object referred to by the object in obj_q.
        # See: https://docs.python.org/3.7/library/gc.html#gc.get_referents
        all_refr = ((id(o), o) for o in gc.get_referents(*obj_q))

        # Filter object that are already marked.
        # Using dict notation will prevent repeated objects.
        new_refr = {o_id: o for o_id, o in all_refr if o_id not in marked and not isinstance(o, type)}

        # The new obj_q will be the ones that were not marked,
        # and we will update marked with their ids so we will
        # not traverse them again.
        obj_q = new_refr.values()
        marked.update(new_refr.keys())

    return sz

def splitSQLargs(s):
    pattern = r'\s+|!=|=|AND|OR|&'
    return [token for token in re.split(pattern, s) if token]
