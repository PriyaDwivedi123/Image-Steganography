
import cv2
import docopt
import numpy as np
from functools import partial
from tkinter.filedialog import askopenfilename
from tkinter import *
root=Tk()

v=IntVar()

class SteganographyException(Exception):
    pass


class LSBSteg():
    def __init__(self, im):
        self.image = im
        self.height, self.width, self.nbchannels = im.shape
        self.size = self.width * self.height
        
        self.maskONEValues = [1,2,4,8,16,32,64,128]
        self.maskONE = self.maskONEValues.pop(0) 
        
        self.maskZEROValues = [254,253,251,247,239,223,191,127]
        self.maskZERO = self.maskZEROValues.pop(0)
        
        self.curwidth = 0  
        self.curheight = 0 
        self.curchan = 0   

    def put_binary_value(self, bits): 
        for c in bits:
            val = list(self.image[self.curheight,self.curwidth]) 
            if int(c) == 1:
                val[self.curchan] = int(val[self.curchan]) | self.maskONE 
            else:
                val[self.curchan] = int(val[self.curchan]) & self.maskZERO 
                
            self.image[self.curheight,self.curwidth] = tuple(val)
            self.next_slot() 
        
    def next_slot(self):
        if self.curchan == self.nbchannels-1: 
            self.curchan = 0
            if self.curwidth == self.width-1: 
                self.curwidth = 0
                if self.curheight == self.height-1:
                    self.curheight = 0
                    if self.maskONE == 128: 
                        raise SteganographyException("No available slot remaining (image filled)")
                    else: 
                        self.maskONE = self.maskONEValues.pop(0)
                        self.maskZERO = self.maskZEROValues.pop(0)
                else:
                    self.curheight +=1
            else:
                self.curwidth +=1
        else:
            self.curchan +=1

    def read_bit(self): 
        val = self.image[self.curheight,self.curwidth][self.curchan]
        val = int(val) & self.maskONE
        self.next_slot()
        if val > 0:
            return "1"
        else:
            return "0"
    
    def read_byte(self):
        return self.read_bits(8)
    
    def read_bits(self, nb): 
        bits = ""
        for i in range(nb):
            bits += self.read_bit()
        return bits

    def byteValue(self, val):
        return self.binary_value(val, 8)
        
    def binary_value(self, val, bitsize): 
        binval = bin(val)[2:]
        if len(binval) > bitsize:
            raise SteganographyException("binary value larger than the expected size")
        while len(binval) < bitsize:
            binval = "0"+binval
        return binval

    def encode_text(self, txt):
        l = len(txt)
        binl = self.binary_value(l, 16) 
        self.put_binary_value(binl) 
        for char in txt: 
            c = ord(char)
            self.put_binary_value(self.byteValue(c))
        return self.image
       
    def decode_text(self):
        ls = self.read_bits(16)
        l = int(ls,2)
        i = 0
        unhideTxt = ""
        while i < l: 
            tmp = self.read_byte() 
            i += 1
            unhideTxt += chr(int(tmp,2)) 
        return unhideTxt

    def encode_image(self, imtohide):
        w = imtohide.width
        h = imtohide.height
        if self.width*self.height*self.nbchannels < w*h*imtohide.channels:
            raise SteganographyException("Carrier image not big enough to hold all the datas to steganography")
        binw = self.binary_value(w, 16) 
        binh = self.binary_value(h, 16)
        self.put_binary_value(binw) 
        self.put_binary_value(binh) 
        for h in range(imtohide.height): 
            for w in range(imtohide.width):
                for chan in range(imtohide.channels):
                    val = imtohide[h,w][chan]
                    self.put_binary_value(self.byteValue(int(val)))
        return self.image

                    
    def decode_image(self):
        width = int(self.read_bits(16),2) 
        height = int(self.read_bits(16),2)
        unhideimg = np.zeros((width,height, 3), np.uint8)
        for h in range(height):
            for w in range(width):
                for chan in range(unhideimg.channels):
                    val = list(unhideimg[h,w])
                    val[chan] = int(self.read_byte(),2) 
                    unhideimg[h,w] = tuple(val)
        return unhideimg
    
    def encode_binary(self, data):
        l = len(data)
        if self.width*self.height*self.nbchannels < l+64:
            raise SteganographyException("Carrier image not big enough to hold all the datas to steganography")
        self.put_binary_value(self.binary_value(l, 64))
        for byte in data:
            byte = byte if isinstance(byte, int) else ord(byte) # Compat py2/py3
            self.put_binary_value(self.byteValue(byte))
        return self.image

    def decode_binary(self):
        l = int(self.read_bits(64), 2)
        output = b""
        for i in range(l):
            output += chr(int(self.read_byte(),2)).encode("utf-8")
        return output

    


