from cryptography.fernet import Fernet
import qrcode
from PIL import Image

def load_key():
    return open("secret.key", "rb").read()

def generateQRCode():
    key = b'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='
    
    # value of key is assigned to a variable
    f = Fernet(key)
    
    # the plaintext is converted to ciphertext
    token = f.encrypt(b"23") # TODO : Pass Salon Id
    
    
    img = qrcode.make('https://goo.gl/maps/QeNkm71tLGggytJw7')

    # qrcode.image.pil.PilImage
    type(img)  

    img.save("shop.png")

    # decrypting the ciphertext
    d = f.decrypt(token)
    
    # display the plaintext and the decode() method 
    # converts it from byte to string
    # print(d.decode())
    return