"""Local game console diagnostics, requires Deadlock -netconport 21245."""
import socket, sys, time
from build_pack import WORK, write
def command(text,seconds=1.0):
    chunks=[]
    with socket.create_connection(('127.0.0.1',21245),3) as s:
        s.settimeout(0.1)
        s.sendall((text+'\n').encode())
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            try:
                data=s.recv(65536)
                if not data: break
                chunks.append(data)
            except socket.timeout: pass
    return b''.join(chunks).decode('utf-8',errors='replace')
if __name__=='__main__':
    result=command(sys.argv[1],float(sys.argv[2]) if len(sys.argv)>2 else 1)
    write(WORK/'logs/console_last.txt',result)
    print(result)
