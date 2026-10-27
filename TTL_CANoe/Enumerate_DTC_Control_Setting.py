import time
import can
from ASC_Logger import ASCLogger

CAN_INTERFACE="vector"; CAN_CHANNEL=0; CAN_APP_NAME="Python"
CAN_BITRATE=500000; CAN_DATA_BITRATE=2000000; EXTENDED_ID=False
SCAN_START=0x00; SCAN_END=0x7F
SESSIONS={0x01:"Default",0x02:"Programming",0x03:"Extended",0x04:"Safety"}
ALL_SESSIONS=[0x01,0x02,0x03]
NRC_NAMES={0x10:"General Reject",0x11:"Service Not Supported",0x12:"Sub-function Not Supported",0x13:"Incorrect Length/Format",0x21:"Busy Repeat Request",0x22:"Conditions Not Correct",0x24:"Request Sequence Error",0x31:"Request Out Of Range",0x33:"Security Access Denied",0x78:"Response Pending",0x7E:"Sub-function Not Supported In Session",0x7F:"Service Not Supported In Session"}
SUPPORTED_NRCS={0x33}
bus=None; TX_ID=RX_ID=None; RESPONSE_TIMEOUT=0.5; REQUEST_INTERVAL=0.01; TX_FD=False


def hex_input(text,default,maximum=0x1FFFFFFF):
    while True:
        try:
            raw=input(f"{text} (default 0x{default:X}): ").strip()
            value=default if not raw else int(raw,16)
            if not 0<=value<=maximum: raise ValueError
            return value
        except ValueError: print("[!] Invalid hexadecimal value.")


def float_input(text,default,zero=False):
    while True:
        try:
            raw=input(f"{text} (default {default} s): ").strip()
            value=default if not raw else float(raw)
            if value<0 or (value==0 and not zero): raise ValueError
            return value
        except ValueError: print("[!] Invalid time value.")


def yes_no(text,default=False):
    while True:
        raw=input(f"{text} (Y/N, default {'Y' if default else 'N'}): ").strip().upper()
        if not raw:return default
        if raw in ('Y','YES'):return True
        if raw in ('N','NO'):return False


def session_input():
    print("\n01 Default | 02 Programming | 03 Extended | 04 Safety")
    print("ALL = all configured sessions | NONE = current session")
    while True:
        raw=input("Select session: ").strip()
        if raw.upper()=="ALL": return "ALL",ALL_SESSIONS.copy()
        if raw.upper()=="NONE": return "NONE",[None]
        try:
            value=int(raw,16)
            if not 0<=value<=0x7F:raise ValueError
            return "SINGLE",[value]
        except ValueError:print("[!] Enter one session, ALL, or NONE.")


def open_bus():
    return can.Bus(interface=CAN_INTERFACE,channel=CAN_CHANNEL,app_name=CAN_APP_NAME,fd=True,bitrate=CAN_BITRATE,dbitrate=CAN_DATA_BITRATE,receive_own_messages=True)


def pad(data,n):return list(data)+[0]*(n-len(data))


def sf(payload):
    if not TX_FD:
        if len(payload)>7:raise ValueError("Classic CAN SF too long")
        return pad([len(payload)]+payload,8)
    raw=[len(payload)]+payload if len(payload)<=7 else [0,len(payload)]+payload
    for n in (8,12,16,20,24,32,48,64):
        if len(raw)<=n:return pad(raw,n)
    raise ValueError("CAN FD SF too long")


def log_tx(msg,logger):
    if not getattr(msg,'timestamp',None):msg.timestamp=time.time()
    logger.log_frame(msg,"Tx")


def send(payload,logger,fd=None):
    use_fd=TX_FD if fd is None else fd
    old=globals()['TX_FD']; globals()['TX_FD']=use_fd
    data=sf(payload); globals()['TX_FD']=old
    msg=can.Message(arbitration_id=TX_ID,is_extended_id=EXTENDED_ID,is_fd=use_fd,bitrate_switch=use_fd,data=data)
    bus.send(msg)
    pass


def drain():
    while bus.recv(timeout=.001) is not None:pass


def parse(msg):
    d=bytes(msg.data)
    if not d:return None
    t=d[0]>>4
    if t==0:
        length=d[0]&15;off=1
        if length==0:
            if len(d)<2:return None
            length=d[1];off=2
        return ('SF',d[off:off+length]) if length<=len(d)-off else None
    if t==1:
        length=((d[0]&15)<<8)|d[1];off=2
        if length==0:
            if len(d)<6:return None
            length=int.from_bytes(d[2:6],'big');off=6
        return ('FF',length,d[off:])
    if t==2:return ('CF',d[0]&15,d[1:])
    return None


