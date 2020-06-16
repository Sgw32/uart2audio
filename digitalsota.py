#---------------------------------------
# received uart data from audio in
#
# sgw32@yandex.ru
# aixi.wang@hotmail.com
#---------------------------------------

import pyaudio
import wave
import sys
import time
from datetime import datetime, date

THRESHOLD1 = 0 #65536*2/4
IDLE_TRESHOLD = 65536*1/4

header_detect_cnt1 = 0
header_detect_cnt2 = 0

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"

IDLE_DURATION = RATE/200

last_d = 0
bit_array = []
bit_state_machine_status = 0

last_j = None

# Filename to write
filename = "test.log"
tlmname = datetime.now().strftime("%Y.%m.%d-%H.%M") + ".dtl"

#-------------------------
# feature_energy
#-------------------------
def feature_energy(raw_data,n):
    e = 0
    i = 0;
    high_b = 0
    for i in range(0,n):
        d = ord(raw_data[i*2]) + ord(raw_data[i*2+1])*256
        if d >= 65536/2:
            d2 = d - 65536
        else:
            d2 = d
        #print 'n:',i,'d2:',d2
        e += d2*d2
    return e/n   

#---------------------
# bit_remove_balance
#---------------------  
def bit_remove_balance(arr):
    if len(arr) % 2 == 1:
        return arr[:-1]
    else:
        return arr
        
#-------------------------
# bitarray_to_str
#-------------------------
def bitarray_to_str(arr):
    global logfile
    global telemetryfile
    i = len(arr);

    if (i % 2) != 0:
        #print 'invalid bit received'
        return ''

    i = len(arr)
        
    s = ''
    #arr = range(0,i)
    
    #0b11001010
    
    man_array = []
    for j in range(0,i/2):
        man_array.append(arr[j*2])
    
    #print 'man_array :',len(man_array),',',man_array
    
    man_array = man_array[:-2]
    man_array = man_array[4:]
    
    #print 'man_array :',len(man_array),',',man_array
    
    i = len(man_array)/8
    arr = man_array
    #print i
    s = '' # raw string
    tlm = '' # telemetry string
    #0b11001010 xor
    #mind the endian!!!
    send_data_tlm = []
    
    for i in range(0,i):
        d = 128*(arr[i*8+7] ^ 1) + 64*(arr[i*8+6] ^ 1) + 32*(arr[i*8+5] ^ 0)+ 16*(arr[i*8+4] ^ 0)
        d += 8*(arr[i*8+3] ^ 1)+ 4*(arr[i*8+2] ^ 0)+ 2*(arr[i*8+1] ^ 1)+ 1*(arr[i*8+0] ^ 0)
        #print d
        send_data_tlm.append(d)
        s += chr(d)
    
    if (send_data_tlm[0]==0xAA):
        temp1 = (send_data_tlm[1]<<8) | send_data_tlm[2]
        temp2 = (send_data_tlm[3]<<8) | send_data_tlm[4]
        if (temp1&0x8000):
            temp1= -0x10000+temp1
        if (temp2&0x8000):
            temp2= -0x10000+temp2
        
        if (temp1/100>-100)and(temp1/100<40):
            if (temp2/100>-100)and(temp2/100<40):
                telemetryfile = open(tlmname, 'a')
                s_t = datetime.now().isoformat() + '\t' + str(float(temp1)/100.0) + '\t' + str(float(temp2)/100.0) 
                telemetryfile.write(s_t + '\r\n')
                print 'OK ' , s_t
                telemetryfile.close()
                
    if ((len(s)>15) and (len(s)<27)):
        if (send_data_tlm[0]==0xAA):
            #print 'OK ' , len(s), send_data_tlm[0]
            logfile = open(filename, 'a')
            logfile.write(s+'\r\n')
            logfile.close()

        #logfile.write('test' + '\r\n')
    #for i in range(0,i):
    #    d = 128*arr[i*8] + 64*arr[i*8+1] + 32*arr[i*8+2] + 16*arr[i*8+3]
    #    d += 8*arr[i*8+4] + 4*arr[i*8+5] + 2*arr[i*8+6] + 1*arr[i*8+7]
    #    s += chr(d)
    
    return s

#-------------------------
# validate_and_retrieve_raw
#-------------------------    
def validate_and_retrieve_raw(s):
    retcode = 0
    if len(s) < 4:
        return -1, ''
    
    if s[0] != '\x55':
        return -2, ''
    
    if ord(s[1]) != len(s)-3:
        return -3, ''
        
    checksum = 0
    for i in range(2,len(s)-1):
        #print 'i:',i
        checksum += ord(s[i])
    checksum %= 256
    
    if ord(s[-1]) != checksum:
        return -4,''
    
    return 0, s[2:-1]
