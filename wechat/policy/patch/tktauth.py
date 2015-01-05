from socket import inet_aton
from struct import pack
import hashlib
import hmac
import time

def createTicket(secret, userid, tokens=(), user_data='', ip='0.0.0.0', timestamp=None, encoding='utf-8', mod_auth_tkt=True):
    """
    By default, use a more compatible
    """
    if timestamp is None:
        timestamp = int(time.time())
    if encoding is not None:
        userid = userid.encode(encoding)
        tokens = [t.encode(encoding) for t in tokens]
        user_data = user_data.encode(encoding)

    token_list = ','.join(tokens)

    # ip address is part of the format, set it to 0.0.0.0 to be ignored.
    # inet_aton packs the ip address into a 4 bytes in network byte order.
    # pack is used to convert timestamp from an unsigned integer to 4 bytes
    # in network byte order.
    # Unfortunately, some older versions of Python assume that longs are always
    # 32 bits, so we need to trucate the result in case we are on a 64-bit
    # naive system.
    data1 = inet_aton(ip)[:4] + pack("!I", timestamp)
    data2 = '\0'.join((userid, token_list, user_data))
#    if isinstance(data2, unicode) and isinstance(data1, basestring):data2 = data2.encode('utf-8')
    if mod_auth_tkt:
        digest = mod_auth_tkt_digest(secret, data1, data2)
    else:
        # a sha256 digest is the same length as an md5 hexdigest
        
        digest = hmac.new(secret, data1+data2, hashlib.sha256).digest()

    # digest + timestamp as an eight character hexadecimal + userid + !
    ticket = "%s%08x%s!" % (digest, timestamp, userid)
    if tokens:
        ticket += token_list + '!'
    ticket += user_data

    return ticket