#!/usr/bin/env python
from threading import Timer
import time
import wiringpi
from samplebase import SampleBase
from PIL import Image, ImageDraw
import urllib
import urllib2

class TrashBin(SampleBase):
    def __init__(self, *args, **kwargs):
        super(TrashBin, self).__init__(*args, **kwargs)
        self.parser.add_argument("-i", "--image", help="The image to display", default="trashbin.png")
        self.url = "https://ygnbinhaustrashbin.herokuapp.com/in/"
        self.rep_url = "https://ygnbinhaustrashbin.herokuapp.com/rep/"
        self.clean_url = "https://ygnbinhaustrashbin.herokuapp.com/clean/"
        self.local_url = "http://192.168.43.223:8000/"
        self.device_id = "B001"
        wiringpi.pinMode(20, 0)
        wiringpi.pinMode(21, 0)
        print("init")

    def applyMask(self,img,rows,count):
        mask = img.copy()
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rectangle([(0,0),(img.size[0],img.size[1]-(img.size[1]/rows)*count)],fill=0)
        return mask

    def clearRep(self,limit):
        applyMask(self.image,limit,0)
        urllib2.urlopen(self.local_url+"clear")

    def run(self):
        print("run start")
        if not 'image' in self.__dict__:
            self.image = Image.open(self.args.image).convert('RGB')
        if self.image.size[0] != self.matrix.width and self.image.size[1] != self.matrix.height:
            self.image.resize((self.matrix.width, self.matrix.height), Image.ANTIALIAS)

        count = 0
        limit = 10

        double_buffer = self.matrix.CreateFrameCanvas()
        print("Created canvas")
        while True:
            print("Loop")
            print(wiringpi.digitalRead(20),wiringpi.digitalRead(21))
            if wiringpi.digitalRead(20):
                count = count + 1
                if count == limit:
                    double_buffer.SetImage(applyMask(self.image,limit,limit),0)
                else:
                    double_buffer.SetImage(applyMask(self.image,limit,count),0)
                double_buffer = self.matrix.SwapOnVSync(double_buffer)

                urllib2.urlopen(self.url+self.device_id)
                if count == limit:
                    urllib2.urlopen(self.local_url+"win")
                    urllib2.urlopen(self.rep_url+self.device_id)
                    self.count = 0
                    clear_timer = Timer(30.0, clearRep,[self,limit])
                    clear_timer.start()

            if wiringpi.digitalRead(21):
                urllib2.urlopen(self.clean_url+self.device_id)

            time.sleep(0.01)

if __name__ == "__main__":
    wiringpi.wiringPiSetupGpio()
    trash_bin = TrashBin()
    if (not trash_bin.process()):
        trash_bin.print_help()