#-------------------------
# decode_uart_data
#-------------------------    
def process_data():
    global header_detect_cnt1
    global header_detect_cnt2
    
    global last_d
    global bit_state_machine_status
    global bit_array
    
    global last_state
    global last_j

    if len(bit_array) > 0:
        #print 'bit_array :',len(bit_array),',',bit_array
        bit_array2 = bit_remove_balance(bit_array)
        #print 'bit_array2:',len(bit_array2),',',bit_array2
        s2 = bitarray_to_str(bit_array2)
        #retcode, s3 = validate_and_retrieve_raw(s2)
        #if retcode == 0:
        #    print'received str(hex):',s3.encode('hex')
        #    print'received str:',s3
        #    
        #else:
            #print'received str(hex):',s2.encode('hex')
            #print'received str:',s2
        
        #    print 'retcode:',retcode,', package integration checking fail'
            
        bit_array = []    
#-------------------------
# decode_uart_data
#-------------------------
def decode_uart_data(raw_data,n):
    global header_detect_cnt1
    global header_detect_cnt2
    
    global last_d
    global bit_state_machine_status
    global bit_array
    
    global last_state
    global last_j
    
    global time_one
    global time_zero
    global time_idle
    global chunk
    global was_idle
    e = 0
    i = 0;
    high_b = 0
    
    for i in range(0,n):
        d = ord(raw_data[i*2]) + ord(raw_data[i*2+1])*256
        
        if d >= 65536/2:
            d2 = d - 65535
        else:
            d2 = d

        d2 = -d2
        # __-- 0
        # --__ 1
        
        #if (was_idle):
        #    print d2

        #print d2
        
        if d2 >= THRESHOLD1: # -------
            error = 0
            #process transition
            if (last_state==0)and(was_idle):
                #Manchester
                if (time_zero>14)and(time_zero<20):
                    chunk = chunk + '0'
                    bit_array.append(0)
                if (time_zero>20)and(time_zero<40):
                    chunk = chunk + '00'
                    bit_array.append(0)
                    bit_array.append(0)
            time_idle = time_idle + 1
            if (time_idle > IDLE_DURATION)and(last_state<2):
                #print ' -- idle -- '
                #print str(bit_array)
                process_data()
                bit_array = []
                chunk = ''
                last_state = 2 # state idle
                was_idle = 1
                time_one = 0
                time_idle = 0
            if (last_state < 2):
                last_state = 1
            time_zero = 0
            time_one = time_one + 1
        else:                # ________
            if (last_state==1)and(was_idle):
                #Manchester
                if (time_one>14)and(time_one<20):
                    chunk = chunk + '1'
                    bit_array.append(1)
                if (time_one>20)and(time_one<40):
                    chunk = chunk + '11'
                    bit_array.append(1)
                    bit_array.append(1)
            time_idle = 0
            time_one = 0
            last_state = 0
            time_zero = time_zero + 1
    

#------------------------------------------
# main
#------------------------------------------
global time_one #one time counter
global time_zero #zero time counter
global time_idle #idle time counter
global chunk # data chunk
global was_idle #was idle mode EVER since start
global last_state
global logfile
global telemetryfile

time_one = 0
time_zero = 0
time_idle = 0
last_state = 0
was_idle = 0

chunk = ''

# Open the file with writing permission
logfile = open(filename, 'w')
logfile.write('DIGITAL SOTA v1.0\n')
logfile.close()

# Open the file with writing permission
telemetryfile = open(tlmname, 'w')
telemetryfile.write('DIGITAL SOTA TELEMETRY LOG v1.0\n')
telemetryfile.close()

#if len(sys.argv) < 2:
#    print("Plays a wave file.\n\nUsage: %s filename.wav" % sys.argv[0])
#    sys.exit(-1)

#wf = wave.open(sys.argv[1], 'rb')

p = pyaudio.PyAudio()

stream = p.open(format = FORMAT,
                channels = CHANNELS,
                rate = RATE,
                input = True,
                output = False,
                input_device_index = 1,                
                frames_per_buffer = CHUNK)

print "listing..."

while True:
    try:
        data = stream.read(CHUNK)
        #print 'data:', str(d),'\r\n'
        decode_uart_data(data,CHUNK)
    except Exception as e:       
        print 'audio exception, retry', str(e)
        time.sleep(1)

sys.exit(-1)

stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True)

FORMAT = p.get_format_from_width(wf.getsampwidth());
RATE = wf.getframerate();

print "listing..."

data = wf.readframes(CHUNK)

while data != '':
    try:
        stream.write(data)
        data = wf.readframes(CHUNK)
        
        #d = feature_energy(data,CHUNK)
        #print 'data:', str(d),'\r\n'
        decode_uart_data(data,CHUNK)
    except Exception as e:       
        print 'audio exception, retry', str(e)
        time.sleep(1)

stream.stop_stream()
stream.close()
#logfile.close()

p.terminate()