def encrypt_window():
    def encrypt(e,e2):
        in_f=r'C:\Users\Aman\Desktop\pandu.jpg'
        if v.get()==1:
            in_f = r'C:\Users\Aman\Desktop\pandu.jpg'
        elif v.get()==2:
            in_f = r'C:\Users\Aman\Desktop\girl.jpg'
        elif v.get()==3:
            in_f = r'C:\Users\Aman\Desktop\Moon.jpg'
        out_f = r'C:\Users\Aman\Desktop\decypted\\'+e2.get()+'.png'
        in_img = cv2.imread(in_f)
        steg = LSBSteg(in_img)
        data = e.get()
        res = steg.encode_binary(data)
        cv2.imwrite(out_f, res)
        Label(window,text="Encrypted",font=("Helvetica", 16)).grid(row=8,column=1,pady=(50,20),padx=50)
    window = Toplevel(root)
    window.state('zoomed')
    window.configure(background='#6F7511')
    Label(window,text="Enter Secret Message:",font=("Helvetica", 16)).grid(row=0,column=0,pady=(50,5))
    e=Entry(window,width=150)
    e.grid(row=1,column=0,padx=50,columnspan=4)
    e2=Entry(window)
    e2.grid(row=5,column=1,pady=(50,20))
    Label(window,text="Select Image:",font=("Helvetica", 16)).grid(row=2,column=0,pady=(50,20),padx=50)
    Label(window,image=logo1,width=200,height=200).grid(column=0,row=3)
    Label(window,image=logo2,width=200,height=200).grid(column=1,row=3)
    Label(window,image=logo3,width=200,height=200).grid(column=2,row=3)
    Radiobutton(window,text="Pic 1",variable=v,value=1).grid(column=0,row=4,pady=10)
    Radiobutton(window,text="Pic 2",variable=v,value=2).grid(column=1,row=4,pady=10)
    Radiobutton(window,text="Pic 3",variable=v,value=3).grid(column=2,row=4,pady=10)
    action_with_arg = partial(encrypt, e,e2)
    Button(window,text="ENCRYPT",command=action_with_arg).grid(column=1,row=7,pady=10)
    Label(window,text="Save As:",font=("Helvetica", 16)).grid(row=5,column=0,pady=(50,20))
    window.mainloop()








def dencrypt_window():
    def ask():
        def decry():
            in_f = filename
            in_img = cv2.imread(in_f)
            steg = LSBSteg(in_img)
            raw = steg.decode_binary()
            print(raw[0::])
            Label(window2,text="Secret Message::",font=("Helvetica", 16)).grid(row=3,column=0,pady=(50,5),padx=100)
            Label(window2,text=raw[0::],font=("Helvetica", 16),height=10,width=40).grid(row=4,column=0,pady=(5,5),padx=100,columnspan=4)
        filename = askopenfilename()
        window2.deiconify()
        e.insert(0,filename)
        Button(window2,text="DECRYPT",command=decry).grid(column=1,row=2,pady=20,padx=10)
        
    window2 = Toplevel(root)
    window2.state('zoomed')
    window2.configure(background='#6F7511')
    Label(window2,text="Enter image location:",font=("Helvetica", 16)).grid(row=0,column=0,pady=(50,5),padx=10)
    e=Entry(window2,width=50)
    e.grid(row=0,column=1,pady=(50,5),padx=10)
    Button(window2,text="Choose file",command=ask).grid(column=1,row=1,pady=5,padx=10)
    window2.mainloop()

    



logo1 = PhotoImage(file=r'C:\Users\Aman\Downloads\tinypng-magento-image_1 (1).gif')
logo3 = PhotoImage(file=r'C:\Users\Aman\Downloads\Moon.gif')
l=Label(root,text="Image Steganography",font=("Helvetica", 16))
l.grid(column=2,row=1,padx=200)
l.configure(background='#EE512A')
b1=Button(root,text="ENCRYPT",command=encrypt_window)
b1.grid(column=2,row=2,padx=200,pady=50)
b2=Button(root,text="DECRYPT",command=dencrypt_window,)
b2.grid(column=2,row=3,padx=200,pady=50)
root.configure(background='#6F7511')
root.state('zoomed')
logo= PhotoImage(file=r'C:\Users\Aman\Downloads\maxresdefault (1).gif')
l1=Label(root,image=logo,width=350,height=200)
l1.grid(column=2,row=0,padx=500,pady=50)
b1.configure(background='#F7DC6F')
b2.configure(background='#F7DC6F')
logo2 = PhotoImage(file=r'C:\Users\Priya\Downloads\taylor JPEG high.gif')