def receive_payload(logger):
    deadline=time.monotonic()+RESPONSE_TIMEOUT;buf=bytearray();total=None;sn=1;transport=None
    while time.monotonic()<deadline:
        msg=bus.recv(timeout=min(.01,max(0,deadline-time.monotonic())))
        if msg is None:continue
        logger.log_frame(msg,"Rx")
        if msg.arbitration_id!=RX_ID:continue
        frame=parse(msg)
        if not frame:continue
        if frame[0]=='SF':return {'status':'complete','payload':frame[1],'transport':'CAN FD SF' if msg.is_fd else 'CAN SF'}
        if frame[0]=='FF':
            total=frame[1];buf=bytearray(frame[2]);sn=1;transport='CAN FD ISO-TP' if msg.is_fd else 'CAN ISO-TP'
            fc=can.Message(arbitration_id=TX_ID,is_extended_id=EXTENDED_ID,is_fd=msg.is_fd,bitrate_switch=msg.bitrate_switch if msg.is_fd else False,data=pad([0x30,0,0],8))
            bus.send(fc)
            pass
            deadline=time.monotonic()+RESPONSE_TIMEOUT

        elif frame[0]=='CF' and total is not None:
            if frame[1]!=sn:return {'status':'sequence_error','payload':None,'transport':transport}
            buf.extend(frame[2]);sn=(sn+1)&15;deadline=time.monotonic()+RESPONSE_TIMEOUT
        if total is not None and len(buf)>=total:return {'status':'complete','payload':bytes(buf[:total]),'transport':transport}
    return {'status':'timeout','payload':None,'transport':transport}


def final_response(sid,logger):
    while True:
        result=receive_payload(logger)
        if result['status']!='complete':return result
        p=result['payload']
        if p and p[0]==sid+0x40:return {'status':'positive','payload':p,'transport':result['transport']}
        if len(p)>=3 and p[0]==0x7F and p[1]==sid:
            if p[2]==0x78:
                print("    [*] NRC 0x78. Waiting for final response...");continue
            return {'status':'negative','payload':p,'nrc':p[2],'transport':result['transport']}


def enter_session(session,logger):
    drain();send([0x10,session],logger);r=final_response(0x10,logger)
    ok=r['status']=='positive' and len(r['payload'])>=2 and (r['payload'][1]&0x7F)==session
    if ok:time.sleep(.5)
    return {'entered':ok,'nrc':r.get('nrc')}


def prepare_session(session,logger):
    if session is None:return {'entered':True,'nrc':None}
    if session!=1:
        r=enter_session(1,logger)
        if not r['entered']:return r
        time.sleep(.5)
    return enter_session(session,logger)


def test_subfunction(subfunction,logger):
    drain();send([0x85,subfunction],logger);r=final_response(0x85,logger)
    if r['status']=='positive':
        p=r['payload'];ok=len(p)>=2 and p[0]==0xC5 and (p[1]&0x7F)==subfunction
        return {'supported':ok,'nrc':None,'kind':'Positive' if ok else 'Mismatch','transport':r.get('transport')}
    if r['status']=='negative':
        nrc=r['nrc'];return {'supported':nrc in SUPPORTED_NRCS,'nrc':nrc,'kind':'Recognised NRC' if nrc in SUPPORTED_NRCS else 'Negative','transport':r.get('transport')}
    return {'supported':False,'nrc':None,'kind':r['status'],'transport':r.get('transport')}


def empty_stats():return {'processed':0,'supported':0,'unsupported':0,'timeout':0,'nrc_11':0,'nrc_12':0,'nrc_13':0,'nrc_22':0,'nrc_31':0,'nrc_33':0,'nrc_7e':0,'nrc_7f':0,'other_nrc':0,'transport_error':0}


def count_nrc(stats,nrc):
    key={0x11:'nrc_11',0x12:'nrc_12',0x13:'nrc_13',0x22:'nrc_22',0x31:'nrc_31',0x33:'nrc_33',0x7E:'nrc_7e',0x7F:'nrc_7f'}.get(nrc)
    if key:stats[key]+=1
    elif nrc is not None:stats['other_nrc']+=1


