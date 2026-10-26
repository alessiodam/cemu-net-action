import fcntl
import os
import select
import socket
import struct
import sys
import time

tap, me, gw, target = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
mac = bytes.fromhex("0284ce000001")
fd = os.open("/dev/net/tun", os.O_RDWR)
fcntl.ioctl(fd, 0x400454CA, struct.pack("16sH", tap.encode(), 0x0002 | 0x1000))


def checksum(data):
    if len(data) % 2:
        data += b"\0"
    s = sum(struct.unpack(f"!{len(data) // 2}H", data))
    while s >> 16:
        s = (s & 0xFFFF) + (s >> 16)
    return ~s & 0xFFFF


def receive(match, timeout=5):
    end = time.time() + timeout
    while time.time() < end:
        if select.select([fd], [], [], end - time.time())[0]:
            frame = os.read(fd, 2048)
            result = match(frame)
            if result:
                return result
    sys.exit(f"timed out waiting on {tap}")


arp = b"\xff" * 6 + mac + b"\x08\x06" + struct.pack("!HHBBH", 1, 0x0800, 6, 4, 1)
arp += mac + socket.inet_aton(me) + b"\0" * 6 + socket.inet_aton(gw)
os.write(fd, arp)
gw_mac = receive(lambda f: f[12:14] == b"\x08\x06" and f[20:22] == b"\x00\x02" and f[28:32] == socket.inet_aton(gw) and f[22:28])
print(f"gateway {gw} is {gw_mac.hex(':')}")

tcp = struct.pack("!HHIIBBHHH", 40000, 443, 1, 0, 5 << 4, 0x02, 64240, 0, 0)
pseudo = socket.inet_aton(me) + socket.inet_aton(target) + struct.pack("!BBH", 0, 6, len(tcp))
tcp = tcp[:16] + struct.pack("!H", checksum(pseudo + tcp)) + tcp[18:]
ip = struct.pack("!BBHHHBBH4s4s", 0x45, 0, 20 + len(tcp), 1, 0, 64, 6, 0, socket.inet_aton(me), socket.inet_aton(target))
ip = ip[:10] + struct.pack("!H", checksum(ip)) + ip[12:]
os.write(fd, gw_mac + mac + b"\x08\x00" + ip + tcp)
receive(lambda f: f[12:14] == b"\x08\x00" and f[23] == 6 and f[26:30] == socket.inet_aton(target) and f[47] & 0x12 == 0x12)
print(f"tcp {target}:443 through NAT ok")
