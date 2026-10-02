import qrcode
from PIL import Image
import requests
from io import BytesIO

class QRCode:
    
    def __init__(self, logo_url, code_data, logo_path=None, is_logo_url=True) -> None:
        self.logo_url = logo_url
        self.code_data = code_data
        self.logo_path = logo_path
        self.is_logo_url = is_logo_url

    def open_image_url(self):
        response = requests.get(self.logo_url)
        return Image.open(BytesIO(response.content))
        

    def open_image_file(self):
        return Image.open(self.logo_path)

    def open_image(self):
        if self.is_logo_url:
            return self.open_image_url()
        return self.open_image_file()

    def generate_qr_code(self):
        # get logo
        logo = self.open_image()

        # taking base width
        basewidth = 500

        # adjust image size
        wpercent = (basewidth/float(logo.size[0]))
        hsize = int((float(logo.size[1])*float(wpercent)))
        logo = logo.resize((basewidth, hsize))
        QRcode = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_H
        )

        # taking url or text
        url = self.code_data

        # adding URL or text to QRcode
        QRcode.add_data(url)

        # generating QR code
        QRcode.make()

        # taking color name from user
        QRcolor = 'Black'

        # adding color to QR code
        QRimg = QRcode.make_image(
            fill_color=QRcolor, back_color="white").convert('RGB')
        # Resize code
        QRimg = QRimg.resize((2050, 2050))
        # set size of QR code
        pos = ((QRimg.size[0] - logo.size[0]) // 2,
               (QRimg.size[1] - logo.size[1]) // 2)
        QRimg.paste(logo, pos)
        # # save the QR code generated
        # QRimg.save('gfg_QR.png')
        return QRimg
