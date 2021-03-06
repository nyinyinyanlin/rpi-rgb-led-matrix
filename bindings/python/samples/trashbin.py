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
        self.kiosk_url = "http://kioskpi:8000/"
        self.device_id = "B001"
        wiringpi.pinMode(16, 0)
        wiringpi.pinMode(21, 0)
        self.insertPinState = False
        self.cleanPinState = False

    def applyMask(self,img,rows,count):
        mask = img.copy()
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rectangle([(0,0),(img.size[0],img.size[1]-(img.size[1]/rows)*count)],fill=0)
        return mask

    def clearRep(self,limit,db):
        db.SetImage(self.applyMask(self.image,limit,0),0)
        db = self.matrix.SwapOnVSync(db)
        urllib2.urlopen(self.kiosk_url+"clear")

    def run(self):
        if not 'image' in self.__dict__:
            self.image = Image.open(self.args.image).convert('RGB')
        if self.image.size[0] != self.matrix.width and self.image.size[1] != self.matrix.height:
            self.image.resize((self.matrix.width, self.matrix.height), Image.ANTIALIAS)

        count = 0
        limit = 10

        double_buffer = self.matrix.CreateFrameCanvas()
        double_buffer.SetImage(self.image,0)
        double_buffer = self.matrix.SwapOnVSync(double_buffer)
        time.sleep(5)
        double_buffer.SetImage(self.applyMask(self.image,limit,0),0)
        double_buffer = self.matrix.SwapOnVSync(double_buffer)

        while True:
            if wiringpi.digitalRead(16) and not self.insertPinState:
                self.insertPinState = True
                count = count + 1
                if count == limit:
                    double_buffer.SetImage(self.applyMask(self.image,limit,limit),0)
                else:
                    double_buffer.SetImage(self.applyMask(self.image,limit,count),0)
                double_buffer = self.matrix.SwapOnVSync(double_buffer)


                urllib2.urlopen(self.kiosk_url+"sound")
                urllib2.urlopen(self.url+self.device_id)
                if count == limit:
                    urllib2.urlopen(self.kiosk_url+"win")
                    urllib2.urlopen(self.rep_url+self.device_id)
                    count = 0
                    clear_timer = Timer(30.0, self.clearRep,[limit,double_buffer])
                    clear_timer.start()
            elif not wiringpi.digitalRead(16) and self.insertPinState:
                self.insertPinState = False

            if wiringpi.digitalRead(21) and not self.cleanPinState:
                self.cleanPinState = True
                urllib2.urlopen(self.clean_url+self.device_id)
            elif not wiringpi.digitalRead(21) and self.cleanPinState:
                self.cleanPinState = False

if __name__ == "__main__":
    wiringpi.wiringPiSetupGpio()
    trash_bin = TrashBin()
    if (not trash_bin.process()):
        trash_bin.print_help()