def scan(logger):
    found=[];stats=empty_stats();total=SCAN_END-SCAN_START+1
    for sub in range(SCAN_START,SCAN_END+1):
        r=test_subfunction(sub,logger);stats['processed']+=1;count_nrc(stats,r.get('nrc'))
        if r['supported']:
            stats['supported']+=1;found.append({'subfunction':sub,'nrc':r.get('nrc'),'kind':r['kind']})
            print(f"\n[+] Supported subfunction 0x{sub:02X} | {r['kind']}")
        else:
            stats['unsupported']+=1
            if r.get('nrc') is None:
                if r['kind']=='timeout':stats['timeout']+=1
                else:stats['transport_error']+=1
        print(f"\rProcessed {stats['processed']:3}/{total} | Current 0x{sub:02X} | Supported {stats['supported']}",end='',flush=True)
        if sub<SCAN_END:time.sleep(REQUEST_INTERVAL)
    print();return {'found':found,'stats':stats}


def show(session,result):
    s=result['stats'];title='Current Active Session' if session is None else f"Session 0x{session:02X} ({SESSIONS.get(session,'OEM')})";line='='*90
    print('\n'+line);print('DTC CONTROL SETTING (0x85) ENUMERATION SUMMARY'.center(90));print(title.center(90));print(line)
    print(f"Total Subfunction Requests Processed : {s['processed']}")
    print(f"Total Unsupported Subfunctions       : {s['unsupported']}")
    print(f"Total Supported Subfunctions         : {s['supported']}")
    print(f"Total No Responses                   : {s['timeout']}")
    for code,key in [(0x11,'nrc_11'),(0x12,'nrc_12'),(0x13,'nrc_13'),(0x22,'nrc_22'),(0x31,'nrc_31'),(0x33,'nrc_33'),(0x7E,'nrc_7e'),(0x7F,'nrc_7f')]:print(f"Total NRC 0x{code:02X} Responses              : {s[key]}")
    print(f"Total Other NRC Responses          : {s['other_nrc']}");print(f"Total Transport Errors             : {s['transport_error']}");print(line)
    print('Enumerated DTC Control Setting Subfunctions:')
    vals=[x['subfunction'] for x in result['found']];cols=10;w=7;bar='+'+'+'.join('-'*w for _ in range(cols))+'+'
    if not vals:print('None');return
    for i in range(0,len(vals),cols):
        row=vals[i:i+cols];print(bar);cells=[f"{x:02X}".center(w) for x in row]+[' '*w]*(cols-len(row));print('|'+'|'.join(cells)+'|')
    print(bar)


def log_name(session):return 'DTC_Control_Setting_Current' if session is None else f"DTC_Control_Setting_Session_{session:02X}_{SESSIONS.get(session,'OEM')}".replace(' ','_')


def scan_session(session):
    logger=ASCLogger();started=False;ready=False;result={'found':[],'stats':empty_stats()}
    try:
        logger.start_log(log_name(session),filters=[TX_ID,RX_ID]);started=True
        ready=prepare_session(session,logger)
        if not ready['entered']:
            print(f"[!] Session entry failed. NRC={ready.get('nrc')}");return result
        result=scan(logger);show(session,result);return result
    finally:
        if started:
            if session is not None and ready and ready.get('entered') and bus is not None:
                try:enter_session(1,logger)
                except Exception as e:print(f"[!] Default-session cleanup failed: {e}")
            logger.stop_log();print(f"[+] ASC log closed: {log_name(session)}")


def main():
    global bus,TX_ID,RX_ID,RESPONSE_TIMEOUT,REQUEST_INTERVAL,TX_FD
    print('\n'+'='*70);print('DTC Control Setting Enumeration Tool'.center(70));print('='*70)
    print('[!] Positive 85 xx requests may change DTC recording state. Use only on an authorised bench.')
    TX_ID=hex_input('Enter TX CAN ID',0x471);RX_ID=hex_input('Enter RX CAN ID',0x479)
    RESPONSE_TIMEOUT=float_input('Enter maximum response timeout',.5)
    REQUEST_INTERVAL=float_input('Enter time between consecutive requests',.01,True)
    TX_FD=yes_no('Transmit diagnostic requests as CAN FD',False)
    mode,sessions=session_input();all_results={}
    try:
        bus=open_bus();print('[+] Vector CAN interface opened.')
        for session in sessions:all_results['CURRENT' if session is None else f"0x{session:02X}"]={'session':session,'result':scan_session(session)}
    except KeyboardInterrupt:print('\n[!] Enumeration stopped by user.')
    except can.CanError as e:print(f"\n[!] CAN error: {e}")
    except Exception as e:print(f"\n[!] Unexpected error: {e}")
    finally:
        if bus is not None:
            try:bus.shutdown();print('[+] Vector CAN interface shut down.')
            except Exception as e:print(f"[!] Bus shutdown error: {e}")
            bus=None
    print('\n'+'='*90);print('DTC CONTROL SETTING ENUMERATION COMPLETED'.center(90));print('='*90)
    for item in all_results.values():show(item['session'],item['result'])


if __name__=='__main__':main()
