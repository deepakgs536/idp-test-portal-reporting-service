import json
from decimal import Decimal
import datetime

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 > 0:
                return float(obj)
            else:
                return int(obj)
        return super(DecimalEncoder, self).default(obj)

def get_current_time():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
