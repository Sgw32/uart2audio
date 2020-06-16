# -*- coding: utf-8 -*-
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
  dev = p.get_device_info_by_index(i)
  print i,dev['name'].encode('utf-8'),dev['maxInputChannels']